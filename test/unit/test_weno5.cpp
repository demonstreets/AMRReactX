#include "weno5.H"

#include <iostream>
#include <vector>
#include <cmath>
#include <cstdint>

using namespace reconstruction;

static int g_passed = 0;

static void check(const char* name, bool cond, const std::string& detail = "")
{
    if (cond) {
        g_passed++;
        std::cout << "[PASS] " << name;
        if (!detail.empty()) std::cout << " (" << detail << ")";
        std::cout << std::endl;
    } else {
        std::cout << "[FAIL] " << name;
        if (!detail.empty()) std::cout << " (" << detail << ")";
        std::cout << std::endl;
    }
}

// ---------------------------------------------------------------------------
// T01: Sine 5th-order convergence
// ---------------------------------------------------------------------------
static void test_t01()
{
    // Grid: x in [0,1], N cells. u_i = cell-average of sin(2*pi*x).
    // Cell average formula: u_i = [cos(2*pi*xL) - cos(2*pi*xR)] / (2*pi*dx)
    // Exact face value at x_{i+1/2}: sin(2*pi * x_{i+1/2})
    // Validate both uL and uR converge at 5th order.

    const int Ns[] = {16, 32, 64, 128};
    const int num_N = 4;
    double l1_errors_L[num_N];
    double l1_errors_R[num_N];

    for (int k = 0; k < num_N; ++k) {
        const int N = Ns[k];
        const double dx = 1.0 / N;
        const double inv_2pi_dx = 1.0 / (2.0 * M_PI * dx);

        // Cell-averaged values u_i
        std::vector<double> u(N);
        for (int i = 0; i < N; ++i) {
            double xL = i * dx;
            double xR = (i + 1) * dx;
            u[i] = (std::cos(2.0 * M_PI * xL) - std::cos(2.0 * M_PI * xR)) * inv_2pi_dx;
        }

        // Reconstruct at interior faces i+1/2 for i = 2 .. N-3
        double l1_sum_L = 0.0, l1_sum_R = 0.0;
        int count = 0;
        for (int i = 2; i <= N - 3; ++i) {
            double uL, uR;
            weno5<double>(u[i-2], u[i-1], u[i], u[i+1], u[i+2], uL, uR, WENOVariant::Z);

            double x_face = (i + 1) * dx;
            double exact = std::sin(2.0 * M_PI * x_face);

            l1_sum_L += std::abs(uL - exact);
            l1_sum_R += std::abs(uR - exact);
            count++;
        }

        l1_errors_L[k] = l1_sum_L / count;
        l1_errors_R[k] = l1_sum_R / count;
    }

    // Fit convergence rate: use max(L1_L, L1_R) per grid
    double sum_x = 0, sum_y = 0, sum_xx = 0, sum_xy = 0;
    for (int k = 0; k < num_N; ++k) {
        double x = std::log2(Ns[k]);
        double e = (l1_errors_L[k] > l1_errors_R[k]) ? l1_errors_L[k] : l1_errors_R[k];
        double y = std::log2(e);
        sum_x  += x;
        sum_y  += y;
        sum_xx += x * x;
        sum_xy += x * y;
    }
    double slope = (num_N * sum_xy - sum_x * sum_y) / (num_N * sum_xx - sum_x * sum_x);

    char buf[128];
    std::snprintf(buf, sizeof(buf), "p=%.2f", -slope);
    check("T01: Sine 5th-order convergence", (-slope) >= 4.5, buf);
}

// ---------------------------------------------------------------------------
// T02: Constant preservation
// ---------------------------------------------------------------------------
static void test_t02()
{
    const double c = 1.0;
    double uL, uR;

    // Test with both variants
    weno5<double>(c, c, c, c, c, uL, uR, WENOVariant::Z);
    double err_z = std::max(std::abs(uL - c), std::abs(uR - c));

    weno5<double>(c, c, c, c, c, uL, uR, WENOVariant::JS);
    double err_js = std::max(std::abs(uL - c), std::abs(uR - c));

    double max_err = std::max(err_z, err_js);
    char buf[128];
    std::snprintf(buf, sizeof(buf), "max_err=%.1e", max_err);
    check("T02: Constant preservation", max_err < 1e-14, buf);
}

// ---------------------------------------------------------------------------
// T03: Linear exact reconstruction
// ---------------------------------------------------------------------------
static void test_t03()
{
    // u(x) = 2x + 1, sampled at cell centers on [0,1] with 64 cells
    // Validate both uL and uR are exact for linear functions.
    const int N = 64;
    const double dx = 1.0 / N;
    std::vector<double> u(N);
    for (int i = 0; i < N; ++i) {
        double xc = (i + 0.5) * dx;   // cell center
        u[i] = 2.0 * xc + 1.0;
    }

    double l1_sum_L = 0.0, l1_sum_R = 0.0;
    int count = 0;
    for (int i = 2; i <= N - 3; ++i) {
        double uL, uR;
        weno5<double>(u[i-2], u[i-1], u[i], u[i+1], u[i+2], uL, uR, WENOVariant::Z);
        double x_face = (i + 1) * dx;
        double exact = 2.0 * x_face + 1.0;
        l1_sum_L += std::abs(uL - exact);
        l1_sum_R += std::abs(uR - exact);
        count++;
    }

    double l1_L = l1_sum_L / count;
    double l1_R = l1_sum_R / count;
    double l1 = (l1_L > l1_R) ? l1_L : l1_R;
    char buf[128];
    std::snprintf(buf, sizeof(buf), "L1=%.1e", l1);
    check("T03: Linear exact reconstruction", l1 < 1e-12, buf);
}

// ---------------------------------------------------------------------------
// T04: Sod jump — no overshoot
// ---------------------------------------------------------------------------
static void test_t04()
{
    double uL, uR;
    const double v1 = 1.0;
    const double v2 = 3.857;

    // Stencil across Sod contact discontinuity
    weno5<double>(v1, v1, v1, v2, v2, uL, uR, WENOVariant::Z);

    bool ok = (uL >= v1 && uL <= v2) && (uR >= v1 && uR <= v2);
    char buf[128];
    std::snprintf(buf, sizeof(buf), "uL=%.6f uR=%.6f", uL, uR);
    check("T04: Sod jump — no overshoot", ok, buf);
}

// ---------------------------------------------------------------------------
// T05: Shock capture — monotone transition
// ---------------------------------------------------------------------------
static void test_t05()
{
    double uL, uR;
    // Shock: 0 -> 1
    weno5<double>(0.0, 0.0, 0.0, 1.0, 1.0, uL, uR, WENOVariant::Z);

    // uL should be close to 0 (left of shock) and uR close to 1 (right of shock)
    // Monotone: 0 <= uL <= uR <= 1
    bool ok = (uL >= 0.0 && uL <= uR && uR <= 1.0);
    char buf[128];
    std::snprintf(buf, sizeof(buf), "uL=%.6f uR=%.6f", uL, uR);
    check("T05: Shock capture — monotone transition", ok, buf);
}

// ---------------------------------------------------------------------------
// T06: WENO-JS vs WENO-Z — Z more accurate near critical point
// ---------------------------------------------------------------------------
static void test_t06()
{
    // Sample f(x)=x^3+1 at x=[-0.4,-0.2,0,0.2,0.4] (dx=0.2).
    // This stencil contains a critical point (f'(0)=0) where WENO-JS
    // loses accuracy but WENO-Z maintains near-optimal weights.
    // Face at x=0.1, exact value f(0.1) = 1 + 0.001 = 1.001.
    double u[5] = {0.936, 0.992, 1.0, 1.008, 1.064};
    const double exact_face = 1.001;   // f(0.1) = 0.1^3 + 1

    double uL_js, uR_js, uL_z, uR_z;
    weno5<double>(u[0], u[1], u[2], u[3], u[4], uL_js, uR_js, WENOVariant::JS);
    weno5<double>(u[0], u[1], u[2], u[3], u[4], uL_z,  uR_z,  WENOVariant::Z);

    // WENO-Z should be closer to the exact face value (more accurate)
    bool z_better = (std::abs(uR_z - exact_face) <= std::abs(uR_js - exact_face));
    char buf[128];
    std::snprintf(buf, sizeof(buf), "JS: uR=%.6f  Z: uR=%.6f  exact=%.3f", uR_js, uR_z, exact_face);
    check("T06: WENO-Z sharper than WENO-JS at discontinuity", z_better, buf);
}

// ---------------------------------------------------------------------------
// T07: Symmetry — weno5() left value equals weno5_left() result
// ---------------------------------------------------------------------------
static void test_t07()
{
    const int N = 64;
    const double dx = 1.0 / N;
    std::vector<double> u(N);
    for (int i = 0; i < N; ++i) {
        double xc = (i + 0.5) * dx;
        u[i] = std::sin(2.0 * M_PI * xc);
    }

    double max_diff = 0.0;
    for (int i = 2; i <= N - 3; ++i) {
        double uL_full, uR_full;
        weno5<double>(u[i-2], u[i-1], u[i], u[i+1], u[i+2], uL_full, uR_full, WENOVariant::Z);

        double uL_sep = weno5_left<double>(u[i-2], u[i-1], u[i], u[i+1], u[i+2], WENOVariant::Z);

        double diff = std::abs(uL_full - uL_sep);
        if (diff > max_diff) max_diff = diff;
    }

    char buf[128];
    std::snprintf(buf, sizeof(buf), "diff=%.1e", max_diff);
    check("T07: Symmetry OK (weno5 vs weno5_left)", max_diff < 1e-13, buf);
}

// ---------------------------------------------------------------------------
// T08: float compatibility — convergence
// ---------------------------------------------------------------------------
static void test_t08()
{
    // Use only 3 grid sizes for float: N=128 has L1 error below float precision (~1e-7)
    // Validate both uL and uR converge.
    const int Ns[] = {16, 32, 64};
    const int num_N = 3;
    float l1_errors_L[num_N];
    float l1_errors_R[num_N];

    for (int k = 0; k < num_N; ++k) {
        const int N = Ns[k];
        const float dx = 1.0f / N;
        const float inv_2pi_dx = 1.0f / (2.0f * float(M_PI) * dx);

        std::vector<float> u(N);
        for (int i = 0; i < N; ++i) {
            float xL = i * dx;
            float xR = (i + 1) * dx;
            u[i] = (std::cos(2.0f * float(M_PI) * xL)
                  - std::cos(2.0f * float(M_PI) * xR)) * inv_2pi_dx;
        }

        float l1_sum_L = 0.0f, l1_sum_R = 0.0f;
        int count = 0;
        for (int i = 2; i <= N - 3; ++i) {
            float uL, uR;
            weno5<float>(u[i-2], u[i-1], u[i], u[i+1], u[i+2], uL, uR, WENOVariant::Z);

            float x_face = (i + 1) * dx;
            float exact = std::sin(2.0f * float(M_PI) * x_face);

            l1_sum_L += std::abs(uL - exact);
            l1_sum_R += std::abs(uR - exact);
            count++;
        }

        l1_errors_L[k] = l1_sum_L / count;
        l1_errors_R[k] = l1_sum_R / count;
    }

    // Fit convergence rate: use max(L1_L, L1_R) per grid
    double sum_x = 0, sum_y = 0, sum_xx = 0, sum_xy = 0;
    for (int k = 0; k < num_N; ++k) {
        double x = std::log2(static_cast<double>(Ns[k]));
        float e = (l1_errors_L[k] > l1_errors_R[k]) ? l1_errors_L[k] : l1_errors_R[k];
        double y = std::log2(static_cast<double>(e));
        sum_x  += x;
        sum_y  += y;
        sum_xx += x * x;
        sum_xy += x * y;
    }
    double slope = (num_N * sum_xy - sum_x * sum_y) / (num_N * sum_xx - sum_x * sum_x);

    char buf[128];
    std::snprintf(buf, sizeof(buf), "p=%.1f", -slope);
    check("T08: float convergence OK", (-slope) >= 2.5, buf);
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------
int main()
{
    std::cout << "=== WENO5 Unit Tests ===" << std::endl;

    test_t01();
    test_t02();
    test_t03();
    test_t04();
    test_t05();
    test_t06();
    test_t07();
    test_t08();

    std::cout << "=== " << g_passed << "/8 PASS ===" << std::endl;
    return (g_passed == 8) ? 0 : 1;
}