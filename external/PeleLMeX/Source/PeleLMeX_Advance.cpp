#include <PeleLMeX.H>
#include <PeleLMeX_Utils.H>
#include <AMReX_MemProfiler.H>
#include <memory>

#include "pelelmex_prob.H"

namespace {

AMREX_GPU_DEVICE
AMREX_FORCE_INLINE
amrex::Real
pelelmex_aux_abs(const amrex::Real x) noexcept
{
  return (x >= 0.0) ? x : -x;
}

AMREX_GPU_DEVICE
AMREX_FORCE_INLINE
amrex::Real
pelelmex_aux_minmod(const amrex::Real a, const amrex::Real b) noexcept
{
  if (a * b <= 0.0) {
    return 0.0;
  }
  return (pelelmex_aux_abs(a) < pelelmex_aux_abs(b)) ? a : b;
}

AMREX_GPU_DEVICE
AMREX_FORCE_INLINE
amrex::Real
pelelmex_aux_clamp01(const amrex::Real a) noexcept
{
  return amrex::min(1.0, amrex::max(0.0, a));
}

AMREX_GPU_DEVICE
AMREX_FORCE_INLINE
amrex::Real
pelelmex_aux_limited_state(
  const amrex::Real donor,
  const amrex::Real delta_lo,
  const amrex::Real delta_hi,
  const amrex::Real face_sign) noexcept
{
  return pelelmex_aux_clamp01(
    donor + 0.5 * face_sign * pelelmex_aux_minmod(delta_lo, delta_hi));
}

} // namespace

void
PeleLM::Advance(const int is_initIter)
{
  BL_PROFILE("PeleLMeX::Advance()");

#ifdef AMREX_MEM_PROFILING
  // Memory profiler if compiled
  amrex::MemProfiler::report("STEP [" + std::to_string(m_nstep) + "]");
#endif

  // Start timing current time step
  const amrex::Real strt_time = amrex::ParallelDescriptor::second();

  //----------------------------------------------------------------
  BL_PROFILE_VAR("PeleLMeX::advance::setup", PLM_SETUP);
  //----------------------------------------------------------------

  // Deal with ambient pressure
  if (m_closed_chamber != 0) {
    m_pNew = m_pOld;
  }

  // Put together new typical values
  if ((is_initIter == 0) && m_nstep > 0 && m_nstep % m_resetTypValInt == 0) {
    setTypicalValues(AmrNewTime);
  }

  //----------------------------------------------------------------
  // Copy old <- new state
  copyStateNewToOld(1);
  copyPressNewToOld();
  //----------------------------------------------------------------

  //----------------------------------------------------------------
  // TIME
  // Compute time-step size
  m_dt = computeDt(is_initIter, AmrOldTime);

#ifdef PELE_USE_SPRAY
  // Create the state MF used for spray interpolation
  SpraySetState(m_dt);
#endif

  // Update time vectors
  for (int lev = 0; lev <= finest_level; ++lev) {
    m_t_old[lev] = m_cur_time;
    m_t_new[lev] = m_cur_time + m_dt;
  }
  //----------------------------------------------------------------

  if (m_verbose != 0) {
    amrex::Long ncells = 0;
    for (int lev = 0; lev <= finest_level; ++lev) {
      ncells += m_extSource[lev]->boxArray().numPts();
    }
    amrex::Print() << " STEP [" << m_nstep << "] - Time: " << m_cur_time
                   << ", dt " << m_dt << ", Ncells " << ncells << "\n";
  }

  checkMemory("Adv. start");

  //----------------------------------------------------------------
  // Data for the advance, only live for the duration of the advance
  std::unique_ptr<AdvanceDiffData> diffData;
  diffData = std::make_unique<AdvanceDiffData>(
    finest_level, grids, dmap, m_factory, m_nGrowAdv, m_use_wbar, m_use_soret,
    m_nAux);
  std::unique_ptr<AdvanceAdvData> advData;
  advData = std::make_unique<AdvanceAdvData>(
    finest_level, grids, dmap, m_factory, m_incompressible, m_nAux, m_nGrowAdv,
    m_nGrowMAC);

  for (int lev = 0; lev <= finest_level; ++lev) {
    m_extSource[lev]->setVal(0.);
  }
  // k-epsilon source term temporaries
  if (m_les_model == "kepsilon" && m_nAux >= 2) {
    m_ke_source.resize(finest_level + 1);
    for (int lev = 0; lev <= finest_level; ++lev) {
      if (!m_ke_source[lev]) {
        m_ke_source[lev] = std::make_unique<amrex::MultiFab>(
          grids[lev], dmap[lev], 2, 0, amrex::MFInfo(), *m_factory[lev]);
      }
      m_ke_source[lev]->setVal(0.);
    }
  }
  //----------------------------------------------------------------

  //----------------------------------------------------------------
  // Advance setup
  // Pre-SDC
  m_sdcIter = 0;

  // initialize temporals
  initTemporals();

  // Reset velocity flux on boundary faces if doing closed chamber
  if (m_closed_chamber != 0) {
    for (int idim = 0; idim < AMREX_SPACEDIM; ++idim) {
      m_domainUmacFlux[2 * idim] = 0.0;
      m_domainUmacFlux[2 * idim + 1] = 0.0;
    }
  }

  // Reset fluctuation warnings each time dt could change
  m_warned_clipped_recycle_avg_window_this_step = false;

  // fillpatch the t^{n} data
  averageDownState(AmrOldTime);
  fillPatchState(AmrOldTime);

  if (m_nAux > 0) {
    averageDownAux(AmrOldTime);
    fillPatchAux(AmrOldTime);
  }

  // compute t^{n} data
  calcViscosity(AmrOldTime);
  if (m_incompressible == 0) {
    calcDiffusivity(AmrOldTime);
#ifdef PELE_USE_PLASMA
    poissonSolveEF(AmrOldTime);
#endif
  }
  if (m_do_les) {
    calcTurbViscosity(AmrOldTime);
  }

  //----------------------------------------------------------------
  BL_PROFILE_VAR_STOP(PLM_SETUP);
  //----------------------------------------------------------------

  // External sources (soot, radiation, user defined, etc.)
  getExternalSources(is_initIter, AmrOldTime, AmrNewTime);

  if (m_incompressible == 0) {
    floorSpecies(AmrOldTime);

    //----------------------------------------------------------------
    BL_PROFILE_VAR("PeleLMeX::advance::mac", PLM_MAC);
    setThermoPress(AmrOldTime);
    BL_PROFILE_VAR_STOP(PLM_MAC);
    //----------------------------------------------------------------
    BL_PROFILE_VAR("PeleLMeX::advance::diffusion", PLM_DIFF);
    const amrex::Real fluxfact = (m_nSDCmax > 1) ? 0.5 : 0.0;
    computeDifferentialDiffusionTerms(AmrOldTime, diffData, 0, fluxfact);
    BL_PROFILE_VAR_STOP(PLM_DIFF);
    //----------------------------------------------------------------
  }

  // Initialize terms t^{np1,k} from t^{n}
  //----------------------------------------------------------------
  BL_PROFILE_VAR_START(PLM_SETUP);
  //----------------------------------------------------------------
  copyTransportOldToNew();
  if (m_incompressible == 0) {
    copyDiffusionOldToNew(diffData);
#ifdef PELE_USE_PLASMA
    ionDriftVelocity(advData);
#endif
  }

#if NUM_ODE > 0
  // Euler step for predicting ode qty at tnp1
  if (m_user_defined_ext_sources) {
    predictODEQty();
  }
#endif
  BL_PROFILE_VAR_STOP(PLM_SETUP);
  //----------------------------------------------------------------

  //----------------------------------------------------------------
  // Scalar advance
  if (m_incompressible != 0) {
    amrex::Real MACStart = 0.0;
    if (m_verbose > 1) {
      MACStart = amrex::ParallelDescriptor::second();
    }

    // Still need to get face velocities ...
    predictVelocity(advData);

    // ... and MAC-project face velocities, but no divu
    macProject(AmrOldTime, advData, {});

    // In incompressible mode the low-Mach SDC scalar path is skipped. Keep
    // auxiliary scalars live with finite-volume fluxes using MAC-projected face
    // velocities. Scheme 1 is first-order upwind; scheme 2 uses minmod MUSCL
    // face states for sharper bounded alpha transport.
    if (m_nAux > 0) {
      const auto aux_advect_v = convertToDeviceVector(m_aux_advect);
      const auto* aux_advect_d = aux_advect_v.dataPtr();
      const auto dt = m_dt;
      const int aux_advect_scheme = m_incompressible_aux_advect_scheme;
      for (int lev = 0; lev <= finest_level; ++lev) {
        auto* ldata_old_p = getLevelDataPtr(lev, AmrOldTime);
        auto* ldata_new_p = getLevelDataPtr(lev, AmrNewTime);
        const auto dx = geom[lev].CellSizeArray();
        const auto domain = geom[lev].Domain();
        const int ilo = domain.smallEnd(0);
        const int ihi = domain.bigEnd(0);
#if AMREX_SPACEDIM >= 2
        const int jlo = domain.smallEnd(1);
        const int jhi = domain.bigEnd(1);
#endif
#if AMREX_SPACEDIM == 3
        const int klo = domain.smallEnd(2);
        const int khi = domain.bigEnd(2);
#endif
#ifdef AMREX_USE_OMP
#pragma omp parallel if (amrex::Gpu::notInLaunchRegion())
#endif
        for (amrex::MFIter mfi(
               ldata_new_p->auxiliaries, amrex::TilingIfNotGPU());
             mfi.isValid(); ++mfi) {
          const amrex::Box& bx = mfi.tilebox();
          auto const& aux_old = ldata_old_p->auxiliaries.const_array(mfi);
          auto const& aux_new = ldata_new_p->auxiliaries.array(mfi);
          auto const& umac = advData->umac[lev][0].const_array(mfi);
#if AMREX_SPACEDIM >= 2
          auto const& vmac = advData->umac[lev][1].const_array(mfi);
#endif
#if AMREX_SPACEDIM == 3
          auto const& wmac = advData->umac[lev][2].const_array(mfi);
#endif
          amrex::ParallelFor(
            bx, m_nAux,
            [aux_old, aux_new, umac,
#if AMREX_SPACEDIM >= 2
             vmac,
#endif
#if AMREX_SPACEDIM == 3
             wmac,
#endif
             aux_advect_d, dx, dt, aux_advect_scheme, ilo, ihi
#if AMREX_SPACEDIM >= 2
             , jlo, jhi
#endif
#if AMREX_SPACEDIM == 3
             , klo, khi
#endif
             ] AMREX_GPU_DEVICE(int i, int j, int k, int n) noexcept {
              const amrex::Real a0 = aux_old(i, j, k, n);
              if (aux_advect_d[n] == 0) {
                aux_new(i, j, k, n) = a0;
                return;
              }

              const amrex::Real ux_hi = umac(i + 1, j, k);
              const amrex::Real ux_lo = umac(i, j, k);
              amrex::Real ax_hi = (ux_hi >= 0.0) ? a0 : aux_old(i + 1, j, k, n);
              amrex::Real ax_lo = (ux_lo >= 0.0) ? aux_old(i - 1, j, k, n) : a0;
              if (aux_advect_scheme == 2) {
                if (ux_hi >= 0.0) {
                  if (i > ilo && i < ihi) {
                    ax_hi = pelelmex_aux_limited_state(
                      a0, a0 - aux_old(i - 1, j, k, n),
                      aux_old(i + 1, j, k, n) - a0, 1.0);
                  }
                } else if (i + 1 > ilo && i + 1 < ihi) {
                  const amrex::Real ar = aux_old(i + 1, j, k, n);
                  ax_hi = pelelmex_aux_limited_state(
                    ar, ar - a0, aux_old(i + 2, j, k, n) - ar, -1.0);
                }
                if (ux_lo >= 0.0) {
                  if (i - 1 > ilo && i - 1 < ihi) {
                    const amrex::Real al = aux_old(i - 1, j, k, n);
                    ax_lo = pelelmex_aux_limited_state(
                      al, al - aux_old(i - 2, j, k, n), a0 - al, 1.0);
                  }
                } else if (i > ilo && i < ihi) {
                  ax_lo = pelelmex_aux_limited_state(
                    a0, a0 - aux_old(i - 1, j, k, n),
                    aux_old(i + 1, j, k, n) - a0, -1.0);
                }
              }
              amrex::Real div_flux = (ux_hi * ax_hi - ux_lo * ax_lo) / dx[0];

#if AMREX_SPACEDIM >= 2
              const amrex::Real vy_hi = vmac(i, j + 1, k);
              const amrex::Real vy_lo = vmac(i, j, k);
              amrex::Real ay_hi = (vy_hi >= 0.0) ? a0 : aux_old(i, j + 1, k, n);
              amrex::Real ay_lo = (vy_lo >= 0.0) ? aux_old(i, j - 1, k, n) : a0;
              if (aux_advect_scheme == 2) {
                if (vy_hi >= 0.0) {
                  if (j > jlo && j < jhi) {
                    ay_hi = pelelmex_aux_limited_state(
                      a0, a0 - aux_old(i, j - 1, k, n),
                      aux_old(i, j + 1, k, n) - a0, 1.0);
                  }
                } else if (j + 1 > jlo && j + 1 < jhi) {
                  const amrex::Real ar = aux_old(i, j + 1, k, n);
                  ay_hi = pelelmex_aux_limited_state(
                    ar, ar - a0, aux_old(i, j + 2, k, n) - ar, -1.0);
                }
                if (vy_lo >= 0.0) {
                  if (j - 1 > jlo && j - 1 < jhi) {
                    const amrex::Real al = aux_old(i, j - 1, k, n);
                    ay_lo = pelelmex_aux_limited_state(
                      al, al - aux_old(i, j - 2, k, n), a0 - al, 1.0);
                  }
                } else if (j > jlo && j < jhi) {
                  ay_lo = pelelmex_aux_limited_state(
                    a0, a0 - aux_old(i, j - 1, k, n),
                    aux_old(i, j + 1, k, n) - a0, -1.0);
                }
              }
              div_flux += (vy_hi * ay_hi - vy_lo * ay_lo) / dx[1];
#endif
#if AMREX_SPACEDIM == 3
              const amrex::Real wz_hi = wmac(i, j, k + 1);
              const amrex::Real wz_lo = wmac(i, j, k);
              amrex::Real az_hi = (wz_hi >= 0.0) ? a0 : aux_old(i, j, k + 1, n);
              amrex::Real az_lo = (wz_lo >= 0.0) ? aux_old(i, j, k - 1, n) : a0;
              if (aux_advect_scheme == 2) {
                if (wz_hi >= 0.0) {
                  if (k > klo && k < khi) {
                    az_hi = pelelmex_aux_limited_state(
                      a0, a0 - aux_old(i, j, k - 1, n),
                      aux_old(i, j, k + 1, n) - a0, 1.0);
                  }
                } else if (k + 1 > klo && k + 1 < khi) {
                  const amrex::Real ar = aux_old(i, j, k + 1, n);
                  az_hi = pelelmex_aux_limited_state(
                    ar, ar - a0, aux_old(i, j, k + 2, n) - ar, -1.0);
                }
                if (wz_lo >= 0.0) {
                  if (k - 1 > klo && k - 1 < khi) {
                    const amrex::Real al = aux_old(i, j, k - 1, n);
                    az_lo = pelelmex_aux_limited_state(
                      al, al - aux_old(i, j, k - 2, n), a0 - al, 1.0);
                  }
                } else if (k > klo && k < khi) {
                  az_lo = pelelmex_aux_limited_state(
                    a0, a0 - aux_old(i, j, k - 1, n),
                    aux_old(i, j, k + 1, n) - a0, -1.0);
                }
              }
              div_flux += (wz_hi * az_hi - wz_lo * az_lo) / dx[2];
#endif

              aux_new(i, j, k, n) = a0 - dt * div_flux;
            });
        }
      }
      amrex::Gpu::streamSynchronize();
      averageDownAux(AmrNewTime);
      fillPatchAux(AmrNewTime);
    }

    if (m_verbose > 1) {
      amrex::Real MACEnd = amrex::ParallelDescriptor::second() - MACStart;
      amrex::ParallelDescriptor::ReduceRealMax(
        MACEnd, amrex::ParallelDescriptor::IOProcessorNumber());
      amrex::Print() << "   - Advance()::MACProjection()  --> Time: " << MACEnd
                     << "\n";
    }
    checkMemory("MAC-Proj");

  } else {

    // SDC iterations
    for (m_sdcIter = 1; m_sdcIter <= m_nSDCmax; ++m_sdcIter) {
      oneSDC(m_sdcIter, advData, diffData);
    }

    // Post SDC
    averageDownScalars(AmrNewTime);
    fillPatchState(AmrNewTime);

    if (m_nAux > 0) {
      averageDownAux(AmrNewTime);
      fillPatchAux(AmrNewTime);

      // k-epsilon aux floor: clip k and epsilon to >= 1e-14
      if (m_les_model == "kepsilon" && m_nAux >= 2) {
        for (int lev = 0; lev <= finest_level; ++lev) {
          auto* ldata_p = getLevelDataPtr(lev, AmrNewTime);
#ifdef AMREX_USE_OMP
#pragma omp parallel if (amrex::Gpu::notInLaunchRegion())
#endif
          for (amrex::MFIter mfi(ldata_p->auxiliaries, amrex::TilingIfNotGPU()); mfi.isValid(); ++mfi) {
            const amrex::Box& bx = mfi.tilebox();
            auto const& aux_arr = ldata_p->auxiliaries.array(mfi);
            amrex::ParallelFor(bx, [aux_arr] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
              aux_arr(i, j, k, 0) = amrex::max(aux_arr(i, j, k, 0), 1e-14_rt);
              aux_arr(i, j, k, 1) = amrex::max(aux_arr(i, j, k, 1), 1e-14_rt);
             });
           }
         }
         // k-epsilon wall functions: set k and ε at wall-adjacent cells
         if (m_ke_wall_functions > 0) {
           applyKEWallFunctions();
         }
        }
     }

#ifdef PELE_USE_SOOT
    if (do_soot_solve) {
      clipSootMoments();
    }
#endif

    if (m_has_divu != 0) {
      constexpr int is_initialization = 0; // Not here
      constexpr int computeDiffusionTerm =
        1; // Yes, re-evaluate the diffusion term after the last chemistry solve
      constexpr int do_avgDown = 1; // Always
      calcDivU(
        is_initialization, computeDiffusionTerm, do_avgDown, AmrNewTime,
        diffData);
    }
  }
  //----------------------------------------------------------------

  //----------------------------------------------------------------
  BL_PROFILE_VAR("PeleLMeX::advance::velocity", PLM_VEL);
  // Velocity advance
  amrex::Real VelAdvStart = 0.0;
  if (m_verbose > 1) {
    VelAdvStart = amrex::ParallelDescriptor::second();
  }
  // Re-evaluate viscosity only if scalar updated
  if (m_incompressible == 0) {
    calcViscosity(AmrNewTime);
  }

  // Compute t^{n+1/2} velocity advection term
  computeVelocityAdvTerm(advData);

  // Compute provisional new velocity for diffusion solve RHS
  // U^{np1**} = U^{n} - dt*AofS^{n+1/2} - dt/rho^{n+1/2} \nabla \pi^{n-1/2} +
  // dt/rho^{n+1/2} * F^{n+1/2}
  updateVelocity(advData);

  // Semi-implicit CN diffusion solve to get U^{np1*}
  diffuseVelocity();

  // Nodal projection to get constrained U^{np1} and new pressure \pi^{n+1/2}
  const TimeStamp rhoTime = AmrHalfTime;
  velocityProjection(is_initIter, rhoTime, m_dt);
  if (m_verbose > 1) {
    amrex::Real VelAdvEnd = amrex::ParallelDescriptor::second() - VelAdvStart;
    amrex::ParallelDescriptor::ReduceRealMax(
      VelAdvEnd, amrex::ParallelDescriptor::IOProcessorNumber());
    amrex::Print() << "   - Advance()::VelocityAdvance  --> Time: " << VelAdvEnd
                   << "\n";
  }
  checkMemory("Nodal-Proj");
  BL_PROFILE_VAR_STOP(PLM_VEL);
  //----------------------------------------------------------------

  // Deal with ambient pressure
  if ((m_closed_chamber != 0) && (is_initIter == 0)) {
    m_pOld = m_pNew;
  }

  // Snapshot the recycling-plane velocity and update the running mean.
  // Skipped during initial-iteration passes so the mean accumulates only
  // over real timesteps.
  if (is_initIter == 0) {
    updateRecyclingPlaneSnapshot();
  }

  //----------------------------------------------------------------
  // Wrapup advance
  // Timing current time step
  if (m_verbose > 0) {
    amrex::Real run_time = amrex::ParallelDescriptor::second() - strt_time;
    amrex::ParallelDescriptor::ReduceRealMax(
      run_time, amrex::ParallelDescriptor::IOProcessorNumber());
    amrex::Print() << " >> PeleLMeX::Advance() --> Time: " << run_time << "\n";
  }

  //----------------------------------------------------------------
  // Post advance steps ProblemSpecificFunctions
  BL_PROFILE_VAR("ProblemSpecificFunctions::postAdvance()", PLM_POSTADV);

  // Collect state MultiFabs and geometries for all levels
  amrex::Vector<amrex::MultiFab*> state_mf(finest_level + 1);
  amrex::Vector<const amrex::Geometry*> geom_vec(finest_level + 1);
  for (int lev = 0; lev <= finest_level; ++lev) {
    auto* ldata_p = getLevelDataPtr(lev, AmrNewTime);
    state_mf[lev] = &(ldata_p->state);
    geom_vec[lev] = &(geom[lev]);
  }
  ProblemSpecificFunctions::postAdvance(
    m_cur_time + m_dt, m_dt, finest_level, state_mf, geom_vec, *prob_parm,
    prob_parm_d);

  BL_PROFILE_VAR_STOP(PLM_POSTADV);
}

void
PeleLM::oneSDC(
  const int sdcIter,
  const std::unique_ptr<AdvanceAdvData>& advData,
  const std::unique_ptr<AdvanceDiffData>& diffData)
{
  BL_PROFILE("PeleLMeX::oneSDC()");

  if (m_verbose > 0) {
    amrex::Print() << "   SDC iter [" << sdcIter << "] \n";
  }

  //----------------------------------------------------------------
  // Update t^{n+1,k} transport/Dnp1/divU
  //----------------------------------------------------------------
  // At the first SDC, we already copied old -> new
  // k-epsilon source terms: compute every SDC iteration
  if (m_les_model == "kepsilon" && m_nAux >= 2) {
    addKESourceTerms(advData);
  }

  if (sdcIter > 1) {

    amrex::Real UpdateStart = 0.0;
    if (m_verbose > 1) {
      UpdateStart = amrex::ParallelDescriptor::second();
    }
    // fillpatch the new state
    averageDownScalars(AmrNewTime);
    fillPatchState(AmrNewTime);

    if (m_nAux > 0) {
      averageDownAux(AmrNewTime);
      fillPatchAux(AmrNewTime);
      // k-epsilon aux floor: clip k and epsilon to >= 1e-14
      if (m_les_model == "kepsilon" && m_nAux >= 2) {
        for (int lev = 0; lev <= finest_level; ++lev) {
          auto* ldata_p = getLevelDataPtr(lev, AmrNewTime);
#ifdef AMREX_USE_OMP
#pragma omp parallel if (amrex::Gpu::notInLaunchRegion())
#endif
          for (amrex::MFIter mfi(ldata_p->auxiliaries, amrex::TilingIfNotGPU()); mfi.isValid(); ++mfi) {
            const amrex::Box& bx = mfi.tilebox();
            auto const& aux_arr = ldata_p->auxiliaries.array(mfi);
            amrex::ParallelFor(bx, [aux_arr] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
              aux_arr(i, j, k, 0) = amrex::max(aux_arr(i, j, k, 0), 1e-14_rt);
              aux_arr(i, j, k, 1) = amrex::max(aux_arr(i, j, k, 1), 1e-14_rt);
             });
           }
         }
         // k-epsilon wall functions: set k and ε at wall-adjacent cells
         if (m_ke_wall_functions > 0) {
           applyKEWallFunctions();
         }
        }
     }

    calcDiffusivity(AmrNewTime);
    const amrex::Real fluxfact = (sdcIter == m_nSDCmax) ? -0.5 : 0.0;
    computeDifferentialDiffusionTerms(AmrNewTime, diffData, 0, fluxfact);
    if (m_has_divu != 0) {
      constexpr int is_initialization = 0;    // Not here
      constexpr int computeDiffusionTerm = 0; // Nope, we just did that
      constexpr int do_avgDown = 1;           // Always
      calcDivU(
        is_initialization, computeDiffusionTerm, do_avgDown, AmrNewTime,
        diffData);
    }
#ifdef PELE_USE_PLASMA
    ionDriftVelocity(advData);
#endif

    // Check divU dt based on NewTime
    checkDt(AmrNewTime, m_dt);

    if (m_verbose > 1) {
      amrex::Real UpdateEnd = amrex::ParallelDescriptor::second() - UpdateStart;
      amrex::ParallelDescriptor::ReduceRealMax(
        UpdateEnd, amrex::ParallelDescriptor::IOProcessorNumber());
      amrex::Print() << "   - oneSDC()::Update t^{n+1,k}  --> Time: "
                     << UpdateEnd << "\n";
    }
  }
  //----------------------------------------------------------------

  //----------------------------------------------------------------
  // Get u MAC
  //----------------------------------------------------------------
  BL_PROFILE_VAR("PeleLMeX::advance::mac", PLM_MAC);
  amrex::Real MACStart = 0.0;
  if (m_verbose > 1) {
    MACStart = amrex::ParallelDescriptor::second();
  }
  // Predict face velocity with Godunov
  predictVelocity(advData);

  // Create S^{n+1/2} by fillpatching t^{n} and t^{np1,k}
  createMACRHS(advData);

  // Re-evaluate thermo. pressure and add chi_increment
  addChiIncrement(sdcIter, AmrNewTime, advData);

  // MAC projection
  macProject(AmrOldTime, advData, GetVecOfPtrs(advData->mac_divu));
  if (m_verbose > 1) {
    amrex::Real MACEnd = amrex::ParallelDescriptor::second() - MACStart;
    amrex::ParallelDescriptor::ReduceRealMax(
      MACEnd, amrex::ParallelDescriptor::IOProcessorNumber());
    amrex::Print() << "   - oneSDC()::MACProjection()   --> Time: " << MACEnd
                   << "\n";
  }
  checkMemory("MAC-Proj");
  BL_PROFILE_VAR_STOP(PLM_MAC);
  //----------------------------------------------------------------

  //----------------------------------------------------------------
  // Scalar advections
  //----------------------------------------------------------------
  BL_PROFILE_VAR("PeleLMeX::advance::scalars_adv", PLM_SADV);
  amrex::Real ScalAdvStart = 0.0;
  if (m_verbose > 1) {
    ScalAdvStart = amrex::ParallelDescriptor::second();
  }
#ifdef PELE_USE_SOOT
  // Compute and update passive advective terms
  computePassiveAdvTerms(advData, FIRSTSOOT, NUMSOOTVAR);
#endif

  // Get scalar advection SDC forcing
  getScalarAdvForce(advData, diffData);

  // Get AofS: (\nabla \cdot (\rho Y Umac))^{n+1/2,k}
  // and for density = \sum_k AofS_k
  computeScalarAdvTerms(advData);

  // Compute \rho^{np1,k+1} and fillpatch new density
  updateDensity(advData);
  fillPatchDensity(AmrNewTime);
  if (m_verbose > 1) {
    amrex::Real ScalAdvEnd = amrex::ParallelDescriptor::second() - ScalAdvStart;
    amrex::ParallelDescriptor::ReduceRealMax(
      ScalAdvEnd, amrex::ParallelDescriptor::IOProcessorNumber());
    amrex::Print() << "   - oneSDC()::ScalarAdvection() --> Time: "
                   << ScalAdvEnd << "\n";
  }
  checkMemory("ScalAdv");
  BL_PROFILE_VAR_STOP(PLM_SADV);
  //----------------------------------------------------------------

  //----------------------------------------------------------------
  // Scalar diffusion
  //----------------------------------------------------------------
  BL_PROFILE_VAR("PeleLMeX::advance::diffusion", PLM_DIFF);
  amrex::Real ScalDiffStart = 0.0;
  if (m_verbose > 1) {
    ScalDiffStart = amrex::ParallelDescriptor::second();
  }
  // Get scalar diffusion SDC RHS (stored in Forcing)
  getScalarDiffForce(advData, diffData);

  // Diffuse scalars
  differentialDiffusionUpdate(advData, diffData);
  if (m_verbose > 1) {
    amrex::Real ScalDiffEnd =
      amrex::ParallelDescriptor::second() - ScalDiffStart;
    amrex::ParallelDescriptor::ReduceRealMax(
      ScalDiffEnd, amrex::ParallelDescriptor::IOProcessorNumber());
    amrex::Print() << "   - oneSDC()::ScalarDiffusion() --> Time: "
                   << ScalDiffEnd << "\n";
  }
  checkMemory("ScalDiff");
  BL_PROFILE_VAR_STOP(PLM_DIFF);
  //----------------------------------------------------------------

#ifdef PELE_USE_PLASMA
  //----------------------------------------------------------------
  // Solve for implicit non-linear nE/PhiV system
  //----------------------------------------------------------------
  implicitNonLinearSolve(sdcIter, m_dt, diffData, advData);
#endif

  //----------------------------------------------------------------
  // Reaction
  //----------------------------------------------------------------
  if (m_do_react != 0) {
    BL_PROFILE_VAR("PeleLMeX::advance::reactions", PLM_REAC);
    amrex::Real ScalReacStart = 0.0;
    if (m_verbose > 1) {
      ScalReacStart = amrex::ParallelDescriptor::second();
    }
    // Get external forcing for chemistry
    getScalarReactForce(advData);

    // Integrate chemistry
    advanceChemistry(advData);
    if (m_verbose > 1) {
      amrex::Real ScalReacEnd =
        amrex::ParallelDescriptor::second() - ScalReacStart;
      amrex::ParallelDescriptor::ReduceRealMax(
        ScalReacEnd, amrex::ParallelDescriptor::IOProcessorNumber());
      amrex::Print() << "   - oneSDC()::ScalarReaction()  --> Time: "
                     << ScalReacEnd << "\n";
    }
    checkMemory("ScalReact");
    BL_PROFILE_VAR_STOP(PLM_REAC);
  }
  //----------------------------------------------------------------

  //----------------------------------------------------------------
  // Wrap it up
  //----------------------------------------------------------------
  // Re-evaluate derived state entries
  setTemperature(AmrNewTime);
  floorSpecies(AmrNewTime);
  setThermoPress(AmrNewTime);
  // k-epsilon aux floor at end of SDC iteration
  if (m_les_model == "kepsilon" && m_nAux >= 2) {
    for (int lev = 0; lev <= finest_level; ++lev) {
      auto* ldata_p = getLevelDataPtr(lev, AmrNewTime);
      for (amrex::MFIter mfi(ldata_p->auxiliaries, amrex::TilingIfNotGPU()); mfi.isValid(); ++mfi) {
        const amrex::Box& bx = mfi.tilebox();
        auto const& aux_arr = ldata_p->auxiliaries.array(mfi);
        amrex::ParallelFor(bx, [aux_arr] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
          aux_arr(i, j, k, 0) = amrex::max(aux_arr(i, j, k, 0), 1e-14_rt);
          aux_arr(i, j, k, 1) = amrex::max(aux_arr(i, j, k, 1), 1e-14_rt);
        });
      }
    }
  }
}