#ifndef PROB_PARM_H
#define PROB_PARM_H

#include <AMReX_REAL.H>
#include <AMReX_GpuQualifiers.H>
#include <AMReX_GpuMemory.H>

struct ProbParmDevice
{
  // Isentropic vortex parameters
  amrex::Real vortex_eps = 0.5;   // legacy vortex strength (reduced to avoid T<0)
  amrex::Real vortex_beta = 5.0;  // standard exact isentropic-vortex strength
  amrex::Real vortex_R = 1.0;     // vortex radius / coordinate scaling
  int exact_vortex = 0;           // 0: legacy profile, 1: standard exact profile
  amrex::Real center_x = 5.0;
  amrex::Real center_y = 5.0;
  // Background state
  amrex::Real rho_bg = 1.0;
  amrex::Real u_bg = 1.0;
  amrex::Real v_bg = 1.0;
  amrex::Real p_bg = 0.714285714; // 1/gamma for gamma=1.4
  amrex::Real T_bg;
  amrex::Real rhoe_bg;
  amrex::Real cp_bg;              // specific heat from EOS (constant for GammaLaw)
};

struct ProbParmHost
{
  ProbParmHost() = default;
};
#endif
