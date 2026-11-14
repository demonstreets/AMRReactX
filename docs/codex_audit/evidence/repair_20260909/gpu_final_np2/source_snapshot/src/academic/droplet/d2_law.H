#pragma once

#include <algorithm>
#include <cmath>
#include <limits>

namespace MyPele::Academic::Droplet {

struct D2LawFuel {
    double liquid_density = 0.0;
    double liquid_cp = 0.0;
    double latent_heat = 0.0;
    double boiling_temperature = 0.0;
};

struct D2LawAmbient {
    double temperature = 0.0;
    double pressure = 0.0;
    double evaporation_constant = 0.0;
    double thermal_relaxation_time = 0.0;
};

struct DropletState {
    double diameter = 0.0;
    double temperature = 0.0;
    double mass = 0.0;
};

struct D2LawBudget {
    double evaporated_mass = 0.0;
    double latent_energy = 0.0;
    double elapsed = 0.0;
    bool fully_evaporated = false;
};

inline bool is_positive_finite(const double value)
{
    return std::isfinite(value) && value > 0.0;
}

inline double droplet_mass_from_diameter(const double diameter, const D2LawFuel& fuel)
{
    if (!is_positive_finite(diameter) || !is_positive_finite(fuel.liquid_density)) {
        return 0.0;
    }
    constexpr double pi = 3.141592653589793238462643383279502884;
    return fuel.liquid_density * pi * diameter * diameter * diameter / 6.0;
}


inline double normalized_d2_from_mass_fraction(const double mass_fraction)
{
    if (!std::isfinite(mass_fraction) || mass_fraction <= 0.0) {
        return 0.0;
    }
    return std::pow(mass_fraction, 2.0 / 3.0);
}

inline double equivalent_diameter_from_mass_fraction(
    const double initial_diameter,
    const double mass_fraction)
{
    if (!is_positive_finite(initial_diameter)) {
        return 0.0;
    }
    return initial_diameter * std::sqrt(normalized_d2_from_mass_fraction(mass_fraction));
}

inline double d2_lifetime(const DropletState& state, const D2LawAmbient& ambient)
{
    if (!is_positive_finite(state.diameter) ||
        !is_positive_finite(ambient.evaporation_constant)) {
        return std::numeric_limits<double>::infinity();
    }
    return state.diameter * state.diameter / ambient.evaporation_constant;
}

inline double relax_temperature(
    const double initial_temperature,
    const D2LawFuel& fuel,
    const D2LawAmbient& ambient,
    const double dt)
{
    if (!std::isfinite(initial_temperature) || !std::isfinite(ambient.temperature) ||
        dt <= 0.0 || !is_positive_finite(ambient.thermal_relaxation_time)) {
        return initial_temperature;
    }

    const double target = is_positive_finite(fuel.boiling_temperature)
        ? std::min(ambient.temperature, fuel.boiling_temperature)
        : ambient.temperature;
    const double alpha = 1.0 - std::exp(-dt / ambient.thermal_relaxation_time);
    return initial_temperature + alpha * (target - initial_temperature);
}

inline D2LawBudget advance_d2_law(
    DropletState& state,
    const D2LawFuel& fuel,
    const D2LawAmbient& ambient,
    const double dt)
{
    D2LawBudget budget{};
    if (dt <= 0.0 || !std::isfinite(dt) || !is_positive_finite(state.diameter)) {
        state.mass = droplet_mass_from_diameter(state.diameter, fuel);
        return budget;
    }

    const double old_mass = droplet_mass_from_diameter(state.diameter, fuel);
    const double old_d2 = state.diameter * state.diameter;
    const double new_d2 = is_positive_finite(ambient.evaporation_constant)
        ? std::max(0.0, old_d2 - ambient.evaporation_constant * dt)
        : old_d2;

    state.diameter = std::sqrt(new_d2);
    state.temperature = relax_temperature(state.temperature, fuel, ambient, dt);
    state.mass = droplet_mass_from_diameter(state.diameter, fuel);

    budget.evaporated_mass = std::max(0.0, old_mass - state.mass);
    budget.latent_energy = is_positive_finite(fuel.latent_heat)
        ? budget.evaporated_mass * fuel.latent_heat
        : 0.0;
    budget.elapsed = dt;
    budget.fully_evaporated = (new_d2 == 0.0);
    return budget;
}

inline D2LawBudget advance_d2_law_until(
    DropletState& state,
    const D2LawFuel& fuel,
    const D2LawAmbient& ambient,
    const double requested_dt)
{
    const double life = d2_lifetime(state, ambient);
    const double dt = std::isfinite(life) ? std::min(requested_dt, life) : requested_dt;
    return advance_d2_law(state, fuel, ambient, dt);
}

} // namespace MyPele::Academic::Droplet
