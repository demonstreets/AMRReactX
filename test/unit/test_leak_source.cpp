#include "leak_source.H"

#include <array>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>

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

struct CellSource {
    std::array<double, 8> values{};

    double& operator()(int, int, int, int n) { return values.at(n); }
};

} // namespace

int main()
{
    namespace Leak = MyPele::Engineering::LeakSource;

    Leak::SphericalLeakSource source;
    source.center[0] = 1.0;
    source.center[1] = 2.0;
    source.center[2] = 3.0;
    source.radius = 0.5;
    source.mass_flow_rate = 2.0;
    source.velocity[0] = 4.0;
    source.velocity[1] = -1.0;
    source.velocity[2] = 0.25;
    source.specific_enthalpy = 10.0;
    source.species_index = 1;

    const double volume = Leak::sphere_volume(source.radius);
    const double mdot_vol = Leak::volumetric_mass_source(source);
    require_near(volume, 4.0 / 3.0 * 3.14159265358979323846 * 0.125, 1.0e-14,
                 "sphere volume uses radius cubed");
    require_near(mdot_vol, source.mass_flow_rate / volume, 1.0e-12,
                 "volumetric source is mass flow divided by injection volume");

    const double prob_lo[3] = {0.0, 0.0, 0.0};
    const double dx[3] = {1.0 / 16.0, 1.0 / 16.0, 1.0 / 16.0};
    const int lo[3] = {0, 0, 0};
    const int hi[3] = {15, 15, 15};
    Leak::SphericalLeakSource discrete_source = source;
    discrete_source.center[0] = 0.5;
    discrete_source.center[1] = 0.5;
    discrete_source.center[2] = 0.5;
    discrete_source.radius = 0.15;
    discrete_source.mass_flow_rate = 1.0e-5;
    const double active_volume = Leak::cell_centered_active_volume(
        discrete_source, prob_lo, dx, lo, hi);
    require(active_volume > 0.0, "discrete leak source activates cells on smoke grid");
    discrete_source.normalization_volume = active_volume;
    require_near(Leak::volumetric_mass_source(discrete_source) * active_volume,
                 discrete_source.mass_flow_rate, 1.0e-18,
                 "discrete leak normalization preserves requested mass flow");
    require(Leak::contains(source, 1.1, 2.0, 3.0), "point inside source sphere is active");
    require(!Leak::contains(source, 2.0, 2.0, 3.0), "point outside source sphere is inactive");



    Leak::PressureOrificeLeakModel orifice;
    orifice.upstream_pressure = 5.0e5;
    orifice.downstream_pressure = 101325.0;
    orifice.temperature = 300.0;
    orifice.diameter = 0.01;
    orifice.discharge_coefficient = 0.80;
    orifice.gamma = 1.405;
    orifice.gas_constant = 4124.0;
    const double orifice_area = Leak::positive_orifice_area(orifice);
    const double orifice_mdot = Leak::pressure_orifice_mass_flow_rate(orifice);
    const double orifice_velocity = Leak::pressure_orifice_exit_velocity(orifice);
    require(orifice_area > 0.0, "pressure-orifice area is positive");
    require(orifice_mdot > 0.0, "pressure-orifice mass flow is positive");
    require(orifice_velocity > 0.0, "pressure-orifice exit velocity is positive");


    Leak::PressureOrificeLeakModel ideal_z = orifice;
    ideal_z.compressibility_factor = 1.0;
    require_near(Leak::pressure_orifice_mass_flow_rate(ideal_z), orifice_mdot,
                 orifice_mdot * 1.0e-14,
                 "Z=1 pressure-orifice path preserves ideal-gas mdot");

    Leak::PressureOrificeLeakModel real_gas_z = orifice;
    real_gas_z.compressibility_factor = 1.21;
    const double real_gas_mdot =
        Leak::pressure_orifice_mass_flow_rate(real_gas_z);
    const double real_gas_velocity =
        Leak::pressure_orifice_exit_velocity(real_gas_z);
    require(real_gas_mdot > 0.0 && real_gas_mdot < orifice_mdot,
            "Z>1 pressure-orifice mass flow is lower than ideal-gas mdot");
    require_near(real_gas_mdot / orifice_mdot,
                 1.0 / std::sqrt(real_gas_z.compressibility_factor), 5.0e-13,
                 "pressure-orifice mdot scales with inverse sqrt(Z)");
    require_near(real_gas_velocity / orifice_velocity,
                 std::sqrt(real_gas_z.compressibility_factor), 5.0e-13,
                 "pressure-orifice exit velocity scales with sqrt(Z)");
    real_gas_z.compressibility_factor = 0.0;
    require(!Leak::valid_pressure_orifice_model(real_gas_z),
            "nonpositive compressibility factor is rejected");

    Leak::PressureOrificeLeakModel high_pressure = orifice;
    high_pressure.upstream_pressure = 1.0e6;
    require(Leak::pressure_orifice_mass_flow_rate(high_pressure) > orifice_mdot,
            "pressure-orifice mass flow increases with tank pressure");

    Leak::PressureOrificeLeakModel large_orifice = orifice;
    large_orifice.diameter = 0.02;
    require_near(Leak::pressure_orifice_mass_flow_rate(large_orifice) / orifice_mdot,
                 4.0, 5.0e-13,
                 "pressure-orifice mass flow scales with area in same branch");

    Leak::PressureOrificeLeakModel two_hole_a = orifice;
    two_hole_a.diameter = 0.004;
    two_hole_a.area = 0.0;
    Leak::PressureOrificeLeakModel two_hole_b = orifice;
    two_hole_b.diameter = 0.006;
    two_hole_b.area = 0.0;
    Leak::PressureOrificeLeakModel equivalent_two_hole = orifice;
    equivalent_two_hole.diameter = 0.0;
    equivalent_two_hole.area = Leak::positive_orifice_area(two_hole_a) +
                               Leak::positive_orifice_area(two_hole_b);
    const double two_hole_mdot =
        Leak::pressure_orifice_mass_flow_rate(two_hole_a) +
        Leak::pressure_orifice_mass_flow_rate(two_hole_b);
    require_near(Leak::pressure_orifice_mass_flow_rate(equivalent_two_hole),
                 two_hole_mdot, two_hole_mdot * 1.0e-13,
                 "parallel pressure-orifice holes sum as equivalent area");

    Leak::PressureOrificeLeakModel subcritical = orifice;
    subcritical.upstream_pressure = 1.5e5;
    require(!Leak::pressure_orifice_is_choked(subcritical),
            "pressure-orifice detects an unchoked pressure ratio");
    const double subcritical_mdot =
        Leak::pressure_orifice_mass_flow_rate(subcritical);
    const double subcritical_velocity =
        Leak::pressure_orifice_exit_velocity(subcritical);
    require(subcritical_mdot > 0.0,
            "subcritical pressure-orifice mass flow is positive");
    Leak::PressureOrificeLeakModel subcritical_real_gas = subcritical;
    subcritical_real_gas.compressibility_factor = 1.44;
    require_near(Leak::pressure_orifice_mass_flow_rate(subcritical_real_gas) /
                     subcritical_mdot,
                 1.0 / std::sqrt(subcritical_real_gas.compressibility_factor),
                 5.0e-13,
                 "subcritical pressure-orifice mdot scales with inverse sqrt(Z)");
    require_near(Leak::pressure_orifice_exit_velocity(subcritical_real_gas) /
                     subcritical_velocity,
                 std::sqrt(subcritical_real_gas.compressibility_factor),
                 5.0e-13,
                 "subcritical pressure-orifice exit velocity scales with sqrt(Z)");

    Leak::PressureOrificeLeakModel no_pressure_drop = orifice;
    no_pressure_drop.downstream_pressure = no_pressure_drop.upstream_pressure;
    require_near(Leak::pressure_orifice_mass_flow_rate(no_pressure_drop), 0.0, 0.0,
                 "pressure-orifice mass flow is zero without pressure drop");

    Leak::PressureOrificeLeakModel pipe_loss = orifice;
    pipe_loss.line_diameter = 0.02;
    pipe_loss.line_length = 12.0;
    pipe_loss.line_friction_factor = 0.025;
    pipe_loss.line_loss_coefficient = 4.0;
    const double loss_coeff = Leak::pipe_loss_coefficient(pipe_loss);
    const double effective_pressure =
        Leak::pressure_orifice_effective_upstream_pressure(pipe_loss);
    const double pipe_loss_mdot = Leak::pressure_orifice_mass_flow_rate(pipe_loss);
    const double pipe_loss_velocity = Leak::pressure_orifice_exit_velocity(pipe_loss);
    require(loss_coeff > pipe_loss.line_loss_coefficient,
            "pipe loss coefficient includes Darcy friction and minor losses");
    require(effective_pressure < pipe_loss.upstream_pressure,
            "pipe loss lowers effective orifice upstream pressure");
    require(effective_pressure > pipe_loss.downstream_pressure,
            "pipe loss keeps effective upstream pressure above ambient for this smoke");
    require(pipe_loss_mdot > 0.0 && pipe_loss_mdot < orifice_mdot,
            "pipe loss reduces pressure-orifice mass flow");
    require(pipe_loss_velocity > 0.0 && std::isfinite(pipe_loss_velocity),
            "pipe loss keeps pressure-orifice exit velocity finite");
    const double derived_linepack_volume = Leak::linepack_volume(pipe_loss, 0.0);
    const double explicit_linepack_volume = 0.0125;
    require_near(derived_linepack_volume,
                 0.25 * 3.14159265358979323846 *
                     pipe_loss.line_diameter * pipe_loss.line_diameter *
                     pipe_loss.line_length,
                 derived_linepack_volume * 1.0e-14,
                 "linepack volume derives from pipe diameter and length");
    require_near(Leak::linepack_volume(pipe_loss, explicit_linepack_volume),
                 explicit_linepack_volume, explicit_linepack_volume * 1.0e-14,
                 "explicit linepack volume overrides pipe geometry volume");

    Leak::PressureOrificeLeakModel blowdown_orifice = orifice;
    blowdown_orifice.upstream_pressure = 8.0e5;
    const double tank_volume = 0.10;
    const double ideal_tank_mass = Leak::tank_blowdown_mass_from_pressure(
        blowdown_orifice.upstream_pressure, tank_volume,
        blowdown_orifice.gas_constant, blowdown_orifice.temperature,
        1.0);
    const double real_gas_tank_mass = Leak::tank_blowdown_mass_from_pressure(
        blowdown_orifice.upstream_pressure, tank_volume,
        blowdown_orifice.gas_constant, blowdown_orifice.temperature,
        1.25);
    require_near(real_gas_tank_mass / ideal_tank_mass, 1.0 / 1.25, 1.0e-14,
                 "tank inventory from pressure scales with inverse Z");
    require_near(Leak::tank_blowdown_pressure_from_mass(
                     real_gas_tank_mass, tank_volume,
                     blowdown_orifice.gas_constant, blowdown_orifice.temperature,
                     1.25),
                 blowdown_orifice.upstream_pressure,
                 blowdown_orifice.upstream_pressure * 1.0e-14,
                 "tank pressure from mass round-trips with Z");
    const auto early_interval = Leak::tank_blowdown_interval(
        blowdown_orifice, tank_volume, 0.0, 0.01, 128);
    const auto late_interval = Leak::tank_blowdown_interval(
        blowdown_orifice, tank_volume, 0.05, 0.01, 128);
    require(early_interval.average_mass_flow_rate > 0.0,
            "tank blowdown produces positive initial mass flow");
    require(late_interval.average_mass_flow_rate > 0.0,
            "tank blowdown produces positive later mass flow");
    require(late_interval.average_mass_flow_rate < early_interval.average_mass_flow_rate,
            "tank blowdown mass flow decreases as tank pressure falls");
    require(late_interval.pressure_start < early_interval.pressure_start,
            "tank blowdown pressure decreases over elapsed time");
    require_near(early_interval.average_mass_flow_rate * 0.01,
                 early_interval.injected_mass,
                 early_interval.injected_mass * 1.0e-12,
                 "tank blowdown average mdot integrates to interval mass");
    require(early_interval.cumulative_injected_mass >= early_interval.injected_mass,
            "tank blowdown cumulative mass includes interval mass");

    Leak::PressureOrificeLeakModel blowdown_pipe_loss = blowdown_orifice;
    blowdown_pipe_loss.line_diameter = 0.02;
    blowdown_pipe_loss.line_length = 12.0;
    blowdown_pipe_loss.line_friction_factor = 0.025;
    blowdown_pipe_loss.line_loss_coefficient = 4.0;
    const auto pipe_loss_interval = Leak::tank_blowdown_interval(
        blowdown_pipe_loss, tank_volume, 0.0, 0.01, 128);
    require(pipe_loss_interval.average_mass_flow_rate > 0.0,
            "tank blowdown with pipe loss still injects mass");
    require(pipe_loss_interval.average_mass_flow_rate <
                early_interval.average_mass_flow_rate,
            "pipe loss reduces tank-blowdown interval mass flow");
    const double linepack_storage_volume = Leak::linepack_volume(
        blowdown_pipe_loss, 0.0);
    const auto linepack_interval = Leak::tank_blowdown_interval(
        blowdown_pipe_loss, linepack_storage_volume, 0.0, 0.01, 128);
    require(linepack_storage_volume > 0.0,
            "linepack blowdown derives positive storage volume from pipe geometry");
    require(linepack_interval.average_mass_flow_rate > 0.0,
            "linepack blowdown produces positive initial mass flow");
    require(linepack_interval.pressure_end < linepack_interval.pressure_start,
            "linepack blowdown pressure decreases over the interval");
    require_near(linepack_interval.injected_mass,
                 linepack_interval.average_mass_flow_rate * 0.01,
                 linepack_interval.injected_mass * 1.0e-12,
                 "linepack blowdown average mdot integrates to interval mass");

    Leak::ValveSchedule delayed_ramp;
    delayed_ramp.open_time = 0.01;
    delayed_ramp.ramp_time = 0.02;
    delayed_ramp.initial_fraction = 0.0;
    delayed_ramp.final_fraction = 1.0;
    require(Leak::valid_valve_schedule(delayed_ramp),
            "delayed ramp valve schedule is valid");
    require(!Leak::valve_schedule_is_always_open(delayed_ramp),
            "delayed ramp valve schedule is not always open");
    require(Leak::valve_schedule_can_close(delayed_ramp),
            "delayed ramp valve schedule can close the orifice");
    require_near(Leak::valve_schedule_fraction(delayed_ramp, 0.0), 0.0, 0.0,
                 "valve schedule is closed before rupture time");
    require_near(Leak::valve_schedule_fraction(delayed_ramp, 0.01), 0.0, 0.0,
                 "valve schedule remains at initial fraction at rupture time");
    require_near(Leak::valve_schedule_fraction(delayed_ramp, 0.02), 0.5,
                 1.0e-14, "valve schedule ramps linearly");
    require_near(Leak::valve_schedule_fraction(delayed_ramp, 0.03), 1.0,
                 1.0e-14, "valve schedule reaches final fraction");
    Leak::ValveSchedule invalid_schedule = delayed_ramp;
    invalid_schedule.final_fraction = 1.2;
    require(!Leak::valid_valve_schedule(invalid_schedule),
            "valve schedule rejects fractions above one");
    invalid_schedule = delayed_ramp;
    invalid_schedule.open_time = -1.0e-3;
    require(!Leak::valid_valve_schedule(invalid_schedule),
            "valve schedule rejects negative times");

    const auto linepack_closed_interval = Leak::tank_blowdown_interval_scheduled(
        blowdown_pipe_loss, linepack_storage_volume, 0.0, 0.005, 128,
        delayed_ramp);
    require_near(linepack_closed_interval.injected_mass, 0.0, 0.0,
                 "closed valve linepack interval injects no mass");
    require_near(linepack_closed_interval.pressure_start,
                 linepack_closed_interval.pressure_end,
                 linepack_closed_interval.pressure_start * 1.0e-14,
                 "closed valve linepack interval holds pressure constant");
    const auto linepack_ramp_interval = Leak::tank_blowdown_interval_scheduled(
        blowdown_pipe_loss, linepack_storage_volume, 0.015, 0.01, 128,
        delayed_ramp);
    const auto linepack_always_open_interval = Leak::tank_blowdown_interval(
        blowdown_pipe_loss, linepack_storage_volume, 0.015, 0.01, 128);
    require(linepack_ramp_interval.injected_mass > 0.0,
            "ramping valve linepack interval injects mass");
    require(linepack_ramp_interval.injected_mass <
                linepack_always_open_interval.injected_mass,
            "ramping valve linepack interval injects less than always-open flow");

    CellSource src;
    constexpr int density = 0;
    constexpr int velx = 1;
    constexpr int vely = 2;
    constexpr int velz = 3;
    constexpr int enthalpy = 4;
    constexpr int first_species = 5;
    constexpr int num_species = 2;

    const bool applied = Leak::apply_single_species_source(
        src, 0, 0, 0, 1.1, 2.0, 3.0, source, density, velx, vely, velz,
        enthalpy, first_species, num_species);
    require(applied, "source applies inside sphere for valid species");
    require_near(src.values[density], mdot_vol, mdot_vol * 1.0e-14,
                 "density source equals injected fuel mass source");
    require_near(src.values[first_species + source.species_index], mdot_vol,
                 mdot_vol * 1.0e-14,
                 "fuel species source equals total density source");
    require_near(src.values[first_species], 0.0, 1.0e-14,
                 "non-injected species receives no mass source");
    require_near(src.values[velx], mdot_vol * source.velocity[0], 1.0e-12,
                 "x momentum/velocity source scales with injected velocity");
    require_near(src.values[vely], mdot_vol * source.velocity[1], 1.0e-12,
                 "y momentum/velocity source scales with injected velocity");
    require_near(src.values[velz], mdot_vol * source.velocity[2], 1.0e-12,
                 "z momentum/velocity source scales with injected velocity");
    require_near(src.values[enthalpy], mdot_vol * source.specific_enthalpy, 1.0e-12,
                 "enthalpy source scales with injected mass source");

    CellSource outside;
    require(!Leak::apply_single_species_source(outside, 0, 0, 0, 2.0, 2.0, 3.0,
                                               source, density, velx, vely, velz,
                                               enthalpy, first_species, num_species),
            "source does not apply outside sphere");
    require_near(outside.values[density], 0.0, 1.0e-14,
                 "inactive source leaves density unchanged");

    source.species_index = num_species;
    CellSource invalid_species;
    require(!Leak::apply_single_species_source(invalid_species, 0, 0, 0,
                                               1.1, 2.0, 3.0, source,
                                               density, velx, vely, velz,
                                               enthalpy, first_species, num_species),
            "invalid species index is rejected");

    return 0;
}
