#pragma once
#include "StiffenedGas.H"
#include <AMReX_REAL.H>
#include <AMReX_Gpu.H>

// Result struct matching what pc_ctoprim needs
struct TwoPhaseResult {
    amrex::Real T;
    amrex::Real p;
    amrex::Real cs;
    amrex::Real gam1;
    amrex::Real dpdr_e;
    amrex::Real dpde;
};

// alpha_tiny: threshold below which pure gas EOS is used
template <typename GasEOS>
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
TwoPhaseResult twophase_mixture_eos(
    amrex::Real rho, amrex::Real e, amrex::Real alpha,
    const amrex::Real* massfrac,
    const GasEOS& gas_eos,
    const StiffenedGasParams& sg,
    amrex::Real cv_liquid,
    amrex::Real alpha_tiny = 1.0e-8)
{
    TwoPhaseResult res;
    bool use_stiffened_gas_sound_speed = false;

    if (alpha < alpha_tiny) {
        // Pure gas: delegate entirely to the existing gas EOS.
        gas_eos.REY2T(rho, e, massfrac, res.T);
        gas_eos.RTY2P(rho, res.T, massfrac, res.p);
        gas_eos.RTY2Cs(rho, res.T, massfrac, res.cs);
        gas_eos.RTY2G(rho, res.T, massfrac, res.gam1);
        gas_eos.RTY2dpde_dpdre(rho, res.T, massfrac, res.dpde, res.dpdr_e);
    } else if (alpha > 1.0 - alpha_tiny) {
        use_stiffened_gas_sound_speed = true;
        // Pure liquid: StiffenedGas.
        res.p = sg_p(sg, rho, e);
        res.T = sg_T(sg, rho, e, cv_liquid);
        res.gam1 = sg.gamma;
        res.dpdr_e = sg_dpdr_e(sg, e);
        res.dpde = sg_dpde(sg, rho);
    } else {
        use_stiffened_gas_sound_speed = true;
        // Interface cell: simplified liquid-dominated closure until full
        // isobaric/isothermal energy partitioning is implemented.
        res.p = sg_p(sg, rho, e);
        res.T = sg_T(sg, rho, e, cv_liquid);
        res.gam1 = sg.gamma;
        res.dpdr_e = sg_dpdr_e(sg, e);
        res.dpde = sg_dpde(sg, rho);
    }

    // Clamp pressure before any stiffened-gas sound-speed evaluation.
    res.p = amrex::max(res.p, 1.0);
    if (use_stiffened_gas_sound_speed) {
        res.cs = sg_cs(sg, rho, res.p);
    }
    res.cs = amrex::max(res.cs, 1.0);

    return res;
}
