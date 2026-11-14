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
  const int* /*init*/,
  const int* /*name*/,
  const int* /*namelen*/,
  const amrex::Real* /*probLo*/,
  const amrex::Real* /*probHi*/)
{
}
}

void
MyProblemSpecificFunctions::EBUserDefined(
  const amrex::Geometry& g,
  const int r,
  const int m)
{
  // Single cylinder: radius 0.5 m, center at (5.0, 5.0, 0.625), axis along z
  amrex::EB2::CylinderIF cylinder(
    0.5,
    10.0,
    2,
    amrex::RealArray{AMREX_D_DECL(5.0, 5.0, 0.625)},
    false);

  auto gshop = amrex::EB2::makeShop(cylinder);
  amrex::EB2::Build(gshop, g, r, m);
}
