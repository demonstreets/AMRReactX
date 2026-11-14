#include <PeleLMeX.H>
#include <AMReX_TagBox.H>
#include <AMReX_REAL.H>
#ifdef AMREX_USE_EB
#include <AMReX_EBAmrUtil.H>
#endif


namespace {

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real codex_abs(amrex::Real value) noexcept
{
  return value >= 0.0 ? value : -value;
}

} // namespace

void
PeleLM::ErrorEst(
  int lev, amrex::TagBoxArray& tags, amrex::Real time, int /*ng*/)
{
  BL_PROFILE("PeleLMeX::ErrorEst()");

#ifdef AMREX_USE_EB
  // Tag EB up to m_EB_refine_LevMax-1 if Static or
  //              m_EB_refine_LevAdapt-1 if Adaptive
  if (
    (m_EB_refine_type == "Static" && lev < m_EB_refine_LevMax) ||
    (m_EB_refine_type == "Adaptive" && lev < m_EB_refine_LevAdapt)) {
    const amrex::MultiFab& state = (getLevelDataPtr(lev, AmrNewTime))->state;
    TagCutCells(tags, state);
  }
#endif



  if (m_plan_amr_tagging != 0 && lev <= m_plan_amr_max_level) {
    const amrex::Real velGrad = m_plan_amr_velocity_gradient;
    const amrex::Real tempGrad = m_plan_amr_temperature_gradient;
    const amrex::Real specGrad = m_plan_amr_species_gradient;
    const amrex::Real alphaCurv = m_plan_amr_interface_curvature;
    const bool useVel = velGrad > 0.0;
    const bool useTemp = tempGrad > 0.0;
    const bool useSpec = specGrad > 0.0;
    const bool useAlpha = alphaCurv > 0.0;

    if (useVel || useTemp || useSpec || useAlpha) {
      const amrex::MultiFab& state = (getLevelDataPtr(lev, AmrNewTime))->state;
      const auto dx = geom[lev].CellSizeArray();
      const amrex::Real inv2dx = 0.5 / dx[0];
#if AMREX_SPACEDIM > 1
      const amrex::Real inv2dy = 0.5 / dx[1];
#else
      const amrex::Real inv2dy = 0.0;
#endif
#if AMREX_SPACEDIM > 2
      const amrex::Real inv2dz = 0.5 / dx[2];
#else
      const amrex::Real inv2dz = 0.0;
#endif
      const amrex::Real velGrad2 = velGrad * velGrad;
      const amrex::Real tempGrad2 = tempGrad * tempGrad;
      const amrex::Real specGrad2 = specGrad * specGrad;

#ifdef AMREX_USE_OMP
#pragma omp parallel if (amrex::Gpu::notInLaunchRegion())
#endif
      for (amrex::MFIter mfi(tags, amrex::TilingIfNotGPU()); mfi.isValid(); ++mfi) {
        const auto& bx = mfi.tilebox();
        const auto tag = tags.array(mfi);
        const auto sarr = state.const_array(mfi);
        amrex::ParallelFor(
          bx, [=] AMREX_GPU_HOST_DEVICE(int i, int j, int k) noexcept {
            bool setTag = false;
            if (useVel) {
              amrex::Real grad2 = 0.0;
              for (int n = VELX; n < VELX + AMREX_SPACEDIM; ++n) {
                const amrex::Real gx = (sarr(i + 1, j, k, n) - sarr(i - 1, j, k, n)) * inv2dx;
#if AMREX_SPACEDIM > 1
                const amrex::Real gy = (sarr(i, j + 1, k, n) - sarr(i, j - 1, k, n)) * inv2dy;
#else
                const amrex::Real gy = 0.0;
#endif
#if AMREX_SPACEDIM > 2
                const amrex::Real gz = (sarr(i, j, k + 1, n) - sarr(i, j, k - 1, n)) * inv2dz;
#else
                const amrex::Real gz = 0.0;
#endif
                grad2 += gx * gx + gy * gy + gz * gz;
              }
              setTag = setTag || grad2 >= velGrad2;
            }
            if (useTemp) {
              const amrex::Real gx = (sarr(i + 1, j, k, TEMP) - sarr(i - 1, j, k, TEMP)) * inv2dx;
#if AMREX_SPACEDIM > 1
              const amrex::Real gy = (sarr(i, j + 1, k, TEMP) - sarr(i, j - 1, k, TEMP)) * inv2dy;
#else
              const amrex::Real gy = 0.0;
#endif
#if AMREX_SPACEDIM > 2
              const amrex::Real gz = (sarr(i, j, k + 1, TEMP) - sarr(i, j, k - 1, TEMP)) * inv2dz;
#else
              const amrex::Real gz = 0.0;
#endif
              setTag = setTag || (gx * gx + gy * gy + gz * gz) >= tempGrad2;
            }
            if (useSpec && NUM_SPECIES > 0) {
              const int n = FIRSTSPEC;
              const amrex::Real gx = (sarr(i + 1, j, k, n) - sarr(i - 1, j, k, n)) * inv2dx;
#if AMREX_SPACEDIM > 1
              const amrex::Real gy = (sarr(i, j + 1, k, n) - sarr(i, j - 1, k, n)) * inv2dy;
#else
              const amrex::Real gy = 0.0;
#endif
#if AMREX_SPACEDIM > 2
              const amrex::Real gz = (sarr(i, j, k + 1, n) - sarr(i, j, k - 1, n)) * inv2dz;
#else
              const amrex::Real gz = 0.0;
#endif
              setTag = setTag || (gx * gx + gy * gy + gz * gz) >= specGrad2;
            }
            if (useAlpha) {
              const int n = FIRSTSPEC;
              const amrex::Real d2x = (sarr(i + 1, j, k, n) - 2.0 * sarr(i, j, k, n) + sarr(i - 1, j, k, n)) / (dx[0] * dx[0]);
#if AMREX_SPACEDIM > 1
              const amrex::Real d2y = (sarr(i, j + 1, k, n) - 2.0 * sarr(i, j, k, n) + sarr(i, j - 1, k, n)) / (dx[1] * dx[1]);
#else
              const amrex::Real d2y = 0.0;
#endif
#if AMREX_SPACEDIM > 2
              const amrex::Real d2z = (sarr(i, j, k + 1, n) - 2.0 * sarr(i, j, k, n) + sarr(i, j, k - 1, n)) / (dx[2] * dx[2]);
#else
              const amrex::Real d2z = 0.0;
#endif
              setTag = setTag || codex_abs(d2x + d2y + d2z) >= alphaCurv;
            }
            if (setTag) {
              tag(i, j, k) = amrex::TagBox::SET;
            }
          });
      }
    }
  }

  for (const auto& errTag : errTags) {
    std::unique_ptr<amrex::MultiFab> mf;
    if (!errTag.Field().empty()) {
      mf = deriveComp(errTag.Field(), time, lev, errTag.NGrow());
    }
    errTag(
      tags, mf.get(), amrex::TagBox::CLEAR, amrex::TagBox::SET, time, lev,
      geom[lev]);
  }

#ifdef AMREX_USE_EB
  // Untag covered cells
#ifdef AMREX_USE_OMP
#pragma omp parallel if (amrex::Gpu::notInLaunchRegion())
#endif
  for (amrex::MFIter mfi(tags, amrex::TilingIfNotGPU()); mfi.isValid(); ++mfi) {
    const auto& bx = mfi.tilebox();
    auto tag = tags.array(mfi);
    auto vfrac = EBFactory(lev).getVolFrac().const_array(mfi);
    amrex::ParallelFor(
      bx, [tag, vfrac] AMREX_GPU_HOST_DEVICE(int i, int j, int k) {
        if (vfrac(i, j, k) <= 0.0) {
          tag(i, j, k) = amrex::TagBox::CLEAR;
        }
      });
  }

  // Untag cell close to EB
  if (m_EB_refine_type == "Static" && lev >= m_EB_refine_LevMax) {
    // Get distance function at current level
    amrex::MultiFab signDist(
      grids[lev], dmap[lev], 1, 0, amrex::MFInfo(), EBFactory(lev));
    getEBDistance(lev, signDist);

    // Estimate how far I need to derefine
    constexpr amrex::Real sqrt2 = 1.4142135623730951;
    const amrex::Real diagFac = sqrt2 * m_derefineEBBuffer;
    amrex::Real clearTagDist =
      Geom(m_EB_refine_LevMax).CellSize(0) *
      static_cast<amrex::Real>(nErrorBuf(m_EB_refine_LevMax)) * diagFac;
    for (int ilev = m_EB_refine_LevMax + 1; ilev <= finest_level; ++ilev) {
      clearTagDist += static_cast<amrex::Real>(nErrorBuf(ilev)) *
                      Geom(m_EB_refine_LevMax).CellSize(0) * diagFac;
    }

    // Untag cells too close to EB
#ifdef AMREX_USE_OMP
#pragma omp parallel if (amrex::Gpu::notInLaunchRegion())
#endif
    for (amrex::MFIter mfi(tags, amrex::TilingIfNotGPU()); mfi.isValid();
         ++mfi) {
      const auto& bx = mfi.tilebox();
      const auto& dist = signDist.const_array(mfi);
      auto tag = tags.array(mfi);
      amrex::ParallelFor(
        bx,
        [dist, clearTagDist, tag] AMREX_GPU_HOST_DEVICE(int i, int j, int k) {
          if (dist(i, j, k) < clearTagDist) {
            tag(i, j, k) = amrex::TagBox::CLEAR;
          }
        });
    }
  }
#endif
}
