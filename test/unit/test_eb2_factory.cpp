#include <eb2_factory.H>

#include <AMReX.H>
#include <AMReX_Print.H>
#include <AMReX_MultiFab.H>
#include <AMReX_Geometry.H>
#include <AMReX_RealBox.H>
#include <AMReX_BoxArray.H>
#include <AMReX_DistributionMapping.H>
#include <AMReX_EB2.H>
#include <AMReX_EB2_Level.H>
#include <AMReX_EBCellFlag.H>

#include <cmath>

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
    int nfail = 0;

    // Small domain for quick test: [0,2]^3, 16^3 cells.
    Box domain(IntVect(0,0,0), IntVect(15,15,15));
    RealBox probBox({0.0, 0.0, 0.0}, {2.0, 2.0, 2.0});
    Array<int,AMREX_SPACEDIM> is_periodic{0,0,0};
    Geometry geom;
    geom.define(domain, probBox, 0, is_periodic);

    // Sphere of radius 0.5 at (1,1,1).
    amrex::Print() << "\n--- Building sphere EB ---\n";
    pele::buildSphereEB(0.5, {1.0, 1.0, 1.0}, geom);

    // Retrieve the EB IndexSpace and level.
    const EB2::IndexSpace& ebis = EB2::IndexSpace::top();
    const EB2::Level& level = ebis.getLevel(geom);

    // Check basic properties.
    nfail += check(level.isOK(), "EB level OK");

    // Get volume fraction.
    BoxArray ba(domain);
    DistributionMapping dm(ba);
    MultiFab vfrac(ba, dm, 1, 0);
    level.fillVolFrac(vfrac, geom);

    // A cell far from sphere should be fully fluid (vfrac = 1).
    // Cell (0,0,0): center at (dx/2, dx/2, dx/2) = (0.0625, ...)
    // Distance from (1,1,1) = sqrt(3*0.9375^2) ~ 1.62 > 0.5 => outside => vfrac = 1
    Real vfrac_corner = 0.0;
    for (MFIter mfi(vfrac); mfi.isValid(); ++mfi) {
        if (mfi.validbox().contains(IntVect(0,0,0))) {
            vfrac_corner = vfrac[mfi](IntVect(0,0,0));
            break;
        }
    }
    nfail += check(vfrac_corner > 0.99, "Corner cell is fluid (vfrac ~ 1)");
    amrex::Print() << "  vfrac at (0,0,0): " << vfrac_corner << "\n";

    // Cell near center is inside sphere = covered = vfrac 0.
    Real vfrac_center = 0.0;
    IntVect center_cell(8, 8, 8);  // nearest to (1,1,1)
    for (MFIter mfi(vfrac); mfi.isValid(); ++mfi) {
        if (mfi.validbox().contains(center_cell)) {
            vfrac_center = vfrac[mfi](center_cell);
            break;
        }
    }
    amrex::Print() << "  vfrac at center cell " << center_cell << ": "
                   << vfrac_center << "\n";

    // Get cell flags.
    FabArray<EBCellFlagFab> flags(ba, dm, 1, 0);
    level.fillEBCellFlag(flags, geom);

    // Check that some cells are cut (neither regular nor covered).
    int ncut = 0, nreg = 0, ncov = 0;
    for (MFIter mfi(flags); mfi.isValid(); ++mfi) {
        auto const& fab = flags[mfi];
        const Box& bx = mfi.validbox();
        amrex::Loop(bx, [&](int i, int j, int k) {
            auto flag = fab(IntVect(i,j,k));
            if (flag.isRegular()) ++nreg;
            else if (flag.isCovered()) ++ncov;
            else ++ncut;
        });
    }
    amrex::Print() << "  Cut: " << ncut << ", Regular: " << nreg
                   << ", Covered: " << ncov << "\n";
    nfail += check(ncut > 0, "Some cut cells exist");
    nfail += check(nreg > 0, "Some regular cells exist");

    // Total vfrac sum.
    Real total_vfrac = vfrac.sum(0);
    Real total_cells = static_cast<Real>(domain.numPts());
    amrex::Print() << "  Total vfrac sum: " << total_vfrac
                   << " (total cells: " << total_cells << ")\n";
    nfail += check(total_vfrac < total_cells,
                   "Total vfrac < total cells (sphere displaces some)");

    amrex::Print() << "\n=== " << (nfail ? "FAILED" : "ALL PASSED") << " ===\n";
    amrex::Finalize();
    return nfail ? 1 : 0;
}
