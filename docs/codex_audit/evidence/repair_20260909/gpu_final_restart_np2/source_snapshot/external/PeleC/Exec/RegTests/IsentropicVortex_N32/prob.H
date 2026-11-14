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
  ProbParmDevice const& /*prob_parm*/)
{
  // Geometry
  const amrex::Real* prob_lo = geomdata.ProbLo();
  const amrex::Real* dx = geomdata.CellSize();
  const amrex::Real x = prob_lo[0] + (i + 0.5) * dx[0];
  const amrex::Real y = prob_lo[1] + (j + 0.5) * dx[1];
  amrex::Real z = 0;
  amrex::Real massfrac[NUM_SPECIES] = {0.0};
  massfrac[0] = 1.0;
#if AMREX_SPACEDIM == 3
  z = prob_lo[2] + (k + 0.5) * dx[2];
#endif

  // Isentropic vortex — parameters hardcoded for debugging
  constexpr amrex::Real gamma = 1.4;
  constexpr amrex::Real Rgas = 1.0;
  constexpr amrex::Real cp = gamma * Rgas / (gamma - 1.0); // 3.5

  // Background state
  constexpr amrex::Real rho_bg = 1.0;
  constexpr amrex::Real u_bg = 1.0;
  constexpr amrex::Real v_bg = 1.0;
  constexpr amrex::Real p_bg = 1.0 / gamma; // 0.714285714...
  constexpr amrex::Real T_bg = p_bg / (rho_bg * Rgas);

  // Vortex parameters
  constexpr amrex::Real x0 = 5.0;
  constexpr amrex::Real y0 = 5.0;
  constexpr amrex::Real Rv = 1.0;  // vortex radius
  constexpr amrex::Real eps = 2.0; // vortex strength

  // Displacements from vortex center
  const amrex::Real dx_v = x - x0;
  const amrex::Real dy_v = y - y0;
  const amrex::Real r2 = dx_v * dx_v + dy_v * dy_v;

  // Isentropic vortex velocity perturbations
  const amrex::Real du = -eps * (dy_v / Rv) * exp(-r2 / (2.0 * Rv * Rv));
  const amrex::Real dv = eps * (dx_v / Rv) * exp(-r2 / (2.0 * Rv * Rv));

  // Total velocity
  const amrex::Real u = u_bg + du;
  const amrex::Real v = v_bg + dv;
  const amrex::Real u2 = u * u + v * v;
  constexpr amrex::Real u2_bg = u_bg * u_bg + v_bg * v_bg;

  // Temperature from steady isentropic energy equation
  const amrex::Real T = T_bg + (u2_bg - u2) / (2.0 * cp);

  // Isentropic relation: T/rho^(gamma-1) = const
  const amrex::Real rho = rho_bg * pow(T / T_bg, 1.0 / (gamma - 1.0));
  const amrex::Real p = p_bg * pow(rho / rho_bg, gamma);

  // Set conserved state
  state(i, j, k, URHO) = rho;
  state(i, j, k, UMX) = rho * u;
  state(i, j, k, UMY) = rho * v;
  state(i, j, k, UMZ) = 0.0;

  // Internal energy: p = (gamma-1)*rho*e  =>  rho*e = p/(gamma-1)
  state(i, j, k, UEINT) = p / (gamma - 1.0);

  // Total energy: UEINT + kinetic
  state(i, j, k, UEDEN) =
    state(i, j, k, UEINT) + 0.5 * rho * u2;

  state(i, j, k, UTEMP) = T;

  // Species
  for (int n = 0; n < NUM_SPECIES; n++) {
    state(i, j, k, UFS + n) = 0;
  }
  state(i, j, k, UFS) = rho;
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
