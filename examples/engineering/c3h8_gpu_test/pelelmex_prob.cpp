#include <PeleLMeX.H>
#include <AMReX_ParmParse.H>
#include <AMReX_EB2.H>
#include <AMReX_EB2_IF.H>
#include "pelelmex_prob.H"
void PeleLM::readProbParm() { amrex::ParmParse pp("prob"); pp.query("P_mean", prob_parm->P_mean); pp.query("T_mean", prob_parm->T_mean); pp.query("wind_u", prob_parm->wind_u); pp.query("wind_v", prob_parm->wind_v); pp.query("leak_xc", prob_parm->leak_xc); pp.query("leak_yc", prob_parm->leak_yc); pp.query("leak_zc", prob_parm->leak_zc); pp.query("leak_rate", prob_parm->leak_rate); pp.query("leak_radius", prob_parm->leak_radius); pp.query("leak_T", prob_parm->leak_T); pp.query("ke_inlet_TI", prob_parm->ke_inlet_TI); pp.query("ke_inlet_L", prob_parm->ke_inlet_L); }
void PeleLM::freeProbParm() {}
void pc_prob_close() {}
extern "C" { void amrex_probinit(const int*, const int*, const int*, const amrex::Real*, const amrex::Real*) {} }
void MyProblemSpecificFunctions::EBUserDefined(const amrex::Geometry& g, const int r, const int m) {
  amrex::EB2::CylinderIF c1(5.0, 8.0, 2, amrex::RealArray{AMREX_D_DECL(20.0, 25.0, 20.0)}, false);
  amrex::EB2::CylinderIF c2(5.0, 8.0, 2, amrex::RealArray{AMREX_D_DECL(40.0, 25.0, 20.0)}, false);
  amrex::EB2::CylinderIF c3(5.0, 8.0, 2, amrex::RealArray{AMREX_D_DECL(60.0, 25.0, 20.0)}, false);
  auto gshop = amrex::EB2::makeShop(amrex::EB2::makeUnion(c1, c2, c3));
  amrex::EB2::Build(gshop, g, r, m);
}
