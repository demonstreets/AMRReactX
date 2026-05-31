#include "AMR/Hierarchy.H"

#include <AMReX_Array4.H>
#include <AMReX_Box.H>
#include <AMReX_DistributionMapping.H>
#include <AMReX_MFIter.H>
#include <AMReX_RealBox.H>
#include <AMReX_Vector.H>

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

} // namespace amrreactx
