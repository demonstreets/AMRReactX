#pragma once

#include "wind_profile.H"

/// @file wind_bc.H
/// Phase 2.6 — Face-type classification and inlet BC computation

namespace Wind {

// ─── Face type enumeration ──────────────────────────────────────────

enum class FaceType { INLET, OUTLET, SLIP, WALL, SYMMETRY };

// ─── 6-face outward normals (domain convention) ─────────────────────

namespace FaceNormal {
    // x = east, y = up, z = north
    constexpr double x_lo[3] = {-1.0,  0.0,  0.0};
    constexpr double x_hi[3] = {+1.0,  0.0,  0.0};
    constexpr double y_lo[3] = { 0.0, -1.0,  0.0};
    constexpr double y_hi[3] = { 0.0, +1.0,  0.0};
    constexpr double z_lo[3] = { 0.0,  0.0, -1.0};
    constexpr double z_hi[3] = { 0.0,  0.0, +1.0};
} // namespace FaceNormal

// ─── Face classification ────────────────────────────────────────────

/// Classify a face from the dot product of wind vector and outward normal.
///   v_dot_n < -eps  →  INLET   (wind blows into domain)
///   v_dot_n > +eps  →  OUTLET  (wind leaves domain)
///   otherwise       →  SLIP    (wind parallel to face)
inline FaceType classify_face(double v_dot_n, double eps = 1.0e-10) {
    if (v_dot_n < -eps)  return FaceType::INLET;
    if (v_dot_n >  eps)  return FaceType::OUTLET;
    return FaceType::SLIP;
}

// ═══════════════════════════════════════════════════════════════════════
//  Inlet BC values
// ═══════════════════════════════════════════════════════════════════════

struct InletBC {
    double u, v, w;         // velocity components [m/s]
    double T;               // temperature [K]
    double k, epsilon;      // turbulence variables
};

/// Compute wind vector dot product with a face outward normal.
inline double dot_wind_normal(double wind_x, double wind_z, const double n[3]) {
    return wind_x * n[0] + 0.0 * n[1] + wind_z * n[2];
}

/// Compute full inlet BC at height z for a given wind configuration.
inline InletBC compute_inlet_bc(double z, const WindConfig& cfg) {
    InletBC bc;

    // log-law magnitude at this height
    const double u_mag = log_law_velocity(z, cfg.u_star, cfg.z0);

    // scale reference direction vector to log-law magnitude
    const double u_ratio = (cfg.u_ref > 0.0) ? (u_mag / cfg.u_ref) : 0.0;
    bc.u = cfg.wind_x * u_ratio;
    bc.v = 0.0;
    bc.w = cfg.wind_z * u_ratio;

    bc.T       = cfg.T_inlet;
    bc.k       = inlet_k(cfg.u_star);
    bc.epsilon = inlet_epsilon(z, cfg.u_star, cfg.z0);

    return bc;
}

// ═══════════════════════════════════════════════════════════════════════
//  All six faces at once
// ═══════════════════════════════════════════════════════════════════════

struct AllFaceTypes {
    FaceType x_lo, x_hi;
    FaceType y_lo, y_hi;
    FaceType z_lo, z_hi;
};

/// Classify all six domain faces given wind velocity components.
/// y_lo is always WALL (ground, uses wall functions).
/// y_hi is always SYMMETRY (top of domain).
inline AllFaceTypes compute_all_face_types(double wind_x, double wind_z) {
    AllFaceTypes ft;

    ft.x_lo = classify_face(dot_wind_normal(wind_x, wind_z, FaceNormal::x_lo));
    ft.x_hi = classify_face(dot_wind_normal(wind_x, wind_z, FaceNormal::x_hi));
    ft.y_lo = FaceType::WALL;
    ft.y_hi = FaceType::SYMMETRY;
    ft.z_lo = classify_face(dot_wind_normal(wind_x, wind_z, FaceNormal::z_lo));
    ft.z_hi = classify_face(dot_wind_normal(wind_x, wind_z, FaceNormal::z_hi));

    return ft;
}

} // namespace Wind
