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

// 品字形三圆柱: radius 5m, height 8m (z-axis)
// 前柱：(x=20, y=25, z=20) — 迎风
// 后柱左：(x=30, y=20, z=20)
// 后柱右：(x=30, y=30, z=20)
void
MyProblemSpecificFunctions::EBUserDefined(
  const amrex::Geometry& g,
  const int r,
  const int m)
{
  // Front cylinder (windward)
  amrex::EB2::CylinderIF c_front(
    5.0,   // radius
    8.0,   // height
    2,     // direction (z-axis)
    amrex::RealArray{AMREX_D_DECL(20.0, 25.0, 20.0)},
    false);
  // Back-left cylinder
  amrex::EB2::CylinderIF c_bl(
    5.0,
    8.0,
    2,
    amrex::RealArray{AMREX_D_DECL(30.0, 20.0, 20.0)},
    false);
  // Back-right cylinder
  amrex::EB2::CylinderIF c_br(
    5.0,
    8.0,
    2,
    amrex::RealArray{AMREX_D_DECL(30.0, 30.0, 20.0)},
    false);
  auto u1 = amrex::EB2::makeUnion(c_front, c_bl);
  auto u2 = amrex::EB2::makeUnion(u1, c_br);
  auto gshop = amrex::EB2::makeShop(u2);
  amrex::EB2::Build(gshop, g, r, m);
}
