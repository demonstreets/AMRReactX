#pragma once
#include <AMReX_REAL.H>
#include <AMReX_Gpu.H>
#include <cmath>

struct StiffenedGasParams {
    amrex::Real gamma;   // gamma_l, typically 1.1-7.0
    amrex::Real p_inf;   // p_infinity [pressure units]; PeleC CGS default 6e9 dyn/cm^2
};

// p = (gamma-1)*rho*e - gamma*p_inf
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real sg_p(const StiffenedGasParams& sg, amrex::Real rho, amrex::Real e) {
    return (sg.gamma - 1.0) * rho * e - sg.gamma * sg.p_inf;
}

// e = (p + gamma*p_inf) / ((gamma-1)*rho)
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real sg_e(const StiffenedGasParams& sg, amrex::Real rho, amrex::Real p) {
    return (p + sg.gamma * sg.p_inf) / ((sg.gamma - 1.0) * rho);
}

// Caloric stiffened gas with zero reference-energy offset: e = cv*T + p_inf/rho.
// Parameters must be calibrated together; this is not a water property table.
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real sg_T(const StiffenedGasParams& sg, amrex::Real rho, amrex::Real e, amrex::Real cv) {
    return (e - sg.p_inf / rho) / cv;
}

// Sound speed: c = sqrt(gamma*(p + p_inf)/rho)
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real sg_cs(const StiffenedGasParams& sg, amrex::Real rho, amrex::Real p) {
    return std::sqrt(sg.gamma * (p + sg.p_inf) / rho);
}

// dp/d(rho) at constant e
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real sg_dpdr_e(const StiffenedGasParams& sg, amrex::Real e) {
    return (sg.gamma - 1.0) * e;
}

// dp/de at constant rho
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real sg_dpde(const StiffenedGasParams& sg, amrex::Real rho) {
    return (sg.gamma - 1.0) * rho;
}
