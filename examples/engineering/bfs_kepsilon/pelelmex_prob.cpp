#include <PeleLMeX.H>
#include <AMReX_ParmParse.H>

void
PeleLM::readProbParm() // NOLINT(readability-make-member-function-const)
{
  amrex::ParmParse pp("prob");

  pp.query("T_mean", prob_parm->T_mean);
  pp.query("P_mean", prob_parm->P_mean);
  pp.query("Y_o2", prob_parm->Y_o2);
  pp.query("T_wall", prob_parm->Twall);
  pp.query("meanFlowMag", prob_parm->meanFlowMag);
  pp.query("windProfileType", prob_parm->windProfileType);
  pp.query("windRefHeight", prob_parm->windRefHeight);
  pp.query("windRoughnessLength", prob_parm->windRoughnessLength);
}

void
PeleLM::freeProbParm()
{
}
