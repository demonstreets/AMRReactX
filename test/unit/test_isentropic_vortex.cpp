#include "isentropic_vortex.H"

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>

namespace v = my_pele::academic::validation;

namespace {

void require(bool ok, const std::string& msg)
{
  if (!ok) {
    throw std::runtime_error(msg);
  }
}

void near(double value, double expected, double tol, const std::string& msg)
{
  if (std::abs(value - expected) > tol) {
    throw std::runtime_error(msg + ": got " + std::to_string(value) + " expected " + std::to_string(expected));
  }
}

double cell_average_density(const v::IsentropicVortexParams& p, double xlo, double ylo, double dx, double dy, double time)
{
  constexpr int q = 8;
  double sum = 0.0;
  for (int j = 0; j < q; ++j) {
    for (int i = 0; i < q; ++i) {
      const double x = xlo + (static_cast<double>(i) + 0.5) * dx / static_cast<double>(q);
      const double y = ylo + (static_cast<double>(j) + 0.5) * dy / static_cast<double>(q);
      sum += v::sample_isentropic_vortex(p, x, y, time).rho;
    }
  }
  return sum / static_cast<double>(q * q);
}

double midpoint_density_error(const v::IsentropicVortexParams& p, int n, double time)
{
  const double dx = p.domain_x / static_cast<double>(n);
  const double dy = p.domain_y / static_cast<double>(n);
  double err = 0.0;
  for (int j = 0; j < n; ++j) {
    for (int i = 0; i < n; ++i) {
      const double xlo = static_cast<double>(i) * dx;
      const double ylo = static_cast<double>(j) * dy;
      const double midpoint = v::sample_isentropic_vortex(p, xlo + 0.5 * dx, ylo + 0.5 * dy, time).rho;
      const double avg = cell_average_density(p, xlo, ylo, dx, dy, time);
      err += std::abs(midpoint - avg) * dx * dy;
    }
  }
  return err / (p.domain_x * p.domain_y);
}

} // namespace

int main()
{
  const v::IsentropicVortexParams params{};
  const double t = 0.7;

  const auto center = v::sample_isentropic_vortex(params, params.x0 + params.u_inf * t, params.y0 + params.v_inf * t, t);
  near(center.u, params.u_inf, 1.0e-13, "center u perturbation");
  near(center.v, params.v_inf, 1.0e-13, "center v perturbation");
  require(center.rho > 0.0 && center.p > 0.0 && center.temperature > 0.0, "center state positivity");
  near(v::entropy_invariant(center, params.gamma), 1.0, 2.0e-14, "center entropy invariant");
  require(v::total_energy_density(center, params.gamma) > 0.0, "positive total energy");

  const auto shifted = v::sample_isentropic_vortex(params, params.x0, params.y0, 0.0);
  near(center.rho, shifted.rho, 2.0e-14, "periodic translation rho");
  near(center.p, shifted.p, 2.0e-14, "periodic translation pressure");

  double min_temp = 1.0e100;
  double max_entropy_error = 0.0;
  for (int j = 0; j < 40; ++j) {
    for (int i = 0; i < 40; ++i) {
      const double x = (static_cast<double>(i) + 0.37) * params.domain_x / 40.0;
      const double y = (static_cast<double>(j) + 0.19) * params.domain_y / 40.0;
      const auto s = v::sample_isentropic_vortex(params, x, y, t);
      min_temp = std::min(min_temp, s.temperature);
      max_entropy_error = std::max(max_entropy_error, std::abs(v::entropy_invariant(s, params.gamma) - 1.0));
    }
  }
  require(min_temp > 0.0, "sampled temperature positivity");
  require(max_entropy_error < 3.0e-14, "entropy invariant across vortex field");

  const double e16 = midpoint_density_error(params, 16, t);
  const double e32 = midpoint_density_error(params, 32, t);
  const double e64 = midpoint_density_error(params, 64, t);
  const double p16_32 = std::log(e16 / e32) / std::log(2.0);
  const double p32_64 = std::log(e32 / e64) / std::log(2.0);
  require(e16 > e32 && e32 > e64, "midpoint density error should decrease");
  require(p16_32 > 1.85 && p32_64 > 1.90, "midpoint density cell-average convergence should be second order");

  bool threw = false;
  try {
    auto bad = params;
    bad.beta = -1.0;
    (void)v::sample_isentropic_vortex(bad, 0.0, 0.0, 0.0);
  } catch (const std::invalid_argument&) {
    threw = true;
  }
  require(threw, "invalid vortex parameters should throw");

  std::cout << "isentropic_vortex_validation PASS min_temp=" << min_temp
            << " entropy_linf=" << max_entropy_error
            << " e16=" << e16
            << " e32=" << e32
            << " e64=" << e64
            << " p16_32=" << p16_32
            << " p32_64=" << p32_64 << "\n";
  return 0;
}
