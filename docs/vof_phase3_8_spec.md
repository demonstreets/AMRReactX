# Phase 3.8 — 两相 HLLC Riemann 求解器

> 日期：2026-06-13 | 前置：3.7 两相 EOS ✅
> 🔴 这是 3.7→3.8 交接契约的执行——替换等温闭合为真正的能量平衡

---

## 0. 范围

**3.8 做**：
- 两相 HLLC 求解器模块（独立于现有 Riemann.H）
- 等压 p_L*=p_R*=p* + 等能量闭合（替换 3.7 的等温）
- 波速估计兼容 stiffened-gas EOS
- 在 MOL.cpp / Godunov.H 中按面两侧相位分派求解器

**3.8 不做**：
- CSF 表面张力（3.9）
- 非平衡相变
- 全耦合迭代 p-T 求解（先做显式等能量）

---

## 1. HLLC 算法概要

三波结构：`S_L < S* < S_R`

```
  左状态 L       左星区 *L    右星区 *R      右状态 R
     ρ_L           ρ*_L         ρ*_R           ρ_R
     u_L           u*           u*             u_R
     p_L           p*           p*             p_R
     e_L           e*_L         e*_R           e_R
```

**波速估计（兼容 stiffened-gas）**：

```
c_k = sqrt(γ_k * (p_k + p_∞,k) / ρ_k)     // k = L, R
q_k = (p* ≤ p_k) ? 1 : sqrt(1 + (γ_k+1)/(2*γ_k) * (p*/p_k - 1))

S_L = u_L - c_L * q_L
S_R = u_R + c_R * q_R
S*  = (p_R - p_L + ρ_L*u_L*(S_L-u_L) - ρ_R*u_R*(S_R-u_R))
      / (ρ_L*(S_L-u_L) - ρ_R*(S_R-u_R))
```

**p* 求解（等压 + 等能量闭合）**：

```
// PVRS 近似（Toro §9.5.2）
a_K = 2 / ((γ_K+1) * ρ_K)
b_K = (γ_K-1)/(γ_K+1) * p_K - (2*γ_K)/(γ_K+1) * p_∞,K
// ... 迭代或不迭代的近似
p* = max(0, PVRS_estimate)
```

**星区状态**：

```
ρ*_K = ρ_K * (S_K - u_K) / (S_K - S*)
e*_K = ((S_K - u_K)*e_K - p_K*u_K + p* * S*) / (S_K * ρ*_K)  // 等能量
```

**通量**：

```
if S_L > 0:     F = F_L
if S* > 0:      F = F_L + S_L*(U*_L - U_L)
if S_R > 0:     F = F_R + S_R*(U*_R - U_R)
else:           F = F_R
```

---

## 2. 新增文件

### 2.1 `src/academic/twophase/TwoPhaseHLLC.H`（~200 行）

```cpp
#pragma once
#include "StiffenedGas.H"
#include <AMReX_REAL.H>
#include <AMReX_Gpu.H>
#include <AMReX_Math.H>

// EOS parameters per side (gamma and p_inf)
struct PhaseEOSParams {
    amrex::Real gamma;
    amrex::Real p_inf;    // 0 for ideal gas
};

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real twophase_soundspeed(
    amrex::Real rho, amrex::Real p, const PhaseEOSParams& eos)
{
    return std::sqrt(eos.gamma * (p + eos.p_inf) / rho);
}

// PVRS pressure estimate (Toro §9.5.2)
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real twophase_pvrs(
    amrex::Real rhoL, amrex::Real uL, amrex::Real pL, amrex::Real cL,
    amrex::Real rhoR, amrex::Real uR, amrex::Real pR, amrex::Real cR)
{
    const amrex::Real p_pvrs = 0.5 * (pL + pR) - 0.125 * (uR - uL) * (rhoL + rhoR) * (cL + cR);
    return amrex::max<amrex::Real>(p_pvrs, 1.0);
}

// Main HLLC flux function
// Input: primitive states (rho, u, p, e) + EOS params for each side
// Output: fluxes (mass, momentum, energy) at the face
template <int NSPEC>
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void twophase_hllc_flux(
    amrex::Real rhoL, amrex::Real uL, amrex::Real pL, amrex::Real eL,
    const amrex::Real* YL,
    const PhaseEOSParams& eosL,
    amrex::Real rhoR, amrex::Real uR, amrex::Real pR, amrex::Real eR,
    const amrex::Real* YR,
    const PhaseEOSParams& eosR,
    amrex::Real& flux_rho,
    amrex::Real* flux_rhoY,
    amrex::Real& flux_u,
    amrex::Real& flux_eden,
    amrex::Real& flux_eint,
    amrex::Real& ustar,
    amrex::Real* Ystar)
{
    const amrex::Real cL = twophase_soundspeed(rhoL, pL, eosL);
    const amrex::Real cR = twophase_soundspeed(rhoR, pR, eosR);

    // Pressure estimate (PVRS)
    const amrex::Real pstar = twophase_pvrs(rhoL, uL, pL, cL, rhoR, uR, pR, cR);

    // Wave speed estimates with stiffened-gas compatible q_k
    // q_k = 1 for rarefaction; > 1 for shock
    auto wave_q = [](amrex::Real pstar_val, amrex::Real pk, amrex::Real gk) {
        if (pstar_val <= pk) return 1.0;
        return std::sqrt(1.0 + (gk + 1.0) / (2.0 * gk) * (pstar_val / pk - 1.0));
    };
    const amrex::Real qL = wave_q(pstar, pL, eosL.gamma);
    const amrex::Real qR = wave_q(pstar, pR, eosR.gamma);

    const amrex::Real SL = uL - cL * qL;
    const amrex::Real SR = uR + cR * qR;

    // Contact wave speed (HLLC, Toro Eq 10.37)
    const amrex::Real denom = rhoL * (SL - uL) - rhoR * (SR - uR);
    const amrex::Real Sstar = (denom != 0.0)
        ? (pR - pL + rhoL * uL * (SL - uL) - rhoR * uR * (SR - uR)) / denom
        : 0.5 * (uL + uR);

    // Star region states
    const amrex::Real rhoL_star = rhoL * (SL - uL) / (SL - Sstar);
    const amrex::Real rhoR_star = rhoR * (SR - uR) / (SR - Sstar);

    // Energy: equi-energy closure (DEFER: 3.9 can add temperature equilibrium)
    const amrex::Real EL = 0.5 * uL * uL + eL;
    const amrex::Real ER = 0.5 * uR * uR + eR;

    // Upwind: choose state based on wave speeds
    amrex::Real flux_rho_tmp, flux_u_tmp, flux_E_tmp;
    amrex::Real rho_face, u_face, p_face;
    amrex::Real Y_face[NSPEC];

    if (SL >= 0.0) {
        // Supersonic left
        flux_rho_tmp = rhoL * uL;
        flux_u_tmp = rhoL * uL * uL + pL;
        flux_E_tmp = (rhoL * EL + pL) * uL;
        for (int n = 0; n < NSPEC; n++) { Y_face[n] = YL[n]; }
        u_face = uL;
        p_face = pL;
    } else if (Sstar >= 0.0) {
        // Left star region
        flux_rho_tmp = rhoL * uL + SL * (rhoL_star - rhoL);
        flux_u_tmp = (rhoL * uL * uL + pL) + SL * (rhoL_star * Sstar - rhoL * uL);
        flux_E_tmp = (rhoL * EL + pL) * uL + SL * (rhoL_star * (0.5*Sstar*Sstar + eL + (pstar-pL)/(rhoL_star*(eosL.gamma-1.0))) - rhoL * EL);
        for (int n = 0; n < NSPEC; n++) { Y_face[n] = YL[n]; }
        u_face = Sstar;
        p_face = pstar;
    } else if (SR >= 0.0) {
        // Right star region
        flux_rho_tmp = rhoR * uR + SR * (rhoR_star - rhoR);
        flux_u_tmp = (rhoR * uR * uR + pR) + SR * (rhoR_star * Sstar - rhoR * uR);
        flux_E_tmp = (rhoR * ER + pR) * uR + SR * (rhoR_star * (0.5*Sstar*Sstar + eR + (pstar-pR)/(rhoR_star*(eosR.gamma-1.0))) - rhoR * ER);
        for (int n = 0; n < NSPEC; n++) { Y_face[n] = YR[n]; }
        u_face = Sstar;
        p_face = pstar;
    } else {
        // Supersonic right
        flux_rho_tmp = rhoR * uR;
        flux_u_tmp = rhoR * uR * uR + pR;
        flux_E_tmp = (rhoR * ER + pR) * uR;
        for (int n = 0; n < NSPEC; n++) { Y_face[n] = YR[n]; }
        u_face = uR;
        p_face = pR;
    }

    flux_rho = flux_rho_tmp;
    flux_u = flux_u_tmp;
    flux_eden = flux_E_tmp;
    flux_eint = flux_rho_tmp * eL;  // simplified
    ustar = u_face;
    for (int n = 0; n < NSPEC; n++) {
        flux_rhoY[n] = flux_rho_tmp * Y_face[n];
        Ystar[n] = Y_face[n];
    }
}
```

---

## 3. 修改 `Riemann.H` — 添加分派逻辑

在 `riemann()` 函数开头，检测是否需要两相处理：

```cpp
// After computing cl, cr:
#if NUM_ADV > 0
  // Check if phases differ across face — dispatch to HLLC if so
  const bool has_liquid_L = (YL[0] > 0.01);  // or pass alpha explicitly
  const bool has_liquid_R = (YR[0] > 0.01);  // NOTE: these are species, need alpha from caller
  // For now: caller passes alphaL/alphaR separately, detected here
#endif
```

**简化方案**：不修改 `riemann()` 签名。在 MOL.cpp / Godunov.H 的**调用点**做分派：
- 如果 α_L > ε 或 α_R > ε → 调用 `twophase_hllc_flux`
- 否则 → 调用现有 `riemann`

这样完全不碰 `Riemann.H`，降低风险。

---

## 4. 修改 MOL.cpp / Godunov.H 的调用点

在 MOL.cpp 的 `pc_compute_hyp_mol_flux` 中，Riemann 调用前：

```cpp
const amrex::Real alphaL = q(ivm, QFA);
const amrex::Real alphaR = q(iv, QFA);
const bool is_twophase = (alphaL > VOF_TINY || alphaR > VOF_TINY);

if (is_twophase) {
    twophase_hllc_flux<NUM_SPECIES>(...);
} else {
    riemann(...);  // existing solver
}
```

---

## 5. 单元测试

`test/unit/test_twophase_hllc.cpp`：

| 测试 | 内容 |
|:--:|------|
| 1 | 纯气-纯气 → 与现有 riemann 一致 |
| 2 | 纯液-纯液 → HLLC 不崩，守恒 |
| 3 | 气-液界面 → p* > 0, 波速正确 |
| 4 | 激波管验证（气-气，已知解析解） |
| 5 | 声速兼容 stiffened-gas |

---

## 6. 交付清单

| 文件 | 操作 |
|------|:--:|
| `TwoPhaseHLLC.H` | 新增 |
| `twophase_modules.H` | 修改（加 include） |
| `MOL.cpp` | 修改（分派逻辑） |
| `Godunov.H` | 修改（分派逻辑） |
| `test_twophase_hllc.cpp` | 新增 |

**约 250 行新代码 + 30 行修改。**
