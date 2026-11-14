#ifndef MYPELE_ENGINEERING_LEAK_SOURCE_H
#define MYPELE_ENGINEERING_LEAK_SOURCE_H

#include <cmath>
#include <limits>

#if defined(AMREX_GPU_HOST_DEVICE)
#define MYPELE_LEAK_HD AMREX_GPU_HOST_DEVICE
#elif defined(AMREX_GPU_DEVICE)
#define MYPELE_LEAK_HD AMREX_GPU_DEVICE
#else
#define MYPELE_LEAK_HD
#endif

namespace MyPele::Engineering::LeakSource {

struct SphericalLeakSource {
    double center[3] = {0.0, 0.0, 0.0};
    double radius = 0.0;
    double mass_flow_rate = 0.0;
    double velocity[3] = {0.0, 0.0, 0.0};
    double specific_enthalpy = 0.0;
    double normalization_volume = 0.0;
    int species_index = 0;
};

struct PressureOrificeLeakModel {
    double upstream_pressure = 0.0;
    double downstream_pressure = 0.0;
    double temperature = 0.0;
    double diameter = 0.0;
    double area = 0.0;
    double discharge_coefficient = 1.0;
    double line_diameter = 0.0;
    double line_length = 0.0;
    double line_friction_factor = 0.0;
    double line_loss_coefficient = 0.0;
    double gamma = 1.4;
    double gas_constant = 1.0;
    double compressibility_factor = 1.0;
};

struct ValveSchedule {
    double open_time = 0.0;
    double ramp_time = 0.0;
    double initial_fraction = 1.0;
    double final_fraction = 1.0;
};

inline bool valid_valve_schedule(const ValveSchedule& schedule)
{
    return schedule.open_time >= 0.0 && schedule.ramp_time >= 0.0 &&
           schedule.initial_fraction >= 0.0 &&
           schedule.initial_fraction <= 1.0 &&
           schedule.final_fraction >= 0.0 &&
           schedule.final_fraction <= 1.0;
}

inline double valve_schedule_fraction(const ValveSchedule& schedule,
                                      const double time)
{
    if (!valid_valve_schedule(schedule)) {
        return 0.0;
    }
    const double t = time > 0.0 ? time : 0.0;
    if (t <= schedule.open_time) {
        return schedule.initial_fraction;
    }
    if (schedule.ramp_time <= 0.0) {
        return schedule.final_fraction;
    }
    const double ramp = (t - schedule.open_time) / schedule.ramp_time;
    if (ramp >= 1.0) {
        return schedule.final_fraction;
    }
    return schedule.initial_fraction +
           ramp * (schedule.final_fraction - schedule.initial_fraction);
}

inline bool valve_schedule_can_close(const ValveSchedule& schedule)
{
    return valid_valve_schedule(schedule) &&
           (schedule.initial_fraction <= 0.0 || schedule.final_fraction <= 0.0);
}

inline bool valve_schedule_is_always_open(const ValveSchedule& schedule)
{
    return valid_valve_schedule(schedule) &&
           schedule.initial_fraction == 1.0 && schedule.final_fraction == 1.0;
}

inline double positive_orifice_area(const PressureOrificeLeakModel& model)
{
    constexpr double pi = 3.141592653589793238462643383279502884;
    if (model.area > 0.0) {
        return model.area;
    }
    return model.diameter > 0.0 ? 0.25 * pi * model.diameter * model.diameter
                                : 0.0;
}

inline PressureOrificeLeakModel valve_scaled_orifice_model(
    const PressureOrificeLeakModel& model,
    const double open_fraction)
{
    PressureOrificeLeakModel scaled = model;
    const double fraction = open_fraction > 0.0 ? open_fraction : 0.0;
    scaled.area = positive_orifice_area(model) * fraction;
    scaled.diameter = 0.0;
    return scaled;
}

inline double positive_line_area(const PressureOrificeLeakModel& model)
{
    constexpr double pi = 3.141592653589793238462643383279502884;
    return model.line_diameter > 0.0
               ? 0.25 * pi * model.line_diameter * model.line_diameter
               : positive_orifice_area(model);
}

inline double pipe_loss_coefficient(const PressureOrificeLeakModel& model)
{
    double total = model.line_loss_coefficient > 0.0
                       ? model.line_loss_coefficient
                       : 0.0;
    if (model.line_friction_factor > 0.0 && model.line_length > 0.0 &&
        model.line_diameter > 0.0) {
        total += model.line_friction_factor * model.line_length /
                 model.line_diameter;
    }
    return total;
}


inline double linepack_volume(const PressureOrificeLeakModel& model,
                              const double explicit_volume)
{
    constexpr double pi = 3.141592653589793238462643383279502884;
    if (explicit_volume > 0.0) {
        return explicit_volume;
    }
    return model.line_diameter > 0.0 && model.line_length > 0.0
               ? 0.25 * pi * model.line_diameter * model.line_diameter *
                     model.line_length
               : 0.0;
}

inline double positive_compressibility_factor(
    const PressureOrificeLeakModel& model)
{
    return model.compressibility_factor > 0.0
               ? model.compressibility_factor
               : 0.0;
}

inline bool valid_pressure_orifice_model(const PressureOrificeLeakModel& model)
{
    return model.upstream_pressure > 0.0 && model.downstream_pressure >= 0.0 &&
           model.temperature > 0.0 && positive_orifice_area(model) > 0.0 &&
           positive_line_area(model) > 0.0 &&
           model.discharge_coefficient > 0.0 && model.gamma > 1.0 &&
           model.gas_constant > 0.0 &&
           positive_compressibility_factor(model) > 0.0;
}

inline double critical_pressure_ratio(const double gamma)
{
    return gamma > 1.0 ? std::pow(2.0 / (gamma + 1.0), gamma / (gamma - 1.0))
                       : 0.0;
}

inline double pressure_orifice_mass_flow_rate_no_line_loss(
    const PressureOrificeLeakModel& model)
{
    if (!valid_pressure_orifice_model(model) ||
        model.downstream_pressure >= model.upstream_pressure) {
        return 0.0;
    }

    const double area = positive_orifice_area(model);
    const double gamma = model.gamma;
    const double pressure_ratio = model.downstream_pressure / model.upstream_pressure;
    const double base = model.discharge_coefficient * area * model.upstream_pressure;
    if (pressure_ratio <= critical_pressure_ratio(gamma)) {
        const double exponent = (gamma + 1.0) / (2.0 * (gamma - 1.0));
        return base * std::sqrt(gamma / (positive_compressibility_factor(model) *
                                          model.gas_constant * model.temperature)) *
               std::pow(2.0 / (gamma + 1.0), exponent);
    }

    const double term = std::pow(pressure_ratio, 2.0 / gamma) -
                        std::pow(pressure_ratio, (gamma + 1.0) / gamma);
    return term > 0.0
               ? base * std::sqrt((2.0 * gamma /
                                    (positive_compressibility_factor(model) *
                                     model.gas_constant * model.temperature *
                                     (gamma - 1.0))) *
                                   term)
               : 0.0;
}

inline double pressure_orifice_effective_upstream_pressure(
    const PressureOrificeLeakModel& model)
{
    if (!valid_pressure_orifice_model(model) ||
        model.downstream_pressure >= model.upstream_pressure) {
        return model.upstream_pressure;
    }

    const double loss_coeff = pipe_loss_coefficient(model);
    if (loss_coeff <= 0.0) {
        return model.upstream_pressure;
    }

    const double line_area = positive_line_area(model);
    const double rho_line = model.upstream_pressure /
                            (positive_compressibility_factor(model) *
                             model.gas_constant * model.temperature);
    if (line_area <= 0.0 || rho_line <= 0.0) {
        return model.upstream_pressure;
    }

    double lo = model.downstream_pressure;
    double hi = model.upstream_pressure;
    for (int iter = 0; iter < 80; ++iter) {
        const double mid = 0.5 * (lo + hi);
        PressureOrificeLeakModel trial = model;
        trial.upstream_pressure = mid;
        trial.line_diameter = 0.0;
        trial.line_length = 0.0;
        trial.line_friction_factor = 0.0;
        trial.line_loss_coefficient = 0.0;
        const double mdot = pressure_orifice_mass_flow_rate_no_line_loss(trial);
        const double velocity = mdot / (rho_line * line_area);
        const double pressure_loss = 0.5 * loss_coeff * rho_line * velocity * velocity;
        const double residual = mid + pressure_loss - model.upstream_pressure;
        if (residual > 0.0) {
            hi = mid;
        } else {
            lo = mid;
        }
    }
    return 0.5 * (lo + hi);
}

inline bool pressure_orifice_is_choked(const PressureOrificeLeakModel& model)
{
    if (!valid_pressure_orifice_model(model) ||
        model.downstream_pressure >= model.upstream_pressure) {
        return false;
    }
    const double effective_upstream =
        pressure_orifice_effective_upstream_pressure(model);
    return effective_upstream > model.downstream_pressure &&
           model.downstream_pressure / effective_upstream <=
               critical_pressure_ratio(model.gamma);
}

inline double pressure_orifice_mass_flow_rate(const PressureOrificeLeakModel& model)
{
    if (!valid_pressure_orifice_model(model) ||
        model.downstream_pressure >= model.upstream_pressure) {
        return 0.0;
    }
    PressureOrificeLeakModel effective_model = model;
    effective_model.upstream_pressure =
        pressure_orifice_effective_upstream_pressure(model);
    effective_model.line_diameter = 0.0;
    effective_model.line_length = 0.0;
    effective_model.line_friction_factor = 0.0;
    effective_model.line_loss_coefficient = 0.0;
    return pressure_orifice_mass_flow_rate_no_line_loss(effective_model);
}

inline double pressure_orifice_exit_velocity(const PressureOrificeLeakModel& model)
{
    if (!valid_pressure_orifice_model(model) ||
        model.downstream_pressure >= model.upstream_pressure) {
        return 0.0;
    }

    PressureOrificeLeakModel effective_model = model;
    effective_model.upstream_pressure =
        pressure_orifice_effective_upstream_pressure(model);
    effective_model.line_diameter = 0.0;
    effective_model.line_length = 0.0;
    effective_model.line_friction_factor = 0.0;
    effective_model.line_loss_coefficient = 0.0;
    if (effective_model.downstream_pressure >= effective_model.upstream_pressure) {
        return 0.0;
    }

    const double gamma = effective_model.gamma;
    const double pressure_ratio =
        effective_model.downstream_pressure / effective_model.upstream_pressure;
    if (pressure_ratio <= critical_pressure_ratio(gamma)) {
        return std::sqrt(gamma *
                         positive_compressibility_factor(effective_model) *
                         effective_model.gas_constant *
                         effective_model.temperature * (2.0 / (gamma + 1.0)));
    }

    const double term = 1.0 - std::pow(pressure_ratio, (gamma - 1.0) / gamma);
    return term > 0.0
               ? std::sqrt(2.0 * gamma / (gamma - 1.0) *
                           positive_compressibility_factor(effective_model) *
                           effective_model.gas_constant *
                           effective_model.temperature * term)
               : 0.0;
}

struct TankBlowdownInterval {
    double pressure_start = 0.0;
    double pressure_end = 0.0;
    double mass_start = 0.0;
    double mass_end = 0.0;
    double injected_mass = 0.0;
    double cumulative_injected_mass = 0.0;
    double average_mass_flow_rate = 0.0;
};

inline double tank_blowdown_mass_from_pressure(
    const double pressure,
    const double tank_volume,
    const double gas_constant,
    const double temperature)
{
    return pressure > 0.0 && tank_volume > 0.0 && gas_constant > 0.0 &&
                   temperature > 0.0
               ? pressure * tank_volume / (gas_constant * temperature)
               : 0.0;
}

inline double tank_blowdown_mass_from_pressure(
    const double pressure,
    const double tank_volume,
    const double gas_constant,
    const double temperature,
    const double compressibility_factor)
{
    return pressure > 0.0 && tank_volume > 0.0 && gas_constant > 0.0 &&
                   temperature > 0.0 && compressibility_factor > 0.0
               ? pressure * tank_volume /
                     (compressibility_factor * gas_constant * temperature)
               : 0.0;
}

inline double tank_blowdown_pressure_from_mass(
    const double mass,
    const double tank_volume,
    const double gas_constant,
    const double temperature)
{
    return mass > 0.0 && tank_volume > 0.0 && gas_constant > 0.0 &&
                   temperature > 0.0
               ? mass * gas_constant * temperature / tank_volume
               : 0.0;
}

inline double tank_blowdown_pressure_from_mass(
    const double mass,
    const double tank_volume,
    const double gas_constant,
    const double temperature,
    const double compressibility_factor)
{
    return mass > 0.0 && tank_volume > 0.0 && gas_constant > 0.0 &&
                   temperature > 0.0 && compressibility_factor > 0.0
               ? mass * compressibility_factor * gas_constant * temperature /
                     tank_volume
               : 0.0;
}

inline bool valid_tank_blowdown_model(const PressureOrificeLeakModel& model,
                                      const double tank_volume)
{
    return valid_pressure_orifice_model(model) && tank_volume > 0.0 &&
           model.upstream_pressure > model.downstream_pressure;
}

inline int positive_substeps(const int requested)
{
    return requested > 0 ? requested : 1;
}

inline int duration_scaled_substeps(
    const double duration,
    const double reference_dt,
    const int requested_substeps)
{
    const int base_substeps = positive_substeps(requested_substeps);
    if (duration <= 0.0 || reference_dt <= 0.0) {
        return base_substeps;
    }
    const double intervals = std::ceil(duration / reference_dt);
    const double scaled = intervals * static_cast<double>(base_substeps);
    const double max_int = static_cast<double>(std::numeric_limits<int>::max());
    return scaled < max_int ? static_cast<int>(scaled) : std::numeric_limits<int>::max();
}

inline double advance_tank_blowdown_mass(
    const PressureOrificeLeakModel& base_model,
    const double tank_volume,
    const double initial_mass,
    const double duration,
    const int requested_substeps)
{
    if (!valid_tank_blowdown_model(base_model, tank_volume) ||
        initial_mass <= 0.0 || duration <= 0.0) {
        return initial_mass;
    }

    const int substeps = positive_substeps(requested_substeps);
    const double sub_dt = duration / static_cast<double>(substeps);
    const double ambient_mass = tank_blowdown_mass_from_pressure(
        base_model.downstream_pressure, tank_volume, base_model.gas_constant,
        base_model.temperature, positive_compressibility_factor(base_model));
    double mass = initial_mass;
    for (int n = 0; n < substeps; ++n) {
        if (mass <= ambient_mass) {
            return ambient_mass;
        }
        PressureOrificeLeakModel step_model = base_model;
        step_model.upstream_pressure = tank_blowdown_pressure_from_mass(
            mass, tank_volume, base_model.gas_constant, base_model.temperature,
            positive_compressibility_factor(base_model));
        const double mdot = pressure_orifice_mass_flow_rate(step_model);
        if (mdot <= 0.0) {
            return mass;
        }
        const double releasable = mass - ambient_mass;
        const double dm = mdot * sub_dt < releasable ? mdot * sub_dt : releasable;
        mass -= dm;
    }
    return mass > ambient_mass ? mass : ambient_mass;
}

inline double advance_tank_blowdown_mass_scheduled(
    const PressureOrificeLeakModel& base_model,
    const double tank_volume,
    const double initial_mass,
    const double start_time,
    const double duration,
    const int requested_substeps,
    const ValveSchedule& valve_schedule)
{
    if (!valid_tank_blowdown_model(base_model, tank_volume) ||
        initial_mass <= 0.0 || duration <= 0.0 ||
        !valid_valve_schedule(valve_schedule)) {
        return initial_mass;
    }

    const int substeps = positive_substeps(requested_substeps);
    const double sub_dt = duration / static_cast<double>(substeps);
    const double ambient_mass = tank_blowdown_mass_from_pressure(
        base_model.downstream_pressure, tank_volume, base_model.gas_constant,
        base_model.temperature, positive_compressibility_factor(base_model));
    double mass = initial_mass;
    const double t0 = start_time > 0.0 ? start_time : 0.0;
    for (int n = 0; n < substeps; ++n) {
        if (mass <= ambient_mass) {
            return ambient_mass;
        }
        const double sub_time = t0 + (static_cast<double>(n) + 0.5) * sub_dt;
        const double open_fraction =
            valve_schedule_fraction(valve_schedule, sub_time);
        if (open_fraction <= 0.0) {
            continue;
        }
        PressureOrificeLeakModel step_model = valve_scaled_orifice_model(
            base_model, open_fraction);
        step_model.upstream_pressure = tank_blowdown_pressure_from_mass(
            mass, tank_volume, base_model.gas_constant, base_model.temperature,
            positive_compressibility_factor(base_model));
        const double mdot = pressure_orifice_mass_flow_rate(step_model);
        if (mdot <= 0.0) {
            continue;
        }
        const double releasable = mass - ambient_mass;
        const double dm = mdot * sub_dt < releasable ? mdot * sub_dt : releasable;
        mass -= dm;
    }
    return mass > ambient_mass ? mass : ambient_mass;
}

inline TankBlowdownInterval tank_blowdown_interval_scheduled(
    const PressureOrificeLeakModel& base_model,
    const double tank_volume,
    const double elapsed_time,
    const double interval_dt,
    const int requested_substeps,
    const ValveSchedule& valve_schedule)
{
    TankBlowdownInterval result;
    if (!valid_tank_blowdown_model(base_model, tank_volume) ||
        interval_dt <= 0.0 || !valid_valve_schedule(valve_schedule)) {
        return result;
    }

    const int substeps = positive_substeps(requested_substeps);
    const double initial_mass = tank_blowdown_mass_from_pressure(
        base_model.upstream_pressure, tank_volume, base_model.gas_constant,
        base_model.temperature, positive_compressibility_factor(base_model));
    const double start_time = elapsed_time > 0.0 ? elapsed_time : 0.0;
    const int start_substeps = duration_scaled_substeps(
        start_time, interval_dt, substeps);
    result.mass_start = advance_tank_blowdown_mass_scheduled(
        base_model, tank_volume, initial_mass, 0.0, start_time,
        start_substeps, valve_schedule);
    result.mass_end = advance_tank_blowdown_mass_scheduled(
        base_model, tank_volume, result.mass_start, start_time, interval_dt,
        substeps, valve_schedule);
    result.pressure_start = tank_blowdown_pressure_from_mass(
        result.mass_start, tank_volume, base_model.gas_constant,
        base_model.temperature, positive_compressibility_factor(base_model));
    result.pressure_end = tank_blowdown_pressure_from_mass(
        result.mass_end, tank_volume, base_model.gas_constant,
        base_model.temperature, positive_compressibility_factor(base_model));
    result.injected_mass = result.mass_start > result.mass_end
                               ? result.mass_start - result.mass_end
                               : 0.0;
    result.cumulative_injected_mass = initial_mass > result.mass_end
                                          ? initial_mass - result.mass_end
                                          : 0.0;
    result.average_mass_flow_rate = result.injected_mass / interval_dt;
    return result;
}

inline TankBlowdownInterval tank_blowdown_interval(
    const PressureOrificeLeakModel& base_model,
    const double tank_volume,
    const double elapsed_time,
    const double interval_dt,
    const int requested_substeps)
{
    TankBlowdownInterval result;
    if (!valid_tank_blowdown_model(base_model, tank_volume) || interval_dt <= 0.0) {
        return result;
    }

    const int substeps = positive_substeps(requested_substeps);
    const double initial_mass = tank_blowdown_mass_from_pressure(
        base_model.upstream_pressure, tank_volume, base_model.gas_constant,
        base_model.temperature, positive_compressibility_factor(base_model));
    const double start_time = elapsed_time > 0.0 ? elapsed_time : 0.0;
    const int start_substeps = duration_scaled_substeps(
        start_time, interval_dt, substeps);
    result.mass_start = advance_tank_blowdown_mass(
        base_model, tank_volume, initial_mass, start_time, start_substeps);
    result.mass_end = advance_tank_blowdown_mass(
        base_model, tank_volume, result.mass_start, interval_dt, substeps);
    result.pressure_start = tank_blowdown_pressure_from_mass(
        result.mass_start, tank_volume, base_model.gas_constant,
        base_model.temperature, positive_compressibility_factor(base_model));
    result.pressure_end = tank_blowdown_pressure_from_mass(
        result.mass_end, tank_volume, base_model.gas_constant,
        base_model.temperature, positive_compressibility_factor(base_model));
    result.injected_mass = result.mass_start > result.mass_end
                               ? result.mass_start - result.mass_end
                               : 0.0;
    result.cumulative_injected_mass = initial_mass > result.mass_end
                                          ? initial_mass - result.mass_end
                                          : 0.0;
    result.average_mass_flow_rate = result.injected_mass / interval_dt;
    return result;
}

MYPELE_LEAK_HD inline double sphere_volume(const double radius)
{
    constexpr double pi = 3.141592653589793238462643383279502884;
    return radius > 0.0 ? (4.0 / 3.0) * pi * radius * radius * radius : 0.0;
}

MYPELE_LEAK_HD inline double normalization_volume(const SphericalLeakSource& source)
{
    return source.normalization_volume > 0.0
               ? source.normalization_volume
               : sphere_volume(source.radius);
}

MYPELE_LEAK_HD inline double volumetric_mass_source(const SphericalLeakSource& source)
{
    const double volume = normalization_volume(source);
    return volume > 0.0 ? source.mass_flow_rate / volume : 0.0;
}

MYPELE_LEAK_HD inline bool contains(const SphericalLeakSource& source,
                                    const double x,
                                    const double y,
                                    const double z)
{
    const double dx = x - source.center[0];
    const double dy = y - source.center[1];
    const double dz = z - source.center[2];
    return source.radius > 0.0 &&
           dx * dx + dy * dy + dz * dz < source.radius * source.radius;
}


MYPELE_LEAK_HD inline double cell_volume(const double dx[3])
{
    return dx[0] > 0.0 && dx[1] > 0.0 && dx[2] > 0.0
               ? dx[0] * dx[1] * dx[2]
               : 0.0;
}

inline double cell_centered_active_volume(const SphericalLeakSource& source,
                                          const double prob_lo[3],
                                          const double dx[3],
                                          const int lo[3],
                                          const int hi[3])
{
    const double vol = cell_volume(dx);
    if (vol <= 0.0 || source.radius <= 0.0) {
        return 0.0;
    }

    long long active_cells = 0;
    for (int k = lo[2]; k <= hi[2]; ++k) {
        const double z = prob_lo[2] + (static_cast<double>(k) + 0.5) * dx[2];
        for (int j = lo[1]; j <= hi[1]; ++j) {
            const double y = prob_lo[1] + (static_cast<double>(j) + 0.5) * dx[1];
            for (int i = lo[0]; i <= hi[0]; ++i) {
                const double x = prob_lo[0] + (static_cast<double>(i) + 0.5) * dx[0];
                if (contains(source, x, y, z)) {
                    ++active_cells;
                }
            }
        }
    }
    return static_cast<double>(active_cells) * vol;
}

template <typename SrcArray>
MYPELE_LEAK_HD inline bool apply_single_species_source(
    SrcArray&& src,
    const int i,
    const int j,
    const int k,
    const double x,
    const double y,
    const double z,
    const SphericalLeakSource& source,
    const int density_comp,
    const int velx_comp,
    const int vely_comp,
    const int velz_comp,
    const int enthalpy_comp,
    const int first_species_comp,
    const int num_species)
{
    if (!contains(source, x, y, z) || source.species_index < 0 ||
        source.species_index >= num_species) {
        return false;
    }

    const double mdot_vol = volumetric_mass_source(source);
    if (mdot_vol == 0.0) {
        return false;
    }

    src(i, j, k, density_comp) += mdot_vol;
    src(i, j, k, first_species_comp + source.species_index) += mdot_vol;
    src(i, j, k, velx_comp) += mdot_vol * source.velocity[0];
    src(i, j, k, vely_comp) += mdot_vol * source.velocity[1];
    src(i, j, k, velz_comp) += mdot_vol * source.velocity[2];
    src(i, j, k, enthalpy_comp) += mdot_vol * source.specific_enthalpy;
    return true;
}

} // namespace MyPele::Engineering::LeakSource

#undef MYPELE_LEAK_HD

#endif
