#include <AMReX.H>

#include <signed_distance.H>

#include <AMReX_Print.H>
#include <AMReX_MultiFab.H>
#include <AMReX_Geometry.H>
#include <AMReX_RealBox.H>
#include <AMReX_BoxArray.H>
#include <AMReX_DistributionMapping.H>

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

    // Domain: [0,2]^3, 32^3 cells.
    Box domain(IntVect(0,0,0), IntVect(31,31,31));
    RealBox probBox({0.0, 0.0, 0.0}, {2.0, 2.0, 2.0});
    Array<int,AMREX_SPACEDIM> is_periodic{0,0,0};
    Geometry geom;
    geom.define(domain, probBox, 0, is_periodic);  // 0 = Cartesian

    BoxArray ba(domain);
    DistributionMapping dm(ba);
    IntVect ng(2);

    MultiFab sdf(ba, dm, 1, ng);

    // Sphere at (1,1,1) with radius 0.5.
    Array<Real,3> center{1.0, 1.0, 1.0};
    Real radius = 0.5;

    pele::computeSphereSDF(sdf, geom, center, radius, ng);

    Real dx = 2.0/32.0;

    // Check at corner cell (0,0,0)
    {
        // Cell center at (dx/2, dx/2, dx/2) = (0.03125, ...)
        // SDF = sqrt(3*(1-0.03125)^2) - 0.5 = sqrt(3)*0.96875 - 0.5
        Real h = dx/2.0;
        Real expected = std::sqrt((1.0-h)*(1.0-h)*3.0) - radius;
        // Access via MFIter
        for (MFIter mfi(sdf); mfi.isValid(); ++mfi) {
            const Box& bx = mfi.validbox();
            if (bx.contains(IntVect(0,0,0))) {
                auto const& arr = sdf.const_array(mfi);
                nfail += check(std::abs(arr(0,0,0) - expected) < 1e-10,
                               "corner cell SDF");
                break;
            }
        }
    }

    // Min/Max checks
    Real min_val = sdf.min(0);
    nfail += check(min_val < -0.4, "min SDF negative (inside sphere)");
    nfail += check(min_val > -0.6, "min SDF > -0.6");

    Real max_val = sdf.max(0);
    nfail += check(max_val > 0.5, "max SDF positive (outside sphere)");

    // L2 error vs analytic
    {
        Real l2_err = 0.0;
        long count = 0;
        for (MFIter mfi(sdf); mfi.isValid(); ++mfi) {
            const Box& bx = mfi.validbox();
            auto const& arr = sdf.const_array(mfi);
            amrex::Loop(bx, [&](int i, int j, int k) {
                Real x = (i + 0.5) * dx;
                Real y = (j + 0.5) * dx;
                Real z = (k + 0.5) * dx;
                Real analytic = std::sqrt((x-1.0)*(x-1.0)+(y-1.0)*(y-1.0)+(z-1.0)*(z-1.0)) - radius;
                l2_err += (arr(i,j,k) - analytic) * (arr(i,j,k) - analytic);
                ++count;
            });
        }
        l2_err = std::sqrt(l2_err / count);
        nfail += check(l2_err < 1e-14, "L2 error vs analytic < 1e-14");
        amrex::Print() << "  L2 error: " << l2_err << "\n";
    }

    amrex::Print() << "\n=== " << (nfail ? "FAILED" : "ALL PASSED") << " ===\n";
    amrex::Finalize();
    return nfail ? 1 : 0;
}
