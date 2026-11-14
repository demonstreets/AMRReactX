#include "prob.H"
void pc_prob_close() {}

void PeleC::problem_post_timestep() {}
void PeleC::problem_post_init() {}
void PeleC::problem_post_restart() {}

extern "C" {
void amrex_probinit(const int*,const int*,const int*,const amrex::Real*,const amrex::Real*) {
    amrex::ParmParse pp("prob");
    pp.query("rho_heavy", PeleC::h_prob_parm_device->rho_heavy);
    pp.query("rho_light", PeleC::h_prob_parm_device->rho_light);
    pp.query("p0", PeleC::h_prob_parm_device->p0);
    pp.query("gravity", PeleC::h_prob_parm_device->gravity);
    pp.query("pert_amp", PeleC::h_prob_parm_device->pert_amp);
    pp.query("pert_mode", PeleC::h_prob_parm_device->pert_mode);
}}
