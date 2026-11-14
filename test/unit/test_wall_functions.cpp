#include "wall_functions.H"
#include <cmath>
#include <iostream>
#include <string>

// ---------- minimal test harness ----------
static int  g_passed = 0;
static int  g_failed = 0;
static std::string g_current_test;

#define TEST(name) static void test_##name()

#define CHECK(cond)                                                    \
    do {                                                               \
        if (!(cond)) {                                                 \
            std::cerr << "  FAIL: " << g_current_test                  \
                      << " [" << __LINE__ << "]: " << #cond << "\n";   \
            ++g_failed;                                                \
            return;                                                    \
        }                                                              \
    } while (0)

#define CHECK_NEAR(a, b, tol)                                          \
    do {                                                               \
        double _a = (a);                                               \
        double _b = (b);                                               \
        if (std::fabs(_a - _b) > (tol)) {                              \
            std::cerr << "  FAIL: " << g_current_test                  \
                      << " [" << __LINE__ << "]: "                     \
                      << #a << " (" << _a << ") vs "                   \
                      << #b << " (" << _b << ")  tol=" << (tol) << "\n"; \
            ++g_failed;                                                \
            return;                                                    \
        }                                                              \
    } while (0)

#define CHECK_FINITE(x)                                                \
    do {                                                               \
        double _x = (x);                                               \
        if (!std::isfinite(_x)) {                                      \
            std::cerr << "  FAIL: " << g_current_test                  \
                      << " [" << __LINE__ << "]: "                     \
                      << #x << " is not finite (" << _x << ")\n";      \
            ++g_failed;                                                \
            return;                                                    \
        }                                                              \
    } while (0)

#define RUN_TEST(name)                                                 \
    do {                                                               \
        g_current_test = #name;                                        \
        test_##name();                                                 \
    } while (0)

// ---------- test cases ----------

// Test 1: y+ basic calculation
//   y_p=0.01, u_tau=0.1, nu=1e-5 → y+ = 100
TEST(yplus_basic) {
    double yp = Turbulence::compute_yplus(0.01, 0.1, 1e-5);
    CHECK_NEAR(yp, 100.0, 1e-12);
    ++g_passed;
}

// Test 2: y+ with y_p = 0
TEST(yplus_zero) {
    double yp = Turbulence::compute_yplus(0.0, 0.1, 1e-5);
    CHECK_NEAR(yp, 0.0, 1e-15);
    ++g_passed;
}

// Test 3: in_log_layer check
TEST(in_log_layer_check) {
    Turbulence::KEpsilonConstants C;
    CHECK(Turbulence::in_log_layer(100.0, C) == true);
    CHECK(Turbulence::in_log_layer(3.0, C)   == false);
    ++g_passed;
}

// Test 4: Newton iteration converges for typical log-layer point
//   y_p=0.01, u_par=2.0, nu=1e-5
TEST(newton_converges) {
    Turbulence::KEpsilonConstants C;
    double u_tau = Turbulence::compute_utau(0.01, 2.0, 1e-5, C);

    // Must return a positive friction velocity
    CHECK(u_tau > 0.0);

    // y+ with computed u_tau must be in log layer
    double yp  = Turbulence::compute_yplus(0.01, u_tau, 1e-5);
    CHECK(yp >= C.yplus_threshold);

    // Verify the log-law relation is satisfied
    double u_plus = 2.0 / u_tau;
    double u_plus_law = std::log(yp) / C.kappa + C.B;
    CHECK_NEAR(u_plus, u_plus_law, 1e-6);

    ++g_passed;
}

// Test 5: Newton returns 0 when initial estimate is in viscous sublayer
//   Use y_p=1e-5 so that initial y+ ≈ 0.1 < 30
TEST(newton_viscous_sublayer) {
    Turbulence::KEpsilonConstants C;
    double u_tau = Turbulence::compute_utau(1e-5, 2.0, 1e-5, C);
    CHECK_NEAR(u_tau, 0.0, 1e-15);
    ++g_passed;
}

// Test 6: tau_wall = rho * u_tau^2
//   rho=1.2, u_tau=0.1 → tau_w = 0.012
TEST(tau_wall_basic) {
    double tw = Turbulence::compute_tau_wall(1.2, 0.1);
    CHECK_NEAR(tw, 0.012, 1e-15);
    ++g_passed;
}

// Test 7: P_k_wall = tau_w * u_par / y_p
//   tau_w=0.012, u_par=2.0, y_p=0.01 → P_k_wall = 2.4
TEST(production_wall_basic) {
    double Pk = Turbulence::compute_production_wall(0.012, 2.0, 0.01);
    CHECK_NEAR(Pk, 2.4, 1e-12);
    ++g_passed;
}

// Test 8: mu_t_wall = max(0, tau_w*y_p/u_par - mu_lam)
//   tau_w=0.012, u_par=2.0, y_p=0.01, mu_lam=1.8e-5
//   result = 6e-5 - 1.8e-5 = 4.2e-5
TEST(mut_wall_basic) {
    double mut = Turbulence::compute_mut_wall(0.012, 2.0, 0.01, 1.8e-5);
    CHECK_NEAR(mut, 4.2e-5, 1e-15);
    ++g_passed;
}

// Test 9: constant default values (B, yplus_threshold)
TEST(constant_defaults) {
    Turbulence::KEpsilonConstants C;
    CHECK_NEAR(C.B,                5.0,  1e-15);
    CHECK_NEAR(C.yplus_threshold, 30.0,  1e-15);
    CHECK(C.max_newton_iter == 20);
    CHECK_NEAR(C.newton_tol,       1.0e-8, 1e-20);
    ++g_passed;
}

// Test 10: mut_wall returns 0 (not negative) for small u_par
//   tau_w=0.012, u_par=1000.0 → tau_w*y_p/u_par = 1.2e-7
//   1.2e-7 - 1.8e-5 = -1.788e-5 → max(0, ...) = 0
TEST(mut_wall_non_negative) {
    double mut = Turbulence::compute_mut_wall(0.012, 1000.0, 0.01, 1.8e-5);
    CHECK_NEAR(mut, 0.0, 1e-15);
    CHECK(mut >= 0.0);
    ++g_passed;
}

// Test 11: compute_mut_wall u_par=0 → returns 0 (HIGH-1 fix)
TEST(mut_wall_u_par_zero) {
    double mut = Turbulence::compute_mut_wall(0.012, 0.0, 0.01, 1.8e-5);
    CHECK_NEAR(mut, 0.0, 1e-15);
    ++g_passed;
}

// Test 12: compute_utau non-convergence → returns NaN, no exit (HIGH-2 fix)
// Uses extreme parameters to stress Newton; the function must return
// (possibly NaN) without calling exit().  For this well-behaved convex
// log-law equation Newton converges quickly with the default 20 iterations,
// so we verify the process survives.  The NaN return path is also covered
// by test 14 (nu=0).
TEST(newton_no_exit) {
    Turbulence::KEpsilonConstants C;
    // Extreme but finite: y_p=1e-4, u_par=1e6, nu=1e-10
    // y+_init ≈ (5e4)*(1e-4)/(1e-10) = 5e10 >> 30, enters Newton
    double u_tau = Turbulence::compute_utau(1e-4, 1e6, 1e-10, C);
    // The critical property: we are still alive (no exit).
    // Return value must be finite (converged) or NaN (non-converged).
    if (std::isfinite(u_tau)) {
        CHECK(u_tau > 0.0);
    } else {
        CHECK(std::isnan(u_tau));
    }
    ++g_passed;
}

// Test 13: compute_production_wall y_p=0 → returns 0 (MEDIUM-1 fix)
TEST(production_wall_y_p_zero) {
    double Pk = Turbulence::compute_production_wall(0.012, 2.0, 0.0);
    CHECK_NEAR(Pk, 0.0, 1e-15);
    ++g_passed;
}

// Test 14: compute_utau nu=0 → returns NaN (MEDIUM-2 fix)
TEST(newton_nu_zero) {
    Turbulence::KEpsilonConstants C;
    double u_tau = Turbulence::compute_utau(0.01, 2.0, 0.0, C);
    CHECK(std::isnan(u_tau));
    ++g_passed;
}


// Test 15: log-law helper returns canonical smooth-wall U+
TEST(log_law_uplus_reference) {
    Turbulence::KEpsilonConstants C;
    const double yplus = 100.0;
    const double expected = std::log(yplus) / C.kappa + C.B;
    CHECK_NEAR(Turbulence::log_law_uplus(yplus, C), expected, 1e-14);
    CHECK_NEAR(Turbulence::log_law_uplus(0.0, C), 0.0, 1e-15);
    ++g_passed;
}

// Test 16: flat-plate skin-friction correlation and tau conversion
TEST(flat_plate_cf_reference) {
    const double rho = 1.225;
    const double u_inf = 10.0;
    const double re_x = 1.0e6;
    const double cf = Turbulence::flat_plate_cf_one_seventh(re_x);
    CHECK_NEAR(cf, 0.027 / std::pow(re_x, 1.0 / 7.0), 1e-15);

    const double tau = 0.5 * rho * u_inf * u_inf * cf;
    CHECK_NEAR(Turbulence::compute_skin_friction_coefficient(tau, rho, u_inf),
               cf, 1e-15);
    CHECK_NEAR(Turbulence::compute_skin_friction_coefficient(tau, 0.0, u_inf),
               0.0, 1e-15);
    CHECK_NEAR(Turbulence::flat_plate_cf_one_seventh(-1.0), 0.0, 1e-15);
    ++g_passed;
}

// Test 17: first-cell y+ target maps to wall distance consistently
TEST(first_cell_yplus_target) {
    const double nu = 1.5e-5;
    const double yplus_target = 50.0;
    const double u_tau = 0.2;
    const double y_p = yplus_target * nu / u_tau;
    CHECK_NEAR(Turbulence::compute_yplus(y_p, u_tau, nu), yplus_target, 1e-12);
    CHECK(Turbulence::in_log_layer(yplus_target));
    CHECK(!Turbulence::in_log_layer(5.0));
    ++g_passed;
}

// ---------- main ----------
int main()
{
    RUN_TEST(yplus_basic);
    RUN_TEST(yplus_zero);
    RUN_TEST(in_log_layer_check);
    RUN_TEST(newton_converges);
    RUN_TEST(newton_viscous_sublayer);
    RUN_TEST(tau_wall_basic);
    RUN_TEST(production_wall_basic);
    RUN_TEST(mut_wall_basic);
    RUN_TEST(constant_defaults);
    RUN_TEST(mut_wall_non_negative);
    RUN_TEST(mut_wall_u_par_zero);
    RUN_TEST(newton_no_exit);
    RUN_TEST(production_wall_y_p_zero);
    RUN_TEST(newton_nu_zero);
    RUN_TEST(log_law_uplus_reference);
    RUN_TEST(flat_plate_cf_reference);
    RUN_TEST(first_cell_yplus_target);

    std::cout << "\n=== Results ===\n";
    std::cout << "  Passed: " << g_passed << "\n";
    std::cout << "  Failed: " << g_failed << "\n";

    return g_failed > 0 ? 1 : 0;
}
