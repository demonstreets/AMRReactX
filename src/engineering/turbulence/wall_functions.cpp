#include "wall_functions.H"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>

namespace Turbulence {

// ============================================================
// y+ = y_p * u_tau / nu
// ============================================================
double compute_yplus(double y_p, double u_tau, double nu)
{
    if (y_p < 0.0 || u_tau < 0.0 || nu <= 0.0) {
        return 0.0;
    }
    return y_p * u_tau / nu;
}

double log_law_uplus(double yplus, const KEpsilonConstants& C)
{
    if (yplus <= 0.0 || C.kappa <= 0.0) {
        return 0.0;
    }
    return std::log(yplus) / C.kappa + C.B;
}

// ============================================================
// Friction velocity via Newton-Raphson iteration
//
// Solve  f(u_tau) = u_tau * [(1/kappa)*ln(y_p*u_tau/nu) + B] - u_par = 0
//        f'(u_tau) = (1/kappa)*ln(y_p*u_tau/nu) + B + 1/kappa
// ============================================================
double compute_utau(double y_p, double u_par, double nu,
                    const KEpsilonConstants& C)
{
    const double inv_kappa = 1.0 / C.kappa;
    if (nu <= 0.0)
        return std::numeric_limits<double>::quiet_NaN();

    // Initial guess: u_tau = u_par / 20  (corresponds to u+ ~ 20)
    double ut = u_par / 20.0;

    // Check whether the initial estimate falls in the viscous sub-layer
    double yp_init = compute_yplus(y_p, ut, nu);
    if (yp_init < C.yplus_threshold) {
        return 0.0;
    }

    for (int iter = 0; iter < C.max_newton_iter; ++iter) {
        double yp  = y_p * ut / nu;
        double log_yp = std::log(yp);
        double A   = inv_kappa * log_yp + C.B;      // u+ = (1/kappa)*ln(y+) + B
        double f   = ut * A - u_par;                 // residual
        double df  = A + inv_kappa;                  // derivative

        // Convergence check
        if (std::fabs(f) < C.newton_tol) {
            return ut;
        }

        // Newton step
        double ut_new = ut - f / df;

        // Alternative convergence: step size
        if (std::fabs(ut_new - ut) < C.newton_tol) {
            return ut_new;
        }

        ut = ut_new;
    }

    std::cerr << "Error: compute_utau: Newton-Raphson did not converge\n"
              << "  y_p = " << y_p << ", u_par = " << u_par
              << ", nu = " << nu << "\n"
              << "  after " << C.max_newton_iter << " iterations\n";
    return std::numeric_limits<double>::quiet_NaN();
}

// ============================================================
// tau_w = rho * u_tau^2
// ============================================================
double compute_tau_wall(double rho, double u_tau)
{
    if (rho <= 0.0 || u_tau < 0.0) {
        return 0.0;
    }
    return rho * u_tau * u_tau;
}

double compute_skin_friction_coefficient(double tau_wall, double rho, double u_inf)
{
    if (tau_wall < 0.0 || rho <= 0.0 || u_inf <= 0.0) {
        return 0.0;
    }
    return tau_wall / (0.5 * rho * u_inf * u_inf);
}

double flat_plate_cf_one_seventh(double re_x)
{
    if (re_x <= 0.0 || !std::isfinite(re_x)) {
        return 0.0;
    }
    return 0.027 / std::pow(re_x, 1.0 / 7.0);
}

// ============================================================
// P_k_wall = (tau_w * u_par) / y_p
// ============================================================
double compute_production_wall(double tau_wall, double u_par, double y_p)
{
    if (y_p <= 0.0)
        return 0.0;
    return tau_wall * u_par / y_p;
}

// ============================================================
// mu_t_eff = max(0, tau_w * y_p / u_par - mu_lam)
// ============================================================
double compute_mut_wall(double tau_wall, double u_par,
                        double y_p, double mu_lam)
{
    if (u_par <= 0.0)
        return 0.0;
    double result = tau_wall * y_p / u_par - mu_lam;
    return std::max(0.0, result);
}

// ============================================================
// Check whether y+ is in the log-law region
// ============================================================
bool in_log_layer(double yplus, const KEpsilonConstants& C)
{
    return yplus >= C.yplus_threshold;
}

} // namespace Turbulence