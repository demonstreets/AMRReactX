#ifndef PELEC_SPECIES_FLUX_LIMITER_H
#define PELEC_SPECIES_FLUX_LIMITER_H

#include <AMReX_Gpu.H>
#include <AMReX_REAL.H>
#include <cmath>

// Limit reconstructed compositions before EOS/Riemann evaluation. Donor
// states are checked, not repaired: an invalid evolved cell must fail visibly.
template <int N>
AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
bool pc_bounded_face_composition(amrex::Real* face, amrex::Real* donor)
{
  amrex::Real donor_sum = 0.0;
  amrex::Real face_sum = 0.0;
  for (int n = 0; n < N; ++n) {
    if (!std::isfinite(donor[n]) || donor[n] < -1.e-12 || donor[n] > 1.0 + 1.e-12)
      return false;
    donor[n] = amrex::max(amrex::Real(0.0), donor[n]);
    donor_sum += donor[n];
    if (!std::isfinite(face[n])) face[n] = donor[n];
    face[n] = amrex::max(amrex::Real(0.0), amrex::min(amrex::Real(1.0), face[n]));
    face_sum += face[n];
  }
  if (!(donor_sum > 0.0) || std::abs(donor_sum - 1.0) > 1.e-8) return false;
  for (int n = 0; n < N; ++n) {
    donor[n] /= donor_sum;
    face[n] = face_sum > 0.0 ? face[n] / face_sum : donor[n];
  }
  return true;
}

// A common convex weight preserves sum(F_species)=F_mass. Limit outgoing
// high-order species fluxes against a conservative donor-cell budget shared
// among the 2*ndim faces. A zero donor species cannot be removed. If the
// low-order mass flux exhausts that per-face budget, revert to donor upwind
// composition; density/CFL admissibility remains the hydro solver's contract.
template <int N>
AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
void pc_bounded_species_flux(
  amrex::Real mass_flux, amrex::Real donor_rho, const amrex::Real* donor,
  const amrex::Real* face, amrex::Real dx, amrex::Real dt, int ndim,
  amrex::Real* species_flux)
{
  amrex::Real theta = 1.0;
  const amrex::Real courant = dt > 0.0 ?
    std::abs(mass_flux) * dt / (donor_rho * dx) : 0.0;
  if (courant > 0.0) {
    const amrex::Real ratio = 1.0 / (2.0 * ndim * courant);
    for (int n = 0; n < N; ++n) {
      const amrex::Real cap = donor[n] * amrex::max(amrex::Real(1.0), ratio);
      if (face[n] > cap && face[n] > donor[n]) {
        theta = amrex::min(theta, (cap - donor[n]) / (face[n] - donor[n]));
      }
    }
  }
  theta = amrex::max(amrex::Real(0.0), amrex::min(amrex::Real(1.0), theta));
  for (int n = 0; n < N; ++n)
    species_flux[n] = mass_flux * (donor[n] + theta * (face[n] - donor[n]));
}
#endif
