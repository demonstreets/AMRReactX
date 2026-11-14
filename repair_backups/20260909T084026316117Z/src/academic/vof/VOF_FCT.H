#ifndef VOF_FCT_H
#define VOF_FCT_H

#include <AMReX_Gpu.H>
#include <AMReX_REAL.H>
#include <AMReX_Array4.H>
#include <cmath>
#include "IndexDefines.H"
#include "VOF_Constants.H"

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void vof_youngs_normal(
  int i, int j, int k,
  const amrex::Array4<const amrex::Real>& alpha,
  amrex::Real& nx, amrex::Real& ny, amrex::Real& nz)
{
  nx = 0.5 * (alpha(i+1,j,k,QFA) - alpha(i-1,j,k,QFA));
  ny = 0.5 * (alpha(i,j+1,k,QFA) - alpha(i,j-1,k,QFA));
#if AMREX_SPACEDIM >= 3
  nz = 0.5 * (alpha(i,j,k+1,QFA) - alpha(i,j,k-1,QFA));
#else
  nz = 0.0;
#endif
  amrex::Real nmag = std::sqrt(nx*nx + ny*ny + nz*nz);
  if (nmag > VOF_TINY) { nx /= nmag; ny /= nmag; nz /= nmag; }
  else { nx = 0.0; ny = 0.0; nz = 0.0; }
}

// MULES compression as cell-centered body force (Phase 3.10b fix)
// Returns (fx, fy, fz) to be added to momentum source term.
// This eliminates boundary-access issues with face-based Youngs normal.
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void vof_mules_body_force(
  int i, int j, int k,
  const amrex::Array4<const amrex::Real>& alpha,
  const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx,
  amrex::Real& fx, amrex::Real& fy, amrex::Real& fz)
{
  fx = fy = fz = 0.0;

  // Only act near interface
  const amrex::Real a_ij = alpha(i,j,k,QFA);
  if (a_ij < VOF_TINY || a_ij > 1.0 - VOF_TINY) return;

  // Interface normal from Youngs gradient
  amrex::Real nx, ny, nz;
  vof_youngs_normal(i, j, k, alpha, nx, ny, nz);

  // Compression: F = C_alpha * |nabla alpha| * n
  // Physically squeezes intermediate alpha values toward 0 or 1 along normal
  constexpr amrex::Real C_alpha = 1.0;
  const amrex::Real compression_factor = a_ij * (1.0 - a_ij);
  const amrex::Real dax = (alpha(i+1,j,k,QFA)-alpha(i-1,j,k,QFA))/(2.0*dx[0]);
  const amrex::Real day = (alpha(i,j+1,k,QFA)-alpha(i,j-1,k,QFA))/(2.0*dx[1]);
#if AMREX_SPACEDIM >= 3
  const amrex::Real daz = (alpha(i,j,k+1,QFA)-alpha(i,j,k-1,QFA))/(2.0*dx[2]);
#else
  const amrex::Real daz = 0.0;
#endif
  const amrex::Real mag_grad = std::sqrt(dax*dax + day*day + daz*daz);

  const amrex::Real force_mag = C_alpha * mag_grad * compression_factor;
  fx = force_mag * nx;
  fy = force_mag * ny;
  fz = force_mag * nz;
}

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real vof_zalesak_limiter(
  int i, int j, int k, int dir,
  const amrex::Array4<const amrex::Real>& alpha,
  amrex::Real flux_low, amrex::Real flux_high,
  const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx, amrex::Real dt)
{
  const amrex::Real A = flux_high - flux_low;
  if (std::abs(A) < VOF_TINY) return flux_high;
  const amrex::IntVect iv{AMREX_D_DECL(i, j, k)};
  const amrex::IntVect dim(amrex::IntVect::TheDimensionVector(dir));
  const amrex::IntVect ivm(iv - dim);
  const amrex::IntVect ivp(iv + dim);
  const amrex::Real a_i = alpha(ivm, QFA);
  const amrex::Real a_ip1 = alpha(iv, QFA);
  const amrex::Real a_im1 = alpha(ivm - dim, QFA);
  const amrex::Real a_ip2 = alpha(ivp, QFA);
  const amrex::Real alpha_max = amrex::max(amrex::max(a_im1, a_i), amrex::max(a_ip1, a_ip2));
  const amrex::Real alpha_min = amrex::min(amrex::min(a_im1, a_i), amrex::min(a_ip1, a_ip2));
  const amrex::Real kfac = amrex::Math::abs(A) * (dt / dx[dir]);
  amrex::Real C;
  if (A > 0.0) {
    const amrex::Real R1 = (a_i - alpha_min) / (kfac + VOF_TINY);
    const amrex::Real R2 = (alpha_max - a_ip1) / (kfac + VOF_TINY);
    C = amrex::min<amrex::Real>(1.0, amrex::min<amrex::Real>(R1, R2));
  } else {
    const amrex::Real R1 = (a_ip1 - alpha_min) / (kfac + VOF_TINY);
    const amrex::Real R2 = (alpha_max - a_i) / (kfac + VOF_TINY);
    C = amrex::min<amrex::Real>(1.0, amrex::min<amrex::Real>(R1, R2));
  }
  return flux_low + C * A;
}

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real vof_fct_flux(
  const amrex::Real ustar, const amrex::Real flxrho,
  const amrex::Real qL, const amrex::Real qR,
  const amrex::Real alphaL, const amrex::Real alphaR,
  int i, int j, int k, int dir,
  const amrex::Array4<const amrex::Real>& alpha,
  const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx, amrex::Real dt)
{
  amrex::Real flux_low, flux_high;
  if (ustar > 0.0) {
    flux_low = flxrho * alphaL; flux_high = flxrho * qL;
  } else if (ustar < 0.0) {
    flux_low = flxrho * alphaR; flux_high = flxrho * qR;
  } else {
    flux_low = flxrho * 0.5 * (alphaL + alphaR);
    flux_high = flxrho * 0.5 * (qL + qR);
  }
  return vof_zalesak_limiter(i, j, k, dir, alpha, flux_low, flux_high, dx, dt);
}

#endif
