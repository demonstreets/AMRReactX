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
  pele::physics::eos::EosParm<pele::physics::PhysicsType::eos_type> const*
    eosparm;
};

struct MyProblemSpecificFunctions : public DefaultProblemSpecificFunctions
{
  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void initdata(
    int i,
    int j,
    int k,
    int /*is_incompressible*/,
    amrex::Array4<amrex::Real> const& state,
    amrex::Array4<amrex::Real> const& aux,
    amrex::GeometryData const& geomdata,
    MyProbParm const& prob_parm,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    const amrex::Real* prob_lo = geomdata.ProbLo();
    const amrex::Real* prob_hi = geomdata.ProbHi();
    const amrex::Real* dx = geomdata.CellSize();

    auto eos = pele::physics::PhysicsType::eos(prob_parm.eosparm);

    state(i, j, k, TEMP) = 300;
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

    AMREX_D_TERM(
      const amrex::Real Lx = prob_hi[0] - prob_lo[0];
      , const amrex::Real Ly = prob_hi[1] - prob_lo[1];
      , const amrex::Real Lz = prob_hi[2] - prob_lo[2]);

    // want a cubic domain for ease
#if AMREX_SPACEDIM > 1
    AMREX_ALWAYS_ASSERT(
      AMREX_D_TERM(, amrex::almostEqual(Lx, Ly), &&amrex::almostEqual(Ly, Lz)));
#endif
    // find the centre of the domain
    const amrex::Real cen[AMREX_SPACEDIM] = {AMREX_D_DECL(
      prob_lo[0] + 0.5_rt * Lx, prob_lo[1] + 0.5_rt * Ly,
      prob_lo[2] + 0.5_rt * Lz)};
    const amrex::Real x[AMREX_SPACEDIM] = {AMREX_D_DECL(
      prob_lo[0] + (i + 0.5_rt) * dx[0], prob_lo[1] + (j + 0.5_rt) * dx[1],
      prob_lo[2] + (k + 0.5_rt) * dx[2])};
    // radius from centre
    const amrex::Real r = std::sqrt(AMREX_D_TERM(
      (x[0] - cen[0]) * (x[0] - cen[0]), +(x[1] - cen[1]) * (x[1] - cen[1]),
      +(x[2] - cen[2]) * (x[2] - cen[2])));

    // k-epsilon turbulence model initialization
    // k: turbulent kinetic energy, epsilon: dissipation rate
    const amrex::Real U_inlet = 1.0;
    const amrex::Real turb_intensity = 0.01; // 1%
    const amrex::Real k_init = 1.5 * (turb_intensity * U_inlet) * (turb_intensity * U_inlet);
    const amrex::Real C_mu = 0.09;
    const amrex::Real L_ref = 1.0;
    const amrex::Real eps_init = std::pow(C_mu, 0.75) * std::pow(k_init, 1.5) / (0.1 * L_ref);

    aux(i, j, k, 0) = k_init;
    aux(i, j, k, 1) = eps_init;

    // constant upwards flow
    state(i, j, k, VELX) = 0.0;
#if AMREX_SPACEDIM == 2
    state(i, j, k, VELY) = 1.0;
#else
    state(i, j, k, VELY) = 0.0;
    state(i, j, k, VELZ) = 1.0;
#endif
  }

};

using ProblemSpecificFunctions = MyProblemSpecificFunctions;
using ProbParm = MyProbParm;

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
        double dudx = (state_arr(i+1,j,k,VELX) - state_arr(i-1,j,k,VELX)) * 0.5;
        double dudy = (state_arr(i,j+1,k,VELX) - state_arr(i,j-1,k,VELX)) * 0.5;
        double dvdx = (state_arr(i+1,j,k,VELY) - state_arr(i-1,j,k,VELY)) * 0.5;
        double dvdy = (state_arr(i,j+1,k,VELY) - state_arr(i,j-1,k,VELY)) * 0.5;
        double S2 = dudx*dudx + dvdy*dvdy + 0.5*(dudy+dvdx)*(dudy+dvdx);
        double P_k = amrex::max(mu_t * 2.0 * S2, 0.0);
        aux_arr(i,j,k,0) += (P_k - rho * eps) * 1.0;
        aux_arr(i,j,k,1) += (C.C_eps1 * eps/k_val * P_k - C.C_eps2 * rho * eps*eps/k_val) * 1.0;
    });
}

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
        // Only apply to first cell off wall (j == 0 in 2D)
        if (j != 0) return;
        amrex::Real y_cell = y_wall + (j + 0.5) * dx; // cell center
        amrex::Real y_p = y_cell - y_wall; // wall distance [m]
        amrex::Real rho = state_arr(i,j,k,DENSITY);
        amrex::Real nu = 1.5e-5; // kinematic viscosity air
        amrex::Real u_par = std::sqrt(state_arr(i,j,k,VELX)*state_arr(i,j,k,VELX));
        // u_tau via Newton (simplified: explicit from log-law assumption)
        amrex::Real u_tau = 0.1; // initial guess
        for (int iter = 0; iter < 10; ++iter) {
            amrex::Real y_plus = y_p * u_tau / nu;
            amrex::Real u_log = u_tau / C.kappa * std::log(y_plus) + C.B * u_tau;
            amrex::Real f = u_log - u_par;
            amrex::Real df = (std::log(y_plus) + 1.0) / C.kappa + C.B;
            u_tau = amrex::max(u_tau - f / df, 1e-10);
            if (std::abs(f) < 1e-6 * u_par) break;
        }
        amrex::Real k_wall = u_tau * u_tau / std::sqrt(C.C_mu);
        amrex::Real eps_wall = u_tau * u_tau * u_tau / (C.kappa * y_p);
        amrex::Real y_plus = y_p * u_tau / nu;
        if (y_plus > 30.0) {
            // Relaxation: blend wall function with existing values
            constexpr amrex::Real relax = 0.3;
            aux_arr(i,j,k,0) = relax * k_wall + (1.0 - relax) * aux_arr(i,j,k,0);
            aux_arr(i,j,k,1) = relax * eps_wall + (1.0 - relax) * aux_arr(i,j,k,1);
        }
        // If y+ < 30, leave k and ε unchanged (viscous sublayer/buffer)
    });
}


#endif
