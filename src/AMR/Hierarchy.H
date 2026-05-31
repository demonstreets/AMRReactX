#pragma once

#include "AMR/Tagging.H"
#include "Core/State.H"

#include <AMReX_DistributionMapping.H>
#include <AMReX_Geometry.H>
#include <AMReX_MultiFab.H>

#include <memory>

namespace amrreactx {

struct ScalarAmrHierarchy {
    int finest_level = 0;
    amrex::Geometry level1_geom;
    amrex::BoxArray level1_box_array;
    amrex::DistributionMapping level1_distribution;
    std::unique_ptr<amrex::MultiFab> level1_state;
    AmrTaggingSummary tag_summary;

    bool has_level1() const noexcept { return finest_level >= 1 && level1_state != nullptr; }
};

amrex::Geometry make_refined_geometry(const amrex::Geometry& geom, int ref_ratio);

void initialize_refined_level_from_coarse(const amrex::MultiFab& coarse_state,
                                          amrex::MultiFab& fine_state,
                                          const amrex::Geometry& coarse_geom,
                                          int ref_ratio);

ScalarAmrHierarchy rebuild_scalar_amr_hierarchy(const amrex::MultiFab& level0_state,
                                                const amrex::Geometry& level0_geom,
                                                const RuntimeParams& params,
                                                int ncomp,
                                                int ngrow);

} // namespace amrreactx
