#ifndef PROB_PARM_H
#define PROB_PARM_H

#include <AMReX_REAL.H>
#include <AMReX_GpuQualifiers.H>
#include <AMReX_GpuMemory.H>

struct ProbParmDevice
{
  // Shock parameters
  amrex::Real shock_M = 10.0;
  amrex::Real gamma = 1.4;
  amrex::Real shock_x0 = 1.0 / 6.0;   // shock intersection with y=0
  amrex::Real shock_angle = 60.0;      // degrees from x-axis
  amrex::Real shock_tan;               // tan(angle) = sqrt(3)
  amrex::Real shock_nx;                // normal x-component
  amrex::Real shock_ny;                // normal y-component
  amrex::Real shock_speed_x;           // shock speed in x (lab frame)
  amrex::Real shock_speed_y;           // shock speed in y (lab frame)

  // Pre-shock (undisturbed) state
  amrex::Real rho_pre = 1.4;
  amrex::Real p_pre = 1.0;
  amrex::Real u_pre = 0.0;
  amrex::Real v_pre = 0.0;
  amrex::Real e_pre;       // specific internal energy
  amrex::Real rhoe_pre;    // rho * e
  amrex::Real a_pre;       // sound speed

  // Post-shock state (Rankine-Hugoniot)
  amrex::Real rho_post;
  amrex::Real p_post;
  amrex::Real u_post;
  amrex::Real v_post;
  amrex::Real e_post;
  amrex::Real rhoe_post;
  amrex::Real a_post;
  amrex::Real vn_post;     // post-shock normal velocity magnitude

  // Wedge
  amrex::Real wedge_start = 1.0 / 6.0;

  // y-hi position (for bcnormal)
  amrex::Real y_hi;
};

struct ProbParmHost
{
  ProbParmHost() = default;
};
#endif
