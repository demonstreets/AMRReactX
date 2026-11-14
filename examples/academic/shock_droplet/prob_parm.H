#ifndef PROB_PARM_H
#define PROB_PARM_H

#include <AMReX_REAL.H>
#include <AMReX_GpuQualifiers.H>
#include <AMReX_GpuMemory.H>

struct ProbParmDevice
{
  // Left state (driver, high pressure / high temperature)
  amrex::Real p_left = 1.0e7;   // [dyn/cm^2] ~10 bar
  amrex::Real T_left = 2000.0;  // [K]
  // Right state (driven, low pressure / low temperature)
  amrex::Real p_right = 1.0e6;  // [dyn/cm^2] ~1 bar
  amrex::Real T_right = 300.0;  // [K]
  // Diaphragm position
  amrex::Real diaphragm = 25.0; // [cm]
  // Air composition (mass fractions)
  amrex::Real Y_O2 = 0.233;
  amrex::Real Y_N2 = 0.767;
  amrex::Real Y_NC7H16 = 0.0;
};

struct ProbParmHost
{
  ProbParmHost() = default;
};

#endif
