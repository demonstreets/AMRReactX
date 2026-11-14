#include <PeleLMeX.H>
#include <AMReX_ParmParse.H>
#include <AMReX_EB2.H>
#include <AMReX_EB2_IF.H>
#include "pelelmex_prob.H"

void
PeleLM::readProbParm()
{
  amrex::ParmParse pp("prob");
  pp.query("P_mean", prob_parm->P_mean);
  pp.query("T_mean", prob_parm->T_mean);
  pp.query("wind_u", prob_parm->wind_u);
  pp.query("wind_v", prob_parm->wind_v);
  pp.query("leak_xc", prob_parm->leak_xc);
  pp.query("leak_yc", prob_parm->leak_yc);
  pp.query("leak_zc", prob_parm->leak_zc);
  pp.query("leak_rate", prob_parm->leak_rate);
  pp.query("leak_radius", prob_parm->leak_radius);
  pp.query("leak_T", prob_parm->leak_T);
  pp.query("ke_inlet_TI", prob_parm->ke_inlet_TI);
  pp.query("ke_inlet_L", prob_parm->ke_inlet_L);
  // Leak-source local refinement: box around leak (25.5,20,20)
  amrex::RealBox leakbox(
    {24.0, 17.0, 17.0},
    {27.0, 23.0, 23.0});
  amrex::AMRErrorTagInfo info;
  info.SetRealBox(leakbox);
  info.SetMaxLevel(1);
  errTags.push_back(amrex::AMRErrorTag(info));
}

void
PeleLM::freeProbParm()
{
}

void
pc_prob_close()
{
}

extern "C" {
void
amrex_probinit(
  const int*, const int*, const int*, const amrex::Real*, const amrex::Real*)
{
}
}

// 3 cylinders: radius 1m, height 8m (z-axis), positions ref FLACS layout
void
MyProblemSpecificFunctions::EBUserDefined(
  const amrex::Geometry& g,
  const int r,
  const int m)
{
  amrex::EB2::CylinderIF c1(
    5.0,   // radius
    8.0,   // height
    2,     // direction (z-axis)
    amrex::RealArray{AMREX_D_DECL(20.0, 25.0, 20.0)},
    false);
  amrex::EB2::CylinderIF c2(
    5.0,
    8.0,
    2,
    amrex::RealArray{AMREX_D_DECL(35.0, 17.5, 20.0)},
    false);
  amrex::EB2::CylinderIF c3(
    5.0,
    8.0,
    2,
    amrex::RealArray{AMREX_D_DECL(35.0, 32.5, 20.0)},
    false);
  auto u1 = amrex::EB2::makeUnion(c1, c2);
  auto u2 = amrex::EB2::makeUnion(u1, c3);
  auto gshop = amrex::EB2::makeShop(u2);
  amrex::EB2::Build(gshop, g, r, m);
}