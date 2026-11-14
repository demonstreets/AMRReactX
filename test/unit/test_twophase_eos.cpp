#include "StiffenedGas.H"
#include "TwoPhaseEOS.H"

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

struct StubGasEOS {
    void REY2T(double rho, double e, const double*, double& T) const
    {
        T = e / 717.5 + 0.01 * rho;
    }

    void RTY2P(double rho, double T, const double*, double& p) const
    {
        p = rho * 287.0 * T;
    }

    void RTY2Cs(double, double, const double*, double& cs) const
    {
        cs = 343.25;
    }

    void RTY2G(double, double, const double*, double& gam1) const
    {
        gam1 = 1.4;
    }

    void RTY2dpde_dpdre(double rho, double, const double*, double& dpde,
                        double& dpdr_e) const
    {
        dpde = 0.4 * rho;
        dpdr_e = 287.0;
    }
};

} // namespace

int main()
{
    const StiffenedGasParams water_like{4.4, 6.0e8};
    constexpr double rho_gas = 1.2;
    constexpr double e_gas = 2.0e5;
    constexpr double rho_liq = 1000.0;
    constexpr double p_liq = 1.0e5;
    constexpr double cv_liq = 4184.0;
    double y[1] = {1.0};
    const StubGasEOS gas;

    const double e_liq = sg_e(water_like, rho_liq, p_liq);
    require_near(sg_p(water_like, rho_liq, e_liq), p_liq, 1.0e-7,
                 "stiffened-gas pressure/energy round trip");
    require(sg_cs(water_like, rho_liq, p_liq) > 0.0,
            "stiffened-gas sound speed is positive for water-like state");
    require_near(sg_dpde(water_like, rho_liq), (water_like.gamma - 1.0) * rho_liq,
                 1.0e-12, "stiffened-gas dp/de relation");

    const auto gas_res = twophase_mixture_eos(
        rho_gas, e_gas, 0.0, y, gas, water_like, cv_liq);
    double expected_T = 0.0;
    gas.REY2T(rho_gas, e_gas, y, expected_T);
    double expected_p = 0.0;
    gas.RTY2P(rho_gas, expected_T, y, expected_p);
    require_near(gas_res.T, expected_T, 1.0e-12,
                 "pure gas branch delegates temperature to gas EOS");
    require_near(gas_res.p, expected_p, 1.0e-8,
                 "pure gas branch delegates pressure to gas EOS");
    require_near(gas_res.cs, 343.25, 1.0e-12,
                 "pure gas branch preserves gas EOS sound speed");
    require_near(gas_res.gam1, 1.4, 1.0e-12,
                 "pure gas branch preserves gas gamma");

    const auto liquid_res = twophase_mixture_eos(
        rho_liq, e_liq, 1.0, y, gas, water_like, cv_liq);
    require_near(liquid_res.p, p_liq, 1.0e-7,
                 "pure liquid branch uses stiffened-gas pressure");
    require_near(liquid_res.T, (e_liq - water_like.p_inf / rho_liq) / cv_liq, 1.0e-12,
                 "pure liquid branch uses liquid cv temperature");
    require_near(liquid_res.cs, sg_cs(water_like, rho_liq, p_liq), 1.0e-8,
                 "pure liquid branch uses stiffened-gas sound speed");
    require_near(liquid_res.dpde, sg_dpde(water_like, rho_liq), 1.0e-12,
                 "pure liquid branch uses stiffened-gas dpde");

    const auto interface_res = twophase_mixture_eos(
        rho_liq, e_liq, 0.5, y, gas, water_like, cv_liq);
    require_near(interface_res.p, p_liq, 1.0e-7,
                 "interface closure currently uses liquid-dominated pressure");
    require_near(interface_res.cs, liquid_res.cs, 1.0e-8,
                 "interface closure uses stiffened-gas sound speed");

    const double negative_pressure_e = 0.0;
    const auto clamped = twophase_mixture_eos(
        rho_liq, negative_pressure_e, 1.0, y, gas, water_like, cv_liq);
    require(clamped.p >= 1.0, "liquid pressure is clamped positive");
    require(clamped.cs >= 1.0, "liquid sound speed is clamped positive");

    return 0;
}
