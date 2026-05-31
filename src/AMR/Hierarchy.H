#pragma once

#include "AMR/Tagging.H"
#include "Core/State.H"

#include <AMReX_DistributionMapping.H>
#include <AMReX_Geometry.H>
#include <AMReX_MultiFab.H>
#include <AMReX_SPACE.H>

#include <cmath>
#include <memory>

namespace amrreactx {

struct RestrictionDiagnostics {
    amrex::Real max_abs_y_error = 0.0;
    amrex::Real l1_y_error = 0.0;
    long long coarse_cell_count = 0;
};

struct AmrMassDiagnostics {
    amrex::Real level1_mass = 0.0;
    amrex::Real covered_level0_mass = 0.0;
    amrex::Real mass_delta = 0.0;
};

struct CoarseFineFluxDiagnostics {
    amrex::Real advective_mismatch = 0.0;
    amrex::Real advective_abs_mismatch = 0.0;
    amrex::Real diffusive_mismatch = 0.0;
    amrex::Real diffusive_abs_mismatch = 0.0;
    long long interface_face_count = 0;
    amrex::Real advective_mismatch_by_face[2 * AMREX_SPACEDIM] = {};
    amrex::Real advective_abs_mismatch_by_face[2 * AMREX_SPACEDIM] = {};
    amrex::Real diffusive_mismatch_by_face[2 * AMREX_SPACEDIM] = {};
    amrex::Real diffusive_abs_mismatch_by_face[2 * AMREX_SPACEDIM] = {};
    long long interface_face_count_by_face[2 * AMREX_SPACEDIM] = {};
};

struct CoarseFineFluxRegister {
    amrex::Real advective_mismatch[2 * AMREX_SPACEDIM] = {};
    amrex::Real advective_abs_mismatch[2 * AMREX_SPACEDIM] = {};
    amrex::Real diffusive_mismatch[2 * AMREX_SPACEDIM] = {};
    amrex::Real diffusive_abs_mismatch[2 * AMREX_SPACEDIM] = {};
    long long interface_face_count[2 * AMREX_SPACEDIM] = {};

    static int face_index(int dir, int side) noexcept
    {
        return 2 * dir + (side > 0 ? 1 : 0);
    }

    void add(int dir, int side, amrex::Real advective, amrex::Real diffusive,
             long long face_count) noexcept
    {
        const int idx = face_index(dir, side);
        advective_mismatch[idx] += advective;
        advective_abs_mismatch[idx] += std::abs(advective);
        diffusive_mismatch[idx] += diffusive;
        diffusive_abs_mismatch[idx] += std::abs(diffusive);
        interface_face_count[idx] += face_count;
    }

    void reset() noexcept
    {
        for (int idx = 0; idx < 2 * AMREX_SPACEDIM; ++idx) {
            advective_mismatch[idx] = 0.0;
            advective_abs_mismatch[idx] = 0.0;
            diffusive_mismatch[idx] = 0.0;
            diffusive_abs_mismatch[idx] = 0.0;
            interface_face_count[idx] = 0;
        }
    }

    void add_register(const CoarseFineFluxRegister& other) noexcept
    {
        for (int idx = 0; idx < 2 * AMREX_SPACEDIM; ++idx) {
            advective_mismatch[idx] += other.advective_mismatch[idx];
            advective_abs_mismatch[idx] += other.advective_abs_mismatch[idx];
            diffusive_mismatch[idx] += other.diffusive_mismatch[idx];
            diffusive_abs_mismatch[idx] += other.diffusive_abs_mismatch[idx];
            interface_face_count[idx] += other.interface_face_count[idx];
        }
    }

    CoarseFineFluxDiagnostics totals() const noexcept
    {
        CoarseFineFluxDiagnostics out;
        for (int idx = 0; idx < 2 * AMREX_SPACEDIM; ++idx) {
            out.advective_mismatch += advective_mismatch[idx];
            out.advective_abs_mismatch += advective_abs_mismatch[idx];
            out.diffusive_mismatch += diffusive_mismatch[idx];
            out.diffusive_abs_mismatch += diffusive_abs_mismatch[idx];
            out.interface_face_count += interface_face_count[idx];
            out.advective_mismatch_by_face[idx] = advective_mismatch[idx];
            out.advective_abs_mismatch_by_face[idx] = advective_abs_mismatch[idx];
            out.diffusive_mismatch_by_face[idx] = diffusive_mismatch[idx];
            out.diffusive_abs_mismatch_by_face[idx] = diffusive_abs_mismatch[idx];
            out.interface_face_count_by_face[idx] = interface_face_count[idx];
        }
        return out;
    }
};

struct ScalarAmrHierarchy {
    int finest_level = 0;
    amrex::Geometry level1_geom;
    amrex::BoxArray level1_box_array;
    amrex::DistributionMapping level1_distribution;
    std::unique_ptr<amrex::MultiFab> level1_state;
    std::unique_ptr<amrex::MultiFab> level0_reflux_mass;
    AmrTaggingSummary tag_summary;
    CoarseFineFluxRegister last_step_flux_register;

    bool has_level1() const noexcept { return finest_level >= 1 && level1_state != nullptr; }
};

amrex::Geometry make_refined_geometry(const amrex::Geometry& geom, int ref_ratio);

void initialize_refined_level_from_coarse(const amrex::MultiFab& coarse_state,
                                          amrex::MultiFab& fine_state,
                                          const amrex::Geometry& coarse_geom,
                                          int ref_ratio);

void advance_scalar_amr_hierarchy(ScalarAmrHierarchy& hierarchy,
                                  const amrex::MultiFab& level0_old_state,
                                  const amrex::MultiFab& level0_new_state,
                                  const amrex::Geometry& level0_geom,
                                  const RuntimeParams& params);

AmrMassDiagnostics restrict_scalar_amr_hierarchy_to_coarse(
    const ScalarAmrHierarchy& hierarchy,
    amrex::MultiFab& level0_state,
    const amrex::Geometry& level0_geom,
    const RuntimeParams& params);

amrex::Real reflux_scalar_amr_hierarchy_to_coarse(
    const ScalarAmrHierarchy& hierarchy,
    amrex::MultiFab& level0_state,
    const amrex::Geometry& level0_geom,
    const RuntimeParams& params);

ScalarAmrHierarchy rebuild_scalar_amr_hierarchy(const amrex::MultiFab& level0_state,
                                                const amrex::Geometry& level0_geom,
                                                const RuntimeParams& params,
                                                int ncomp,
                                                int ngrow);

RestrictionDiagnostics compute_restriction_diagnostics(const amrex::MultiFab& level0_state,
                                                       const ScalarAmrHierarchy& hierarchy,
                                                       const amrex::Geometry& level0_geom,
                                                       int ref_ratio);

AmrMassDiagnostics compute_amr_mass_diagnostics(const amrex::MultiFab& level0_state,
                                                const ScalarAmrHierarchy& hierarchy,
                                                const amrex::Geometry& level0_geom,
                                                const RuntimeParams& params);

CoarseFineFluxDiagnostics compute_coarse_fine_flux_diagnostics(
    const amrex::MultiFab& level0_state,
    const ScalarAmrHierarchy& hierarchy,
    const amrex::Geometry& level0_geom,
    const RuntimeParams& params);

} // namespace amrreactx
