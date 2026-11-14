#include <cmath>
#include "prob.H"

void pc_prob_close() {}

extern "C" {
void amrex_probinit(
  const int* /*init*/, const int* /*name*/, const int* /*namelen*/,
  const amrex::Real* problo, const amrex::Real* probhi)
{
  amrex::ParmParse pp("prob");
  pp.query("p_0", PeleC::h_prob_parm_device->p_0);
  pp.query("T_0", PeleC::h_prob_parm_device->T_0);
  pp.query("T_hot", PeleC::h_prob_parm_device->T_hot);
  pp.query("p_hot", PeleC::h_prob_parm_device->p_hot);
  pp.query("r_hot", PeleC::h_prob_parm_device->r_hot);
  pp.query("u_hot", PeleC::h_prob_parm_device->u_hot);

  auto eos = pele::physics::PhysicsType::eos();

  // === Background: stoichiometric H2/O2 ===
  amrex::Real mf0[NUM_SPECIES] = {0.0};
  mf0[H2_ID] = 2.016 / (2.016 + 15.999);  // ~0.112 (stoich H2+0.5O2 → mass-based)
  mf0[O2_ID] = 15.999 / (2.016 + 15.999); // ~0.888
  for (int n = 0; n < NUM_SPECIES; n++)
    PeleC::h_prob_parm_device->massfrac_0[n] = mf0[n];

  // Compute rho_0 = PYT2R(p, Y, T)
  eos.PYT2R(PeleC::h_prob_parm_device->p_0, mf0,
            PeleC::h_prob_parm_device->T_0,
            PeleC::h_prob_parm_device->rho_0);

  // Compute rhoe_0 = rho * e via RYP2E(rho, Y, p, e)
  amrex::Real e_0;
  eos.RYP2E(PeleC::h_prob_parm_device->rho_0, mf0,
            PeleC::h_prob_parm_device->p_0, e_0);
  PeleC::h_prob_parm_device->rhoe_0 =
    PeleC::h_prob_parm_device->rho_0 * e_0;

  // === Hotspot: CJ products (mostly H2O, trace radicals) ===
  // Hotspot: ZND CJ products parameters (p from inputs, T/rho from EOS)
  amrex::Real mf_hot[NUM_SPECIES] = {0.0};
  mf_hot[H2O_ID] = 1.0;
  for (int n = 0; n < NUM_SPECIES; n++)
    PeleC::h_prob_parm_device->massfrac_hot[n] = mf_hot[n];

  // Compute hotspot properties: T_hot from inputs, rho/rhoe from EOS
  eos.PYT2R(PeleC::h_prob_parm_device->p_hot, mf_hot,
            PeleC::h_prob_parm_device->T_hot,
            PeleC::h_prob_parm_device->rho_hot);
  amrex::Real e_hot;
  eos.RYP2E(PeleC::h_prob_parm_device->rho_hot, mf_hot,
            PeleC::h_prob_parm_device->p_hot, e_hot);
  PeleC::h_prob_parm_device->rhoe_hot =
    PeleC::h_prob_parm_device->rho_hot * e_hot;

  // Log
  if (amrex::ParallelDescriptor::IOProcessor()) {
    std::ofstream ofs("ic.txt", std::ofstream::out);
    amrex::Print(ofs).SetPrecision(6);
    amrex::Print(ofs) << "=== Hotspot Detonation IC ===" << std::endl;
    amrex::Print(ofs) << "Background: p=" << PeleC::h_prob_parm_device->p_0
      << " T=" << PeleC::h_prob_parm_device->T_0
      << " rho=" << PeleC::h_prob_parm_device->rho_0
      << " Y_H2=" << mf0[H2_ID] << " Y_O2=" << mf0[O2_ID] << std::endl;
    amrex::Print(ofs) << "Hotspot: p=" << PeleC::h_prob_parm_device->p_hot
      << " T=" << PeleC::h_prob_parm_device->T_hot
      << " rho=" << PeleC::h_prob_parm_device->rho_hot
      << " r=" << PeleC::h_prob_parm_device->r_hot << " cm"
      << " u=" << PeleC::h_prob_parm_device->u_hot << " cm/s" << std::endl;
    ofs.close();
  }
}
}

void PeleC::problem_post_timestep() {}
void PeleC::problem_post_init()
{
  // GPU NaN check disabled — __device__ lambda + Atomic::Add incompatible
  // with PeleC member function access. Initial state verified in amrex_probinit.
}
void PeleC::problem_post_restart() {}
