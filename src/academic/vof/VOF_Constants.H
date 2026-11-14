#ifndef VOF_CONSTANTS_H
#define VOF_CONSTANTS_H

#include <AMReX_REAL.H>

// VOF control parameters
constexpr amrex::Real VOF_TINY = 1.0e-12; // small threshold for denominator protection
constexpr amrex::Real VOF_CLIP_LO = 0.0;  // advected scalar lower bound
constexpr amrex::Real VOF_CLIP_HI = 1.0;  // advected scalar upper bound

#endif // VOF_CONSTANTS_H
