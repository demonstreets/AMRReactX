#pragma once

#include "StiffenedGas.H"
#include <AMReX_REAL.H>
#include <AMReX_Gpu.H>
#include <AMReX_Math.H>
#include <cmath>

// Per-side EOS parameters for two-phase HLLC
struct PhaseEOSParams {
    amrex::Real gamma;   // ratio of specific heats
    amrex::Real p_inf;   // stiffened-gas reference pressure, 0 for ideal gas
};

// Sound speed: c = sqrt(gamma*(p + p_inf)/rho)
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real twophase_soundspeed(
    const amrex::Real rho,
    const amrex::Real p,
    const PhaseEOSParams& eos)
{
    return std::sqrt(eos.gamma * (p + eos.p_inf) / rho);
}

// Specific internal energy from pressure and density (stiffened-gas EOS):
//   e = (p + gamma*p_inf) / ((gamma-1)*rho)
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real twophase_internal_energy(
    const amrex::Real rho,
    const amrex::Real p,
    const PhaseEOSParams& eos)
{
    return (p + eos.gamma * eos.p_inf) / ((eos.gamma - 1.0) * rho);
}

// PVRS pressure estimate (Toro §9.5.2)
// Returns max(p_pvrs, 1.0) to keep pressure positive
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real twophase_pvrs(
    const amrex::Real rhoL, const amrex::Real uL,
    const amrex::Real pL, const amrex::Real cL,
    const amrex::Real rhoR, const amrex::Real uR,
    const amrex::Real pR, const amrex::Real cR)
{
    const amrex::Real p_pvrs =
        0.5 * (pL + pR) - 0.125 * (uR - uL) * (rhoL + rhoR) * (cL + cR);
    return amrex::max<amrex::Real>(p_pvrs, 1.0);
}

// ============================================================================
// Two-phase HLLC Riemann solver
//
// HLLC three-wave structure: S_L < S* < S_R
//
//   Left state L     Left star *L    Right star *R    Right state R
//      ρ_L              ρ*_L            ρ*_R              ρ_R
//      u_L              S*              S*                u_R
//      p_L              p*              p*                p_R
//      e_L              e*_L            e*_R              e_R
//
// Star-state internal energy uses stiffened-gas EOS at p*:
//   e*_K = (p* + γ_K·p_∞,K) / ((γ_K-1)·ρ*_K)      K = L, R
//
// Species are passively advected: Y_face follows the upwind side.
// ============================================================================
template <int NSPEC>
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void twophase_hllc_flux(
    const amrex::Real rhoL, const amrex::Real uL,
    const amrex::Real pL,   const amrex::Real eL,
    const amrex::Real* YL,  const PhaseEOSParams& eosL,
    const amrex::Real rhoR, const amrex::Real uR,
    const amrex::Real pR,   const amrex::Real eR,
    const amrex::Real* YR,  const PhaseEOSParams& eosR,
    amrex::Real& flux_rho,
    amrex::Real* flux_rhoY,
    amrex::Real& flux_u,
    amrex::Real& flux_eden,
    amrex::Real& flux_eint,
    amrex::Real& ustar,
    amrex::Real* Ystar)
{
    // ---- 1. Sound speeds ----
    const amrex::Real cL = twophase_soundspeed(rhoL, pL, eosL);
    const amrex::Real cR = twophase_soundspeed(rhoR, pR, eosR);

    // ---- 2. Pressure estimate via PVRS ----
    const amrex::Real pstar = twophase_pvrs(rhoL, uL, pL, cL, rhoR, uR, pR, cR);

    // ---- 3. Wave speed q_k factor (stiffened-gas compatible) ----
    // q = 1 for rarefaction (p* ≤ p); q > 1 for shock
    auto wave_q = [](amrex::Real ps, amrex::Real pk, amrex::Real gk) {
        if (ps <= pk) { return 1.0; }
        return std::sqrt(1.0 + (gk + 1.0) / (2.0 * gk) * (ps / pk - 1.0));
    };
    const amrex::Real qL = wave_q(pstar, pL, eosL.gamma);
    const amrex::Real qR = wave_q(pstar, pR, eosR.gamma);

    // ---- 4. Nonlinear wave speeds ----
    const amrex::Real SL = uL - cL * qL;
    const amrex::Real SR = uR + cR * qR;

    // ---- 5. Contact wave speed (HLLC, Toro Eq 10.37) ----
    const amrex::Real denom = rhoL * (SL - uL) - rhoR * (SR - uR);
    const amrex::Real Sstar = (std::abs(denom) > 1.0e-40)
        ? (pR - pL + rhoL * uL * (SL - uL) - rhoR * uR * (SR - uR)) / denom
        : 0.5 * (uL + uR);

    // ---- 6. Star region densities (Toro Eq 10.38) ----
    const amrex::Real rhoL_star = rhoL * (SL - uL) / (SL - Sstar);
    const amrex::Real rhoR_star = rhoR * (SR - uR) / (SR - Sstar);

    // ---- 7. Star region internal energies (stiffened-gas EOS at p*) ----
    const amrex::Real eL_star = twophase_internal_energy(rhoL_star, pstar, eosL);
    const amrex::Real eR_star = twophase_internal_energy(rhoR_star, pstar, eosR);

    // Total energy per unit mass: E = e + 0.5*u^2
    const amrex::Real EL = 0.5 * uL * uL + eL;
    const amrex::Real ER = 0.5 * uR * uR + eR;
    const amrex::Real EL_star = 0.5 * Sstar * Sstar + eL_star;
    const amrex::Real ER_star = 0.5 * Sstar * Sstar + eR_star;

    // ---- 8. Upwind based on wave speeds ----
    amrex::Real flux_rho_tmp, flux_u_tmp, flux_E_tmp, flux_eint_tmp;
    amrex::Real Y_face[NSPEC];

    if (SL >= 0.0) {
        // Supersonic left
        flux_rho_tmp  = rhoL * uL;
        flux_u_tmp    = rhoL * uL * uL + pL;
        flux_E_tmp    = (rhoL * EL + pL) * uL;
        flux_eint_tmp = rhoL * uL * eL;
        for (int n = 0; n < NSPEC; n++) { Y_face[n] = YL[n]; }
        ustar = uL;
    } else if (Sstar >= 0.0) {
        // Left star region (HLLC flux)
        flux_rho_tmp  = rhoL * uL + SL * (rhoL_star - rhoL);
        flux_u_tmp    = (rhoL * uL * uL + pL) + SL * (rhoL_star * Sstar - rhoL * uL);
        flux_E_tmp    = (rhoL * EL + pL) * uL + SL * (rhoL_star * EL_star - rhoL * EL);
        flux_eint_tmp = rhoL_star * Sstar * eL_star;
        for (int n = 0; n < NSPEC; n++) { Y_face[n] = YL[n]; }
        ustar = Sstar;
    } else if (SR >= 0.0) {
        // Right star region (HLLC flux)
        flux_rho_tmp  = rhoR * uR + SR * (rhoR_star - rhoR);
        flux_u_tmp    = (rhoR * uR * uR + pR) + SR * (rhoR_star * Sstar - rhoR * uR);
        flux_E_tmp    = (rhoR * ER + pR) * uR + SR * (rhoR_star * ER_star - rhoR * ER);
        flux_eint_tmp = rhoR_star * Sstar * eR_star;
        for (int n = 0; n < NSPEC; n++) { Y_face[n] = YR[n]; }
        ustar = Sstar;
    } else {
        // Supersonic right
        flux_rho_tmp  = rhoR * uR;
        flux_u_tmp    = rhoR * uR * uR + pR;
        flux_E_tmp    = (rhoR * ER + pR) * uR;
        flux_eint_tmp = rhoR * uR * eR;
        for (int n = 0; n < NSPEC; n++) { Y_face[n] = YR[n]; }
        ustar = uR;
    }

    // ---- 9. Populate outputs ----
    flux_rho  = flux_rho_tmp;
    flux_u    = flux_u_tmp;
    flux_eden = flux_E_tmp;
    flux_eint = flux_eint_tmp;
    for (int n = 0; n < NSPEC; n++) {
        flux_rhoY[n] = flux_rho_tmp * Y_face[n];
        Ystar[n]     = Y_face[n];
    }
}
