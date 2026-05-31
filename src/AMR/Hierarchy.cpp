#include "AMR/Hierarchy.H"

#include <AMReX_Array4.H>
#include <AMReX_Box.H>
#include <AMReX_DistributionMapping.H>
#include <AMReX_MFIter.H>
#include <AMReX_ParallelDescriptor.H>
#include <AMReX_RealBox.H>
#include <AMReX_Vector.H>

#include <algorithm>
#include <cmath>

namespace amrreactx {

amrex::Geometry make_refined_geometry(const amrex::Geometry& geom, int ref_ratio)
{
    const amrex::Box fine_domain = amrex::refine(geom.Domain(), ref_ratio);
    const amrex::RealBox real_box(geom.ProbLo(), geom.ProbHi());
    amrex::Vector<int> is_periodic(AMREX_SPACEDIM, 0);
    for (int d = 0; d < AMREX_SPACEDIM; ++d) {
        is_periodic[d] = geom.isPeriodic(d) ? 1 : 0;
    }
    return amrex::Geometry(fine_domain, &real_box, geom.Coord(), is_periodic.data());
}

void initialize_refined_level_from_coarse(const amrex::MultiFab& coarse_state,
                                          amrex::MultiFab& fine_state,
                                          const amrex::Geometry& coarse_geom,
                                          int ref_ratio)
{
    amrex::BoxArray coarse_for_fine_ba = fine_state.boxArray();
    coarse_for_fine_ba.coarsen(ref_ratio);
    amrex::MultiFab coarse_for_fine(coarse_for_fine_ba,
                                    fine_state.DistributionMap(),
                                    coarse_state.nComp(),
                                    0);
    coarse_for_fine.ParallelCopy(coarse_state, 0, 0, coarse_state.nComp(),
                                 0, 0, coarse_geom.periodicity());

    for (amrex::MFIter mfi(fine_state); mfi.isValid(); ++mfi) {
        const amrex::Box& bx = mfi.validbox();
        const amrex::Array4<amrex::Real> fine = fine_state.array(mfi);
        const amrex::Array4<const amrex::Real> coarse = coarse_for_fine.const_array(mfi);
        const int ncomp = fine_state.nComp();
        for (int comp = 0; comp < ncomp; ++comp) {
            amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
                fine(i, j, k, comp) = coarse(i / ref_ratio,
                                             j / ref_ratio,
                                             k / ref_ratio,
                                             comp);
            });
        }
    }
}

ScalarAmrHierarchy rebuild_scalar_amr_hierarchy(const amrex::MultiFab& level0_state,
                                                const amrex::Geometry& level0_geom,
                                                const RuntimeParams& params,
                                                int ncomp,
                                                int ngrow)
{
    ScalarAmrHierarchy hierarchy;
    if (params.tagging_enabled == 0) {
        return hierarchy;
    }

    amrex::MultiFab tags(level0_state.boxArray(), level0_state.DistributionMap(), NumTag, 0);
    fill_tagging_indicators(level0_state, tags, level0_geom, params);
    const CandidateLevel1Grids candidate = make_candidate_level1_grids(tags, level0_geom, params);
    hierarchy.tag_summary = candidate.summary;
    if (candidate.summary.cluster_count == 0) {
        return hierarchy;
    }

    hierarchy.finest_level = 1;
    hierarchy.level1_geom = make_refined_geometry(level0_geom, params.tag_ref_ratio);
    hierarchy.level1_box_array = candidate.box_array;
    hierarchy.level1_distribution = amrex::DistributionMapping(hierarchy.level1_box_array);
    hierarchy.level1_state = std::make_unique<amrex::MultiFab>(
        hierarchy.level1_box_array, hierarchy.level1_distribution, ncomp, ngrow);
    initialize_refined_level_from_coarse(level0_state, *hierarchy.level1_state,
                                         level0_geom, params.tag_ref_ratio);
    return hierarchy;
}

RestrictionDiagnostics compute_restriction_diagnostics(const amrex::MultiFab& level0_state,
                                                       const ScalarAmrHierarchy& hierarchy,
                                                       const amrex::Geometry& level0_geom,
                                                       int ref_ratio)
{
    RestrictionDiagnostics out;
    if (!hierarchy.has_level1()) {
        return out;
    }

    amrex::BoxArray coarse_ba = hierarchy.level1_state->boxArray();
    coarse_ba.coarsen(ref_ratio);
    amrex::MultiFab coarse_reference(coarse_ba,
                                     hierarchy.level1_state->DistributionMap(),
                                     NumState,
                                     0);
    coarse_reference.ParallelCopy(level0_state, 0, 0, NumState,
                                  0, 0, level0_geom.periodicity());

    amrex::Real local_max_error = 0.0;
    amrex::Real local_l1_error_sum = 0.0;
    amrex::Long local_count = 0;
    const amrex::Real inv_ratio_volume =
        1.0 / static_cast<amrex::Real>(AMREX_D_TERM(ref_ratio, * ref_ratio, * ref_ratio));

    for (amrex::MFIter mfi(coarse_reference); mfi.isValid(); ++mfi) {
        const amrex::Box& cbx = mfi.validbox();
        const amrex::Array4<const amrex::Real> coarse = coarse_reference.const_array(mfi);
        const amrex::Array4<const amrex::Real> fine = hierarchy.level1_state->const_array(mfi);
        const auto lo = cbx.smallEnd();
        const auto hi = cbx.bigEnd();
        for (int k = lo[2]; k <= hi[2]; ++k) {
            for (int j = lo[1]; j <= hi[1]; ++j) {
                for (int i = lo[0]; i <= hi[0]; ++i) {
                    amrex::Real restricted_y = 0.0;
                    for (int kk = 0; kk < ref_ratio; ++kk) {
                        for (int jj = 0; jj < ref_ratio; ++jj) {
                            for (int ii = 0; ii < ref_ratio; ++ii) {
                                restricted_y += fine(ref_ratio * i + ii,
                                                     ref_ratio * j + jj,
                                                     ref_ratio * k + kk,
                                                     YLeak);
                            }
                        }
                    }
                    restricted_y *= inv_ratio_volume;
                    const amrex::Real error = std::abs(restricted_y - coarse(i, j, k, YLeak));
                    local_max_error = std::max(local_max_error, error);
                    local_l1_error_sum += error;
                    ++local_count;
                }
            }
        }
    }

    amrex::ParallelDescriptor::ReduceRealMax(local_max_error);
    amrex::ParallelDescriptor::ReduceRealSum(local_l1_error_sum);
    amrex::ParallelDescriptor::ReduceLongSum(local_count);
    out.max_abs_y_error = local_max_error;
    out.coarse_cell_count = static_cast<long long>(local_count);
    if (local_count > 0) {
        out.l1_y_error = local_l1_error_sum / static_cast<amrex::Real>(local_count);
    }
    return out;
}

} // namespace amrreactx
