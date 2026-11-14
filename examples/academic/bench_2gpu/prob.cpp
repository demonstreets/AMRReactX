#include <cmath>
#include "prob.H"

void pc_prob_close() {}

extern "C" {
void amrex_probinit(
  const int* /*init*/, const int* /*name*/, const int* /*namelen*/,
  const amrex::Real* problo, const amrex::Real* probhi)
{
  amrex::ParmParse pp("prob");
  auto& prm = *PeleC::h_prob_parm_device;
  const amrex::Real height = probhi[1] - problo[1];
  const amrex::Real fractions[4] = {0.15, 0.35, 0.55, 0.80};
  amrex::Vector<amrex::Real> positions(4);
  for (int n = 0; n < 4; ++n) positions[n] = problo[1] + fractions[n] * height;
  pp.queryarr("y_hot", positions);
  if (positions.size() != 4 || !std::isfinite(height) || height <= 0.0) {
    amrex::Abort("prob.y_hot must contain four absolute y coordinates in a positive-height domain");
  }
  for (int n = 0; n < 4; ++n) {
    if (!std::isfinite(positions[n]) || positions[n] < problo[1] || positions[n] > probhi[1]) {
      amrex::Abort("prob.y_hot lies outside the domain; refusing an empty hotspot initialization");
    }
    prm.y_hot[n] = positions[n];
  }
  prm.r_hot = 0.03 * height; // cm; follows the original 0.3 cm in a 10 cm domain

  pp.query("p_0", PeleC::h_prob_parm_device->p_0);
  pp.query("T_0", PeleC::h_prob_parm_device->T_0);
  pp.query("T_hot", PeleC::h_prob_parm_device->T_hot);
  pp.query("p_hot", PeleC::h_prob_parm_device->p_hot);
  pp.query("r_hot", PeleC::h_prob_parm_device->r_hot);
  pp.query("u_hot", PeleC::h_prob_parm_device->u_hot);
  if (!std::isfinite(prm.r_hot) || prm.r_hot <= 0.0 ||
      !std::isfinite(prm.p_0) || prm.p_0 <= 0.0 ||
      !std::isfinite(prm.p_hot) || prm.p_hot <= 0.0 ||
      !std::isfinite(prm.T_0) || prm.T_0 <= 0.0 ||
      !std::isfinite(prm.T_hot) || prm.T_hot <= prm.T_0 ||
      !std::isfinite(prm.u_hot)) {
    amrex::Abort("invalid hotspot state: require finite positive p, T, radius and T_hot > T_0 (CGS units)");
  }

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
  // MultiFab reduction performs the GPU and MPI reduction. Checking the
  // initialized cells catches a radius smaller than the first cell center.
  const auto& state = get_new_data(State_Type);
  const amrex::Real tmax = state.max(UTEMP);
  const amrex::Real background = h_prob_parm_device->T_0;
  if (!std::isfinite(tmax) || tmax <= background + 1.0e-6) {
    amrex::Abort("hotspot initialized zero resolved hot cells; check radius and grid spacing");
  }
  amrex::Print() << "Resolved hotspot initial temperature max = " << tmax << " K\n";
}
void PeleC::problem_post_restart() {}
