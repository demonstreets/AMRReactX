#include "bc_tags.H"

#ifdef PELE_HAVE_AMREX_EB_HEADERS
#include <AMReX.H>
#include <AMReX_EB2.H>
#include <AMReX_EB2_Level.H>
#include <AMReX_EBCellFlag.H>
#include <AMReX_iMultiFab.H>
#endif

#include <algorithm>
#include <cctype>

namespace pele {

BoundaryType
parseBoundaryType(const std::string& token)
{
    std::string value;
    value.reserve(token.size());
    for (unsigned char c : token) {
        if (c != '-' && c != '_') {
            value.push_back(static_cast<char>(std::tolower(c)));
        }
    }

    if (value == "wall" || value == "noslip" || value == "noslipwall") return BoundaryType::WALL;
    if (value == "slip" || value == "slipwall") return BoundaryType::SLIP_WALL;
    if (value == "inlet" || value == "inflow") return BoundaryType::INLET;
    if (value == "outlet" || value == "outflow") return BoundaryType::OUTLET;
    if (value == "symmetry" || value == "sym") return BoundaryType::SYMMETRY;
    return BoundaryType::UNKNOWN;
}

#ifdef PELE_HAVE_AMREX_EB_HEADERS

void
tagCellsFromFlags(const amrex::FabArray<amrex::EBCellFlagFab>& flags,
                  amrex::iMultiFab& tags)
{
    AMREX_ALWAYS_ASSERT(flags.boxArray() == tags.boxArray());
    AMREX_ALWAYS_ASSERT(flags.DistributionMap() == tags.DistributionMap());

    for (amrex::MFIter mfi(flags); mfi.isValid(); ++mfi) {
        const amrex::Box& bx = mfi.validbox();
        auto const& flag_fab = flags.const_array(mfi);
        auto const& tag_arr = tags.array(mfi);

        amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE (int i, int j, int k) noexcept {
            auto f = flag_fab(i,j,k);
            if (f.isCovered()) {
                tag_arr(i,j,k) = static_cast<int>(CellType::COVERED);
            } else if (f.isRegular()) {
                tag_arr(i,j,k) = static_cast<int>(CellType::FLUID);
            } else {
                tag_arr(i,j,k) = static_cast<int>(CellType::CUT);
            }
        });
    }
}

void
buildCellTags(amrex::iMultiFab& cell_type,
              const amrex::Geometry& geom)
{
    const auto& eb_level = amrex::EB2::IndexSpace::top().getLevel(geom);

    // Fill EBCellFlag
    amrex::FabArray<amrex::EBCellFlagFab> flags(cell_type.boxArray(),
                                                 cell_type.DistributionMap(),
                                                 1, 0);
    eb_level.fillEBCellFlag(flags, geom);

    // Convert flags to tags
    tagCellsFromFlags(flags, cell_type);
}

#endif

} // namespace pele
