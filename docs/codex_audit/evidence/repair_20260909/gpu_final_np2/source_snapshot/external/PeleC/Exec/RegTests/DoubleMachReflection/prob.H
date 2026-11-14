#ifndef PROB_H
#define PROB_H

#include <AMReX_Print.H>
#include <AMReX_ParmParse.H>
#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>
#include <AMReX_REAL.H>
#include <AMReX_GpuMemory.H>
#include <AMReX_Math.H>

#include "mechanism.H"

#include "PeleC.H"
#include "IndexDefines.H"
#include "Constants.H"
#include "PelePhysics.H"
#include "Tagging.H"

#include "ProblemSpecificFunctions.H"
#include "prob_parm.H"

AMREX_GPU_DEVICE
AMREX_FORCE_INLINE
void
pc_initdata(
  int i,
  int j,
  int k,
  amrex::Array4<amrex::Real> const& state,
  amrex::GeometryData const& geomdata,
  ProbParmDevice const& prob_parm)
{
  // Geometry
  const amrex::Real* prob_lo = geomdata.ProbLo();
  const amrex::Real* dx = geomdata.CellSize();
  const amrex::Real x = prob_lo[0] + (i + 0.5) * dx[0];
  const amrex::Real y = prob_lo[1] + (j + 0.5) * dx[1];
#if AMREX_SPACEDIM == 3
  const amrex::Real z = prob_lo[2] + (k + 0.5) * dx[2];
  amrex::ignore_unused(z);
#endif

  // Shock position at t=0: x = shock_x0 + y / shock_tan
  const amrex::Real shock_x = prob_parm.shock_x0 + y / prob_parm.shock_tan;

  // Determine which side of shock
  const bool post_shock = (x <= shock_x);

  // Set mass fractions (single species)
  amrex::Real massfrac[NUM_SPECIES] = {0.0};
  massfrac[0] = 1.0;

  if (post_shock) {
    state(i, j, k, URHO) = prob_parm.rho_post;
    state(i, j, k, UMX) = prob_parm.rho_post * prob_parm.u_post;
    state(i, j, k, UMY) = prob_parm.rho_post * prob_parm.v_post;
    state(i, j, k, UMZ) = 0.0;
    state(i, j, k, UEINT) = prob_parm.rhoe_post;
    state(i, j, k, UEDEN) =
      prob_parm.rhoe_post +
      0.5 * prob_parm.rho_post *
        (prob_parm.u_post * prob_parm.u_post +
         prob_parm.v_post * prob_parm.v_post);

    // Compute temperature via EOS
    auto eos = pele::physics::PhysicsType::eos();
    amrex::Real e_check, T;
    eos.RYP2E(prob_parm.rho_post, massfrac, prob_parm.p_post, e_check);
    eos.EY2T(e_check, massfrac, T);
    state(i, j, k, UTEMP) = T;
  } else {
    state(i, j, k, URHO) = prob_parm.rho_pre;
    state(i, j, k, UMX) = prob_parm.rho_pre * prob_parm.u_pre;
    state(i, j, k, UMY) = prob_parm.rho_pre * prob_parm.v_pre;
    state(i, j, k, UMZ) = 0.0;
    state(i, j, k, UEINT) = prob_parm.rhoe_pre;
    state(i, j, k, UEDEN) =
      prob_parm.rhoe_pre +
      0.5 * prob_parm.rho_pre *
        (prob_parm.u_pre * prob_parm.u_pre +
         prob_parm.v_pre * prob_parm.v_pre);

    // Compute temperature via EOS
    auto eos = pele::physics::PhysicsType::eos();
    amrex::Real e_check, T;
    eos.RYP2E(prob_parm.rho_pre, massfrac, prob_parm.p_pre, e_check);
    eos.EY2T(e_check, massfrac, T);
    state(i, j, k, UTEMP) = T;
  }

  for (int n = 0; n < NUM_SPECIES; n++) {
    state(i, j, k, UFS + n) = 0;
  }
  state(i, j, k, UFS) = state(i, j, k, URHO);
}

AMREX_GPU_DEVICE
AMREX_FORCE_INLINE
void
bcnormal(
  const amrex::Real x[AMREX_SPACEDIM],
  const amrex::Real s_int[NVAR],
  amrex::Real s_ext[NVAR],
  const int idir,
  const int sgn,
  const amrex::Real time,
  amrex::GeometryData const& /*geomdata*/,
  ProbParmDevice const& prob_parm,
  const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& /*turb_fluc*/)
{
  // Set mass fractions
  amrex::Real massfrac[NUM_SPECIES] = {0.0};
  massfrac[0] = 1.0;

  // --- x-direction boundaries ---
  if (idir == 0) {
    if (sgn == -1) {
      // x-lo: always post-shock inflow
      s_ext[URHO] = prob_parm.rho_post;
      s_ext[UMX] = prob_parm.rho_post * prob_parm.u_post;
      s_ext[UMY] = prob_parm.rho_post * prob_parm.v_post;
      s_ext[UMZ] = 0.0;
      s_ext[UEINT] = prob_parm.rhoe_post;
      s_ext[UEDEN] =
        prob_parm.rhoe_post +
        0.5 * prob_parm.rho_post *
          (prob_parm.u_post * prob_parm.u_post +
           prob_parm.v_post * prob_parm.v_post);
      auto eos = pele::physics::PhysicsType::eos();
      amrex::Real e, T;
      eos.RYP2E(prob_parm.rho_post, massfrac, prob_parm.p_post, e);
      eos.EY2T(e, massfrac, T);
      s_ext[UTEMP] = T;
    } else {
      // x-hi: pre-shock (copied from interior)
      s_ext[URHO] = s_int[URHO];
      s_ext[UMX] = s_int[UMX];
      s_ext[UMY] = s_int[UMY];
      s_ext[UMZ] = s_int[UMZ];
      s_ext[UEINT] = s_int[UEINT];
      s_ext[UEDEN] = s_int[UEDEN];
      s_ext[UTEMP] = s_int[UTEMP];
    }
  }

  // --- y-direction boundaries ---
  else if (idir == 1) {
    if (sgn == -1) {
      // y-lo: wedge (x >= wedge_start) or post-shock inflow (x < wedge_start)
      const amrex::Real xpos = x[0];
      if (xpos >= prob_parm.wedge_start) {
        // Inviscid slip wall (wedge): reflect normal velocity only
        // s_int has: URHO, UMX, UMY, UMZ, UEDEN, UEINT, UTEMP, UFS...
        s_ext[URHO] = s_int[URHO];
        s_ext[UMX] = s_int[UMX];    // tangential, same
        s_ext[UMY] = -s_int[UMY];   // normal, reflected
        s_ext[UMZ] = s_int[UMZ];    // tangential, same
        s_ext[UEINT] = s_int[UEINT];
        // Recompute total energy with reflected velocity
        s_ext[UEDEN] =
          s_int[UEINT] +
          0.5 * (s_ext[UMX] * s_ext[UMX] / s_ext[URHO] +
                 s_ext[UMY] * s_ext[UMY] / s_ext[URHO] +
                 s_ext[UMZ] * s_ext[UMZ] / s_ext[URHO]);
        s_ext[UTEMP] = s_int[UTEMP];
      } else {
        // x < wedge_start: post-shock inflow
        s_ext[URHO] = prob_parm.rho_post;
        s_ext[UMX] = prob_parm.rho_post * prob_parm.u_post;
        s_ext[UMY] = prob_parm.rho_post * prob_parm.v_post;
        s_ext[UMZ] = 0.0;
        s_ext[UEINT] = prob_parm.rhoe_post;
        s_ext[UEDEN] =
          prob_parm.rhoe_post +
          0.5 * prob_parm.rho_post *
            (prob_parm.u_post * prob_parm.u_post +
             prob_parm.v_post * prob_parm.v_post);
        auto eos = pele::physics::PhysicsType::eos();
        amrex::Real e, T;
        eos.RYP2E(prob_parm.rho_post, massfrac, prob_parm.p_post, e);
        eos.EY2T(e, massfrac, T);
        s_ext[UTEMP] = T;
      }
    } else {
      // y-hi: time-dependent shock position
      const amrex::Real xpos = x[0];
      const amrex::Real ypos = x[1];
      // Shock position at time t:
      // shock_x(t, y) = shock_x0 + y/shock_tan + shock_speed_x * t
      const amrex::Real shock_x =
        prob_parm.shock_x0 + ypos / prob_parm.shock_tan +
        prob_parm.shock_speed_x * time;

      if (xpos <= shock_x) {
        // Post-shock state
        s_ext[URHO] = prob_parm.rho_post;
        s_ext[UMX] = prob_parm.rho_post * prob_parm.u_post;
        s_ext[UMY] = prob_parm.rho_post * prob_parm.v_post;
        s_ext[UMZ] = 0.0;
        s_ext[UEINT] = prob_parm.rhoe_post;
        s_ext[UEDEN] =
          prob_parm.rhoe_post +
          0.5 * prob_parm.rho_post *
            (prob_parm.u_post * prob_parm.u_post +
             prob_parm.v_post * prob_parm.v_post);
        auto eos = pele::physics::PhysicsType::eos();
        amrex::Real e, T;
        eos.RYP2E(prob_parm.rho_post, massfrac, prob_parm.p_post, e);
        eos.EY2T(e, massfrac, T);
        s_ext[UTEMP] = T;
      } else {
        // Pre-shock state
        s_ext[URHO] = prob_parm.rho_pre;
        s_ext[UMX] = prob_parm.rho_pre * prob_parm.u_pre;
        s_ext[UMY] = prob_parm.rho_pre * prob_parm.v_pre;
        s_ext[UMZ] = 0.0;
        s_ext[UEINT] = prob_parm.rhoe_pre;
        s_ext[UEDEN] =
          prob_parm.rhoe_pre +
          0.5 * prob_parm.rho_pre *
            (prob_parm.u_pre * prob_parm.u_pre +
             prob_parm.v_pre * prob_parm.v_pre);
        auto eos = pele::physics::PhysicsType::eos();
        amrex::Real e, T;
        eos.RYP2E(prob_parm.rho_pre, massfrac, prob_parm.p_pre, e);
        eos.EY2T(e, massfrac, T);
        s_ext[UTEMP] = T;
      }
    }
  }

  // --- z-direction boundaries ---
  else if (idir == 2) {
    // Slip wall in z: reflect normal velocity
    s_ext[URHO] = s_int[URHO];
    s_ext[UMX] = s_int[UMX];
    s_ext[UMY] = s_int[UMY];
    s_ext[UMZ] = -s_int[UMZ];
    s_ext[UEINT] = s_int[UEINT];
    s_ext[UEDEN] =
      s_int[UEINT] +
      0.5 * (s_ext[UMX] * s_ext[UMX] / s_ext[URHO] +
             s_ext[UMY] * s_ext[UMY] / s_ext[URHO] +
             s_ext[UMZ] * s_ext[UMZ] / s_ext[URHO]);
    s_ext[UTEMP] = s_int[UTEMP];
  }

  // Species
  for (int n = 0; n < NUM_SPECIES; n++) {
    s_ext[UFS + n] = 0;
  }
  s_ext[UFS] = s_ext[URHO];
}

void pc_prob_close();

using ProblemSpecificFunctions = DefaultProblemSpecificFunctions;

#endif
