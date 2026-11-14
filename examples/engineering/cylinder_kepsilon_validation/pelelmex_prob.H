#ifndef PELELM_PROB_H
#define PELELM_PROB_H

#include "my_pele_modules.H"

#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>
#include <AMReX_SPACE.H>
#include <AMReX_REAL.H>

#include <PeleLMeX_ProblemSpecificFunctions.H>
#include <PeleLMeX_Index.H>
#include <PMFData.H>
#include <PelePhysics.H>

using namespace amrex::literals;

struct MyProbParm : public ProbParmDefault
{
  amrex::Real P_mean = 101325.0;
  amrex::Real T_mean = 300.0;
  amrex::Real wind_u = 8.0;
  amrex::Real wind_v = 0.0;
};

struct MyProblemSpecificFunctions : public DefaultProblemSpecificFunctions
{
  // -----------------------------------------------------------------------
  // EB cylinder geometry — declared in pelelmex_prob.cpp
  // -----------------------------------------------------------------------
  static void EBUserDefined(
    const amrex::Geometry& geom,
    const int max_level,
    const int max_coarsening_level);

  // -----------------------------------------------------------------------
  // Initial condition: uniform flow U=8 m/s in +x, T=300K, air (N2/O2).
  // k-epsilon values initialized to inlet turbulence level.
  // -----------------------------------------------------------------------
  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void initdata(
    int i,
    int j,
    int k,
    int is_incompressible,
    amrex::Array4<amrex::Real> const& state,
    amrex::Array4<amrex::Real> const& aux,
    amrex::GeometryData const& /*geomdata*/,
    MyProbParm const& pp,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    auto eos = pele::physics::PhysicsType::eos();

    // Air composition by mass fraction
    amrex::Real mf[NUM_SPECIES] = {0.0};
    mf[N2_ID] = 0.767;
    mf[O2_ID] = 0.767;  // placeholder, corrected below

    state(i, j, k, TEMP) = pp.T_mean;
    AMREX_D_TERM(state(i, j, k, VELX) = pp.wind_u;
                 , state(i, j, k, VELY) = pp.wind_v;
                 , state(i, j, k, VELZ) = 0.0);

    // Correct air mass fractions
    mf[O2_ID] = 0.233;
    mf[N2_ID] = 0.767;

    amrex::Real P_cgs = pp.P_mean * 10.0;
    amrex::Real rho_cgs = 0.0;
    eos.PYT2R(P_cgs, mf, state(i, j, k, TEMP), rho_cgs);
    state(i, j, k, DENSITY) = rho_cgs * 1.0e3;

    for (int n = 0; n < NUM_SPECIES; n++) {
      state(i, j, k, FIRSTSPEC + n) = state(i, j, k, DENSITY) * mf[n];
    }

    amrex::Real h_cgs = 0.0;
    eos.TY2H(state(i, j, k, TEMP), mf, h_cgs);
    state(i, j, k, RHOH) = h_cgs * 1.0e-4 * state(i, j, k, DENSITY);
    state(i, j, k, RHORT) = 0.0;

    // k-epsilon initialization: 1% turbulence intensity at U=8 m/s
    // k = 1.5 * (I*U)^2 = 0.0096
    // eps = C_mu^0.75 * k^1.5 / L_t ≈ 0.00221
    aux(i, j, k, 0) = 0.0096;
    aux(i, j, k, 1) = 0.00221;
  }

  // -----------------------------------------------------------------------
  // bcnormal: inlet BC for flow variables (lo-x face only)
  // -----------------------------------------------------------------------
  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void bcnormal(
    const amrex::Real /*x*/[AMREX_SPACEDIM],
    const amrex::CellData<amrex::Real>& /*s_in*/,
    amrex::Real s_ext[NVAR],
    const int idir,
    const int sgn,
    const amrex::Real /*time*/,
    amrex::GeometryData const& /*geomdata*/,
    MyProbParm const& pp,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    auto eos = pele::physics::PhysicsType::eos();

    // Inlet BC on lo-x face (idir=0, sgn=1)
    if (idir == 0 && sgn == 1) {
      amrex::Real mf[NUM_SPECIES] = {0.0};
      mf[O2_ID] = 0.233;
      mf[N2_ID] = 0.767;

      s_ext[TEMP] = pp.T_mean;
      AMREX_D_TERM(s_ext[VELX] = pp.wind_u;
                   , s_ext[VELY] = pp.wind_v;
                   , s_ext[VELZ] = 0.0);

      amrex::Real P_cgs = pp.P_mean * 10.0;
      amrex::Real rho_cgs = 0.0;
      eos.PYT2R(P_cgs, mf, s_ext[TEMP], rho_cgs);
      s_ext[DENSITY] = rho_cgs * 1.0e3;

      amrex::Real h_cgs = 0.0;
      eos.TY2H(s_ext[TEMP], mf, h_cgs);
      s_ext[RHOH] = h_cgs * 1.0e-4 * s_ext[DENSITY];

      for (int n = 0; n < NUM_SPECIES; n++) {
        s_ext[FIRSTSPEC + n] = mf[n] * s_ext[DENSITY];
      }
      s_ext[RHORT] = 0.0;
    }
  }

  // -----------------------------------------------------------------------
  // bcnormal_aux: inlet BC for k and epsilon (1% turbulence intensity)
  // -----------------------------------------------------------------------
  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void bcnormal_aux(
    const amrex::Real /*x*/[AMREX_SPACEDIM],
    amrex::CellData<amrex::Real>& aux_ext,
    const int /*idir*/,
    const int /*sgn*/,
    const amrex::Real /*time*/,
    amrex::GeometryData const& /*geomdata*/,
    MyProbParm const& /*prob_parm*/,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    // Inlet turbulence: 1% TI at U=8 m/s
    // k = 1.5 * (0.01 * 8)^2 = 0.0096
    // eps = C_mu^0.75 * k^1.5 / L_t = 0.1643 * 0.000941 / 0.07 ≈ 0.00221
    aux_ext[0] = 0.0096;
    aux_ext[1] = 0.00221;

    // Any additional aux components set to small background
    for (int n = 2; n < aux_ext.ncomp; ++n) {
      aux_ext[n] = 1.0e-6;
    }
  }
};

using ProblemSpecificFunctions = MyProblemSpecificFunctions;
using ProbParm = MyProbParm;

#endif
