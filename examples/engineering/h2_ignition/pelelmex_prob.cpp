#include <PeleLMeX.H>
#include <AMReX_ParmParse.H>

void
PeleLM::readProbParm() // NOLINT(readability-make-member-function-const)
{
  amrex::ParmParse pp("prob");

  pp.query("P_mean", prob_parm->P_mean);
  pp.query("T_mean", prob_parm->T_mean);
  pp.query("T_bubble", prob_parm->T_bubble);
  pp.query("bubble_radius", prob_parm->bubble_rad);
  pp.query("bubble_y0", prob_parm->bubble_y0);
  pp.query("use_symmetry", prob_parm->is_sym);
  pp.query("use_mix_bubble", prob_parm->bubble_is_mix);

}

void
PeleLM::freeProbParm()
{
}
