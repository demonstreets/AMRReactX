# Phase 3.9 — CSF 表面张力（Continuum Surface Force）

> 日期：2026-06-14 | 前置：3.5b VOF+MULES ✅、3.8 HLLC ✅

---

## 0. 算法

Brackbill 1992 CSF 模型：

```
F_s = σ · κ · ∇α

其中：
  n = ∇α / |∇α|          （界面法向，已有 vof_youngs_normal）
  κ = -∇·n               （曲率）
  δ_s = |∇α|              （界面 delta 函数，隐含在 ∇α 中）
  σ = 表面张力系数 [N/m]
```

**在 PeleC 中的位置**：作为动量方程的体力源项，加到 `sources_for_hydro`（Godunov 路径）或 MOL flux 路径。

---

## 1. 新增文件

### 1.1 `src/academic/twophase/CSF.H`（~100 行）

```cpp
#pragma once
#include <AMReX_REAL.H>
#include <AMReX_Gpu.H>
#include <AMReX_Array4.H>
#include "StiffenedGas.H"  // for VOF_TINY via VOF_Constants

// CSF surface tension force at a cell (i,j,k)
// Returns volumetric force vector (fx, fy, fz) [N/m³]
// sigma = surface tension coefficient [N/m]
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void csf_force(
    int i, int j, int k,
    const amrex::Array4<const amrex::Real>& alpha,  // volume fraction field
    const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx,
    amrex::Real sigma,
    amrex::Real& fx, amrex::Real& fy, amrex::Real& fz)
{
    // Step 1: Compute ∇α at cell center (Youngs central difference)
    amrex::Real nx, ny, nz;
    vof_youngs_normal(i, j, k, alpha, nx, ny, nz);  // returns normalized n

    // |∇α| for delta function
    const amrex::Real dax = 0.5 * (alpha(i+1,j,k,QFA) - alpha(i-1,j,k,QFA));
    const amrex::Real day = 0.5 * (alpha(i,j+1,k,QFA) - alpha(i,j-1,k,QFA));
#if AMREX_SPACEDIM == 3
    const amrex::Real daz = 0.5 * (alpha(i,j,k+1,QFA) - alpha(i,j,k-1,QFA));
#else
    const amrex::Real daz = 0.0;
#endif
    const amrex::Real grad_alpha_mag = std::sqrt(
        (dax/dx[0])*(dax/dx[0]) + (day/dx[1])*(day/dx[1]) + (daz/dx[2])*(daz/dx[2]));

    // Skip if not near interface
    if (grad_alpha_mag < 1.0 / amrex::max(amrex::max(dx[0], dx[1]), 
        AMREX_D_PICK(dx[2], dx[2], dx[2]))) {
        fx = fy = fz = 0.0;
        return;
    }

    // Step 2: Compute curvature κ = -∇·n
    // n is already normalized by vof_youngs_normal
    amrex::Real nxR, nyR, nzR, nxL, nyL, nzL;
    vof_youngs_normal(i+1, j, k, alpha, nxR, nyR, nzR);
    vof_youngs_normal(i-1, j, k, alpha, nxL, nyL, nzL);
    const amrex::Real dnxd = (nxR - nxL) / (2.0 * dx[0]);

    vof_youngs_normal(i, j+1, k, alpha, nxR, nyR, nzR);
    vof_youngs_normal(i, j-1, k, alpha, nxL, nyL, nzL);
    const amrex::Real dnyd = (nyR - nyL) / (2.0 * dx[1]);

#if AMREX_SPACEDIM == 3
    vof_youngs_normal(i, j, k+1, alpha, nxR, nyR, nzR);
    vof_youngs_normal(i, j, k-1, alpha, nxL, nyL, nzL);
    const amrex::Real dnzd = (nzR - nzL) / (2.0 * dx[2]);
#else
    const amrex::Real dnzd = 0.0;
#endif

    const amrex::Real kappa = -(dnxd + dnyd + dnzd);

    // Step 3: CSF force = σ · κ · ∇α
    const amrex::Real force_mag = sigma * kappa;
    fx = force_mag * dax / dx[0];
    fy = force_mag * day / dx[1];
    fz = force_mag * daz / dx[2];
}
```

### 1.2 更新 `twophase_modules.H`

加 `#include "CSF.H"`

---

## 2. 集成到 PeleC

### 方案 A：Godunov 路径（`Hydro.cpp`）

在 `construct_hydro_source()` 中，`sources_for_hydro.setVal(0.0)` 之后、`FillBoundary` 之前，加 CSF 循环：

```cpp
// CSF surface tension source term
#if NUM_ADV > 0
{
    const amrex::Real sigma = 0.072; // water-air [N/m], from prob_parm
    const amrex::MultiFab& S_new = get_new_data(State_Type);
    for (MFIter mfi(sources_for_hydro); mfi.isValid(); ++mfi) {
        const Box& bx = mfi.validbox();
        auto const& src = sources_for_hydro.array(mfi);
        auto const& q = ...; // need primitive alpha field
        // or directly from conserved state:
        auto const& state = S_new.const_array(mfi);
        
        amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE(int i, int j, int k) {
            amrex::Real fx, fy, fz;
            // Need alpha array — use state and derive alpha = state(UFA)/state(URHO)
            // Build a temporary alpha Array4 from the state... 
            // 
            // Simpler approach: CSF is computed as a separate MultiFab,
            // filled by calling csf_force on the primitive alpha field.
        });
    }
}
#endif
```

**简化方案**：不内联到 Hydro.cpp。提供一个独立的 `fill_csf_source` 函数，在 `construct_hydro_source` 中调用：

```cpp
// In CSF.H:
void fill_csf_source(
    const amrex::MultiFab& alpha,    // primitive alpha (cell-centered)
    const amrex::Geometry& geom,
    amrex::Real sigma,
    amrex::MultiFab& force_mf);     // output: 3-component force (fx, fy, fz)
```

然后在 `Hydro.cpp` 中（sources_for_hydro 的 ParallelFor 循环内）：
```cpp
const auto& force_arr = csf_force_mf.const_array(mfi);
src(i, j, k, UMX) += force_arr(i, j, k, 0);
src(i, j, k, UMY) += force_arr(i, j, k, 1);
src(i, j, k, UMZ) += force_arr(i, j, k, 2);
```

---

## 3. 单元测试

`test/unit/test_csf.cpp`：

| 测试 | 内容 |
|:--:|------|
| 1 | 均匀场 α=0 → 力为零 |
| 2 | 均匀场 α=1 → 力为零 |
| 3 | 1D 线性 α 梯度 → κ=0（平面界面），力为零 |
| 4 | 2D 圆形液滴 → κ > 0，力指向中心（内聚） |
| 5 | 力大小 ∝ σ（正比校验） |
| 6 | 弯月面界面 → κ 符号正确 |

---

## 4. 交付清单

| 文件 | 操作 |
|------|:--:|
| `CSF.H` | 新增（~100 行） |
| `twophase_modules.H` | 修改（+1 include） |
| `Hydro.cpp` | 修改（~15 行，加 CSF 源项调用） |
| `test_csf.cpp` | 新增（~200 行） |

**约 320 行新代码。**
