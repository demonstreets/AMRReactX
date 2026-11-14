#include <PeleLMeX.H>
#include <AMReX_ParmParse.H>

void
PeleLM::readProbParm() // NOLINT(readability-make-member-function-const)
{
  amrex::ParmParse pp("prob");
  pp.query("P_mean", prob_parm->P_mean);
  pp.query("T_mean", prob_parm->T_mean);
  pp.query("meanFlowMag", prob_parm->meanFlowMag);
  pp.query("meanFlowDir", prob_parm->meanFlowDir);
  PeleLM::prob_parm->eosparm = PeleLM::eos_parms.device_parm();
}

void
PeleLM::freeProbParm()
{
}
