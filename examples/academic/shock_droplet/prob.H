#ifndef PROB_H
#define PROB_H

#include <AMReX_Print.H>
#include <AMReX_ParmParse.H>
#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>

#include "mechanism.H"

// Explicit supported mechanism mappings. Lu's 88-species mechanism uses
// lowercase generated identifiers; the transport-only 3-species model uses
// uppercase. Never infer species indices from their order in a mechanism.
#if defined(nc7h16_ID) && defined(o2_ID) && defined(n2_ID)
constexpr int shock_heptane_id = nc7h16_ID;
constexpr int shock_oxygen_id = o2_ID;
constexpr int shock_nitrogen_id = n2_ID;
#elif defined(NC7H16_ID) && defined(O2_ID) && defined(N2_ID)
constexpr int shock_heptane_id = NC7H16_ID;
constexpr int shock_oxygen_id = O2_ID;
constexpr int shock_nitrogen_id = N2_ID;
#else
#error "shock_droplet requires an explicit n-heptane/O2/N2 mechanism mapping"
#endif


#include "IndexDefines.H"
#include "Constants.H"
#include "PelePhysics.H"
#include "Tagging.H"
#include "ProblemSpecificFunctions.H"
#include "prob_parm.H"

AMREX_GPU_DEVICE
AMREX_FORCE_INLINE
void
pc_initdata(
  int i,
  int j,
  int k,
  amrex::Array4<amrex::Real> const& state,
  amrex::GeometryData const& geomdata,
  ProbParmDevice const& prob_parm)
{
  const amrex::Real* prob_lo = geomdata.ProbLo();
  const amrex::Real* dx = geomdata.CellSize();
  const amrex::Real x = prob_lo[0] + (i + 0.5) * dx[0];

  // Shock tube: left = driver, right = driven
  const bool left_side = (x < prob_parm.diaphragm);
  const amrex::Real p = left_side ? prob_parm.p_left : prob_parm.p_right;
  const amrex::Real T = left_side ? prob_parm.T_left : prob_parm.T_right;

  // Mass fractions: air with optional heptane vapor for reacting spray gates.
  amrex::Real massfrac[NUM_SPECIES] = {0.0};
  massfrac[shock_heptane_id] = prob_parm.Y_NC7H16;
  massfrac[shock_oxygen_id] = prob_parm.Y_O2;
  massfrac[shock_nitrogen_id] = prob_parm.Y_N2;

  auto eos = pele::physics::PhysicsType::eos();
  amrex::Real rho, eint;
  eos.PYT2RE(p, massfrac, T, rho, eint);

  // Zero velocity initially everywhere
  amrex::Real u = 0.0;

  // Set conservative state
  state(i, j, k, URHO) = rho;
  state(i, j, k, UMX) = rho * u;
  state(i, j, k, UMY) = 0.0;
  state(i, j, k, UMZ) = 0.0;
  state(i, j, k, UEINT) = rho * eint;
  state(i, j, k, UEDEN) = rho * (eint + 0.5 * u * u);
  state(i, j, k, UTEMP) = T;
  for (int n = 0; n < NUM_SPECIES; n++) {
    state(i, j, k, UFS + n) = rho * massfrac[n];
  }
}

AMREX_GPU_DEVICE
AMREX_FORCE_INLINE
void
bcnormal(
  const amrex::Real* /*x*/,
  const amrex::Real s_int[NVAR],
  amrex::Real s_ext[NVAR],
  const int /*idir*/,
  const int /*sgn*/,
  const amrex::Real /*time*/,
  amrex::GeometryData const& /*geomdata*/,
  ProbParmDevice const& /*prob_parm*/,
  const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& /*turb_fluc*/)
{
  // Copy interior to boundary (FOExtrap)
  for (int n = 0; n < NVAR; n++) {
    s_ext[n] = s_int[n];
  }
}

void pc_prob_close();

using ProblemSpecificFunctions = DefaultProblemSpecificFunctions;

#endif
