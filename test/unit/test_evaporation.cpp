#include "evaporation_model.H"
#include "antoine_data.H"
#include "pool_evaporation.H"

#include <cmath>
#include <iostream>
#include <string>
#include <cstring>

// ─── minimal test harness (matching test_k_epsilon.cpp style) ───
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

// ═══════════════════════════════════════════════════════════════════
// Test 1: friction_velocity — basic computation
//   u_ref=5.0, C_f=0.001 → u* = sqrt(0.001) * 5.0
//   = 0.15811388300841897...
// ═══════════════════════════════════════════════════════════════════
TEST(friction_velocity_basic) {
    double u_star = Evaporation::friction_velocity(5.0, 0.001);
    CHECK_NEAR(u_star, 0.158113883008419, 1e-12);
    CHECK(u_star > 0.0);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 2: mass_transfer_coefficient — FLACS surface renewal formula
//   u* = 0.158113883, κ = 0.41, Sc = 1.0, Sc_t = 0.7
//   k_m = (u*/κ) / (Sc_t + 5·Sc^(2/3) − 5)
//       = 0.385643617 / 0.7  = 0.550919452...
// ═══════════════════════════════════════════════════════════════════
TEST(mass_transfer_coefficient_flacs) {
    double u_star = 0.158113883008419;
    double kappa  = 0.41;
    double Sc     = 1.0;
    double Sc_t   = 0.7;

    double k_m = Evaporation::mass_transfer_coefficient(u_star, kappa, Sc, Sc_t);
    CHECK_NEAR(k_m, 0.550919452991007, 1e-12);
    CHECK_FINITE(k_m);
    CHECK(k_m > 0.0);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 3: saturation_pressure — water at 373.15 K (100 °C)
//   Antoine form (Celsius, mmHg): log10 P_mmHg = A - B/(t + C)
//   t = 373.15 - 273.15 = 100.0 °C
//   log10 P_mmHg = 8.07131 - 1730.63/(100.0 + 233.426) ≈ 2.88086
//   P_mmHg = 10^2.88086 ≈ 760.1 mmHg
//   P_sat = 760.1 × 133.322 ≈ 101336 Pa  (correct physics: ~1 atm)
// ═══════════════════════════════════════════════════════════════════
TEST(saturation_pressure_water) {
    double A = 8.07131, B = 1730.63, C = 233.426;
    double T = 373.15;
    double P = Evaporation::saturation_pressure(T, A, B, C);

    CHECK_NEAR(P, 101336.0, 10.0);  // ~1 atm
    CHECK_FINITE(P);
    CHECK(P > 0.0);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 4: saturation_density — water at 373.15 K
//   ρ = P_sat · M_v / (R · T)
//   P_sat ≈ 101336 Pa, M_v = 0.01802 kg/mol
//   ρ ≈ 101336 × 0.01802 / (8.314 × 373.15) ≈ 0.5886 kg/m³
// ═══════════════════════════════════════════════════════════════════
TEST(saturation_density_water) {
    double A = 8.07131, B = 1730.63, C = 233.426;
    double M_v = 0.01802;
    double T   = 373.15;
    double rho = Evaporation::saturation_density(T, 101325.0, M_v, A, B, C);

    CHECK_NEAR(rho, 0.588608, 0.001);
    CHECK_FINITE(rho);
    CHECK(rho > 0.0);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 5: evaporation_flux — basic calculation
//   k_m = 0.01 m/s, ρ_sat = 0.597 kg/m³, ρ_inf = 0
//   ḿ'' = 0.01 × 0.597 = 0.00597 kg/(m²·s)
// ═══════════════════════════════════════════════════════════════════
TEST(evaporation_flux_basic) {
    double k_m     = 0.01;
    double rho_sat = 0.597;
    double rho_inf = 0.0;

    double mdot = Evaporation::evaporation_flux(k_m, rho_sat, rho_inf);
    CHECK_NEAR(mdot, 0.00597, 1e-12);
    CHECK_FINITE(mdot);
    CHECK(mdot >= 0.0);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 6: cell_in_pool — positive and negative cases
//   PoolGeometry: x=[0,2], y=[0,0], z=[0,1]
//   (1.0, 0.0, 0.5) → inside  → true
//   (3.0, 0.0, 0.5) → outside (x) → false
//   (1.0, 0.0, 2.0) → outside (z) → false
// ═══════════════════════════════════════════════════════════════════
TEST(cell_in_pool_pos_neg) {
    Evaporation::PoolGeometry geom;
    geom.x_lo = 0.0; geom.x_hi = 2.0;
    geom.y_lo = 0.0; geom.y_hi = 0.0;
    geom.z_lo = 0.0; geom.z_hi = 1.0;

    Evaporation::EvaporationParams params;
    params.M_v = 0.01802;
    params.antoine_A = 8.07131;
    params.antoine_B = 1730.63;
    params.antoine_C = 233.426;
    params.D_air = 1.0e-5;

    Evaporation::PoolEvaporation pool;
    pool.configure(geom, params);

    // Inside
    CHECK(pool.cell_in_pool(1.0, 0.0, 0.5) == true);
    // Outside x
    CHECK(pool.cell_in_pool(3.0, 0.0, 0.5) == false);
    // Outside z
    CHECK(pool.cell_in_pool(1.0, 0.0, 2.0) == false);
    // On boundary
    CHECK(pool.cell_in_pool(0.0, 0.0, 0.0) == true);
    CHECK(pool.cell_in_pool(2.0, 0.0, 1.0) == true);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 7: Antoine database — lookup by name and alias
//   methane, propane, n-hexane, ammonia, chlorine, water
//   Aliases: CH4, LNG, C3H8, hexane, gasoline, NH3, Cl2, H2O
// ═══════════════════════════════════════════════════════════════════
TEST(antoine_database_lookup) {
    // ── methane by primary name ──────────────────────────
    {
        auto c = Evaporation::lookup_antoine("methane");
        CHECK(c.found == true);
        CHECK_NEAR(c.A, 6.69561, 1e-10);
        CHECK_NEAR(c.B, 405.42,   1e-10);
        CHECK_NEAR(c.M_v, 0.01604, 1e-10);
    }

    // ── methane by alias CH4 ─────────────────────────────
    {
        auto c = Evaporation::lookup_antoine("CH4");
        CHECK(c.found == true);
        CHECK_NEAR(c.A, 6.69561, 1e-10);
    }

    // ── methane by alias LNG ─────────────────────────────
    {
        auto c = Evaporation::lookup_antoine("LNG");
        CHECK(c.found == true);
        CHECK_NEAR(c.M_v, 0.01604, 1e-10);
    }

    // ── propane by primary name ──────────────────────────
    {
        auto c = Evaporation::lookup_antoine("propane");
        CHECK(c.found == true);
        CHECK_NEAR(c.A, 6.95719, 1e-10);
        CHECK_NEAR(c.M_v, 0.04410, 1e-10);
    }

    // ── propane by alias C3H8 ────────────────────────────
    {
        auto c = Evaporation::lookup_antoine("C3H8");
        CHECK(c.found == true);
        CHECK_NEAR(c.M_v, 0.04410, 1e-10);
    }

    // ── n-hexane by alias gasoline ───────────────────────
    {
        auto c = Evaporation::lookup_antoine("gasoline");
        CHECK(c.found == true);
        CHECK_NEAR(c.A, 6.91058, 1e-10);
        CHECK_NEAR(c.M_v, 0.08618, 1e-10);
    }

    // ── ammonia by alias NH3 ─────────────────────────────
    {
        auto c = Evaporation::lookup_antoine("NH3");
        CHECK(c.found == true);
        CHECK_NEAR(c.A, 7.55466, 1e-10);
    }

    // ── chlorine ─────────────────────────────────────────
    {
        auto c = Evaporation::lookup_antoine("chlorine");
        CHECK(c.found == true);
        CHECK_NEAR(c.M_v, 0.07091, 1e-10);
    }

    // ── water by alias H2O ───────────────────────────────
    {
        auto c = Evaporation::lookup_antoine("H2O");
        CHECK(c.found == true);
        CHECK_NEAR(c.A, 8.07131, 1e-10);
        CHECK_NEAR(c.B, 1730.63, 1e-10);
        CHECK_NEAR(c.C, 233.426, 1e-10);
        CHECK_NEAR(c.M_v, 0.01802, 1e-10);
    }

    // ── case insensitivity ───────────────────────────────
    {
        auto c = Evaporation::lookup_antoine("Methane");
        CHECK(c.found == true);
        CHECK_NEAR(c.A, 6.69561, 1e-10);
    }

    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 8: Antoine database — unknown species returns error
// ═══════════════════════════════════════════════════════════════════
TEST(antoine_unknown_species) {
    auto c = Evaporation::lookup_antoine("nonexistent_substance");
    CHECK(c.found == false);
    CHECK(c.M_v == 0.0);
    CHECK(c.A == 0.0);
    CHECK(c.B == 0.0);
    CHECK(c.C == 0.0);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 9: Level 0 — constant flux mode
//   Configure with ModelType::constant and constant_flux=0.05.
//   get_mass_flux() should return exactly 0.05.
// ═══════════════════════════════════════════════════════════════════
TEST(level0_constant_flux) {
    Evaporation::PoolGeometry geom;
    geom.x_lo = 0.0; geom.x_hi = 1.0;
    geom.y_lo = 0.0; geom.y_hi = 0.0;
    geom.z_lo = 0.0; geom.z_hi = 1.0;

    Evaporation::EvaporationParams params;
    params.model_type   = Evaporation::ModelType::constant;
    params.constant_flux = 0.05;
    params.h_v_form     = -2.5e6;
    params.vapor_species_name = "test_species";

    Evaporation::PoolEvaporation pool;
    pool.configure(geom, params);

    CHECK_NEAR(pool.get_mass_flux(), 0.05, 1e-15);
    CHECK_NEAR(pool.get_vapor_formation_enthalpy(), -2.5e6, 1e-10);
    CHECK(pool.get_vapor_species_name() == "test_species");
    CHECK(pool.model_type() == Evaporation::ModelType::constant);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 10: y_lo != y_hi → runtime error (no crash)
//   PoolEvaporation::configure() rejects non-horizontal pools by
//   setting m_valid=false and skipping flux computation.
//   ─ valid geometry (y_lo==y_hi) → m_valid=true, flux computed
//   ─ invalid geometry (y_lo!=y_hi) → m_valid=false, flux=0.0
// ═══════════════════════════════════════════════════════════════════
TEST(ylo_not_equals_yhi_runtime_check) {
    // Valid geometry: works normally
    {
        Evaporation::PoolGeometry geom;
        geom.x_lo = 0.0; geom.x_hi = 1.0;
        geom.y_lo = 0.0; geom.y_hi = 0.0;
        geom.z_lo = 0.0; geom.z_hi = 1.0;

        Evaporation::EvaporationParams params;
        params.model_type = Evaporation::ModelType::constant;
        params.constant_flux = 0.01;

        Evaporation::PoolEvaporation pool;
        pool.configure(geom, params);
        CHECK(pool.is_valid() == true);
        CHECK_NEAR(pool.get_mass_flux(), 0.01, 1e-15);
    }

    // Invalid geometry: y_lo != y_hi → should not crash, should be invalid
    {
        Evaporation::PoolGeometry geom;
        geom.x_lo = 0.0; geom.x_hi = 1.0;
        geom.y_lo = 0.0; geom.y_hi = 1.0;  // non-horizontal!
        geom.z_lo = 0.0; geom.z_hi = 1.0;

        Evaporation::EvaporationParams params;
        params.model_type = Evaporation::ModelType::constant;
        params.constant_flux = 0.05;

        Evaporation::PoolEvaporation pool;
        pool.configure(geom, params);
        CHECK(pool.is_valid() == false);
        CHECK_NEAR(pool.get_mass_flux(), 0.0, 1e-15);
    }
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 11: friction_velocity — C_f <= 0 → returns 0.0
// ═══════════════════════════════════════════════════════════════════
TEST(friction_velocity_nonpositive_Cf) {
    // C_f = 0 → u* = 0 (log-layer singularity avoided)
    double u1 = Evaporation::friction_velocity(5.0, 0.0);
    CHECK_NEAR(u1, 0.0, 1e-15);

    // C_f < 0 → u* = 0 (physically invalid input)
    double u2 = Evaporation::friction_velocity(5.0, -0.5);
    CHECK_NEAR(u2, 0.0, 1e-15);

    // C_f = 0.001 still works normally
    double u3 = Evaporation::friction_velocity(5.0, 0.001);
    CHECK_NEAR(u3, 0.158113883008419, 1e-12);
    CHECK(u3 > 0.0);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 12: saturation_pressure — water at 293 K (20 °C)
//   t = 19.85 °C, log10 P_mmHg ≈ 1.238, P_mmHg ≈ 17.3 mmHg
//   P_sat ≈ 2308 Pa  (correct physics for water at 20 °C)
// ═══════════════════════════════════════════════════════════════════
TEST(saturation_pressure_water_293K) {
    double A = 8.07131, B = 1730.63, C = 233.426;
    double P = Evaporation::saturation_pressure(293.0, A, B, C);
    CHECK_NEAR(P, 2308.0, 5.0);
    CHECK_FINITE(P);
    CHECK(P > 0.0);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 13: invalid Antoine params → recompute_flux returns 0
//   Antoine A ≤ 0 → flux 0 (invalid Antoine A coefficient)
//   Antoine B ≤ 0 → flux 0 (invalid Antoine B coefficient)
// ═══════════════════════════════════════════════════════════════════
TEST(invalid_antoine_params_flux_zero) {
    Evaporation::PoolGeometry geom;
    geom.x_lo = 0.0; geom.x_hi = 1.0;
    geom.y_lo = 0.0; geom.y_hi = 0.0;
    geom.z_lo = 0.0; geom.z_hi = 1.0;

    Evaporation::EvaporationParams params;
    params.model_type = Evaporation::ModelType::mass_transfer;
    params.u_ref = 5.0;
    params.T_pool = 300.0;
    params.M_v = 0.01802;
    params.D_air = 1.0e-5;

    // Case A: A <= 0 (invalid)
    {
        params.antoine_A = 0.0;
        params.antoine_B = 1730.63;
        params.antoine_C = 233.426;
        Evaporation::PoolEvaporation pool;
        pool.configure(geom, params);
        CHECK_NEAR(pool.get_mass_flux(), 0.0, 1e-15);
    }

    // Case B: B <= 0 (invalid)
    {
        params.antoine_A = 8.07131;
        params.antoine_B = 0.0;
        params.antoine_C = 233.426;
        Evaporation::PoolEvaporation pool;
        pool.configure(geom, params);
        CHECK_NEAR(pool.get_mass_flux(), 0.0, 1e-15);
    }

    // Case C: valid params still work
    {
        params.antoine_A = 8.07131;
        params.antoine_B = 1730.63;
        params.antoine_C = 233.426;
        Evaporation::PoolEvaporation pool;
        pool.configure(geom, params);
        CHECK(pool.is_valid() == true);
        CHECK(pool.get_mass_flux() > 0.0);
    }
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 14: propane with negative C at low T → T+C ≤ 0 → returns 0
//   propane: C = -45.957, T_pool = 30 K → t = -243.15 °C
//   t + C = -243.15 + (-45.957) = -289.107 ≤ 0
//   → saturation_pressure returns 0.0 (safe short-circuit)
// ═══════════════════════════════════════════════════════════════════
TEST(propane_low_temperature_returns_zero) {
    // Direct saturation_pressure call
    double P = Evaporation::saturation_pressure(
        30.0, 6.95719, 1424.255, -45.957);
    CHECK_NEAR(P, 0.0, 1e-15);
    CHECK_FINITE(P);

    // Pool-level: recompute_flux should detect T_pool+C ≤ 0 and return 0
    Evaporation::PoolGeometry geom;
    geom.x_lo = 0.0; geom.x_hi = 1.0;
    geom.y_lo = 0.0; geom.y_hi = 0.0;
    geom.z_lo = 0.0; geom.z_hi = 1.0;

    Evaporation::EvaporationParams params;
    params.model_type = Evaporation::ModelType::mass_transfer;
    params.u_ref = 5.0;
    params.T_pool = 30.0;  // extremely low for propane
    params.M_v = 0.04410;
    params.D_air = 1.0e-5;
    params.antoine_A = 6.95719;
    params.antoine_B = 1424.255;
    params.antoine_C = -45.957;  // propane

    Evaporation::PoolEvaporation pool;
    pool.configure(geom, params);
    CHECK_NEAR(pool.get_mass_flux(), 0.0, 1e-15);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// Test 15: saturation_pressure — T+C = 0 edge case → returns 0
//   Using water constants but T such that t+C = 0 exactly
//   t = -233.426 °C → T = 39.724 K  (edge case)
// ═══════════════════════════════════════════════════════════════════
TEST(saturation_pressure_T_plus_C_zero) {
    // t + C = 0 exactly → short-circuit to 0
    double T = 273.15 - 233.426;  // = 39.724 K → t = -233.426 °C
    double P = Evaporation::saturation_pressure(T, 8.07131, 1730.63, 233.426);
    CHECK_NEAR(P, 0.0, 1e-15);
    CHECK_FINITE(P);
    ++g_passed;
}

// ═══════════════════════════════════════════════════════════════════
// main
// ═══════════════════════════════════════════════════════════════════
int main() {
    RUN_TEST(friction_velocity_basic);
    RUN_TEST(mass_transfer_coefficient_flacs);
    RUN_TEST(saturation_pressure_water);
    RUN_TEST(saturation_density_water);
    RUN_TEST(evaporation_flux_basic);
    RUN_TEST(cell_in_pool_pos_neg);
    RUN_TEST(antoine_database_lookup);
    RUN_TEST(antoine_unknown_species);
    RUN_TEST(level0_constant_flux);
    RUN_TEST(ylo_not_equals_yhi_runtime_check);
    RUN_TEST(friction_velocity_nonpositive_Cf);
    RUN_TEST(saturation_pressure_water_293K);
    RUN_TEST(invalid_antoine_params_flux_zero);
    RUN_TEST(propane_low_temperature_returns_zero);
    RUN_TEST(saturation_pressure_T_plus_C_zero);

    std::cout << "\n=== Results: " << g_passed << " passed, "
              << g_failed << " failed ===\n";

    return (g_failed == 0) ? 0 : 1;
}
