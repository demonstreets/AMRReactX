#include "AMR/Hierarchy.H"

#include "Numerics/ScalarTransport.H"

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

namespace {

void fill_refined_level_from_coarse(const amrex::MultiFab& coarse_state,
                                    amrex::MultiFab& fine_state,
                                    const amrex::Geometry& coarse_geom,
                                    int ref_ratio,
                                    bool fill_valid)
{
    amrex::BoxArray coarse_for_fine_ba = fine_state.boxArray();
    coarse_for_fine_ba.coarsen(ref_ratio);
    amrex::MultiFab coarse_for_fine(coarse_for_fine_ba,
                                    fine_state.DistributionMap(),
                                    coarse_state.nComp(),
                                    fine_state.nGrow());
    coarse_for_fine.ParallelCopy(coarse_state, 0, 0, coarse_state.nComp(),
                                 0, fine_state.nGrow(), coarse_geom.periodicity());

    const amrex::Box fine_domain = amrex::refine(coarse_geom.Domain(), ref_ratio);
    for (amrex::MFIter mfi(fine_state); mfi.isValid(); ++mfi) {
        const amrex::Box grown_box = amrex::grow(mfi.validbox(), fine_state.nGrow())
            & fine_domain;
        const amrex::Box valid_box = mfi.validbox();
        const auto valid_lo = valid_box.smallEnd();
        const auto valid_hi = valid_box.bigEnd();
        const amrex::Array4<amrex::Real> fine = fine_state.array(mfi);
        const amrex::Array4<const amrex::Real> coarse = coarse_for_fine.const_array(mfi);
        const int ncomp = fine_state.nComp();
        for (int comp = 0; comp < ncomp; ++comp) {
            amrex::ParallelFor(grown_box, [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
                const bool in_valid = i >= valid_lo[0] && i <= valid_hi[0]
                                   && j >= valid_lo[1] && j <= valid_hi[1]
                                   && k >= valid_lo[2] && k <= valid_hi[2];
                if (fill_valid || !in_valid) {
                    fine(i, j, k, comp) = coarse(i / ref_ratio,
                                                 j / ref_ratio,
                                                 k / ref_ratio,
                                                 comp);
                }
            });
        }
    }
}

void fill_refined_level_from_coarse_time_interpolated(
    const amrex::MultiFab& coarse_old_state,
    const amrex::MultiFab& coarse_new_state,
    amrex::MultiFab& fine_state,
    const amrex::Geometry& coarse_geom,
    int ref_ratio,
    amrex::Real alpha)
{
    amrex::BoxArray coarse_for_fine_ba = fine_state.boxArray();
    coarse_for_fine_ba.coarsen(ref_ratio);
    amrex::MultiFab coarse_old_for_fine(coarse_for_fine_ba,
                                        fine_state.DistributionMap(),
                                        coarse_old_state.nComp(),
                                        fine_state.nGrow());
    amrex::MultiFab coarse_new_for_fine(coarse_for_fine_ba,
                                        fine_state.DistributionMap(),
                                        coarse_new_state.nComp(),
                                        fine_state.nGrow());
    coarse_old_for_fine.ParallelCopy(coarse_old_state, 0, 0, coarse_old_state.nComp(),
                                     0, fine_state.nGrow(), coarse_geom.periodicity());
    coarse_new_for_fine.ParallelCopy(coarse_new_state, 0, 0, coarse_new_state.nComp(),
                                     0, fine_state.nGrow(), coarse_geom.periodicity());

    const amrex::Box fine_domain = amrex::refine(coarse_geom.Domain(), ref_ratio);
    const amrex::Real old_weight = 1.0 - alpha;
    for (amrex::MFIter mfi(fine_state); mfi.isValid(); ++mfi) {
        const amrex::Box grown_box = amrex::grow(mfi.validbox(), fine_state.nGrow())
            & fine_domain;
        const amrex::Box valid_box = mfi.validbox();
        const auto valid_lo = valid_box.smallEnd();
        const auto valid_hi = valid_box.bigEnd();
        const amrex::Array4<amrex::Real> fine = fine_state.array(mfi);
        const amrex::Array4<const amrex::Real> coarse_old =
            coarse_old_for_fine.const_array(mfi);
        const amrex::Array4<const amrex::Real> coarse_new =
            coarse_new_for_fine.const_array(mfi);
        const int ncomp = fine_state.nComp();
        for (int comp = 0; comp < ncomp; ++comp) {
            amrex::ParallelFor(grown_box, [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
                const bool in_valid = i >= valid_lo[0] && i <= valid_hi[0]
                                   && j >= valid_lo[1] && j <= valid_hi[1]
                                   && k >= valid_lo[2] && k <= valid_hi[2];
                if (!in_valid) {
                    const int ci = i / ref_ratio;
                    const int cj = j / ref_ratio;
                    const int ck = k / ref_ratio;
                    fine(i, j, k, comp) =
                        old_weight * coarse_old(ci, cj, ck, comp)
                        + alpha * coarse_new(ci, cj, ck, comp);
                }
            });
        }
    }
}

} // namespace

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
    fill_refined_level_from_coarse(coarse_state, fine_state, coarse_geom, ref_ratio, true);
}

void advance_scalar_amr_hierarchy(ScalarAmrHierarchy& hierarchy,
                                  const amrex::MultiFab& level0_old_state,
                                  const amrex::MultiFab& level0_new_state,
                                  const amrex::Geometry& level0_geom,
                                  const RuntimeParams& params)
{
    if (!hierarchy.has_level1()) {
        return;
    }

    const int nsubsteps = std::max(1, params.tag_ref_ratio);
    RuntimeParams fine_params = params;
    fine_params.dt = params.dt / static_cast<amrex::Real>(nsubsteps);

    amrex::MultiFab level1_next(hierarchy.level1_state->boxArray(),
                                hierarchy.level1_state->DistributionMap(),
                                hierarchy.level1_state->nComp(),
                                hierarchy.level1_state->nGrow());
    for (int substep = 0; substep < nsubsteps; ++substep) {
        const amrex::Real alpha =
            static_cast<amrex::Real>(substep) / static_cast<amrex::Real>(nsubsteps);
        fill_refined_level_from_coarse_time_interpolated(
            level0_old_state, level0_new_state, *hierarchy.level1_state,
            level0_geom, params.tag_ref_ratio, alpha);
        advance_scalar(*hierarchy.level1_state, level1_next,
                       hierarchy.level1_geom, fine_params);
        amrex::MultiFab::Copy(*hierarchy.level1_state, level1_next, 0, 0,
                              hierarchy.level1_state->nComp(), 0);
    }
}

AmrMassDiagnostics restrict_scalar_amr_hierarchy_to_coarse(
    const ScalarAmrHierarchy& hierarchy,
    amrex::MultiFab& level0_state,
    const amrex::Geometry& level0_geom,
    const RuntimeParams& params)
{
    if (!hierarchy.has_level1()) {
        return {};
    }

    const AmrMassDiagnostics mass_before =
        compute_amr_mass_diagnostics(level0_state, hierarchy, level0_geom, params);
    const int ref_ratio = params.tag_ref_ratio;
    amrex::BoxArray coarse_ba = hierarchy.level1_state->boxArray();
    coarse_ba.coarsen(ref_ratio);
    amrex::MultiFab restricted(coarse_ba,
                               hierarchy.level1_state->DistributionMap(),
                               level0_state.nComp(),
                               0);
    const amrex::Real inv_ratio_volume =
        1.0 / static_cast<amrex::Real>(AMREX_D_TERM(ref_ratio, * ref_ratio, * ref_ratio));

    for (amrex::MFIter mfi(restricted); mfi.isValid(); ++mfi) {
        const amrex::Box& cbx = mfi.validbox();
        const amrex::Array4<amrex::Real> coarse = restricted.array(mfi);
        const amrex::Array4<const amrex::Real> fine = hierarchy.level1_state->const_array(mfi);
        const int ncomp = restricted.nComp();
        for (int comp = 0; comp < ncomp; ++comp) {
            amrex::ParallelFor(cbx, [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
                amrex::Real average = 0.0;
                for (int kk = 0; kk < ref_ratio; ++kk) {
                    for (int jj = 0; jj < ref_ratio; ++jj) {
                        for (int ii = 0; ii < ref_ratio; ++ii) {
                            average += fine(ref_ratio * i + ii,
                                            ref_ratio * j + jj,
                                            ref_ratio * k + kk,
                                            comp);
                        }
                    }
                }
                coarse(i, j, k, comp) = average * inv_ratio_volume;
            });
        }
    }

    level0_state.ParallelCopy(restricted, 0, 0, level0_state.nComp(), 0, 0);
    return mass_before;
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

AmrMassDiagnostics compute_amr_mass_diagnostics(const amrex::MultiFab& level0_state,
                                                const ScalarAmrHierarchy& hierarchy,
                                                const amrex::Geometry& level0_geom,
                                                const RuntimeParams& params)
{
    AmrMassDiagnostics out;
    if (!hierarchy.has_level1()) {
        return out;
    }

    const int ref_ratio = params.tag_ref_ratio;
    const auto fine_dx = hierarchy.level1_geom.CellSizeArray();
    const amrex::Real fine_cell_volume =
        AMREX_D_TERM(fine_dx[0], * fine_dx[1], * fine_dx[2]);
    out.level1_mass =
        params.rho0 * hierarchy.level1_state->sum(YLeak) * fine_cell_volume;

    amrex::BoxArray coarse_ba = hierarchy.level1_state->boxArray();
    coarse_ba.coarsen(ref_ratio);
    amrex::MultiFab covered_level0(coarse_ba,
                                   hierarchy.level1_state->DistributionMap(),
                                   NumState,
                                   0);
    covered_level0.ParallelCopy(level0_state, 0, 0, NumState,
                                0, 0, level0_geom.periodicity());
    const auto coarse_dx = level0_geom.CellSizeArray();
    const amrex::Real coarse_cell_volume =
        AMREX_D_TERM(coarse_dx[0], * coarse_dx[1], * coarse_dx[2]);
    out.covered_level0_mass =
        params.rho0 * covered_level0.sum(YLeak) * coarse_cell_volume;
    out.mass_delta = out.level1_mass - out.covered_level0_mass;
    return out;
}

} // namespace amrreactx
