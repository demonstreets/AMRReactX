#include "wind_bc.H"
#include "k_epsilon_constants.H"

#include <cmath>
#include <iostream>
#include <string>

// ─── minimal test harness (matching test_k_epsilon.cpp style) ───────
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

// ═══════════════════════════════════════════════════════════════════════
//  Test 1 — resolve_direction: compass → degrees and numeric pass-through
// ═══════════════════════════════════════════════════════════════════════
TEST(resolve_direction) {
    CHECK_NEAR(Wind::resolve_direction(std::string("SSW")), 202.5, 1e-12);
    CHECK_NEAR(Wind::resolve_direction(std::string("N")),    0.0, 1e-12);
    CHECK_NEAR(Wind::resolve_direction(std::string("E")),   90.0, 1e-12);

    // numeric fallback
    CHECK_NEAR(Wind::resolve_direction(std::string("45")),   45.0, 1e-12);

    // case-insensitive
    CHECK_NEAR(Wind::resolve_direction(std::string("ssw")), 202.5, 1e-12);

    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════════
//  Test 2 — Wind direction → velocity vector (SSW, meteorological convention)
//  θ=202.5°: wind FROM SSW blows TOWARD NNE → (+x, +z)
//  wind_x = -sin(θ)·u_ref ≈ 0.383·u_ref
//  wind_z = -cos(θ)·u_ref ≈ 0.924·u_ref
// ═══════════════════════════════════════════════════════════════════════
TEST(direction_to_vector) {
    Wind::WindConfig cfg;
    cfg.direction_deg = 202.5;   // SSW
    cfg.u_ref         = 1.0;
    cfg.z_ref         = 10.0;
    cfg.z0            = 0.03;
    cfg.T_inlet       = 293.0;

    Wind::compute_wind_config(cfg);

    const double expected_wx = 0.38268343236509;   // -sin(202.5°) ≈ +0.383
    const double expected_wz = 0.92387953251129;   // -cos(202.5°) ≈ +0.924

    CHECK_NEAR(cfg.wind_x, expected_wx, 1e-3);
    CHECK_NEAR(cfg.wind_z, expected_wz, 1e-3);

    // normalised: sqrt(wind_x² + wind_z²) ≈ 1.0
    CHECK_NEAR(std::sqrt(cfg.wind_x * cfg.wind_x + cfg.wind_z * cfg.wind_z),
               cfg.u_ref, 1e-12);

    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════════
//  Test 3 — friction_velocity
//  u_ref=3, z_ref=10, z0=0.03, κ=0.41
//  u_* = κ·u_ref / ln(z_ref/z0) = 1.23 / ln(333.33…) ≈ 0.2117
// ═══════════════════════════════════════════════════════════════════════
TEST(friction_velocity) {
    double u_star = Wind::friction_velocity(3.0, 10.0, 0.03, 0.41);

    // compute expected inline for maximum precision
    double expected = 0.41 * 3.0 / std::log(10.0 / 0.03);
    CHECK_NEAR(u_star, expected, 1e-12);
    CHECK_FINITE(u_star);
    CHECK(u_star > 0.0);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════════
//  Test 4 — log_law_velocity: reference-height closure
//  With the same u_* as Test 3, u(z_ref) should recover u_ref = 3.0
// ═══════════════════════════════════════════════════════════════════════
TEST(log_law_closure_at_zref) {
    double u_star = Wind::friction_velocity(3.0, 10.0, 0.03, 0.41);
    double u10    = Wind::log_law_velocity(10.0, u_star, 0.03, 0.41);

    CHECK_NEAR(u10, 3.0, 1e-9);   // closure: u(z_ref) must equal u_ref
    CHECK_FINITE(u10);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════════
//  Test 5 — log_law_velocity: sub-z₀ clamping
//  For z < z₀, z is clamped to z₀ so ln(1) = 0 → u = 0
// ═══════════════════════════════════════════════════════════════════════
TEST(log_law_sub_z0_clamping) {
    double u_star = Wind::friction_velocity(3.0, 10.0, 0.03, 0.41);

    // z = 0.005 < z0 = 0.03 → clamped to z0, log-law → 0
    double u_below = Wind::log_law_velocity(0.005, u_star, 0.03, 0.41);
    CHECK_NEAR(u_below, 0.0, 1e-12);

    // z exactly at z0 → ln(1) = 0 → u = 0
    double u_at_z0 = Wind::log_law_velocity(0.03, u_star, 0.03, 0.41);
    CHECK_NEAR(u_at_z0, 0.0, 1e-12);

    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════════
//  Test 6 — Face classification: SSW wind
//  SSW → wind vector ≈ (+0.383·u, +0.924·u)  (blow toward +x,+z)
//   x_lo: v·(-1,0,0) = -wx < 0  → INLET
//   x_hi: v·(+1,0,0) = +wx > 0  → OUTLET
//   z_lo: v·(0,0,-1) = -wz < 0  → INLET
//   z_hi: v·(0,0,+1) = +wz > 0  → OUTLET
//   y_lo: WALL (ground)
//   y_hi: SYMMETRY (top)
// ═══════════════════════════════════════════════════════════════════════
TEST(face_classification_SSW) {
    Wind::WindConfig cfg;
    cfg.direction_deg = 202.5;
    cfg.u_ref = 3.0;
    cfg.z_ref = 10.0;
    cfg.z0    = 0.03;
    cfg.T_inlet = 293.0;
    Wind::compute_wind_config(cfg);

    // sanity: wind blows toward +x and +z
    CHECK(cfg.wind_x > 0.0);
    CHECK(cfg.wind_z > 0.0);

    Wind::AllFaceTypes ft = Wind::compute_all_face_types(cfg.wind_x, cfg.wind_z);

    CHECK(ft.x_lo == Wind::FaceType::INLET);
    CHECK(ft.x_hi == Wind::FaceType::OUTLET);
    CHECK(ft.y_lo == Wind::FaceType::WALL);
    CHECK(ft.y_hi == Wind::FaceType::SYMMETRY);
    CHECK(ft.z_lo == Wind::FaceType::INLET);
    CHECK(ft.z_hi == Wind::FaceType::OUTLET);

    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════════
//  Test 7 — inlet_k: k = u_*² / √C_μ
//  u_* = 0.185, C_μ = 0.09 → k = 0.034225 / 0.3 ≈ 0.11408
// ═══════════════════════════════════════════════════════════════════════
TEST(inlet_k_value) {
    double k = Wind::inlet_k(0.185);
    double expected = 0.185 * 0.185 / std::sqrt(0.09);
    CHECK_NEAR(k, expected, 1e-12);
    CHECK_FINITE(k);
    CHECK(k > 0.0);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════════
//  Test 8 — inlet_epsilon: ε = u_*³ / (κ · max(z, z₀))
//  u_* = 0.185, z = 10, z₀ = 0.03, κ = 0.41
//  ε = 0.0063316 / 4.1 ≈ 0.001544
// ═══════════════════════════════════════════════════════════════════════
TEST(inlet_epsilon_value) {
    double eps = Wind::inlet_epsilon(10.0, 0.185, 0.03, 0.41);
    double expected = 0.185 * 0.185 * 0.185 / (0.41 * 10.0);
    CHECK_NEAR(eps, expected, 1e-12);
    CHECK_FINITE(eps);
    CHECK(eps > 0.0);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════════
//  Test 9 — compute_inlet_bc: full end-to-end validation
//  SSW wind, u_ref=3, z_ref=10, z₀=0.03, T_inlet=293, z=10
//  At z=z_ref the log-law should give u_mag = u_ref.
//  bc.u, bc.w should match the reference direction vector.
// ═══════════════════════════════════════════════════════════════════════
TEST(compute_inlet_bc_full) {
    Wind::WindConfig cfg;
    cfg.direction_deg = 202.5;
    cfg.u_ref   = 3.0;
    cfg.z_ref   = 10.0;
    cfg.z0      = 0.03;
    cfg.T_inlet = 293.0;
    Wind::compute_wind_config(cfg);

    Wind::InletBC bc = Wind::compute_inlet_bc(10.0, cfg);

    // velocity magnitude at z=10 should recover u_ref=3.0
    double u_mag = std::sqrt(bc.u * bc.u + bc.v * bc.v + bc.w * bc.w);
    CHECK_NEAR(u_mag, 3.0, 1e-9);

    // direction components should match the reference vector
    CHECK_NEAR(bc.u, cfg.wind_x, 1e-9);
    CHECK_NEAR(bc.v, 0.0, 1e-12);
    CHECK_NEAR(bc.w, cfg.wind_z, 1e-9);

    CHECK_NEAR(bc.T, 293.0, 1e-12);

    // k and ε must be consistent with the profile functions
    CHECK_NEAR(bc.k, Wind::inlet_k(cfg.u_star), 1e-12);
    CHECK_NEAR(bc.epsilon, Wind::inlet_epsilon(10.0, cfg.u_star, cfg.z0, 0.41), 1e-12);

    CHECK_FINITE(bc.k);
    CHECK_FINITE(bc.epsilon);
    CHECK(bc.k > 0.0);
    CHECK(bc.epsilon > 0.0);

    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════════
//  Test 10 — z₀ = 0 auto-protection → 1e-4
//  All functions must handle z₀ = 0 gracefully without NaN/Inf.
// ═══════════════════════════════════════════════════════════════════════
TEST(z0_zero_protection) {
    // sanitize_z0 alone
    CHECK_NEAR(Wind::sanitize_z0(0.0),    1.0e-4, 1e-12);
    CHECK_NEAR(Wind::sanitize_z0(-1.0),   1.0e-4, 1e-12);
    CHECK_NEAR(Wind::sanitize_z0(0.03),   0.03,   1e-12);

    // friction_velocity with z0=0 must be finite
    double u_star = Wind::friction_velocity(3.0, 10.0, 0.0, 0.41);
    CHECK_FINITE(u_star);
    CHECK(u_star > 0.0);

    // log_law_velocity with z0=0 must be finite
    double u = Wind::log_law_velocity(10.0, u_star, 0.0, 0.41);
    CHECK_FINITE(u);
    CHECK(u >= 0.0);

    // inlet_epsilon with z0=0 must be finite
    double eps = Wind::inlet_epsilon(10.0, 0.185, 0.0, 0.41);
    CHECK_FINITE(eps);
    CHECK(eps > 0.0);

    // compute_wind_config must sanitise z0 internally
    Wind::WindConfig cfg;
    cfg.direction_deg = 202.5;
    cfg.u_ref   = 3.0;
    cfg.z_ref   = 10.0;
    cfg.z0      = 0.0;
    cfg.T_inlet = 293.0;
    Wind::compute_wind_config(cfg);

    CHECK_FINITE(cfg.u_star);
    CHECK_FINITE(cfg.wind_x);
    CHECK_FINITE(cfg.wind_z);
    CHECK(cfg.u_star > 0.0);

    // inlet BC must be valid with z0=0
    Wind::InletBC bc = Wind::compute_inlet_bc(10.0, cfg);
    CHECK_FINITE(bc.u);
    CHECK_FINITE(bc.w);
    CHECK_FINITE(bc.k);
    CHECK_FINITE(bc.epsilon);

    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════════
//  Test 11 — friction_velocity: z_ref < z0 returns 0.0 (no NaN/INF)
//  z_ref=0.02 is below z0=0.03; the profile is unphysical and u_*=0.
// ═══════════════════════════════════════════════════════════════════════
TEST(friction_velocity_zref_lt_z0) {
    double u_star = Wind::friction_velocity(3.0, 0.02, 0.03, 0.41);
    CHECK_NEAR(u_star, 0.0, 1e-12);
    CHECK_FINITE(u_star);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════════
//  Test 12 — inlet_k: result matches manual compute with C_mu=0.09
//  inlet_k(u_*) uses the internal KEpsilonConstants{}.C_mu = 0.09.
//  Manual: k = u_*² / √0.09  should match exactly.
// ═══════════════════════════════════════════════════════════════════════
TEST(inlet_k_vs_manual_cmu) {
    const double u_star = 0.2117;   // typical value from Test 3
    double k_wind  = Wind::inlet_k(u_star);
    double k_manual = u_star * u_star / std::sqrt(0.09);
    CHECK_NEAR(k_wind, k_manual, 1e-12);
    CHECK_FINITE(k_wind);
    CHECK(k_wind > 0.0);
    ++g_passed;
}

// ─── main ───────────────────────────────────────────────────────────
int main() {
    RUN_TEST(resolve_direction);
    RUN_TEST(direction_to_vector);
    RUN_TEST(friction_velocity);
    RUN_TEST(log_law_closure_at_zref);
    RUN_TEST(log_law_sub_z0_clamping);
    RUN_TEST(face_classification_SSW);
    RUN_TEST(inlet_k_value);
    RUN_TEST(inlet_epsilon_value);
    RUN_TEST(compute_inlet_bc_full);
    RUN_TEST(z0_zero_protection);
    RUN_TEST(friction_velocity_zref_lt_z0);
    RUN_TEST(inlet_k_vs_manual_cmu);

    std::cout << "\n=== Results: " << g_passed << " passed, "
              << g_failed << " failed ===\n";

    return (g_failed == 0) ? 0 : 1;
}
