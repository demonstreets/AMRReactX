# Phase 2.2 — k-ε 湍流模型核心实现 Spec

**日期**: 2026-06-09  
**位置**: `~/my-pele/src/engineering/turbulence/`  
**依赖**: 无外部库（纯数值计算模块，独立于 AMReX）

---

## 1. 物理模型

### 1.1 控制方程

标准 Jones-Launder k-ε 模型：

```
∂(ρk)/∂t + ∇·(ρu k) = ∇·[(μ + μ_t/σ_k) ∇k] + P_k - ρε
∂(ρε)/∂t + ∇·(ρu ε) = ∇·[(μ + μ_t/σ_ε) ∇ε] + C_ε1 (ε/k) P_k - C_ε2 ρ ε²/k
```

其中：
- **涡粘系数**: `μ_t = C_μ · ρ · k² / ε`
- **湍流生成项**: `P_k = μ_t · S²`，S 为平均应变率张量的模 `S = √(2 S_ij S_ij)`
- **常数**:
  - `C_μ = 0.09`
  - `C_ε1 = 1.44`
  - `C_ε2 = 1.92`
  - `σ_k = 1.0`
  - `σ_ε = 1.3`

### 1.2 模块边界

本模块是**纯计算核心**——不负责对流传导（由 PeleLMeX 的 advection-diffusion 框架处理），只负责：

| 职责 | 输入 | 输出 |
|------|------|------|
| 计算涡粘系数 | ρ, k, ε | μ_t |
| 计算湍流生成项 | μ_t, 速度梯度 ∂u_i/∂x_j | P_k |
| 计算 k 方程源项 | ρ, P_k, ε | S_k = P_k - ρε |
| 计算 ε 方程源项 | ρ, P_k, k, ε | S_ε = C_ε1·(ε/k)·P_k - C_ε2·ρ·ε²/k |
| 湍流扩散系数 | μ, μ_t, σ | μ + μ_t/σ（分别给 k 和 ε） |

---

## 2. C++ 数据结构

### 2.1 文件清单

```
src/engineering/turbulence/
├── k_epsilon_constants.H    # 模型常数
├── k_epsilon_core.H         # 涡粘 + 源项 + 扩散系数 声明
└── k_epsilon_core.cpp       # 实现
```

### 2.2 常数定义 (`k_epsilon_constants.H`)

```cpp
#pragma once
#include <cmath>

namespace Turbulence {

struct KEpsilonConstants {
    double C_mu   = 0.09;
    double C_eps1 = 1.44;
    double C_eps2 = 1.92;
    double sigma_k = 1.0;
    double sigma_eps = 1.3;

    // 数值裁剪（防止除零和负值）
    double k_min  = 1.0e-14;  // k 下限
    double eps_min = 1.0e-14; // ε 下限
    double mu_t_max_ratio = 1.0e5; // μ_t / μ 上限
};

} // namespace Turbulence
```

### 2.3 核心函数声明 (`k_epsilon_core.H`)

```cpp
#pragma once
#include "k_epsilon_constants.H"

namespace Turbulence {

// ============================================================
// 涡粘系数: μ_t = C_μ * ρ * k² / ε
// 含裁剪：k = max(k, k_min), ε = max(ε, eps_min)
//         μ_t = min(C_μ*ρ*k²/ε, mu_t_max_ratio * mu_lam)
// ============================================================
double compute_mut(double rho, double k, double eps,
                   double mu_lam,
                   const KEpsilonConstants& C = KEpsilonConstants());

// ============================================================
// 湍流生成项: P_k = μ_t * S²
// S² = 2 * S_ij * S_ij
// S_ij 从速度梯度计算：
//   du/dx, du/dy, du/dz
//   dv/dx, dv/dy, dv/dz
//   dw/dx, dw/dy, dw/dz
// ============================================================
double compute_strain_sq(const double grad_u[3][3]);

double compute_production(double mut, double strain_sq);

// ============================================================
// 源项
// S_k = P_k - ρ * ε
// S_ε = C_eps1 * (ε/k) * P_k - C_eps2 * ρ * ε²/k
// 含裁剪：
//   k = max(k, k_min) 防止除零
//   ε = max(ε, eps_min)
//   P_k = max(P_k, 0)  生成项非负（物理约束）
// ============================================================
void compute_source_terms(double rho, double k, double eps,
                          double P_k,
                          double& S_k, double& S_eps,
                          const KEpsilonConstants& C = KEpsilonConstants());

// ============================================================
// 有效扩散系数（湍流贡献）
// Γ_k  = mu_lam + mu_t / sigma_k
// Γ_eps = mu_lam + mu_t / sigma_eps
// ============================================================
double compute_diff_k(double mu_lam, double mu_t,
                      const KEpsilonConstants& C = KEpsilonConstants());
double compute_diff_eps(double mu_lam, double mu_t,
                        const KEpsilonConstants& C = KEpsilonConstants());

// ============================================================
// 边界条件辅助：壁面 k 和 ε（标准 k-ε 壁面函数）
// 基于摩擦速度 u_tau:
//   k_wall = u_tau² / sqrt(C_mu)
//   eps_wall = u_tau³ / (κ * y_p)    其中 κ=0.41, y_p 为第一层网格距壁面距离
// 注：完整壁面函数在 Phase 2.3 实现，此处只提供基础公式
// ============================================================
double compute_k_wall(double u_tau,
                      const KEpsilonConstants& C = KEpsilonConstants());
double compute_eps_wall(double u_tau, double y_p);

} // namespace Turbulence
```

---

## 3. 实现细节

### 3.1 应变率张量

```
S_ij = 0.5 * (∂u_i/∂x_j + ∂u_j/∂x_i)

S² = 2 * (S_xx² + S_yy² + S_zz² + 2*S_xy² + 2*S_xz² + 2*S_yz²)

其中:
  S_xx = du/dx,  S_yy = dv/dy,  S_zz = dw/dz
  S_xy = 0.5*(du/dy + dv/dx)
  S_xz = 0.5*(du/dz + dw/dx)
  S_yz = 0.5*(dv/dz + dw/dy)
```

### 3.2 数值稳定性措施

| 风险 | 措施 |
|------|------|
| k → 0 导致 μ_t 除零 | `k = max(k, k_min)` where `k_min = 1e-14` |
| ε → 0 导致 μ_t → ∞ | `ε = max(ε, eps_min)`; `μ_t` 上限裁剪 |
| P_k < 0（数值噪声）| `P_k = max(P_k, 0.0)` |
| k, ε 变负（对流传导后）| 调用方负责裁剪 ≥ 0；本模块输入假设已正 |

### 3.3 与 PeleLMeX 的接口约定（后续集成）

PeleLMeX 在 advection-diffusion 步骤中：
1. 对流通量由 Godunov 格式计算（k 和 ε 作为被动标量）
2. 扩散通量由扩散求解器计算，使用 `compute_diff_k/eps` 返回的有效扩散系数
3. 源项通过 `compute_source_terms` 返回，作为显式源项加入
4. 涡粘系数 `μ_t` 通过 `compute_mut` 加入动量方程的有效粘度

**本模块不实现上述对接**——仅提供纯函数接口。

---

## 4. 单元测试

文件：`~/my-pele/test/unit/test_k_epsilon.cpp`

### 测试用例

| # | 测试 | 验证方法 |
|---|------|---------|
| 1 | 常数默认值 | C_mu=0.09, C_eps1=1.44, ... |
| 2 | compute_mut 基本计算 | ρ=1.0, k=0.1, ε=10.0, μ_lam=1e-5 → μ_t = 0.09*1*0.01/10 = 9e-5 |
| 3 | compute_mut 裁剪（k=0）| k=0 → k 被裁剪到 k_min，μ_t 有限 |
| 4 | compute_mut 裁剪（ε=0）| ε=0 → ε 被裁剪到 eps_min，μ_t 有限 |
| 5 | compute_mut 上限裁剪 | 超大 k/ε 比值 → μ_t 被裁剪到 mu_t_max_ratio * μ_lam |
| 6 | compute_strain_sq 均匀剪切 | du/dy=1.0 → S² = 2*(0.5)²*2 = 1.0 |
| 7 | compute_strain_sq 零梯度 | 全零 → S² = 0 |
| 8 | compute_strain_sq 各向同性压缩 | ∂u_i/∂x_j = δ_ij → S² = ... |
| 9 | compute_production | mut=0.09, S²=100 → P_k=9.0 |
| 10 | source_terms 基本 | ρ=1.0, k=0.1, ε=10.0, P_k=1.0 → 验证 S_k, S_eps |
| 11 | source_terms P_k=0 | 纯耗散 → S_k = -ρε, S_eps = -C_eps2*ρ*ε²/k |
| 12 | source_terms k 裁剪 | k→0 → 使用 k_min 防除零 |
| 13 | diff_k/diff_eps | mu_lam=1e-5, mu_t=9e-5 → Γ_k=1e-5+9e-5/1.0=1e-4 |
| 14 | k_wall / eps_wall | u_tau=0.1 → k_wall=0.01/sqrt(0.09)≈0.0333 |

编译：
```bash
g++ -std=c++17 -Isrc/engineering/turbulence \
    test/unit/test_k_epsilon.cpp \
    src/engineering/turbulence/k_epsilon_core.cpp \
    -o build_test/test_k_epsilon && ./build_test/test_k_epsilon
```

---

## 5. 交付物

| 文件 | 行数估计 |
|------|---------|
| `src/engineering/turbulence/k_epsilon_constants.H` | ~25 |
| `src/engineering/turbulence/k_epsilon_core.H` | ~60 |
| `src/engineering/turbulence/k_epsilon_core.cpp` | ~120 |
| `test/unit/test_k_epsilon.cpp` | ~250 |
| **总计** | **~455 行** |
