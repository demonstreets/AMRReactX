#include <PeleLMeX.H>
#include <AMReX_ParmParse.H>

void
PeleLM::readProbParm()
{
  amrex::ParmParse pp("prob");
  pp.query("P_mean", PeleLM::prob_parm->P_mean);
  pp.query("jet1_ylo", PeleLM::prob_parm->jet1_ylo);
  pp.query("jet1_yhi", PeleLM::prob_parm->jet1_yhi);
  pp.query("jet1_T", PeleLM::prob_parm->jet1_T);
  pp.query("jet1_U", PeleLM::prob_parm->jet1_U);
  pp.query("jet1_Y_C12H23", PeleLM::prob_parm->jet1_Y_C12H23);
  pp.query("jet1_Y_N2", PeleLM::prob_parm->jet1_Y_N2);
  pp.query("jet2_ylo", PeleLM::prob_parm->jet2_ylo);
  pp.query("jet2_yhi", PeleLM::prob_parm->jet2_yhi);
  pp.query("jet2_T", PeleLM::prob_parm->jet2_T);
  pp.query("jet2_U", PeleLM::prob_parm->jet2_U);
  pp.query("jet2_Y_O2", PeleLM::prob_parm->jet2_Y_O2);
  pp.query("jet2_Y_N2", PeleLM::prob_parm->jet2_Y_N2);
  pp.query("do_ignit", PeleLM::prob_parm->do_ignit);
  pp.query("ignitSphX", PeleLM::prob_parm->ignitSphX);
  pp.query("ignitSphY", PeleLM::prob_parm->ignitSphY);
  pp.query("ignitSphRad", PeleLM::prob_parm->ignitSphRad);
  pp.query("ignitT", PeleLM::prob_parm->ignitT);
}

void
PeleLM::freeProbParm()
{
}
