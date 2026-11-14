#pragma once

#ifndef MASA_HD
#  ifdef AMREX_GPU_HOST_DEVICE
#    define MASA_HD AMREX_GPU_HOST_DEVICE
#  elif defined(AMREX_GPU_DEVICE)
#    define MASA_HD AMREX_GPU_DEVICE
#  else
#    define MASA_HD
#  endif
#endif

#include <cmath>
#include <cstdio>

namespace MASA {

inline void masa_init(const char*, const char*) {}
inline void masa_set_param(const char*, double) {}
inline void masa_display_param()
{
  std::printf("MASA shim: nonconstant-density stationary manufactured solution\n");
}
inline void masa_sanity_check() {}

MASA_HD inline double masa_eval_3d_exact_rho(double x, double y, double z)
{
  constexpr double pi = 3.141592653589793238462643383279502884;
  return 1.0 + 0.05 * std::cos(2.0 * pi * x) * std::cos(2.0 * pi * y) *
                 std::cos(2.0 * pi * z);
}
MASA_HD inline double masa_eval_3d_exact_u(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_exact_v(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_exact_w(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_exact_p(double, double, double) { return 101325.0; }

MASA_HD inline double masa_eval_3d_source_rho(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_source_rho_u(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_source_rho_v(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_source_rho_w(double, double, double) { return 0.0; }
MASA_HD inline double masa_eval_3d_source_rho_e(double, double, double) { return 0.0; }

} // namespace MASA
