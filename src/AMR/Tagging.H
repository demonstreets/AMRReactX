#pragma once

#include "Core/State.H"

#include <AMReX_Geometry.H>
#include <AMReX_MultiFab.H>

namespace amrreactx {

struct AmrTaggingSummary {
    long long refine_cell_count = 0;
    long long cluster_count = 0;
    long long candidate_level1_cell_count = 0;
    amrex::Real candidate_level1_volume = 0.0;
};

struct CandidateLevel1Grids {
    amrex::BoxArray box_array;
    AmrTaggingSummary summary;
};

void fill_tagging_indicators(const amrex::MultiFab& state,
                             amrex::MultiFab& tags,
                             const amrex::Geometry& geom,
                             const RuntimeParams& params);

CandidateLevel1Grids make_candidate_level1_grids(const amrex::MultiFab& tags,
                                                 const amrex::Geometry& geom,
                                                 const RuntimeParams& params);

AmrTaggingSummary build_candidate_level1_grids(const amrex::MultiFab& tags,
                                               const amrex::Geometry& geom,
                                               const RuntimeParams& params);

} // namespace amrreactx
