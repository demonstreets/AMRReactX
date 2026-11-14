#pragma once

#include "evaporation_model.H"
#include "antoine_data.H"
#include <string>
#include <cmath>

namespace Evaporation {

// ============================================================
// ModelType — evaporation modelling level
// ============================================================
enum class ModelType {
    constant,       // Level 0: user-specified constant flux
    mass_transfer   // Level 1: convective mass transfer model
};

// ============================================================
// PoolGeometry — spatial extent of the liquid pool.
// The pool lies on a horizontal plane (y_lo == y_hi).
// ============================================================
struct PoolGeometry {
    double x_lo = 0.0;
    double x_hi = 0.0;
    double y_lo = 0.0;
    double y_hi = 0.0;
    double z_lo = 0.0;
    double z_hi = 0.0;
};

// ============================================================
// EvaporationParams — physical parameters for the evaporation
// model. Populated from YAML or directly by the user.
// ============================================================
struct EvaporationParams {
    // ── model selection ──────────────────────────────────
    ModelType model_type = ModelType::mass_transfer;

    // ── Level 0: constant flux ───────────────────────────
    double constant_flux = 0.0;   // kg/(m²·s)

    // ── Level 1: mass transfer ───────────────────────────
    double u_ref       = 0.0;     // reference wind speed [m/s]
    double T_pool      = 293.0;   // pool temperature [K]
    double C_f         = 0.001;   // friction coefficient
    double pool_length = 1.0;     // pool length along wind [m]
    double Sc_t        = 0.7;     // turbulent Schmidt number
    double D_air       = 1.0e-5;  // species diffusivity in air [m²/s]

    // ── species properties (from Antoine DB or custom) ──
    double M_v      = 0.0;      // molecular weight [kg/mol]
    double L_v      = 0.0;      // latent heat [J/kg]
    double h_v_form = 0.0;      // vapour formation enthalpy [J/kg]
    double antoine_A = 0.0;     // Antoine A (mmHg-form)
    double antoine_B = 0.0;     // Antoine B [°C]
    double antoine_C = 0.0;     // Antoine C [°C]

    // ── species name (for reference) ─────────────────────
    std::string vapor_species_name;
};

// ============================================================
// PoolEvaporation — liquid pool evaporation source term model.
//
// Usage:
//   PoolEvaporation pool;
//   pool.configure(geom, params);          // or pool.init_from_yaml(node);
//   double mdot = pool.get_mass_flux();     // kg/(m²·s)
//   if (pool.cell_in_pool(x, y, z)) { ... }
// ============================================================
class PoolEvaporation {
public:
    PoolEvaporation() = default;

    // ── configuration ────────────────────────────────────
    void configure(const PoolGeometry& geom,
                   const EvaporationParams& params);

    // ── accessors ────────────────────────────────────────
    bool is_valid() const { return m_valid; }
    double get_mass_flux() const { return m_dot_per_area_; }
    double get_vapor_formation_enthalpy() const { return params_.h_v_form; }
    const std::string& get_vapor_species_name() const { return params_.vapor_species_name; }
    const PoolGeometry& geometry() const { return geom_; }
    const EvaporationParams& params() const { return params_; }
    ModelType model_type() const { return params_.model_type; }

    // ── spatial query ────────────────────────────────────
    bool cell_in_pool(double x, double y, double z) const;

private:
    void recompute_flux();

    PoolGeometry      geom_;
    EvaporationParams params_;
    double            m_dot_per_area_ = 0.0;  // kg/(m²·s)
    bool              m_valid         = false;
    bool              m_params_valid  = false;
};

// ============================================================
// Implementation
// ============================================================

inline void PoolEvaporation::configure(const PoolGeometry& geom,
                                        const EvaporationParams& params)
{
    geom_   = geom;
    params_ = params;

    // y_lo must equal y_hi — the pool must lie on a single
    // horizontal plane (spec §4.3 item 10)
    if (geom.y_lo != geom.y_hi) {
        m_dot_per_area_ = 0.0;
        m_valid = false;
        m_params_valid = false;
        return;
    }
    recompute_flux();
}

inline bool PoolEvaporation::cell_in_pool(double x, double y, double z) const
{
    // Check x-range
    if (x < geom_.x_lo || x > geom_.x_hi) return false;
    // Check y-range (pool plane)
    if (y < geom_.y_lo || y > geom_.y_hi) return false;
    // Check z-range
    if (z < geom_.z_lo || z > geom_.z_hi) return false;
    return true;
}

inline void PoolEvaporation::recompute_flux()
{
    // Validate Antoine constants for mass_transfer mode
    if (params_.model_type == ModelType::mass_transfer) {
        if (params_.antoine_A <= 0.0 || params_.antoine_B <= 0.0 ||
            params_.T_pool <= 0.0 || params_.M_v <= 0.0 ||
            params_.D_air <= 0.0 || params_.Sc_t <= 0.0 ||
            (params_.T_pool - 273.15 + params_.antoine_C) <= 0.0) {
            m_dot_per_area_ = 0.0;
            m_params_valid = false;
            return;
        }
    }

    switch (params_.model_type) {

    case ModelType::constant:
        // Level 0: user-specified constant flux
        if (params_.constant_flux < 0.0) {
            m_dot_per_area_ = 0.0;
            m_params_valid = false;
            m_valid = false;
            return;
        }
        m_dot_per_area_ = params_.constant_flux;
        break;

    case ModelType::mass_transfer: {
        // Level 1: convective mass transfer model
        //
        // Step 1 — friction velocity
        double u_star = friction_velocity(params_.u_ref, params_.C_f);

        // Step 2 — laminar Schmidt number
        // ν_air ≈ 1.5×10⁻⁵ m²/s (kinematic viscosity of air)
        constexpr double nu_air = 1.5e-5;
        double Sc = nu_air / params_.D_air;

        // Step 3 — mass transfer coefficient k_m
        constexpr double kappa = 0.41;  // von Kármán constant
        double k_m = mass_transfer_coefficient(
            u_star, kappa, Sc, params_.Sc_t);

        // Step 4 — saturated vapour density at pool surface
        double rho_sat = saturation_density(
            params_.T_pool,
            101325.0,  // P_atm (reserved for future use)
            params_.M_v,
            params_.antoine_A, params_.antoine_B, params_.antoine_C);

        // Step 5 — evaporation flux (ρ_v,∞ ≈ 0 for open air)
        m_dot_per_area_ = evaporation_flux(k_m, rho_sat, 0.0);
        break;
    }

    } // switch

    m_valid        = true;
    m_params_valid = true;
}

} // namespace Evaporation