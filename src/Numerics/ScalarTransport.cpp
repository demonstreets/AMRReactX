#include "Numerics/ScalarTransport.H"

#include "AMR/BoundaryConditions.H"
#include "Physics/SourceTerms.H"

#include <AMReX_Array4.H>
#include <AMReX_Box.H>
#include <AMReX_GpuQualifiers.H>
#include <AMReX_MFIter.H>
#include <AMReX_REAL.H>

#include <algorithm>
#include <cmath>

namespace amrreactx {

namespace {

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real limited_y(amrex::Real y) noexcept
{
    if (y < 0.0) {
        return 0.0;
    }
    if (y > 1.0) {
        return 1.0;
    }
    return y;
}

} // namespace

void initialize_state(amrex::MultiFab& state, const amrex::Geometry& geom, const RuntimeParams& params)
{
    const auto dx = geom.CellSizeArray();
    const auto prob_lo = geom.ProbLoArray();
    const amrex::Real rho0 = params.rho0;
    const amrex::Real wind_x = params.wind[0];
    const amrex::Real wind_y = params.wind[1];
    const amrex::Real wind_z = params.wind[2];
    const int init_type = params.init_type;
    const amrex::Real init_x = params.init_center[0];
    const amrex::Real init_y = params.init_center[1];
    const amrex::Real init_z = params.init_center[2];
    const amrex::Real init_sigma = params.init_sigma;
    const amrex::Real init_amplitude = params.init_amplitude;

    for (amrex::MFIter mfi(state); mfi.isValid(); ++mfi) {
        const amrex::Box& bx = mfi.validbox();
        const amrex::Array4<amrex::Real> arr = state.array(mfi);

        amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
            amrex::Real y_leak = 0.0;
            if (init_type == Gaussian) {
                const amrex::Real x = prob_lo[0] + (static_cast<amrex::Real>(i) + 0.5) * dx[0];
                const amrex::Real y = prob_lo[1] + (static_cast<amrex::Real>(j) + 0.5) * dx[1];
                const amrex::Real z = prob_lo[2] + (static_cast<amrex::Real>(k) + 0.5) * dx[2];
                const amrex::Real r2 = (x - init_x) * (x - init_x)
                                     + (y - init_y) * (y - init_y)
                                     + (z - init_z) * (z - init_z);
                y_leak = init_amplitude * std::exp(-r2 / (2.0 * init_sigma * init_sigma));
            }
            arr(i, j, k, Rho) = rho0;
            arr(i, j, k, Uvel) = wind_x;
            arr(i, j, k, Vvel) = wind_y;
            arr(i, j, k, Wvel) = wind_z;
            arr(i, j, k, YLeak) = y_leak;
        });
    }
}

void advance_scalar(amrex::MultiFab& state,
                    amrex::MultiFab& next_state,
                    const amrex::Geometry& geom,
                    const RuntimeParams& params)
{
    const auto dx = geom.CellSizeArray();
    const auto prob_lo = geom.ProbLoArray();
    const auto domain = geom.Domain();
    const auto dom_lo = domain.smallEnd();
    const auto dom_hi = domain.bigEnd();
    KernelParams kparams{};
    fill_kernel_params(kparams, params);

    state.FillBoundary(geom.periodicity());

    for (amrex::MFIter mfi(state); mfi.isValid(); ++mfi) {
        const amrex::Box& bx = mfi.validbox();
        const amrex::Array4<const amrex::Real> s = state.const_array(mfi);
        const amrex::Array4<amrex::Real> n = next_state.array(mfi);

        amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
            const amrex::Real yc = s(i, j, k, YLeak);

            const int bcxlo = kparams.bc_lo[0];
            const int bcxhi = kparams.bc_hi[0];
            const int bcylo = kparams.bc_lo[1];
            const int bcyhi = kparams.bc_hi[1];
            const int bczlo = kparams.bc_lo[2];
            const int bczhi = kparams.bc_hi[2];
            const amrex::Real ymx = (i == dom_lo[0]) ? boundary_y(yc, bcxlo, kparams) : s(i - 1, j, k, YLeak);
            const amrex::Real ypx = (i == dom_hi[0]) ? boundary_y(yc, bcxhi, kparams) : s(i + 1, j, k, YLeak);
            const amrex::Real ymy = (j == dom_lo[1]) ? boundary_y(yc, bcylo, kparams) : s(i, j - 1, k, YLeak);
            const amrex::Real ypy = (j == dom_hi[1]) ? boundary_y(yc, bcyhi, kparams) : s(i, j + 1, k, YLeak);
            const amrex::Real ymz = (k == dom_lo[2]) ? boundary_y(yc, bczlo, kparams) : s(i, j, k - 1, YLeak);
            const amrex::Real ypz = (k == dom_hi[2]) ? boundary_y(yc, bczhi, kparams) : s(i, j, k + 1, YLeak);

            const amrex::Real fxp = (i == dom_hi[0])
                ? face_flux(yc, kparams.wind[0], bcxhi, 1, kparams)
                : (kparams.wind[0] >= 0.0 ? kparams.wind[0] * yc : kparams.wind[0] * ypx);
            const amrex::Real fxm = (i == dom_lo[0])
                ? face_flux(yc, kparams.wind[0], bcxlo, -1, kparams)
                : (kparams.wind[0] >= 0.0 ? kparams.wind[0] * ymx : kparams.wind[0] * yc);
            const amrex::Real fyp = (j == dom_hi[1])
                ? face_flux(yc, kparams.wind[1], bcyhi, 1, kparams)
                : (kparams.wind[1] >= 0.0 ? kparams.wind[1] * yc : kparams.wind[1] * ypy);
            const amrex::Real fym = (j == dom_lo[1])
                ? face_flux(yc, kparams.wind[1], bcylo, -1, kparams)
                : (kparams.wind[1] >= 0.0 ? kparams.wind[1] * ymy : kparams.wind[1] * yc);
            const amrex::Real fzp = (k == dom_hi[2])
                ? face_flux(yc, kparams.wind[2], bczhi, 1, kparams)
                : (kparams.wind[2] >= 0.0 ? kparams.wind[2] * yc : kparams.wind[2] * ypz);
            const amrex::Real fzm = (k == dom_lo[2])
                ? face_flux(yc, kparams.wind[2], bczlo, -1, kparams)
                : (kparams.wind[2] >= 0.0 ? kparams.wind[2] * ymz : kparams.wind[2] * yc);

            const amrex::Real adv = -((fxp - fxm) / dx[0]
                                    + (fyp - fym) / dx[1]
                                    + (fzp - fzm) / dx[2]);

            const amrex::Real diff = kparams.diffusion
                * ((ypx - 2.0 * yc + ymx) / (dx[0] * dx[0])
                 + (ypy - 2.0 * yc + ymy) / (dx[1] * dx[1])
                 + (ypz - 2.0 * yc + ymz) / (dx[2] * dx[2]));

            const amrex::Real x = prob_lo[0] + (static_cast<amrex::Real>(i) + 0.5) * dx[0];
            const amrex::Real y = prob_lo[1] + (static_cast<amrex::Real>(j) + 0.5) * dx[1];
            const amrex::Real z = prob_lo[2] + (static_cast<amrex::Real>(k) + 0.5) * dx[2];
            const amrex::Real source = scalar_source(x, y, z, kparams);

            n(i, j, k, Rho) = kparams.rho0;
            n(i, j, k, Uvel) = kparams.wind[0];
            n(i, j, k, Vvel) = kparams.wind[1];
            n(i, j, k, Wvel) = kparams.wind[2];
            n(i, j, k, YLeak) = limited_y(yc + kparams.dt * (adv + diff + source));
        });
    }
}

StabilityInfo compute_stability(const amrex::Geometry& geom, const RuntimeParams& params)
{
    const auto dx = geom.CellSizeArray();
    StabilityInfo info;
    amrex::Real inverse_advective_dt = 0.0;
    amrex::Real inverse_diffusive_dt = 0.0;
    for (int d = 0; d < AMREX_SPACEDIM; ++d) {
        const amrex::Real directional_cfl = std::abs(params.wind[d]) * params.dt / dx[d];
        info.advective_cfl += directional_cfl;
        info.max_directional_cfl = std::max(info.max_directional_cfl, directional_cfl);
        info.diffusion_number += params.diffusion * params.dt / (dx[d] * dx[d]);
        inverse_advective_dt += std::abs(params.wind[d]) / dx[d];
        inverse_diffusive_dt += params.diffusion / (dx[d] * dx[d]);
    }
    if (inverse_advective_dt > 0.0) {
        info.dt_advective_limit = params.cfl / inverse_advective_dt;
    }
    if (inverse_diffusive_dt > 0.0) {
        info.dt_diffusion_limit = params.diff_cfl / inverse_diffusive_dt;
    }
    info.recommended_dt = std::min(info.dt_advective_limit, info.dt_diffusion_limit);
    return info;
}

amrex::Real compute_dt(const amrex::Geometry& geom, const RuntimeParams& params, amrex::Real time)
{
    amrex::Real dt = params.dt;
    if (params.use_auto_dt != 0) {
        dt = compute_stability(geom, params).recommended_dt;
    }
    if (params.stop_time >= 0.0) {
        dt = std::min(dt, params.stop_time - time);
    }
    return std::max(dt, amrex::Real(0.0));
}

} // namespace amrreactx
