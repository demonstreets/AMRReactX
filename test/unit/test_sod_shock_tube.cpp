#include "sod_shock_tube.H"

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

struct Totals {
  double mass = 0.0;
  double momentum = 0.0;
  double energy = 0.0;
};

Totals integrate_exact(const v::SodSolution& sol, double t, int n)
{
  const double dx = 1.0 / static_cast<double>(n);
  Totals total;
  for (int i = 0; i < n; ++i) {
    const double x = (static_cast<double>(i) + 0.5) * dx;
    const auto s = v::sample(sol, x, t);
    total.mass += s.rho * dx;
    total.momentum += s.rho * s.u * dx;
    total.energy += v::total_energy_density(s, sol.gamma) * dx;
    require(s.rho > 0.0 && s.p > 0.0 && std::isfinite(s.u), "nonphysical Sod sample");
  }
  return total;
}

} // namespace

int main()
{
  const v::SodState left{1.0, 0.0, 1.0};
  const v::SodState right{0.125, 0.0, 0.1};
  const auto sol = v::make_sod_solution(left, right, 1.4, 0.5);

  near(sol.p_star, 0.303130178, 5.0e-9, "Sod p_star reference");
  near(sol.u_star, 0.927452620, 5.0e-9, "Sod u_star reference");

  const double t = 0.2;
  const auto undisturbed_left = v::sample(sol, 0.10, t);
  near(undisturbed_left.rho, 1.0, 1.0e-12, "left state rho");
  near(undisturbed_left.u, 0.0, 1.0e-12, "left state u");
  near(undisturbed_left.p, 1.0, 1.0e-12, "left state p");

  const auto fan = v::sample(sol, 0.30, t);
  near(fan.rho, 0.8774525327552777, 1.0e-12, "fan rho");
  near(fan.u, 0.1526799638499357, 1.0e-12, "fan u");
  near(fan.p, 0.8327470150499660, 1.0e-12, "fan p");

  const auto left_star = v::sample(sol, 0.60, t);
  near(left_star.rho, 0.4263194281784952, 5.0e-12, "left star rho");
  near(left_star.u, sol.u_star, 1.0e-12, "left star u");
  near(left_star.p, sol.p_star, 1.0e-12, "left star p");

  const auto right_star = v::sample(sol, 0.70, t);
  near(right_star.rho, 0.2655737117053071, 5.0e-12, "right star rho");
  near(right_star.u, sol.u_star, 1.0e-12, "right star u");
  near(right_star.p, sol.p_star, 1.0e-12, "right star p");

  const auto undisturbed_right = v::sample(sol, 0.95, t);
  near(undisturbed_right.rho, 0.125, 1.0e-12, "right state rho");
  near(undisturbed_right.u, 0.0, 1.0e-12, "right state u");
  near(undisturbed_right.p, 0.1, 1.0e-12, "right state p");

  const auto initial = integrate_exact(sol, 0.0, 200000);
  const auto evolved = integrate_exact(sol, t, 200000);
  near(evolved.mass, initial.mass, 2.0e-6, "domain mass conservation before boundary interaction");
  near(evolved.momentum, (left.p - right.p) * t, 2.0e-6, "domain momentum change from pressure boundary force");
  near(evolved.energy, initial.energy, 2.0e-6, "domain energy conservation before boundary interaction");

  bool threw = false;
  try {
    (void)v::make_sod_solution({-1.0, 0.0, 1.0}, right);
  } catch (const std::invalid_argument&) {
    threw = true;
  }
  require(threw, "invalid Sod input should throw");

  std::cout << "sod_shock_tube_validation PASS p_star=" << sol.p_star
            << " u_star=" << sol.u_star
            << " mass=" << evolved.mass
            << " momentum=" << evolved.momentum
            << " energy=" << evolved.energy << "\n";
  return 0;
}
