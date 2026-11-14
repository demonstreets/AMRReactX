#pragma once

#include <string>
#include <unordered_map>
#include <cmath>

namespace Evaporation {

// ============================================================
// AntoineConstants — Antoine equation parameters + thermophysical
// properties for a single species.
//
// Antoine form stored in the database:
//   log10 P_sat[mmHg] = A - B / (t[°C] + C)
// ============================================================
struct AntoineConstants {
    double A;          // Antoine A coefficient (mmHg-form)
    double B;          // Antoine B coefficient [°C]
    double C;          // Antoine C coefficient [°C]
    double M_v;        // molecular weight [kg/mol]
    double L_v;        // latent heat of vaporization [J/kg]
    double h_v_form;   // vapour formation enthalpy [J/kg]
    bool   found;      // true if species was found in the database
};

// ============================================================
// lookup_antoine — search the built-in database by species name
// or alias. Returns AntoineConstants with found=true on success,
// or found=false if the species is not in the database.
//
// Supported species and aliases:
//   methane    / CH4  / LNG
//   propane    / C3H8
//   n-hexane   / hexane / gasoline
//   ammonia    / NH3
//   chlorine   / Cl2
//   water      / H2O
// ============================================================
AntoineConstants lookup_antoine(const std::string& species_name);

// ============================================================
// Implementation (header-only for simplicity, matching the
// turbulence module convention)
// ============================================================

inline AntoineConstants lookup_antoine(const std::string& species_name)
{
    // Normalise to lowercase for case-insensitive matching
    std::string key;
    key.reserve(species_name.size());
    for (char c : species_name) {
        key += static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    }

    // ─── methane ──────────────────────────────────────────
    if (key == "methane" || key == "ch4" || key == "lng") {
        return { 6.69561, 405.42, 267.777,
                 0.01604, 5.10e5, -4.65e6, true };
    }

    // ─── propane ──────────────────────────────────────────
    if (key == "propane" || key == "c3h8") {
        return { 6.95719, 1424.255, -45.957,
                 0.04410, 4.26e5, -2.15e6, true };
    }

    // ─── n-hexane ─────────────────────────────────────────
    if (key == "n-hexane" || key == "hexane" || key == "gasoline") {
        return { 6.91058, 1189.64, 226.28,
                 0.08618, 3.65e5, -2.05e6, true };
    }

    // ─── ammonia ──────────────────────────────────────────
    if (key == "ammonia" || key == "nh3") {
        return { 7.55466, 1002.711, 247.885,
                 0.01703, 1.37e6, -2.74e6, true };
    }

    // ─── chlorine ─────────────────────────────────────────
    if (key == "chlorine" || key == "cl2") {
        return { 6.92717, 862.72, 221.44,
                 0.07091, 2.88e5, 0.0, true };
    }

    // ─── water ────────────────────────────────────────────
    if (key == "water" || key == "h2o") {
        return { 8.07131, 1730.63, 233.426,
                 0.01802, 2.26e6, -1.344e7, true };
    }

    // ─── not found ────────────────────────────────────────
    return { 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, false };
}

} // namespace Evaporation
