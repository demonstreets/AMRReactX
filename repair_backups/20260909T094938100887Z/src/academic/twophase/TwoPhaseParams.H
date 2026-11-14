#pragma once

#include "StiffenedGas.H"

// Defaults preserve the existing water-like two-phase model. Individual
// benchmark executables may override these at compile time for dimensionless
// reference problems without changing the physical default.
#ifndef MYPELE_TWOPHASE_GAS_GAMMA
#define MYPELE_TWOPHASE_GAS_GAMMA 1.4
#endif
#ifndef MYPELE_TWOPHASE_GAS_PINF
#define MYPELE_TWOPHASE_GAS_PINF 0.0
#endif
#ifndef MYPELE_TWOPHASE_LIQUID_GAMMA
#define MYPELE_TWOPHASE_LIQUID_GAMMA 4.4
#endif
#ifndef MYPELE_TWOPHASE_LIQUID_PINF
#define MYPELE_TWOPHASE_LIQUID_PINF 6.0e8
#endif
#ifndef MYPELE_TWOPHASE_LIQUID_CV
#define MYPELE_TWOPHASE_LIQUID_CV 4.18e7
#endif

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE constexpr
StiffenedGasParams twophase_liquid_params()
{
    return {MYPELE_TWOPHASE_LIQUID_GAMMA,
            MYPELE_TWOPHASE_LIQUID_PINF};
}
