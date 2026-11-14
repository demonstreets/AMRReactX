# TASK 3.10e: k-ε 壁面函数 + 源项核心化

## 背景

3.10d 完成了 k-ε 运行时集成（扩散增强、面心插值修复、aux clipping）。
`addKESourceTerms()` 已实现并正常工作。
但 **壁面函数完全缺失**：`m_ke_wall_functions` 参数在 Setup.cpp:498 读取了，却全 PeleLMeX 源码从未使用。

Phase 2.3 写了独立壁面函数库 `src/engineering/turbulence/wall_functions.H`（compute_utau, compute_k_wall, compute_eps_wall），但从未接入求解器。

## 改动 1：壁面函数 BC 实现 (~40 行)

### 1.1 新增方法声明
**文件**: `external/PeleLMeX/Source/PeleLMeX.H`
- 在 `addKESourceTerms` 声明附近（约 1805 行）添加：
```cpp
void applyKEWallFunctions();
```

### 1.2 新增方法实现
**文件**: `external/PeleLMeX/Source/PeleLMeX_Diffusion.cpp`
- 在 `addKESourceTerms` 函数后面添加 `applyKEWallFunctions()` 实现
- 算法：Launder-Spalding 标准壁面函数

```cpp
void
PeleLM::applyKEWallFunctions()
{
  if (m_ke_wall_functions == 0 || m_les_model != "kepsilon" || m_nAux < 2) return;
  
  BL_PROFILE("PeleLMeX::applyKEWallFunctions()");
  
  const amrex::Real kappa = m_ke_kappa;
  const amrex::Real C_mu = m_ke_C_mu;
  const amrex::Real B = 5.2;  // log-law constant
  const amrex::Real yplus_threshold = 11.225;
  const int max_iter = 20;
  const amrex::Real tol = 1e-6;
  
  for (int lev = 0; lev <= finest_level; ++lev) {
    auto* ldata_p = getLevelDataPtr(lev, AmrNewTime);
    const auto& geom = Geom(lev);
    const amrex::Real* dx = geom.CellSize();
    const amrex::Real* plo = geom.ProbLo();
    
    auto const& state_ma = ldata_p->state.const_arrays();
    auto const& aux_ma = ldata_p->auxiliaries.arrays();
    
    // Check which walls have wall-function BC
    const auto& bcs = m_bcrec_aux[0];  // aux component 0 = k
    // y_lo wall check
    bool has_y_lo_wall = (bcs[0].lo(1) == amrex::BCType::ext_dir || 
                           bcs[0].lo(1) == amrex::BCType::foextrap);
    
    if (has_y_lo_wall) {
      const amrex::Real y_p = plo[1] + 0.5 * dx[1];  // first cell center y
      amrex::Real nu_lam = 1.5e-5;  // air kinematic viscosity ~1.5e-5 m²/s
      
      for (amrex::MFIter mfi(ldata_p->auxiliaries, amrex::TilingIfNotGPU()); mfi.isValid(); ++mfi) {
        const amrex::Box& bx = mfi.tilebox();
        // Only process cells at j=0 (first interior from y_lo wall)
        if (!bx.smallEnd(1) == 0) continue;  // only bottom-most boxes
        
        amrex::Box wall_box = bx;
        wall_box.setSmall(1, 0);
        wall_box.setBig(1, 0);
        
        amrex::ParallelFor(wall_box, [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
          // Tangential velocity at first cell
          amrex::Real u_tau = 0.0;
          amrex::Real u_par = std::sqrt(
            state_ma[box_no](i,j,k,VELX) * state_ma[box_no](i,j,k,VELX) +
            state_ma[box_no](i,j,k,VELZ) * state_ma[box_no](i,j,k,VELZ));
          
          amrex::Real rho = state_ma[box_no](i,j,k,DENSITY);
          amrex::Real mu_lam = 1.8e-5;  // dynamic viscosity air
          amrex::Real nu = mu_lam / amrex::max(rho, 1e-10_rt);
          
          // Initial guess: u_tau = u_par / 20
          u_tau = u_par / 20.0_rt;
          amrex::Real yplus = y_p * u_tau / nu;
          
          // Newton-Raphson for log-law: u_par/u_tau - (1/kappa)*ln(yplus) - B = 0
          if (yplus > yplus_threshold) {
            bool converged = false;
            for (int iter = 0; iter < max_iter; ++iter) {
              amrex::Real f = u_par / u_tau - (1.0_rt / kappa) * std::log(yplus) - B;
              amrex::Real df = -u_par / (u_tau * u_tau) - 1.0_rt / (kappa * u_tau);
              amrex::Real du = -f / df;
              u_tau += du;
              yplus = y_p * u_tau / nu;
              if (std::abs(du / u_tau) < tol) {
                converged = true;
                break;
              }
            }
            if (!converged) {
              // Fallback: use laminar estimate
              u_tau = std::sqrt(nu * u_par / y_p);
            }
          } else {
            // Viscous sublayer: u_tau = sqrt(nu * u_par / y_p)
            u_tau = std::sqrt(nu * u_par / y_p);
          }
          
          // Set k and ε from wall functions
          aux_ma[box_no](i, j, k, 0) = u_tau * u_tau / std::sqrt(C_mu);       // k_wall
          aux_ma[box_no](i, j, k, 1) = u_tau * u_tau * u_tau / (kappa * y_p); // ε_wall
        });
      }
    }
  }
}
```

**注意**：上面的伪代码有几个需要修正的地方：
1. 需要用 `box_no` 索引（`aux_ma[box_no]` 是 MFIter 的 box index）
2. `bcs[0].lo(1)` 的 BC 类型检查需要查看 PeleLMeX 实际用什么 BC 类型表示 wall
3. 可能需要检查所有 6 个面（x_lo, x_hi, y_lo, y_hi, z_lo, z_hi），不只是 y_lo
4. 物理 BC 类型的检查和 AMReX BCType 的映射需要确认
5. `nu_lam` 应该从流场计算（μ/ρ）而非硬编码

**简化建议**：不检查 BC 类型，直接用 `amrex::Geometry::isPeriodic` + domain boundary 位置判断。对每个壁面方向（y_lo），处理 j=0 的第一层内部网格。

### 1.3 调用位置
**文件**: `external/PeleLMeX/Source/PeleLMeX_Advance.cpp`
- 在 SDC 迭代循环中，`fillPatchAux(AmrNewTime)` 之后，扩散求解之前
- 约在第 367 行（aux floor clipping 的位置）附近添加：
```cpp
// Apply k-ε wall functions at wall-adjacent cells
if (m_les_model == "kepsilon" && m_nAux >= 2 && m_ke_wall_functions > 0) {
  applyKEWallFunctions();
}
```

## 改动 2：源项代码整理 (~15 行)

### 2.1 提取 S² 计算为静态辅助函数
**文件**: `external/PeleLMeX/Source/PeleLMeX_Diffusion.cpp`
- 在 `addKESourceTerms` 之前，将 2D/3D 重复的速度梯度计算提取为：
```cpp
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
static amrex::Real computeStrainRateSq(
    const amrex::Array4<const amrex::Real>& state, int box_no, int i, int j, int k)
{
  // 3D strain rate S_ij * S_ij, then S² = 2 * S_ij * S_ij
  // ... (existing 3D code)
}
```
- `addKESourceTerms` 中替换为调用此函数

## 验证

1. 编译：`make clean && make -j8`（在 c3h8_flacs 或任意 k-ε 算例目录）
2. 默认 `ke_wall_functions = 0` → 壁面函数不生效，结果与之前完全一致
3. 设 `peleLM.ke_wall_functions = 1` → 壁面函数启用，y_lo 处 k 和 ε 被壁面函数覆盖
4. 100 步无 NaN/崩溃
5. k 场在 y_lo 壁面附近应有物理合理的值（不再均匀衰减到极小值）

## 关键路径
- PeleLMeX 源码: `/home/cj/my-pele/external/PeleLMeX/Source/`
- 独立壁面函数库: `/home/cj/my-pele/src/engineering/turbulence/wall_functions.H`
- c3h8_flacs 算例: `/home/cj/my-pele/examples/engineering/c3h8_flacs/`
- PeleLMeX.H 声明: 约 1805 行（addKESourceTerms 附近）
- PeleLMeX_Diffusion.cpp: addKESourceTerms 约 1886 行
- PeleLMeX_Advance.cpp: SDC 循环 aux 相关代码约 349-370 行
