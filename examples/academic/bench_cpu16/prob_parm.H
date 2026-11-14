#ifndef PROB_PARM_H
#define PROB_PARM_H
#include <AMReX_REAL.H>
#include <AMReX_GpuQualifiers.H>

struct ProbParmDevice
{
  // === Background (unburned stoichiometric H2/O2) ===
  amrex::Real p_0 = 2.0e5;   // Pa
  amrex::Real T_0 = 300.0;   // K
  amrex::Real rho_0;          // computed: PYT2R(p_0, Y_0, T_0)
  amrex::Real rhoe_0;         // computed: rho_0 * e_0 via RYP2E

  // === Hotspot (CJ products) ===
  amrex::Real T_hot = 3000.0; // K
  amrex::Real p_hot = 2.0e6;  // Pa
  amrex::Real r_hot = 0.3;    // cm
  amrex::Real u_hot = 2.84e5; // cm/s (CJ speed)
  amrex::Real rho_hot;         // computed: PYT2R(p_hot, Y_hot, T_hot)
  amrex::Real rhoe_hot;        // computed: rho_hot * e_hot via RYP2E

  // === Hotspot positions ===
  int n_hot = 4;
  amrex::Real y_hot[4] = {1.5, 4.0, 6.5, 8.5}; // cm from prob_lo

  // === Mass fractions (LiDryer order: H2 O2 H2O H O OH HO2 H2O2 N2) ===
  amrex::Real massfrac_0[NUM_SPECIES];   // Background
  amrex::Real massfrac_hot[NUM_SPECIES]; // Hotspot
};

struct ProbParmHost { ProbParmHost() = default; };
#endif
