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
  const amrex::Real y = prob_lo[1] + (j + 0.5) * dx[1];
  amrex::Real z = 0;
  amrex::Real massfrac[NUM_SPECIES] = {0.0};
  massfrac[0] = 1.0;
#if AMREX_SPACEDIM == 3
  z = prob_lo[2] + (k + 0.5) * dx[2];
#endif

  // All parameters read from ProbParmDevice (set via prob.cpp + inputs)
  const amrex::Real gamma  = 1.4;               // GammaLaw EOS default
  const amrex::Real rho_bg = prob_parm.rho_bg;
  const amrex::Real u_bg   = prob_parm.u_bg;
  const amrex::Real v_bg   = prob_parm.v_bg;
  const amrex::Real p_bg   = prob_parm.p_bg;
  const amrex::Real T_bg   = prob_parm.T_bg;    // from EOS in probinit
  const amrex::Real cp_bg  = prob_parm.cp_bg;   // from EOS in probinit

  // Vortex parameters
  const amrex::Real x0  = prob_parm.center_x;
  const amrex::Real y0  = prob_parm.center_y;
  const amrex::Real Rv  = prob_parm.vortex_R;
  const amrex::Real dx_v = (x - x0) / Rv;
  const amrex::Real dy_v = (y - y0) / Rv;
  const amrex::Real r2 = dx_v * dx_v + dy_v * dy_v;

  amrex::Real u = u_bg;
  amrex::Real v = v_bg;
  amrex::Real T = T_bg;

  if (prob_parm.exact_vortex != 0) {
    // Standard smooth isentropic-vortex exact solution for ideal-gas Euler in
    // Mach-scaled units.  The dimensionless temperature ratio theta = T/T_inf
    // preserves p/rho^gamma and advects unchanged with the uniform background.
    constexpr amrex::Real pi = 3.141592653589793238462643383279502884;
    const amrex::Real beta = prob_parm.vortex_beta;
    const amrex::Real e = exp(0.5 * (1.0 - r2));
    const amrex::Real theta =
      1.0 - (gamma - 1.0) * beta * beta / (8.0 * gamma * pi * pi) * exp(1.0 - r2);
    AMREX_ALWAYS_ASSERT(theta > 0.0);
    u += -beta / (2.0 * pi) * e * dy_v;
    v +=  beta / (2.0 * pi) * e * dx_v;
    T = T_bg * theta;
  } else {
    const amrex::Real eps = prob_parm.vortex_eps;
    const amrex::Real e = exp(-r2 / 2.0);
    const amrex::Real du = -eps * dy_v * e;
    const amrex::Real dv =  eps * dx_v * e;
    u += du;
    v += dv;
    const amrex::Real u2 = u * u + v * v;
    const amrex::Real u2_bg = u_bg * u_bg + v_bg * v_bg;
    T = T_bg - (u2 - u2_bg) / (2.0 * cp_bg);
  }

  AMREX_ALWAYS_ASSERT(T > 0.0);

  const amrex::Real theta = T / T_bg;
  const amrex::Real rho = rho_bg * pow(theta, 1.0 / (gamma - 1.0));
  const amrex::Real p = p_bg * pow(rho / rho_bg, gamma);
  const amrex::Real u2 = u * u + v * v;

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
