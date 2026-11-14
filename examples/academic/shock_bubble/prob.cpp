#include "prob.H"

void pc_prob_close() {}

extern "C" {
void
amrex_probinit(
  const int*,
  const int*,
  const int*,
  const amrex::Real*,
  const amrex::Real*)
{
  amrex::ParmParse pp("prob");
  pp.query("T_heavy", PeleC::h_prob_parm_device->T_heavy);
  pp.query("T_light", PeleC::h_prob_parm_device->T_light);
  pp.query("p_left", PeleC::h_prob_parm_device->p_left);
  pp.query("p_right", PeleC::h_prob_parm_device->p_right);
  pp.query("shock_x", PeleC::h_prob_parm_device->shock_x);
  pp.query("driver_u", PeleC::h_prob_parm_device->driver_u);
  pp.query("bubble_cx", PeleC::h_prob_parm_device->bubble_cx);
  pp.query("bubble_cy", PeleC::h_prob_parm_device->bubble_cy);
  pp.query("bubble_r", PeleC::h_prob_parm_device->bubble_r);
  pp.query("interface_width", PeleC::h_prob_parm_device->interface_width);
  pp.query("positivity_rhoe_floor", PeleC::h_prob_parm_device->positivity_rhoe_floor);
  pp.query("positivity_temp_floor", PeleC::h_prob_parm_device->positivity_temp_floor);
}
}

void
PeleC::problem_post_timestep()
{
  const amrex::Real rhoe_floor = PeleC::h_prob_parm_device->positivity_rhoe_floor;
  const amrex::Real temp_floor = PeleC::h_prob_parm_device->positivity_temp_floor;
  if (rhoe_floor <= 0.0 && temp_floor <= 0.0) {
    return;
  }

  amrex::MultiFab& state = get_new_data(State_Type);
  auto const& arrs = state.arrays();
  const amrex::IntVect ngs(0);
  amrex::ParallelFor(
    state, ngs, [=] AMREX_GPU_DEVICE(int nbx, int i, int j, int k) noexcept {
      amrex::Real rho = arrs[nbx](i, j, k, URHO);
      if (!(rho > 1.0e-30)) {
        rho = 1.0e-30;
      }
      const amrex::Real ux = arrs[nbx](i, j, k, UMX) / rho;
      const amrex::Real uy = arrs[nbx](i, j, k, UMY) / rho;
      const amrex::Real uz = arrs[nbx](i, j, k, UMZ) / rho;
      const amrex::Real ke = 0.5 * rho * (ux * ux + uy * uy + uz * uz);
      if (rhoe_floor > 0.0 && !(arrs[nbx](i, j, k, UEINT) >= rhoe_floor)) {
        arrs[nbx](i, j, k, UEINT) = rhoe_floor;
      }
      const amrex::Real eden_floor = arrs[nbx](i, j, k, UEINT) + ke;
      if (rhoe_floor > 0.0 && !(arrs[nbx](i, j, k, UEDEN) >= eden_floor)) {
        arrs[nbx](i, j, k, UEDEN) = eden_floor;
      }
      amrex::Real massfrac[NUM_SPECIES] = {0.0};
      for (int n = 0; n < NUM_SPECIES; n++) {
        massfrac[n] = arrs[nbx](i, j, k, UFS + n) / rho;
      }
      auto eos = pele::physics::PhysicsType::eos();
      amrex::Real T = temp_floor;
      eos.REY2T(rho, arrs[nbx](i, j, k, UEINT) / rho, massfrac, T);
      if (T > temp_floor) {
        arrs[nbx](i, j, k, UTEMP) = T;
      } else if (temp_floor > 0.0) {
        arrs[nbx](i, j, k, UTEMP) = temp_floor;
      }
    });
  amrex::Gpu::synchronize();
}

void PeleC::problem_post_init() {}
void PeleC::problem_post_restart() {}
