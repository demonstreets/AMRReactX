# Phase 3.7 — 两相状态方程（理想气体 + Stiffened-Gas）

> 日期：2026-06-13 | 前置：3.5b VOF+MULES ✅
> 🔴 传给 3.8 的契约：等温/等能量平衡模型 → 3.7 不做，3.8 实现

---

## 0. 范围界定

**3.7 只做**：
- Stiffened-Gas 液体 EOS 独立模块
- 两相混合物 EOS 包装器（调用气体 EOS + 液体 EOS → 等压闭合）
- 修改 `pc_ctoprim`：α > ε 时启用混合物 EOS
- 纯相极限验证

**3.7 不做（交给 3.8）**：
- 🔴 等温平衡 / 等能量平衡的能量分配模型
- 🔴 两相 Riemann 求解器（HLLC）
- 🔴 界面单元的迭代温度求解
- 🔴 表面张力（3.9）

**3.7 的混合物闭合假设（临时，3.8 替换）**：
- 等压：p_gas = p_liquid = p
- 温度：T_gas = T_liquid = T（先用等温，3.8 换真正的能量平衡）
- 密度：α 体积加权 → ρ = (1-α)ρ_gas + α ρ_liquid
- 内能：从各相 EOS 反推 → e_gas(ρ_gas, T), e_liquid(ρ_liquid, T) → e = (1-α)e_gas + α e_liquid

---

## 1. 新增文件

### 1.1 `src/academic/twophase/StiffenedGas.H`（~80 行）

```cpp
// Stiffened-gas EOS: p = (gamma - 1) * rho * e - gamma * p_inf
// Parameters: gamma_l (typically 1.1-7.0), p_inf (typically 1e8-1e9 Pa for water-like)

struct StiffenedGasParams {
    amrex::Real gamma;   // ratio of specific heats, γ_l
    amrex::Real p_inf;   // background pressure, p_∞ [Pa]
};

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real sg_p_from_re(const StiffenedGasParams& sg,
                          amrex::Real rho, amrex::Real e) {
    return (sg.gamma - 1.0) * rho * e - sg.gamma * sg.p_inf;
}

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real sg_e_from_rp(const StiffenedGasParams& sg,
                          amrex::Real rho, amrex::Real p) {
    return (p + sg.gamma * sg.p_inf) / ((sg.gamma - 1.0) * rho);
}

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real sg_T_from_re(const StiffenedGasParams& sg,
                          amrex::Real rho, amrex::Real e,
                          amrex::Real cv) {
    // T = e / cv (simplified — incompressible liquid approximation)
    return e / cv;
}

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real sg_cs(const StiffenedGasParams& sg,
                   amrex::Real rho, amrex::Real p) {
    return std::sqrt(sg.gamma * (p + sg.p_inf) / rho);
}
```

### 1.2 `src/academic/twophase/TwoPhaseEOS.H`（~120 行）

混合物包装器。关键函数：

```cpp
// Given: ρ_total, e_total, α, gas_massfrac[], gas_EOS
// Returns: p, T, cs, dpdr_e, dpde, gam1
// Closure: isobaric p_g = p_l, isothermal T_g = T_l (DEFER: 3.8 replaces T assumption)

struct TwoPhaseState {
    amrex::Real p;
    amrex::Real T;
    amrex::Real cs;
    amrex::Real gam1;
    amrex::Real dpdr_e;
    amrex::Real dpde;
};

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
TwoPhaseState twophase_mixture_eos(
    const amrex::Real rho_total,
    const amrex::Real e_total,
    const amrex::Real alpha,
    const amrex::Real* massfrac,
    const pele::physics::eos::Fuego& gas_eos,  // or template
    const StiffenedGasParams& sg,
    const amrex::Real cv_liquid,
    const amrex::Real alpha_tiny = 1.0e-8)
{
    TwoPhaseState result;

    if (alpha < alpha_tiny) {
        // Pure gas — delegate to Fuego
        gas_eos.REY2T(rho_total, e_total, massfrac, result.T);
        gas_eos.RTY2P(rho_total, result.T, massfrac, result.p);
        gas_eos.RTY2Cs(rho_total, result.T, massfrac, result.cs);
        gas_eos.RTY2G(rho_total, result.T, massfrac, result.gam1);
        gas_eos.RTY2dpde_dpdre(rho_total, result.T, massfrac, result.dpde, result.dpdr_e);
    } else if (alpha > 1.0 - alpha_tiny) {
        // Pure liquid — StiffenedGas
        result.p = sg_p_from_re(sg, rho_total, e_total);
        result.T = sg_T_from_re(sg, rho_total, e_total, cv_liquid);
        result.cs = sg_cs(sg, rho_total, result.p);
        result.gam1 = sg.gamma;
        // Simplified derivatives for pure liquid
        result.dpdr_e = (sg.gamma - 1.0) * e_total;
        result.dpde = (sg.gamma - 1.0) * rho_total;
    } else {
        // 🔴 INTERFACE CELL — simple isobaric+isothermal closure (3.8 replaces)
        // Assume: ρ_liquid = ρ_liquid_0 (incompressible baseline)
        // This is a placeholder. 3.8 will implement proper energy partition.
        const amrex::Real rho_liquid = rho_total; // simplified
        const amrex::Real rho_gas = rho_total;    // simplified
        const amrex::Real e_gas = e_total;
        const amrex::Real e_liquid = e_total;

        result.p = sg_p_from_re(sg, rho_liquid, e_liquid);
        result.T = sg_T_from_re(sg, rho_liquid, e_liquid, cv_liquid);
        result.cs = sg_cs(sg, rho_total, result.p);
        result.gam1 = sg.gamma;
        result.dpdr_e = (sg.gamma - 1.0) * e_total;
        result.dpde = (sg.gamma - 1.0) * rho_total;
    }

    return result;
}
```

### 1.3 `src/academic/twophase/twophase_modules.H`（聚合头）

```cpp
#pragma once
#include "StiffenedGas.H"
#include "TwoPhaseEOS.H"
```

---

## 2. 修改 `pc_ctoprim`（PeleCUtilities.H ~L242）

在现有 EOS 调用段，插入两相逻辑：

```cpp
// After computing massfrac[] and before calling eos.REY2T:

#if NUM_ADV > 0
  const amrex::Real alpha = q(i, j, k, QFA);  // VOF volume fraction
#else
  const amrex::Real alpha = 0.0;
#endif

  if (alpha < 1e-8) {
    // Pure gas — original Fuego/GammaLaw path (unchanged)
    eos.Y2WBAR(massfrac, wbar);
    eos.REY2T(rho, e, massfrac, T);
    eos.RTY2P(rho, T, massfrac, p);
    eos.RTY2Cs(rho, T, massfrac, cs);
    eos.RTY2G(rho, T, massfrac, gam1);
    eos.RTY2dpde_dpdre(rho, T, massfrac, dpde, dpdr_e);
  } else {
    // Two-phase mixture EOS
    auto twophase = twophase_mixture_eos(rho, e, alpha, massfrac,
                                          eos, sg_params, cv_liquid);
    T = twophase.T;
    p = twophase.p;
    cs = twophase.cs;
    gam1 = twophase.gam1;
    dpdr_e = twophase.dpdr_e;
    dpde = twophase.dpde;
  }
```

---

## 3. 参数定义

在 `prob_parm.H` 或专用头文件中：

```cpp
struct TwoPhaseParams {
    amrex::Real gamma_liquid = 4.4;      // water-like
    amrex::Real p_inf_liquid = 6.0e8;    // [Pa]
    amrex::Real cv_liquid = 4180.0;      // J/(kg·K) for water
};
```

---

## 4. 单元测试

`test/unit/test_twophase_eos.cpp`：

| 测试 | 内容 |
|:--:|------|
| 1 | 纯气体极限（α=0）→ 输出与 Fuego 一致 |
| 2 | 纯液体极限（α=1）→ p, cs 与 stiffened-gas 解析解一致 |
| 3 | α=1e-16 → 触发纯气体路径 |
| 4 | α=0.9999 → 触发纯液体路径 |
| 5 | 声速正定性：cs > 0 |
| 6 | 压力正定性：p > 0 |
| 7 | 界面区（α=0.5）→ 不崩溃、不 NaN |

---

## 5. 交付清单

| 文件 | 操作 |
|------|:--:|
| `StiffenedGas.H` | 新增 |
| `TwoPhaseEOS.H` | 新增 |
| `twophase_modules.H` | 新增 |
| `test_twophase_eos.cpp` | 新增 |
| `PeleCUtilities.H` | 修改 `pc_ctoprim` |

**约 250 行新代码 + 20 行修改。**

---

## 6. 🔴 3.8 接口契约（必须写在 PROGRESS.md）

```
Phase 3.7 → 3.8 交接：
- 3.7 提供了 StiffenedGas + TwoPhaseMixture EOS 模块
- 界面单元使用了临时等温+等压闭合（ρ_liquid = ρ_total 简化）
- 3.8 需要：
  1. 实现两相 HLLC Riemann 求解器
  2. 替换界面单元的能量分配模型（等温 → 等能量 or 等温平衡迭代求解）
  3. 两相 HLLC 的波速估计需用混合物声速（来自 TwoPhaseEOS）
- 3.7 的 twophase_mixture_eos 接口签名保持不变，3.8 只替换内部实现
```
