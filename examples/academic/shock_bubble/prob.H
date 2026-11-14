#ifndef SHOCK_BUBBLE_PROB_H
#define SHOCK_BUBBLE_PROB_H

#include "prob_parm.H"

#include <AMReX_Geometry.H>
#include <AMReX_Gpu.H>
#include <AMReX_ParmParse.H>
#include <AMReX_REAL.H>
#include <cmath>

#include "mechanism.H"

#include "IndexDefines.H"
#include "PeleC.H"
#include "PelePhysics.H"
#include "ProblemSpecificFunctions.H"
#include "Tagging.H"

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void
pc_initdata(
  int i,
  int j,
  int k,
  amrex::Array4<amrex::Real> const& state,
  amrex::GeometryData const& geomdata,
  ProbParmDevice const& prob_parm)
{
  const amrex::Real* prob_lo = geomdata.ProbLo();
  const amrex::Real* dx = geomdata.CellSize();
  const amrex::Real x = prob_lo[0] + (i + 0.5) * dx[0];
  const amrex::Real y = prob_lo[1] + (j + 0.5) * dx[1];

  const amrex::Real r = std::sqrt(
    (x - prob_parm.bubble_cx) * (x - prob_parm.bubble_cx) +
    (y - prob_parm.bubble_cy) * (y - prob_parm.bubble_cy));
  amrex::Real alpha = (r < prob_parm.bubble_r) ? 0.0 : 1.0;
  if (prob_parm.interface_width > 0.0) {
    const amrex::Real eta = (r - prob_parm.bubble_r) / prob_parm.interface_width;
    alpha = 0.5 * (1.0 + std::tanh(eta));
    alpha = amrex::min(1.0, amrex::max(0.0, alpha));
  }

  const bool driver = x < prob_parm.shock_x;
  const amrex::Real p = driver ? prob_parm.p_left : prob_parm.p_right;
  const amrex::Real u = driver ? prob_parm.driver_u : 0.0;
  const amrex::Real light_fraction = 1.0 - alpha;
  const amrex::Real T =
    prob_parm.T_heavy * alpha + prob_parm.T_light * light_fraction;

  amrex::Real massfrac[NUM_SPECIES] = {0.0};
  massfrac[0] = 1.0;
  auto eos = pele::physics::PhysicsType::eos();
  amrex::Real rho = 0.0;
  amrex::Real e = 0.0;
  eos.PYT2RE(p, massfrac, T, rho, e);

  state(i, j, k, URHO) = rho;
  state(i, j, k, UMX) = rho * u;
  state(i, j, k, UMY) = 0.0;
  state(i, j, k, UMZ) = 0.0;
  state(i, j, k, UEINT) = rho * e;
  state(i, j, k, UEDEN) = rho * (e + 0.5 * u * u);
  state(i, j, k, UTEMP) = T;

#if NUM_ADV > 0
  state(i, j, k, UFA) = rho * alpha;
#endif
  for (int n = 0; n < NUM_SPECIES; n++) {
    state(i, j, k, UFS + n) = rho * massfrac[n];
  }
}

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void
bcnormal(
  const amrex::Real*,
  const amrex::Real s_int[NVAR],
  amrex::Real s_ext[NVAR],
  const int,
  const int,
  const amrex::Real,
  amrex::GeometryData const&,
  ProbParmDevice const&,
  const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>&)
{
  for (int n = 0; n < NVAR; n++) {
    s_ext[n] = s_int[n];
  }
}

void pc_prob_close();

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void
pc_check_initial_species(int, int, int, amrex::Array4<amrex::Real>&)
{
}

using ProblemSpecificFunctions = DefaultProblemSpecificFunctions;

#endif
