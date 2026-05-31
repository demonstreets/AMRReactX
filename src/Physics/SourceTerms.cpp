#include "Physics/SourceTerms.H"

#include <AMReX.H>

namespace amrreactx {

int parse_source_type(const std::string& name)
{
    if (name == "gaussian") {
        return SourceGaussian;
    }
    if (name == "box") {
        return SourceBox;
    }
    amrex::Abort("Unknown scalar source type: " + name);
    return SourceGaussian;
}

std::string source_type_name(int source_type)
{
    switch (source_type) {
    case SourceGaussian:
        return "gaussian";
    case SourceBox:
        return "box";
    default:
        return "unknown";
    }
}

} // namespace amrreactx
