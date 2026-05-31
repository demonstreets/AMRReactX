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

} // namespace amrreactx
