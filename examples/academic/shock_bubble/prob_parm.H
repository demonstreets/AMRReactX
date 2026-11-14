#ifndef SHOCK_BUBBLE_PROB_PARM_H
#define SHOCK_BUBBLE_PROB_PARM_H

#include <AMReX_GpuQualifiers.H>
#include <AMReX_REAL.H>

struct ProbParmDevice {
  amrex::Real T_heavy = 300.0;
  amrex::Real T_light = 3000.0;
  amrex::Real p_left = 8.0e5;
  amrex::Real p_right = 1.0e5;
  amrex::Real shock_x = 0.20;
  amrex::Real driver_u = 250.0;
  amrex::Real bubble_cx = 0.42;
  amrex::Real bubble_cy = 0.125;
  amrex::Real bubble_r = 0.055;
  amrex::Real interface_width = 0.006;
  amrex::Real positivity_rhoe_floor = 1.0e-12;
  amrex::Real positivity_temp_floor = 1.0e-12;
};

struct ProbParmHost {
  ProbParmHost() = default;
};

#endif
