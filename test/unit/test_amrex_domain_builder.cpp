#include "domain_builder.H"

#include <AMReX.H>

#include <array>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
int g_failed = 0;

void check(const char* name, bool ok)
{
    std::cout << (ok ? "[PASS] " : "[FAIL] ") << name << '\n';
    if (!ok) ++g_failed;
}

bool near(double a, double b, double tol = 1.0e-12)
{
    return std::abs(a - b) <= tol;
}
} // namespace

int main(int argc, char** argv)
{
    amrex::Initialize(argc, argv);
    {
        pele::STLFacet f{};
        f.vertices[0][0] = 0.0; f.vertices[0][1] = 0.0; f.vertices[0][2] = 0.0;
        f.vertices[1][0] = 1.0; f.vertices[1][1] = 0.0; f.vertices[1][2] = 0.0;
        f.vertices[2][0] = 0.0; f.vertices[2][1] = 2.0; f.vertices[2][2] = 0.5;

        const auto domain = pele::makeMeshDomainFromFacets({f}, 0.125, 0.0, 0.125, 4);
        const auto mesh = pele::makeAmrexMeshDomain(domain, 3, 8);

        check("AMReX domain starts at zero index", mesh.domain_box.smallEnd(0) == 0 &&
              mesh.domain_box.smallEnd(1) == 0 && mesh.domain_box.smallEnd(2) == 0);
        check("AMReX domain cell counts match generated n_cell",
              mesh.domain_box.length(0) == domain.n_cell[0] &&
              mesh.domain_box.length(1) == domain.n_cell[1] &&
              mesh.domain_box.length(2) == domain.n_cell[2]);
        check("AMReX Geometry RealBox carries generated physical lower bounds",
              near(mesh.geometry.ProbLo(0), domain.prob_lo[0]) &&
              near(mesh.geometry.ProbLo(1), domain.prob_lo[1]) &&
              near(mesh.geometry.ProbLo(2), domain.prob_lo[2]));
        check("AMReX Geometry RealBox carries generated physical upper bounds",
              near(mesh.geometry.ProbHi(0), domain.prob_hi[0]) &&
              near(mesh.geometry.ProbHi(1), domain.prob_hi[1]) &&
              near(mesh.geometry.ProbHi(2), domain.prob_hi[2]));
        check("AMReX BoxArray covers generated domain", mesh.box_array.minimalBox() == mesh.domain_box);
        bool boxes_respect_max_grid_size = true;
        for (int ibox = 0; ibox < mesh.box_array.size(); ++ibox) {
            const auto& box = mesh.box_array[ibox];
            for (int d = 0; d < AMREX_SPACEDIM; ++d) {
                boxes_respect_max_grid_size = boxes_respect_max_grid_size && box.length(d) <= 8;
            }
        }
        check("AMReX BoxArray respects max grid size", boxes_respect_max_grid_size);

        bool threw = false;
        try {
            auto bad = domain;
            bad.n_cell[0] = 0;
            (void)pele::makeAmrexMeshDomain(bad, 3, 8);
        } catch (const std::invalid_argument&) {
            threw = true;
        }
        check("AMReX mesh rejects nonpositive cell counts", threw);
    }
    amrex::Finalize();
    return g_failed == 0 ? 0 : 1;
}
