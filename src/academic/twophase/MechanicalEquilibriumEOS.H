#pragma once

#include <AMReX_REAL.H>
#include <AMReX_Gpu.H>
#include <cmath>
#include <limits>

namespace MyPele::Academic::TwoPhase {

// All quantities use one consistent unit system (CGS when used with Fuego).
// e_l = q_l + cv_l*T_l + pinf_l/rho_l. The reference energy q_l
// must share the gas mechanism's reference before phase change is enabled.
struct LiquidCaloricEOS {
    amrex::Real gamma, pinf, cv, reference_energy;
};

struct MechanicalState {
    amrex::Real p = 0, Tg = 0, Tl = 0;
    amrex::Real rhog = 0, rhol = 0;
    amrex::Real eg = 0, el = 0;
    amrex::Real cg = 0, cl = 0, c = 0;
    amrex::Real K_liquid = 0, energy_residual = 0;
    int iterations = 0;
    bool valid = false;
};

// Mechanical equilibrium is NOT thermal equilibrium: Tg and Tl are separate.
// mg and ml are phase mass per mixture volume; alpha is liquid volume fraction.
// The gas composition is normalized by mg, never by total mixture density.
template <class GasEOS>
AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
MechanicalState recover_mechanical_state(
    amrex::Real mg, amrex::Real ml, amrex::Real alpha,
    amrex::Real internal_energy_density, const amrex::Real* Yg,
    const GasEOS& gas, const LiquidCaloricEOS& liquid,
    amrex::Real pressure_seed = 1.e6,
    amrex::Real gas_temperature_min = 90.,
    amrex::Real gas_temperature_max = 10000.)
{
    using R = amrex::Real;
    MechanicalState s;
    if (!(mg >= 0 && ml >= 0 && mg+ml > 0 && alpha >= 0 && alpha <= 1 &&
          std::isfinite(internal_energy_density) && liquid.gamma > 1 &&
          liquid.pinf >= 0 && liquid.cv > 0 &&
          gas_temperature_min > 0 && gas_temperature_max > gas_temperature_min)) return s;
    // No phase-floor clipping: losing an occupied phase is a failed state.
    if ((alpha == 0) != (ml == 0) || (alpha == 1) != (mg == 0)) return s;
    const R ag = 1-alpha;
    s.rhol = ml > 0 ? ml/alpha : 0;
    s.rhog = mg > 0 ? mg/ag : 0;
    if (mg == 0) {
        s.el = internal_energy_density/ml;
        s.p = (liquid.gamma-1)*s.rhol*(s.el-liquid.reference_energy)-liquid.gamma*liquid.pinf;
        s.Tl = (s.el-liquid.reference_energy-liquid.pinf/s.rhol)/liquid.cv;
        if (!(s.p+liquid.pinf > 0 && s.Tl > 0 && std::isfinite(s.p))) return s;
        s.cl = std::sqrt(liquid.gamma*(s.p+liquid.pinf)/s.rhol);
        s.c = s.cl;
        s.valid = std::isfinite(s.c);
        return s;
    }
    // RYP2T/E are the thermally perfect ideal-gas interface used by Fuego.
    // Bracket by temperature validity, rather than allowing an EOS extrapolation
    // to produce a plausible pressure from an inadmissible energy.
    R lo, hi;
    gas.RTY2P(s.rhog,gas_temperature_min,Yg,lo);
    gas.RTY2P(s.rhog,gas_temperature_max,Yg,hi);
    if (!(hi > lo && lo > 0 && std::isfinite(hi))) return s;
    const R liquid_offset = ml*liquid.reference_energy +
        alpha*liquid.gamma*liquid.pinf/(liquid.gamma-1);
    auto energy = [&](R p, R& eg) {
        gas.RYP2E(s.rhog,Yg,p,eg);
        return mg*eg + liquid_offset + alpha*p/(liquid.gamma-1);
    };
    R eg_tmp;
    const R elo = energy(lo,eg_tmp), ehi = energy(hi,eg_tmp);
    if (!(internal_energy_density >= elo && internal_energy_density <= ehi)) return s;
    R p = pressure_seed > lo && pressure_seed < hi ? pressure_seed : (lo+hi)/2;
    // Energy references can cause cancellation: use the sum of phase energy
    // magnitudes as the tolerance scale, and verify the final residual below.
    for (int n=0; n<100; ++n) {
        const R E = energy(p,s.eg);
        s.energy_residual = E-internal_energy_density;
        s.iterations = n+1;
        const R scale = std::abs(mg*s.eg)+std::abs(liquid_offset)+
            std::abs(alpha*p/(liquid.gamma-1))+std::abs(internal_energy_density)+R(1.e-100);
        if (std::abs(s.energy_residual) <= R(2.e-13)*scale) break;
        if (s.energy_residual > 0) hi=p; else lo=p;
        gas.RYP2T(s.rhog,Yg,p,s.Tg);
        R cv; gas.RTY2Cv(s.rhog,s.Tg,Yg,cv);
        const R derivative = mg*cv*s.Tg/p + alpha/(liquid.gamma-1);
        R next = p-s.energy_residual/derivative;
        if (!(next > lo && next < hi && std::isfinite(next))) next=(lo+hi)/2;
        p=next;
    }
    s.p=p;
    const R E=energy(p,s.eg);
    s.energy_residual=E-internal_energy_density;
    const R scale=std::abs(mg*s.eg)+std::abs(liquid_offset)+std::abs(alpha*p/(liquid.gamma-1))+
        std::abs(internal_energy_density)+R(1.e-100);
    if (!(std::abs(s.energy_residual) <= R(3.e-13)*scale)) return s;
    gas.RYP2T(s.rhog,Yg,p,s.Tg);
    gas.RTY2Cs(s.rhog,s.Tg,Yg,s.cg);
    if (!(s.cg > 0 && std::isfinite(s.cg))) return s;
    if (ml > 0) {
        s.el=liquid.reference_energy+(p+liquid.gamma*liquid.pinf)/((liquid.gamma-1)*s.rhol);
        s.Tl=(p+liquid.pinf)/((liquid.gamma-1)*s.rhol*liquid.cv);
        s.cl=std::sqrt(liquid.gamma*(p+liquid.pinf)/s.rhol);
        const R Bg=s.rhog*s.cg*s.cg, Bl=s.rhol*s.cl*s.cl;
        const R compliance=ag/Bg+alpha/Bl;
        s.c=std::sqrt(1/((mg+ml)*compliance));
        // D alpha_l / Dt = K_l div(u), Kapila mechanical-equilibrium model.
        s.K_liquid=alpha*ag*(Bg-Bl)/(alpha*Bg+ag*Bl);
        if (!(s.Tl > 0 && std::isfinite(s.cl))) return s;
    } else s.c=s.cg;
    s.valid=std::isfinite(s.c) && s.c > 0 && s.Tg >= gas_temperature_min && s.Tg <= gas_temperature_max;
    return s;
}

} // namespace MyPele::Academic::TwoPhase
