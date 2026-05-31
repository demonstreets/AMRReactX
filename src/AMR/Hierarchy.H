#pragma once

#include <AMReX_Geometry.H>
#include <AMReX_MultiFab.H>

namespace amrreactx {

amrex::Geometry make_refined_geometry(const amrex::Geometry& geom, int ref_ratio);

void initialize_refined_level_from_coarse(const amrex::MultiFab& coarse_state,
                                          amrex::MultiFab& fine_state,
                                          const amrex::Geometry& coarse_geom,
                                          int ref_ratio);

} // namespace amrreactx
