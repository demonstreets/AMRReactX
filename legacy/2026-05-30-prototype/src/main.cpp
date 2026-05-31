#include <AMReX.H>
#include <AMReX_Array4.H>
#include <AMReX_BoxArray.H>
#include <AMReX_DistributionMapping.H>
#include <AMReX_Geometry.H>
#include <AMReX_MFIter.H>
#include <AMReX_Math.H>
#include <AMReX_MultiFab.H>
#include <AMReX_ParallelDescriptor.H>
#include <AMReX_ParmParse.H>
#include <AMReX_PlotFileUtil.H>
#include <AMReX_REAL.H>
#include <AMReX_RealBox.H>
#include <AMReX_Vector.H>

#include <cmath>
#include <string>

namespace {

enum StateIndex {
    Rho = 0,
    Uvel,
    Vvel,
    Wvel,
    YLeak,
    NumState
};

amrex::Geometry make_geometry()
{
    amrex::Vector<int> n_cell(AMREX_SPACEDIM, 32);
    amrex::Vector<amrex::Real> prob_lo(AMREX_SPACEDIM, 0.0);
    amrex::Vector<amrex::Real> prob_hi(AMREX_SPACEDIM, 1.0);

    amrex::ParmParse pp;
    pp.queryarr("n_cell", n_cell, 0, AMREX_SPACEDIM);
    pp.queryarr("prob_lo", prob_lo, 0, AMREX_SPACEDIM);
    pp.queryarr("prob_hi", prob_hi, 0, AMREX_SPACEDIM);

    const amrex::IntVect dom_lo(AMREX_D_DECL(0, 0, 0));
    const amrex::IntVect dom_hi(AMREX_D_DECL(n_cell[0] - 1,
                                             n_cell[1] - 1,
                                             n_cell[2] - 1));
    const amrex::Box domain(dom_lo, dom_hi);
    const amrex::RealBox real_box(prob_lo.data(), prob_hi.data());
    const int coord_sys = 0;
    amrex::Vector<int> is_periodic(AMREX_SPACEDIM, 0);

    return amrex::Geometry(domain, &real_box, coord_sys, is_periodic.data());
}

void initialize_leak_cloud(amrex::MultiFab& state, const amrex::Geometry& geom)
{
    const auto dx = geom.CellSizeArray();
    const auto prob_lo = geom.ProbLoArray();
    const auto prob_hi = geom.ProbHiArray();

    const amrex::Real xc = prob_lo[0] + 0.25 * (prob_hi[0] - prob_lo[0]);
    const amrex::Real yc = 0.5 * (prob_lo[1] + prob_hi[1]);
    const amrex::Real zc = 0.5 * (prob_lo[2] + prob_hi[2]);
    const amrex::Real sigma = 0.08 * (prob_hi[0] - prob_lo[0]);

    for (amrex::MFIter mfi(state); mfi.isValid(); ++mfi) {
        const amrex::Box& bx = mfi.validbox();
        const amrex::Array4<amrex::Real> arr = state.array(mfi);

        amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
            const amrex::Real x = prob_lo[0] + (static_cast<amrex::Real>(i) + 0.5) * dx[0];
            const amrex::Real y = prob_lo[1] + (static_cast<amrex::Real>(j) + 0.5) * dx[1];
            const amrex::Real z = prob_lo[2] + (static_cast<amrex::Real>(k) + 0.5) * dx[2];

            const amrex::Real r2 = (x - xc) * (x - xc)
                                 + (y - yc) * (y - yc)
                                 + (z - zc) * (z - zc);
            const amrex::Real cloud = std::exp(-r2 / (2.0 * sigma * sigma));

            arr(i, j, k, Rho) = 1.0 + 0.20 * cloud;
            arr(i, j, k, Uvel) = 1.0;
            arr(i, j, k, Vvel) = 0.05 * cloud;
            arr(i, j, k, Wvel) = 0.0;
            arr(i, j, k, YLeak) = cloud;
        });
    }
}

} // namespace

int main(int argc, char* argv[])
{
    amrex::Initialize(argc, argv);
    {
        const amrex::Geometry geom = make_geometry();

        int max_grid_size = 32;
        std::string plotfile = "plt_mini_leak";
        amrex::ParmParse pp;
        pp.query("max_grid_size", max_grid_size);
        pp.query("plotfile", plotfile);

        amrex::BoxArray ba(geom.Domain());
        ba.maxSize(max_grid_size);
        const amrex::DistributionMapping dm(ba);

        amrex::MultiFab state(ba, dm, NumState, 0);
        initialize_leak_cloud(state, geom);

        const amrex::Vector<std::string> var_names{
            "rho", "u", "v", "w", "Y_leak"
        };

        amrex::WriteSingleLevelPlotfile(plotfile, state, var_names, geom, 0.0, 0);

        amrex::Print() << "AMRReactX mini plotfile written to " << plotfile << "\n";
        amrex::Print() << "MPI ranks: " << amrex::ParallelDescriptor::NProcs() << "\n";
    }
    amrex::Finalize();
}
