#ifndef PELELM_PROB_H
#define PELELM_PROB_H

#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>
#include <AMReX_SPACE.H>

#include <PeleLMeX_ProblemSpecificFunctions.H>
#include <PeleLMeX_Index.H>
#include <PMFData.H>
#include <PelePhysics.H>

struct MyProbParm : public ProbParmDefault
{
  amrex::Real P_mean = 101325.0;
  amrex::Real jet1_ylo = 0.030;
  amrex::Real jet1_yhi = 0.035;
  amrex::Real jet1_T   = 400.0;
  amrex::Real jet1_U   = 2.0;
  amrex::Real jet1_Y_C12H23 = 0.02;
  amrex::Real jet1_Y_N2     = 0.98;
  amrex::Real jet2_ylo = 0.020;
  amrex::Real jet2_yhi = 0.025;
  amrex::Real jet2_T   = 1500.0;
  amrex::Real jet2_U   = 2.0;
  amrex::Real jet2_Y_O2 = 0.233;
  amrex::Real jet2_Y_N2 = 0.767;

  // Ignition
  int do_ignit = 0;
  amrex::Real ignitSphX  = 0.03;
  amrex::Real ignitSphY  = 0.025;
  amrex::Real ignitSphRad = 0.005;
  amrex::Real ignitT     = 2000.0;
};

struct MyProblemSpecificFunctions : public DefaultProblemSpecificFunctions
{
  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void initdata(
    int i, int j, int k,
    int /*is_incompressible*/,
    amrex::Array4<amrex::Real> const& state,
    amrex::Array4<amrex::Real> const& /*aux*/,
    amrex::GeometryData const& geomdata,
    MyProbParm const& prob_parm,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    auto eos = pele::physics::PhysicsType::eos();

    // Background: pure N2 at 298K
    amrex::Real mf[NUM_SPECIES] = {0.0};
    mf[O2_ID] = 0.0;
    mf[N2_ID] = 1.0;

    const amrex::Real T_init = 298.0;

    // EOS call: CGS units
    amrex::Real P_cgs = prob_parm.P_mean * 10.0;   // Pa -> dyn/cm²
    amrex::Real rho_cgs = 0.0;
    eos.PYT2R(P_cgs, mf, T_init, rho_cgs);

    // Convert to MKS and store
    state(i,j,k,DENSITY) = rho_cgs * 1.0e3;         // g/cm³ -> kg/m³
    state(i,j,k,TEMP)    = T_init;

    // Species: rho * Y
    for (int n = 0; n < NUM_SPECIES; n++) {
      state(i,j,k,FIRSTSPEC+n) = mf[n] * state(i,j,k,DENSITY);
    }

    // Enthalpy
    amrex::Real h_cgs = 0.0;
    eos.TY2H(T_init, mf, h_cgs);
    state(i,j,k,RHOH) = h_cgs * 1.0e-4 * state(i,j,k,DENSITY); // erg/g -> J/kg

    // Velocity
    state(i,j,k,VELX) = 0.0;
    state(i,j,k,VELY) = 0.0;

    // Thermo pressure
    state(i,j,k,RHORT) = 0.0;

    // Ignition sphere: override temperature in a spherical region
    if (prob_parm.do_ignit) {
      const amrex::Real* prob_lo = geomdata.ProbLo();
      const amrex::Real* dx = geomdata.CellSize();
      AMREX_D_TERM(
        const amrex::Real x = prob_lo[0] + (i + 0.5) * dx[0];,
        const amrex::Real y = prob_lo[1] + (j + 0.5) * dx[1];,
        const amrex::Real z = 0.0;);
      amrex::Real dist = std::sqrt(
        (x - prob_parm.ignitSphX) * (x - prob_parm.ignitSphX) +
        (y - prob_parm.ignitSphY) * (y - prob_parm.ignitSphY));
      if (dist < prob_parm.ignitSphRad) {
        state(i,j,k,TEMP) = prob_parm.ignitT;
        amrex::Real rho_ign = 0.0;
        eos.PYT2R(P_cgs, mf, prob_parm.ignitT, rho_ign);
        state(i,j,k,DENSITY) = rho_ign * 1.0e3;
        for (int n = 0; n < NUM_SPECIES; n++) {
          state(i,j,k,FIRSTSPEC+n) = mf[n] * state(i,j,k,DENSITY);
        }
        amrex::Real h_ign = 0.0;
        eos.TY2H(prob_parm.ignitT, mf, h_ign);
        state(i,j,k,RHOH) = h_ign * 1.0e-4 * state(i,j,k,DENSITY);
      }
    }
  }

  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void bcnormal(
    const amrex::Real x[AMREX_SPACEDIM],
    const amrex::CellData<amrex::Real>& /*s_in*/,
    amrex::Real s_ext[NVAR],
    const int idir,
    const int sgn,
    const amrex::Real /*time*/,
    amrex::GeometryData const& /*geomdata*/,
    MyProbParm const& prob_parm,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    auto eos = pele::physics::PhysicsType::eos();
    const amrex::Real y = x[1];

    // Default: air at 300K, zero velocity (outflow / no-slip)
    amrex::Real mf[NUM_SPECIES] = {0.0};
    amrex::Real T_bc = 300.0;
    amrex::Real U_bc = 0.0;
    mf[O2_ID] = 0.0;
    mf[N2_ID] = 1.0;

    // Check jet regions (inflow from left: idir==0, sgn==1 per PeleLMeX convention)
    // Jet1: C12H23 + N2 fuel jet
    if (y >= prob_parm.jet1_ylo && y <= prob_parm.jet1_yhi) {
      for (int n = 0; n < NUM_SPECIES; n++) mf[n] = 0.0;
      mf[C12H23_ID] = prob_parm.jet1_Y_C12H23;
      T_bc = prob_parm.jet1_T;
      U_bc = prob_parm.jet1_U;
    }
    // Jet2: O2 + N2 hot air jet
    if (y >= prob_parm.jet2_ylo && y <= prob_parm.jet2_yhi) {
      for (int n = 0; n < NUM_SPECIES; n++) mf[n] = 0.0;
      mf[O2_ID] = prob_parm.jet2_Y_O2;
      T_bc = prob_parm.jet2_T;
      U_bc = prob_parm.jet2_U;
    }

    // EOS call: CGS units
    amrex::Real P_cgs = prob_parm.P_mean * 10.0;
    amrex::Real rho_cgs = 0.0;
    eos.PYT2R(P_cgs, mf, T_bc, rho_cgs);

    s_ext[DENSITY] = rho_cgs * 1.0e3;
    s_ext[TEMP]    = T_bc;
    s_ext[VELX]    = U_bc;
    s_ext[VELY]    = 0.0;

    // Species: rho * Y
    for (int n = 0; n < NUM_SPECIES; n++) {
      s_ext[FIRSTSPEC+n] = mf[n] * s_ext[DENSITY];
    }

    // Enthalpy
    amrex::Real h_cgs = 0.0;
    eos.TY2H(T_bc, mf, h_cgs);
    s_ext[RHOH] = h_cgs * 1.0e-4 * s_ext[DENSITY];

    s_ext[RHORT] = 0.0;
  }
};

using ProbParm = MyProbParm;
using ProblemSpecificFunctions = MyProblemSpecificFunctions;

#endif
