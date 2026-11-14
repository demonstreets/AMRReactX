#include "gaussian_plume.H"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>

namespace {

void require(bool condition, const std::string& message)
{
    if (!condition) {
        std::cerr << "FAIL: " << message << "\n";
        std::exit(1);
    }
}

void require_near(double value, double expected, double tolerance,
                  const std::string& message)
{
    if (std::abs(value - expected) > tolerance) {
        std::cerr << "FAIL: " << message << ": got " << value
                  << ", expected " << expected << " +/- " << tolerance << "\n";
        std::exit(1);
    }
}

template <typename Func>
double integrate_midpoint(Func&& f, double lo, double hi, int n)
{
    const double dx = (hi - lo) / static_cast<double>(n);
    double sum = 0.0;
    for (int i = 0; i < n; ++i) {
        sum += f(lo + (static_cast<double>(i) + 0.5) * dx);
    }
    return sum * dx;
}

} // namespace

int main()
{
    namespace Plume = MyPele::Engineering::Dispersion;

    Plume::GaussianPlumeSource source;
    source.mass_flow_rate = 0.104;
    source.wind_speed = 2.0;
    source.release_height = 1.25;
    source.sigma_y = 0.8;
    source.sigma_z = 0.45;

    require(Plume::valid(source), "valid H2 plume source parameters are accepted");
    require_near(Plume::gaussian_pdf(0.0, source.sigma_y),
                 1.0 / (std::sqrt(2.0 * 3.14159265358979323846) * source.sigma_y),
                 1.0e-14,
                 "Gaussian PDF has the expected center value");

    const double center = Plume::centerline_concentration(source);
    require(center > Plume::concentration(source, source.sigma_y, source.release_height),
            "centerline concentration is larger than one-sigma crosswind value");
    require(Plume::ground_centerline_concentration(source) < center,
            "elevated release has lower ground centerline concentration than release height");

    const double y_extent = 8.0 * source.sigma_y;
    const double z_extent = source.release_height + 8.0 * source.sigma_z;
    const int ny = 1400;
    const int nz = 1400;
    const double cross_section = integrate_midpoint(
        [&](double z) {
            return integrate_midpoint(
                [&](double y) { return Plume::concentration(source, y, z); },
                -y_extent, y_extent, ny);
        },
        0.0, z_extent, nz);
    require_near(cross_section * source.wind_speed, source.mass_flow_rate,
                 source.mass_flow_rate * 2.0e-5,
                 "ground-reflected plume conserves injected mass flux across a far section");

    const double z_probe = source.release_height + 0.3;
    const double crosswind_integral = integrate_midpoint(
        [&](double y) { return Plume::concentration(source, y, z_probe); },
        -y_extent, y_extent, ny);
    require_near(crosswind_integral,
                 Plume::crosswind_integrated_concentration(source, z_probe),
                 crosswind_integral * 1.0e-12,
                 "crosswind integral matches analytic one-dimensional reduction");

    const double d1 = Plume::centerline_threshold_distance_neutral(
        source.mass_flow_rate, source.wind_speed, 1.0e-3, 0.12, 0.08);
    const double d2 = Plume::centerline_threshold_distance_neutral(
        source.mass_flow_rate, source.wind_speed, 2.5e-4, 0.12, 0.08);
    require_near(d2 / d1, 2.0, 1.0e-12,
                 "neutral-plume threshold distance follows inverse square-root concentration scaling");
    require_near(Plume::centerline_threshold_distance_neutral(
                     source.mass_flow_rate, source.wind_speed, 1.0, 0.12, 0.08, 20.0),
                 20.0, 1.0e-14,
                 "minimum report distance is enforced for near-field thresholds");

    Plume::GaussianPlumeSource invalid = source;
    invalid.wind_speed = 0.0;
    require(!Plume::valid(invalid), "zero wind speed is rejected");
    require_near(Plume::concentration(invalid, 0.0, 0.0), 0.0, 1.0e-14,
                 "invalid plume returns zero concentration");

    return 0;
}
