#ifndef PELELM_QTL03_AUX_BRIDGE_PROB_H
#define PELELM_QTL03_AUX_BRIDGE_PROB_H

#include <AMReX_FArrayBox.H>
#include <AMReX_Geometry.H>
#include <AMReX_REAL.H>
#include <AMReX_SPACE.H>
#include <AMReX_Array.H>

#include <PeleLMeX_Index.H>
#include <PeleLMeX_ProblemSpecificFunctions.H>
#include <PMFData.H>
#include <PelePhysics.H>

#include <cmath>

struct MyProbParm : public ProbParmDefault
{
  amrex::GpuArray<amrex::Real, AMREX_SPACEDIM> bubble_center{
    AMREX_D_DECL(0.5, 0.5, 0.5)};
  amrex::Real bubble_radius = 0.25;
  amrex::Real interface_thickness = 0.025;
  amrex::Real u0 = 0.0;
  amrex::Real v0 = 0.2;
  amrex::Real surface_tension_sigma = 0.0;
  amrex::Real surface_tension_grad_floor = 1.0e-12;
  amrex::Real surface_tension_force_cap = 0.0;
  int surface_tension_curvature_scheme = 1;
  int surface_tension_force_form = 1;
};

struct MyProblemSpecificFunctions : public DefaultProblemSpecificFunctions
{
  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void initdata(
    int i,
    int j,
    int k,
    int is_incompressible,
    amrex::Array4<amrex::Real> const& state,
    amrex::Array4<amrex::Real> const& aux,
    amrex::GeometryData const& geomdata,
    MyProbParm const& prob_parm,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    const amrex::Real* prob_lo = geomdata.ProbLo();
    const amrex::Real* dx = geomdata.CellSize();
    const amrex::Real x = prob_lo[0] + (static_cast<amrex::Real>(i) + 0.5) * dx[0];
    const amrex::Real y = prob_lo[1] + (static_cast<amrex::Real>(j) + 0.5) * dx[1];
    const amrex::Real r = std::sqrt(
      (x - prob_parm.bubble_center[0]) * (x - prob_parm.bubble_center[0]) +
      (y - prob_parm.bubble_center[1]) * (y - prob_parm.bubble_center[1]));
    const amrex::Real eps = amrex::max(prob_parm.interface_thickness, 1.0e-12);
    const amrex::Real alpha =
      0.5 * (1.0 - std::tanh((r - prob_parm.bubble_radius) / eps));

    if (is_incompressible != 0) {
      state(i, j, k, VELX) = prob_parm.u0;
      state(i, j, k, VELY) = prob_parm.v0;
    } else {
      amrex::Abort("qlt03_lm_aux_bridge requires peleLM.incompressible = 1");
    }

    for (int n = 0; n < aux.nComp(); ++n) {
      aux(i, j, k, n) = alpha;
    }
  }

  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static amrex::Real alpha_clamped(
    amrex::Array4<const amrex::Real> const& aux,
    const int i,
    const int j,
    const int k) noexcept
  {
    return amrex::min(1.0, amrex::max(0.0, aux(i, j, k, 0)));
  }

  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static amrex::Real normal_x(
    amrex::Array4<const amrex::Real> const& aux,
    const int i,
    const int j,
    const int k,
    const amrex::Real dx0,
    const amrex::Real dx1,
    const amrex::Real grad_floor) noexcept
  {
    const amrex::Real gx =
      (alpha_clamped(aux, i + 1, j, k) - alpha_clamped(aux, i - 1, j, k)) /
      (2.0 * dx0);
    const amrex::Real gy =
      (alpha_clamped(aux, i, j + 1, k) - alpha_clamped(aux, i, j - 1, k)) /
      (2.0 * dx1);
    const amrex::Real gm = std::sqrt(gx * gx + gy * gy + grad_floor * grad_floor);
    return gx / gm;
  }

  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static amrex::Real normal_y(
    amrex::Array4<const amrex::Real> const& aux,
    const int i,
    const int j,
    const int k,
    const amrex::Real dx0,
    const amrex::Real dx1,
    const amrex::Real grad_floor) noexcept
  {
    const amrex::Real gx =
      (alpha_clamped(aux, i + 1, j, k) - alpha_clamped(aux, i - 1, j, k)) /
      (2.0 * dx0);
    const amrex::Real gy =
      (alpha_clamped(aux, i, j + 1, k) - alpha_clamped(aux, i, j - 1, k)) /
      (2.0 * dx1);
    const amrex::Real gm = std::sqrt(gx * gx + gy * gy + grad_floor * grad_floor);
    return gy / gm;
  }

  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void csf_normal_and_gradmag(
    amrex::Array4<const amrex::Real> const& aux,
    const int i,
    const int j,
    const int k,
    const amrex::Real dx0,
    const amrex::Real dx1,
    const amrex::Real grad_floor,
    amrex::Real& nx,
    amrex::Real& ny,
    amrex::Real& gm) noexcept
  {
    const amrex::Real gx =
      (alpha_clamped(aux, i + 1, j, k) - alpha_clamped(aux, i - 1, j, k)) /
      (2.0 * dx0);
    const amrex::Real gy =
      (alpha_clamped(aux, i, j + 1, k) - alpha_clamped(aux, i, j - 1, k)) /
      (2.0 * dx1);
    gm = std::sqrt(gx * gx + gy * gy + grad_floor * grad_floor);
    nx = gx / gm;
    ny = gy / gm;
  }

  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void csf_stress(
    amrex::Array4<const amrex::Real> const& aux,
    const int i,
    const int j,
    const int k,
    const amrex::Real dx0,
    const amrex::Real dx1,
    const amrex::Real grad_floor,
    const amrex::Real sigma,
    amrex::Real& txx,
    amrex::Real& txy,
    amrex::Real& tyy) noexcept
  {
    amrex::Real nx = 0.0;
    amrex::Real ny = 0.0;
    amrex::Real gm = 0.0;
    csf_normal_and_gradmag(aux, i, j, k, dx0, dx1, grad_floor, nx, ny, gm);
    const amrex::Real coeff = sigma * gm;
    txx = coeff * (1.0 - nx * nx);
    txy = -coeff * nx * ny;
    tyy = coeff * (1.0 - ny * ny);
  }

  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static amrex::Real alpha_at_point(
    const amrex::Real x,
    const amrex::Real y,
    const MyProbParm& prob_parm)
  {
    const amrex::Real r = std::sqrt(
      (x - prob_parm.bubble_center[0]) * (x - prob_parm.bubble_center[0]) +
      (y - prob_parm.bubble_center[1]) * (y - prob_parm.bubble_center[1]));
    const amrex::Real eps = amrex::max(prob_parm.interface_thickness, 1.0e-12);
    return 0.5 * (1.0 - std::tanh((r - prob_parm.bubble_radius) / eps));
  }

  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void bcnormal(
    const amrex::Real* /*x*/,
    const amrex::CellData<amrex::Real>& /*s_in*/,
    amrex::Real s_ext[NVAR],
    const int /*idir*/,
    const int /*sgn*/,
    const amrex::Real /*time*/,
    amrex::GeometryData const& /*geomdata*/,
    MyProbParm const& /*prob_parm*/,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    AMREX_D_TERM(s_ext[VELX] = 0.0;, s_ext[VELY] = 0.0;, s_ext[VELZ] = 0.0;)
  }

  AMREX_GPU_DEVICE
  AMREX_FORCE_INLINE
  static void bcnormal_aux(
    const amrex::Real x[AMREX_SPACEDIM],
    amrex::CellData<amrex::Real>& aux_ext,
    const int /*idir*/,
    const int /*sgn*/,
    const amrex::Real /*time*/,
    amrex::GeometryData const& /*geomdata*/,
    MyProbParm const& prob_parm,
    pele::physics::PMF::PmfData::DataContainer const* /*pmf_data*/)
  {
    for (int n = 0; n < aux_ext.nComp(); ++n) {
      aux_ext[n] = alpha_at_point(x[0], x[1], prob_parm);
    }
  }

  static void modify_ext_sources(
    amrex::Real /*time*/,
    amrex::Real /*dt*/,
    const amrex::MultiFab& state_old,
    const amrex::MultiFab& state_new,
    const amrex::MultiFab* aux_old,
    const amrex::MultiFab* aux_new,
    std::unique_ptr<amrex::MultiFab>& ext_src,
    const amrex::GeometryData& geomdata,
    const MyProbParm* prob_parm)
  {
    amrex::ignore_unused(state_old, state_new, aux_old);
    if (prob_parm == nullptr) {
      amrex::Abort("qlt03_lm_aux_bridge received a null ProbParm pointer");
    }
    if (prob_parm->surface_tension_sigma <= 0.0) {
      return;
    }
    if (aux_new == nullptr || aux_new->nComp() < 1) {
      amrex::Abort("qlt03_lm_aux_bridge CSF source requires Aux alpha");
    }

    auto const& aux = aux_new->const_arrays();
    auto const& src = ext_src->arrays();
    const amrex::Box domain = geomdata.Domain();
    const int ilo = domain.smallEnd(0);
    const int ihi = domain.bigEnd(0);
    const int jlo = domain.smallEnd(1);
    const int jhi = domain.bigEnd(1);
    const amrex::Real dx0 = geomdata.CellSize(0);
    const amrex::Real dx1 = geomdata.CellSize(1);
    const amrex::Real sigma = prob_parm->surface_tension_sigma;
    const amrex::Real grad_floor = prob_parm->surface_tension_grad_floor;
    const amrex::Real force_cap = prob_parm->surface_tension_force_cap;
    const int force_form = prob_parm->surface_tension_force_form;
    amrex::ParallelFor(
      *ext_src, amrex::IntVect(0),
      [=] AMREX_GPU_DEVICE(int nbx, int i, int j, int k) noexcept {
        if (i <= ilo || i >= ihi || j <= jlo || j >= jhi) {
          return;
        }
        amrex::Real force_x = 0.0;
        amrex::Real force_y = 0.0;
        if (force_form == 3) {
          if (i <= ilo + 1 || i >= ihi - 1 || j <= jlo + 1 || j >= jhi - 1) {
            return;
          }
          amrex::Real txx_ip = 0.0;
          amrex::Real txy_ip = 0.0;
          amrex::Real tyy_ip = 0.0;
          amrex::Real txx_im = 0.0;
          amrex::Real txy_im = 0.0;
          amrex::Real tyy_im = 0.0;
          amrex::Real txx_jp = 0.0;
          amrex::Real txy_jp = 0.0;
          amrex::Real tyy_jp = 0.0;
          amrex::Real txx_jm = 0.0;
          amrex::Real txy_jm = 0.0;
          amrex::Real tyy_jm = 0.0;
          csf_stress(aux[nbx], i + 1, j, k, dx0, dx1, grad_floor, sigma, txx_ip, txy_ip, tyy_ip);
          csf_stress(aux[nbx], i - 1, j, k, dx0, dx1, grad_floor, sigma, txx_im, txy_im, tyy_im);
          csf_stress(aux[nbx], i, j + 1, k, dx0, dx1, grad_floor, sigma, txx_jp, txy_jp, tyy_jp);
          csf_stress(aux[nbx], i, j - 1, k, dx0, dx1, grad_floor, sigma, txx_jm, txy_jm, tyy_jm);
          // Continuum-surface-stress candidate: div(sigma |grad alpha| (I - n n)).
          // It is intentionally default-off until QLT-03 force-pressure gates pass.
          force_x = (txx_ip - txx_im) / (2.0 * dx0) + (txy_jp - txy_jm) / (2.0 * dx1);
          force_y = (txy_ip - txy_im) / (2.0 * dx0) + (tyy_jp - tyy_jm) / (2.0 * dx1);
        } else {
          const amrex::Real alpha = alpha_clamped(aux[nbx], i, j, k);
          const amrex::Real alpha_ip = alpha_clamped(aux[nbx], i + 1, j, k);
          const amrex::Real alpha_im = alpha_clamped(aux[nbx], i - 1, j, k);
          const amrex::Real alpha_jp = alpha_clamped(aux[nbx], i, j + 1, k);
          const amrex::Real alpha_jm = alpha_clamped(aux[nbx], i, j - 1, k);
          const amrex::Real grad_x = (alpha_ip - alpha_im) / (2.0 * dx0);
          const amrex::Real grad_y = (alpha_jp - alpha_jm) / (2.0 * dx1);
          const amrex::Real grad_mag = std::sqrt(
            grad_x * grad_x + grad_y * grad_y + grad_floor * grad_floor);
          const amrex::Real lap_alpha =
            (alpha_ip - 2.0 * alpha + alpha_im) / (dx0 * dx0) +
            (alpha_jp - 2.0 * alpha + alpha_jm) / (dx1 * dx1);
          amrex::Real curvature = -lap_alpha / grad_mag;
          if (
            prob_parm->surface_tension_curvature_scheme == 2 && i > ilo + 1 &&
            i < ihi - 1 && j > jlo + 1 && j < jhi - 1) {
            const amrex::Real nx_ip = normal_x(aux[nbx], i + 1, j, k, dx0, dx1, grad_floor);
            const amrex::Real nx_im = normal_x(aux[nbx], i - 1, j, k, dx0, dx1, grad_floor);
            const amrex::Real ny_jp = normal_y(aux[nbx], i, j + 1, k, dx0, dx1, grad_floor);
            const amrex::Real ny_jm = normal_y(aux[nbx], i, j - 1, k, dx0, dx1, grad_floor);
            curvature = -((nx_ip - nx_im) / (2.0 * dx0) + (ny_jp - ny_jm) / (2.0 * dx1));
          }
          // The bridge uses alpha=1 for the light bubble, so grad(alpha) points
          // opposite to the heavy-phase convention assumed by the original CSF
          // sign. Flip the source to keep surface tension restorative.
          force_x = -sigma * curvature * grad_x;
          force_y = -sigma * curvature * grad_y;
        }
        const amrex::Real force_mag =
          std::sqrt(force_x * force_x + force_y * force_y);
        if (force_cap > 0.0 && force_mag > force_cap) {
          const amrex::Real scale = force_cap / force_mag;
          force_x *= scale;
          force_y *= scale;
        }
        src[nbx](i, j, k, VELX) += force_x;
        src[nbx](i, j, k, VELY) += force_y;
      });
    amrex::Gpu::streamSynchronize();
  }
};

using ProblemSpecificFunctions = MyProblemSpecificFunctions;
using ProbParm = MyProbParm;

#endif
