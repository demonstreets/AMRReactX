#include "pool_vof_coupling.H"

#include <AMReX_Array4.H>
#include <AMReX_Box.H>
#include <AMReX_REAL.H>

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

namespace {

void require(bool condition, const std::string& message)
{
    if (!condition) {
        std::cerr << "FAIL: " << message << "\n";
        std::exit(1);
    }
}

void require_near(double value, double expected, double tolerance,
                  const std::string& message)
{
    if (std::abs(value - expected) > tolerance) {
        std::cerr << "FAIL: " << message << ": got " << value
                  << ", expected " << expected << " +/- " << tolerance << "\n";
        std::exit(1);
    }
}

} // namespace

int main()
{
    using amrex::Array4;
    using amrex::Box;
    using amrex::IntVect;
    using amrex::Real;

    static_assert(AMREX_SPACEDIM == 2, "This smoke is configured for the 2D VOF source path");
    static_assert(NUM_ADV == 1, "The VOF alpha advected scalar must be enabled");
    static_assert(NUM_SPECIES == 1, "The smoke uses one vapor species");

    const Box box(IntVect(0, 0), IntVect(4, 4));
    constexpr int nx = 5;
    constexpr int ny = 5;
    constexpr int nz = 1;
    std::vector<Real> state_storage(nx * ny * nz * NVAR, 0.0);
    std::vector<Real> src_storage(nx * ny * nz * NVAR, 0.0);

    Array4<Real> state_arr(state_storage.data(), box, NVAR);
    Array4<Real> src_arr(src_storage.data(), box, NVAR);
    Array4<const Real> const_state(state_arr);

    for (int j = 0; j <= 4; ++j) {
        for (int i = 0; i <= 4; ++i) {
            state_arr(i, j, 0, URHO) = 1.0;
            state_arr(i, j, 0, UTEMP) = 293.15;
            state_arr(i, j, 0, UFA) = 0.0;
        }
    }

    state_arr(2, 2, 0, UFA) = 0.5;
    state_arr(1, 2, 0, UFA) = 1.0;
    state_arr(3, 2, 0, UFA) = 0.0;
    state_arr(2, 1, 0, UFA) = 0.5;
    state_arr(2, 3, 0, UFA) = 0.5;

    VOFEvap::PoolVOFParams p;
    p.antoine_A = 6.91058;
    p.antoine_B = 1189.64;
    p.antoine_C = 226.28;
    p.M_v = 0.08618;
    p.L_v = 3.65e5;
    p.h_m = 0.01;
    p.rho_v_inf = 0.0;
    p.vapor_species_idx = 0;
    p.apply_energy_sink = true;

    amrex::GpuArray<Real, AMREX_SPACEDIM> dx{0.25, 0.5};

    require(VOFEvap::is_pool_surface_cell(2, 2, 0, const_state, p),
            "interface cell with liquid neighbor is detected");
    require(!VOFEvap::is_pool_surface_cell(3, 2, 0, const_state, p),
            "gas-side cell is not a pool surface");

    const Real grad_alpha = VOFEvap::compute_interface_area_density(2, 2, 0, const_state, dx);
    require_near(grad_alpha, 2.0, 1.0e-12,
                 "2D interface area density uses x/y spacing without dx[2]");

    const Real m_dot = VOFEvap::compute_cell_evap_flux(293.15, p);
    require(m_dot > 0.0, "cell evaporation mass flux is positive");

    const Real expected_rate = m_dot * grad_alpha;
    const Real source_rate = VOFEvap::compute_pool_vof_source_rate(
        2, 2, 0, const_state, dx, p);
    require_near(source_rate, expected_rate, expected_rate * 1.0e-12,
                 "source-rate helper matches flux times interface area density");

    VOFEvap::apply_pool_vof_sources(2, 2, 0, const_state, src_arr, dx, p);
    require_near(src_arr(2, 2, 0, URHO), expected_rate, expected_rate * 1.0e-12,
                 "density source equals mass flux times interface area density");
    require_near(src_arr(2, 2, 0, UFS), expected_rate, expected_rate * 1.0e-12,
                 "vapor species source matches total mass source");
    require_near(src_arr(2, 2, 0, UEINT), -expected_rate * p.L_v,
                 std::abs(expected_rate * p.L_v) * 1.0e-12,
                 "energy sink equals latent heat times mass source");

    const Real dt = 0.05;
    const Real dV = VOFEvap::cell_volume(dx);
    require_near(dV, dx[0] * dx[1], 1.0e-15,
                 "2D pool source cell measure uses dx*dy");
    const VOFEvap::PoolSourceBudget one_step =
        VOFEvap::integrate_source_rate(source_rate, dx, dt, p);
    require_near(one_step.density_mass, src_arr(2, 2, 0, URHO) * dV * dt,
                 one_step.density_mass * 1.0e-12,
                 "time-integrated density mass matches source rate budget");
    require_near(one_step.vapor_mass, one_step.density_mass,
                 one_step.density_mass * 1.0e-12,
                 "time-integrated vapor species mass equals total evaporated mass");
    require_near(one_step.latent_energy, src_arr(2, 2, 0, UEINT) * dV * dt,
                 std::abs(one_step.latent_energy) * 1.0e-12,
                 "time-integrated latent energy matches energy source budget");

    Real cumulative_mass = 0.0;
    Real cumulative_energy = 0.0;
    constexpr int nsteps = 100;
    for (int n = 0; n < nsteps; ++n) {
        const VOFEvap::PoolSourceBudget step =
            VOFEvap::integrate_source_rate(source_rate, dx, dt, p);
        cumulative_mass += step.vapor_mass;
        cumulative_energy += step.latent_energy;
    }
    require(std::isfinite(cumulative_mass) && cumulative_mass > 0.0,
            "100-step evaporation mass budget remains positive and finite");
    require(std::isfinite(cumulative_energy) && cumulative_energy < 0.0,
            "100-step evaporation energy budget remains cooling and finite");
    require_near(cumulative_mass, nsteps * one_step.vapor_mass,
                 cumulative_mass * 1.0e-12,
                 "100-step vapor budget is the sum of per-step sources");
    require_near(cumulative_energy, nsteps * one_step.latent_energy,
                 std::abs(cumulative_energy) * 1.0e-12,
                 "100-step latent-energy budget is the sum of per-step sources");

    VOFEvap::apply_pool_vof_sources(3, 2, 0, const_state, src_arr, dx, p);
    require(src_arr(3, 2, 0, URHO) == 0.0, "non-surface cells receive no source");
    require(VOFEvap::compute_pool_vof_source_rate(3, 2, 0, const_state, dx, p) == 0.0,
            "source-rate helper returns zero for non-surface cells");

    return 0;
}
