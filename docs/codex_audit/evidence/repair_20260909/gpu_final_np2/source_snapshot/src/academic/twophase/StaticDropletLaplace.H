#pragma once

#include <AMReX_Gpu.H>
#include <AMReX_REAL.H>

#include <cmath>

namespace my_pele::twophase {

struct StaticDropletLaplaceReference {
    amrex::Real curvature = 0.0;
    amrex::Real pressure_jump = 0.0;
};

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real static_droplet_curvature(int dim, amrex::Real radius)
{
    if ((dim != 2 && dim != 3) || !(radius > 0.0) || !std::isfinite(radius)) {
        return 0.0;
    }
    return static_cast<amrex::Real>(dim - 1) / radius;
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real static_droplet_laplace_pressure_jump(
    int dim,
    amrex::Real radius,
    amrex::Real sigma)
{
    if (!(sigma >= 0.0) || !std::isfinite(sigma)) {
        return 0.0;
    }
    return sigma * static_droplet_curvature(dim, radius);
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
StaticDropletLaplaceReference make_static_droplet_laplace_reference(
    int dim,
    amrex::Real radius,
    amrex::Real sigma)
{
    StaticDropletLaplaceReference ref;
    ref.curvature = static_droplet_curvature(dim, radius);
    ref.pressure_jump = static_droplet_laplace_pressure_jump(dim, radius, sigma);
    return ref;
}

} // namespace my_pele::twophase
