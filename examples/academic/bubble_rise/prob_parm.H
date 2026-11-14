#ifndef PROB_PARM_H
#define PROB_PARM_H
#include <AMReX_REAL.H>
#include <AMReX_GpuQualifiers.H>
struct ProbParmDevice {
    amrex::Real rho_heavy = 1.0;
    amrex::Real rho_light = 0.1;
    amrex::Real p0 = 1.0;
    amrex::Real bubble_cx = 0.1;
    amrex::Real bubble_cy = 0.1;
    amrex::Real bubble_r = 0.025;
    amrex::Real interface_width = 0.0;
    amrex::Real buoyancy_accel = 9.81;
    amrex::Real buoyancy_start_time = 0.0;
    amrex::Real buoyancy_end_time = 1.0e200;
    amrex::Real buoyancy_ramp_time = 0.0;
    amrex::Real buoyancy_terminal_speed = -1.0;
    amrex::Real buoyancy_energy_correction = 1.0;
    amrex::Real surface_tension_sigma = 0.0;
    amrex::Real surface_tension_grad_floor = 1.0e-12;
    amrex::Real surface_tension_force_cap = -1.0;
    amrex::Real phase_viscosity_mu_heavy = 0.0;
    amrex::Real phase_viscosity_mu_light = 0.0;
    amrex::Real phase_viscosity_force_cap = -1.0;
    amrex::Real positivity_rhoe_floor = -1.0;
    amrex::Real positivity_temp_floor = -1.0;
};
struct ProbParmHost { ProbParmHost() = default; };
#endif
