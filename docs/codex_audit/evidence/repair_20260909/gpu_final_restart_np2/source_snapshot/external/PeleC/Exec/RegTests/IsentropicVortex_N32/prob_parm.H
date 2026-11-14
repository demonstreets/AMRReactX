#ifndef PROB_PARM_H
#define PROB_PARM_H

#include <AMReX_REAL.H>
#include <AMReX_GpuQualifiers.H>
#include <AMReX_GpuMemory.H>

struct ProbParmDevice
{
  // Isentropic vortex parameters
  amrex::Real vortex_eps = 5.0;   // vortex strength
  amrex::Real vortex_R = 1.0;     // vortex radius
  amrex::Real center_x = 5.0;
  amrex::Real center_y = 5.0;
  // Background state
  amrex::Real rho_bg = 1.0;
  amrex::Real u_bg = 1.0;
  amrex::Real v_bg = 1.0;
  amrex::Real p_bg = 0.714285714; // 1/gamma for gamma=1.4
  amrex::Real T_bg;
  amrex::Real rhoe_bg;
};

struct ProbParmHost
{
  ProbParmHost() = default;
};
#endif
