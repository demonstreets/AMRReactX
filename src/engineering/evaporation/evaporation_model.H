#pragma once

#include <cmath>

namespace Evaporation {

// ============================================================
// Universal gas constant
// ============================================================
constexpr double R_universal = 8.314;   // J/(mol·K)

// ============================================================
// friction_velocity — compute friction velocity u* from
// reference wind speed and surface friction coefficient.
//
//   u* = sqrt(C_f) * u_ref
//
// Parameters:
//   u_ref   reference wind speed [m/s]
//   C_f     surface friction coefficient (default 0.001 for water)
// Returns:
//   friction velocity [m/s]
// ============================================================
inline double friction_velocity(double u_ref, double C_f)
{
    if (C_f <= 0.0) return 0.0;
    return std::sqrt(C_f) * u_ref;
}

// ============================================================
// mass_transfer_coefficient — compute convective mass transfer
// coefficient k_m using the surface renewal theory
// (FLACS-style formulation).
//
//   k_m = (u* / κ) / (Sc_t + 5.0 · Sc^{2/3} − 5.0)
//
// Parameters:
//   u_star   friction velocity [m/s]
//   kappa    von Kármán constant (typically 0.41)
//   Sc       laminar Schmidt number  ν / D
//   Sc_t     turbulent Schmidt number (typically 0.7)
// Returns:
//   mass transfer coefficient k_m [m/s]
// ============================================================
inline double mass_transfer_coefficient(double u_star, double kappa,
                                         double Sc, double Sc_t)
{
    if (u_star <= 0.0 || kappa <= 0.0 || Sc <= 0.0 || Sc_t <= 0.0) {
        return 0.0;
    }

    double denom = Sc_t + 5.0 * std::pow(Sc, 2.0 / 3.0) - 5.0;
    if (denom <= 0.0) {
        return 0.0;
    }
    return (u_star / kappa) / denom;
}

// ============================================================
// saturation_pressure — evaluate the Antoine equation.
//
//   Antoine form (Celsius, mmHg):
//     log10 P_sat[mmHg] = A − B / (t[°C] + C)
//
//   Conversion to Pa:
//     P_sat[Pa] = 10^{A − B / (t + C)} × 133.322
//
// Parameters:
//   T    temperature [K]
//   A    Antoine A coefficient (mmHg-form)
//   B    Antoine B coefficient [°C]
//   C    Antoine C coefficient [°C]
// Returns:
//   saturation pressure [Pa]
// ============================================================
inline double saturation_pressure(double T, double A, double B, double C)
{
    double t = T - 273.15;       // K → °C
    if (t + C <= 0.0) return 0.0; // outside Antoine's valid temperature range
    double exponent = A - B / (t + C);
    double P_mmHg = std::pow(10.0, exponent);
    return P_mmHg * 133.322;     // mmHg → Pa
}

// ============================================================
// saturation_density — compute saturated vapour density at a
// given temperature using the ideal gas law.
//
//   ρ_v,sat = P_sat · M_v / (R · T)
//
// Uses saturation_pressure() internally.
//
// Parameters:
//   T      temperature [K]
//   P_atm  ambient pressure [Pa] (reserved for
//          future boiling-point clipping)
//   M_v    vapour molecular weight [kg/mol]
//   A, B, C  Antoine coefficients
// Returns:
//   saturated vapour density [kg/m³]
// ============================================================
inline double saturation_density(double T, double /*P_atm*/,
                                  double M_v, double A, double B, double C)
{
    if (T <= 0.0 || M_v <= 0.0) {
        return 0.0;
    }

    double P_sat = saturation_pressure(T, A, B, C);
    return P_sat * M_v / (R_universal * T);
}

// ============================================================
// evaporation_flux — compute evaporation mass flux (Level 1
// convective mass transfer model).
//
//   ḿ'' = k_m · (ρ_v,sat − ρ_v,∞)
//
// Parameters:
//   k_m       mass transfer coefficient [m/s]
//   rho_sat   saturated vapour density at pool temperature [kg/m³]
//   rho_inf   ambient vapour density (typically ≈ 0) [kg/m³]
// Returns:
//   evaporation mass flux [kg/(m²·s)]
// ============================================================
inline double evaporation_flux(double k_m, double rho_sat, double rho_inf)
{
    if (k_m <= 0.0 || rho_sat <= rho_inf) {
        return 0.0;
    }
    return k_m * (rho_sat - rho_inf);
}

} // namespace Evaporation