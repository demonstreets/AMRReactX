#ifndef MYPELE_ENGINEERING_NUMERICS_SECOND_ORDER_ADVECTION_H
#define MYPELE_ENGINEERING_NUMERICS_SECOND_ORDER_ADVECTION_H

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <vector>

namespace MyPele::Engineering::Numerics {

inline double minmod(const double a, const double b)
{
    if (a * b <= 0.0) {
        return 0.0;
    }
    return std::copysign(std::min(std::abs(a), std::abs(b)), a);
}

inline std::vector<double> periodic_muscl_slopes(const std::vector<double>& q,
                                                 const bool limited = true)
{
    const std::size_t n = q.size();
    std::vector<double> slope(n, 0.0);
    if (n < 3) {
        return slope;
    }
    for (std::size_t i = 0; i < n; ++i) {
        const double dl = q[i] - q[(i + n - 1) % n];
        const double dr = q[(i + 1) % n] - q[i];
        slope[i] = limited ? minmod(dl, dr) : 0.5 * (dl + dr);
    }
    return slope;
}

inline std::vector<double> periodic_upwind_muscl_flux(const std::vector<double>& q,
                                                      const double velocity,
                                                      const bool limited = true)
{
    const std::size_t n = q.size();
    std::vector<double> flux(n, 0.0);
    if (n == 0) {
        return flux;
    }
    const std::vector<double> slope = periodic_muscl_slopes(q, limited);
    for (std::size_t iface = 0; iface < n; ++iface) {
        const std::size_t left = iface;
        const std::size_t right = (iface + 1) % n;
        const double q_face = velocity >= 0.0 ? q[left] + 0.5 * slope[left]
                                             : q[right] - 0.5 * slope[right];
        flux[iface] = velocity * q_face;
    }
    return flux;
}

inline std::vector<double> periodic_advection_rhs(const std::vector<double>& q,
                                                  const double velocity,
                                                  const double dx,
                                                  const bool limited = true)
{
    const std::size_t n = q.size();
    std::vector<double> rhs(n, 0.0);
    if (n == 0 || dx <= 0.0) {
        return rhs;
    }
    const std::vector<double> flux = periodic_upwind_muscl_flux(q, velocity, limited);
    for (std::size_t i = 0; i < n; ++i) {
        const double f_hi = flux[i];
        const double f_lo = flux[(i + n - 1) % n];
        rhs[i] = -(f_hi - f_lo) / dx;
    }
    return rhs;
}

inline std::vector<double> forward_euler_periodic_advection(
    const std::vector<double>& q,
    const double velocity,
    const double dx,
    const double dt,
    const bool limited = true)
{
    std::vector<double> next(q);
    const std::vector<double> rhs = periodic_advection_rhs(q, velocity, dx, limited);
    for (std::size_t i = 0; i < next.size(); ++i) {
        next[i] += dt * rhs[i];
    }
    return next;
}

inline double periodic_mass(const std::vector<double>& q, const double dx)
{
    double sum = 0.0;
    for (const double value : q) {
        sum += value;
    }
    return sum * dx;
}

inline double l1_norm(const std::vector<double>& values, const double dx)
{
    double sum = 0.0;
    for (const double value : values) {
        sum += std::abs(value);
    }
    return sum * dx;
}

} // namespace MyPele::Engineering::Numerics

#endif
