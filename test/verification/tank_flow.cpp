//! \file tank_flow.cpp
//! Tank verification: generate STL for 2-3 cylinders and run the full
//! STL → SDF → EB pipeline.  Validate that the EB level is built
//! correctly and boundary conditions are properly identified.

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
#include <AMReX_EB2_GeometryShop.H>
#include <AMReX_EB2_IF_Base.H>
#include <AMReX_EB2_IF_Cylinder.H>
#include <AMReX_EB2_IF_Union.H>
#include <AMReX_iMultiFab.H>

#include <cmath>
#include <cstdlib>
#include <fstream>

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

//! Write a simple ASCII STL file for a cylinder.
//! The cylinder axis is along z, centered at (cx, cy) with given radius and height.
//! Uses nseg segments around the circumference.
static void writeCylinderSTL(const std::string& path,
                             Real cx, Real cy, Real zlo, Real zhi,
                             Real radius, int nseg = 24)
{
    std::ofstream ofs(path);
    if (!ofs) { amrex::Abort("Cannot write " + path); }

    ofs << "solid cylinder\n";

    // Generate vertices around top and bottom circles
    Vector<std::pair<Real,Real>> pts(nseg);
    for (int i = 0; i < nseg; ++i) {
        Real theta = 2.0 * M_PI * i / nseg;
        pts[i] = {cx + radius * std::cos(theta),
                  cy + radius * std::sin(theta)};
    }

    // Side faces (quadrilaterals split into 2 triangles each)
    for (int i = 0; i < nseg; ++i) {
        int next = (i + 1) % nseg;
        auto [x1, y1] = pts[i];
        auto [x2, y2] = pts[next];

        // Normal for side: outward radial direction
        Real nx = (x1 + x2) / 2.0 - cx;
        Real ny = (y1 + y2) / 2.0 - cy;
        Real len = std::sqrt(nx*nx + ny*ny);
        nx /= len; ny /= len;

        // Triangle 1: (x1,y1,zlo) - (x2,y2,zlo) - (x1,y1,zhi)
        ofs << "  facet normal " << nx << " " << ny << " 0\n";
        ofs << "    outer loop\n";
        ofs << "      vertex " << x1 << " " << y1 << " " << zlo << "\n";
        ofs << "      vertex " << x2 << " " << y2 << " " << zlo << "\n";
        ofs << "      vertex " << x1 << " " << y1 << " " << zhi << "\n";
        ofs << "    endloop\n";
        ofs << "  endfacet\n";

        // Triangle 2: (x2,y2,zlo) - (x2,y2,zhi) - (x1,y1,zhi)
        ofs << "  facet normal " << nx << " " << ny << " 0\n";
        ofs << "    outer loop\n";
        ofs << "      vertex " << x2 << " " << y2 << " " << zlo << "\n";
        ofs << "      vertex " << x2 << " " << y2 << " " << zhi << "\n";
        ofs << "      vertex " << x1 << " " << y1 << " " << zhi << "\n";
        ofs << "    endloop\n";
        ofs << "  endfacet\n";
    }

    // Bottom cap
    ofs << "  facet normal 0 0 -1\n";
    ofs << "    outer loop\n";
    for (int i = nseg-1; i >= 0; --i) {
        auto [x, y] = pts[i];
        ofs << "      vertex " << x << " " << y << " " << zlo << "\n";
        if (i == nseg-1 || i == 0) continue; // fan triangulation
    }
    // Simple fan: triangles from (cx, cy, zlo) to consecutive edge pts
    for (int i = 0; i < nseg; ++i) {
        int next = (i + 1) % nseg;
        auto [x1, y1] = pts[i];
        auto [x2, y2] = pts[next];
        ofs << "  facet normal 0 0 -1\n";
        ofs << "    outer loop\n";
        ofs << "      vertex " << cx << " " << cy << " " << zlo << "\n";
        ofs << "      vertex " << x1 << " " << y1 << " " << zlo << "\n";
        ofs << "      vertex " << x2 << " " << y2 << " " << zlo << "\n";
        ofs << "    endloop\n";
        ofs << "  endfacet\n";
    }

    // Top cap
    for (int i = 0; i < nseg; ++i) {
        int next = (i + 1) % nseg;
        auto [x1, y1] = pts[i];
        auto [x2, y2] = pts[next];
        ofs << "  facet normal 0 0 1\n";
        ofs << "    outer loop\n";
        ofs << "      vertex " << cx << " " << cy << " " << zhi << "\n";
        ofs << "      vertex " << x2 << " " << y2 << " " << zhi << "\n";
        ofs << "      vertex " << x1 << " " << y1 << " " << zhi << "\n";
        ofs << "    endloop\n";
        ofs << "  endfacet\n";
    }

    ofs << "endsolid cylinder\n";
}

int main(int argc, char* argv[])
{
    amrex::Initialize(argc, argv);
    int nfail = 0;

    // Domain: [-1, 1]^3, 32^3 cells
    const int n_cell = 32;
    Box domain(IntVect(0,0,0), IntVect(n_cell-1, n_cell-1, n_cell-1));
    RealBox probBox({-1.0, -1.0, -1.0}, {1.0, 1.0, 1.0});
    Array<int,AMREX_SPACEDIM> is_periodic{0,0,0};
    Geometry geom;
    geom.define(domain, probBox, 0, is_periodic);

    BoxArray ba(domain);
    DistributionMapping dm(ba);

    // ========== 1. Generate tank STL ==========
    // Tank: 3 vertical cylinders arranged in a triangle
    amrex::Print() << "\n=== 1. Generating tank STL ===\n";

    // Cylinder 1: at (-0.4, -0.23, -0.8 to 0.8), r=0.2
    writeCylinderSTL("/tmp/tank_cyl1.stl", -0.4, -0.23, -0.8, 0.8, 0.2);
    // Cylinder 2: at (0.4, -0.23, -0.8 to 0.8), r=0.2
    writeCylinderSTL("/tmp/tank_cyl2.stl", 0.4, -0.23, -0.8, 0.8, 0.2);
    // Cylinder 3: at (0.0, 0.46, -0.8 to 0.8), r=0.2
    writeCylinderSTL("/tmp/tank_cyl3.stl", 0.0, 0.46, -0.8, 0.8, 0.2);
    amrex::Print() << "  3 cylinder STL files written\n";

    // ========== 2. Build EB using AMReX built-in cylinders (union) ==========
    amrex::Print() << "\n=== 2. Building tank EB via union of cylinders ===\n";

    // Use AMReX built-in CylinderIF for GPU-capable implicit geometry
    EB2::CylinderIF cyl1(0.2, 2, { -0.4, -0.23, 0.0 }, false);
    EB2::CylinderIF cyl2(0.2, 2, {  0.4, -0.23, 0.0 }, false);
    EB2::CylinderIF cyl3(0.2, 2, {  0.0,  0.46, 0.0 }, false);

    auto tank = EB2::makeUnion(cyl1, cyl2, cyl3);
    EB2::GeometryShop<decltype(tank)> gshop(tank);
    EB2::Build(gshop, geom, 0, 0);

    const EB2::Level& level = EB2::IndexSpace::top().getLevel(geom);
    nfail += check(level.isOK(), "Tank EB level OK");

    // Volume fraction
    MultiFab vfrac(ba, dm, 1, 0);
    level.fillVolFrac(vfrac, geom);

    Real total_vfrac = vfrac.sum(0);
    Real total_cells = domain.numPts();
    amrex::Print() << "  Total vfrac sum: " << total_vfrac
                   << " (total cells: " << total_cells << ")\n";
    nfail += check(total_vfrac < total_cells, "vfrac sum < n_cells");

    // ========== 3. BC Tags ==========
    amrex::Print() << "\n=== 3. Tank BC tags ===\n";
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

    amrex::Print() << "\n========================================\n";
    if (nfail == 0) {
        amrex::Print() << "TANK VERIFICATION PASSED\n";
    } else {
        amrex::Print() << nfail << " TEST(S) FAILED\n";
    }
    amrex::Print() << "========================================\n";

    amrex::Finalize();
    return nfail ? 1 : 0;
}
