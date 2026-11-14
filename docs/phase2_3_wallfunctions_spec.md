# Phase 2.3 — Launder-Spalding 壁面函数 Spec

**日期**: 2026-06-09  
**位置**: `~/my-pele/src/engineering/turbulence/`  
**依赖**: 2.2 k-ε 核心（`k_epsilon_core.H`）

---

## 1. 物理模型

### 1.1 壁面律 (Law of the Wall)

近壁区域分为三层，k-ε 壁面函数工作在 **对数律区**（y⁺ > 30）：

```
粘性子层:   u⁺ = y⁺                              (y⁺ ≤ 5)
缓冲区:     过渡                                   (5 < y⁺ ≤ 30)
对数律区:   u⁺ = (1/κ)·ln(y⁺) + B                 (y⁺ > 30)
```

其中：
- `u⁺ = u_∥ / u_τ` — 无量纲切向速度
- `y⁺ = y_p · u_τ / ν` — 无量纲壁面距离
- `u_τ = √(τ_w / ρ)` — 摩擦速度
- `y_p` — 第一层网格中心到壁面的垂直距离
- `ν = μ / ρ` — 运动粘度
- `κ = 0.41` (von Kármán 常数)
- `B = 5.0` (光滑壁面常数)

### 1.2 模块职责

本模块是**纯计算核心**，计算壁面函数所需的量：

| 函数 | 输入 | 输出 | 用途 |
|------|------|------|------|
| y⁺ 计算 | y_p, u_τ, ν | y⁺ | 判断是否在对数律区 |
| 摩擦速度迭代 | y_p, u_∥, ν, ρ | u_τ, τ_w | 从已知切向速度反推摩擦速度 |
| 壁面 k | u_τ, C | k_wall | 壁面 k 边界值 |
| 壁面 ε | u_τ, y_p, C | ε_wall | 壁面 ε 边界值 |
| 壁面生成项修正 | τ_w, u_∥, y_p, ρ, C | P_k_wall | 壁面第一层网格的 P_k |
| 有效涡粘（壁面）| τ_w, u_∥, y_p, ν | μ_t_wall | 避免壁面 μ_t 高估 |

### 1.3 摩擦速度求解（关键）

已知：近壁第一层网格的切向速度 `u_p`、距壁面距离 `y_p`、流体特性 `ν`、`ρ`。

求：`u_τ`，满足对数律方程（假设 y⁺ > 30）：

```
u_p / u_τ = (1/κ) · ln(y_p · u_τ / ν) + B
```

移项：`f(u_τ) = u_τ · [(1/κ) · ln(y_p · u_τ / ν) + B] - u_p = 0`

用 Newton-Raphson 迭代求解：

```
u_τ^(n+1) = u_τ^(n) - f(u_τ^(n)) / f'(u_τ^(n))
f'(u_τ) = u_p / u_τ^(-?)   actually:
f(u_τ) = u_τ * A(u_τ) - u_p, where A = u⁺ = (1/κ)ln(y⁺) + B
f'(u_τ) = A(u_τ) + u_τ * (1/κ) * (1/u_τ) = A(u_τ) + 1/κ = u⁺ + 1/κ
```

初始猜测：`u_τ^(0) = u_p / 20`（对应 u⁺ ≈ 20，在对数律区）

---

## 2. C++ 接口

### 2.1 文件清单

```
src/engineering/turbulence/
├── k_epsilon_constants.H    # 2.2 已有（无需修改）
├── k_epsilon_core.H/.cpp    # 2.2 已有（无需修改）
├── wall_functions.H         # NEW
└── wall_functions.cpp       # NEW
```

### 2.2 常数扩展

在 `KEpsilonConstants` 中新增壁面函数常数（修改 `k_epsilon_constants.H`）：

```cpp
double B = 5.0;          // 光滑壁面对数律常数
double yplus_threshold = 30.0;  // 对数律区阈值
int max_newton_iter = 20;       // Newton 迭代最大步数
double newton_tol = 1.0e-8;     // Newton 迭代收敛容差
```

### 2.3 函数声明 (`wall_functions.H`)

```cpp
#pragma once
#include "k_epsilon_constants.H"

namespace Turbulence {

// ============================================================
// y⁺ 计算: y⁺ = y_p * u_tau / nu
// ============================================================
double compute_yplus(double y_p, double u_tau, double nu);

// ============================================================
// 摩擦速度 Newton-Raphson 迭代求解
// 输入：y_p（壁面距离）、u_par（切向速度）、nu（运动粘度）
// 输出：u_tau（摩擦速度）
// 如果 y⁺ 初始估计 < yplus_threshold，返回 0 表示在粘性子层
// 如果迭代不收敛，返回 -1 表示失败
// ============================================================
double compute_utau(double y_p, double u_par, double nu,
                    const KEpsilonConstants& C = KEpsilonConstants());

// ============================================================
// 壁面剪切应力: τ_w = ρ * u_tau²
// ============================================================
double compute_tau_wall(double rho, double u_tau);

// ============================================================
// 壁面 k 值（2.2 已有 compute_k_wall，此处保留调用）
// k_wall = u_tau² / sqrt(C_mu)
// ============================================================

// ============================================================
// 壁面 ε 值（2.2 已有 compute_eps_wall，此处保留调用）
// ε_wall = u_tau³ / (kappa * y_p)
// ============================================================

// ============================================================
// 壁面生成项修正
// 标准做法：P_k 在近壁面使用壁面剪切应力替代涡粘公式
// P_k_wall = (τ_w * u_par) / y_p
// 这是基于"局部平衡假设"：P_k ≈ ρε 在对数律区
// ============================================================
double compute_production_wall(double tau_wall, double u_par, double y_p);

// ============================================================
// 壁面有效湍流粘度
// μ_t_eff = max(0, τ_w * y_p / u_par - μ_lam)
// 防止壁面 μ_t 被标准 k-ε 公式高估
// ============================================================
double compute_mut_wall(double tau_wall, double u_par,
                        double y_p, double mu_lam);

// ============================================================
// 辅助：检查是否在对数律区
// ============================================================
bool in_log_layer(double yplus,
                  const KEpsilonConstants& C = KEpsilonConstants());

} // namespace Turbulence
```

---

## 3. 单元测试

文件：`~/my-pele/test/unit/test_wall_functions.cpp`

### 测试用例

| # | 测试 | 验证方法 |
|---|------|---------|
| 1 | y⁺ 基本计算 | y_p=0.01, u_tau=0.1, nu=1e-5 → y⁺=100 |
| 2 | y⁺ 为零 | y_p=0 → y⁺=0 |
| 3 | in_log_layer 判断 | y⁺=100 → true; y⁺=3 → false |
| 4 | Newton 迭代基本收敛 | y_p=0.01, u_par=2.0, nu=1e-5 → u_tau 收敛 |
| 5 | Newton 迭代粘性子层 | y_p 极小导致 y⁺<30 → 返回 0 |
| 6 | τ_w 计算 | rho=1.2, u_tau=0.1 → τ_w=0.012 |
| 7 | P_k_wall 计算 | τ_w=0.012, u_par=2.0, y_p=0.01 → P_k_wall=2.4 |
| 8 | μ_t_wall 计算 | τ_w=0.012, u_par=2.0, y_p=0.01, mu_lam=1.8e-5 |
| 9 | 常数默认值 | B=5.0, yplus_threshold=30.0 |
| 10 | μ_t_wall 非负 | 小 u_par 时不返回负值 |

### 编译

```bash
g++ -std=c++17 \
    -Isrc/engineering/turbulence \
    test/unit/test_wall_functions.cpp \
    src/engineering/turbulence/k_epsilon_core.cpp \
    src/engineering/turbulence/wall_functions.cpp \
    -o build_test/test_wall_functions && ./build_test/test_wall_functions
```

---

## 4. 与 2.2 的关系

2.2 中的 `compute_k_wall` 和 `compute_eps_wall` 基础公式保留，壁面函数层调用它们。本模块（2.3）新增的是**摩擦速度求解**和**壁面生成项/涡粘修正**——这些是 2.2 基础公式的输入准备和修正逻辑。

---

## 5. 交付物

| 文件 | 行数估计 |
|------|---------|
| `k_epsilon_constants.H` (修改) | +4 行 |
| `src/engineering/turbulence/wall_functions.H` | ~55 |
| `src/engineering/turbulence/wall_functions.cpp` | ~150 |
| `test/unit/test_wall_functions.cpp` | ~200 |
| **总计** | **~410 行** |
