#include <PeleLMeX.H>
#include <AMReX_ParmParse.H>

void
PeleLM::readProbParm() // NOLINT(readability-make-member-function-const)
{
  amrex::ParmParse pp("prob");

  pp.query("T_mean", prob_parm->T_mean);
  pp.query("P_mean", prob_parm->P_mean);
  pp.query("Y_o2", prob_parm->Y_o2);
  pp.query("T_hot", prob_parm->T_hot);
  pp.query("T_wall", prob_parm->Twall);
  pp.query("meanFlowMag", prob_parm->meanFlowMag);
  pp.query("do_ignite", prob_parm->ignite_flow);

  if (prob_parm->ignite_flow) {
    pp.query("ignition_temperature", prob_parm->ignition_temperature);
  }

  pp.query("EBinflow_T", prob_parm->EBinflow_T);
  pp.query("EBinflow_vel", prob_parm->EBinflow_vel);
  pp.query("EBinflow_Y_o2", prob_parm->EBinflow_Y_o2);

  amrex::ParmParse pplm("peleLM");
  pplm.query("EBinflow", prob_parm->do_EBinflow);
  pplm.query("ke_inlet_TI", prob_parm->ke_inlet_TI);
  pplm.query("ke_inlet_L", prob_parm->ke_inlet_L);

  pp.query("inlet_profile", prob_parm->inlet_profile);
  pp.query("inlet_channel_ylo", prob_parm->inlet_channel_ylo);
  pp.query("inlet_channel_yhi", prob_parm->inlet_channel_yhi);
  pp.query("inlet_power_law_exp", prob_parm->inlet_power_law_exp);
}

void
PeleLM::freeProbParm()
{
}
