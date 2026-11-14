#include "turbulent_transport.H"
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

#define RUN_TEST(name)                                                 \
    do {                                                               \
        g_current_test = #name;                                        \
        test_##name();                                                 \
    } while (0)

// ---------- test cases ----------

// Test 1: D_t basic
//   mu_t=1e-3, rho=1.0, Sc_t=0.7 → D_t = 1e-3/(1.0*0.7) = 1.428571...e-3
TEST(dt_basic) {
    double Dt = Turbulence::compute_turbulent_diffusivity(1e-3, 1.0, 0.7);
    CHECK_NEAR(Dt, 1.4285714285714285e-3, 1e-12);
    ++g_passed;
}

// Test 2: D_t rho=0 protection
TEST(dt_rho_zero) {
    double Dt = Turbulence::compute_turbulent_diffusivity(1e-3, 0.0, 0.7);
    CHECK_NEAR(Dt, 0.0, 1e-15);
    ++g_passed;
}

// Test 3: D_t custom Sc_t=1.0
//   mu_t=1e-3, rho=1.0, Sc_t=1.0 → D_t = 1e-3
TEST(dt_custom_sct) {
    double Dt = Turbulence::compute_turbulent_diffusivity(1e-3, 1.0, 1.0);
    CHECK_NEAR(Dt, 1.0e-3, 1e-15);
    ++g_passed;
}

// Test 4: D_eff
//   D_lam=2e-5, mu_t=1e-3, rho=1.0 → D_eff = 2e-5 + 1.4286e-3
TEST(deff_basic) {
    double Deff = Turbulence::compute_effective_diffusivity(2e-5, 1e-3, 1.0, 0.7);
    double Dt   = Turbulence::compute_turbulent_diffusivity(1e-3, 1.0, 0.7);
    CHECK_NEAR(Deff, 2e-5 + Dt, 1e-12);
    ++g_passed;
}

// Test 5: mu_eff
//   mu_lam=1.8e-5, mu_t=9e-5 → mu_eff = 1.08e-4
TEST(mueff_basic) {
    double mueff = Turbulence::compute_effective_viscosity(1.8e-5, 9e-5);
    CHECK_NEAR(mueff, 1.08e-4, 1e-15);
    ++g_passed;
}

// Test 6: batch N=3
//   3 species with distinct D_lam; verify D_eff[i] = D_lam[i] + same D_t
TEST(batch_n3) {
    double D_lam[3] = {2e-5, 4e-5, 6e-5};
    double D_eff[3] = {0.0, 0.0, 0.0};
    double Dt_expected = Turbulence::compute_turbulent_diffusivity(1e-3, 1.0, 0.7);

    Turbulence::compute_effective_diffusivities(D_lam, 3, 1e-3, 1.0, 0.7, D_eff);

    for (int i = 0; i < 3; ++i) {
        CHECK_NEAR(D_eff[i], D_lam[i] + Dt_expected, 1e-12);
    }
    ++g_passed;
}

// Test 7: Sc_t default value in constants
TEST(constant_sct_default) {
    Turbulence::KEpsilonConstants C;
    CHECK_NEAR(C.Sc_t, 0.7, 1e-15);
    ++g_passed;
}

// ---------- main ----------
int main() {
    RUN_TEST(dt_basic);
    RUN_TEST(dt_rho_zero);
    RUN_TEST(dt_custom_sct);
    RUN_TEST(deff_basic);
    RUN_TEST(mueff_basic);
    RUN_TEST(batch_n3);
    RUN_TEST(constant_sct_default);

    std::cout << "\n=== Results: " << g_passed << " passed, "
              << g_failed << " failed ===\n";

    return (g_failed == 0) ? 0 : 1;
}
