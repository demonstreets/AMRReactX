//! \file sphere_flow.cpp
//! Verification test: build a sphere embedded boundary and validate
//! the signed-distance field and volume fraction against analytic values.
//!
//! Expected: SDF L2 error < 1e-14 (analytic SDF on Cartesian grid);
//! volFrac integral consistent with known sphere volume.

#include <eb2_factory.H>
#include <signed_distance.H>
#include <bc_tags.H>

#include <AMReX.H>
#include <AMReX_Print.H>
#include <AMReX_MultiFab.H>
#include <AMReX_Geometry.H>
#include <AMReX_RealBox.H>
#include <AMReX_BoxArray.H>
#include <AMReX_DistributionMapping.H>
#include <AMReX_EB2.H>
#include <AMReX_EB2_Level.H>
#include <AMReX_iMultiFab.H>

#include <cmath>
#include <cstdlib>

using namespace amrex;

static int check(bool condition, const std::string& msg)
{
    if (!condition) {
        amrex::Print() << "  FAIL: " << msg << "\n";
        return 1;
    }
    amrex::Print() << "  PASS: " << msg << "\n";
    return 0;
}

int main(int argc, char* argv[])
{
    amrex::Initialize(argc, argv);

    // ---------- Configuration ----------
    // Domain: [0, 2]^3 with 64^3 cells → dx = 1/32
    const int n_cell = 64;
    Box domain(IntVect(0,0,0), IntVect(n_cell-1, n_cell-1, n_cell-1));
    RealBox probBox({0.0, 0.0, 0.0}, {2.0, 2.0, 2.0});
    Array<int,AMREX_SPACEDIM> is_periodic{0,0,0};
    Geometry geom;
    geom.define(domain, probBox, 0, is_periodic);

    const Real dx = 2.0 / n_cell;

    // Sphere: centre (1,1,1), radius 0.5
    constexpr Real radius = 0.5;
    const Array<Real,3> center{1.0, 1.0, 1.0};

    BoxArray ba(domain);
    DistributionMapping dm(ba);
    IntVect ng(2);

    int nfail = 0;

    // ========== 1. Sphere SDF verification ==========
    amrex::Print() << "\n=== 1. Sphere SDF verification ===\n";
    {
        MultiFab sdf(ba, dm, 1, ng);
        pele::computeSphereSDF(sdf, geom, center, radius, ng);

        // Compute L2 error vs analytic
        Real l2_err = 0.0;
        long count = 0;
        for (MFIter mfi(sdf); mfi.isValid(); ++mfi) {
            const Box& bx = mfi.growntilebox(ng);
            auto const& arr = sdf.const_array(mfi);
            amrex::Loop(bx, [&](int i, int j, int k) {
                Real x = (i + 0.5) * dx;
                Real y = (j + 0.5) * dx;
                Real z = (k + 0.5) * dx;
                Real analytic = std::sqrt((x-1.0)*(x-1.0)+(y-1.0)*(y-1.0)+(z-1.0)*(z-1.0)) - radius;
                Real diff = arr(i,j,k) - analytic;
                l2_err += diff * diff;
                ++count;
            });
        }
        l2_err = std::sqrt(l2_err / count);
        amrex::Print() << "  SDF L2 error: " << l2_err << "\n";
        nfail += check(l2_err < 1e-14, "SDF L2 error < 1e-14");
    }

    // ========== 2. EB2 Sphere build ==========
    amrex::Print() << "\n=== 2. EB2 sphere build ===\n";
    {
        pele::buildSphereEB(radius, center, geom);

        const EB2::Level& level = EB2::IndexSpace::top().getLevel(geom);
        nfail += check(level.isOK(), "EB level is OK");

        // Volume fraction
        MultiFab vfrac(ba, dm, 1, 0);
        level.fillVolFrac(vfrac, geom);

        // Total vfrac sum.
        Real total_vfrac = vfrac.sum(0);
        Real total_cells = static_cast<Real>(domain.numPts());
        Real fluid_cells_expected = total_cells - (4.0/3.0 * M_PI * radius*radius*radius) / (dx*dx*dx);
        amrex::Print() << "  Total vfrac sum: " << total_vfrac
                       << " expected ~ " << fluid_cells_expected << "\n";

        nfail += check(total_vfrac < total_cells, "vfrac sum < n_cells");
        nfail += check(std::abs(total_vfrac - fluid_cells_expected) / total_cells < 0.05,
                       "vfrac error < 5% (Gate Review criterion)");
    }

    // ========== 3. BC Tags ==========
    amrex::Print() << "\n=== 3. BC tags ===\n";
    {
        iMultiFab tags(ba, dm, 1, 0);
        pele::buildCellTags(tags, geom);

        int nfluid = 0, ncut = 0, ncovered = 0;
        for (MFIter mfi(tags); mfi.isValid(); ++mfi) {
            const Box& bx = mfi.validbox();
            auto const& arr = tags.const_array(mfi);
            amrex::Loop(bx, [&](int i, int j, int k) {
                int t = arr(i,j,k);
                if (t == static_cast<int>(pele::CellType::FLUID)) ++nfluid;
                else if (t == static_cast<int>(pele::CellType::CUT)) ++ncut;
                else if (t == static_cast<int>(pele::CellType::COVERED)) ++ncovered;
            });
        }
        amrex::Print() << "  FLUID: " << nfluid << " CUT: " << ncut
                       << " COVERED: " << ncovered << "\n";
        nfail += check(nfluid > 0, "FLUID cells exist");
        nfail += check(ncut > 0, "CUT cells exist");
        nfail += check(ncovered > 0, "COVERED cells exist");
        nfail += check(nfluid + ncut + ncovered == domain.numPts(),
                       "All cells tagged");
    }

    // ========== Summary ==========
    amrex::Print() << "\n========================================\n";
    if (nfail == 0) {
        amrex::Print() << "ALL VERIFICATION TESTS PASSED\n";
    } else {
        amrex::Print() << nfail << " TEST(S) FAILED\n";
    }
    amrex::Print() << "========================================\n";

    amrex::Finalize();
    return nfail ? 1 : 0;
}
