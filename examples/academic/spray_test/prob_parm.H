#ifndef PROB_PARM_H
#define PROB_PARM_H

#include <AMReX_REAL.H>
#include <AMReX_GpuQualifiers.H>
#include <AMReX_GpuMemory.H>

struct ProbParmDevice
{
  amrex::Real rho0 = 1.0;    // uniform density (g/cc)
  amrex::Real u0 = 1.0;      // uniform x-velocity (cm/s)
  amrex::Real p0 = 1.0e6;    // uniform pressure (dyn/cm^2)
  amrex::Real T0 = 300.0;    // uniform temperature (K)
  amrex::Real alpha_lo = 0.25; // left edge of α=1 region
  amrex::Real alpha_hi = 0.50; // right edge of α=1 region
};

struct ProbParmHost
{
  ProbParmHost() = default;
};
#endif
