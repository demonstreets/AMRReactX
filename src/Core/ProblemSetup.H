#pragma once

#include "Core/State.H"

#include <AMReX_Geometry.H>

namespace amrreactx {

amrex::Geometry make_geometry();
RuntimeParams read_params(const amrex::Geometry& geom);

} // namespace amrreactx
