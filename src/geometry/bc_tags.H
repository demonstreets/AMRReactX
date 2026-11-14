#ifndef PELE_BC_TAGS_H
#define PELE_BC_TAGS_H

#if __has_include(<AMReX_EB2.H>)
#define PELE_HAVE_AMREX_EB_HEADERS 1
#include <AMReX_EB2.H>
#include <AMReX_EB2_Level.H>
#include <AMReX_iMultiFab.H>
#include <AMReX_MultiFab.H>
#include <AMReX_Geometry.H>
#include <AMReX_EBCellFlag.H>
#endif

#include <string>
#include <vector>

namespace pele {

//! Face-level boundary condition tags used by the geometry pipeline.
enum class BoundaryType : int {
    WALL = 0,
    INLET = 1,
    OUTLET = 2,
    SYMMETRY = 3,
    SLIP_WALL = 4,
    UNKNOWN = 5
};

//! Convert a boundary type to the canonical lower-case input token.
inline std::string boundaryTypeName(BoundaryType t) {
    switch (t) {
        case BoundaryType::WALL: return "wall";
        case BoundaryType::INLET: return "inlet";
        case BoundaryType::OUTLET: return "outlet";
        case BoundaryType::SYMMETRY: return "symmetry";
        case BoundaryType::SLIP_WALL: return "slip_wall";
        case BoundaryType::UNKNOWN: return "unknown";
    }
    return "unknown";
}

//! Parse user-facing BC tokens accepted by the master-plan schema.
BoundaryType parseBoundaryType(const std::string& token);

//! Cell type classification after EB construction.
enum class CellType : int {
    FLUID   = 0,   // Fully fluid (regular cell, vfrac = 1)
    CUT     = 1,   // Intersects EB (0 < vfrac < 1)
    COVERED = 2,   // Inside solid body (vfrac = 0)
    SOLID   = 3    // Explicitly marked as solid (user override)
};

//! Convert CellType to a human-readable string.
inline std::string cellTypeName(CellType t) {
    switch (t) {
        case CellType::FLUID:   return "FLUID";
        case CellType::CUT:     return "CUT";
        case CellType::COVERED: return "COVERED";
        case CellType::SOLID:   return "SOLID";
    }
    return "UNKNOWN";
}

//! Tag cells in an iMultiFab based on EB cell flags.
//!
//! Uses EBCellFlag data from the EB2 level to classify each cell as
//! FLUID, CUT, or COVERED.  The output iMultiFab must have the same
//! BoxArray/DistributionMapping as the EB level.
//!
//! \param flags   EBCellFlag fabric (from level.fillEBCellFlag).
//! \param tags    Output iMultiFab (same layout as flags) filled with CellType.
#ifdef PELE_HAVE_AMREX_EB_HEADERS
void tagCellsFromFlags(const amrex::FabArray<amrex::EBCellFlagFab>& flags,
                       amrex::iMultiFab& tags);

//! High-level helper: build EB cell tags using an already-built EB2 IndexSpace.
//!
//! \param cell_type  Output iMultiFab.
//! \param geom       Geometry matching the finest EB level.
void buildCellTags(amrex::iMultiFab& cell_type,
                   const amrex::Geometry& geom);
#endif

} // namespace pele

#endif // PELE_BC_TAGS_H
