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
  // Parse vortex params (allow override from inputs)
  amrex::ParmParse pp("prob");
  pp.query("vortex_eps", PeleC::h_prob_parm_device->vortex_eps);
  pp.query("vortex_R", PeleC::h_prob_parm_device->vortex_R);
  pp.query("center_x", PeleC::h_prob_parm_device->center_x);
  pp.query("center_y", PeleC::h_prob_parm_device->center_y);
  pp.query("rho_bg", PeleC::h_prob_parm_device->rho_bg);
  pp.query("u_bg", PeleC::h_prob_parm_device->u_bg);
  pp.query("v_bg", PeleC::h_prob_parm_device->v_bg);
  pp.query("p_bg", PeleC::h_prob_parm_device->p_bg);

  amrex::Real massfrac[NUM_SPECIES] = {0.0};
  massfrac[0] = 1.0;

  // Compute background internal energy and temperature from EOS
  auto eos = pele::physics::PhysicsType::eos();
  amrex::Real e_bg;
  eos.RYP2E(
    PeleC::h_prob_parm_device->rho_bg, massfrac,
    PeleC::h_prob_parm_device->p_bg, e_bg);
  PeleC::h_prob_parm_device->rhoe_bg =
    PeleC::h_prob_parm_device->rho_bg * e_bg;
  eos.EY2T(e_bg, massfrac, PeleC::h_prob_parm_device->T_bg);

  amrex::Print() << "=== IsentropicVortex probinit ===" << std::endl;
  amrex::Print() << "  vortex_eps = "
                 << PeleC::h_prob_parm_device->vortex_eps << std::endl;
  amrex::Print() << "  vortex_R   = "
                 << PeleC::h_prob_parm_device->vortex_R << std::endl;
  amrex::Print() << "  center_x   = "
                 << PeleC::h_prob_parm_device->center_x << std::endl;
  amrex::Print() << "  center_y   = "
                 << PeleC::h_prob_parm_device->center_y << std::endl;
  amrex::Print() << "  rho_bg     = "
                 << PeleC::h_prob_parm_device->rho_bg << std::endl;
  amrex::Print() << "  u_bg       = "
                 << PeleC::h_prob_parm_device->u_bg << std::endl;
  amrex::Print() << "  v_bg       = "
                 << PeleC::h_prob_parm_device->v_bg << std::endl;
  amrex::Print() << "  p_bg       = "
                 << PeleC::h_prob_parm_device->p_bg << std::endl;
  amrex::Print() << "  T_bg       = "
                 << PeleC::h_prob_parm_device->T_bg << std::endl;
  amrex::Print() << "  rhoe_bg    = "
                 << PeleC::h_prob_parm_device->rhoe_bg << std::endl;
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
