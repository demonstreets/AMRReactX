#include <bc_tags.H>
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

    // Small domain.
    Box domain(IntVect(0,0,0), IntVect(15,15,15));
    RealBox probBox({0.0, 0.0, 0.0}, {2.0, 2.0, 2.0});
    Array<int,AMREX_SPACEDIM> is_periodic{0,0,0};
    Geometry geom;
    geom.define(domain, probBox, 0, is_periodic);

    // Build sphere EB.
    pele::buildSphereEB(0.5, {1.0, 1.0, 1.0}, geom);

    // Allocate tags.
    BoxArray ba(domain);
    DistributionMapping dm(ba);
    iMultiFab cell_type(ba, dm, 1, 0);

    // Build cell tags.
    pele::buildCellTags(cell_type, geom);

    // Verify: corner cell (0,0,0) should be FLUID.
    {
        int corner_type = -1;
        for (MFIter mfi(cell_type); mfi.isValid(); ++mfi) {
            if (mfi.validbox().contains(IntVect(0,0,0))) {
                corner_type = cell_type[mfi](IntVect(0,0,0));
                break;
            }
        }
        nfail += check(corner_type == static_cast<int>(pele::CellType::FLUID),
                       "Corner cell is FLUID");
    }

    // Verify: center region should have CUT cells.
    {
        int nfluid = 0, ncut = 0, ncovered = 0;
        for (MFIter mfi(cell_type); mfi.isValid(); ++mfi) {
            const Box& bx = mfi.validbox();
            auto const& arr = cell_type.const_array(mfi);
            amrex::Loop(bx, [&](int i, int j, int k) {
                int t = arr(i,j,k);
                if (t == static_cast<int>(pele::CellType::FLUID)) ++nfluid;
                else if (t == static_cast<int>(pele::CellType::CUT)) ++ncut;
                else if (t == static_cast<int>(pele::CellType::COVERED)) ++ncovered;
            });
        }
        amrex::Print() << "  FLUID: " << nfluid << ", CUT: " << ncut
                       << ", COVERED: " << ncovered << "\n";
        nfail += check(nfluid > 0, "Some FLUID cells");
        nfail += check(ncut > 0, "Some CUT cells");
        nfail += check(ncovered > 0, "Some COVERED cells");
        nfail += check(nfluid + ncut + ncovered == domain.numPts(),
                       "All cells accounted for");
    }

    // Verify cellTypeName works.
    {
        nfail += check(pele::cellTypeName(pele::CellType::FLUID) == "FLUID",
                       "FLUID name");
        nfail += check(pele::cellTypeName(pele::CellType::CUT) == "CUT",
                       "CUT name");
        nfail += check(pele::cellTypeName(pele::CellType::COVERED) == "COVERED",
                       "COVERED name");
    }

    amrex::Print() << "\n=== " << (nfail ? "FAILED" : "ALL PASSED") << " ===\n";
    amrex::Finalize();
    return nfail ? 1 : 0;
}
