#include "CSF.H"

#include <AMReX_Array4.H>
#include <AMReX_Box.H>
#include <AMReX_REAL.H>

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

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

} // namespace

int main()
{
    using amrex::Array4;
    using amrex::Box;
    using amrex::IntVect;
    using amrex::Real;

    static_assert(AMREX_SPACEDIM == 2, "This smoke exercises the 2D CSF path");

    const Box box(IntVect(0, 0), IntVect(4, 4));
    constexpr int nx = 5;
    constexpr int ny = 5;
    constexpr int nz = 1;
    constexpr int ncomp = 1;
    std::vector<Real> alpha_storage(nx * ny * nz * ncomp, 0.0);
    Array4<Real> alpha(alpha_storage.data(), box, ncomp);
    Array4<const Real> const_alpha(alpha);

    for (int j = 0; j <= 4; ++j) {
        for (int i = 0; i <= 4; ++i) {
            alpha(i, j, 0, 0) = 0.25;
        }
    }

    amrex::GpuArray<Real, AMREX_SPACEDIM> dx{1.0, 1.0};
    Real nxn = -1.0;
    Real nyn = -1.0;
    Real nzn = -1.0;
    csf_normal_c0(2, 2, 0, const_alpha, nxn, nyn, nzn);
    require_near(nxn, 0.0, 1.0e-14, "constant alpha has zero x-normal");
    require_near(nyn, 0.0, 1.0e-14, "constant alpha has zero y-normal");
    require_near(nzn, 0.0, 1.0e-14, "2D constant alpha has zero z-normal");

    Real fx = 1.0;
    Real fy = 1.0;
    Real fz = 1.0;
    csf_force(2, 2, 0, const_alpha, dx, 0.072, fx, fy, fz);
    require_near(fx, 0.0, 1.0e-14, "constant alpha has zero x-force");
    require_near(fy, 0.0, 1.0e-14, "constant alpha has zero y-force");
    require_near(fz, 0.0, 1.0e-14, "2D constant alpha has zero z-force");

    for (int j = 0; j <= 4; ++j) {
        for (int i = 0; i <= 4; ++i) {
            alpha(i, j, 0, 0) = static_cast<Real>(i);
        }
    }

    csf_normal_c0(2, 2, 0, const_alpha, nxn, nyn, nzn);
    require_near(nxn, 1.0, 1.0e-14, "planar alpha has unit x-normal");
    require_near(nyn, 0.0, 1.0e-14, "planar alpha has zero y-normal");
    require_near(nzn, 0.0, 1.0e-14, "2D planar alpha has zero z-normal");

    fx = fy = fz = 123.0;
    csf_force(2, 2, 0, const_alpha, dx, 0.072, fx, fy, fz);
    require_near(fx, 0.0, 1.0e-14,
                 "planar interface has zero curvature and zero x-force");
    require_near(fy, 0.0, 1.0e-14,
                 "planar interface has zero curvature and zero y-force");
    require_near(fz, 0.0, 1.0e-14,
                 "2D planar interface has zero z-force without dx[2]");

    for (int j = 0; j <= 4; ++j) {
        for (int i = 0; i <= 4; ++i) {
            const Real x = static_cast<Real>(i) - 2.0;
            const Real y = static_cast<Real>(j) - 2.0;
            alpha(i, j, 0, 0) = x * x + y * y;
        }
    }

    csf_normal_c0(3, 2, 0, const_alpha, nxn, nyn, nzn);
    require(nxn > 0.99, "radial alpha normal points outward at +x side");
    require(std::abs(nyn) < 1.0e-14, "radial alpha normal has near-zero y at +x side");
    require_near(nzn, 0.0, 1.0e-14, "2D radial alpha has zero z-normal");

    const Box big_box(IntVect(0, 0), IntVect(20, 20));
    constexpr int big_nx = 21;
    constexpr int big_ny = 21;
    std::vector<Real> big_storage(big_nx * big_ny * nz * ncomp, 0.0);
    Array4<Real> big_alpha(big_storage.data(), big_box, ncomp);
    Array4<const Real> const_big_alpha(big_alpha);

    constexpr Real center = 10.0;
    constexpr Real radius = 8.0;
    for (int j = 0; j <= 20; ++j) {
        for (int i = 0; i <= 20; ++i) {
            const Real x = static_cast<Real>(i) - center;
            const Real y = static_cast<Real>(j) - center;
            big_alpha(i, j, 0, 0) = x * x + y * y;
        }
    }

    const Real kappa = csf_curvature_c0(18, 10, 0, const_big_alpha, dx);
    require_near(kappa, -1.0 / radius, 2.0e-3,
                 "2D circular alpha curvature follows CSF sign convention");

    const Real work = csf_force_work(
        2.0, -4.0, 99.0,
        5.0,
        10.0, 15.0, 123.0);
    require_near(work, -8.0, 1.0e-14,
                 "CSF source work is force dot velocity in 2D");

    return 0;
}
