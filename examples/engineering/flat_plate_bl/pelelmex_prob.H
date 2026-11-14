#ifndef PELELM_PROB_H
#define PELELM_PROB_H

#include "my_pele_modules.H"

#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>
#include <AMReX_SPACE.H>
#include <AMReX_REAL.H>

#include <PeleLMeX_ProblemSpecificFunctions.H>
#include <PeleLMeX_Index.H>
#include <PMFData.H>
#include <PelePhysics.H>

using namespace amrex::literals;

struct MyProbParm : public ProbParmDefault
{
  amrex::Real T_mean = 293.0;
  amrex::Real meanFlowMag = 10.0;
  int meanFlowDir = 1;
  pele::physics::eos::EosParm<pele::physics::PhysicsType::eos_type> const*
    eosparm;
};

struct MyProblemSpecificFunctions : public DefaultProblemSpecificFunctions
{
  // -----------------------------------------------------------------------
  // Initial condition: uniform flow at 10 m/s in +x, T=293K,
  // low-turbulence k=1.5e-4, ε=3e-6 (~1% TI at 10 m/s).
  // -----------------------------------------------------------------------
  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void initdata(
    int i,
    int j,
    int k,
    int is_incompressible,
    amrex::Array4<amrex::Real> const& state,
    amrex::Array4<amrex::Real> const& aux,
    amrex::GeometryData const& /*geomdata*/,
    MyProbParm const& prob_parm,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    // Uniform freestream in +x direction
    switch (prob_parm.meanFlowDir) {
    case 1:
      AMREX_D_TERM(state(i, j, k, VELX) = prob_parm.meanFlowMag;
                   , state(i, j, k, VELY) = 0.0;
                   , state(i, j, k, VELZ) = 0.0);
      break;
    default:
      AMREX_D_TERM(state(i, j, k, VELX) = prob_parm.meanFlowMag;
                   , state(i, j, k, VELY) = 0.0;
                   , state(i, j, k, VELZ) = 0.0);
    }

    // In incompressible mode, density/temperature/species are constant
    if (is_incompressible != 0) {
      aux(i, j, k, 0) = 1.5e-4;
      aux(i, j, k, 1) = 3.0e-6;
      return;
    }

    auto eos = pele::physics::PhysicsType::eos(prob_parm.eosparm);

    state(i, j, k, TEMP) = prob_parm.T_mean;
    amrex::Real P_cgs = prob_parm.P_mean * 10.0;
    amrex::Real molefrac[NUM_SPECIES] = {0.0};
    amrex::Real massfrac[NUM_SPECIES] = {0.0};

    molefrac[N2_ID] = 0.79;
    molefrac[O2_ID] = 0.21;

    eos.X2Y(molefrac, massfrac);
    amrex::Real rho_cgs = 0.0;
    eos.PYT2R(P_cgs, massfrac, state(i, j, k, TEMP), rho_cgs);
    state(i, j, k, DENSITY) = rho_cgs * 1.0e3;

    for (int n = 0; n < NUM_SPECIES; n++) {
      state(i, j, k, FIRSTSPEC + n) = state(i, j, k, DENSITY) * massfrac[n];
    }
    amrex::Real h_cgs = 0.0;
    eos.TY2H(state(i, j, k, TEMP), massfrac, h_cgs);
    state(i, j, k, RHOH) = h_cgs * 1.0e-4 * state(i, j, k, DENSITY);

    // k-ε low-turbulence initialization
    // k=1.5e-4, ε=3e-6 → ~1% turbulence intensity at U∞=10 m/s
    aux(i, j, k, 0) = 1.5e-4;
    aux(i, j, k, 1) = 3.0e-6;
  }

  // -----------------------------------------------------------------------
  // bcnormal: handles both x_lo (inlet) and y_lo (symmetry → wall)
  //
  // x_lo: uniform 10 m/s +x, T=293K, air mixture (inlet)
  // y_lo: x < 0.05 m → symmetry  (vel=extrapolated tangentially, v=0)
  //       x ≥ 0.05 m → no-slip   (u=0, v=0)
  // -----------------------------------------------------------------------
  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void bcnormal(
    const amrex::Real x[AMREX_SPACEDIM],
    const amrex::CellData<amrex::Real>& s_in,
    amrex::Real s_ext[NVAR],
    const int idir,
    const int sgn,
    const amrex::Real /*time*/,
    amrex::GeometryData const& /*geomdata*/,
    MyProbParm const& prob_parm,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    amrex::Real massfrac[NUM_SPECIES] = {0.0};
    auto eos = pele::physics::PhysicsType::eos();

    // ---- y_lo face: symmetry (x<0.05 m) → no-slip wall (x≥0.05 m) ----
    if (idir == 1 && sgn == 1) {
      constexpr amrex::Real x_wall_start = 0.05;
      if (x[0] < x_wall_start) {
        // Symmetry: tangential velocity extrapolated from interior,
        //           normal velocity = 0
        s_ext[VELX] = s_in[VELX];
        s_ext[VELY] = 0.0;
      } else {
        // No-slip wall
        s_ext[VELX] = 0.0;
        s_ext[VELY] = 0.0;
      }
      AMREX_D_TERM(,, s_ext[VELZ] = 0.0);

      massfrac[O2_ID] = 0.233;
      massfrac[N2_ID] = 0.767;
      s_ext[TEMP] = prob_parm.T_mean;
      amrex::Real rho_cgs, P_cgs, RhoH_temp;
      P_cgs = prob_parm.P_mean * 10.0;
      eos.PYT2R(P_cgs, massfrac, s_ext[TEMP], rho_cgs);
      s_ext[DENSITY] = rho_cgs * 1.0e3;
      eos.TY2H(s_ext[TEMP], massfrac, RhoH_temp);
      s_ext[RHOH] = RhoH_temp * 1.0e-4 * s_ext[DENSITY];
      for (int n = 0; n < NUM_SPECIES; n++) {
        s_ext[FIRSTSPEC + n] = massfrac[n] * s_ext[DENSITY];
      }
      return;
    }

    // ---- x_lo (and other faces): inlet BC ----
    switch (prob_parm.meanFlowDir) {
    case 1:
      AMREX_D_TERM(s_ext[VELX] = prob_parm.meanFlowMag;
                   , s_ext[VELY] = 0.0;
                   , s_ext[VELZ] = 0.0);
      break;
    default:
      AMREX_D_TERM(s_ext[VELX] = prob_parm.meanFlowMag;
                   , s_ext[VELY] = 0.0;
                   , s_ext[VELZ] = 0.0);
    }

    massfrac[O2_ID] = 0.233;
    massfrac[N2_ID] = 0.767;

    s_ext[TEMP] = prob_parm.T_mean;

    amrex::Real rho_cgs, P_cgs, RhoH_temp;
    P_cgs = prob_parm.P_mean * 10.0;

    eos.PYT2R(P_cgs, massfrac, s_ext[TEMP], rho_cgs);
    s_ext[DENSITY] = rho_cgs * 1.0e3;

    eos.TY2H(s_ext[TEMP], massfrac, RhoH_temp);
    s_ext[RHOH] = RhoH_temp * 1.0e-4 * s_ext[DENSITY];

    for (int n = 0; n < NUM_SPECIES; n++) {
      s_ext[FIRSTSPEC + n] = massfrac[n] * s_ext[DENSITY];
    }
  }

  // -----------------------------------------------------------------------
  // bcnormal_aux: inlet BC for auxiliary variables (k and ε)
  // -----------------------------------------------------------------------
  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void bcnormal_aux(
    const amrex::Real x[AMREX_SPACEDIM],
    amrex::CellData<amrex::Real>& aux_ext,
    const int /*idir*/,
    const int /*sgn*/,
    const amrex::Real /*time*/,
    amrex::GeometryData const& /*geomdata*/,
    MyProbParm const& /*prob_parm*/,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    amrex::ignore_unused(x);
    // Inlet turbulence: k=1.5e-4, ε=3e-6
    aux_ext[0] = 1.5e-4;
    aux_ext[1] = 3.0e-6;
  }

};

using ProblemSpecificFunctions = MyProblemSpecificFunctions;
using ProbParm = MyProbParm;

// -----------------------------------------------------------------------------
// k-ε auxiliary source terms — production from shear
// -----------------------------------------------------------------------------
inline void add_kepsilon_aux_sources(
    const amrex::Box& bx,
    const amrex::Array4<amrex::Real>& aux_arr,
    const amrex::Array4<const amrex::Real>& state_arr)
{
    auto const& C = Turbulence::KEpsilonConstants();
    amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE(int i, int j, int k) {
        double rho = state_arr(i,j,k,DENSITY);
        double k_val = amrex::max(aux_arr(i,j,k,0), 1e-14);
        double eps = amrex::max(aux_arr(i,j,k,1), 1e-14);

        double mu_t = C.C_mu * rho * k_val * k_val / eps;

        // Strain rate in 2D: S_ij S_ij = (dudx)² + (dvdy)² + ½(dudy+dvdx)²
        double dudx = (state_arr(i+1,j,k,VELX) - state_arr(i-1,j,k,VELX)) / 2.0;
        double dudy = (state_arr(i,j+1,k,VELX) - state_arr(i,j-1,k,VELX)) / 2.0;
        double dvdx = (state_arr(i+1,j,k,VELY) - state_arr(i-1,j,k,VELY)) / 2.0;
        double dvdy = (state_arr(i,j+1,k,VELY) - state_arr(i,j-1,k,VELY)) / 2.0;
        double S2 = dudx*dudx + dvdy*dvdy + 0.5*(dudy+dvdx)*(dudy+dvdx);
        double P_k = amrex::max(mu_t * 2.0 * S2, 0.0);

        aux_arr(i,j,k,0) += P_k - rho * eps;
        aux_arr(i,j,k,1) += C.C_eps1 * eps / k_val * P_k
                          - C.C_eps2 * rho * eps * eps / k_val;
    });
}

// -----------------------------------------------------------------------------
// Wall functions — bottom wall (y_lo) Launder-Spalding log-law
// -----------------------------------------------------------------------------
inline void apply_wall_functions_bottom(
    const amrex::Box& bx,
    const amrex::Array4<amrex::Real>& aux_arr,
    const amrex::Array4<const amrex::Real>& state_arr,
    const amrex::GeometryData& geomdata,
    amrex::Real dx)
{
    auto const& C = Turbulence::KEpsilonConstants();
    amrex::Real y_wall = geomdata.ProbLo(1); // bottom wall y-coordinate

    amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE(int i, int j, int k) {
        // Only apply to first cell off wall
        if (j != 0) return;

        amrex::Real y_cell = y_wall + (amrex::Real(j) + 0.5_rt) * dx;
        amrex::Real y_p = y_cell - y_wall; // wall distance [m]
        amrex::Real rho = state_arr(i,j,k,DENSITY);
        amrex::Real nu = 1.5e-5; // kinematic viscosity of air [m²/s]

        // Wall-parallel velocity magnitude
        amrex::Real u_par = std::sqrt(
            state_arr(i,j,k,VELX) * state_arr(i,j,k,VELX) +
            state_arr(i,j,k,VELY) * state_arr(i,j,k,VELY));

        // Newton solve for u_tau from log-law: u_par = u_tau/κ · ln(y⁺) + B·u_tau
        amrex::Real u_tau = amrex::max(u_par / 20.0, 1e-6);
        for (int iter = 0; iter < 10; ++iter) {
            amrex::Real y_plus = y_p * u_tau / nu;
            amrex::Real u_log = u_tau / C.kappa * std::log(amrex::max(y_plus, 1.0))
                              + C.B * u_tau;
            amrex::Real f = u_log - u_par;
            amrex::Real df = (std::log(amrex::max(y_plus, 1.0)) + 1.0) / C.kappa + C.B;
            u_tau = amrex::max(u_tau - f / df, 1e-10);
            if (std::abs(f) < 1e-6 * u_par) break;
        }

        amrex::Real y_plus = y_p * u_tau / nu;

        amrex::Real k_wall = u_tau * u_tau / std::sqrt(C.C_mu);
        amrex::Real eps_wall = u_tau * u_tau * u_tau / (C.kappa * y_p);

        // Only apply wall functions in fully turbulent region (y⁺ > 30)
        if (y_plus > 30.0) {
            constexpr amrex::Real relax = 0.3;
            aux_arr(i,j,k,0) = relax * k_wall + (1.0 - relax) * aux_arr(i,j,k,0);
            aux_arr(i,j,k,1) = relax * eps_wall + (1.0 - relax) * aux_arr(i,j,k,1);
        }
    });
}

#endif
