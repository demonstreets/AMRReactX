#ifndef BUBBLE_PROB_H
#define BUBBLE_PROB_H

#include "prob_parm.H"

#include <AMReX_Geometry.H>
#include <AMReX_Gpu.H>
#include <AMReX_ParmParse.H>
#include <AMReX_REAL.H>
#include <cmath>

#include "IndexDefines.H"
#include "PeleC.H"
#include "ProblemSpecificFunctions.H"
#include "StiffenedGas.H"
#include "Tagging.H"

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
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
  const amrex::Real y = prob_lo[1] + (j + 0.5) * dx[1];
  const amrex::Real r = std::sqrt(
    (x - prob_parm.bubble_cx) * (x - prob_parm.bubble_cx) +
    (y - prob_parm.bubble_cy) * (y - prob_parm.bubble_cy));
  amrex::Real alpha = (r < prob_parm.bubble_r) ? 0.0 : 1.0;
  if (prob_parm.interface_width > 0.0) {
    const amrex::Real eta = (r - prob_parm.bubble_r) /
                            prob_parm.interface_width;
    alpha = 0.5 * (1.0 + std::tanh(eta));
    alpha = amrex::min(1.0, amrex::max(0.0, alpha));
  }
  const amrex::Real light_fraction = 1.0 - alpha;
  const amrex::Real rho =
    prob_parm.rho_heavy * alpha + prob_parm.rho_light * light_fraction;
  const amrex::Real gamma_gas = 1.4;
  constexpr StiffenedGasParams sg = {4.4, 6.0e9};
  const amrex::Real e =
    (alpha > 0.5) ? sg_e(sg, rho, prob_parm.p0)
                  : prob_parm.p0 / ((gamma_gas - 1.0) * rho);

  state(i, j, k, URHO) = rho;
  state(i, j, k, UMX) = 0.0;
  state(i, j, k, UMY) = 0.0;
  state(i, j, k, UMZ) = 0.0;
  state(i, j, k, UEINT) = rho * e;
  state(i, j, k, UEDEN) = rho * e;

  constexpr amrex::Real cv_liquid = 4.18e7;
  state(i, j, k, UTEMP) =
    (alpha > 0.5) ? sg_T(sg, rho, e, cv_liquid) : prob_parm.p0 / rho;

#if NUM_ADV > 0
  state(i, j, k, UFS) = rho;
  state(i, j, k, UFA) = rho * alpha;
#endif
}

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void
bcnormal(
  const amrex::Real*,
  const amrex::Real s_int[NVAR],
  amrex::Real s_ext[NVAR],
  const int,
  const int,
  const amrex::Real,
  amrex::GeometryData const&,
  ProbParmDevice const&,
  const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>&)
{
  for (int n = 0; n < NVAR; n++) {
    s_ext[n] = s_int[n];
  }
}

void pc_prob_close();
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void
pc_check_initial_species(int, int, int, amrex::Array4<amrex::Real>&)
{
}

struct BubbleRiseProblemSpecificFunctions : public DefaultProblemSpecificFunctions
{
  static void problem_modify_ext_sources(
    amrex::Real time,
    amrex::Real dt,
    const amrex::MultiFab& state_old,
    const amrex::MultiFab& state_new,
    amrex::MultiFab& ext_src,
    int /*ng*/,
    amrex::GeometryData const& geomdata,
    ProbParmDevice const& prob_parm)
  {
#if NUM_ADV > 0
    amrex::ignore_unused(state_old);
    const bool buoyancy_active =
      time >= prob_parm.buoyancy_start_time &&
      time <= prob_parm.buoyancy_end_time &&
      prob_parm.buoyancy_accel != 0.0;
    const bool surface_tension_active = prob_parm.surface_tension_sigma > 0.0;
    const bool phase_viscosity_active =
      prob_parm.phase_viscosity_mu_heavy > 0.0 ||
      prob_parm.phase_viscosity_mu_light > 0.0;
    if (!buoyancy_active && !surface_tension_active && !phase_viscosity_active) {
      return;
    }
    amrex::Real source_factor = buoyancy_active ? 1.0 : 0.0;
    if (buoyancy_active && prob_parm.buoyancy_ramp_time > 0.0) {
      source_factor = amrex::min(
        1.0,
        amrex::max(
          0.0,
          (time - prob_parm.buoyancy_start_time) /
            prob_parm.buoyancy_ramp_time));
    }
    auto const& state = state_new.const_arrays();
    auto const& src = ext_src.arrays();
    const amrex::Box domain = geomdata.Domain();
    const int ilo = domain.smallEnd(0);
    const int ihi = domain.bigEnd(0);
    const int jlo = domain.smallEnd(1);
    const int jhi = domain.bigEnd(1);
    const amrex::Real dx0 = geomdata.CellSize(0);
    const amrex::Real dx1 = geomdata.CellSize(1);
    const amrex::IntVect ngs(0);
    amrex::ParallelFor(
      ext_src, ngs, [=] AMREX_GPU_DEVICE(int nbx, int i, int j, int k)
                       noexcept {
                         const amrex::Real rho =
                           amrex::max(state[nbx](i, j, k, URHO), 1.0e-30);
                         const amrex::Real alpha = amrex::min(
                           1.0,
                           amrex::max(0.0, state[nbx](i, j, k, UFA) / rho));
                         const amrex::Real light_fraction = 1.0 - alpha;
                         const amrex::Real ux = state[nbx](i, j, k, UMX) / rho;
                         const amrex::Real uy = state[nbx](i, j, k, UMY) / rho;
                         amrex::Real force_x = 0.0;
                         amrex::Real force_y = 0.0;
                         if (buoyancy_active) {
                           amrex::Real limiter = 1.0;
                           if (prob_parm.buoyancy_terminal_speed > 0.0) {
                             limiter = amrex::max(
                               0.0,
                               1.0 -
                                 amrex::max(0.0, uy) /
                                   prob_parm.buoyancy_terminal_speed);
                           }
                           force_y += source_factor * limiter * rho *
                                      light_fraction *
                                      prob_parm.buoyancy_accel;
                         }
                         if (
                           surface_tension_active && i > ilo && i < ihi &&
                           j > jlo && j < jhi) {
                           const amrex::Real rho_ip =
                             amrex::max(state[nbx](i + 1, j, k, URHO), 1.0e-30);
                           const amrex::Real rho_im =
                             amrex::max(state[nbx](i - 1, j, k, URHO), 1.0e-30);
                           const amrex::Real rho_jp =
                             amrex::max(state[nbx](i, j + 1, k, URHO), 1.0e-30);
                           const amrex::Real rho_jm =
                             amrex::max(state[nbx](i, j - 1, k, URHO), 1.0e-30);
                           const amrex::Real alpha_ip = amrex::min(
                             1.0,
                             amrex::max(
                               0.0, state[nbx](i + 1, j, k, UFA) / rho_ip));
                           const amrex::Real alpha_im = amrex::min(
                             1.0,
                             amrex::max(
                               0.0, state[nbx](i - 1, j, k, UFA) / rho_im));
                           const amrex::Real alpha_jp = amrex::min(
                             1.0,
                             amrex::max(
                               0.0, state[nbx](i, j + 1, k, UFA) / rho_jp));
                           const amrex::Real alpha_jm = amrex::min(
                             1.0,
                             amrex::max(
                               0.0, state[nbx](i, j - 1, k, UFA) / rho_jm));
                           const amrex::Real grad_x =
                             (alpha_ip - alpha_im) / (2.0 * dx0);
                           const amrex::Real grad_y =
                             (alpha_jp - alpha_jm) / (2.0 * dx1);
                           const amrex::Real grad_mag = std::sqrt(
                             grad_x * grad_x + grad_y * grad_y +
                             prob_parm.surface_tension_grad_floor *
                               prob_parm.surface_tension_grad_floor);
                           const amrex::Real lap_alpha =
                             (alpha_ip - 2.0 * alpha + alpha_im) /
                               (dx0 * dx0) +
                             (alpha_jp - 2.0 * alpha + alpha_jm) /
                               (dx1 * dx1);
                           const amrex::Real curvature = -lap_alpha / grad_mag;
                           amrex::Real st_force_x =
                             prob_parm.surface_tension_sigma * curvature *
                             grad_x;
                           amrex::Real st_force_y =
                             prob_parm.surface_tension_sigma * curvature *
                             grad_y;
                           const amrex::Real st_mag = std::sqrt(
                             st_force_x * st_force_x +
                             st_force_y * st_force_y);
                           if (
                             prob_parm.surface_tension_force_cap > 0.0 &&
                             st_mag > prob_parm.surface_tension_force_cap) {
                             const amrex::Real scale =
                               prob_parm.surface_tension_force_cap / st_mag;
                             st_force_x *= scale;
                             st_force_y *= scale;
                           }
                           force_x += st_force_x;
                           force_y += st_force_y;
                         }
                         if (
                           phase_viscosity_active && i > ilo && i < ihi &&
                           j > jlo && j < jhi) {
                           const amrex::Real rho_ip =
                             amrex::max(state[nbx](i + 1, j, k, URHO), 1.0e-30);
                           const amrex::Real rho_im =
                             amrex::max(state[nbx](i - 1, j, k, URHO), 1.0e-30);
                           const amrex::Real rho_jp =
                             amrex::max(state[nbx](i, j + 1, k, URHO), 1.0e-30);
                           const amrex::Real rho_jm =
                             amrex::max(state[nbx](i, j - 1, k, URHO), 1.0e-30);
                           const amrex::Real ux_ip =
                             state[nbx](i + 1, j, k, UMX) / rho_ip;
                           const amrex::Real ux_im =
                             state[nbx](i - 1, j, k, UMX) / rho_im;
                           const amrex::Real ux_jp =
                             state[nbx](i, j + 1, k, UMX) / rho_jp;
                           const amrex::Real ux_jm =
                             state[nbx](i, j - 1, k, UMX) / rho_jm;
                           const amrex::Real uy_ip =
                             state[nbx](i + 1, j, k, UMY) / rho_ip;
                           const amrex::Real uy_im =
                             state[nbx](i - 1, j, k, UMY) / rho_im;
                           const amrex::Real uy_jp =
                             state[nbx](i, j + 1, k, UMY) / rho_jp;
                           const amrex::Real uy_jm =
                             state[nbx](i, j - 1, k, UMY) / rho_jm;
                           const amrex::Real lap_ux =
                             (ux_ip - 2.0 * ux + ux_im) / (dx0 * dx0) +
                             (ux_jp - 2.0 * ux + ux_jm) / (dx1 * dx1);
                           const amrex::Real lap_uy =
                             (uy_ip - 2.0 * uy + uy_im) / (dx0 * dx0) +
                             (uy_jp - 2.0 * uy + uy_jm) / (dx1 * dx1);
                           const amrex::Real mu_mix =
                             alpha * prob_parm.phase_viscosity_mu_heavy +
                             light_fraction *
                               prob_parm.phase_viscosity_mu_light;
                           amrex::Real visc_force_x = mu_mix * lap_ux;
                           amrex::Real visc_force_y = mu_mix * lap_uy;
                           const amrex::Real visc_mag = std::sqrt(
                             visc_force_x * visc_force_x +
                             visc_force_y * visc_force_y);
                           if (
                             prob_parm.phase_viscosity_force_cap > 0.0 &&
                             visc_mag > prob_parm.phase_viscosity_force_cap) {
                             const amrex::Real scale =
                               prob_parm.phase_viscosity_force_cap / visc_mag;
                             visc_force_x *= scale;
                             visc_force_y *= scale;
                           }
                           force_x += visc_force_x;
                           force_y += visc_force_y;
                         }
                         src[nbx](i, j, k, UMX) += force_x;
                         src[nbx](i, j, k, UMY) += force_y;
                         src[nbx](i, j, k, UEDEN) +=
                           ux * force_x + uy * force_y +
                           prob_parm.buoyancy_energy_correction * 0.5 * dt *
                             (force_x * force_x + force_y * force_y) / rho;
                       });
    amrex::Gpu::synchronize();
#else
    amrex::ignore_unused(state_old, state_new, ext_src, prob_parm);
#endif
  }
};

using ProblemSpecificFunctions = BubbleRiseProblemSpecificFunctions;

#endif
