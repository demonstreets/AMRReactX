#include "wind_bc.H"
#include "wind_profile.H"

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
    using namespace Wind;

    require_near(resolve_direction(" north "), 0.0, 1.0e-12,
                 "case-insensitive north direction");
    require_near(resolve_direction("sw"), 225.0, 1.0e-12,
                 "lowercase southwest direction");
    require_near(resolve_direction("292.5"), 292.5, 1.0e-12,
                 "numeric direction fallback");
    require_near(sanitize_z0(-1.0), 1.0e-4, 1.0e-16,
                 "roughness length is sanitized");

    constexpr double kappa = 0.41;
    const double u_ref = 10.0;
    const double z_ref = 10.0;
    const double z0 = 0.1;
    const double u_star = friction_velocity(u_ref, z_ref, z0, kappa);
    const double expected_ustar = kappa * u_ref / std::log(z_ref / z0);
    require_near(u_star, expected_ustar, 1.0e-14,
                 "friction velocity follows log-law relation");
    require(friction_velocity(u_ref, z0, z0, kappa) == 0.0,
            "invalid reference height gives zero friction velocity");

    require_near(log_law_velocity(z_ref, u_star, z0, kappa), u_ref, 1.0e-12,
                 "log-law recovers reference speed at reference height");
    require(log_law_velocity(z0, u_star, z0, kappa) == 0.0,
            "log-law velocity is zero at roughness height");
    require_near(power_law_velocity(20.0, u_ref, 10.0, 0.2),
                 u_ref * std::pow(2.0, 0.2), 1.0e-12,
                 "power-law profile follows exponent relation");
    require(power_law_velocity(5.0, u_ref, 0.0, 0.2) == 0.0,
            "invalid power-law reference height is guarded");

    // Neutral ABL reference table for z0=0.03 m, U(10 m)=2 m/s.
    // Values are fixed regression targets for the log-law profile and inlet
    // turbulence helpers used by generated engineering boundary inputs.
    const double abl_z0 = 0.03;
    const double abl_u_ref = 2.0;
    const double abl_z_ref = 10.0;
    const double abl_u_star = friction_velocity(abl_u_ref, abl_z_ref, abl_z0, kappa);
    require_near(abl_u_star, 0.14115679393109118, 1.0e-14,
                 "neutral ABL friction velocity reference");

    struct ABLReference {
        double z;
        double u;
        double epsilon;
    };
    const ABLReference abl_reference[] = {
        {0.03, 0.0, 0.22866528971229463},
        {0.10, 0.41450961228993694, 0.06859958691368838},
        {0.50, 0.9686147238761464, 0.013719917382737678},
        {2.00, 1.4458948884137905, 0.0034299793456844196},
        {10.0, 2.0, 0.0006859958691368839},
        {40.0, 2.4772801645376443, 0.00017149896728422097},
    };
    double previous_u = -1.0;
    double previous_epsilon = 1.0e99;
    for (const auto& row : abl_reference) {
        require_near(log_law_velocity(row.z, abl_u_star, abl_z0, kappa),
                     row.u, 2.0e-13,
                     "neutral ABL log-law reference velocity");
        require_near(inlet_epsilon(row.z, abl_u_star, abl_z0, kappa),
                     row.epsilon, 2.0e-13,
                     "neutral ABL epsilon reference");
        require(row.u >= previous_u,
                "neutral ABL velocity is monotone with height");
        require(row.epsilon <= previous_epsilon,
                "neutral ABL epsilon decreases with height");
        previous_u = row.u;
        previous_epsilon = row.epsilon;
    }
    require_near(inlet_k(abl_u_star), 0.06641746824301513, 1.0e-14,
                 "neutral ABL k reference");

    WindConfig cfg{};
    cfg.direction_deg = resolve_direction("E");
    cfg.u_ref = 8.0;
    cfg.z_ref = 10.0;
    cfg.z0 = 0.2;
    cfg.T_inlet = 300.0;
    compute_wind_config(cfg);
    require(cfg.u_star > 0.0, "computed wind config has positive friction velocity");
    require_near(cfg.wind_x, -8.0, 1.0e-12,
                 "meteorological east wind maps to negative x velocity");
    require_near(cfg.wind_z, 0.0, 1.0e-12,
                 "east wind has no north/south component");

    const AllFaceTypes ft = compute_all_face_types(cfg.wind_x, cfg.wind_z);
    require(ft.x_lo == FaceType::OUTLET, "west face is outlet for negative x wind");
    require(ft.x_hi == FaceType::INLET, "east face is inlet for negative x wind");
    require(ft.y_lo == FaceType::WALL, "ground face is wall");
    require(ft.y_hi == FaceType::SYMMETRY, "top face is symmetry");
    require(ft.z_lo == FaceType::SLIP, "south face is slip for pure east wind");
    require(ft.z_hi == FaceType::SLIP, "north face is slip for pure east wind");

    const InletBC bc_low = compute_inlet_bc(2.0, cfg);
    const InletBC bc = compute_inlet_bc(10.0, cfg);
    const InletBC bc_high = compute_inlet_bc(20.0, cfg);
    require(std::abs(bc_low.u) < std::abs(bc.u),
            "vertical inlet sampling gives lower speed below z_ref");
    require(std::abs(bc_high.u) > std::abs(bc.u),
            "vertical inlet sampling gives higher speed above z_ref");
    require(bc_low.epsilon > bc.epsilon,
            "vertical inlet sampling raises epsilon near the ground");
    require(bc_high.epsilon < bc.epsilon,
            "vertical inlet sampling lowers epsilon aloft");
    require_near(bc.u, cfg.wind_x, 1.0e-12,
                 "inlet BC recovers reference x velocity at z_ref");
    require_near(bc.w, cfg.wind_z, 1.0e-12,
                 "inlet BC recovers reference z velocity at z_ref");
    require_near(bc.T, cfg.T_inlet, 1.0e-12,
                 "inlet BC temperature is passed through");
    require_near(bc.k, inlet_k(cfg.u_star), 1.0e-14,
                 "inlet BC k matches k-epsilon helper");
    require_near(bc.epsilon, inlet_epsilon(10.0, cfg.u_star, cfg.z0), 1.0e-14,
                 "inlet BC epsilon matches k-epsilon helper");
    require(inlet_k(-1.0) == 0.0, "negative friction velocity gives zero k");
    require(inlet_epsilon(1.0, -1.0, cfg.z0) == 0.0,
            "negative friction velocity gives zero epsilon");

    return 0;
}
