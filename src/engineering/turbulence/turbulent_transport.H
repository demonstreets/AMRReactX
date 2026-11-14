#pragma once
#include "k_epsilon_constants.H"

namespace Turbulence {

// ============================================================
// Turbulent diffusivity: D_t = mu_t / (rho * Sc_t)
//
// Input:  mu_t (turbulent eddy viscosity), rho (density),
//         Sc_t (turbulent Schmidt number, e.g. KEpsilonConstants::Sc_t)
// Return: D_t (m²/s)
// Guard:  rho <= 0 → return 0.0
// ============================================================
inline double compute_turbulent_diffusivity(
    double mu_t, double rho,
    double Sc_t)
{
    if (rho <= 0.0) return 0.0;
    return mu_t / (rho * Sc_t);
}

// ============================================================
// Effective diffusivity: D_eff = D_lam + D_t
// ============================================================
inline double compute_effective_diffusivity(
    double D_lam, double mu_t, double rho,
    double Sc_t)
{
    return D_lam + compute_turbulent_diffusivity(mu_t, rho, Sc_t);
}

// ============================================================
// Effective viscosity: mu_eff = mu_lam + mu_t
// ============================================================
inline double compute_effective_viscosity(double mu_lam, double mu_t)
{
    return mu_lam + mu_t;
}

// ============================================================
// Batch effective diffusivities for N species.
// D_lam[i] are laminar diffusivities; D_eff[i] are filled with
// D_lam[i] + D_t (same D_t for all).
// ============================================================
inline void compute_effective_diffusivities(
    const double* D_lam, int n_species,
    double mu_t, double rho, double Sc_t,
    double* D_eff)
{
    double D_t = compute_turbulent_diffusivity(mu_t, rho, Sc_t);
    for (int i = 0; i < n_species; ++i) {
        D_eff[i] = D_lam[i] + D_t;
    }
}

} // namespace Turbulence
