#include <cmath>
#include "prob.H"

void pc_prob_close() {}

extern "C" {
void amrex_probinit(
  const int* /*init*/, const int* /*name*/, const int* /*namelen*/,
  const amrex::Real* problo, const amrex::Real* probhi)
{
  amrex::ParmParse pp("prob");
  pp.query("p_r", PeleC::h_prob_parm_device->p_r);
  pp.query("T_r", PeleC::h_prob_parm_device->T_r);
  pp.query("rho_r", PeleC::h_prob_parm_device->rho_r);
  pp.query("p_l", PeleC::h_prob_parm_device->p_l);
  pp.query("T_l", PeleC::h_prob_parm_device->T_l);
  pp.query("x_split", PeleC::h_prob_parm_device->x_split);
  pp.query("A_per", PeleC::h_prob_parm_device->A_per);
  pp.query("lambda", PeleC::h_prob_parm_device->lambda);
  // Backward compat: also read legacy p_0 / T_0 as overrides for p_r / T_r
  pp.query("p_0", PeleC::h_prob_parm_device->p_r);
  pp.query("T_0", PeleC::h_prob_parm_device->T_r);

  auto eos = pele::physics::PhysicsType::eos();

  // Right state: stoichiometric H2/O2/N2 mixture
  amrex::Real mf_r[NUM_SPECIES] = {0.0};
  mf_r[H2_ID] = 0.0285;
  mf_r[O2_ID] = 0.228;
  mf_r[N2_ID] = 0.7435;
  for (int n = 0; n < NUM_SPECIES; n++)
    PeleC::h_prob_parm_device->massfrac_r[n] = mf_r[n];

  // Left state: CJ products (mostly H2O)
  amrex::Real mf_l[NUM_SPECIES] = {0.0};
  mf_l[H2O_ID] = 1.0;
  for (int n = 0; n < NUM_SPECIES; n++)
    PeleC::h_prob_parm_device->massfrac_l[n] = mf_l[n];

  // Compute rho_r = PYT2R(p_r, mf_r, T_r)
  eos.PYT2R(PeleC::h_prob_parm_device->p_r, mf_r,
            PeleC::h_prob_parm_device->T_r,
            PeleC::h_prob_parm_device->rho_r);

  // Compute rho_l = PYT2R(p_l, mf_l, T_l)
  eos.PYT2R(PeleC::h_prob_parm_device->p_l, mf_l,
            PeleC::h_prob_parm_device->T_l,
            PeleC::h_prob_parm_device->rho_l);

  // Log
  if (amrex::ParallelDescriptor::IOProcessor()) {
    std::ofstream ofs("ic.txt", std::ofstream::out);
    amrex::Print(ofs).SetPrecision(6);
    amrex::Print(ofs) << "=== ZND Riemann IC ===" << std::endl;
    amrex::Print(ofs) << "Right (unburned): p=" << PeleC::h_prob_parm_device->p_r
      << " T=" << PeleC::h_prob_parm_device->T_r
      << " rho=" << PeleC::h_prob_parm_device->rho_r
      << " Y_H2=" << mf_r[H2_ID] << " Y_O2=" << mf_r[O2_ID]
      << " Y_N2=" << mf_r[N2_ID] << std::endl;
    amrex::Print(ofs) << "Left (CJ products): p=" << PeleC::h_prob_parm_device->p_l
      << " T=" << PeleC::h_prob_parm_device->T_l
      << " rho=" << PeleC::h_prob_parm_device->rho_l
      << " Y_H2O=" << mf_l[H2O_ID] << std::endl;
    amrex::Print(ofs) << "x_split=" << PeleC::h_prob_parm_device->x_split
      << " A_per=" << PeleC::h_prob_parm_device->A_per
      << " lambda=" << PeleC::h_prob_parm_device->lambda << std::endl;
    ofs.close();
  }
}
}

void PeleC::problem_post_timestep() {}
void PeleC::problem_post_init() {}
void PeleC::problem_post_restart() {}
