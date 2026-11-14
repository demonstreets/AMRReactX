#pragma once

#include <cmath>
#include <string>
#include <algorithm>
#include <cctype>
#include <cstdlib>
#include "k_epsilon_constants.H"

/// @file wind_profile.H
/// Phase 2.6 — Atmospheric boundary-layer wind profile (log-law, k-ε inlet)

namespace Wind {

// ─── WindConfig ──────────────────────────────────────────────────────

struct WindConfig {
    double direction_deg;     // meteorological wind direction [°] (0=N, clockwise)
    double u_ref;             // reference velocity at reference height [m/s]
    double z_ref;             // reference height [m]
    double z0;                // aerodynamic roughness length [m]
    double T_inlet;           // inlet temperature [K]

    // derived / computed
    double u_star;            // friction velocity [m/s]
    double wind_x, wind_z;    // wind velocity vector in domain coords [m/s]
                              //   +x = east, +z = north, +y = vertical
};

// ─── Compass direction → degrees ────────────────────────────────────

inline double resolve_direction(const std::string& input) {
    std::string key;
    key.reserve(input.size());
    for (unsigned char c : input) {
        if (!std::isspace(c)) {
            key.push_back(static_cast<char>(std::toupper(c)));
        }
    }

    if (key == "N" || key == "NORTH") return 0.0;
    if (key == "NNE") return 22.5;
    if (key == "NE" || key == "NORTHEAST") return 45.0;
    if (key == "ENE") return 67.5;
    if (key == "E" || key == "EAST") return 90.0;
    if (key == "ESE") return 112.5;
    if (key == "SE" || key == "SOUTHEAST") return 135.0;
    if (key == "SSE") return 157.5;
    if (key == "S" || key == "SOUTH") return 180.0;
    if (key == "SSW") return 202.5;
    if (key == "SW" || key == "SOUTHWEST") return 225.0;
    if (key == "WSW") return 247.5;
    if (key == "W" || key == "WEST") return 270.0;
    if (key == "WNW") return 292.5;
    if (key == "NW" || key == "NORTHWEST") return 315.0;
    if (key == "NNW") return 337.5;

    // numeric fallback, e.g. "202.5", "45", "0"
    char* end = nullptr;
    const double value = std::strtod(input.c_str(), &end);
    return (end != input.c_str()) ? value : 0.0;
}

/// Overload for plain double — pass-through convenience.
inline double resolve_direction(double deg) {
    return deg;
}

// ─── z₀ sanitisation ────────────────────────────────────────────────

/// Returns 1e-4 if z0 ≤ 0, otherwise z0 unchanged.
inline double sanitize_z0(double z0) {
    return (z0 <= 0.0) ? 1.0e-4 : z0;
}

// ─── Friction velocity ──────────────────────────────────────────────

/// u_* = κ · u_ref / ln(z_eff / z₀)
/// Guard: if z_eff ≤ z₀ (z_ref too small or z₀ too large), return 0.
inline double friction_velocity(double u_ref, double z_ref, double z0,
                                 double kappa = 0.41) {
    if (u_ref <= 0.0 || kappa <= 0.0) return 0.0;
    double z0_eff = sanitize_z0(z0);
    if (z_ref <= z0_eff) return 0.0;
    double z_eff = std::max(z_ref, z0_eff * 1.01);
    return kappa * u_ref / std::log(z_eff / z0_eff);
}

// ─── Log-law velocity ───────────────────────────────────────────────

/// u(z) = (u_*/κ) · ln( max(z, z₀) / z₀ )
inline double log_law_velocity(double z, double u_star, double z0,
                                double kappa = 0.41) {
    if (u_star <= 0.0 || kappa <= 0.0) return 0.0;
    double z0_eff = sanitize_z0(z0);
    double z_eff  = std::max(z, z0_eff);
    return (u_star / kappa) * std::log(z_eff / z0_eff);
}

// ─── Power-law velocity profile ───────────────────────────────────

/// u(z) = u_ref * (max(z, z_min) / z_ref)^alpha.
inline double power_law_velocity(double z, double u_ref, double z_ref,
                                 double alpha = 1.0 / 7.0) {
    if (u_ref <= 0.0 || z_ref <= 0.0 || alpha <= 0.0) return 0.0;
    const double z_eff = std::max(z, 0.0);
    return u_ref * std::pow(z_eff / z_ref, alpha);
}

// ─── Inlet k profile ────────────────────────────────────────────────

/// k(z) ≈ u_*² / √C_μ   (simplified: δ ≫ z)
/// C_μ from Turbulence::KEpsilonConstants.
inline double inlet_k(double u_star) {
    if (u_star <= 0.0) return 0.0;
    return u_star * u_star / std::sqrt(Turbulence::KEpsilonConstants{}.C_mu);
}

// ─── Inlet ε profile ────────────────────────────────────────────────

/// ε(z) ≈ u_*³ / (κ · max(z, z₀))   (simplified: δ ≫ z)
inline double inlet_epsilon(double z, double u_star, double z0,
                             double kappa = 0.41) {
    if (u_star <= 0.0 || kappa <= 0.0) return 0.0;
    double z0_eff = sanitize_z0(z0);
    double z_eff  = std::max(z, z0_eff);
    return u_star * u_star * u_star / (kappa * z_eff);
}

// ─── Populate WindConfig from basic inputs ──────────────────────────

/// Fill computed fields (u_star, wind_x, wind_z) from the raw inputs.
inline void compute_wind_config(WindConfig& cfg) {
    cfg.z0 = sanitize_z0(cfg.z0);

    constexpr double pi = 3.141592653589793238462643383279502884;
    const double theta = cfg.direction_deg * pi / 180.0;  // radians
    cfg.wind_x = -std::sin(theta) * cfg.u_ref;              // meteorological convention
    cfg.wind_z = -std::cos(theta) * cfg.u_ref;

    cfg.u_star = friction_velocity(cfg.u_ref, cfg.z_ref, cfg.z0);
}

} // namespace Wind
