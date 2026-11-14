#pragma once

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace my_pele::academic::validation {

struct VortexState {
  double rho = 0.0;
  double u = 0.0;
  double v = 0.0;
  double p = 0.0;
  double temperature = 0.0;
};

struct IsentropicVortexParams {
  double gamma = 1.4;
  double beta = 5.0;
  double x0 = 5.0;
  double y0 = 5.0;
  double u_inf = 1.0;
  double v_inf = 1.0;
  double domain_x = 10.0;
  double domain_y = 10.0;
};

inline double wrap_periodic_delta(double x, double center, double period)
{
  if (!(period > 0.0)) {
    throw std::invalid_argument("invalid vortex period");
  }
  double d = x - center;
  d -= period * std::floor(d / period + 0.5);
  return d;
}

inline double periodic_position(double x, double period)
{
  if (!(period > 0.0)) {
    throw std::invalid_argument("invalid vortex period");
  }
  double y = std::fmod(x, period);
  if (y < 0.0) {
    y += period;
  }
  return y;
}

inline VortexState sample_isentropic_vortex(const IsentropicVortexParams& p, double x, double y, double time)
{
  if (!(p.gamma > 1.0) || !(p.beta > 0.0) || !(p.domain_x > 0.0) || !(p.domain_y > 0.0) || !(time >= 0.0)) {
    throw std::invalid_argument("invalid isentropic vortex parameters");
  }
  constexpr double pi = 3.141592653589793238462643383279502884;
  const double cx = periodic_position(p.x0 + p.u_inf * time, p.domain_x);
  const double cy = periodic_position(p.y0 + p.v_inf * time, p.domain_y);
  const double dx = wrap_periodic_delta(x, cx, p.domain_x);
  const double dy = wrap_periodic_delta(y, cy, p.domain_y);
  const double r2 = dx * dx + dy * dy;
  const double e = std::exp(0.5 * (1.0 - r2));
  const double du = -p.beta / (2.0 * pi) * e * dy;
  const double dv = p.beta / (2.0 * pi) * e * dx;
  const double temperature = 1.0 - (p.gamma - 1.0) * p.beta * p.beta / (8.0 * p.gamma * pi * pi) * std::exp(1.0 - r2);
  if (!(temperature > 0.0)) {
    throw std::runtime_error("isentropic vortex temperature became nonpositive");
  }
  const double rho = std::pow(temperature, 1.0 / (p.gamma - 1.0));
  const double pressure = std::pow(rho, p.gamma);
  return {rho, p.u_inf + du, p.v_inf + dv, pressure, temperature};
}

inline double total_energy_density(const VortexState& s, double gamma)
{
  if (!(gamma > 1.0) || !(s.rho > 0.0) || !(s.p > 0.0)) {
    throw std::invalid_argument("invalid vortex state");
  }
  return s.p / (gamma - 1.0) + 0.5 * s.rho * (s.u * s.u + s.v * s.v);
}

inline double entropy_invariant(const VortexState& s, double gamma)
{
  if (!(gamma > 1.0) || !(s.rho > 0.0) || !(s.p > 0.0)) {
    throw std::invalid_argument("invalid vortex state");
  }
  return s.p / std::pow(s.rho, gamma);
}

} // namespace my_pele::academic::validation
