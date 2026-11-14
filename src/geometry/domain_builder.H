#ifndef PELE_DOMAIN_BUILDER_H
#define PELE_DOMAIN_BUILDER_H

#include "stl_parser.H"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <vector>

#if __has_include(<AMReX_Geometry.H>)
#define PELE_DOMAIN_BUILDER_HAVE_AMREX 1
#include <AMReX_Array.H>
#include <AMReX_Box.H>
#include <AMReX_BoxArray.H>
#include <AMReX_Geometry.H>
#include <AMReX_IntVect.H>
#include <AMReX_RealBox.H>
#endif

namespace pele {

struct Bounds3D {
    std::array<double, 3> lo{{0.0, 0.0, 0.0}};
    std::array<double, 3> hi{{0.0, 0.0, 0.0}};
    bool valid = false;
};

struct MeshDomain {
    std::array<double, 3> prob_lo{{0.0, 0.0, 0.0}};
    std::array<double, 3> prob_hi{{0.0, 0.0, 0.0}};
    std::array<int, 3> n_cell{{0, 0, 0}};
};

inline Bounds3D computeFacetBounds(const std::vector<STLFacet>& facets)
{
    Bounds3D bounds;
    if (facets.empty()) {
        return bounds;
    }

    bounds.lo = {{
        std::numeric_limits<double>::max(),
        std::numeric_limits<double>::max(),
        std::numeric_limits<double>::max()
    }};
    bounds.hi = {{
        std::numeric_limits<double>::lowest(),
        std::numeric_limits<double>::lowest(),
        std::numeric_limits<double>::lowest()
    }};

    for (const auto& facet : facets) {
        for (const auto& vertex : facet.vertices) {
            for (int d = 0; d < 3; ++d) {
                bounds.lo[d] = std::min(bounds.lo[d], vertex[d]);
                bounds.hi[d] = std::max(bounds.hi[d], vertex[d]);
            }
        }
    }

    bounds.valid = true;
    return bounds;
}

inline Bounds3D padBounds(const Bounds3D& bounds,
                          double relative_padding = 0.1,
                          double minimum_padding = 1.0e-6)
{
    if (!bounds.valid) {
        throw std::invalid_argument("cannot pad invalid geometry bounds");
    }
    if (relative_padding < 0.0 || minimum_padding < 0.0) {
        throw std::invalid_argument("geometry padding must be nonnegative");
    }

    Bounds3D padded;
    padded.valid = true;
    for (int d = 0; d < 3; ++d) {
        const double length = bounds.hi[d] - bounds.lo[d];
        const double scale = std::max(std::abs(bounds.lo[d]), std::abs(bounds.hi[d]));
        const double fallback = std::max(scale, 1.0);
        const double pad = std::max(minimum_padding,
                                    relative_padding * ((length > 0.0) ? length : fallback));
        padded.lo[d] = bounds.lo[d] - pad;
        padded.hi[d] = bounds.hi[d] + pad;
    }
    return padded;
}

inline int roundUpToMultiple(int value, int multiple)
{
    if (multiple <= 1) {
        return value;
    }
    return ((value + multiple - 1) / multiple) * multiple;
}

inline MeshDomain makeMeshDomain(const Bounds3D& padded_bounds,
                                 double target_cell_size,
                                 int blocking_factor = 8)
{
    if (!padded_bounds.valid) {
        throw std::invalid_argument("cannot build mesh domain from invalid bounds");
    }
    if (target_cell_size <= 0.0) {
        throw std::invalid_argument("target cell size must be positive");
    }
    if (blocking_factor <= 0) {
        throw std::invalid_argument("blocking factor must be positive");
    }

    MeshDomain domain;
    domain.prob_lo = padded_bounds.lo;
    domain.prob_hi = padded_bounds.hi;
    for (int d = 0; d < 3; ++d) {
        const double length = padded_bounds.hi[d] - padded_bounds.lo[d];
        if (length <= 0.0) {
            throw std::invalid_argument("padded domain must have positive extent");
        }
        const int raw_cells = static_cast<int>(std::ceil(length / target_cell_size));
        domain.n_cell[d] = roundUpToMultiple(std::max(raw_cells, 1), blocking_factor);
    }
    return domain;
}

inline MeshDomain makeMeshDomainFromFacets(const std::vector<STLFacet>& facets,
                                           double target_cell_size,
                                           double relative_padding = 0.1,
                                           double minimum_padding = 1.0e-6,
                                           int blocking_factor = 8)
{
    return makeMeshDomain(
        padBounds(computeFacetBounds(facets), relative_padding, minimum_padding),
        target_cell_size,
        blocking_factor);
}

#ifdef PELE_DOMAIN_BUILDER_HAVE_AMREX
struct AmrexMeshDomain {
    amrex::Box domain_box;
    amrex::RealBox real_box;
    amrex::Geometry geometry;
    amrex::BoxArray box_array;
};

inline amrex::Box makeAmrexDomainBox(const MeshDomain& domain, int dim)
{
    if (dim != 2 && dim != 3) {
        throw std::invalid_argument("AMReX domain dimension must be 2 or 3");
    }
    amrex::IntVect lo(AMREX_D_DECL(0, 0, 0));
    amrex::IntVect hi(AMREX_D_DECL(
        domain.n_cell[0] - 1,
        domain.n_cell[1] - 1,
        (dim == 3 ? domain.n_cell[2] - 1 : 0)));
    for (int d = 0; d < dim; ++d) {
        if (domain.n_cell[d] <= 0) {
            throw std::invalid_argument("AMReX domain cell counts must be positive");
        }
        if (!(domain.prob_hi[d] > domain.prob_lo[d])) {
            throw std::invalid_argument("AMReX domain physical extents must be positive");
        }
    }
    return amrex::Box(lo, hi);
}

inline amrex::RealBox makeAmrexRealBox(const MeshDomain& domain, int dim)
{
    if (dim != 2 && dim != 3) {
        throw std::invalid_argument("AMReX RealBox dimension must be 2 or 3");
    }
    amrex::GpuArray<amrex::Real, AMREX_SPACEDIM> lo{{AMREX_D_DECL(
        static_cast<amrex::Real>(domain.prob_lo[0]),
        static_cast<amrex::Real>(domain.prob_lo[1]),
        static_cast<amrex::Real>(dim == 3 ? domain.prob_lo[2] : 0.0))}};
    amrex::GpuArray<amrex::Real, AMREX_SPACEDIM> hi{{AMREX_D_DECL(
        static_cast<amrex::Real>(domain.prob_hi[0]),
        static_cast<amrex::Real>(domain.prob_hi[1]),
        static_cast<amrex::Real>(dim == 3 ? domain.prob_hi[2] : 1.0))}};
    return amrex::RealBox(lo.data(), hi.data());
}

inline AmrexMeshDomain makeAmrexMeshDomain(const MeshDomain& domain,
                                           int dim,
                                           int max_grid_size,
                                           int coord_sys = 0)
{
    if (max_grid_size <= 0) {
        throw std::invalid_argument("AMReX BoxArray max_grid_size must be positive");
    }
    AmrexMeshDomain out{
        makeAmrexDomainBox(domain, dim),
        makeAmrexRealBox(domain, dim),
        amrex::Geometry(),
        amrex::BoxArray()
    };
    amrex::Array<int, AMREX_SPACEDIM> periodic{{AMREX_D_DECL(0, 0, 0)}};
    out.geometry.define(out.domain_box, &out.real_box, coord_sys, periodic.data());
    out.box_array.define(out.domain_box);
    out.box_array.maxSize(max_grid_size);
    return out;
}
#endif

} // namespace pele

#endif // PELE_DOMAIN_BUILDER_H
