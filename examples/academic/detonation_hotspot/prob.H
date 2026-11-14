#ifndef PROB_H
#define PROB_H

#include <AMReX_Print.H>
#include <AMReX_ParmParse.H>
#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>
#include <AMReX_REAL.H>
#include <AMReX_GpuMemory.H>

#include "mechanism.H"
#include "PeleC.H"
#include "IndexDefines.H"
#include "Constants.H"
#include "PelePhysics.H"
#include "Tagging.H"
#include "ProblemSpecificFunctions.H"
#include "prob_parm.H"

AMREX_GPU_DEVICE
AMREX_FORCE_INLINE
void pc_initdata(
  int i, int j, int k,
  amrex::Array4<amrex::Real> const& state,
  amrex::GeometryData const& geomdata,
  ProbParmDevice const& prob_parm)
{
  const amrex::Real* prob_lo = geomdata.ProbLo();
  const amrex::Real* dx = geomdata.CellSize();
  const amrex::Real x = prob_lo[0] + (i + 0.5) * dx[0];
  const amrex::Real y = prob_lo[1] + (j + 0.5) * dx[1];

  // Check distance to each hotspot (hotspots at x=0, various y)
  bool in_hotspot = false;
  for (int n = 0; n < prob_parm.n_hot; n++) {
    amrex::Real dy = y - prob_parm.y_hot[n];
    amrex::Real dist = std::sqrt((x-0.0)*(x-0.0) + dy*dy);
    if (dist <= prob_parm.r_hot) {
      in_hotspot = true;
      break;
    }
  }

  if (in_hotspot) {
    state(i,j,k,URHO)  = prob_parm.rho_hot;
    state(i,j,k,UMX)   = prob_parm.rho_hot * prob_parm.u_hot;
    state(i,j,k,UMY)   = 0.0;
    state(i,j,k,UMZ)   = 0.0;
    state(i,j,k,UEINT) = prob_parm.rhoe_hot;
    amrex::Real ke_hot = 0.5 * prob_parm.rho_hot * prob_parm.u_hot * prob_parm.u_hot;
    state(i,j,k,UEDEN) = prob_parm.rhoe_hot + ke_hot;
    state(i,j,k,UTEMP) = prob_parm.T_hot;
    for (int n = 0; n < NUM_SPECIES; n++)
      state(i,j,k,UFS+n) = prob_parm.rho_hot * prob_parm.massfrac_hot[n];
  } else {
    state(i,j,k,URHO)  = prob_parm.rho_0;
    state(i,j,k,UMX)   = 0.0;
    state(i,j,k,UMY)   = 0.0;
    state(i,j,k,UMZ)   = 0.0;
    state(i,j,k,UEINT) = prob_parm.rhoe_0;
    state(i,j,k,UEDEN) = prob_parm.rhoe_0;
    state(i,j,k,UTEMP) = prob_parm.T_0;
    for (int n = 0; n < NUM_SPECIES; n++)
      state(i,j,k,UFS+n) = prob_parm.rho_0 * prob_parm.massfrac_0[n];
  }
}

AMREX_GPU_DEVICE
AMREX_FORCE_INLINE
void bcnormal(
  const amrex::Real* x,
  const amrex::Real s_int[NVAR],
  amrex::Real s_ext[NVAR],
  const int idir, const int sgn,
  const amrex::Real time,
  amrex::GeometryData const& geomdata,
  ProbParmDevice const& prob_parm,
  const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& turb_fluc)
{
  for (int n = 0; n < NVAR; n++) s_ext[n] = s_int[n];
  // No-slip wall: x-lo (idir=0, sgn=-1), y-lo/hi (idir=1)
  if ((idir == 0 && sgn == -1) || idir == 1) {
    s_ext[UMX] = 0.0; s_ext[UMY] = 0.0; s_ext[UMZ] = 0.0;
    s_ext[UEDEN] = s_ext[UEINT];
  }
}

void pc_prob_close();
using ProblemSpecificFunctions = DefaultProblemSpecificFunctions;

#endif
