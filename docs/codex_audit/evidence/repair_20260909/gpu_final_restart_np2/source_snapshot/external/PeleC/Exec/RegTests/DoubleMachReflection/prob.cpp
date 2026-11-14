#include "prob.H"
#include <cmath>

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
  // Parse problem parameters (allow override from inputs)
  amrex::ParmParse pp("prob");
  pp.query("shock_M", PeleC::h_prob_parm_device->shock_M);
  pp.query("gamma", PeleC::h_prob_parm_device->gamma);
  pp.query("shock_x0", PeleC::h_prob_parm_device->shock_x0);
  pp.query("rho_pre", PeleC::h_prob_parm_device->rho_pre);
  pp.query("p_pre", PeleC::h_prob_parm_device->p_pre);
  pp.query("u_pre", PeleC::h_prob_parm_device->u_pre);
  pp.query("v_pre", PeleC::h_prob_parm_device->v_pre);
  pp.query("wedge_start", PeleC::h_prob_parm_device->wedge_start);

  const amrex::Real M = PeleC::h_prob_parm_device->shock_M;
  const amrex::Real gm = PeleC::h_prob_parm_device->gamma;
  const amrex::Real rho_pre = PeleC::h_prob_parm_device->rho_pre;
  const amrex::Real p_pre = PeleC::h_prob_parm_device->p_pre;

  // Pre-shock sound speed
  PeleC::h_prob_parm_device->a_pre = std::sqrt(gm * p_pre / rho_pre);

  // Pre-shock internal energy
  PeleC::h_prob_parm_device->e_pre = p_pre / ((gm - 1.0) * rho_pre);
  PeleC::h_prob_parm_device->rhoe_pre =
    rho_pre * PeleC::h_prob_parm_device->e_pre;

  // Normal shock RH relations for post-shock state
  // rho_post/rho_pre = (gm+1)*M^2 / ((gm-1)*M^2 + 2)
  // p_post/p_pre = 1 + 2*gm/(gm+1) * (M^2 - 1)
  // v_n_post (lab) = a_pre * 2*(M^2-1) / ((gm+1)*M)
  const amrex::Real M2 = M * M;
  const amrex::Real rho_ratio =
    (gm + 1.0) * M2 / ((gm - 1.0) * M2 + 2.0);
  const amrex::Real p_ratio =
    1.0 + 2.0 * gm / (gm + 1.0) * (M2 - 1.0);
  const amrex::Real vn_post =
    PeleC::h_prob_parm_device->a_pre * 2.0 * (M2 - 1.0) /
    ((gm + 1.0) * M);

  PeleC::h_prob_parm_device->rho_post = rho_pre * rho_ratio;
  PeleC::h_prob_parm_device->p_post = p_pre * p_ratio;
  PeleC::h_prob_parm_device->vn_post = vn_post;

  // Post-shock internal energy
  PeleC::h_prob_parm_device->e_post =
    PeleC::h_prob_parm_device->p_post /
    ((gm - 1.0) * PeleC::h_prob_parm_device->rho_post);
  PeleC::h_prob_parm_device->rhoe_post =
    PeleC::h_prob_parm_device->rho_post *
    PeleC::h_prob_parm_device->e_post;

  // Post-shock sound speed
  PeleC::h_prob_parm_device->a_post =
    std::sqrt(gm * PeleC::h_prob_parm_device->p_post /
              PeleC::h_prob_parm_device->rho_post);

  // Shock geometry: 60 degree shock
  // Shock line: x = shock_x0 + y / tan(60°) = shock_x0 + y/sqrt(3)
  // Normal (pointing from post to pre): (sqrt(3)/2, -1/2)
  const amrex::Real angle_rad = PeleC::h_prob_parm_device->shock_angle *
                                M_PI / 180.0;
  PeleC::h_prob_parm_device->shock_tan = std::tan(angle_rad);
  PeleC::h_prob_parm_device->shock_nx = std::cos(M_PI / 6.0); // cos(30°)
  PeleC::h_prob_parm_device->shock_ny = -std::sin(M_PI / 6.0); // -sin(30°)

  // Post-shock velocity vector (lab frame)
  PeleC::h_prob_parm_device->u_post =
    vn_post * PeleC::h_prob_parm_device->shock_nx;
  PeleC::h_prob_parm_device->v_post =
    vn_post * PeleC::h_prob_parm_device->shock_ny;

  // Shock speed in lab frame
  // Shock front equation: n·(r - r0) = M*a_pre*t
  // Solve for x:  x = shock_x0 + y/tan(angle) + (M*a_pre / nx) * t
  // Solve for y:  y = tan(angle)*(x - shock_x0) + (M*a_pre / ny) * t
  // nx = cos(30°) = √3/2,  ny = -sin(30°) = -1/2
  PeleC::h_prob_parm_device->shock_speed_x =
    M * PeleC::h_prob_parm_device->a_pre /
    PeleC::h_prob_parm_device->shock_nx;
  PeleC::h_prob_parm_device->shock_speed_y =
    M * PeleC::h_prob_parm_device->a_pre /
    PeleC::h_prob_parm_device->shock_ny;

  // Store y-hi for bcnormal
  PeleC::h_prob_parm_device->y_hi = probhi[1];

  // Verify computed mass fractions for single-species GammaLaw
  amrex::Real massfrac[NUM_SPECIES] = {0.0};
  massfrac[0] = 1.0;

  auto eos = pele::physics::PhysicsType::eos();
  amrex::Real e_check, T_check;

  // Verify pre-shock state consistently through EOS
  eos.RYP2E(
    PeleC::h_prob_parm_device->rho_pre, massfrac,
    PeleC::h_prob_parm_device->p_pre, e_check);
  eos.EY2T(e_check, massfrac, T_check);

  // Verify post-shock state
  eos.RYP2E(
    PeleC::h_prob_parm_device->rho_post, massfrac,
    PeleC::h_prob_parm_device->p_post, e_check);
  eos.EY2T(e_check, massfrac, T_check);
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
