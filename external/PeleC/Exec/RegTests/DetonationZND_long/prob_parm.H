#ifndef PROB_PARM_H
#define PROB_PARM_H

#include <AMReX_REAL.H>
#include <AMReX_GpuQualifiers.H>

struct ProbParmDevice
{
  // Left state (CJ equilibrium products)
  amrex::Real rho_l = 2.4e-3;   // g/cm^3
  amrex::Real p_l = 1.8e7;      // dyn/cm^2
  amrex::Real T_l = 0.0;        // K — computed by EY2T from (rho_l, p_l, Y); ~2214 K
  amrex::Real rhoe_l;           // computed in amrex_probinit

  // Right state (stoichiometric H2/air, unburned)
  amrex::Real rho_r = 8.5e-4;   // g/cm^3 (~ stoichiometric H2/air @ 300 K / 1 atm)
  amrex::Real p_r = 1.013e6;    // dyn/cm^2 (~1 atm)
  amrex::Real T_r = 300.0;      // K
  amrex::Real rhoe_r;            // computed in amrex_probinit

  // Interface position (cm from prob_lo)
  amrex::Real x_split = 0.1;

  // Mass fractions (LiDryer order: H2 O2 H2O H O OH HO2 H2O2 N2)
  amrex::Real massfrac_L[9]; // CJ products (mostly H2O + N2)
  amrex::Real massfrac_R[9]; // Unburned H2/air
};

struct ProbParmHost
{
  ProbParmHost() = default;
};
#endif
