#pragma once
#include "k_epsilon_constants.H"

namespace Turbulence {

// ============================================================
// y+ computation: y+ = y_p * u_tau / nu
// ============================================================
double compute_yplus(double y_p, double u_tau, double nu);

// Log-law dimensionless velocity: U+ = ln(y+)/kappa + B.
double log_law_uplus(double yplus,
                     const KEpsilonConstants& C = KEpsilonConstants());

// ============================================================
// Friction velocity via Newton-Raphson iteration
// Solves the log-law equation for u_tau:
//   u_par / u_tau = (1/kappa) * ln(y_p * u_tau / nu) + B
// Input:  y_p   — wall distance of first cell centre
//         u_par — tangential velocity magnitude
//         nu    — kinematic viscosity
//         C     — model constants (kappa, B, yplus_threshold, …)
// Returns: u_tau (friction velocity)
//   - 0 if the initial y+ estimate is below yplus_threshold
//     (flow is in the viscous sub-layer)
//   - NaN if nu <= 0 or Newton does not converge (caller must handle)
// ============================================================
double compute_utau(double y_p, double u_par, double nu,
                    const KEpsilonConstants& C = KEpsilonConstants());

// ============================================================
// Wall shear stress: tau_w = rho * u_tau^2
// ============================================================
double compute_tau_wall(double rho, double u_tau);

// Skin-friction coefficient from wall shear: Cf = tau_w/(0.5*rho*U_inf^2).
double compute_skin_friction_coefficient(double tau_wall, double rho, double u_inf);

// Turbulent flat-plate one-seventh-power correlation: Cf = 0.027/Re_x^(1/7).
double flat_plate_cf_one_seventh(double re_x);

// ============================================================
// Wall production correction
// P_k_wall = (tau_w * u_par) / y_p
// Based on local-equilibrium hypothesis: P_k ≈ rho * epsilon
// in the log-law region.
// ============================================================
double compute_production_wall(double tau_wall, double u_par, double y_p);

// ============================================================
// Effective turbulent viscosity at the wall
// mu_t_eff = max(0, tau_w * y_p / u_par - mu_lam)
// Prevents the standard k-epsilon formula from over-predicting
// wall mu_t.
// ============================================================
double compute_mut_wall(double tau_wall, double u_par,
                        double y_p, double mu_lam);

// ============================================================
// Helper: check whether a y+ value is in the log-law region
// ============================================================
bool in_log_layer(double yplus,
                  const KEpsilonConstants& C = KEpsilonConstants());

} // namespace Turbulence
