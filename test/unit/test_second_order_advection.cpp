#include "second_order_advection.H"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using namespace MyPele::Engineering::Numerics;

namespace {

constexpr double pi = 3.141592653589793238462643383279502884;

void require_true(const bool condition, const std::string& message)
{
    if (!condition) {
        std::cerr << "second_order_advection_smoke failure: " << message << "\n";
        std::exit(1);
    }
}

void require_near(const double value,
                  const double expected,
                  const double tolerance,
                  const std::string& message)
{
    if (std::abs(value - expected) > tolerance) {
        std::cerr << "second_order_advection_smoke failure: " << message
                  << " value=" << value << " expected=" << expected
                  << " tolerance=" << tolerance << "\n";
        std::exit(1);
    }
}

std::vector<double> sine_cell_average(const int n)
{
    std::vector<double> q(static_cast<std::size_t>(n));
    const double dx = 1.0 / static_cast<double>(n);
    for (int i = 0; i < n; ++i) {
        const double xlo = i * dx;
        const double xhi = (i + 1) * dx;
        q[static_cast<std::size_t>(i)] =
            (std::cos(2.0 * pi * xlo) - std::cos(2.0 * pi * xhi)) /
            (2.0 * pi * dx);
    }
    return q;
}

double sine_rhs_l1_error(const int n)
{
    const double velocity = 1.7;
    const double dx = 1.0 / static_cast<double>(n);
    const std::vector<double> q = sine_cell_average(n);
    const std::vector<double> rhs = periodic_advection_rhs(q, velocity, dx, false);

    std::vector<double> err(static_cast<std::size_t>(n));
    for (int i = 0; i < n; ++i) {
        const double xc = (static_cast<double>(i) + 0.5) * dx;
        const double exact = -velocity * 2.0 * pi * std::cos(2.0 * pi * xc);
        err[static_cast<std::size_t>(i)] = rhs[static_cast<std::size_t>(i)] - exact;
    }
    return l1_norm(err, dx);
}

} // namespace

int main()
{
    {
        const std::vector<double> q(32, 3.25);
        const auto rhs = periodic_advection_rhs(q, 2.0, 1.0 / 32.0);
        for (const double value : rhs) {
            require_near(value, 0.0, 1.0e-14, "constant field has zero advection RHS");
        }
    }

    {
        const std::vector<double> q{0.0, 0.0, 1.0, 1.0, 0.0, 0.0};
        const auto slopes = periodic_muscl_slopes(q, true);
        require_near(slopes[1], 0.0, 1.0e-14, "limiter suppresses new extremum at rising step");
        require_near(slopes[2], 0.0, 1.0e-14, "limiter suppresses new extremum on plateau");
        require_near(slopes[3], 0.0, 1.0e-14, "limiter suppresses new extremum at falling step");
    }

    {
        std::vector<double> q(64, 0.1);
        for (int i = 24; i < 40; ++i) {
            q[static_cast<std::size_t>(i)] = 0.8;
        }
        const double dx = 1.0 / static_cast<double>(q.size());
        const double mass0 = periodic_mass(q, dx);
        const auto next = forward_euler_periodic_advection(q, 1.0, dx, 0.35 * dx, true);
        const double mass1 = periodic_mass(next, dx);
        require_near(mass1, mass0, 1.0e-14, "periodic finite-volume update conserves mass");
        const auto bounds = std::minmax_element(next.begin(), next.end());
        require_true(*bounds.first >= -1.0e-14, "limited update remains nonnegative for CFL<1");
        require_true(*bounds.second <= 0.8 + 1.0e-14, "limited update does not overshoot top-hat maximum");
    }

    const double e32 = sine_rhs_l1_error(32);
    const double e64 = sine_rhs_l1_error(64);
    const double e128 = sine_rhs_l1_error(128);
    const double p32_64 = std::log(e32 / e64) / std::log(2.0);
    const double p64_128 = std::log(e64 / e128) / std::log(2.0);

    require_true(e32 > e64 && e64 > e128, "smooth sine RHS errors decrease with refinement");
    require_true(p32_64 > 1.90, "32->64 sine RHS convergence is second order");
    require_true(p64_128 > 1.95, "64->128 sine RHS convergence is second order");

    std::cout << "second_order_advection_smoke PASS e32=" << e32
              << " e64=" << e64 << " e128=" << e128
              << " p32_64=" << p32_64 << " p64_128=" << p64_128 << "\n";
    return 0;
}
