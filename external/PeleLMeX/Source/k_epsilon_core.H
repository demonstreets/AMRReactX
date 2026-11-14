#pragma once
#include "k_epsilon_constants.H"

namespace Turbulence {

// ============================================================
// Eddy viscosity: μ_t = C_μ * ρ * k² / ε
// Clipping: k = max(k, k_min), ε = max(ε, eps_min)
//           μ_t = min(C_μ * ρ * k² / ε, mu_t_max_ratio * μ_lam)
// ============================================================
double compute_mut(double rho, double k, double eps,
                   double mu_lam,
                   const KEpsilonConstants& C = KEpsilonConstants());

// ============================================================
// Turbulent production term: P_k = μ_t * S²
// S² = 2 * S_ij * S_ij
// S_ij computed from velocity gradients:
//   du/dx, du/dy, du/dz
//   dv/dx, dv/dy, dv/dz
//   dw/dx, dw/dy, dw/dz
// ============================================================
double compute_strain_sq(const double grad_u[3][3]);

double compute_production(double mut, double strain_sq);

// ============================================================
// Source terms
// S_k = P_k - ρ * ε
// S_ε = C_eps1 * (ε/k) * P_k - C_eps2 * ρ * ε² / k
// Clipping:
//   k = max(k, k_min)  prevents div-by-zero
//   ε = max(ε, eps_min)
//   P_k = max(P_k, 0)  production non-negative (physical constraint)
// ============================================================
void compute_source_terms(double rho, double k, double eps,
                          double P_k,
                          double& S_k, double& S_eps,
                          const KEpsilonConstants& C = KEpsilonConstants());

// ============================================================
// Effective diffusion coefficients (turbulent contribution)
// Γ_k  = μ_lam + μ_t / σ_k
// Γ_eps = μ_lam + μ_t / σ_eps
// ============================================================
double compute_diff_k(double mu_lam, double mu_t,
                      const KEpsilonConstants& C = KEpsilonConstants());
double compute_diff_eps(double mu_lam, double mu_t,
                        const KEpsilonConstants& C = KEpsilonConstants());

// ============================================================
// Boundary condition helpers: wall k and ε (standard k-ε wall functions)
// Based on friction velocity u_tau:
//   k_wall = u_tau² / sqrt(C_mu)
//   ε_wall = u_tau³ / (κ * y_p)    where κ=0.41, y_p = first-cell wall distance
// Note: full wall functions in Phase 2.3; these are the base formulas
// ============================================================
double compute_k_wall(double u_tau,
                      const KEpsilonConstants& C = KEpsilonConstants());
double compute_eps_wall(double u_tau, double y_p,
                        const KEpsilonConstants& C = KEpsilonConstants());

} // namespace Turbulence
