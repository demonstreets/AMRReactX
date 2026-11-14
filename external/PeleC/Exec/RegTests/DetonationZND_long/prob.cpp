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
  amrex::ParmParse pp("prob");
  pp.query("rho_l", PeleC::h_prob_parm_device->rho_l);
  pp.query("p_l", PeleC::h_prob_parm_device->p_l);
  pp.query("T_l", PeleC::h_prob_parm_device->T_l);
  pp.query("rho_r", PeleC::h_prob_parm_device->rho_r);
  pp.query("p_r", PeleC::h_prob_parm_device->p_r);
  pp.query("T_r", PeleC::h_prob_parm_device->T_r);
  pp.query("x_split", PeleC::h_prob_parm_device->x_split);

  auto eos = pele::physics::PhysicsType::eos();

  // Set mass fractions for left state (CJ equilibrium products)
  // LiDryer order: H2(0) O2(1) H2O(2) H(3) O(4) OH(5) HO2(6) H2O2(7) N2(8)
  amrex::Real massfrac_L[NUM_SPECIES] = {0.0};
  massfrac_L[H2O_ID] = 0.255;
  massfrac_L[N2_ID] = 0.745;
  for (int n = 0; n < NUM_SPECIES; n++) {
    PeleC::h_prob_parm_device->massfrac_L[n] = massfrac_L[n];
  }

  // Compute left internal energy from rho, Y, p
  amrex::Real e_l;
  eos.RYP2E(
    PeleC::h_prob_parm_device->rho_l, massfrac_L,
    PeleC::h_prob_parm_device->p_l, e_l);
  eos.EY2T(e_l, massfrac_L, PeleC::h_prob_parm_device->T_l);
  PeleC::h_prob_parm_device->rhoe_l =
    PeleC::h_prob_parm_device->rho_l * e_l;

  // Set mass fractions for right state (stoichiometric H2/air)
  amrex::Real massfrac_R[NUM_SPECIES] = {0.0};
  massfrac_R[H2_ID] = 0.0283;
  massfrac_R[O2_ID] = 0.2264;
  massfrac_R[N2_ID] = 0.7453;
  for (int n = 0; n < NUM_SPECIES; n++) {
    PeleC::h_prob_parm_device->massfrac_R[n] = massfrac_R[n];
  }

  // Compute right internal energy from rho, Y, p
  amrex::Real e_r;
  eos.RYP2E(
    PeleC::h_prob_parm_device->rho_r, massfrac_R,
    PeleC::h_prob_parm_device->p_r, e_r);
  eos.EY2T(e_r, massfrac_R, PeleC::h_prob_parm_device->T_r);
  PeleC::h_prob_parm_device->rhoe_r =
    PeleC::h_prob_parm_device->rho_r * e_r;

  // Write IC to file
  if (amrex::ParallelDescriptor::IOProcessor()) {
    std::ofstream ofs("ic.txt", std::ofstream::out);
    amrex::Print(ofs) << "ZND Detonation Initial Condition" << std::endl;
    amrex::Print(ofs) << "Left (CJ products): rho="
                      << PeleC::h_prob_parm_device->rho_l
                      << " p=" << PeleC::h_prob_parm_device->p_l
                      << " T=" << PeleC::h_prob_parm_device->T_l
                      << " eint=" << e_l << std::endl;
    amrex::Print(ofs) << "Right (H2/air): rho="
                      << PeleC::h_prob_parm_device->rho_r
                      << " p=" << PeleC::h_prob_parm_device->p_r
                      << " T=" << PeleC::h_prob_parm_device->T_r
                      << " eint=" << e_r << std::endl;
    amrex::Print(ofs) << "x_split=" << PeleC::h_prob_parm_device->x_split
                      << std::endl;
    ofs.close();
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
