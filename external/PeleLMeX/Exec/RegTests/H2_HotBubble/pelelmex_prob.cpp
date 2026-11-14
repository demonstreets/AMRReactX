#include <PeleLMeX.H>
#include <AMReX_ParmParse.H>

void
PeleLM::readProbParm() // NOLINT(readability-make-member-function-const)
{
  amrex::ParmParse pp("prob");

  pp.query("P_mean", prob_parm->P_mean);
  pp.query("T_mean", prob_parm->T_mean);
  pp.query("T_hot", prob_parm->T_hot);
  pp.query("r_hot", prob_parm->r_hot);
  pp.query("phi", prob_parm->phi);
}

void
PeleLM::freeProbParm()
{
}
