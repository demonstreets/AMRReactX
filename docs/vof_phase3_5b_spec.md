# Phase 3.5b — VOF MULES 压缩项

> FCT 底板 (3.5a) 已验证通过。3.5b 只做增量修改。

## 修改范围

只改 1 个文件：`src/academic/vof/VOF_FCT.H`，外加更新单元测试。

### 1. 填充 `vof_youngs_normal()` 骨架

当前是空函数。实现 Youngs (1982) 梯度法计算界面法向：

```cpp
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void vof_youngs_normal(
    int i, int j, int k,
    const amrex::Array4<const amrex::Real>& alpha,
    amrex::Real& nx, amrex::Real& ny, amrex::Real& nz)
{
    // Youngs method: central difference of alpha field
    // nx = (alpha(i+1,j,k) - alpha(i-1,j,k)) / (2*dx)  — but we don't have dx
    // Simplified: use grid-index differences
    nx = 0.5 * (alpha(i+1,j,k,QFA) - alpha(i-1,j,k,QFA));
    ny = 0.5 * (alpha(i,j+1,k,QFA) - alpha(i,j-1,k,QFA));
#if AMREX_SPACEDIM >= 3
    nz = 0.5 * (alpha(i,j,k+1,QFA) - alpha(i,j,k-1,QFA));
#else
    nz = 0.0;
#endif
    
    // Normalize
    amrex::Real nmag = std::sqrt(nx*nx + ny*ny + nz*nz);
    if (nmag > VOF_TINY) {
        nx /= nmag;
        ny /= nmag;
        nz /= nmag;
    } else {
        nx = 0.0; ny = 0.0; nz = 0.0;
    }
}
```

### 2. 新增 `vof_mules_compression_flux()` 函数

```cpp
// Compute MULES compression flux at a face.
// Called per face during flux assembly.
// u_face = face-normal velocity (positive from L to R)
// alphaL, alphaR = cell-centered alpha on left/right of face
// nmag_face = dot(normal, face_direction), where normal is interface normal at face center
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real vof_mules_compression_flux(
    amrex::Real u_face,
    amrex::Real flxrho,
    amrex::Real alphaL,
    amrex::Real alphaR,
    amrex::Real nmag_face)
{
    // Compression only acts at interface (alpha not 0 or 1)
    // and only in direction of interface normal
    const amrex::Real alpha_face = 0.5 * (alphaL + alphaR);
    const amrex::Real compression_factor = alpha_face * (1.0 - alpha_face);
    
    if (compression_factor < VOF_TINY || std::abs(nmag_face) < VOF_TINY)
        return 0.0;
    
    // Compression velocity magnitude: C_alpha * |u_face|, limited
    constexpr amrex::Real C_alpha = 1.0;
    const amrex::Real u_comp = C_alpha * std::abs(u_face);
    
    // Compression flux = rho * u_comp * nmag_face * alpha*(1-alpha)
    // Sign: nmag_face determines direction, compression_factor gives magnitude
    const amrex::Real sign_n = (nmag_face > 0.0) ? 1.0 : -1.0;
    return flxrho * u_comp * sign_n * compression_factor / std::max(std::abs(u_face), VOF_TINY);
}
```

### 3. 修改 `vof_fct_flux()` — 嵌入压缩通量

当前逻辑：
```
A = flux_high - flux_low
C = zalesak_limiter(A, ...)
flux = flux_low + C * A
```

修改后：
```
A = flux_high - flux_low + flux_compression
C = zalesak_limiter(A, ...)
flux = flux_low + C * A
```

具体改动：在 `vof_fct_flux` 中，计算完 `flux_low` 和 `flux_high` 之后、调 `vof_zalesak_limiter` 之前，加入压缩通量。

需要：
- 计算界面法向（调用 `vof_youngs_normal`，在面两侧格的中间取平均）
- 计算压缩通量
- 把压缩通量加到高阶通量上

关键改动段（在 vof_fct_flux 函数内，flux_high 计算完之后）：
```cpp
// ── MULES compression term ──
amrex::Real flux_comp = 0.0;
{
    // Interface normal from left and right cells (average)
    amrex::Real nxL, nyL, nzL, nxR, nyR, nzR;
    // Get left cell index
    const amrex::IntVect ivL{AMREX_D_DECL(
        i - (dir==0 ? 1 : 0), 
        j - (dir==1 ? 1 : 0), 
        k - (dir==2 ? 1 : 0))};
    const amrex::IntVect ivR{AMREX_D_DECL(i,j,k)}; // face is at i+1/2, so right cell is at face index
    
    vof_youngs_normal(ivL[0], ivL[1], ivL[2], alpha, nxL, nyL, nzL);
    vof_youngs_normal(ivR[0], ivR[1], ivR[2], alpha, nxR, nyR, nzR);
    
    // Face-centered normal (average)
    const amrex::Real nx_face = 0.5 * (nxL + nxR);
    const amrex::Real ny_face = 0.5 * (nyL + nyR);
    const amrex::Real nz_face = 0.5 * (nzL + nzR);
    
    // Normal component in face direction
    const amrex::Real nmag_face = 
        (dir == 0) ? nx_face : ((dir == 1) ? ny_face : nz_face);
    
    flux_comp = vof_mules_compression_flux(ustar, flxrho, alphaL, alphaR, nmag_face);
}

// Modified anti-diffusive flux includes compression
const amrex::Real flux_high_total = flux_high + flux_comp;

// Apply FCT limiter
return vof_zalesak_limiter(i, j, k, dir, alpha, flux_low, flux_high_total, dx, dt);
```

### 4. 更新单元测试

在 `test_vof_fct.cpp` 中新增 MULES 压缩项测试：
- 测试界面处（α=0.5）有法向分量 → 压缩生效
- 测试远离界面（α=0）→ 压缩为零
- 测试法向 perpendicular to face → 压缩最大
- 测试法向 parallel to face → 压缩为零

同时更新 `VOF_FCT.H` 需要的 include。

### 5. 验证算例

在 3.5a 的 `vof_advection_1D` 基础上：
- 添加 MULES 压缩项后重新编译
- 跑 500 步验证 α 仍有界且界面比纯 FCT 更锐

不需要新建算例，复用 3.5a 的。

## 验收标准

| 编号 | 条件 |
|:--:|------|
| AC1 | α ∈ [0,1] 不被破坏（FCT 限制器仍在工作） |
| AC2 | 界面过渡带比纯 FCT（3.5a）窄 |
| AC3 | 单元测试全部 PASS |
| AC4 | 代码编译通过，NUM_ADV=1 |
