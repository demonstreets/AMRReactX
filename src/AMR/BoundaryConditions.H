#pragma once

#include "Core/State.H"

#include <AMReX_GpuQualifiers.H>
#include <AMReX_REAL.H>

#include <string>

namespace amrreactx {

int parse_boundary_type(const std::string& name);
std::string boundary_type_name(int bc);

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real boundary_y(amrex::Real interior_y, int bc, const KernelParams& params) noexcept
{
    if (bc == BcInlet) {
        return params.inlet_y;
    }
    return interior_y;
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real face_flux(amrex::Real interior_y,
                      amrex::Real exterior_y,
                      amrex::Real velocity,
                      int bc,
                      int side) noexcept
{
    if (bc == BcWall) {
        return 0.0;
    }
    if (side < 0) {
        return velocity >= 0.0 ? velocity * exterior_y : velocity * interior_y;
    }
    return velocity >= 0.0 ? velocity * interior_y : velocity * exterior_y;
}

} // namespace amrreactx
