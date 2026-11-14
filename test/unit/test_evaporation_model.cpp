#include "antoine_data.H"
#include "evaporation_model.H"
#include "pool_evaporation.H"

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

} // namespace

int main()
{
    using namespace Evaporation;

    const auto propane = lookup_antoine("C3H8");
    require(propane.found, "propane alias lookup");
    require_near(propane.M_v, 0.04410, 1.0e-8, "propane molecular weight");
    require(!lookup_antoine("not-a-species").found, "unknown species lookup fails");

    const auto water = lookup_antoine("water");
    require(water.found, "water lookup");
    const double water_psat_100c = saturation_pressure(373.15, water.A, water.B, water.C);
    require(std::isfinite(water_psat_100c), "water saturation pressure is finite");
    require_near(water_psat_100c, 101336.0, 350.0,
                 "water Antoine pressure near one atmosphere at 100 C");

    require(friction_velocity(10.0, 0.0) == 0.0, "zero friction coefficient gives zero u_star");
    require(mass_transfer_coefficient(0.1, 0.41, 1.5, 0.7) > 0.0,
            "nominal mass-transfer coefficient is positive");
    require(mass_transfer_coefficient(0.1, 0.41, 0.0, 0.7) == 0.0,
            "zero Schmidt number is guarded");
    require(mass_transfer_coefficient(0.1, 0.41, 0.01, 0.1) == 0.0,
            "nonpositive denominator is guarded");

    const auto hexane = lookup_antoine("gasoline");
    require(hexane.found, "gasoline alias maps to n-hexane surrogate");
    const double rho_sat = saturation_density(293.15, 101325.0, hexane.M_v,
                                              hexane.A, hexane.B, hexane.C);
    require(std::isfinite(rho_sat) && rho_sat > 0.0,
            "hexane saturation density is positive and finite at room temperature");
    require(saturation_density(0.0, 101325.0, hexane.M_v,
                               hexane.A, hexane.B, hexane.C) == 0.0,
            "nonphysical temperature density is guarded");
    require(evaporation_flux(0.01, rho_sat, 0.0) > 0.0,
            "dry-air evaporation flux is positive");
    require(evaporation_flux(0.01, rho_sat, rho_sat) == 0.0,
            "saturated ambient does not produce negative evaporation");

    PoolGeometry geom;
    geom.x_lo = 0.0;
    geom.x_hi = 2.0;
    geom.y_lo = 0.0;
    geom.y_hi = 0.0;
    geom.z_lo = -1.0;
    geom.z_hi = 1.0;

    EvaporationParams params;
    params.model_type = ModelType::mass_transfer;
    params.u_ref = 3.0;
    params.T_pool = 293.15;
    params.C_f = 0.001;
    params.Sc_t = 0.7;
    params.D_air = 1.0e-5;
    params.M_v = hexane.M_v;
    params.L_v = hexane.L_v;
    params.h_v_form = hexane.h_v_form;
    params.antoine_A = hexane.A;
    params.antoine_B = hexane.B;
    params.antoine_C = hexane.C;
    params.vapor_species_name = "n-hexane";

    PoolEvaporation pool;
    pool.configure(geom, params);
    require(pool.is_valid(), "valid mass-transfer pool configuration");
    require(pool.get_mass_flux() > 0.0, "pool mass-transfer flux is positive");
    require(pool.cell_in_pool(1.0, 0.0, 0.0), "point inside pool footprint");
    require(!pool.cell_in_pool(3.0, 0.0, 0.0), "point outside pool footprint");

    PoolGeometry invalid_geom = geom;
    invalid_geom.y_hi = 0.1;
    pool.configure(invalid_geom, params);
    require(!pool.is_valid(), "invalid nonplanar pool geometry is rejected");
    require(pool.get_mass_flux() == 0.0, "invalid reconfiguration clears old flux");

    params.model_type = ModelType::constant;
    params.constant_flux = -1.0e-3;
    pool.configure(geom, params);
    require(!pool.is_valid(), "negative constant evaporation flux is rejected");
    require(pool.get_mass_flux() == 0.0, "negative constant flux is cleared");

    return 0;
}
