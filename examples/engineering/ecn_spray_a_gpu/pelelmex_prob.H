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
  amrex::Real T_amb = 1000.0;
  amrex::Real Y_O2_amb = 0.233;
  amrex::Real Y_N2_amb = 0.767;
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

    // Uniform ambient: 1000K air (O2 23.3%, N2 76.7%)
    amrex::Real mf[NUM_SPECIES] = {0.0};
    mf[O2_ID] = prob_parm.Y_O2_amb;
    mf[N2_ID] = prob_parm.Y_N2_amb;

    const amrex::Real P_cgs = prob_parm.P_mean * 10.0;  // Pa -> dyn/cm^2
    amrex::Real rho_cgs = 0.0;
    eos.PYT2R(P_cgs, mf, prob_parm.T_amb, rho_cgs);

    state(i,j,k,DENSITY) = rho_cgs * 1.0e3;   // g/cm^3 -> kg/m^3
    state(i,j,k,TEMP)    = prob_parm.T_amb;
    for (int n = 0; n < NUM_SPECIES; n++) {
      state(i,j,k,FIRSTSPEC+n) = mf[n] * state(i,j,k,DENSITY);
    }

    amrex::Real h_cgs = 0.0;
    eos.TY2H(prob_parm.T_amb, mf, h_cgs);
    state(i,j,k,RHOH)  = h_cgs * 1.0e-4 * state(i,j,k,DENSITY);  // erg/g -> J/kg
    state(i,j,k,VELX)  = 0.0;
    state(i,j,k,VELY)  = 0.0;
    state(i,j,k,RHORT) = 0.0;
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
    const amrex::Real P_cgs = prob_parm.P_mean * 10.0;

    // Default: ambient air, zero velocity
    amrex::Real mf[NUM_SPECIES] = {0.0};
    mf[O2_ID] = prob_parm.Y_O2_amb;
    mf[N2_ID] = prob_parm.Y_N2_amb;
    amrex::Real T_bc = prob_parm.T_amb;
    amrex::Real U_bc = 0.0;

    amrex::Real rho_cgs = 0.0;
    eos.PYT2R(P_cgs, mf, T_bc, rho_cgs);

    s_ext[DENSITY] = rho_cgs * 1.0e3;
    s_ext[TEMP]    = T_bc;
    s_ext[VELX]    = U_bc;
    s_ext[VELY]    = 0.0;

    for (int n = 0; n < NUM_SPECIES; n++) {
      s_ext[FIRSTSPEC+n] = mf[n] * s_ext[DENSITY];
    }

    amrex::Real h_cgs = 0.0;
    eos.TY2H(T_bc, mf, h_cgs);
    s_ext[RHOH]  = h_cgs * 1.0e-4 * s_ext[DENSITY];
    s_ext[RHORT] = 0.0;
  }
};

using ProblemSpecificFunctions = MyProblemSpecificFunctions;
using ProbParm = MyProbParm;

#endif
