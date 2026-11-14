#pragma once
#include <AMReX_REAL.H>
#include <AMReX_Gpu.H>
#include <AMReX_Array4.H>
#include <cmath>
#include "VOF_Constants.H"  // VOF_TINY

// ── Component-0 interface normal (for use with 1-component alpha FArrayBox) ──
// Same algorithm as vof_youngs_normal but accesses alpha(i,j,k,0) instead of QFA.
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void csf_normal_c0(
    int i,
    int j,
    int k,
    const amrex::Array4<const amrex::Real>& alpha,
    amrex::Real& nx,
    amrex::Real& ny,
    amrex::Real& nz)
{
    nx = 0.5 * (alpha(i+1, j, k, 0) - alpha(i-1, j, k, 0));
    ny = 0.5 * (alpha(i, j+1, k, 0) - alpha(i, j-1, k, 0));
#if AMREX_SPACEDIM >= 3
    nz = 0.5 * (alpha(i, j, k+1, 0) - alpha(i, j, k-1, 0));
#else
    nz = 0.0;
#endif

    // Normalize
    const amrex::Real nmag = std::sqrt(nx*nx + ny*ny + nz*nz);
    if (nmag > VOF_TINY) {
        nx /= nmag;
        ny /= nmag;
        nz /= nmag;
    } else {
        nx = 0.0;
        ny = 0.0;
        nz = 0.0;
    }
}

// Curvature kappa = -div(n), with n the normalized alpha-gradient normal.
// For a smooth circular alpha field increasing outward, this returns about -1/R
// in 2D and -2/R in 3D under the sign convention used by csf_force.
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real csf_curvature_c0(
    int i,
    int j,
    int k,
    const amrex::Array4<const amrex::Real>& alpha,
    const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx)
{
    amrex::Real nxR, nyR, nzR, nxL, nyL, nzL;

    csf_normal_c0(i + 1, j, k, alpha, nxR, nyR, nzR);
    csf_normal_c0(i - 1, j, k, alpha, nxL, nyL, nzL);
    const amrex::Real dnxd = (nxR - nxL) / (2.0 * dx[0]);

    csf_normal_c0(i, j + 1, k, alpha, nxR, nyR, nzR);
    csf_normal_c0(i, j - 1, k, alpha, nxL, nyL, nzL);
    const amrex::Real dnyd = (nyR - nyL) / (2.0 * dx[1]);

#if AMREX_SPACEDIM == 3
    csf_normal_c0(i, j, k + 1, alpha, nxR, nyR, nzR);
    csf_normal_c0(i, j, k - 1, alpha, nxL, nyL, nzL);
    const amrex::Real dnzd = (nzR - nzL) / (2.0 * dx[2]);
#else
    const amrex::Real dnzd = 0.0;
#endif

    return -(dnxd + dnyd + dnzd);
}

// ── CSF surface tension (Brackbill 1992) ──
// Computes the volumetric surface tension force at a cell (i,j,k).
// F_s = sigma * kappa * grad(alpha)
//
// alpha    : cell-centered volume fraction field (Array4, component 0)
// dx       : cell spacing
// sigma    : surface tension coefficient [N/m]
// fx,fy,fz : output force components [N/m³]
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void csf_force(
    int i,
    int j,
    int k,
    const amrex::Array4<const amrex::Real>& alpha,
    const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx,
    amrex::Real sigma,
    amrex::Real& fx,
    amrex::Real& fy,
    amrex::Real& fz)
{
    // Step 1: interface normal via Youngs (grid-index central difference)
    amrex::Real nx, ny, nz;
    csf_normal_c0(i, j, k, alpha, nx, ny, nz);

    // Step 2: |∇α| for delta function — physical-space gradient magnitude
    const amrex::Real dax = 0.5 * (alpha(i + 1, j, k, 0) - alpha(i - 1, j, k, 0));
    const amrex::Real day = 0.5 * (alpha(i, j + 1, k, 0) - alpha(i, j - 1, k, 0));
#if AMREX_SPACEDIM == 3
    const amrex::Real daz = 0.5 * (alpha(i, j, k + 1, 0) - alpha(i, j, k - 1, 0));
#else
    const amrex::Real daz = 0.0;
#endif

#if AMREX_SPACEDIM >= 3
    const amrex::Real grad_z = daz / dx[2];
#else
    const amrex::Real grad_z = 0.0;
#endif

    const amrex::Real grad_alpha_mag = std::sqrt(
        (dax / dx[0]) * (dax / dx[0]) +
        (day / dx[1]) * (day / dx[1]) +
        grad_z * grad_z);

    // Skip if not near a resolved interface
#if AMREX_SPACEDIM >= 3
    const amrex::Real dx_max = amrex::max(amrex::max(dx[0], dx[1]), dx[2]);
#else
    const amrex::Real dx_max = amrex::max(dx[0], dx[1]);
#endif
    if (grad_alpha_mag * dx_max < 0.5) {
        fx = fy = fz = 0.0;
        return;
    }

    // Step 3: curvature kappa = -div(n)
    const amrex::Real kappa = csf_curvature_c0(i, j, k, alpha, dx);

    // Step 4: CSF body force = sigma * kappa * grad(alpha)
    const amrex::Real force_mag = sigma * kappa;
    fx = force_mag * dax / dx[0];
    fy = force_mag * day / dx[1];
#if AMREX_SPACEDIM >= 3
    fz = force_mag * daz / dx[2];
#else
    fz = 0.0;
#endif
}

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real csf_force_work(
    amrex::Real fx,
    amrex::Real fy,
    amrex::Real fz,
    amrex::Real rho,
    amrex::Real momx,
    amrex::Real momy,
    amrex::Real momz)
{
    const amrex::Real inv_rho = amrex::Real(1.0) /
        amrex::max(rho, amrex::Real(1.0e-10));
    amrex::Real work = fx * momx * inv_rho + fy * momy * inv_rho;
#if AMREX_SPACEDIM >= 3
    work += fz * momz * inv_rho;
#else
    (void)fz;
    (void)momz;
#endif
    return work;
}
