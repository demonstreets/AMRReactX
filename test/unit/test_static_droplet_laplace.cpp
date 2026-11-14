#include "StaticDropletLaplace.H"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>

namespace {

void require_near(double value, double expected, double tolerance,
                  const std::string& message)
{
    if (std::abs(value - expected) > tolerance) {
        std::cerr << "FAIL: " << message << ": got " << value
                  << ", expected " << expected << " +/- " << tolerance << "\n";
        std::exit(1);
    }
}

} // namespace

int main()
{
    constexpr amrex::Real sigma = 0.072;
    constexpr amrex::Real radius = 0.004;

    const auto ref2d = my_pele::twophase::make_static_droplet_laplace_reference(
        2, radius, sigma);
    require_near(ref2d.curvature, 250.0, 1.0e-12,
                 "2D droplet curvature is 1/R");
    require_near(ref2d.pressure_jump, 18.0, 1.0e-12,
                 "2D Laplace pressure jump is sigma/R");

    const auto ref3d = my_pele::twophase::make_static_droplet_laplace_reference(
        3, radius, sigma);
    require_near(ref3d.curvature, 500.0, 1.0e-12,
                 "3D droplet curvature is 2/R");
    require_near(ref3d.pressure_jump, 36.0, 1.0e-12,
                 "3D Laplace pressure jump is 2 sigma/R");

    require_near(my_pele::twophase::static_droplet_curvature(1, radius), 0.0,
                 1.0e-14, "unsupported dimension returns zero curvature");
    require_near(my_pele::twophase::static_droplet_curvature(2, 0.0), 0.0,
                 1.0e-14, "non-positive radius returns zero curvature");
    require_near(my_pele::twophase::static_droplet_laplace_pressure_jump(
                     2, radius, -sigma),
                 0.0, 1.0e-14,
                 "negative surface tension returns zero pressure jump");

    return 0;
}
