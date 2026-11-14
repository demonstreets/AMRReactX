#ifndef PROB_PARM_H
#define PROB_PARM_H

#include <AMReX_REAL.H>
#include <AMReX_GpuQualifiers.H>

struct ProbParmDevice
{
  amrex::Real p0 = 1.01325e6; // [erg cm^-3]
  amrex::Real T0 = 800.0;
  amrex::Real rho0 = 0.0;
  amrex::Real v0 = 0.0;
  amrex::Real Y_O2 = 0.233;
  amrex::Real Y_N2 = 0.767;
};

struct ProbParmHost
{
};

#endif
