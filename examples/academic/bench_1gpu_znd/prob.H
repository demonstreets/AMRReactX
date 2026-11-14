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

  // Riemann partition: left (x < x_split) = CJ products, right = unburned
  const bool left_side = (x < prob_parm.x_split);

  const amrex::Real rho = left_side ? prob_parm.rho_l : prob_parm.rho_r;
  amrex::Real T = left_side ? prob_parm.T_l : prob_parm.T_r;
  const amrex::Real p = left_side ? prob_parm.p_l : prob_parm.p_r;

  // Sine perturbation on temperature (instability trigger)
  T *= (1.0 + prob_parm.A_per *
        std::sin(2.0 * M_PI * y / prob_parm.lambda));

  // Write conserved state
  state(i, j, k, URHO) = rho;
  state(i, j, k, UMX) = 0.0;
  state(i, j, k, UMY) = 0.0;
  state(i, j, k, UMZ) = 0.0;
  state(i, j, k, UTEMP) = T;

  // Species: rho * Y
  for (int n = 0; n < NUM_SPECIES; n++) {
    state(i, j, k, UFS + n) =
      rho * (left_side ? prob_parm.massfrac_l[n] : prob_parm.massfrac_r[n]);
  }

  // Internal energy from EOS: RYP2E
  auto eos = pele::physics::PhysicsType::eos();
  amrex::Real e;
  // Build a local non-const mf for EOS call
  amrex::Real mf_local[NUM_SPECIES];
  for (int n = 0; n < NUM_SPECIES; n++) {
    mf_local[n] = left_side ? prob_parm.massfrac_l[n] : prob_parm.massfrac_r[n];
  }
  eos.RYP2E(rho, mf_local, p, e);

  state(i, j, k, UEINT) = rho * e;
  state(i, j, k, UEDEN) = rho * e; // zero kinetic energy
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
