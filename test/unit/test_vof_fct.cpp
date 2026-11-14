#include "VOF_FCT.H"

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


void fill_periodic_ghosts(amrex::Array4<amrex::Real>& q, int nx, int ng)
{
    for (int i = -ng; i < 0; ++i) {
        const int src = ((i % nx) + nx) % nx;
        q(i, 0, 0, QFA) = q(src, 0, 0, QFA);
    }
    for (int i = nx; i < nx + ng; ++i) {
        const int src = i % nx;
        q(i, 0, 0, QFA) = q(src, 0, 0, QFA);
    }
}

double alpha_mass(const amrex::Array4<const amrex::Real>& q, int nx)
{
    double mass = 0.0;
    for (int i = 0; i < nx; ++i) {
        mass += q(i, 0, 0, QFA);
    }
    return mass;
}

void require_periodic_shift_contract()
{
    using amrex::Array4;
    using amrex::Box;
    using amrex::IntVect;
    using amrex::Real;

    constexpr int nx = 16;
    constexpr int ng = 2;
    const Box box(IntVect(-ng, 0), IntVect(nx + ng - 1, 0));
    std::vector<Real> old_storage((nx + 2 * ng) * QVAR, 0.0);
    std::vector<Real> new_storage((nx + 2 * ng) * QVAR, 0.0);
    Array4<Real> old_q(old_storage.data(), box, QVAR);
    Array4<Real> new_q(new_storage.data(), box, QVAR);
    Array4<const Real> cold_q(old_q);

    for (int i = 0; i < nx; ++i) {
        old_q(i, 0, 0, QFA) = (i >= 4 && i < 8) ? 1.0 : 0.0;
    }
    fill_periodic_ghosts(old_q, nx, ng);

    const double initial_mass = alpha_mass(cold_q, nx);
    require_near(initial_mass, 4.0, 1.0e-14,
                 "periodic top-hat initial alpha mass");

    amrex::GpuArray<Real, AMREX_SPACEDIM> dx{1.0, 1.0};
    constexpr Real dt = 1.0;
    Real flux[nx + 1] = {0.0};
    for (int face = 0; face <= nx; ++face) {
        const Real alphaL = old_q(face - 1, 0, 0, QFA);
        const Real alphaR = old_q(face, 0, 0, QFA);
        flux[face] = vof_fct_flux(1.0, 1.0,
                                  alphaL, alphaR, alphaL, alphaR,
                                  face, 0, 0, 0, cold_q, dx, dt);
    }

    for (int i = 0; i < nx; ++i) {
        new_q(i, 0, 0, QFA) = old_q(i, 0, 0, QFA) - (dt / dx[0]) * (flux[i + 1] - flux[i]);
        require(new_q(i, 0, 0, QFA) >= -1.0e-14 &&
                    new_q(i, 0, 0, QFA) <= 1.0 + 1.0e-14,
                "periodic one-step VOF update remains bounded");
        const int shifted_from = (i - 1 + nx) % nx;
        require_near(new_q(i, 0, 0, QFA), old_q(shifted_from, 0, 0, QFA),
                     1.0e-14, "CFL=1 periodic top-hat shifts exactly one cell");
    }
    Array4<const Real> cnew_q(new_q);
    require_near(alpha_mass(cnew_q, nx), initial_mass, 1.0e-14,
                 "periodic one-step VOF update conserves alpha mass");
}

} // namespace

int main()
{
    using amrex::Array4;
    using amrex::Box;
    using amrex::IntVect;
    using amrex::Real;

    static_assert(AMREX_SPACEDIM == 2, "This smoke exercises the 2D VOF path");
    static_assert(NUM_ADV == 1, "VOF alpha requires one advected scalar");

    const Box box(IntVect(0, 0), IntVect(4, 4));
    constexpr int nx = 5;
    constexpr int ny = 5;
    constexpr int nz = 1;
    std::vector<Real> q_storage(nx * ny * nz * QVAR, 0.0);
    Array4<Real> q(q_storage.data(), box, QVAR);
    Array4<const Real> cq(q);

    for (int j = 0; j <= 4; ++j) {
        for (int i = 0; i <= 4; ++i) {
            q(i, j, 0, QFA) = 0.5;
        }
    }

    Real nxn = -1.0;
    Real nyn = -1.0;
    Real nzn = -1.0;
    vof_youngs_normal(2, 2, 0, cq, nxn, nyn, nzn, QFA);
    require_near(nxn, 0.0, 1.0e-14, "constant alpha has zero x-normal");
    require_near(nyn, 0.0, 1.0e-14, "constant alpha has zero y-normal");
    require_near(nzn, 0.0, 1.0e-14, "2D constant alpha has zero z-normal");

    Real fx = 1.0;
    Real fy = 1.0;
    Real fz = 1.0;
    amrex::GpuArray<Real, AMREX_SPACEDIM> dx{1.0, 1.0};
    vof_mules_body_force(2, 2, 0, cq, dx, fx, fy, fz, QFA);
    require_near(fx, 0.0, 1.0e-14, "constant alpha has zero compression x-force");
    require_near(fy, 0.0, 1.0e-14, "constant alpha has zero compression y-force");
    require_near(fz, 0.0, 1.0e-14, "2D constant alpha has zero compression z-force");

    for (int j = 0; j <= 4; ++j) {
        for (int i = 0; i <= 4; ++i) {
            q(i, j, 0, QFA) = 0.5;
        }
    }
    q(1, 2, 0, QFA) = 0.0;
    q(2, 2, 0, QFA) = 0.5;
    q(3, 2, 0, QFA) = 1.0;

    vof_youngs_normal(2, 2, 0, cq, nxn, nyn, nzn, QFA);
    require_near(nxn, 1.0, 1.0e-14, "linear alpha has unit x-normal");
    require_near(nyn, 0.0, 1.0e-14, "linear alpha has zero y-normal");
    require_near(nzn, 0.0, 1.0e-14, "2D linear alpha has zero z-normal");

    fx = fy = fz = 0.0;
    vof_mules_body_force(2, 2, 0, cq, dx, fx, fy, fz, QFA);
    require_near(fx, 0.125, 1.0e-14,
                 "compression force magnitude is |grad alpha| alpha(1-alpha) along normal");
    require_near(fy, 0.0, 1.0e-14, "compression y-force is zero for x-only interface");
    require_near(fz, 0.0, 1.0e-14, "2D compression z-force is zero");

    q(0, 2, 0, QFA) = 0.0;
    q(1, 2, 0, QFA) = 0.2;
    q(2, 2, 0, QFA) = 0.4;
    q(3, 2, 0, QFA) = 0.8;
    q(4, 2, 0, QFA) = 1.0;

    const Real limited_pos = vof_zalesak_limiter(2, 2, 0, 0, cq,
                                                0.2, 1.2, dx, 0.1);
    require(limited_pos >= 0.2 - 1.0e-14 && limited_pos <= 1.2 + 1.0e-14,
            "positive antidiffusive flux stays between low and high fluxes");
    require_near(limited_pos, 1.2, 1.0e-14,
                 "positive limiter keeps high flux when local stencil allows it");

    const Real limited_pos_restricted = vof_zalesak_limiter(2, 2, 0, 0, cq,
                                                           0.2, 1.2, dx, 10.0);
    require(limited_pos_restricted > 0.2 && limited_pos_restricted < limited_pos,
            "positive limiter reduces antidiffusive flux for large dt/dx");

    const Real limited_neg = vof_zalesak_limiter(2, 2, 0, 0, cq,
                                                1.2, 0.2, dx, 0.1);
    require(limited_neg >= 0.2 - 1.0e-14 && limited_neg <= 1.2 + 1.0e-14,
            "negative antidiffusive flux stays between low and high fluxes");

    const Real flux = vof_fct_flux(1.0, 2.0, 0.9, 0.1, 0.4, 0.8,
                                   2, 2, 0, 0, cq, dx, 0.1);
    require(flux >= 2.0 * 0.4 - 1.0e-14 && flux <= 2.0 * 0.9 + 1.0e-14,
            "FCT upwind flux is bounded by low/high candidate fluxes");

    require_periodic_shift_contract();

    return 0;
}
