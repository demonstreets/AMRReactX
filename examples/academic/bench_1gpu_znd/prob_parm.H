#ifndef PROB_PARM_H
#define PROB_PARM_H
#include <AMReX_REAL.H>
#include <AMReX_GpuQualifiers.H>

struct ProbParmDevice
{
  // Right state (unburned stoichiometric H2/O2/N2)
  amrex::Real p_r = 2.0e5;   // Pa
  amrex::Real T_r = 300.0;   // K
  amrex::Real rho_r;          // computed: PYT2R(p_r, mf_r, T_r)

  // Left state (CJ products, mostly H2O)
  amrex::Real p_l = 1.8e7;   // Pa
  amrex::Real T_l = 3000.0;  // K
  amrex::Real rho_l;          // computed: PYT2R(p_l, mf_l, T_l)

  // Riemann geometry / perturbation
  amrex::Real x_split = 0.0; // interface position (cm)
  amrex::Real A_per = 0.1;   // perturbation amplitude
  amrex::Real lambda = 1.0;  // perturbation wavelength (cm)

  // Mass fractions (LiDryer order: H2 O2 H2O H O OH HO2 H2O2 N2)
  amrex::Real massfrac_l[NUM_SPECIES]; // Left: CJ products
  amrex::Real massfrac_r[NUM_SPECIES]; // Right: stoichiometric H2:O2:N2
};

struct ProbParmHost { ProbParmHost() = default; };
#endif
