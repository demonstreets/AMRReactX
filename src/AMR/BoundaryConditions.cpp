#include "AMR/BoundaryConditions.H"

#include <AMReX.H>

namespace amrreactx {

int parse_boundary_type(const std::string& name)
{
    if (name == "inlet") {
        return BcInlet;
    }
    if (name == "outlet") {
        return BcOutlet;
    }
    if (name == "wall") {
        return BcWall;
    }
    if (name == "open") {
        return BcOpen;
    }
    amrex::Abort("Unknown scalar boundary type: " + name);
    return BcOpen;
}

std::string boundary_type_name(int bc)
{
    switch (bc) {
    case BcInlet:
        return "inlet";
    case BcOutlet:
        return "outlet";
    case BcWall:
        return "wall";
    case BcOpen:
        return "open";
    default:
        return "unknown";
    }
}

} // namespace amrreactx
