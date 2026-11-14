#include "d2_law.H"

#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using MyPele::Academic::Droplet::D2LawAmbient;
using MyPele::Academic::Droplet::D2LawFuel;
using MyPele::Academic::Droplet::DropletState;
using MyPele::Academic::Droplet::advance_d2_law;
using MyPele::Academic::Droplet::advance_d2_law_until;
using MyPele::Academic::Droplet::d2_lifetime;
using MyPele::Academic::Droplet::droplet_mass_from_diameter;
using MyPele::Academic::Droplet::equivalent_diameter_from_mass_fraction;
using MyPele::Academic::Droplet::normalized_d2_from_mass_fraction;

static int n_pass = 0;
static int n_fail = 0;

#define TEST(name) do { std::cout << "  TEST: " << name << " ... "; } while (0)
#define PASS() do { std::cout << "PASS" << std::endl; ++n_pass; } while (0)
#define FAIL(msg) do { std::cout << "FAIL: " << msg << std::endl; ++n_fail; return; } while (0)
#define CHECK(cond, msg) do { if (!(cond)) { FAIL(msg); } } while (0)
#define CHECK_CLOSE(a, b, tol, msg) do { \
    const double av = (a); \
    const double bv = (b); \
    const double diff = std::abs(av - bv); \
    const double denom = std::max(std::abs(av), std::abs(bv)); \
    const double rel = denom > 1.0e-15 ? diff / denom : diff; \
    if (rel > (tol)) { \
        std::cout << "FAIL: " << msg << " (" << av << " vs " << bv \
                  << ", rel=" << rel << ")" << std::endl; \
        ++n_fail; \
        return; \
    } \
} while (0)

static D2LawFuel heptane_like_fuel()
{
    D2LawFuel fuel{};
    fuel.liquid_density = 681.4;
    fuel.liquid_cp = 2.2483e3;
    fuel.latent_heat = 3.63e5;
    fuel.boiling_temperature = 371.6;
    return fuel;
}


struct P3DParticleRecord {
    double temperature = 0.0;
    double diameter = 0.0;
    double mass_fraction = 0.0;
};

static P3DParticleRecord read_single_particle_p3d(const std::string& path)
{
    std::ifstream input(path);
    int version = 0;
    int nvalues = 0;
    int unused0 = 0;
    int unused1 = 0;
    int unused2 = 0;
    input >> version >> nvalues >> unused0 >> unused1 >> unused2;

    std::vector<double> values;
    double value = 0.0;
    while (input >> value) {
        values.push_back(value);
    }

    if (version != 1 || nvalues != 10 || values.size() < 12) {
        return {};
    }

    P3DParticleRecord record{};
    record.temperature = values[4];
    record.diameter = values[5];
    record.mass_fraction = values[11];
    return record;
}


struct LinearFit {
    double slope = 0.0;
    double intercept = 0.0;
    double r2 = 0.0;
};

static LinearFit least_squares_fit(const std::vector<double>& x,
                                   const std::vector<double>& y)
{
    LinearFit fit{};
    if (x.size() != y.size() || x.size() < 2) {
        return fit;
    }

    double mean_x = 0.0;
    double mean_y = 0.0;
    for (std::size_t n = 0; n < x.size(); ++n) {
        mean_x += x[n];
        mean_y += y[n];
    }
    mean_x /= static_cast<double>(x.size());
    mean_y /= static_cast<double>(y.size());

    double sxx = 0.0;
    double sxy = 0.0;
    double sst = 0.0;
    for (std::size_t n = 0; n < x.size(); ++n) {
        const double dx = x[n] - mean_x;
        const double dy = y[n] - mean_y;
        sxx += dx * dx;
        sxy += dx * dy;
        sst += dy * dy;
    }
    if (sxx <= 0.0) {
        return fit;
    }

    fit.slope = sxy / sxx;
    fit.intercept = mean_y - fit.slope * mean_x;

    double sse = 0.0;
    for (std::size_t n = 0; n < x.size(); ++n) {
        const double residual = y[n] - (fit.intercept + fit.slope * x[n]);
        sse += residual * residual;
    }
    fit.r2 = sst > 0.0 ? 1.0 - sse / sst : 1.0;
    return fit;
}

static std::vector<double> read_numeric_tokens(const std::string& path)
{
    std::ifstream input(path);
    std::vector<double> values;
    std::string line;
    while (std::getline(input, line)) {
        const auto hash = line.find('#');
        if (hash != std::string::npos) {
            line.erase(hash);
        }
        std::istringstream iss(line);
        double value = 0.0;
        while (iss >> value) {
            values.push_back(value);
        }
    }
    return values;
}

void test_mass_from_diameter()
{
    TEST("mass from spherical droplet diameter");
    const auto fuel = heptane_like_fuel();
    const double diameter = 57.0e-6;
    const double mass = droplet_mass_from_diameter(diameter, fuel);
    constexpr double pi = 3.141592653589793238462643383279502884;
    CHECK_CLOSE(mass, fuel.liquid_density * pi * std::pow(diameter, 3) / 6.0,
                1.0e-14, "spherical mass formula");
    CHECK(droplet_mass_from_diameter(-diameter, fuel) == 0.0, "negative diameter guard");
    PASS();
}

void test_d2_linear_regression()
{
    TEST("D2 law gives linear diameter-squared decay");
    const auto fuel = heptane_like_fuel();
    const D2LawAmbient ambient{800.0, 1.01325e5, 2.0e-9, 0.02};
    DropletState state{57.0e-6, 300.0, 0.0};
    state.mass = droplet_mass_from_diameter(state.diameter, fuel);

    const double old_d2 = state.diameter * state.diameter;
    const auto budget = advance_d2_law(state, fuel, ambient, 0.25);
    CHECK_CLOSE(state.diameter * state.diameter, old_d2 - ambient.evaporation_constant * 0.25,
                1.0e-12, "linear D2 decay");
    CHECK(budget.evaporated_mass > 0.0, "evaporated mass positive");
    CHECK_CLOSE(budget.latent_energy, budget.evaporated_mass * fuel.latent_heat,
                1.0e-14, "latent energy budget");
    CHECK(state.temperature > 300.0, "droplet heats toward ambient");
    CHECK(state.temperature <= fuel.boiling_temperature, "temperature is boiling limited");
    PASS();
}

void test_lifetime_and_nonnegative_clamp()
{
    TEST("lifetime truncates D2 decay and clamps mass nonnegative");
    const auto fuel = heptane_like_fuel();
    const D2LawAmbient ambient{900.0, 1.01325e5, 1.5e-9, 0.01};
    DropletState state{30.0e-6, 300.0, 0.0};
    state.mass = droplet_mass_from_diameter(state.diameter, fuel);
    const double life = d2_lifetime(state, ambient);
    CHECK_CLOSE(life, (30.0e-6 * 30.0e-6) / ambient.evaporation_constant,
                1.0e-14, "D2 lifetime");

    const auto budget = advance_d2_law_until(state, fuel, ambient, 100.0 * life);
    CHECK(budget.fully_evaporated, "fully evaporated flag");
    CHECK_CLOSE(budget.elapsed, life, 1.0e-14, "elapsed time truncated to lifetime");
    CHECK_CLOSE(state.diameter, 0.0, 1.0e-14, "diameter clamps to zero");
    CHECK_CLOSE(state.mass, 0.0, 1.0e-14, "mass clamps to zero");
    CHECK(budget.evaporated_mass > 0.0, "evaporated mass tracked");
    PASS();
}

void test_guards_disable_unphysical_updates()
{
    TEST("guards keep invalid updates finite and non-evaporating");
    const auto fuel = heptane_like_fuel();
    const D2LawAmbient ambient{500.0, 1.01325e5, -1.0, 0.0};
    DropletState state{20.0e-6, 310.0, 0.0};
    const double old_d = state.diameter;
    const auto budget = advance_d2_law(state, fuel, ambient, 0.1);
    CHECK_CLOSE(state.diameter, old_d, 1.0e-14, "invalid K leaves diameter unchanged");
    CHECK_CLOSE(state.temperature, 310.0, 1.0e-14, "invalid relaxation leaves temperature unchanged");
    CHECK_CLOSE(budget.evaporated_mass, 0.0, 1.0e-14, "no mass evaporated");
    CHECK(std::isfinite(state.mass), "mass finite");
    PASS();
}


void test_historical_d2_ascii_snapshots_are_monotone()
{
    TEST("historical D2 ASCII snapshots are parseable and monotone");
    const char* files[] = {
        "examples/academic/d2_law/spray00000.p3d",
        "examples/academic/d2_law/spray05755.p3d",
        "examples/academic/d2_law/spray11504.p3d",
        "examples/academic/d2_law/spray17253.p3d",
        "examples/academic/d2_law/spray23002.p3d",
        "examples/academic/d2_law/spray28750.p3d",
        "examples/academic/d2_law/spray34499.p3d",
        "examples/academic/d2_law/spray40248.p3d",
        "examples/academic/d2_law/spray45997.p3d",
        "examples/academic/d2_law/spray51746.p3d",
        "examples/academic/d2_law/spray57495.p3d",
    };

    P3DParticleRecord first = read_single_particle_p3d(files[0]);
    CHECK(first.temperature > 0.0, "first snapshot parsed");
    CHECK_CLOSE(first.diameter, 0.057, 1.0e-12, "initial historical diameter");
    CHECK_CLOSE(first.mass_fraction, 1.0, 1.0e-12, "initial historical mass fraction");

    double previous_temperature = first.temperature;
    double previous_mass_fraction = first.mass_fraction;
    for (const char* file : files) {
        const auto record = read_single_particle_p3d(file);
        CHECK(record.temperature >= previous_temperature - 1.0e-12,
              "historical temperature monotone nondecreasing");
        CHECK(record.mass_fraction <= previous_mass_fraction + 1.0e-12,
              "historical mass fraction monotone nonincreasing");
        CHECK(record.mass_fraction > 0.0 && record.mass_fraction <= 1.0,
              "historical mass fraction bounded");
        CHECK_CLOSE(record.diameter, 0.057, 1.0e-12,
                    "historical diameter field remains constant in ASCII output");
        previous_temperature = record.temperature;
        previous_mass_fraction = record.mass_fraction;
    }

    const auto last = read_single_particle_p3d(files[10]);
    CHECK_CLOSE(last.temperature, 300.035152783009, 1.0e-12,
                "historical final particle temperature");
    CHECK_CLOSE(last.mass_fraction, 0.999953022577235, 1.0e-12,
                "historical final particle mass fraction");
    CHECK(last.temperature > first.temperature, "historical particle heats");
    CHECK(last.mass_fraction < first.mass_fraction, "historical particle evaporates");
    PASS();
}

void test_historical_d2_ascii_snapshots_have_linear_equivalent_d2()
{
    TEST("historical D2 ASCII snapshots have quantitative linear equivalent-D2 slope");
    const char* files[] = {
        "examples/academic/d2_law/spray00000.p3d",
        "examples/academic/d2_law/spray05755.p3d",
        "examples/academic/d2_law/spray11504.p3d",
        "examples/academic/d2_law/spray17253.p3d",
        "examples/academic/d2_law/spray23002.p3d",
        "examples/academic/d2_law/spray28750.p3d",
        "examples/academic/d2_law/spray34499.p3d",
        "examples/academic/d2_law/spray40248.p3d",
        "examples/academic/d2_law/spray45997.p3d",
        "examples/academic/d2_law/spray51746.p3d",
        "examples/academic/d2_law/spray57495.p3d",
    };

    std::vector<double> steps;
    std::vector<double> normalized_d2;
    double previous_d2 = 2.0;
    for (const char* file : files) {
        const auto record = read_single_particle_p3d(file);
        const std::string name(file);
        const auto begin = name.find("spray") + 5;
        const auto end = name.find(".p3d");
        const double step = std::stod(name.substr(begin, end - begin));
        const double d2 = normalized_d2_from_mass_fraction(record.mass_fraction);
        CHECK(d2 > 0.0 && d2 <= 1.0, "equivalent D2 is bounded");
        CHECK(d2 <= previous_d2 + 1.0e-14, "equivalent D2 decreases monotonically");
        steps.push_back(step);
        normalized_d2.push_back(d2);
        previous_d2 = d2;
    }

    const auto fit = least_squares_fit(steps, normalized_d2);
    CHECK(fit.slope < 0.0, "historical equivalent D2 slope is negative");
    CHECK(fit.r2 > 0.999999, "historical equivalent D2 is highly linear");
    CHECK_CLOSE(fit.slope, -5.447514367215504e-10, 1.0e-6,
                "historical equivalent D2 slope regression");
    CHECK_CLOSE(fit.intercept, 1.0000000060187568, 1.0e-10,
                "historical equivalent D2 intercept regression");
    CHECK_CLOSE(normalized_d2.back(), 0.9999686814729428, 1.0e-12,
                "historical final equivalent D2 reference");
    CHECK(equivalent_diameter_from_mass_fraction(57.0e-6, 0.125) > 0.0,
          "equivalent diameter helper maps positive mass fraction");
    CHECK_CLOSE(equivalent_diameter_from_mass_fraction(57.0e-6, 0.125),
                57.0e-6 * 0.5, 1.0e-14,
                "one-eighth mass fraction gives half diameter");
    PASS();
}

void test_repo_d2_law_input_contract()
{
    TEST("repo D2-law input particle can be advanced safely");
    const auto values = read_numeric_tokens("examples/academic/d2_law/initsprayfile.dat");
    CHECK(values.size() >= 7, "initsprayfile has particle tokens");
    CHECK_CLOSE(values[0], 1.0, 1.0e-14, "one particle in init file");

    const auto fuel = heptane_like_fuel();
    const double diameter = values[6] * 1.0e-3;
    CHECK(diameter > 0.0, "mapped initial diameter positive");

    DropletState state{diameter, values[5] > 0.0 ? values[5] : 300.0, 0.0};
    state.mass = droplet_mass_from_diameter(state.diameter, fuel);
    const D2LawAmbient ambient{500.0, 1.01325e5, 8.0e-10, 0.05};

    double cumulative_mass = 0.0;
    double cumulative_energy = 0.0;
    double previous_d2 = state.diameter * state.diameter;
    for (int step = 0; step < 20; ++step) {
        const auto budget = advance_d2_law(state, fuel, ambient, 0.01);
        cumulative_mass += budget.evaporated_mass;
        cumulative_energy += budget.latent_energy;
        const double d2 = state.diameter * state.diameter;
        CHECK(d2 <= previous_d2 + 1.0e-20, "D2 is monotone nonincreasing");
        CHECK(state.mass >= 0.0, "mass remains nonnegative");
        previous_d2 = d2;
    }

    CHECK(cumulative_mass > 0.0, "cumulative evaporation positive");
    CHECK_CLOSE(cumulative_energy, cumulative_mass * fuel.latent_heat,
                1.0e-12, "cumulative latent budget");
    PASS();
}

int main()
{
    std::cout << "\n=== D2-law Droplet Unit Tests ===\n" << std::endl;
    test_mass_from_diameter();
    test_d2_linear_regression();
    test_lifetime_and_nonnegative_clamp();
    test_guards_disable_unphysical_updates();
    test_repo_d2_law_input_contract();
    test_historical_d2_ascii_snapshots_are_monotone();
    test_historical_d2_ascii_snapshots_have_linear_equivalent_d2();
    std::cout << "\n=== Results: " << n_pass << " passed, "
              << n_fail << " failed ===" << std::endl;
    return n_fail == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
