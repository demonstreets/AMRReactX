#ifndef PROB_PARM_H
#define PROB_PARM_H
#include <AMReX_REAL.H>
#include <AMReX_GpuQualifiers.H>
struct ProbParmDevice {
    amrex::Real rho_heavy = 2.0;
    amrex::Real rho_light = 1.0;
    amrex::Real p0 = 2.5;
    amrex::Real gravity = 9.81;
    amrex::Real pert_amp = 0.05;
    int pert_mode = 2;
};
struct ProbParmHost { ProbParmHost() = default; };
#endif
