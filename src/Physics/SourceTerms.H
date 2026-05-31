#pragma once

#include "Core/State.H"

#include <AMReX_GpuQualifiers.H>
#include <AMReX_REAL.H>

#include <cmath>
#include <string>

namespace amrreactx {

int parse_source_type(const std::string& name);
std::string source_type_name(int source_type);

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real scalar_source(amrex::Real x,
                          amrex::Real y,
                          amrex::Real z,
                          const KernelParams& params) noexcept
{
    if (params.source_strength == 0.0) {
        return 0.0;
    }

    if (params.source_type == SourceBox) {
        const bool inside = x >= params.source_box_lo[0] && x <= params.source_box_hi[0]
                         && y >= params.source_box_lo[1] && y <= params.source_box_hi[1]
                         && z >= params.source_box_lo[2] && z <= params.source_box_hi[2];
        return inside ? params.source_strength : 0.0;
    }

    const amrex::Real r2 = (x - params.source_center[0]) * (x - params.source_center[0])
                         + (y - params.source_center[1]) * (y - params.source_center[1])
                         + (z - params.source_center[2]) * (z - params.source_center[2]);
    return params.source_strength
        * std::exp(-r2 / (2.0 * params.source_sigma * params.source_sigma));
}

} // namespace amrreactx
