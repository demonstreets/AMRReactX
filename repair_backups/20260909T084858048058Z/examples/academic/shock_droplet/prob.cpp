#include "prob.H"

extern "C" {
void
amrex_probinit(
  const int* /*init*/,
  const int* /*name*/,
  const int* /*namelen*/,
  const amrex_real* /*problo*/,
  const amrex_real* /*probhi*/)
{
  amrex::ParmParse pp("prob");

  pp.query("p_left", PeleC::h_prob_parm_device->p_left);
  pp.query("T_left", PeleC::h_prob_parm_device->T_left);
  pp.query("p_right", PeleC::h_prob_parm_device->p_right);
  pp.query("T_right", PeleC::h_prob_parm_device->T_right);
  pp.query("diaphragm", PeleC::h_prob_parm_device->diaphragm);

  pp.query("Y_O2", PeleC::h_prob_parm_device->Y_O2);
  pp.query("Y_N2", PeleC::h_prob_parm_device->Y_N2);
  pp.query("Y_NC7H16", PeleC::h_prob_parm_device->Y_NC7H16);
}
}

void
pc_prob_close()
{
}

void
PeleC::problem_post_timestep()
{
}

void
PeleC::problem_post_init()
{
}

void
PeleC::problem_post_restart()
{
}
