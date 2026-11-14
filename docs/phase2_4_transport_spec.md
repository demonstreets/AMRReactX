# Phase 2.4 — 湍流-扩散耦合 Spec

**日期**: 2026-06-09  
**位置**: `~/my-pele/src/engineering/turbulence/`  
**依赖**: 2.2 k-ε 核心（提供 μ_t）

---

## 1. 物理模型

### 1.1 湍流 Schmidt 数

RANS 框架下，湍流脉动增强组分混合。有效扩散系数：

```
D_i,eff = D_i,lam + D_t
D_t = ν_t / Sc_t = μ_t / (ρ · Sc_t)
```

其中：
- `D_i,lam` — 组分 i 的层流扩散系数（m²/s）
- `ν_t = μ_t / ρ` — 湍流运动粘度（m²/s）
- `Sc_t` — 湍流 Schmidt 数，气体推荐值 0.7

### 1.2 模块职责

| 函数 | 输入 | 输出 | 用途 |
|------|------|------|------|
| 湍流扩散系数 | μ_t, ρ, Sc_t | D_t | 物种扩散增强 |
| 有效扩散系数 | D_lam, μ_t, ρ, Sc_t | D_eff | 替换 PeleLMeX 扩散系数 |
| 有效粘度 | μ_lam, μ_t | μ_eff | 动量方程有效粘度 |

---

## 2. C++ 接口

### 2.1 文件清单

```
src/engineering/turbulence/
├── k_epsilon_constants.H      # 已有
├── k_epsilon_core.H/.cpp      # 已有
├── wall_functions.H/.cpp      # 已有
├── turbulent_transport.H      # NEW — 全部 inline
```

### 2.2 常数扩展

在 `KEpsilonConstants` 中新增：

```cpp
double Sc_t = 0.7;  // 湍流 Schmidt 数（气体）
```

### 2.3 函数声明 (`turbulent_transport.H`)

```cpp
#pragma once
#include "k_epsilon_constants.H"

namespace Turbulence {

// ============================================================
// 湍流扩散系数: D_t = mu_t / (rho * Sc_t)
// 输入: mu_t (涡粘系数), rho (密度), Sc_t (湍流Schmidt数)
// 返回: D_t (m²/s)
// 保护: rho <= 0 → return 0.0
// ============================================================
inline double compute_turbulent_diffusivity(
    double mu_t, double rho,
    double Sc_t = 0.7)
{
    if (rho <= 0.0) return 0.0;
    return mu_t / (rho * Sc_t);
}

// ============================================================
// 有效扩散系数: D_eff = D_lam + D_t
// ============================================================
inline double compute_effective_diffusivity(
    double D_lam, double mu_t, double rho,
    double Sc_t = 0.7)
{
    return D_lam + compute_turbulent_diffusivity(mu_t, rho, Sc_t);
}

// ============================================================
// 有效粘度: mu_eff = mu_lam + mu_t
// ============================================================
inline double compute_effective_viscosity(double mu_lam, double mu_t)
{
    return mu_lam + mu_t;
}

// ============================================================
// 批量：对 N 个组分计算有效扩散系数
// D_lam[i] 是层流扩散系数数组
// 返回填充到 D_eff[i]
// ============================================================
inline void compute_effective_diffusivities(
    const double* D_lam, int n_species,
    double mu_t, double rho, double Sc_t,
    double* D_eff)
{
    double D_t = compute_turbulent_diffusivity(mu_t, rho, Sc_t);
    for (int i = 0; i < n_species; ++i) {
        D_eff[i] = D_lam[i] + D_t;
    }
}

} // namespace Turbulence
```

---

## 3. 单元测试

文件：`~/my-pele/test/unit/test_turbulent_transport.cpp`

| # | 测试 | 验证 |
|---|------|------|
| 1 | D_t 基本 | μ_t=1e-3, ρ=1.0, Sc_t=0.7 → D_t=1.4286e-3 |
| 2 | D_t rho=0 | → 0.0 |
| 3 | D_t 自定义 Sc_t=1.0 | μ_t=1e-3, ρ=1.0 → D_t=1e-3 |
| 4 | D_eff | D_lam=2e-5, μ_t=1e-3, ρ=1.0 → D_eff=2e-5+1.4286e-3 |
| 5 | μ_eff | μ_lam=1.8e-5, μ_t=9e-5 → μ_eff=1.08e-4 |
| 6 | 批量 N=3 | 验证 3 个组分输出不同 D_lam + 相同 D_t |
| 7 | Sc_t 默认值 | 验证 KEpsilonConstants 中 Sc_t=0.7 |

编译：
```bash
g++ -std=c++17 -Isrc/engineering/turbulence \
    test/unit/test_turbulent_transport.cpp \
    -o build_test/test_turbulent_transport && ./build_test/test_turbulent_transport
```

（不需要链接 .cpp —— 全部 inline）

---

## 4. 交付物

| 文件 | 行数 |
|------|:--:|
| `k_epsilon_constants.H` (修改) | +1 |
| `turbulent_transport.H` | ~45 |
| `test/unit/test_turbulent_transport.cpp` | ~120 |
| **总计** | **~165 行** |
