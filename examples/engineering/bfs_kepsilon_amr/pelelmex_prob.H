#ifndef PELELM_PROB_H
#define PELELM_PROB_H

#include "my_pele_modules.H"

#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>
#include <AMReX_SPACE.H>

#include <PeleLMeX_ProblemSpecificFunctions.H>
#include <PeleLMeX_Index.H>
#include <PMFData.H>
#include <PelePhysics.H>

struct MyProbParm : public ProbParmDefault
{
  amrex::Real T_mean = 298.0;
  amrex::Real Y_o2 = 0.233;
  amrex::Real T_hot = 1800.0;
  amrex::Real Twall = 300.0;
  amrex::Real meanFlowMag = 0.0;
};

struct MyProblemSpecificFunctions : public DefaultProblemSpecificFunctions
{
  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void initdata(
    int i,
    int j,
    int k,
    int is_incompressible,
    amrex::Array4<amrex::Real> const& state,
    amrex::Array4<amrex::Real> const& aux,
    amrex::GeometryData const& geomdata,
    MyProbParm const& prob_parm,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    const amrex::Real* prob_lo = geomdata.ProbLo();
    const amrex::Real* dx = geomdata.CellSize();

    auto eos = pele::physics::PhysicsType::eos();

    amrex::Real massfrac[NUM_SPECIES] = {0.0};
    massfrac[O2_ID] = prob_parm.Y_o2;
    massfrac[N2_ID] = 1.0 - prob_parm.Y_o2;

    AMREX_D_TERM(state(i, j, k, VELX) = prob_parm.meanFlowMag;
                 , state(i, j, k, VELY) = 0.0;, state(i, j, k, VELZ) = 0.0);

    if (!(is_incompressible == 0)) {
      return;
    }

    state(i, j, k, TEMP) = prob_parm.T_mean;

    amrex::Real P_cgs = prob_parm.P_mean * 10.0;

    // Density
    amrex::Real rho_cgs = 0.0;
    eos.PYT2R(P_cgs, massfrac, state(i, j, k, TEMP), rho_cgs);
    state(i, j, k, DENSITY) = rho_cgs * 1.0e3;

    // Enthalpy
    amrex::Real h_cgs = 0.0;
    eos.TY2H(state(i, j, k, TEMP), massfrac, h_cgs);
    state(i, j, k, RHOH) = h_cgs * 1.0e-4 * state(i, j, k, DENSITY);

    // Species mass
    for (int n = 0; n < NUM_SPECIES; n++) {
      state(i, j, k, FIRSTSPEC + n) = massfrac[n] * state(i, j, k, DENSITY);
    }

    // k-epsilon initialization (uniform using inlet formula as reference)
    amrex::Real U_mag = prob_parm.meanFlowMag;
    amrex::Real TI = 0.05;
    amrex::Real L_t = 0.0381;
    amrex::Real C_mu = 0.09;
    amrex::Real k_init = 1.5 * (TI * U_mag) * (TI * U_mag);
    amrex::Real eps_init = std::pow(C_mu, 0.75) * std::pow(k_init, 1.5) / L_t;
    aux(i, j, k, 0) = k_init;
    aux(i, j, k, 1) = eps_init;
  }

  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void bcnormal(
    const amrex::Real* /*x[AMREX_SPACEDIM]*/,
    const amrex::CellData<amrex::Real>& /*s_in*/,
    amrex::Real s_ext[NVAR],
    const int idir,
    const int sgn,
    const amrex::Real /*time*/,
    amrex::GeometryData const& /*geomdata*/,
    MyProbParm const& prob_parm,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    if (sgn == 1) {
      amrex::Real massfrac[NUM_SPECIES] = {0.0};
      auto eos = pele::physics::PhysicsType::eos();
      s_ext[VELX] += prob_parm.meanFlowMag;

      massfrac[O2_ID] = prob_parm.Y_o2;
      massfrac[N2_ID] = 1.0 - prob_parm.Y_o2;

      s_ext[TEMP] = prob_parm.T_mean;

      amrex::Real rho_cgs, P_cgs, RhoH_temp;
      P_cgs = prob_parm.P_mean * 10.0;

      eos.PYT2R(P_cgs, massfrac, s_ext[TEMP], rho_cgs);
      s_ext[DENSITY] = rho_cgs * 1.0e3;

      eos.TY2H(s_ext[TEMP], massfrac, RhoH_temp);
      s_ext[RHOH] = RhoH_temp * 1.0e-4 * s_ext[DENSITY];

      for (int n = 0; n < NUM_SPECIES; n++) {
        s_ext[FIRSTSPEC + n] = massfrac[n] * s_ext[DENSITY];
      }
    }

    // Set domain boundary Temp on the y-low face when using NoSlipWallIsotherm
    if (idir == 1 && sgn == 1) {
      s_ext[TEMP] = prob_parm.Twall;
    }
  }

  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void bcnormal_aux(
    const amrex::Real x[AMREX_SPACEDIM],
    amrex::CellData<amrex::Real>& aux_ext,
    const int idir,
    const int /*sgn*/,
    const amrex::Real /*time*/,
    amrex::GeometryData const& /*geomdata*/,
    MyProbParm const& /*prob_parm*/,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    // Default: set k and epsilon to small values for non-inflow boundaries
    // Inflow boundaries are handled by fillPatchAux override
    aux_ext[0] = 1.0e-6;   // k
    aux_ext[1] = 1.0e-12;  // epsilon
  }
};

using ProblemSpecificFunctions = MyProblemSpecificFunctions;
using ProbParm = MyProbParm;

#endif
