#include "WENO.H"

#include <cmath>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

int g_failed = 0;

void check(const std::string& name, bool ok, const std::string& detail = "")
{
  std::cout << (ok ? "[PASS] " : "[FAIL] ") << name;
  if (!detail.empty()) {
    std::cout << " (" << detail << ")";
  }
  std::cout << '\n';
  if (!ok) {
    ++g_failed;
  }
}

bool near(amrex::Real a, amrex::Real b, amrex::Real tol)
{
  return std::abs(a - b) <= tol;
}

std::string format_real(amrex::Real value)
{
  std::ostringstream os;
  os << std::scientific << std::setprecision(12) << value;
  return os.str();
}

constexpr amrex::Real pi()
{
  return amrex::Real(3.141592653589793238462643383279502884);
}

amrex::Real sine_value(amrex::Real x)
{
  return std::sin(2.0 * pi() * x);
}

amrex::Real sine_cell_average(int i, int n)
{
  const amrex::Real dx = 1.0 / static_cast<amrex::Real>(n);
  const amrex::Real x_lo = static_cast<amrex::Real>(i) * dx;
  const amrex::Real x_hi = static_cast<amrex::Real>(i + 1) * dx;
  return (std::cos(2.0 * pi() * x_lo) - std::cos(2.0 * pi() * x_hi)) /
         (2.0 * pi() * dx);
}

amrex::Real weno5z_sine_l1(int n)
{
  const amrex::Real dx = 1.0 / static_cast<amrex::Real>(n);
  std::vector<amrex::Real> u(n);
  for (int i = 0; i < n; ++i) {
    u[static_cast<std::size_t>(i)] = sine_cell_average(i, n);
  }

  amrex::Real sum = 0.0;
  int count = 0;
  for (int i = 3; i <= n - 4; ++i) {
    amrex::Real s5[5] = {
      u[static_cast<std::size_t>(i - 2)],
      u[static_cast<std::size_t>(i - 1)],
      u[static_cast<std::size_t>(i)],
      u[static_cast<std::size_t>(i + 1)],
      u[static_cast<std::size_t>(i + 2)]};
    amrex::Real sm = 0.0;
    amrex::Real sp = 0.0;
    weno_reconstruct_5z(s5, sm, sp);
    const amrex::Real exact = sine_value((static_cast<amrex::Real>(i) + 1.0) * dx);
    sum += std::abs(sp - exact);
    ++count;
  }
  return sum / static_cast<amrex::Real>(count);
}

amrex::Real linear_sine_l1(int n)
{
  const amrex::Real dx = 1.0 / static_cast<amrex::Real>(n);
  std::vector<amrex::Real> u(n);
  for (int i = 0; i < n; ++i) {
    u[static_cast<std::size_t>(i)] = sine_cell_average(i, n);
  }

  amrex::Real sum = 0.0;
  int count = 0;
  for (int i = 3; i <= n - 4; ++i) {
    const amrex::Real face = 0.5 *
      (u[static_cast<std::size_t>(i)] + u[static_cast<std::size_t>(i + 1)]);
    const amrex::Real exact = sine_value((static_cast<amrex::Real>(i) + 1.0) * dx);
    sum += std::abs(face - exact);
    ++count;
  }
  return sum / static_cast<amrex::Real>(count);
}

amrex::Real observed_order(amrex::Real coarse_error, amrex::Real fine_error)
{
  return std::log(coarse_error / fine_error) / std::log(2.0);
}

void test_constant_preservation()
{
  amrex::Real s5[5] = {2.5, 2.5, 2.5, 2.5, 2.5};
  amrex::Real sm = 0.0;
  amrex::Real sp = 0.0;

  weno_reconstruct_5js(s5, sm, sp);
  check("PeleC WENO5-JS constant preservation", near(sm, 2.5, 1.0e-14) && near(sp, 2.5, 1.0e-14));

  sm = 0.0;
  sp = 0.0;
  weno_reconstruct_5z(s5, sm, sp);
  check("PeleC WENO5-Z constant preservation", near(sm, 2.5, 1.0e-14) && near(sp, 2.5, 1.0e-14));

  amrex::Real s7[7] = {2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5};
  sm = 0.0;
  sp = 0.0;
  weno_reconstruct_7z(s7, sm, sp);
  check("PeleC WENO7-Z constant preservation", near(sm, 2.5, 1.0e-14) && near(sp, 2.5, 1.0e-14));

  amrex::Real s3[3] = {2.5, 2.5, 2.5};
  sm = 0.0;
  sp = 0.0;
  weno_reconstruct_3z(s3, sm, sp);
  check("PeleC WENO3-Z constant preservation", near(sm, 2.5, 1.0e-14) && near(sp, 2.5, 1.0e-14));
}

void test_linear_exactness()
{
  constexpr amrex::Real a = 0.75;
  constexpr amrex::Real b = -1.25;
  amrex::Real s5[5] = {b - 2.0 * a, b - a, b, b + a, b + 2.0 * a};
  amrex::Real sm = 0.0;
  amrex::Real sp = 0.0;
  const amrex::Real left = b - 0.5 * a;
  const amrex::Real right = b + 0.5 * a;

  weno_reconstruct_5js(s5, sm, sp);
  check("PeleC WENO5-JS linear exactness", near(sm, left, 1.0e-12) && near(sp, right, 1.0e-12));

  sm = 0.0;
  sp = 0.0;
  weno_reconstruct_5z(s5, sm, sp);
  check("PeleC WENO5-Z linear exactness", near(sm, left, 1.0e-12) && near(sp, right, 1.0e-12));

  amrex::Real s7[7] = {b - 3.0 * a, b - 2.0 * a, b - a, b, b + a, b + 2.0 * a, b + 3.0 * a};
  sm = 0.0;
  sp = 0.0;
  weno_reconstruct_7z(s7, sm, sp);
  check("PeleC WENO7-Z linear exactness", near(sm, left, 1.0e-12) && near(sp, right, 1.0e-12));

  amrex::Real s3[3] = {b - a, b, b + a};
  sm = 0.0;
  sp = 0.0;
  weno_reconstruct_3z(s3, sm, sp);
  check("PeleC WENO3-Z linear exactness", near(sm, left, 1.0e-12) && near(sp, right, 1.0e-12));
}

void test_step_bounds()
{
  amrex::Real s5[5] = {0.0, 0.0, 0.0, 1.0, 1.0};
  amrex::Real sm = 0.0;
  amrex::Real sp = 0.0;
  weno_reconstruct_5z(s5, sm, sp);
  const bool weno5_ok = std::isfinite(sm) && std::isfinite(sp) && sm >= -0.25 && sm <= 1.25 && sp >= -0.25 && sp <= 1.25;
  check("PeleC WENO5-Z controlled step response", weno5_ok, "sm=" + std::to_string(sm) + " sp=" + std::to_string(sp));

  amrex::Real s7[7] = {0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0};
  sm = 0.0;
  sp = 0.0;
  weno_reconstruct_7z(s7, sm, sp);
  const bool weno7_ok = std::isfinite(sm) && std::isfinite(sp) && sm >= -0.25 && sm <= 1.25 && sp >= -0.25 && sp <= 1.25;
  check("PeleC WENO7-Z controlled step response", weno7_ok, "sm=" + std::to_string(sm) + " sp=" + std::to_string(sp));
}


void test_smooth_sine_regression()
{
  const amrex::Real e32 = weno5z_sine_l1(32);
  const amrex::Real e64 = weno5z_sine_l1(64);
  const amrex::Real e128 = weno5z_sine_l1(128);
  const amrex::Real p32_64 = observed_order(e32, e64);
  const amrex::Real p64_128 = observed_order(e64, e128);
  const bool order_ok = std::isfinite(p32_64) && std::isfinite(p64_128) &&
                        p32_64 > 4.5 && p64_128 > 4.5;
  check("PeleC WENO5-Z smooth sine regression order", order_ok,
        "p32-64=" + format_real(p32_64) +
        " p64-128=" + format_real(p64_128));

  const amrex::Real linear_error = linear_sine_l1(64);
  const bool weno_beats_linear = e64 < 0.02 * linear_error;
  check("PeleC WENO5-Z beats second-order face average on smooth sine",
        weno_beats_linear,
        "weno=" + format_real(e64) +
        " linear=" + format_real(linear_error));
}

} // namespace

int main()
{
  test_constant_preservation();
  test_linear_exactness();
  test_step_bounds();
  test_smooth_sine_regression();
  return g_failed == 0 ? 0 : 1;
}
