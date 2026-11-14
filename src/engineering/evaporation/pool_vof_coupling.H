#pragma once
// ============================================================
// pool_vof_coupling.H — VOF-to-evaporation source term bridge
//
// Links the VOF volume fraction field α (PeleC UFA) to the pool
// evaporation model, computing cell-local mass flux via Antoine
// equation and applying mass/species/energy source terms through
// PeleC's problem_modify_ext_sources() hook.
//
// Data flow (task spec):
//   VOF α(UFA) → pool surface cell detection → m_dot_vapor (Antoine)
//     → source terms on ext_src (species vapour, density, energy sink)
//     → combustion sees fuel vapor → heat feedback → T↑ → m_dot↑ (self-sustaining)
//
// Target code: PeleC (native VOF support, UFA/IndexDefines.H)
//
// Example integration in prob.H's problem_modify_ext_sources:
//
//   #include "pool_vof_coupling.H"
//
//   VOFEvap::PoolVOFParams evp;
//   evp.antoine_A = 6.95719;    // propane
//   evp.antoine_B = 1424.255;
//   evp.antoine_C = -45.957;
//   evp.M_v       = 0.04410;
//   evp.L_v       = 4.26e5;
//   evp.vapor_species_idx = C3H8_ID;  // 0-based offset in UFS
//
//   auto const& arrs   = ext_src.arrays();
//   auto const& sarrs  = state_old.const_arrays();
//   auto const& dx_arr = geomdata.CellSizeArray();
//   amrex::ParallelFor(ext_src, [=] AMREX_GPU_DEVICE (int nbx, int i, int j, int k)
//   {
//       VOFEvap::apply_pool_vof_sources(i, j, k,
//           sarrs[nbx], arrs[nbx], dx_arr, evp);
//   });
//   amrex::Gpu::streamSynchronize();
//
// Acceptance criteria (task spec):
//   1. Pool surface cells correctly identified (α ≈ 0.5 cells)
//   2. Evaporation produces gas-phase fuel vapor (Y_vapor > 0 above pool)
//   3. Evaporative cooling lowers pool surface temperature
//   4. 100 steps zero-crash
// ============================================================

#include <AMReX_Gpu.H>
#include <AMReX_Array4.H>
#include <AMReX_REAL.H>
#include <AMReX_GpuQualifiers.H>
#include <cmath>
#include "IndexDefines.H"        // UFA, UTEMP, URHO, UEINT, UFS, UFX, NUM_ADV
#include "evaporation_model.H"   // Antoine, saturation_density, evaporation_flux

namespace VOFEvap {

// ============================================================
// PoolVOFParams — physical parameters for VOF-coupled evaporation
// ============================================================
struct PoolVOFParams
{
    // ── Pool surface detection thresholds ─────────────────
    amrex::Real alpha_lo       = 0.3;  // lower bound for interface cell
    amrex::Real alpha_hi       = 0.7;  // upper bound for interface cell
    amrex::Real liquid_thresh  = 0.7;  // neighbor α > this → liquid side

    // ── Antoine parameters for the evaporating species ────
    amrex::Real antoine_A = 0.0;  // Antoine A (mmHg-form)
    amrex::Real antoine_B = 0.0;  // Antoine B [°C]
    amrex::Real antoine_C = 0.0;  // Antoine C [°C]
    amrex::Real M_v       = 0.0;  // molecular weight [kg/mol]
    amrex::Real L_v       = 0.0;  // latent heat of vaporization [J/kg]
    amrex::Real h_v_form  = 0.0;  // vapour formation enthalpy [J/kg]

    // ── Mass transfer parameters ──────────────────────────
    amrex::Real h_m       = 0.01; // mass transfer coefficient [m/s]
    amrex::Real rho_v_inf = 0.0;  // ambient vapour density [kg/m³]

    // ── Species index (0-based offset from UFS) ───────────
    int vapor_species_idx = 0;

    // ── Control flags ─────────────────────────────────────
    bool apply_energy_sink  = true;   // latent heat cooling
    bool apply_momentum_src = false;  // vapour momentum (usually off)
};

// ============================================================
// is_pool_surface_cell — VOF-based pool surface detection
//
// PeleC stores UFA = rho * alpha (conserved form). We recover
// alpha = UFA / max(URHO, epsilon) for the volume-fraction check.
//
// Criterion (task spec §1):
//   α_cell ∈ [alpha_lo, alpha_hi]  AND
//   at least one direct neighbor has α > liquid_thresh.
//
// This avoids the gas-side interface "tail" and ensures we
// are on the liquid→gas emission side.
// ============================================================
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
bool is_pool_surface_cell(
    int i, int j, int k,
    const amrex::Array4<const amrex::Real>& state,
    const PoolVOFParams& p,
    int alpha_offset = 0)
{
    using amrex::Real;

#if NUM_ADV == 0
    amrex::ignore_unused(i, j, k, state, p, alpha_offset);
    return false;
#else
    const int alpha_idx = UFA + alpha_offset;

    // Recover volume fraction α from conserved UFA = rho*α
    auto alpha_at = [&](int ii, int jj, int kk) -> Real {
        const Real rho = state(ii, jj, kk, URHO);
        constexpr Real eps = 1.0e-30;
        return (rho > eps) ? state(ii, jj, kk, alpha_idx) / rho : 0.0;
    };

    const Real a_cell = alpha_at(i, j, k);

    // Step 1: within interface band
    if (a_cell < p.alpha_lo || a_cell > p.alpha_hi) return false;

    // Step 2: has a liquid-side neighbor (6-neighbor stencil)
    if (alpha_at(i + 1, j, k) > p.liquid_thresh) return true;
    if (alpha_at(i - 1, j, k) > p.liquid_thresh) return true;
    if (alpha_at(i, j + 1, k) > p.liquid_thresh) return true;
    if (alpha_at(i, j - 1, k) > p.liquid_thresh) return true;
#if AMREX_SPACEDIM >= 3
    if (alpha_at(i, j, k + 1) > p.liquid_thresh) return true;
    if (alpha_at(i, j, k - 1) > p.liquid_thresh) return true;
#endif

    return false;
#endif
}

// ============================================================
// compute_interface_area_density — |∇α| via central differences
//
// Uses α = UFA/URHO (volume fraction, not conserved form).
// For a sharp interface, ∫|∇α| dV = interface area.
// Converts mass flux [kg/(m²·s)] → volumetric source [kg/(m³·s)].
// ============================================================
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real compute_interface_area_density(
    int i, int j, int k,
    const amrex::Array4<const amrex::Real>& state,
    const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx,
    int alpha_offset = 0)
{
    using amrex::Real;

    const int alpha_idx = UFA + alpha_offset;
    constexpr Real eps = 1.0e-30;

    // Recover α = UFA/URHO at a stencil point
    auto alpha_at = [&](int ii, int jj, int kk) -> Real {
        const Real rho = state(ii, jj, kk, URHO);
        return (rho > eps) ? state(ii, jj, kk, alpha_idx) / rho : 0.0;
    };

    const Real dax = 0.5 * (alpha_at(i + 1, j, k) - alpha_at(i - 1, j, k));
    const Real day = 0.5 * (alpha_at(i, j + 1, k) - alpha_at(i, j - 1, k));
#if AMREX_SPACEDIM >= 3
    const Real daz = 0.5 * (alpha_at(i, j, k + 1) - alpha_at(i, j, k - 1));
#else
    const Real daz = 0.0;
#endif

#if AMREX_SPACEDIM >= 3
    const Real grad_z = daz / dx[2];
#else
    const Real grad_z = 0.0;
#endif

    return std::sqrt(
        (dax / dx[0]) * (dax / dx[0]) +
        (day / dx[1]) * (day / dx[1]) +
        grad_z * grad_z);
}

// ============================================================
// compute_cell_evap_flux — evaporation mass flux at cell T
//
//   P_sat(T) = 10^{A − B/(t[°C]+C)} × 133.322 Pa
//   ρ_sat    = P_sat · M_v / (R · T)
//   m_dot''  = h_m · (ρ_sat − ρ_v,inf)           [kg/(m²·s)]
// ============================================================
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real compute_cell_evap_flux(
    amrex::Real T,
    const PoolVOFParams& p)
{
    using amrex::Real;

    // Valid temperature range
    if (T < 200.0 || T > 2000.0) return 0.0;

    const Real rho_sat = Evaporation::saturation_density(
        T, 101325.0, p.M_v,
        p.antoine_A, p.antoine_B, p.antoine_C);

    return Evaporation::evaporation_flux(p.h_m, rho_sat, p.rho_v_inf);
}

// ============================================================
// compute_pool_vof_source_rate -- volumetric evaporation source
//
// Returns m_dot'' * |grad alpha| [kg/(m^3 s)] for a surface cell,
// or zero when the cell is not an active evaporating interface.
// ============================================================
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real compute_pool_vof_source_rate(
    int i, int j, int k,
    const amrex::Array4<const amrex::Real>& state,
    const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx,
    const PoolVOFParams& p,
    int alpha_offset = 0)
{
    using amrex::Real;

    if (!is_pool_surface_cell(i, j, k, state, p, alpha_offset)) return 0.0;

    const Real T = state(i, j, k, UTEMP);
    if (T < 200.0 || T > 2000.0) return 0.0;

    const Real m_dot = compute_cell_evap_flux(T, p);
    if (m_dot <= 1.0e-20) return 0.0;

    const Real grad_alpha = compute_interface_area_density(
        i, j, k, state, dx, alpha_offset);
    constexpr Real tiny = 1.0e-20;
    if (grad_alpha < tiny) return 0.0;

    return m_dot * grad_alpha;
}

struct PoolSourceBudget
{
    amrex::Real density_mass = 0.0;
    amrex::Real vapor_mass = 0.0;
    amrex::Real latent_energy = 0.0;
};

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real cell_volume(const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx)
{
    amrex::Real volume = 1.0;
    for (int d = 0; d < AMREX_SPACEDIM; ++d) {
        if (dx[d] <= 0.0) return 0.0;
        volume *= dx[d];
    }
    return volume;
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
PoolSourceBudget integrate_source_rate(
    amrex::Real src_rate,
    const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx,
    amrex::Real dt,
    const PoolVOFParams& p)
{
    PoolSourceBudget budget;
    const amrex::Real measure = cell_volume(dx) * dt;
    if (src_rate <= 0.0 || measure <= 0.0) return budget;

    budget.density_mass = src_rate * measure;
    budget.vapor_mass = src_rate * measure;
    if (p.apply_energy_sink) {
        budget.latent_energy = -budget.density_mass * p.L_v;
    }
    return budget;
}

// ============================================================
// apply_pool_vof_sources -- per-cell VOF evaporation source terms
//
// Call from within ParallelFor in problem_modify_ext_sources().
//
// Actions (task spec 3):
//   a. Species vapour mass:  src(UFS+vapor_idx) += m_dot'' * |grad alpha|
//   b. Total density:        src(URHO)           += m_dot'' * |grad alpha|
//   c. Energy sink:          src(UEINT)          -= m_dot'' * |grad alpha| * L_v
//   d. Momentum:             omitted (low-speed evaporation)
// ============================================================
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void apply_pool_vof_sources(
    int i, int j, int k,
    const amrex::Array4<const amrex::Real>& state,
    amrex::Array4<amrex::Real>& src,
    const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx,
    const PoolVOFParams& p,
    int alpha_offset = 0)
{
    using amrex::Real;

    const Real src_rate = compute_pool_vof_source_rate(
        i, j, k, state, dx, p, alpha_offset);
    if (src_rate <= 0.0) return;

    // a. Species vapour mass (primary effect)
    src(i, j, k, UFS + p.vapor_species_idx) += src_rate;

    // b. Total density
    src(i, j, k, URHO) += src_rate;

    // c. Energy sink: latent heat of vaporization. UEINT is internal
    //    energy (rho*e), so this is a volumetric energy source.
    if (p.apply_energy_sink) {
        src(i, j, k, UEINT) -= src_rate * p.L_v;
    }

    // d. Momentum omitted for low-speed evaporation.
}

} // namespace VOFEvap
