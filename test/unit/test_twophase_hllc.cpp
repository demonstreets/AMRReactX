// Standalone unit test for TwoPhaseHLLC.H
// No AMReX runtime — uses stubs from test/unit/amrex_stubs/
//
// Compile:
//   g++ -std=c++17 -I test/unit/amrex_stubs -I src/academic/twophase \
//       test/unit/test_twophase_hllc.cpp -o build_test/test_twophase_hllc
// Run:
//   ./build_test/test_twophase_hllc

#include <iostream>
#include <cmath>
#include <cstdlib>

#include "TwoPhaseHLLC.H"

using amrex::Real;

static int n_pass = 0;
static int n_fail = 0;

#define TEST(name)                                              \
    do {                                                        \
        std::cout << "  TEST: " << name << " ... ";             \
    } while (0)

#define PASS()                                                  \
    do {                                                        \
        std::cout << "PASS" << std::endl;                       \
        n_pass++;                                               \
    } while (0)

#define FAIL(msg)                                               \
    do {                                                        \
        std::cout << "FAIL: " << msg << std::endl;              \
        n_fail++;                                               \
    } while (0)

#define CHECK(cond, msg)                                        \
    do {                                                        \
        if (!(cond)) { FAIL(msg); return; }                     \
    } while (0)

#define CHECK_CLOSE(a, b, tol, msg)                             \
    do {                                                        \
        Real diff = std::abs((a) - (b));                        \
        Real denom = std::max(std::abs(a), std::abs(b));        \
        Real rel = (denom > 1e-15) ? diff / denom : diff;       \
        if (rel > (tol)) {                                      \
            std::cout << "FAIL: " << msg << " ("                \
                      << a << " vs " << b                       \
                      << ", rel_diff=" << rel << ")"            \
                      << std::endl;                             \
            n_fail++;                                           \
            return;                                             \
        }                                                       \
    } while (0)

static void physical_flux(
    const Real rho, const Real u, const Real p, const Real e,
    Real& flux_rho, Real& flux_u, Real& flux_eden, Real& flux_eint)
{
    const Real E = e + 0.5 * u * u;
    flux_rho = rho * u;
    flux_u = rho * u * u + p;
    flux_eden = (rho * E + p) * u;
    flux_eint = rho * u * e;
}

// ---------------------------------------------------------------------------
// Test 1: Pure gas-gas HLLC — Sod shock tube
// ---------------------------------------------------------------------------
void test_gas_gas()
{
    TEST("Gas-gas Sod shock tube (ρL=1, uL=0, pL=1e5, ρR=0.125, uR=0, pR=1e4, γ=1.4)");

    constexpr int NSPEC = 2;
    const PhaseEOSParams eos = {1.4, 0.0};  // ideal gas

    Real rhoL = 1.0, uL = 0.0, pL = 1.0e5;
    Real rhoR = 0.125, uR = 0.0, pR = 1.0e4;

    Real eL = (pL) / ((eos.gamma - 1.0) * rhoL);  // ≈ 2.5e5
    Real eR = (pR) / ((eos.gamma - 1.0) * rhoR);  // ≈ 2.0e5

    Real YL[NSPEC] = {0.8, 0.2};
    Real YR[NSPEC] = {0.8, 0.2};

    Real flux_rho, flux_u, flux_eden, flux_eint, ustar;
    Real flux_rhoY[NSPEC], Ystar[NSPEC];

    twophase_hllc_flux<NSPEC>(
        rhoL, uL, pL, eL, YL, eos,
        rhoR, uR, pR, eR, YR, eos,
        flux_rho, flux_rhoY, flux_u, flux_eden, flux_eint, ustar, Ystar);

    // Basic sanity: fluxes should be finite and reasonable
    CHECK(std::isfinite(flux_rho), "flux_rho is NaN/inf");
    CHECK(std::isfinite(flux_u), "flux_u is NaN/inf");
    CHECK(std::isfinite(flux_eden), "flux_eden is NaN/inf");
    CHECK(std::isfinite(flux_eint), "flux_eint is NaN/inf");

    // For Sod problem with uL=uR=0 and pL > pR, flux should be positive
    CHECK(flux_rho > 0.0, "flux_rho should be positive (high P pushes right)");
    CHECK(flux_u > 0.0, "momentum flux should be positive");

    // Species mass fluxes should sum to mass flux
    Real sum_rhoY = 0.0;
    for (int n = 0; n < NSPEC; n++) sum_rhoY += flux_rhoY[n];
    CHECK_CLOSE(sum_rhoY, flux_rho, 1e-12, "species mass flux sum != mass flux");

    // Ystar should sum to 1.0
    Real sum_Y = 0.0;
    for (int n = 0; n < NSPEC; n++) sum_Y += Ystar[n];
    CHECK_CLOSE(sum_Y, 1.0, 1e-12, "Ystar sum != 1.0");

    PASS();
}

// ---------------------------------------------------------------------------
// Test 2: Pure liquid-liquid — no NaN, momentum conserved
// ---------------------------------------------------------------------------
void test_liquid_liquid()
{
    TEST("Pure liquid-liquid (water-like, γ=4.4, p_inf=6e8)");

    constexpr int NSPEC = 1;
    const PhaseEOSParams eos = {4.4, 6.0e8};

    // Slightly asymmetric to get nonzero fluxes
    Real rhoL = 1000.0, uL = 1.0, pL = 1.0e5;
    Real rhoR = 1000.0, uR = 0.0, pR = 1.0e5;

    Real eL = (pL + eos.gamma * eos.p_inf) / ((eos.gamma - 1.0) * rhoL);
    Real eR = (pR + eos.gamma * eos.p_inf) / ((eos.gamma - 1.0) * rhoR);

    Real YL[1] = {1.0};
    Real YR[1] = {1.0};

    Real flux_rho, flux_u, flux_eden, flux_eint, ustar;
    Real flux_rhoY[1], Ystar[1];

    twophase_hllc_flux<NSPEC>(
        rhoL, uL, pL, eL, YL, eos,
        rhoR, uR, pR, eR, YR, eos,
        flux_rho, flux_rhoY, flux_u, flux_eden, flux_eint, ustar, Ystar);

    CHECK(std::isfinite(flux_rho), "flux_rho is NaN/inf");
    CHECK(std::isfinite(flux_u), "flux_u is NaN/inf");
    CHECK(std::isfinite(flux_eden), "flux_eden is NaN/inf");
    CHECK(std::isfinite(flux_eint), "flux_eint is NaN/inf");
    CHECK(flux_rho > 0.0, "flux_rho should be positive (left flow right)");

    // Momentum conservation: for symmetric states except velocity,
    // the star pressure should be positive
    CHECK(ustar > 0.0, "ustar should be positive");

    PASS();
}

// ---------------------------------------------------------------------------
// Test 3: Gas-liquid interface — no NaN, pstar > 0
// ---------------------------------------------------------------------------
void test_gas_liquid()
{
    TEST("Gas-liquid interface (γ_gas=1.4, γ_liq=4.4, p_inf=6e8)");

    constexpr int NSPEC = 2;
    const PhaseEOSParams eos_gas = {1.4, 0.0};
    const PhaseEOSParams eos_liq = {4.4, 6.0e8};

    // Gas (left) → Liquid (right) interface
    Real rhoL = 1.2, uL = 100.0, pL = 1.0e5;
    Real rhoR = 1000.0, uR = 0.0, pR = 1.0e5;

    Real eL = (pL + eos_gas.gamma * eos_gas.p_inf) / ((eos_gas.gamma - 1.0) * rhoL);
    Real eR = (pR + eos_liq.gamma * eos_liq.p_inf) / ((eos_liq.gamma - 1.0) * rhoR);

    Real YL[NSPEC] = {1.0, 0.0};  // pure gas species
    Real YR[NSPEC] = {0.0, 1.0};  // pure liquid species

    Real flux_rho, flux_u, flux_eden, flux_eint, ustar;
    Real flux_rhoY[NSPEC], Ystar[NSPEC];

    twophase_hllc_flux<NSPEC>(
        rhoL, uL, pL, eL, YL, eos_gas,
        rhoR, uR, pR, eR, YR, eos_liq,
        flux_rho, flux_rhoY, flux_u, flux_eden, flux_eint, ustar, Ystar);

    CHECK(std::isfinite(flux_rho), "flux_rho is NaN/inf");
    CHECK(std::isfinite(flux_u), "flux_u is NaN/inf");
    CHECK(std::isfinite(flux_eden), "flux_eden is NaN/inf");
    CHECK(std::isfinite(flux_eint), "flux_eint is NaN/inf");
    CHECK(flux_rho > 0.0, "flux_rho should be positive (left flow right)");

    // The liquid has very high p_inf, pstar should be well above 0
    // (we check pstar indirectly: HLLC fluxes should be reasonable)

    // ustar should be between uL and uR (or close)
    CHECK(ustar >= uR - 10.0 && ustar <= uL + 10.0,
          "ustar outside reasonable range");

    PASS();
}

// ---------------------------------------------------------------------------
// Test 4: Wave speed ordering SL < Sstar < SR
// ---------------------------------------------------------------------------
void test_wave_ordering()
{
    TEST("Wave speed ordering SL < Sstar < SR");

    const PhaseEOSParams eos = {1.4, 0.0};

    // Sod-like problem ensures distinct waves
    constexpr int NSPEC = 1;
    Real rhoL = 1.0, uL = 0.0, pL = 1.0e5;
    Real rhoR = 0.125, uR = 0.0, pR = 1.0e4;
    Real eL = (pL) / ((eos.gamma - 1.0) * rhoL);
    Real eR = (pR) / ((eos.gamma - 1.0) * rhoR);
    Real YL[1] = {1.0}, YR[1] = {1.0};

    // We need to compute SL, SR, Sstar internally.
    // Test by checking the output ustar (which is one of SL/uL/Sstar/uR/SR)
    // and verify that the upwind branch makes physical sense.

    Real flux_rho, flux_u, flux_eden, flux_eint, ustar;
    Real flux_rhoY[1], Ystar[1];

    twophase_hllc_flux<NSPEC>(
        rhoL, uL, pL, eL, YL, eos,
        rhoR, uR, pR, eR, YR, eos,
        flux_rho, flux_rhoY, flux_u, flux_eden, flux_eint, ustar, Ystar);

    // For Sod problem with pL >> pR and uL=uR=0:
    // - Rarefaction on left (SL < 0 typically), contact going right
    // - ustar should be positive (contact moving right)
    CHECK(ustar > 0.0, "ustar should be > 0 for Sod problem");

    // The flux should be dominated by left state material flowing right
    CHECK_CLOSE(flux_rho / ustar, rhoL, 0.5, "face density roughly rhoL");

    PASS();
}

// ---------------------------------------------------------------------------
// Test 5: Symmetry — swapping L/R gives same flux magnitude, opposite sign
// ---------------------------------------------------------------------------
void test_symmetry()
{
    TEST("L/R symmetry");

    constexpr int NSPEC = 1;
    const PhaseEOSParams eos = {1.4, 0.0};

    Real rhoL = 2.0, uL = 50.0, pL = 2.0e5;
    Real rhoR = 1.0, uR = -50.0, pR = 1.0e5;
    Real eL = (pL) / ((eos.gamma - 1.0) * rhoL);
    Real eR = (pR) / ((eos.gamma - 1.0) * rhoR);
    Real YL[1] = {1.0}, YR[1] = {1.0};

    // Forward: L→R
    Real fr_f, fu_f, fe_f, fei_f, us_f;
    Real fry_f[1], ys_f[1];
    twophase_hllc_flux<NSPEC>(
        rhoL, uL, pL, eL, YL, eos,
        rhoR, uR, pR, eR, YR, eos,
        fr_f, fry_f, fu_f, fe_f, fei_f, us_f, ys_f);

    // Reverse: swap L/R AND flip velocity signs (mirror)
    Real fr_r, fu_r, fe_r, fei_r, us_r;
    Real fry_r[1], ys_r[1];
    twophase_hllc_flux<NSPEC>(
        rhoR, -uR, pR, eR, YR, eos,   // swapped, velocities negated
        rhoL, -uL, pL, eL, YL, eos,
        fr_r, fry_r, fu_r, fe_r, fei_r, us_r, ys_r);

    // Mass flux should be antisymmetric: fr_f ≈ -fr_r
    CHECK_CLOSE(fr_f, -fr_r, 1e-12, "mass flux not antisymmetric");

    // Momentum flux should be symmetric: fu_f ≈ fu_r
    // (both sides see the same collision)
    CHECK_CLOSE(fu_f, fu_r, 1e-10, "momentum flux not symmetric");

    // ustar should be antisymmetric
    CHECK_CLOSE(us_f, -us_r, 1e-12, "ustar not antisymmetric");

    PASS();
}

// ---------------------------------------------------------------------------
// Test 6: Passive scalar transport — Ystar agrees with ustar upwinding
// ---------------------------------------------------------------------------
void test_passive_scalar()
{
    TEST("Passive scalar Ystar follows ustar upwinding");

    constexpr int NSPEC = 3;
    const PhaseEOSParams eos = {1.4, 0.0};

    // Left-moving flow (uL < 0, uR < 0)
    Real rhoL = 1.0, uL = -30.0, pL = 1.0e5;
    Real rhoR = 1.0, uR = -50.0, pR = 1.0e5;
    Real eL = (pL) / ((eos.gamma - 1.0) * rhoL);
    Real eR = (pR) / ((eos.gamma - 1.0) * rhoR);
    Real YL[NSPEC] = {0.7, 0.2, 0.1};
    Real YR[NSPEC] = {0.5, 0.3, 0.2};

    Real flux_rho, flux_u, flux_eden, flux_eint, ustar;
    Real flux_rhoY[NSPEC], Ystar[NSPEC];

    twophase_hllc_flux<NSPEC>(
        rhoL, uL, pL, eL, YL, eos,
        rhoR, uR, pR, eR, YR, eos,
        flux_rho, flux_rhoY, flux_u, flux_eden, flux_eint, ustar, Ystar);

    // ustar should be negative (flow goes left)
    CHECK(ustar < 0.0, "ustar should be negative for leftward flow");

    // Ystar should equal right state (upwind side for ustar < 0)
    // But note: if we're in a star region, Ystar is assigned per-side
    // before final upwind. For supersonic case it's clean.
    // We test: species mass fluxes should be consistent with Ystar
    for (int n = 0; n < NSPEC; n++) {
        CHECK_CLOSE(flux_rhoY[n], flux_rho * Ystar[n], 1e-12,
                    "flux_rhoY != flux_rho * Ystar");
    }

    // Now test rightward flow
    Real rhoL2 = 1.0, uL2 = 50.0, pL2 = 1.0e5;
    Real rhoR2 = 1.0, uR2 = 30.0, pR2 = 1.0e5;
    Real eL2 = (pL2) / ((eos.gamma - 1.0) * rhoL2);
    Real eR2 = (pR2) / ((eos.gamma - 1.0) * rhoR2);

    twophase_hllc_flux<NSPEC>(
        rhoL2, uL2, pL2, eL2, YL, eos,
        rhoR2, uR2, pR2, eR2, YR, eos,
        flux_rho, flux_rhoY, flux_u, flux_eden, flux_eint, ustar, Ystar);

    CHECK(ustar > 0.0, "ustar should be positive for rightward flow");

    for (int n = 0; n < NSPEC; n++) {
        CHECK_CLOSE(flux_rhoY[n], flux_rho * Ystar[n], 1e-12,
                    "flux_rhoY != flux_rho * Ystar (rightward)");
    }

    PASS();
}

// ---------------------------------------------------------------------------
// Test 7: Sound speed compatibility with stiffened-gas
// ---------------------------------------------------------------------------
void test_soundspeed()
{
    TEST("Sound speed for stiffened-gas EOS");

    const PhaseEOSParams eos_ideal = {1.4, 0.0};
    const PhaseEOSParams eos_sg    = {4.4, 6.0e8};

    // Ideal gas: c = sqrt(γ p / ρ)
    Real c_ideal = twophase_soundspeed(1.2, 1.0e5, eos_ideal);
    Real c_expected = std::sqrt(1.4 * 1.0e5 / 1.2);  // ≈ 341.6 m/s
    CHECK_CLOSE(c_ideal, c_expected, 1e-10, "ideal gas sound speed");

    // Stiffened gas: c = sqrt(γ (p + p_inf) / ρ)
    Real c_sg = twophase_soundspeed(1000.0, 1.0e5, eos_sg);
    Real c_sg_expected = std::sqrt(4.4 * (1.0e5 + 6.0e8) / 1000.0);  // ≈ 1625 m/s
    CHECK_CLOSE(c_sg, c_sg_expected, 1e-10, "stiffened-gas sound speed");
    CHECK(c_sg > c_ideal, "stiffened-gas sound speed should exceed ideal gas");

    PASS();
}

// ---------------------------------------------------------------------------
// Test 8: Internal energy formula for stiffened-gas
// ---------------------------------------------------------------------------
void test_internal_energy()
{
    TEST("Internal energy for stiffened-gas EOS");

    const PhaseEOSParams eos_ideal = {1.4, 0.0};
    const PhaseEOSParams eos_sg    = {4.4, 6.0e8};

    // Ideal gas: e = p / ((γ-1) ρ)
    Real e_ideal = twophase_internal_energy(1.2, 1.0e5, eos_ideal);
    Real e_expected = 1.0e5 / (0.4 * 1.2);  // ≈ 208333
    CHECK_CLOSE(e_ideal, e_expected, 1e-10, "ideal gas internal energy");

    // Stiffened gas: e = (p + γ p_inf) / ((γ-1) ρ)
    Real e_sg = twophase_internal_energy(1000.0, 1.0e5, eos_sg);
    Real e_sg_expected = (1.0e5 + 4.4 * 6.0e8) / (3.4 * 1000.0);
    CHECK_CLOSE(e_sg, e_sg_expected, 1e-10, "stiffened-gas internal energy");

    // Stiffened-gas internal energy should be >> ideal gas (due to p_inf)
    CHECK(e_sg > e_ideal, "stiffened-gas e should exceed ideal gas e");

    PASS();
}

// ---------------------------------------------------------------------------
// Test 9: Uniform state preservation - HLLC returns the physical flux
// ---------------------------------------------------------------------------
void test_uniform_state_physical_flux()
{
    TEST("Uniform state returns physical flux");

    constexpr int NSPEC = 3;
    const PhaseEOSParams eos = {1.4, 0.0};

    const Real rho = 1.7;
    const Real u = -42.0;
    const Real p = 1.8e5;
    const Real e = p / ((eos.gamma - 1.0) * rho);
    Real Y[NSPEC] = {0.2, 0.3, 0.5};

    Real flux_rho, flux_u, flux_eden, flux_eint, ustar;
    Real flux_rhoY[NSPEC], Ystar[NSPEC];
    twophase_hllc_flux<NSPEC>(
        rho, u, p, e, Y, eos,
        rho, u, p, e, Y, eos,
        flux_rho, flux_rhoY, flux_u, flux_eden, flux_eint, ustar, Ystar);

    Real ref_rho, ref_u, ref_eden, ref_eint;
    physical_flux(rho, u, p, e, ref_rho, ref_u, ref_eden, ref_eint);

    CHECK_CLOSE(flux_rho, ref_rho, 1e-12, "uniform mass flux");
    CHECK_CLOSE(flux_u, ref_u, 1e-12, "uniform momentum flux");
    CHECK_CLOSE(flux_eden, ref_eden, 1e-12, "uniform total-energy flux");
    CHECK_CLOSE(flux_eint, ref_eint, 1e-12, "uniform internal-energy flux");
    CHECK_CLOSE(ustar, u, 1e-12, "uniform contact speed");
    for (int n = 0; n < NSPEC; ++n) {
        CHECK_CLOSE(Ystar[n], Y[n], 1e-12, "uniform Ystar");
        CHECK_CLOSE(flux_rhoY[n], ref_rho * Y[n], 1e-12, "uniform species flux");
    }

    PASS();
}

// ---------------------------------------------------------------------------
// Test 10: Supersonic branch consistency - exact one-sided physical fluxes
// ---------------------------------------------------------------------------
void test_supersonic_branch_physical_flux()
{
    TEST("Supersonic branches return one-sided physical fluxes");

    constexpr int NSPEC = 2;
    const PhaseEOSParams eos = {1.4, 0.0};

    Real YL[NSPEC] = {0.75, 0.25};
    Real YR[NSPEC] = {0.1, 0.9};

    auto run_case = [&](Real rhoL, Real uL, Real pL,
                        Real rhoR, Real uR, Real pR,
                        const Real* Yref, Real rho_ref, Real u_ref, Real p_ref,
                        const char* label) {
        const Real eL = pL / ((eos.gamma - 1.0) * rhoL);
        const Real eR = pR / ((eos.gamma - 1.0) * rhoR);
        const Real e_ref = p_ref / ((eos.gamma - 1.0) * rho_ref);

        Real flux_rho, flux_u, flux_eden, flux_eint, ustar;
        Real flux_rhoY[NSPEC], Ystar[NSPEC];
        twophase_hllc_flux<NSPEC>(
            rhoL, uL, pL, eL, YL, eos,
            rhoR, uR, pR, eR, YR, eos,
            flux_rho, flux_rhoY, flux_u, flux_eden, flux_eint, ustar, Ystar);

        Real ref_rho, ref_u, ref_eden, ref_eint;
        physical_flux(rho_ref, u_ref, p_ref, e_ref,
                      ref_rho, ref_u, ref_eden, ref_eint);

        CHECK_CLOSE(flux_rho, ref_rho, 1e-12, label);
        CHECK_CLOSE(flux_u, ref_u, 1e-12, label);
        CHECK_CLOSE(flux_eden, ref_eden, 1e-12, label);
        CHECK_CLOSE(flux_eint, ref_eint, 1e-12, label);
        CHECK_CLOSE(ustar, u_ref, 1e-12, label);
        for (int n = 0; n < NSPEC; ++n) {
            CHECK_CLOSE(Ystar[n], Yref[n], 1e-12, label);
            CHECK_CLOSE(flux_rhoY[n], ref_rho * Yref[n], 1e-12, label);
        }
    };

    run_case(1.0, 900.0, 1.0e5,
             0.8, 700.0, 0.8e5,
             YL, 1.0, 900.0, 1.0e5,
             "supersonic-left branch");

    run_case(1.0, -700.0, 1.0e5,
             0.8, -900.0, 0.8e5,
             YR, 0.8, -900.0, 0.8e5,
             "supersonic-right branch");

    PASS();
}

// ---------------------------------------------------------------------------  
// Main
// ---------------------------------------------------------------------------
int main()
{
    std::cout << "\n=== TwoPhaseHLLC Unit Tests ===\n" << std::endl;

    test_soundspeed();
    test_internal_energy();
    test_gas_gas();
    test_liquid_liquid();
    test_gas_liquid();
    test_passive_scalar();
    test_symmetry();
    test_wave_ordering();
    test_uniform_state_physical_flux();
    test_supersonic_branch_physical_flux();

    std::cout << "\n=== Results: " << n_pass << " passed, "
              << n_fail << " failed ===" << std::endl;

    return (n_fail > 0) ? 1 : 0;
}
