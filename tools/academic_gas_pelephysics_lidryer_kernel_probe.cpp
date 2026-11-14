#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

#include "mechanism.H"

namespace {

constexpr std::array<const char*, NUM_SPECIES> species_names = {
  "H2", "O2", "H2O", "H", "O", "OH", "HO2", "H2O2", "N2"};

struct State {
  const char* name;
  double temperature_k;
  double pressure_pa;
  double phi;
};

void
require_finite(const char* label, const double value)
{
  if (!std::isfinite(value)) {
    std::cerr << "non-finite " << label << ": " << value << "\n";
    std::exit(2);
  }
}

std::array<amrex::Real, NUM_SPECIES>
mole_fractions_for_phi(const double phi)
{
  std::array<amrex::Real, NUM_SPECIES> x{};
  x[H2_ID] = 2.0 * phi;
  x[O2_ID] = 1.0;
  x[N2_ID] = 3.76;
  amrex::Real sum = 0.0;
  for (const auto value : x) {
    sum += value;
  }
  for (auto& value : x) {
    value /= sum;
  }
  return x;
}

void
write_csv_header()
{
  std::cout << "case,temperature_k,pressure_pa,pressure_cgs,phi";
  for (const auto* name : species_names) {
    std::cout << ",x_" << name;
  }
  for (const auto* name : species_names) {
    std::cout << ",y_" << name;
  }
  std::cout << ",rho_cgs,cpbs_erg_g_K";
  for (const auto* name : species_names) {
    std::cout << ",wdot_" << name << "_mol_cm3_s";
  }
  std::cout << "\n";
}

void
write_state(const State& state)
{
  const auto x = mole_fractions_for_phi(state.phi);
  std::array<amrex::Real, NUM_SPECIES> y{};
  std::array<amrex::Real, NUM_SPECIES> wdot{};
  amrex::Real rho_cgs = 0.0;
  amrex::Real cpbs = 0.0;
  const amrex::Real pressure_cgs = state.pressure_pa * 10.0;

  CKXTY(x.data(), y.data());
  CKRHOY(pressure_cgs, state.temperature_k, y.data(), rho_cgs);
  CKCPBS(state.temperature_k, y.data(), cpbs);
  CKWYP(pressure_cgs, state.temperature_k, y.data(), wdot.data());

  require_finite("rho_cgs", rho_cgs);
  require_finite("cpbs", cpbs);
  for (int i = 0; i < NUM_SPECIES; ++i) {
    require_finite(species_names[i], wdot[i]);
  }

  std::cout << state.name << "," << state.temperature_k << ","
            << state.pressure_pa << "," << pressure_cgs << "," << state.phi;
  for (const auto value : x) {
    std::cout << "," << value;
  }
  for (const auto value : y) {
    std::cout << "," << value;
  }
  std::cout << "," << rho_cgs << "," << cpbs;
  for (const auto value : wdot) {
    std::cout << "," << value;
  }
  std::cout << "\n";
}

} // namespace

int
main()
{
  int mm = 0;
  int kk = 0;
  int ii = 0;
  int nfit = 0;
  CKINDX(mm, kk, ii, nfit);
  if (mm != NUM_ELEMENTS || kk != NUM_SPECIES || ii != NUM_REACTIONS) {
    std::cerr << "CKINDX mismatch\n";
    return 2;
  }

  const std::vector<State> states = {
    {"lean_phi0p6_900K_1atm", 900.0, 101325.0, 0.6},
    {"lean_phi0p6_1200K_1atm", 1200.0, 101325.0, 0.6},
    {"lean_phi0p6_1600K_1atm", 1600.0, 101325.0, 0.6},
    {"stoich_phi1p0_900K_1atm", 900.0, 101325.0, 1.0},
    {"stoich_phi1p0_1200K_1atm", 1200.0, 101325.0, 1.0},
    {"stoich_phi1p0_1600K_1atm", 1600.0, 101325.0, 1.0},
    {"rich_phi1p6_900K_1atm", 900.0, 101325.0, 1.6},
    {"rich_phi1p6_1200K_1atm", 1200.0, 101325.0, 1.6},
    {"rich_phi1p6_1600K_1atm", 1600.0, 101325.0, 1.6},
    {"stoich_phi1p0_1200K_5atm", 1200.0, 506625.0, 1.0},
    {"lean_phi0p6_1200K_5atm", 1200.0, 506625.0, 0.6},
    {"rich_phi1p6_1200K_5atm", 1200.0, 506625.0, 1.6},
  };

  std::cout << std::setprecision(17);
  write_csv_header();
  for (const auto& state : states) {
    write_state(state);
  }
  return 0;
}
