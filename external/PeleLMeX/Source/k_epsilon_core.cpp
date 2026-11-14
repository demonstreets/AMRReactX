#include "k_epsilon_core.H"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>

namespace Turbulence {

// ============================================================
// Eddy viscosity: μ_t = C_μ * ρ * k² / ε
// ============================================================
double compute_mut(double rho, double k, double eps,
                   double mu_lam,
                   const KEpsilonConstants& C)
{
    // Clip k and ε to lower bounds
    k   = std::max(k,   C.k_min);
    eps = std::max(eps, C.eps_min);

    double mut = C.C_mu * rho * k * k / eps;

    // Upper-bound clipping: μ_t must not exceed mu_t_max_ratio * μ_lam
    double mut_max = C.mu_t_max_ratio * mu_lam;
    return std::min(mut, mut_max);
}

// ============================================================
// Strain rate tensor magnitude squared
// S_ij = 0.5 * (∂u_i/∂x_j + ∂u_j/∂x_i)
// S² = 2 * (S_xx² + S_yy² + S_zz² + 2*S_xy² + 2*S_xz² + 2*S_yz²)
// ============================================================
double compute_strain_sq(const double grad_u[3][3])
{
    // Diagonal: S_ii = ∂u_i/∂x_i
    double S_xx = grad_u[0][0];
    double S_yy = grad_u[1][1];
    double S_zz = grad_u[2][2];

    // Off-diagonal: S_ij = 0.5 * (∂u_i/∂x_j + ∂u_j/∂x_i)
    double S_xy = 0.5 * (grad_u[0][1] + grad_u[1][0]);
    double S_xz = 0.5 * (grad_u[0][2] + grad_u[2][0]);
    double S_yz = 0.5 * (grad_u[1][2] + grad_u[2][1]);

    // S² = 2 * Σ S_ij²
    return 2.0 * (S_xx * S_xx + S_yy * S_yy + S_zz * S_zz
                + 2.0 * S_xy * S_xy
                + 2.0 * S_xz * S_xz
                + 2.0 * S_yz * S_yz);
}

// ============================================================
// Turbulent production: P_k = μ_t * S²
// ============================================================
double compute_production(double mut, double strain_sq)
{
    return mut * strain_sq;
}

// ============================================================
// Source terms for k and ε
// ============================================================
void compute_source_terms(double rho, double k, double eps,
                          double P_k,
                          double& S_k, double& S_eps,
                          const KEpsilonConstants& C)
{
    // Clip to prevent division-by-zero and negative production
    k   = std::max(k,   C.k_min);
    eps = std::max(eps, C.eps_min);
    P_k = std::max(P_k, 0.0);

    S_k   = P_k - rho * eps;
    S_eps = C.C_eps1 * (eps / k) * P_k - C.C_eps2 * rho * eps * eps / k;
}

// ============================================================
// Effective diffusion coefficient for k
// ============================================================
double compute_diff_k(double mu_lam, double mu_t,
                      const KEpsilonConstants& C)
{
    return mu_lam + mu_t / C.sigma_k;
}

// ============================================================
// Effective diffusion coefficient for ε
// ============================================================
double compute_diff_eps(double mu_lam, double mu_t,
                        const KEpsilonConstants& C)
{
    return mu_lam + mu_t / C.sigma_eps;
}

// ============================================================
// Wall k from friction velocity
// ============================================================
double compute_k_wall(double u_tau,
                      const KEpsilonConstants& C)
{
    return u_tau * u_tau / std::sqrt(C.C_mu);
}

// ============================================================
// Wall ε from friction velocity and first-cell distance
// ============================================================
double compute_eps_wall(double u_tau, double y_p,
                        const KEpsilonConstants& C)
{
    if (y_p <= 0.0) {
        std::cerr << "Error: compute_eps_wall: y_p must be > 0, got " << y_p << std::endl;
        std::exit(1);
    }
    return u_tau * u_tau * u_tau / (C.kappa * y_p);
}

} // namespace Turbulence
