#include <PeleLMeX.H>
#include <AMReX_ParmParse.H>

void
PeleLM::readProbParm() // NOLINT(readability-make-member-function-const)
{
  amrex::ParmParse pp("prob");
  pp.query("P_mean", prob_parm->P_mean);
  amrex::Vector<amrex::Real> bubble_center(AMREX_SPACEDIM);
  for (int d = 0; d < AMREX_SPACEDIM; ++d) {
    bubble_center[d] = prob_parm->bubble_center[d];
  }
  if (pp.queryarr("bubble_center", bubble_center, 0, AMREX_SPACEDIM) != 0) {
    for (int d = 0; d < AMREX_SPACEDIM; ++d) {
      prob_parm->bubble_center[d] = bubble_center[d];
    }
  }
  pp.query("bubble_radius", prob_parm->bubble_radius);
  pp.query("interface_thickness", prob_parm->interface_thickness);
  pp.query("u0", prob_parm->u0);
  pp.query("v0", prob_parm->v0);
  pp.query("surface_tension_sigma", prob_parm->surface_tension_sigma);
  pp.query("surface_tension_grad_floor", prob_parm->surface_tension_grad_floor);
  pp.query("surface_tension_force_cap", prob_parm->surface_tension_force_cap);
  pp.query("surface_tension_curvature_scheme", prob_parm->surface_tension_curvature_scheme);
  pp.query("surface_tension_force_form", prob_parm->surface_tension_force_form);
}

void
PeleLM::freeProbParm()
{
}
