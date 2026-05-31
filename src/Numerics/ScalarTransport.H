#pragma once

#include "Core/State.H"

#include <AMReX_Geometry.H>
#include <AMReX_MultiFab.H>

namespace amrreactx {

void initialize_state(amrex::MultiFab& state, const amrex::Geometry& geom, const RuntimeParams& params);

void advance_scalar(amrex::MultiFab& state,
                    amrex::MultiFab& next_state,
                    const amrex::Geometry& geom,
                    const RuntimeParams& params);

StabilityInfo compute_stability(const amrex::Geometry& geom, const RuntimeParams& params);
amrex::Real compute_dt(const amrex::Geometry& geom, const RuntimeParams& params, amrex::Real time);

} // namespace amrreactx
