#pragma once

#include "Core/State.H"

#include <AMReX_Geometry.H>
#include <AMReX_GpuQualifiers.H>
#include <AMReX_MultiFab.H>
#include <AMReX_REAL.H>

namespace amrreactx {

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real scalar_advective_flux(amrex::Real left_y,
                                  amrex::Real right_y,
                                  amrex::Real velocity) noexcept
{
    return velocity >= 0.0 ? velocity * left_y : velocity * right_y;
}

void initialize_state(amrex::MultiFab& state, const amrex::Geometry& geom, const RuntimeParams& params);

void advance_scalar(amrex::MultiFab& state,
                    amrex::MultiFab& next_state,
                    const amrex::Geometry& geom,
                    const RuntimeParams& params);

StabilityInfo compute_stability(const amrex::Geometry& geom, const RuntimeParams& params);
amrex::Real compute_dt(const amrex::Geometry& geom, const RuntimeParams& params, amrex::Real time);

} // namespace amrreactx
