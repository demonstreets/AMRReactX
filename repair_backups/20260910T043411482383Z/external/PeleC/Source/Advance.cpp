#include "mechanism.H"

#include "PeleC.H"
#include "IndexDefines.H"
#include "PelePhysics.H"
#include <AMReX_ParmParse.H>

#ifdef PELE_USE_SPRAY
#include "SprayParticles.H"
#endif

amrex::Real
PeleC::advance(
  amrex::Real time, amrex::Real dt, int amr_iteration, int amr_ncycle)
{
  // The main driver for a single level implementing the time advance.
  //        @param time the current simulation time
  //        @param dt the timestep to advance (e.g., go from time to time + dt)
  //        @param amr_iteration where we are in the current AMR subcycle.  Each
  //                        level will take a number of steps to reach the
  //                        final time of the coarser level below it.  This
  //                        counter starts at 1
  //        @param amr_ncycle  the number of subcycles at this level

  BL_PROFILE("PeleC::advance()");

  int finest_level = parent->finestLevel();

  if (level < finest_level && do_reflux) {
    getFluxReg(level + 1).reset();

    if (!amrex::DefaultGeometry().IsCartesian()) {
      amrex::Abort("Flux registers not r-z compatible yet");
    }
  }

  // Opt-in uniform-grid Strang split: C(dt/2), native transport/spray(dt),
  // C(dt/2). Chemistry sees no constant extrapolated transport forcing.
  std::string chemistry_transport_split = "sdc";
  amrex::ParmParse("pelec").query("chemistry_transport_split", chemistry_transport_split);
  if (chemistry_transport_split != "sdc" && chemistry_transport_split != "strang") {
    amrex::Abort("pelec.chemistry_transport_split must be sdc or strang");
  }
  if (do_react && chemistry_transport_split == "strang") {
    if (level != 0 || parent->maxLevel() != 0 || do_mol || do_rf || sdc_iters != 1) {
      amrex::Abort("Strang chemistry currently requires max_level=0, do_mol=0, do_rf=0, sdc_iters=1");
    }
    auto& initial = get_new_data(State_Type);
    auto const& eb = dynamic_cast<amrex::EBFArrayBoxFactory const&>(initial.Factory());
    for (amrex::MFIter mfi(initial); mfi.isValid(); ++mfi) {
      if (eb.getMultiEBCellFlagFab()[mfi].getType(mfi.validbox()) != amrex::FabType::regular) {
        amrex::Abort("Strang chemistry currently requires an all-regular Cartesian domain");
      }
    }
    amrex::MultiFab original(grids, dmap, NVAR, initial.nGrow(), amrex::MFInfo(), Factory());
    amrex::MultiFab::Copy(original, initial, 0, 0, NVAR, initial.nGrow());
    amrex::MultiFab chem(grids, dmap, NUM_SPECIES + 2, 0);
    amrex::MultiFab forcing_y(grids, dmap, NUM_SPECIES, 0);
    amrex::MultiFab forcing_e(grids, dmap, 1, 0);
    amrex::MultiFab counts(grids, dmap, 1, 0);
    amrex::iMultiFab mask(grids, dmap, 1, 0);
    forcing_y.setVal(0.0); forcing_e.setVal(0.0); counts.setVal(0.0); mask.setVal(1);
    const amrex::Real half_dt = 0.5 * dt;
    auto pure_chemistry = [&](amrex::MultiFab& state_in, amrex::Real chemistry_time) {
      for (amrex::MFIter mfi(state_in, amrex::TilingIfNotGPU()); mfi.isValid(); ++mfi) {
        const auto bx = mfi.tilebox();
        const auto s = state_in.array(mfi);
        const auto y = chem.array(mfi);
        const auto temperature = chem.array(mfi, NUM_SPECIES);
        const auto energy = chem.array(mfi, NUM_SPECIES + 1);
        amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
          for (int n = 0; n < NUM_SPECIES; ++n) y(i,j,k,n) = s(i,j,k,UFS+n);
          temperature(i,j,k) = s(i,j,k,UTEMP);
          energy(i,j,k) = s(i,j,k,UEDEN) - 0.5 *
            (s(i,j,k,UMX)*s(i,j,k,UMX) + s(i,j,k,UMY)*s(i,j,k,UMY) +
             s(i,j,k,UMZ)*s(i,j,k,UMZ)) / s(i,j,k,URHO);
        });
        auto clock = chemistry_time;
        reactor->react(bx, y, forcing_y.array(mfi), temperature, energy,
          forcing_e.array(mfi), counts.array(mfi), mask.array(mfi), half_dt, clock
#ifdef AMREX_USE_GPU
          , amrex::Gpu::gpuStream()
#endif
        );
        amrex::Gpu::Device::streamSynchronize();
        amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
          const auto density = s(i,j,k,URHO);
          amrex::Real sum = 0., minimum = 1.;
          bool valid = std::isfinite(density) && density > 0. &&
            std::isfinite(temperature(i,j,k)) && temperature(i,j,k) > 0.;
          for (int n = 0; n < NUM_SPECIES; ++n) {
            const auto yn = y(i,j,k,n) / density;
            sum += y(i,j,k,n); minimum = amrex::min(minimum, yn);
            valid = valid && std::isfinite(yn) && yn >= -1.e-12 && yn <= 1.+1.e-12;
          }
          valid = valid && amrex::Math::abs(sum-density) <= 1.e-10*density;
          if (!valid) {
            printf("INVALID_PURE_CHEMISTRY cell=(%d,%d,%d) dt=%.17e rho=%.17e sum=%.17e T=%.17e minY=%.17e\n",
              i,j,k,half_dt,density,sum,temperature(i,j,k),minimum);
            amrex::Abort("pure chemistry produced inadmissible state or mass drift");
          }
          for (int n = 0; n < NUM_SPECIES; ++n) s(i,j,k,UFS+n) = y(i,j,k,n);
          s(i,j,k,UTEMP) = temperature(i,j,k);
          // Retain the conservative density, momentum and total energy exactly.
          s(i,j,k,UEINT) = s(i,j,k,UEDEN) - 0.5 *
            (s(i,j,k,UMX)*s(i,j,k,UMX) + s(i,j,k,UMY)*s(i,j,k,UMY) +
             s(i,j,k,UMZ)*s(i,j,k,UMZ)) / density;
        });
      }
      computeTemp(state_in, 0);
    };
    pure_chemistry(initial, time);
    do_react = 0;
    get_new_data(Reactions_Type).setVal(0.0);
    const auto transport_dt = do_sdc_advance(time, dt, amr_iteration, amr_ncycle);
    do_react = 1;
    auto& final_state = get_new_data(State_Type);
    pure_chemistry(final_state, time + half_dt);
    amrex::MultiFab::Copy(get_old_data(State_Type), original, 0, 0, NVAR, original.nGrow());
    // In this split, reaction diagnostics are instantaneous rates at the final
    // state (not the SDC time-averaged, transport-subtracted source).
    auto& rates = get_new_data(Reactions_Type);
    rates.setVal(0.0);
    for (amrex::MFIter mfi(final_state, amrex::TilingIfNotGPU()); mfi.isValid(); ++mfi) {
      const auto s = final_state.const_array(mfi);
      const auto r = rates.array(mfi);
      amrex::ParallelFor(mfi.tilebox(), [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
        amrex::Real y[NUM_SPECIES], w[NUM_SPECIES], h[NUM_SPECIES];
        const auto density = s(i,j,k,URHO), temperature = s(i,j,k,UTEMP);
        for (int n = 0; n < NUM_SPECIES; ++n) y[n] = s(i,j,k,UFS+n)/density;
        auto eos = pele::physics::PhysicsType::eos();
        eos.RTY2WDOT(density,temperature,y,w);
        eos.T2Hi(temperature,h);
        amrex::Real heat = 0.;
        for (int n = 0; n < NUM_SPECIES; ++n) { r(i,j,k,n)=w[n]; heat -= h[n]*w[n]; }
        r(i,j,k,NUM_SPECIES+1)=heat;
      });
    }
    return transport_dt;
  }

  amrex::Real dt_new;
  if (do_mol) {
    dt_new = do_mol_advance(time, dt, amr_iteration, amr_ncycle);
  } else {
    dt_new = do_sdc_advance(time, dt, amr_iteration, amr_ncycle);
  }

  return dt_new;
}

amrex::Real
PeleC::do_mol_advance(
  amrex::Real time, amrex::Real dt, int amr_iteration, int amr_ncycle)
{
  BL_PROFILE("PeleC::do_mol_advance()");

  // Check that we are not asking to advance stuff we don't know to
  // if (src_list.size() > 0) amrex::Abort("Have not integrated other sources
  // into MOL advance yet");

  for (int i = 0; i < num_state_type; ++i) {
    if ((i != Reactions_Type) || (!do_react)) {
      state[i].allocOldData();
      state[i].swapTimeLevels(dt);
    }
  }

  if (do_mol_load_balance || do_react_load_balance) {
    get_new_data(Work_Estimate_Type).setVal(0.0);
  }

  amrex::MultiFab& S_old = get_old_data(State_Type);
  amrex::MultiFab& S_new = get_new_data(State_Type);

  amrex::MultiFab molSrc(grids, dmap, NVAR, 0, amrex::MFInfo(), Factory());

  amrex::MultiFab molSrc_old;
  amrex::MultiFab molSrc_new;
  if (mol_iters > 1) {
    molSrc_old.define(grids, dmap, NVAR, 0, amrex::MFInfo(), Factory());
    molSrc_new.define(grids, dmap, NVAR, 0, amrex::MFInfo(), Factory());
  }

  if (!do_react) {
    get_new_data(Reactions_Type).setVal(0.0);
  }
  const amrex::MultiFab& I_R = get_new_data(Reactions_Type);

  set_body_state(S_old);
  set_body_state(S_new);

  // Compute S^{n} = MOLRhs(U^{n})
  if (verbose != 0) {
    amrex::Print() << "... Computing MOL source term at t^{n} " << std::endl;
  }

  int nGrow_FP_border = numGrow() + nGrowF;
#ifdef PELE_USE_SPRAY
  const int spray_state_ghosts = sprayStateGhosts(amr_ncycle);
  nGrow_FP_border = amrex::max<int>(nGrow_FP_border, spray_state_ghosts);
  AMREX_ASSERT(Sborder.nGrow() >= nGrow_FP_border);
#endif

  FillPatcherFill(Sborder, 0, NVAR, nGrow_FP_border, time, State_Type, 0);
  amrex::Real reflux_factor = 0.5;
  getMOLSrcTerm(Sborder, molSrc, time, dt, reflux_factor);

  // Build other (non-diffusion) sources at t_old
  for (int src : src_list) {
    if (src != diff_src) {
      construct_old_source(src, time, dt, amr_iteration, amr_ncycle, 0, 0);

      // add sources to molsrc
#ifdef PELE_USE_SPRAY
      int ncomp_old = NVAR;
#else
      int ncomp_old = NVAR;
#endif
      amrex::MultiFab::Saxpy(molSrc, 1.0, *old_sources[src], 0, 0, ncomp_old, 0);
    }
  }

  if (mol_iters > 1) {
    amrex::MultiFab::Copy(molSrc_old, molSrc, 0, 0, NVAR, 0);
  }

  // U^* = U^n + dt*S^n
  amrex::MultiFab::LinComb(S_new, 1.0, Sborder, 0, dt, molSrc, 0, 0, NVAR, 0);

  // U^{n+1,*} = U^n + dt*S^n + dt*I_R
  if (do_react) {
    amrex::MultiFab::Saxpy(S_new, dt, I_R, 0, FirstSpec, NUM_SPECIES, 0);
    amrex::MultiFab::Saxpy(S_new, dt, I_R, NUM_SPECIES, Eden, 1, 0);
  }

  computeTemp(S_new, 0);

  // Compute S^{n+1} = MOLRhs(U^{n+1,*})
  if (verbose != 0) {
    amrex::Print() << "... Computing MOL source term at t^{n+1} " << std::endl;
  }

  FillPatcherFill(Sborder, 0, NVAR, nGrow_FP_border, time + dt, State_Type, 0);
  reflux_factor = mol_iters > 1 ? 0 : 0.5;
  getMOLSrcTerm(Sborder, molSrc, time, dt, reflux_factor);

  // Build other (non-diffusion) sources at t_new
  for (int src : src_list) {
    if (src != diff_src) {
      construct_new_source(src, time + dt, dt, amr_iteration, amr_ncycle, 0, 0);

      // add sources to molsrc
#ifdef PELE_USE_SPRAY
      int ncomp_new = NVAR;
#else
      int ncomp_new = NVAR;
#endif
      amrex::MultiFab::Saxpy(molSrc, 1.0, *new_sources[src], 0, 0, ncomp_new, 0);
    }
  }

  // U^{n+1.**} = 0.5*(U^n + U^{n+1,*}) + 0.5*dt*S^{n+1} = U^n + 0.5*dt*S^n +
  // 0.5*dt*S^{n+1} + 0.5*dt*I_R
  amrex::MultiFab::LinComb(S_new, 0.5, Sborder, 0, 0.5, S_old, 0, 0, NVAR, 0);
  amrex::MultiFab::Saxpy(
    S_new, 0.5 * dt, molSrc, 0, 0, NVAR,
    0); //  NOTE: If I_R=0, we are done and U_new is the final new-time state

  if (do_react) {
    amrex::MultiFab::Saxpy(S_new, 0.5 * dt, I_R, 0, FirstSpec, NUM_SPECIES, 0);
    amrex::MultiFab::Saxpy(S_new, 0.5 * dt, I_R, NUM_SPECIES, Eden, 1, 0);

    // F_{AD} = (1/dt)(U^{n+1,**} - U^n) - I_R = 0.5*(S^{n}+S^{n+1}(which is a
    // guess!))
    amrex::MultiFab::LinComb(
      molSrc, 1.0 / dt, S_new, 0, -1.0 / dt, S_old, 0, 0, NVAR, 0);
    amrex::MultiFab::Subtract(molSrc, I_R, 0, FirstSpec, NUM_SPECIES, 0);
    amrex::MultiFab::Subtract(molSrc, I_R, NUM_SPECIES, Eden, 1, 0);

    // Compute I_R and U^{n+1} = U^n + dt*(F_{AD} + I_R)
    react_state(time, dt, false, &molSrc);
  }

  computeTemp(S_new, 0);

  if (do_react) {
    for (int mol_iter = 2; mol_iter <= mol_iters; ++mol_iter) {
      if (verbose != 0) {
        amrex::Print() << "... Re-computing MOL source term at t^{n+1} (iter = "
                       << mol_iter << " of " << mol_iters << ")" << std::endl;
      }

      FillPatcherFill(
        Sborder, 0, NVAR, nGrow_FP_border, time + dt, State_Type, 0);
      reflux_factor = mol_iter == mol_iters ? 0.5 : 0;
      getMOLSrcTerm(Sborder, molSrc_new, time, dt, reflux_factor);

      // F_{AD} = (1/2)(molSrc_old + molSrc_new)
      amrex::MultiFab::LinComb(
        molSrc, 0.5, molSrc_old, 0, 0.5, molSrc_new, 0, 0, NVAR, 0);

      // Compute I_R and U^{n+1} = U^n + dt*(F_{AD} + I_R)
      react_state(time, dt, false, &molSrc);

      computeTemp(S_new, 0);
    }
  }

  set_body_state(S_new);

  return dt;
}

amrex::Real
PeleC::do_sdc_advance(
  amrex::Real time, amrex::Real dt, int amr_iteration, int amr_ncycle)
{
  BL_PROFILE("PeleC::do_sdc_advance()");

  amrex::Real dt_new = dt;

  // This routine will advance the old state data (called S_old here)
  // to the new time, for a single level.  The new data is called
  // S_new here.  The update includes reactions (if we are not doing
  // SDC), hydro, and the source terms.

  initialize_sdc_advance(time, dt, amr_iteration, amr_ncycle);

  if (do_react_load_balance) {
    get_new_data(Work_Estimate_Type).setVal(0.0);
  }

  for (int sdc_iter = 0; sdc_iter < sdc_iters; ++sdc_iter) {
    if (sdc_iters > 1) {
      amrex::Print() << "SDC iteration " << sdc_iter + 1 << " of " << sdc_iters
                     << ".\n";
    }

    dt_new = do_sdc_iteration(
      time, dt, amr_iteration, amr_ncycle, sdc_iter, sdc_iters);
  }

  finalize_sdc_advance(time, dt, amr_iteration, amr_ncycle);

  return dt_new;
}

amrex::Real
PeleC::do_sdc_iteration(
  amrex::Real time,
  amrex::Real dt,
  int amr_iteration,
  int amr_ncycle,
  int sub_iteration,
  int sub_ncycle)
{
  // This routine will advance the old state data (called S_old here)
  // to the new time, for a single level.  The new data is called
  // S_new here.  The update includes hydro, and the source terms.

  BL_PROFILE("PeleC::do_sdc_iteration()");

  const amrex::MultiFab& S_old = get_old_data(State_Type);
  amrex::MultiFab& S_new = get_new_data(State_Type);

  initialize_sdc_iteration(
    time, dt, amr_iteration, amr_ncycle, sub_iteration, sub_ncycle);

  // Create Sborder if hydro or diffuse, with the appropriate number of grow
  // cells
  int nGrow_FP_border = 0;
  bool fill_Sborder = false;

  if (do_hydro) {
    fill_Sborder = true;
    nGrow_FP_border = numGrow() + nGrowF;
  } else if (do_diffuse) {
    fill_Sborder = true;
    nGrow_FP_border = numGrow();
  }
#ifdef PELE_USE_SPRAY
  if (do_spray_particles) {
    const int spray_state_ghosts = sprayStateGhosts(amr_ncycle);
    fill_Sborder = true;
    nGrow_FP_border = amrex::max<int>(nGrow_FP_border, spray_state_ghosts);
    AMREX_ASSERT(Sborder.nGrow() >= nGrow_FP_border);
  }
#endif

  if (fill_Sborder) {
    FillPatcherFill(Sborder, 0, NVAR, nGrow_FP_border, time, State_Type, 0);
  }

  if (sub_iteration == 0) {

    // Build other (non-diffusion) sources at t_old
    for (int n : src_list) {
      if (n != diff_src) {
        construct_old_source(
          n, time, dt, amr_iteration, amr_ncycle, sub_iteration, sub_ncycle);
      }
    }

    // Get diffusion source separate from other sources, since it requires grow
    // cells, and we may want to reuse what we fill-patched for hydro
    if (do_diffuse) {
      if (verbose != 0) {
        amrex::Print() << "... Computing diffusion terms at t^(n)" << std::endl;
      }
      AMREX_ASSERT(
        !do_mol); // Currently this combo only managed through MOL integrator
      amrex::Real reflux_factor_old = 0.5;

      getMOLSrcTerm(
        Sborder, *old_sources[diff_src], time, dt, reflux_factor_old);
    }

    // Initialize sources at t_new by copying from t_old
    for (int src : src_list) {
#ifdef PELE_USE_SPRAY
      int ncomp_src = NVAR;
#else
      int ncomp_src = NVAR;
#endif
      amrex::MultiFab::Copy(
        *new_sources[src], *old_sources[src], 0, 0, ncomp_src, 0);
    }
  }

  // Construct hydro source, will use old and current iterate of new sources.
  if (do_hydro) {
    construct_hydro_source(
      Sborder, time, dt, amr_iteration, amr_ncycle, sub_iteration, sub_ncycle);
  }

  // Construct S_new with current iterate of all sources
  construct_Snew(S_new, S_old, dt);

  int ng_src = 0;
  computeTemp(S_new, ng_src);

  // Now update t_new sources (diffusion separate because it requires a fill
  // patch)
  if (do_diffuse || do_spray_particles) {
    int nGrowDiff = numGrow();
    if (do_spray_particles && level > 0) {
      nGrowDiff = amrex::max<int>(nGrowDiff, nGrow_FP_border);
    }
    FillPatcherFill(Sborder, 0, NVAR, nGrowDiff, time + dt, State_Type, 0);
  }
  if (do_diffuse) {
    if (verbose != 0) {
      amrex::Print() << "... Computing diffusion terms at t^(n+1,"
                     << sub_iteration + 1 << ")" << std::endl;
    }
    amrex::Real reflux_factor_new = sub_iteration == sub_ncycle - 1 ? 0.5 : 0;
    getMOLSrcTerm(Sborder, *new_sources[diff_src], time, dt, reflux_factor_new);
  }

  // Build other (non-diffusion) sources at t_new
  for (int n : src_list) {
    if (n != diff_src) {
      construct_new_source(
        n, time + dt, dt, amr_iteration, amr_ncycle, sub_iteration, sub_ncycle);
    }
  }

  // Update I_R and rebuild S_new accordingly
  if (do_react) {
    react_state(time, dt);
  } else {
    construct_Snew(S_new, S_old, dt);
    get_new_data(Reactions_Type).setVal(0);
  }

  computeTemp(S_new, ng_src);

  finalize_sdc_iteration(
    time, dt, amr_iteration, amr_ncycle, sub_iteration, sub_ncycle);

  return dt;
}

void
PeleC::construct_Snew(
  amrex::MultiFab& S_new, const amrex::MultiFab& S_old, amrex::Real dt)
{
  int ng = 0;

  amrex::MultiFab::Copy(S_new, S_old, 0, 0, NVAR, ng);
  for (int src : src_list) {
#ifdef PELE_USE_SPRAY
    int ncomp_snew = NVAR;
#else
    int ncomp_snew = NVAR;
#endif
    amrex::MultiFab::Saxpy(S_new, 0.5 * dt, *new_sources[src], 0, 0, ncomp_snew, ng);
    amrex::MultiFab::Saxpy(S_new, 0.5 * dt, *old_sources[src], 0, 0, ncomp_snew, ng);
  }
  if (do_hydro) {
    amrex::MultiFab::Saxpy(S_new, dt, hydro_source, 0, 0, NVAR, ng);
  }

  if (do_react) {
    const amrex::MultiFab& I_R = get_new_data(Reactions_Type);
    amrex::MultiFab::Saxpy(S_new, dt, I_R, 0, FirstSpec, NUM_SPECIES, 0);
    amrex::MultiFab::Saxpy(S_new, dt, I_R, NUM_SPECIES, Eden, 1, 0);
  }
}

void
PeleC::initialize_sdc_iteration(
  amrex::Real /*time*/,
  amrex::Real /*dt*/,
  int /*amr_iteration*/,
  int /*amr_ncycle*/,
  int /*sdc_iteration*/,
  int /*sdc_ncycle*/)
{
  BL_PROFILE("PeleC::initialize_sdc_iteration()");

  // Reset the change from density resets
  frac_change = 1;
}

void
PeleC::finalize_sdc_iteration(
  amrex::Real /*time*/,
  amrex::Real /*dt*/,
  int /*amr_iteration*/,
  int /*amr_ncycle*/,
  int /*sdc_iteration*/,
  int /*sdc_ncycle*/)
{
  BL_PROFILE("PeleC::finalize_sdc_iteration()");
}

void
PeleC::initialize_sdc_advance(
  amrex::Real /*time*/,
  amrex::Real dt,
  int /*amr_iteration*/,
  int /*amr_ncycle*/)
{
  BL_PROFILE("PeleC::initialize_sdc_advance()");

  for (int i = 0; i < num_state_type; ++i) {
    state[i].allocOldData();
    state[i].swapTimeLevels(dt);
  }

  if (do_react) {
    // Initialize I_R with value from previous time step
    amrex::MultiFab::Copy(
      get_new_data(Reactions_Type), get_old_data(Reactions_Type), 0, 0,
      get_new_data(Reactions_Type).nComp(),
      get_new_data(Reactions_Type).nGrow());
  }
}

void
PeleC::finalize_sdc_advance(
  amrex::Real /*time*/,
  amrex::Real /*dt*/,
  int /*amr_iteration*/,
  int /*amr_ncycle*/)
{
  BL_PROFILE("PeleC::finalize_sdc_advance()");
}
