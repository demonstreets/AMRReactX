#include "prob.H"
void pc_prob_close() {}
extern "C" {
void amrex_probinit(const int*,const int*,const int*,const amrex::Real*,const amrex::Real*) {
    amrex::ParmParse pp("prob");
    pp.query("rho_heavy", PeleC::h_prob_parm_device->rho_heavy);
    pp.query("rho_light", PeleC::h_prob_parm_device->rho_light);
    pp.query("p0", PeleC::h_prob_parm_device->p0);
    pp.query("bubble_cx", PeleC::h_prob_parm_device->bubble_cx);
    pp.query("bubble_cy", PeleC::h_prob_parm_device->bubble_cy);
    pp.query("bubble_r", PeleC::h_prob_parm_device->bubble_r);
    pp.query("interface_width", PeleC::h_prob_parm_device->interface_width);
    pp.query("gravity", PeleC::h_prob_parm_device->buoyancy_accel);
    pp.query("buoyancy_accel", PeleC::h_prob_parm_device->buoyancy_accel);
    pp.query("buoyancy_start_time", PeleC::h_prob_parm_device->buoyancy_start_time);
    pp.query("buoyancy_end_time", PeleC::h_prob_parm_device->buoyancy_end_time);
    pp.query("buoyancy_ramp_time", PeleC::h_prob_parm_device->buoyancy_ramp_time);
    pp.query("buoyancy_terminal_speed", PeleC::h_prob_parm_device->buoyancy_terminal_speed);
    pp.query("buoyancy_energy_correction", PeleC::h_prob_parm_device->buoyancy_energy_correction);
    pp.query("surface_tension_sigma", PeleC::h_prob_parm_device->surface_tension_sigma);
    pp.query("surface_tension_grad_floor", PeleC::h_prob_parm_device->surface_tension_grad_floor);
    pp.query("surface_tension_force_cap", PeleC::h_prob_parm_device->surface_tension_force_cap);
    pp.query("phase_viscosity_mu_heavy", PeleC::h_prob_parm_device->phase_viscosity_mu_heavy);
    pp.query("phase_viscosity_mu_light", PeleC::h_prob_parm_device->phase_viscosity_mu_light);
    pp.query("phase_viscosity_force_cap", PeleC::h_prob_parm_device->phase_viscosity_force_cap);
    pp.query("positivity_rhoe_floor", PeleC::h_prob_parm_device->positivity_rhoe_floor);
    pp.query("positivity_temp_floor", PeleC::h_prob_parm_device->positivity_temp_floor);
}}
void PeleC::problem_post_timestep()
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
      state, ngs, [=] AMREX_GPU_DEVICE(int nbx, int i, int j, int k)
                     noexcept {
                       amrex::Real rho = arrs[nbx](i, j, k, URHO);
                       if (!(rho > 1.0e-30)) {
                           rho = 1.0e-30;
                       }
                       const amrex::Real ux = arrs[nbx](i, j, k, UMX) / rho;
                       const amrex::Real uy = arrs[nbx](i, j, k, UMY) / rho;
                       const amrex::Real uz = arrs[nbx](i, j, k, UMZ) / rho;
                       const amrex::Real ke =
                         0.5 * rho * (ux * ux + uy * uy + uz * uz);
                       if (rhoe_floor > 0.0) {
                           if (!(arrs[nbx](i, j, k, UEINT) >= rhoe_floor)) {
                               arrs[nbx](i, j, k, UEINT) = rhoe_floor;
                           }
                           const amrex::Real eden_floor =
                             arrs[nbx](i, j, k, UEINT) + ke;
                           if (!(arrs[nbx](i, j, k, UEDEN) >= eden_floor)) {
                               arrs[nbx](i, j, k, UEDEN) = eden_floor;
                           }
                       }
                       if (temp_floor > 0.0) {
                           if (!(arrs[nbx](i, j, k, UTEMP) >= temp_floor)) {
                               arrs[nbx](i, j, k, UTEMP) = temp_floor;
                           }
                       }
                     });
    amrex::Gpu::synchronize();
}
void PeleC::problem_post_init() {}
void PeleC::problem_post_restart() {}
