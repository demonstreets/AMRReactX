#pragma once

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace my_pele::academic::validation {

struct SodState {
  double rho = 0.0;
  double u = 0.0;
  double p = 0.0;
};

struct SodSolution {
  SodState left;
  SodState right;
  double gamma = 1.4;
  double x0 = 0.5;
  double p_star = 0.0;
  double u_star = 0.0;
};

inline double sound_speed(const SodState& s, double gamma)
{
  if (!(s.rho > 0.0) || !(s.p > 0.0) || !(gamma > 1.0)) {
    throw std::invalid_argument("invalid Sod state");
  }
  return std::sqrt(gamma * s.p / s.rho);
}

inline double pressure_function(double p, const SodState& s, double gamma)
{
  const double a = sound_speed(s, gamma);
  if (p > s.p) {
    const double A = 2.0 / ((gamma + 1.0) * s.rho);
    const double B = (gamma - 1.0) / (gamma + 1.0) * s.p;
    return (p - s.p) * std::sqrt(A / (p + B));
  }
  return 2.0 * a / (gamma - 1.0) * (std::pow(p / s.p, (gamma - 1.0) / (2.0 * gamma)) - 1.0);
}

inline double pressure_derivative(double p, const SodState& s, double gamma)
{
  const double a = sound_speed(s, gamma);
  if (p > s.p) {
    const double A = 2.0 / ((gamma + 1.0) * s.rho);
    const double B = (gamma - 1.0) / (gamma + 1.0) * s.p;
    const double root = std::sqrt(A / (p + B));
    return root * (1.0 - 0.5 * (p - s.p) / (p + B));
  }
  return (1.0 / (s.rho * a)) * std::pow(p / s.p, -(gamma + 1.0) / (2.0 * gamma));
}

inline SodSolution make_sod_solution(SodState left, SodState right, double gamma = 1.4, double x0 = 0.5)
{
  if (!(left.rho > 0.0) || !(left.p > 0.0) || !(right.rho > 0.0) || !(right.p > 0.0) || !(gamma > 1.0)) {
    throw std::invalid_argument("invalid Sod input");
  }
  const double a_l = sound_speed(left, gamma);
  const double a_r = sound_speed(right, gamma);
  double p = std::max(1.0e-12, 0.5 * (left.p + right.p) - 0.125 * (right.u - left.u) * (left.rho + right.rho) * (a_l + a_r));
  for (int iter = 0; iter < 40; ++iter) {
    const double f = pressure_function(p, left, gamma) + pressure_function(p, right, gamma) + right.u - left.u;
    const double df = pressure_derivative(p, left, gamma) + pressure_derivative(p, right, gamma);
    const double p_next = std::max(1.0e-14, p - f / df);
    if (std::abs(p_next - p) <= 1.0e-13 * std::max(1.0, p_next)) {
      p = p_next;
      break;
    }
    p = p_next;
  }
  const double u_star = 0.5 * (left.u + right.u + pressure_function(p, right, gamma) - pressure_function(p, left, gamma));
  return {left, right, gamma, x0, p, u_star};
}

inline SodState sample(const SodSolution& sol, double x, double t)
{
  if (!(t >= 0.0)) {
    throw std::invalid_argument("negative time");
  }
  if (t == 0.0) {
    return x < sol.x0 ? sol.left : sol.right;
  }
  const double gamma = sol.gamma;
  const double xi = (x - sol.x0) / t;
  const double a_l = sound_speed(sol.left, gamma);
  const double a_r = sound_speed(sol.right, gamma);

  if (xi <= sol.u_star) {
    const double p_ratio = sol.p_star / sol.left.p;
    const double a_star_l = a_l * std::pow(p_ratio, (gamma - 1.0) / (2.0 * gamma));
    const double head = sol.left.u - a_l;
    const double tail = sol.u_star - a_star_l;
    if (xi <= head) {
      return sol.left;
    }
    if (xi >= tail) {
      const double rho = sol.left.rho * std::pow(p_ratio, 1.0 / gamma);
      return {rho, sol.u_star, sol.p_star};
    }
    const double u = 2.0 / (gamma + 1.0) * (a_l + 0.5 * (gamma - 1.0) * sol.left.u + xi);
    const double a = 2.0 / (gamma + 1.0) * (a_l + 0.5 * (gamma - 1.0) * (sol.left.u - xi));
    const double rho = sol.left.rho * std::pow(a / a_l, 2.0 / (gamma - 1.0));
    const double p = sol.left.p * std::pow(a / a_l, 2.0 * gamma / (gamma - 1.0));
    return {rho, u, p};
  }

  const double p_ratio = sol.p_star / sol.right.p;
  const double rho_star_r = sol.right.rho * ((p_ratio + (gamma - 1.0) / (gamma + 1.0)) / ((gamma - 1.0) / (gamma + 1.0) * p_ratio + 1.0));
  const double shock_speed = sol.right.u + a_r * std::sqrt((gamma + 1.0) / (2.0 * gamma) * p_ratio + (gamma - 1.0) / (2.0 * gamma));
  if (xi < shock_speed) {
    return {rho_star_r, sol.u_star, sol.p_star};
  }
  return sol.right;
}

inline double total_energy_density(const SodState& s, double gamma)
{
  return s.p / (gamma - 1.0) + 0.5 * s.rho * s.u * s.u;
}

} // namespace my_pele::academic::validation
