#ifndef PROB_PARM_H
#define PROB_PARM_H
#include <AMReX_REAL.H>
#include <AMReX_GpuContainers.H>
#include "mechanism.H"
struct ProbParmDevice {
  amrex::Real front=2., perturbation=0., width=4.;
  int perturbation_mode=1;
  amrex::Real p0=506625., T0=300.;
  amrex::GpuArray<amrex::Real,NUM_SPECIES> Y0{};
  int rows=0;
  const amrex::Real* profile=nullptr;
};
struct ProbParmHost {
  amrex::Gpu::DeviceVector<amrex::Real> profile;
};
#endif
