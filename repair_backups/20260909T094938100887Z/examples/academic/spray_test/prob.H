#ifndef PROB_H
#define PROB_H

#include <AMReX_Print.H>
#include <AMReX_ParmParse.H>
#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>
#include <AMReX_REAL.H>
#include <AMReX_GpuMemory.H>

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

  // Determine VOF phase
#if NUM_ADV > 0
  const bool is_liquid = (x >= prob_parm.alpha_lo && x <= prob_parm.alpha_hi);
#else
  const bool is_liquid = false;
#endif

  // Species
  amrex::Real massfrac[NUM_SPECIES] = {0.0};
  massfrac[0] = 0.233; massfrac[1] = 0.767;
  for (int n = 0; n < NUM_SPECIES; n++) {
    state(i, j, k, UFS + n) = 0.0;
  }
  state(i, j, k, UFS) = prob_parm.rho0 * 0.233;
  state(i, j, k, UFS + 1) = prob_parm.rho0 * 0.767;

  // Velocity
  state(i, j, k, URHO) = prob_parm.rho0;
  state(i, j, k, UMX) = prob_parm.rho0 * prob_parm.u0;
  state(i, j, k, UMY) = 0.0;
  state(i, j, k, UMZ) = 0.0;

  // Energy: SG-consistent for liquid, ideal-gas for gas
  const amrex::Real ke = 0.5 * prob_parm.rho0 * prob_parm.u0 * prob_parm.u0;
  amrex::Real e_int;
  if (is_liquid) {
    // StiffenedGas: e = (p + γ*p∞) / ((γ-1)*ρ)
    constexpr amrex::Real gamma_l = 4.4;
    constexpr amrex::Real p_inf = 6.0e8;
    e_int = (prob_parm.p0 + gamma_l * p_inf) / ((gamma_l - 1.0) * prob_parm.rho0);
    state(i, j, k, UTEMP) = e_int / 4180.0; // SG: T = e/cv
  } else {
    auto eos = pele::physics::PhysicsType::eos();
    eos.RYP2E(prob_parm.rho0, massfrac, prob_parm.p0, e_int);
    state(i, j, k, UTEMP) = prob_parm.T0;
  }
  state(i, j, k, UEINT) = prob_parm.rho0 * e_int;
  state(i, j, k, UEDEN) = state(i, j, k, UEINT) + ke;

  // VOF α: 1 in [alpha_lo, alpha_hi], 0 elsewhere
#if NUM_ADV > 0
  state(i, j, k, UFA) = is_liquid ? prob_parm.rho0 : 0.0;
#endif
}

AMREX_GPU_DEVICE
AMREX_FORCE_INLINE
void
bcnormal(
  const amrex::Real* /*x[AMREX_SPACEDIM]*/,
  const amrex::Real s_int[NVAR],
  amrex::Real s_ext[NVAR],
  const int /*idir*/,
  const int /*sgn*/,
  const amrex::Real /*time*/,
  amrex::GeometryData const& /*geomdata*/,
  ProbParmDevice const& /*prob_parm*/,
  const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& /*turb_fluc*/)
{
  for (int n = 0; n < NVAR; n++) {
    s_ext[n] = s_int[n];
  }
}

void pc_prob_close();

using ProblemSpecificFunctions = DefaultProblemSpecificFunctions;

#endif
