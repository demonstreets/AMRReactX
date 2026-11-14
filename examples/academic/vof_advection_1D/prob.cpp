#include "prob.H"

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
  const amrex::Real* problo,
  const amrex::Real* probhi)
{
  // Parse params
  {
    amrex::ParmParse pp("prob");
    pp.query("rho0", PeleC::h_prob_parm_device->rho0);
    pp.query("u0", PeleC::h_prob_parm_device->u0);
    pp.query("p0", PeleC::h_prob_parm_device->p0);
    pp.query("T0", PeleC::h_prob_parm_device->T0);
    pp.query("alpha_lo", PeleC::h_prob_parm_device->alpha_lo);
    pp.query("alpha_hi", PeleC::h_prob_parm_device->alpha_hi);
  }
}
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
