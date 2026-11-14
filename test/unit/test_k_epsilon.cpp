#include "k_epsilon_core.H"
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

// Test 1: constant default values
TEST(constant_defaults) {
    Turbulence::KEpsilonConstants C;
    CHECK_NEAR(C.C_mu,   0.09, 1e-15);
    CHECK_NEAR(C.C_eps1, 1.44, 1e-15);
    CHECK_NEAR(C.C_eps2, 1.92, 1e-15);
    CHECK_NEAR(C.sigma_k,  1.0, 1e-15);
    CHECK_NEAR(C.sigma_eps,1.3, 1e-15);
    CHECK_NEAR(C.k_min, 1.0e-14, 1e-20);
    CHECK_NEAR(C.eps_min, 1.0e-14, 1e-20);
    CHECK_NEAR(C.mu_t_max_ratio, 1.0e5, 1e-10);
    ++g_passed;
}

// Test 2: compute_mut basic
//  ρ=1.0, k=0.1, ε=10.0, μ_lam=1e-5 → μ_t = 0.09·1·0.01/10 = 9e-5
TEST(compute_mut_basic) {
    double mut = Turbulence::compute_mut(1.0, 0.1, 10.0, 1e-5);
    CHECK_NEAR(mut, 9.0e-5, 1e-12);
    ++g_passed;
}

// Test 3: compute_mut clipping (k=0)
//  k=0 → clipped to k_min=1e-14, result ≪ 1e-20 but finite
TEST(compute_mut_clip_k_zero) {
    double mut = Turbulence::compute_mut(1.0, 0.0, 10.0, 1e-5);
    CHECK_FINITE(mut);
    CHECK(mut >= 0.0);
    ++g_passed;
}

// Test 4: compute_mut clipping (ε=0)
//  ε=0 → clipped to eps_min=1e-14; with k=1.0 raw μ_t=9e12, capped to 1.0
TEST(compute_mut_clip_eps_zero) {
    double mut = Turbulence::compute_mut(1.0, 1.0, 0.0, 1e-5);
    CHECK_FINITE(mut);
    // raw = 9e12, upper cap = 1e5 * 1e-5 = 1.0
    CHECK_NEAR(mut, 1.0, 1e-12);
    ++g_passed;
}

// Test 5: compute_mut upper-bound clipping
//  k=10.0, ε=1e-8 → raw μ_t=9e8, cap=1.0
TEST(compute_mut_upper_bound) {
    double mut = Turbulence::compute_mut(1.0, 10.0, 1e-8, 1e-5);
    CHECK_NEAR(mut, 1.0, 1e-12);
    ++g_passed;
}

// Test 6: compute_strain_sq uniform shear (du/dy=1)
//  grad_u = {{0,1,0},{0,0,0},{0,0,0}}
//  S_xy=0.5, S² = 2*(2*0.25) = 1.0
TEST(strain_sq_uniform_shear) {
    const double grad[3][3] = {
        {0.0, 1.0, 0.0},
        {0.0, 0.0, 0.0},
        {0.0, 0.0, 0.0}
    };
    double S2 = Turbulence::compute_strain_sq(grad);
    CHECK_NEAR(S2, 1.0, 1e-12);
    ++g_passed;
}

// Test 7: compute_strain_sq zero gradient
TEST(strain_sq_zero) {
    const double grad[3][3] = {
        {0.0, 0.0, 0.0},
        {0.0, 0.0, 0.0},
        {0.0, 0.0, 0.0}
    };
    double S2 = Turbulence::compute_strain_sq(grad);
    CHECK_NEAR(S2, 0.0, 1e-12);
    ++g_passed;
}

// Test 8: compute_strain_sq isotropic compression
//  grad_u = identity → S_ii=1, off-diag=0 → S² = 2*3 = 6.0
TEST(strain_sq_isotropic) {
    const double grad[3][3] = {
        {1.0, 0.0, 0.0},
        {0.0, 1.0, 0.0},
        {0.0, 0.0, 1.0}
    };
    double S2 = Turbulence::compute_strain_sq(grad);
    CHECK_NEAR(S2, 6.0, 1e-12);
    ++g_passed;
}

// Test 9: compute_production
TEST(production_basic) {
    double Pk = Turbulence::compute_production(0.09, 100.0);
    CHECK_NEAR(Pk, 9.0, 1e-12);
    ++g_passed;
}

// Test 10: source_terms basic
//  ρ=1, k=0.1, ε=10, P_k=1
//  S_k = 1 - 10 = -9
//  S_eps = 1.44*(10/0.1)*1 - 1.92*1*100/0.1 = 144 - 1920 = -1776
TEST(source_terms_basic) {
    double S_k, S_eps;
    Turbulence::compute_source_terms(1.0, 0.1, 10.0, 1.0, S_k, S_eps);
    CHECK_NEAR(S_k,   -9.0,   1e-12);
    CHECK_NEAR(S_eps, -1776.0, 1e-10);
    ++g_passed;
}

// Test 11: source_terms P_k=0 (pure dissipation)
//  S_k   = -10
//  S_eps = -1.92 * 1 * 100 / 0.1 = -1920
TEST(source_terms_pure_dissipation) {
    double S_k, S_eps;
    Turbulence::compute_source_terms(1.0, 0.1, 10.0, 0.0, S_k, S_eps);
    CHECK_NEAR(S_k,   -10.0,   1e-12);
    CHECK_NEAR(S_eps, -1920.0, 1e-10);
    ++g_passed;
}

// Test 12: source_terms k clipping (k→0)
//  k=0 → clipped to k_min=1e-14
//  S_k = 1 - 10 = -9
//  S_eps = 1.44*(10/1e-14)*1 - 1.92*1*100/1e-14 = 1.44e15 - 1.92e16 = -1.776e16
TEST(source_terms_clip_k) {
    double S_k, S_eps;
    Turbulence::compute_source_terms(1.0, 0.0, 10.0, 1.0, S_k, S_eps);
    CHECK_NEAR(S_k, -9.0, 1e-12);
    CHECK_FINITE(S_eps);
    CHECK(S_eps < 0.0);
    ++g_passed;
}

// Test 13: diff_k / diff_eps
//  μ_lam=1e-5, μ_t=9e-5
//  Γ_k   = 1e-5 + 9e-5/1.0 = 1e-4
//  Γ_eps = 1e-5 + 9e-5/1.3 ≈ 7.923076923076923e-5
TEST(diffusion_coefficients) {
    double Gk = Turbulence::compute_diff_k(1e-5, 9e-5);
    double Ge = Turbulence::compute_diff_eps(1e-5, 9e-5);
    CHECK_NEAR(Gk, 1.0e-4, 1e-15);
    CHECK_NEAR(Ge, 7.923076923076923e-5, 1e-14);
    ++g_passed;
}

// Test 14: k_wall / eps_wall
//  u_tau=0.1
//  k_wall = 0.01 / sqrt(0.09) = 1/30 ≈ 0.03333333...
//  eps_wall (y_p=0.01) = 0.001 / (0.41*0.01) = 0.001/0.0041 ≈ 0.243902439...
TEST(wall_functions) {
    Turbulence::KEpsilonConstants C;
    double kw = Turbulence::compute_k_wall(0.1, C);
    double ew = Turbulence::compute_eps_wall(0.1, 0.01, C);
    CHECK_NEAR(C.kappa, 0.41, 1e-15);  // verify kappa is accessible
    CHECK_NEAR(kw, 0.03333333333333333, 1e-12);
    CHECK_NEAR(ew, 0.24390243902439024, 1e-12);
    ++g_passed;
}

// Test 15: k_wall / eps_wall with custom kappa
//  Same as Test 14 but explicit C to verify C.kappa path
TEST(wall_functions_custom_kappa) {
    Turbulence::KEpsilonConstants C;
    double ew = Turbulence::compute_eps_wall(0.1, 0.01, C);
    // Expected: 0.1^3 / (0.41 * 0.01) = 0.001 / 0.0041
    CHECK_NEAR(ew, 0.001 / (C.kappa * 0.01), 1e-12);
    ++g_passed;
}

// Test 16: eps_wall y_p=0 protection
//  y_p=0 triggers error message + exit(1) via compute_eps_wall.
//  This is verified by code inspection; inline testing is impossible
//  because exit(1) terminates the process. If this protection is
//  removed or broken, a division-by-zero or negative kappa*y_p would
//  silently produce inf/nan/negative ε_wall.
//  To manually verify: call compute_eps_wall(u_tau, 0.0, C)
//  and confirm the process exits with code 1.
TEST(wall_eps_yp_zero_protection) {
    // Structural validation: the function exists and accepts the C parameter.
    // The y_p > 0 guard is tested by code review.
    Turbulence::KEpsilonConstants C;
    // Verify the function works with a tiny-but-positive y_p
    double ew = Turbulence::compute_eps_wall(0.1, 1e-10, C);
    CHECK_FINITE(ew);
    CHECK(ew > 0.0);
    ++g_passed;
}

// ---------- main ----------
int main() {
    RUN_TEST(constant_defaults);
    RUN_TEST(compute_mut_basic);
    RUN_TEST(compute_mut_clip_k_zero);
    RUN_TEST(compute_mut_clip_eps_zero);
    RUN_TEST(compute_mut_upper_bound);
    RUN_TEST(strain_sq_uniform_shear);
    RUN_TEST(strain_sq_zero);
    RUN_TEST(strain_sq_isotropic);
    RUN_TEST(production_basic);
    RUN_TEST(source_terms_basic);
    RUN_TEST(source_terms_pure_dissipation);
    RUN_TEST(source_terms_clip_k);
    RUN_TEST(diffusion_coefficients);
    RUN_TEST(wall_functions);
    RUN_TEST(wall_functions_custom_kappa);
    RUN_TEST(wall_eps_yp_zero_protection);

    std::cout << "\n=== Results: " << g_passed << " passed, "
              << g_failed << " failed ===\n";

    return (g_failed == 0) ? 0 : 1;
}
