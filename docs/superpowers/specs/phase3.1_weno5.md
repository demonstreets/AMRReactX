# Phase 3.1 Spec: WENO5/WENO5-Z 重构模块

**版本:** v1.0  
**日期:** 2026-06-11  
**状态:** 待审阅  
**范围:** 独立数学库 + 1D 单元测试（不涉及 PeleC/AMReX 集成）

---

## 1. 物理背景与数值方法

### 1.1 问题

有限体积法中，控制方程离散需要 cell 面处的通量。已知 cell-averaged 值 ū_i，需要重构面 i+1/2 处的左右值 u^L_{i+1/2} 和 u^R_{i+1/2}，作为 Riemann 求解器的输入。

二阶 MUSCL/PLM 在激波/爆轰等强间断处精度不足或需要额外限制器。WENO（Weighted Essentially Non-Oscillatory）通过 5 点模板的非线性凸组合，在光滑区达到 5 阶精度，在间断处自动降阶以避免振荡。

### 1.2 数学公式

#### 子模板二次插值

对 5 个 cell-averaged 值 (u_{i-2}, u_{i-1}, u_i, u_{i+1}, u_{i+2})，定义 3 个子模板：

| 模板 | 点集 | 面 i+1/2 左值插值 u^L_{i+1/2} | 面 i+1/2 右值插值 u^R_{i+1/2} |
|------|------|-------------------------------|-------------------------------|
| S₀ | {i-2, i-1, i} | v₀ = (2u_{i-2} - 7u_{i-1} + 11u_i) / 6 | v₀' = (-u_{i-1} + 5u_i + 2u_{i+1}) / 6 |
| S₁ | {i-1, i, i+1} | v₁ = (-u_{i-1} + 5u_i + 2u_{i+1}) / 6 | v₁' = (2u_i + 5u_{i+1} - u_{i+2}) / 6 |
| S₂ | {i, i+1, i+2} | v₂ = (2u_i + 5u_{i+1} - u_{i+2}) / 6 | v₂' = (2u_{i+2} - 7u_{i+1} + 11u_i) / 6 |

> **注意**：v₀ 和 v₂'，v₁ 和 v₁'，v₂ 和 v₀' 之间分别存在对称性——右值可以复用左值的模板权重，只交换子模板映射。

#### 理想线性权重

各子模板在光滑区的理论最优权重（使得组合达到 5 阶）：

- d₀ = 1/10 = 0.1
- d₁ = 6/10 = 0.6
- d₂ = 3/10 = 0.3

#### 光滑指示器（Jiang-Shu, 1996）

β_k 衡量子模板 S_k 上的光滑程度，值越小越光滑：

- **β₀** = (13/12)(u_{i-2} - 2u_{i-1} + u_i)² + (1/4)(u_{i-2} - 4u_{i-1} + 3u_i)²
- **β₁** = (13/12)(u_{i-1} - 2u_i + u_{i+1})² + (1/4)(u_{i-1} - u_{i+1})²
- **β₂** = (13/12)(u_i - 2u_{i+1} + u_{i+2})² + (1/4)(3u_i - 4u_{i+1} + u_{i+2})²

#### WENO-JS 非线性权重（Jiang & Shu, 1996）

```
α_k = d_k / (β_k + ε)^p
ω_k = α_k / (α₀ + α₁ + α₂)
```

其中 ε = 1e-6（防止除零），p = 2。

#### WENO-Z 非线性权重（Borges et al., 2008）

增加全局光滑指示器 τ₅ = |β₀ - β₂|：

```
α_k = d_k · [1 + (τ₅ / (β_k + ε))^p]
ω_k = α_k / (α₀ + α₁ + α₂)
```

其中 p = 2。WENO-Z 在强间断处非振荡性优于 WENO-JS，对爆轰波面更合适。

#### 最终重构

```
u^L_{i+1/2} = ω₀·v₀ + ω₁·v₁ + ω₂·v₂
u^R_{i+1/2} = ω₀'·v₀' + ω₁'·v₁' + ω₂'·v₂'
```

右值的子模板映射（对称性）：
- 计算 u^R 可直接调用 u^L 的逻辑，但输入序列反转：(u_{i+2}, u_{i+1}, u_i, u_{i-1}, u_{i-2})
- 或者复用左值权重 ω_k 到对称的右值子模板

---

## 2. 接口设计

### 2.1 函数签名

```cpp
#ifndef AMREX_GPU_HOST_DEVICE
#define AMREX_GPU_HOST_DEVICE
#endif

namespace reconstruction {

enum class WENOVariant { JS, Z };

/// 标量 1D WENO5 重构
/// @tparam T  数据类型 (float/double)
/// @param u_im2, u_im1, u_i, u_ip1, u_ip2  5 个 cell-averaged 值
/// @param[out] u_left   面 i+1/2 左值
/// @param[out] u_right  面 i+1/2 右值
/// @param variant  WENO 变体 (JS 或 Z)
template <typename T>
AMREX_GPU_HOST_DEVICE
void weno5(const T u_im2, const T u_im1, const T u_i, const T u_ip1, const T u_ip2,
           T& u_left, T& u_right,
           WENOVariant variant = WENOVariant::Z);

/// 仅重构左值（用于逐面循环场景）
template <typename T>
AMREX_GPU_HOST_DEVICE
T weno5_left(const T u_im2, const T u_im1, const T u_i, const T u_ip1, const T u_ip2,
             WENOVariant variant = WENOVariant::Z);

/// 光滑指示器（供调试诊断）
template <typename T>
AMREX_GPU_HOST_DEVICE
void smoothness_indicators(const T u_im2, const T u_im1, const T u_i, const T u_ip1, const T u_ip2,
                           T& beta0, T& beta1, T& beta2);

} // namespace reconstruction
```

### 2.2 设计原则

| 原则 | 实现 |
|------|------|
| 无状态 | 纯函数，所有输入通过参数传递 |
| 无 AMReX 依赖 | `AMREX_GPU_HOST_DEVICE` 仅作标记宏，可空定义 |
| 模板化 | `template <typename T>` 支持 float/double |
| 头文件 only | 编译时全内联，无 .cpp |
| 无内存分配 | 全部栈变量 |

### 2.3 精度要求

- double 精度下的光滑正弦函数：5 阶收敛（L₁ 误差 ∝ Δx⁵，p ≥ 4.5）
- float 精度下：至少 3 阶（受限于单精度有效位数）

---

## 3. 文件结构

```
my-pele/
├── src/common/reconstruction/
│   ├── weno5.H          # WENO5 核心实现（含 JS + Z 两套权重）
│   └── reconstruction_factory.H  # (预留) 统一入口，本次不建
└── test/unit/
    └── test_weno5.cpp   # 1D 单元测试
```

说明：一个 `weno5.H` 包含 WENO-JS 和 WENO-Z 两套权重逻辑，通过 `WENOVariant` 枚举在 `weno5()` 函数内 switch。不必拆成两个头文件。`reconstruction_factory.H` 留到 Phase 3.2 跟 PeleC 集成时再建。

---

## 4. 单元测试设计

### 4.1 测试框架

纯 C++，无外部依赖，编译为独立可执行文件：

```bash
g++ -std=c++17 -O2 -o build_test/test_weno5 test/unit/test_weno5.cpp
./build_test/test_weno5
```

### 4.2 测试用例

| # | 测试名 | 输入 | 验证项 | 通过条件 |
|---|--------|------|--------|----------|
| T01 | **光滑正弦 5 阶精度** | u(x)=sin(2πx), N=[16,32,64,128] | L₁/L∞ 误差 vs 解析值 | L₁ 收敛率 ≥ 4.5 |
| T02 | **常数场保形** | u(x)=1.0 | 重构值 ≡ 1.0 | 逐点误差 < 1e-14 |
| T03 | **线性场精确重构** | u(x)=ax+b | 重构值 vs 解析 | L₁ < 1e-12 (double) |
| T04 | **Sod 管间断** | u=[1,1,1,3.857,3.857] | 无过冲/下冲 | u_left, u_right ∈ [1, 3.857] |
| T05 | **激波捕捉** | u=[0,0,0,1,1] | 过渡区 ≤ 3 格点 | 无振荡（单调过渡） |
| T06 | **WENO-JS vs WENO-Z** | 间断+高频波混合 | Z 在间断处更锐利 | Z 在 β 退化时不出现 |
| T07 | **对称性** | 正向扫描 vs 反向扫描 | 逐位一致 | 误差 < 1e-13 |
| T08 | **float 兼容性** | 同 T01，T=float | 至少 3 阶 | L₁ 收敛率 ≥ 2.5 |

### 4.3 平滑正弦 5 阶精度测试详情

对一维均匀网格 x ∈ [0, 1]，N = 16, 32, 64, 128 个格点：

```
u_i = sin(2π · x_i)   （cell-averaged 值用 cell 中心近似）

对每个内格点 i = 2..N-3：
  weno5(u_{i-2..i+2}, uL, uR)
  解析值：u_exact = sin(2π · x_{i+1/2})
  误差 = |uL - u_exact|
```

L₁ 误差 = (1/N_face) · Σ|error|，拟合 log₂(L₁) vs log₂(N)，斜率即为收敛阶。

### 4.4 预期输出

```
=== WENO5 Unit Tests ===
[PASS] T01: Sine 5th-order convergence (p=4.92)
[PASS] T02: Constant preservation (max_err=0)
[PASS] T03: Linear exact reconstruction (L1=3.2e-16)
[PASS] T04: Sod jump — no overshoot
[PASS] T05: Shock capture — monotone transition
[PASS] T06: WENO-Z sharper than WENO-JS at discontinuity
[PASS] T07: Symmetry OK (diff=0)
[PASS] T08: float convergence OK (p=3.1)
=== 8/8 PASS ===
```

---

## 5. 验收标准

- [ ] 所有 8 个测试 PASS（含 5 阶精度确认）
- [ ] 代码不含任何 `#include <amrex>` 或 `#include <Pele*>` 依赖
- [ ] 所有函数标记 `AMREX_GPU_HOST_DEVICE`
- [ ] 无动态内存分配
- [ ] code-reviewer Type A 审查 PASS

---

## 6. 审查要点（给 code-reviewer 的预检清单）

| # | 检查项 | 严重度 |
|---|--------|:---:|
| 1 | WENO-JS 子模板插值系数正确性（v₀, v₁, v₂ 对照公式验证） | CRITICAL |
| 2 | 光滑指示器 β 公式正确性 | CRITICAL |
| 3 | 权重归一化（Σω = 1） | CRITICAL |
| 4 | 右值重构的对称性处理正确（不重复计算权重） | HIGH |
| 5 | 无穷大/NaN 防护（ε 正性、分母非零） | HIGH |
| 6 | 模板参数 T 无隐式转换陷阱 | WARN |
| 7 | 头文件 include guard | WARN |
