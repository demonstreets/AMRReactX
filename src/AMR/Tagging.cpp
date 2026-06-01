#include "AMR/Tagging.H"

#include <AMReX_Array4.H>
#include <AMReX_Box.H>
#include <AMReX_BoxArray.H>
#include <AMReX_MFIter.H>
#include <AMReX_ParallelDescriptor.H>

#include <algorithm>
#include <cmath>
#include <limits>

namespace amrreactx {

void fill_tagging_indicators(const amrex::MultiFab& state,
                             amrex::MultiFab& tags,
                             const amrex::Geometry& geom,
                             const RuntimeParams& params)
{
    tags.setVal(0.0);
    if (params.tagging_enabled == 0) {
        return;
    }

    amrex::MultiFab state_with_ghosts(state.boxArray(), state.DistributionMap(), NumState, 1);
    amrex::MultiFab::Copy(state_with_ghosts, state, 0, 0, NumState, 0);
    state_with_ghosts.FillBoundary(geom.periodicity());

    const auto dx = geom.CellSizeArray();
    const auto prob_lo = geom.ProbLoArray();
    const auto dom_lo = geom.Domain().smallEnd();
    const auto dom_hi = geom.Domain().bigEnd();
    const amrex::Real grad_threshold = params.tag_grad_y;
    const int tag_source_region = params.tag_source_region;
    const int tag_porosity_interface = params.tag_porosity_interface;
    const amrex::Real porosity_threshold = params.tag_porosity_threshold;
    const int source_type = params.source_type;
    const amrex::Real source_x = params.source_center[0];
    const amrex::Real source_y = params.source_center[1];
    const amrex::Real source_z = params.source_center[2];
    const amrex::Real source_radius =
        params.tag_source_radius > 0.0 ? params.tag_source_radius : 3.0 * params.source_sigma;
    const amrex::Real source_radius2 = source_radius * source_radius;
    const amrex::Real source_box_buffer = params.tag_source_box_buffer;
    const amrex::Real box_lo_x = params.source_box_lo[0] - source_box_buffer;
    const amrex::Real box_lo_y = params.source_box_lo[1] - source_box_buffer;
    const amrex::Real box_lo_z = params.source_box_lo[2] - source_box_buffer;
    const amrex::Real box_hi_x = params.source_box_hi[0] + source_box_buffer;
    const amrex::Real box_hi_y = params.source_box_hi[1] + source_box_buffer;
    const amrex::Real box_hi_z = params.source_box_hi[2] + source_box_buffer;

    for (amrex::MFIter mfi(tags); mfi.isValid(); ++mfi) {
        const amrex::Box& bx = mfi.validbox();
        const amrex::Array4<const amrex::Real> s = state_with_ghosts.const_array(mfi);
        const amrex::Array4<amrex::Real> tag = tags.array(mfi);

        amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
            const amrex::Real yc = s(i, j, k, YLeak);
            const amrex::Real pc = s(i, j, k, Porosity);
            const amrex::Real ymx = (i == dom_lo[0]) ? yc : s(i - 1, j, k, YLeak);
            const amrex::Real ypx = (i == dom_hi[0]) ? yc : s(i + 1, j, k, YLeak);
            const amrex::Real ymy = (j == dom_lo[1]) ? yc : s(i, j - 1, k, YLeak);
            const amrex::Real ypy = (j == dom_hi[1]) ? yc : s(i, j + 1, k, YLeak);
            const amrex::Real ymz = (k == dom_lo[2]) ? yc : s(i, j, k - 1, YLeak);
            const amrex::Real ypz = (k == dom_hi[2]) ? yc : s(i, j, k + 1, YLeak);
            const amrex::Real pmx = (i == dom_lo[0]) ? pc : s(i - 1, j, k, Porosity);
            const amrex::Real ppx = (i == dom_hi[0]) ? pc : s(i + 1, j, k, Porosity);
            const amrex::Real pmy = (j == dom_lo[1]) ? pc : s(i, j - 1, k, Porosity);
            const amrex::Real ppy = (j == dom_hi[1]) ? pc : s(i, j + 1, k, Porosity);
            const amrex::Real pmz = (k == dom_lo[2]) ? pc : s(i, j, k - 1, Porosity);
            const amrex::Real ppz = (k == dom_hi[2]) ? pc : s(i, j, k + 1, Porosity);

            const amrex::Real gx = (ypx - ymx) / (2.0 * dx[0]);
            const amrex::Real gy = (ypy - ymy) / (2.0 * dx[1]);
            const amrex::Real gz = (ypz - ymz) / (2.0 * dx[2]);
            const amrex::Real grad_mag = std::sqrt(gx * gx + gy * gy + gz * gz);
            const amrex::Real grad_tag = grad_mag >= grad_threshold ? 1.0 : 0.0;

            const amrex::Real x = prob_lo[0] + (static_cast<amrex::Real>(i) + 0.5) * dx[0];
            const amrex::Real y = prob_lo[1] + (static_cast<amrex::Real>(j) + 0.5) * dx[1];
            const amrex::Real z = prob_lo[2] + (static_cast<amrex::Real>(k) + 0.5) * dx[2];
            amrex::Real source_tag = 0.0;
            if (tag_source_region != 0) {
                if (source_type == SourceBox) {
                    const bool inside_box = x >= box_lo_x && x <= box_hi_x
                                         && y >= box_lo_y && y <= box_hi_y
                                         && z >= box_lo_z && z <= box_hi_z;
                    source_tag = inside_box ? 1.0 : 0.0;
                } else {
                    const amrex::Real r2 = (x - source_x) * (x - source_x)
                                         + (y - source_y) * (y - source_y)
                                         + (z - source_z) * (z - source_z);
                    source_tag = r2 <= source_radius2 ? 1.0 : 0.0;
                }
            }

            amrex::Real porosity_tag = 0.0;
            if (tag_porosity_interface != 0) {
                amrex::Real porosity_jump = std::abs(pc - pmx);
                porosity_jump = std::max(porosity_jump, std::abs(pc - ppx));
                porosity_jump = std::max(porosity_jump, std::abs(pc - pmy));
                porosity_jump = std::max(porosity_jump, std::abs(pc - ppy));
                porosity_jump = std::max(porosity_jump, std::abs(pc - pmz));
                porosity_jump = std::max(porosity_jump, std::abs(pc - ppz));
                const bool transition_cell = pc > porosity_threshold
                                          && pc < 1.0 - porosity_threshold;
                porosity_tag = (porosity_jump >= porosity_threshold || transition_cell)
                    ? 1.0 : 0.0;
            }

            tag(i, j, k, GradYTag) = grad_tag;
            tag(i, j, k, SourceRegionTag) = source_tag;
            tag(i, j, k, PorosityInterfaceTag) = porosity_tag;
            tag(i, j, k, RefineTag) =
                (grad_tag > 0.0 || source_tag > 0.0 || porosity_tag > 0.0) ? 1.0 : 0.0;
        });
    }
}

CandidateLevel1Grids make_candidate_level1_grids(const amrex::MultiFab& tags,
                                                 const amrex::Geometry& geom,
                                                 const RuntimeParams& params)
{
    CandidateLevel1Grids candidate;
    if (params.tagging_enabled == 0) {
        return candidate;
    }

    const auto dom_lo = geom.Domain().smallEnd();
    const auto dom_hi = geom.Domain().bigEnd();
    int tagged_lo[AMREX_SPACEDIM] = {
        AMREX_D_DECL(std::numeric_limits<int>::max(),
                     std::numeric_limits<int>::max(),
                     std::numeric_limits<int>::max())
    };
    int tagged_hi[AMREX_SPACEDIM] = {
        AMREX_D_DECL(std::numeric_limits<int>::lowest(),
                     std::numeric_limits<int>::lowest(),
                     std::numeric_limits<int>::lowest())
    };
    amrex::Long local_tagged_count = 0;

    for (amrex::MFIter mfi(tags); mfi.isValid(); ++mfi) {
        const amrex::Box& bx = mfi.validbox();
        const amrex::Array4<const amrex::Real> tag = tags.const_array(mfi);
        const auto lo = bx.smallEnd();
        const auto hi = bx.bigEnd();
        for (int k = lo[2]; k <= hi[2]; ++k) {
            for (int j = lo[1]; j <= hi[1]; ++j) {
                for (int i = lo[0]; i <= hi[0]; ++i) {
                    if (tag(i, j, k, RefineTag) > 0.0) {
                        ++local_tagged_count;
                        tagged_lo[0] = std::min(tagged_lo[0], i);
                        tagged_lo[1] = std::min(tagged_lo[1], j);
                        tagged_lo[2] = std::min(tagged_lo[2], k);
                        tagged_hi[0] = std::max(tagged_hi[0], i);
                        tagged_hi[1] = std::max(tagged_hi[1], j);
                        tagged_hi[2] = std::max(tagged_hi[2], k);
                    }
                }
            }
        }
    }

    amrex::ParallelDescriptor::ReduceLongSum(local_tagged_count);
    amrex::ParallelDescriptor::ReduceIntMin(tagged_lo, AMREX_SPACEDIM);
    amrex::ParallelDescriptor::ReduceIntMax(tagged_hi, AMREX_SPACEDIM);
    candidate.summary.refine_cell_count = static_cast<long long>(local_tagged_count);
    if (candidate.summary.refine_cell_count == 0) {
        return candidate;
    }

    const amrex::IntVect candidate_lo(AMREX_D_DECL(
        std::max(dom_lo[0], tagged_lo[0] - params.tag_buffer),
        std::max(dom_lo[1], tagged_lo[1] - params.tag_buffer),
        std::max(dom_lo[2], tagged_lo[2] - params.tag_buffer)));
    const amrex::IntVect candidate_hi(AMREX_D_DECL(
        std::min(dom_hi[0], tagged_hi[0] + params.tag_buffer),
        std::min(dom_hi[1], tagged_hi[1] + params.tag_buffer),
        std::min(dom_hi[2], tagged_hi[2] + params.tag_buffer)));
    amrex::BoxArray candidate_level0(amrex::Box(candidate_lo, candidate_hi));
    if (params.tag_max_grid_size > 0) {
        candidate_level0.maxSize(params.tag_max_grid_size);
    }

    candidate.box_array = candidate_level0;
    candidate.box_array.refine(params.tag_ref_ratio);
    candidate.summary.cluster_count = static_cast<long long>(candidate.box_array.size());
    candidate.summary.candidate_level1_cell_count = static_cast<long long>(candidate.box_array.numPts());

    const auto dx = geom.CellSizeArray();
    const amrex::Real coarse_cell_volume = AMREX_D_TERM(dx[0], * dx[1], * dx[2]);
    const amrex::Real ratio_volume =
        std::pow(static_cast<amrex::Real>(params.tag_ref_ratio), AMREX_SPACEDIM);
    candidate.summary.candidate_level1_volume =
        static_cast<amrex::Real>(candidate.summary.candidate_level1_cell_count)
        * coarse_cell_volume / ratio_volume;
    return candidate;
}

AmrTaggingSummary build_candidate_level1_grids(const amrex::MultiFab& tags,
                                               const amrex::Geometry& geom,
                                               const RuntimeParams& params)
{
    return make_candidate_level1_grids(tags, geom, params).summary;
}

} // namespace amrreactx
