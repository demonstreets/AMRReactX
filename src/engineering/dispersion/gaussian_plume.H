#ifndef MYPELE_ENGINEERING_GAUSSIAN_PLUME_H
#define MYPELE_ENGINEERING_GAUSSIAN_PLUME_H

#include <algorithm>
#include <cmath>

namespace MyPele::Engineering::Dispersion {

struct GaussianPlumeSource {
    double mass_flow_rate = 0.0;   // kg/s
    double wind_speed = 0.0;       // m/s
    double release_height = 0.0;   // m
    double sigma_y = 0.0;          // m
    double sigma_z = 0.0;          // m
};

inline bool valid(const GaussianPlumeSource& source)
{
    return source.mass_flow_rate >= 0.0 && source.wind_speed > 0.0 &&
           source.release_height >= 0.0 && source.sigma_y > 0.0 &&
           source.sigma_z > 0.0;
}

inline double gaussian_pdf(const double x, const double sigma)
{
    constexpr double pi = 3.141592653589793238462643383279502884;
    if (sigma <= 0.0) {
        return 0.0;
    }
    const double eta = x / sigma;
    return std::exp(-0.5 * eta * eta) / (std::sqrt(2.0 * pi) * sigma);
}

inline double ground_reflected_vertical_pdf(const double z,
                                            const double release_height,
                                            const double sigma_z)
{
    if (z < 0.0) {
        return 0.0;
    }
    return gaussian_pdf(z - release_height, sigma_z) +
           gaussian_pdf(z + release_height, sigma_z);
}

inline double concentration(const GaussianPlumeSource& source,
                            const double y,
                            const double z)
{
    if (!valid(source)) {
        return 0.0;
    }
    return (source.mass_flow_rate / source.wind_speed) *
           gaussian_pdf(y, source.sigma_y) *
           ground_reflected_vertical_pdf(z, source.release_height, source.sigma_z);
}

inline double centerline_concentration(const GaussianPlumeSource& source)
{
    return concentration(source, 0.0, source.release_height);
}

inline double crosswind_integrated_concentration(const GaussianPlumeSource& source,
                                                 const double z)
{
    if (!valid(source)) {
        return 0.0;
    }
    return (source.mass_flow_rate / source.wind_speed) *
           ground_reflected_vertical_pdf(z, source.release_height, source.sigma_z);
}

inline double ground_centerline_concentration(const GaussianPlumeSource& source)
{
    return concentration(source, 0.0, 0.0);
}

inline double centerline_threshold_distance_neutral(
    const double mass_flow_rate,
    const double wind_speed,
    const double threshold,
    const double sigma_y_slope,
    const double sigma_z_slope,
    const double min_distance = 0.0)
{
    constexpr double pi = 3.141592653589793238462643383279502884;
    if (mass_flow_rate <= 0.0 || wind_speed <= 0.0 || threshold <= 0.0 ||
        sigma_y_slope <= 0.0 || sigma_z_slope <= 0.0) {
        return 0.0;
    }

    const double distance = std::sqrt(
        mass_flow_rate / (2.0 * pi * wind_speed * sigma_y_slope *
                          sigma_z_slope * threshold));
    return std::max(distance, min_distance);
}

} // namespace MyPele::Engineering::Dispersion

#endif
