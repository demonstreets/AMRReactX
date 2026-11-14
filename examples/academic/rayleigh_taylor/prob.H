#ifndef PROB_H
#define PROB_H
#include <AMReX_Print.H>
#include <AMReX_ParmParse.H>
#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>
#include <AMReX_REAL.H>
#include <AMReX_GpuMemory.H>
#include <cmath>
#include "mechanism.H"
#include "PeleC.H"
#include "IndexDefines.H"
#include "Constants.H"
#include "PelePhysics.H"
#include "Tagging.H"
#include "ProblemSpecificFunctions.H"
#include "prob_parm.H"
#include "StiffenedGas.H"
#include "TwoPhaseParams.H"

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void pc_initdata(int i, int j, int k, amrex::Array4<amrex::Real> const& state,
    amrex::GeometryData const& geomdata, ProbParmDevice const& prob_parm)
{
    const amrex::Real* prob_lo = geomdata.ProbLo();
    const amrex::Real* prob_hi = geomdata.ProbHi();
    const amrex::Real* dx = geomdata.CellSize();
    const amrex::Real x = prob_lo[0] + (i + 0.5) * dx[0];
    const amrex::Real y = prob_lo[1] + (j + 0.5) * dx[1];
    const amrex::Real Lx = prob_hi[0] - prob_lo[0];
    const amrex::Real Ly = prob_hi[1] - prob_lo[1];
    const amrex::Real y_iface = 0.5 * (prob_lo[1] + prob_hi[1]) +
        prob_parm.pert_amp *
        std::cos(2.0 * M_PI * prob_parm.pert_mode * (x - prob_lo[0]) / Lx);
    const bool in_heavy = (y > y_iface);
    const amrex::Real rho = in_heavy ? prob_parm.rho_heavy : prob_parm.rho_light;
    const amrex::Real alpha = in_heavy ? 1.0 : 0.0;
    constexpr amrex::Real gamma_gas = 1.4;
    constexpr StiffenedGasParams sg = twophase_liquid_params();
    constexpr amrex::Real cv_liquid = MYPELE_TWOPHASE_LIQUID_CV;
    constexpr amrex::Real gas_constant =
        pele::physics::Constants::RU / pele::physics::Constants::AIRMW;

    // Hydrostatic pressure for downward gravity, continuous at the perturbed
    // interface. Each phase uses the EOS used by primitive recovery/HLLC.
    const amrex::Real p_iface = prob_parm.p0 +
        prob_parm.rho_heavy * prob_parm.gravity *
        (prob_hi[1] - y_iface);
    const amrex::Real p_hydro = in_heavy ?
        prob_parm.p0 + prob_parm.rho_heavy * prob_parm.gravity *
        (prob_hi[1] - y) :
        p_iface + prob_parm.rho_light * prob_parm.gravity * (y_iface - y);
    const amrex::Real e = in_heavy ?
        sg_e(sg, rho, p_hydro) :
        p_hydro / ((gamma_gas - 1.0) * rho);

    state(i,j,k,URHO) = rho;
    state(i,j,k,UMX) = 0.0;
    state(i,j,k,UMY) = 0.0;
    state(i,j,k,UMZ) = 0.0;
    state(i,j,k,UEINT) = rho * e;
    state(i,j,k,UEDEN) = rho * e;
    state(i,j,k,UTEMP) = in_heavy ?
        sg_T(sg, rho, e, cv_liquid) :
        p_hydro / (rho * gas_constant);
#if NUM_ADV > 0
    state(i,j,k,UFA) = rho * alpha;
#endif
    for (int n = 0; n < NUM_SPECIES; ++n) {
        state(i,j,k,UFS+n) = 0.0;
    }
    state(i,j,k,UFS) = rho;
}
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void bcnormal(const amrex::Real*, const amrex::Real s_int[NVAR],
    amrex::Real s_ext[NVAR], const int, const int, const amrex::Real,
    amrex::GeometryData const&, ProbParmDevice const&,
    const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>&)
{ for (int n = 0; n < NVAR; n++) s_ext[n] = s_int[n]; }

void pc_prob_close();
using ProblemSpecificFunctions = DefaultProblemSpecificFunctions;
#endif
