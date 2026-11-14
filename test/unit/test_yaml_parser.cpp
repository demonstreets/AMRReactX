#include "yaml_schema.H"
#include "yaml_parser.H"
#include "parmparse_writer.H"

#include <iostream>
#include <cassert>
#include <cstring>
#include <fstream>
#include <cmath>
#include <string>
#include <filesystem>
#include <sys/wait.h>
#include <unistd.h>

// ─── helpers ─────────────────────────────────────────────────────────────────

static int test_count = 0;
static int pass_count = 0;
static int fail_count = 0;

#define TEST(name)                                                       \
    do {                                                                 \
        std::cout << "\n=== Test " << ++test_count << ": " << name      \
                  << " ===" << std::endl;                                 \
    } while(0)

#define CHECK(cond)                                                      \
    do {                                                                 \
        if (!(cond)) {                                                   \
            std::cerr << "  [FAIL] " << __FILE__ << ":" << __LINE__     \
                      << " — " << #cond << std::endl;                    \
            ++fail_count;                                                \
        } else {                                                         \
            std::cout << "  [PASS] " << #cond << std::endl;             \
            ++pass_count;                                                \
        }                                                                \
    } while(0)

#define CHECK_EQ(a, b) CHECK((a) == (b))
#define CHECK_DOUBLE_EQ(a, b, tol) CHECK(std::abs((a) - (b)) < (tol))
#define CHECK_STREQ(a, b) CHECK(std::strcmp((a), (b)) == 0)

// ─── temporary file helpers ─────────────────────────────────────────────────

static std::string temp_path(const std::string& name) {
    return (std::filesystem::temp_directory_path() / name).string();
}

static void write_temp(const std::string& path, const std::string& content) {
    std::ofstream f(path);
    f << content;
    f.close();
}

/// Fork; in child run fn(); parent waits and returns child exit status.
/// Returns -1 on fork failure.
static int run_in_child_and_wait(void (*fn)(void)) {
    pid_t pid = fork();
    if (pid < 0) return -1;
    if (pid == 0) {
        fn();
        _exit(0); // never reached if fn calls exit(1)
    }
    int status = 0;
    waitpid(pid, &status, 0);
    return WIFEXITED(status) ? WEXITSTATUS(status) : -1;
}

// ─── Test 1: Full YAML parse ────────────────────────────────────────────────

void test_full_yaml() {
    TEST("Full YAML parse");
    auto cfg = YamlParser::parse_config("test/unit/test_full.yaml");

    // geometry
    CHECK_STREQ(cfg.geometry.type.c_str(), "stl");
    CHECK_STREQ(cfg.geometry.file.c_str(), "test/tanks.stl");
    CHECK_DOUBLE_EQ(cfg.geometry.scale, 0.5, 1e-12);

    // domain
    CHECK_DOUBLE_EQ(cfg.domain.xmin, -10.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.domain.xmax,  10.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.domain.ymin,  -5.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.domain.ymax,   5.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.domain.zmin,   0.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.domain.zmax,  12.0, 1e-12);

    // mesh
    CHECK_EQ(cfg.mesh.n_cell.size(), 3u);
    CHECK_EQ(cfg.mesh.n_cell[0], 256);
    CHECK_EQ(cfg.mesh.n_cell[1], 128);
    CHECK_EQ(cfg.mesh.n_cell[2],  64);
    CHECK_EQ(cfg.mesh.max_level, 3);
    CHECK_EQ(cfg.mesh.blocking_factor, 16);
    CHECK_EQ(cfg.mesh.max_grid_size, 64);
    CHECK(cfg.mesh.refine.near_wall == true);
    CHECK(cfg.mesh.refine.near_leak == false);

    // physics
    CHECK_STREQ(cfg.physics.model.c_str(), "dispersion");
    CHECK_STREQ(cfg.physics.chemistry.mechanism.c_str(), "drm19");
    CHECK_STREQ(cfg.physics.chemistry.mechanism_file.c_str(), "");
    CHECK_EQ(cfg.physics.species.tracked.size(), 3u);
    CHECK_STREQ(cfg.physics.species.tracked[0].c_str(), "CH4");
    CHECK_STREQ(cfg.physics.species.tracked[1].c_str(), "C3H8");
    CHECK_STREQ(cfg.physics.species.tracked[2].c_str(), "H2");
    CHECK_STREQ(cfg.physics.transport.model.c_str(), "Simple");
    CHECK_STREQ(cfg.physics.eos.type.c_str(), "ideal_gas");

    // time
    CHECK_DOUBLE_EQ(cfg.time.stop_time, 30.0, 1e-12);
    CHECK_EQ(cfg.time.max_step, 50000);
    CHECK_DOUBLE_EQ(cfg.time.cfl, 0.5, 1e-12);
    CHECK_DOUBLE_EQ(cfg.time.dt_init, 5.0e-7, 1e-15);
    CHECK_DOUBLE_EQ(cfg.time.dt_max, 0.005, 1e-15);

    // leaks
    CHECK_EQ(cfg.leaks.size(), 2u);

    // leak 0
    CHECK_STREQ(cfg.leaks[0].name.c_str(), "leak_main");
    CHECK_DOUBLE_EQ(cfg.leaks[0].position[0], 0.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.leaks[0].position[1], 0.3, 1e-12);
    CHECK_DOUBLE_EQ(cfg.leaks[0].position[2], 1.5, 1e-12);
    CHECK_DOUBLE_EQ(cfg.leaks[0].radius, 0.02, 1e-12);
    CHECK_DOUBLE_EQ(cfg.leaks[0].direction[0], 0.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.leaks[0].direction[1], 0.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.leaks[0].direction[2], 1.0, 1e-12);
    CHECK_EQ(cfg.leaks[0].species.size(), 2u);
    CHECK_DOUBLE_EQ(cfg.leaks[0].species.at("CH4"),  0.9, 1e-12);
    CHECK_DOUBLE_EQ(cfg.leaks[0].species.at("C3H8"), 0.1, 1e-12);
    CHECK_DOUBLE_EQ(cfg.leaks[0].mass_flow_rate, 0.25, 1e-12);
    CHECK_DOUBLE_EQ(cfg.leaks[0].temperature, 310.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.leaks[0].velocity, 12.0, 1e-12);

    // leak 1
    CHECK_STREQ(cfg.leaks[1].name.c_str(), "leak_secondary");
    CHECK_DOUBLE_EQ(cfg.leaks[1].position[0], 2.0, 1e-12);
    CHECK_EQ(cfg.leaks[1].species.size(), 1u);
    CHECK_DOUBLE_EQ(cfg.leaks[1].species.at("H2"), 1.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.leaks[1].mass_flow_rate, 0.05, 1e-12);

    // wind
    CHECK_STREQ(cfg.wind.model.c_str(), "power_law");
    CHECK_DOUBLE_EQ(cfg.wind.reference_height, 10.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.wind.reference_speed,   4.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.wind.roughness_length,  0.05, 1e-12);
    CHECK_DOUBLE_EQ(cfg.wind.direction[0], 1.0, 1e-12);

    // pool
    CHECK(cfg.pool.enabled == true);
    CHECK_DOUBLE_EQ(cfg.pool.position[0],  0.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.pool.position[1], -1.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.pool.area, 2.5, 1e-12);
    CHECK_STREQ(cfg.pool.species.c_str(), "C8H18");
    CHECK_DOUBLE_EQ(cfg.pool.temperature, 298.0, 1e-12);

    // ignition (disabled — fields use defaults)
    CHECK(cfg.ignition.enabled == false);
    CHECK_STREQ(cfg.ignition.type.c_str(), "spark"); // default

    // turbulence
    CHECK_STREQ(cfg.turbulence.model.c_str(), "k_epsilon");
    CHECK_DOUBLE_EQ(cfg.turbulence.constants.C_mu,    0.09, 1e-12);
    CHECK_DOUBLE_EQ(cfg.turbulence.constants.C_eps1,  1.44, 1e-12);
    CHECK_DOUBLE_EQ(cfg.turbulence.constants.C_eps2,  1.92, 1e-12);
    CHECK_DOUBLE_EQ(cfg.turbulence.constants.sigma_k, 1.0,  1e-12);
    CHECK_DOUBLE_EQ(cfg.turbulence.constants.sigma_eps, 1.3, 1e-12);
    CHECK_STREQ(cfg.turbulence.wall_function.c_str(), "launder_spalding");

    // output
    CHECK_EQ(cfg.output.plot_int, 50);
    CHECK_EQ(cfg.output.chk_int, 200);
    CHECK(cfg.output.diagnostics == true);
    CHECK_EQ(cfg.output.diagnostics_interval, 5);
    CHECK_STREQ(cfg.output.format.c_str(), "hdf5");

    CHECK_STREQ(cfg.boundaries.faces.xlo.c_str(), "inlet");
    CHECK_STREQ(cfg.boundaries.faces.xhi.c_str(), "outlet");
    CHECK_STREQ(cfg.boundaries.faces.ylo.c_str(), "wall");
    CHECK_STREQ(cfg.boundaries.faces.yhi.c_str(), "symmetry");
    CHECK_STREQ(cfg.boundaries.faces.zlo.c_str(), "slip_wall");
    CHECK_STREQ(cfg.boundaries.faces.zhi.c_str(), "outlet");

    CHECK_EQ(cfg.parmparse.size(), 1u);
    CHECK_STREQ(cfg.parmparse.at("amr.derive_plot_vars").c_str(), "avg_pressure mag_vort");
}

// ─── Test 2: Minimal YAML ───────────────────────────────────────────────────

void test_minimal_yaml() {
    TEST("Minimal YAML (only required fields)");
    auto cfg = YamlParser::parse_config("test/unit/test_minimal.yaml");

    // geometry
    CHECK_STREQ(cfg.geometry.type.c_str(), "builtin");
    CHECK_STREQ(cfg.geometry.file.c_str(), "");         // default
    CHECK_DOUBLE_EQ(cfg.geometry.scale, 1.0, 1e-12);    // default

    // domain
    CHECK_DOUBLE_EQ(cfg.domain.xmin, -5.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.domain.xmax,  5.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.domain.ymin, -3.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.domain.ymax,  3.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.domain.zmin,  0.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.domain.zmax,  8.0, 1e-12);

    // mesh — only n_cell was given; verify defaults
    CHECK_EQ(cfg.mesh.n_cell.size(), 3u);
    CHECK_EQ(cfg.mesh.n_cell[0], 128);
    CHECK_EQ(cfg.mesh.n_cell[1],  64);
    CHECK_EQ(cfg.mesh.n_cell[2],  96);
    CHECK_EQ(cfg.mesh.max_level, 2);             // default
    CHECK_EQ(cfg.mesh.blocking_factor, 8);       // default
    CHECK_EQ(cfg.mesh.max_grid_size, 32);        // default
    CHECK(cfg.mesh.refine.near_wall == true);    // default
    CHECK(cfg.mesh.refine.near_leak == true);    // default

    // physics — all defaults
    CHECK_STREQ(cfg.physics.model.c_str(), "dispersion");
    CHECK_STREQ(cfg.physics.chemistry.mechanism.c_str(), "drm19");
    CHECK_EQ(cfg.physics.species.tracked.size(), 1u);
    CHECK_STREQ(cfg.physics.species.tracked[0].c_str(), "CH4");
    CHECK_STREQ(cfg.physics.transport.model.c_str(), "Simple");
    CHECK_STREQ(cfg.physics.eos.type.c_str(), "ideal_gas");

    // time — all defaults
    CHECK_DOUBLE_EQ(cfg.time.stop_time, 10.0, 1e-12);
    CHECK_EQ(cfg.time.max_step, 10000);
    CHECK_DOUBLE_EQ(cfg.time.cfl, 0.7, 1e-12);
    CHECK_DOUBLE_EQ(cfg.time.dt_init, 1.0e-6, 1e-12);
    CHECK_DOUBLE_EQ(cfg.time.dt_max, 0.01, 1e-12);

    // leaks — empty
    CHECK_EQ(cfg.leaks.size(), 0u);

    // wind — all defaults
    CHECK_STREQ(cfg.wind.model.c_str(), "log_law");
    CHECK_DOUBLE_EQ(cfg.wind.reference_height, 10.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.wind.reference_speed,   5.0, 1e-12);
    CHECK_DOUBLE_EQ(cfg.wind.roughness_length,  0.03, 1e-12);

    // pool — defaults (disabled)
    CHECK(cfg.pool.enabled == false);

    // ignition — defaults (disabled)
    CHECK(cfg.ignition.enabled == false);

    // turbulence — defaults
    CHECK_STREQ(cfg.turbulence.model.c_str(), "k_epsilon");
    CHECK_STREQ(cfg.turbulence.wall_function.c_str(), "launder_spalding");

    // output — defaults
    CHECK_EQ(cfg.output.plot_int, 100);
    CHECK_EQ(cfg.output.chk_int, 500);
    CHECK(cfg.output.diagnostics == true);
    CHECK_EQ(cfg.output.diagnostics_interval, 10);
    CHECK_STREQ(cfg.output.format.c_str(), "plotfile");
}

// ─── Test 3: Missing required field ─────────────────────────────────────────

static void do_missing_required() {
    // domain is missing → fatal
    write_temp(temp_path("codex_test_missing.yaml"),
        "geometry:\n"
        "  type: stl\n"
        "  file: foo.stl\n"
        "mesh:\n"
        "  n_cell: [64, 32, 48]\n");
    YamlParser::parse_config(temp_path("codex_test_missing.yaml"));
    // Should not reach here
}

void test_missing_required() {
    TEST("Missing required field (domain)");
    int status = run_in_child_and_wait(do_missing_required);
    CHECK(status == 1);
}

// ─── Test 4: Multiple leak sources ──────────────────────────────────────────

void test_multiple_leaks() {
    TEST("Multiple leak sources");
    write_temp(temp_path("codex_test_multi_leak.yaml"),
        "geometry:\n"
        "  type: builtin\n"
        "domain:\n"
        "  xmin: -1.0\n"
        "  xmax: 1.0\n"
        "  ymin: -1.0\n"
        "  ymax: 1.0\n"
        "  zmin: 0.0\n"
        "  zmax: 2.0\n"
        "mesh:\n"
        "  n_cell: [32, 32, 32]\n"
        "leaks:\n"
        "  - name: L1\n"
        "    position: [0.0, 0.0, 0.0]\n"
        "    species:\n"
        "      CH4: 0.5\n"
        "      H2: 0.5\n"
        "  - name: L2\n"
        "    position: [1.0, 1.0, 1.0]\n"
        "    species:\n"
        "      C3H8: 1.0\n"
        "  - name: L3\n"
        "    position: [2.0, 2.0, 2.0]\n");

    auto cfg = YamlParser::parse_config(temp_path("codex_test_multi_leak.yaml"));

    CHECK_EQ(cfg.leaks.size(), 3u);
    CHECK_STREQ(cfg.leaks[0].name.c_str(), "L1");
    CHECK_STREQ(cfg.leaks[1].name.c_str(), "L2");
    CHECK_STREQ(cfg.leaks[2].name.c_str(), "L3");

    CHECK_EQ(cfg.leaks[0].species.size(), 2u);
    CHECK_DOUBLE_EQ(cfg.leaks[0].species.at("CH4"), 0.5, 1e-12);
    CHECK_DOUBLE_EQ(cfg.leaks[0].species.at("H2"),  0.5, 1e-12);

    CHECK_EQ(cfg.leaks[1].species.size(), 1u);
    CHECK_DOUBLE_EQ(cfg.leaks[1].species.at("C3H8"), 1.0, 1e-12);

    CHECK_EQ(cfg.leaks[2].species.size(), 0u);
}

// ─── Test 5: Optional modules disabled ──────────────────────────────────────

void test_optional_modules_disabled() {
    TEST("Optional modules disabled");
    write_temp(temp_path("codex_test_optional_disabled.yaml"),
        "geometry:\n"
        "  type: builtin\n"
        "domain:\n"
        "  xmin: -1.0\n"
        "  xmax: 1.0\n"
        "  ymin: -1.0\n"
        "  ymax: 1.0\n"
        "  zmin: 0.0\n"
        "  zmax: 2.0\n"
        "mesh:\n"
        "  n_cell: [16, 16, 16]\n"
        "pool:\n"
        "  enabled: false\n"
        "  area: 999.0\n"
        "  species: SHOULD_NOT_BE_READ\n"
        "ignition:\n"
        "  enabled: false\n"
        "  type: hot_surface\n"
        "  energy: 999.0\n");

    auto cfg = YamlParser::parse_config(temp_path("codex_test_optional_disabled.yaml"));

    // pool — disabled, so defaults preserved
    CHECK(cfg.pool.enabled == false);
    CHECK_STREQ(cfg.pool.species.c_str(), "C8H18");  // default
    CHECK_DOUBLE_EQ(cfg.pool.area, 1.0, 1e-12);       // default (999 was ignored)

    // ignition — disabled, so defaults preserved
    CHECK(cfg.ignition.enabled == false);
    CHECK_STREQ(cfg.ignition.type.c_str(), "spark");  // default (hot_surface was ignored)
    CHECK_DOUBLE_EQ(cfg.ignition.energy, 0.0, 1e-12);  // default (999 was ignored)
}

// ─── Test 6: Type error ────────────────────────────────────────────────────

static void do_type_error() {
    write_temp(temp_path("codex_test_type_error.yaml"),
        "geometry:\n"
        "  type: stl\n"
        "  file: foo.stl\n"
        "domain:\n"
        "  xmin: -1.0\n"
        "  xmax: 1.0\n"
        "  ymin: -1.0\n"
        "  ymax: 1.0\n"
        "  zmin: 0.0\n"
        "  zmax: not_a_number\n");   // type error!
    YamlParser::parse_config(temp_path("codex_test_type_error.yaml"));
    // Should not reach here
}

void test_type_error() {
    TEST("Type error (string where double expected)");
    int status = run_in_child_and_wait(do_type_error);
    CHECK(status == 1);
}

// ─── Test 7: Additional edge cases ──────────────────────────────────────────

// Test: geometry.type=stl without file should abort
static void do_stl_no_file() {
    write_temp(temp_path("codex_test_stl_nofile.yaml"),
        "geometry:\n"
        "  type: stl\n"
        "domain:\n"
        "  xmin: -1.0\n"
        "  xmax: 1.0\n"
        "  ymin: -1.0\n"
        "  ymax: 1.0\n"
        "  zmin: 0.0\n"
        "  zmax: 2.0\n"
        "mesh:\n"
        "  n_cell: [32, 32, 32]\n");
    YamlParser::parse_config(temp_path("codex_test_stl_nofile.yaml"));
}

void test_stl_no_file() {
    TEST("STL geometry without file → abort");
    int status = run_in_child_and_wait(do_stl_no_file);
    CHECK(status == 1);
}

// Test: n_cell wrong size should abort
static void do_ncell_wrong_size() {
    write_temp(temp_path("codex_test_ncell_wrong.yaml"),
        "geometry:\n"
        "  type: builtin\n"
        "domain:\n"
        "  xmin: -1.0\n"
        "  xmax: 1.0\n"
        "  ymin: -1.0\n"
        "  ymax: 1.0\n"
        "  zmin: 0.0\n"
        "  zmax: 2.0\n"
        "mesh:\n"
        "  n_cell: [32, 32]\n");  // only 2 elements!
    YamlParser::parse_config(temp_path("codex_test_ncell_wrong.yaml"));
}

void test_ncell_wrong_size() {
    TEST("n_cell wrong size → abort");
    int status = run_in_child_and_wait(do_ncell_wrong_size);
    CHECK(status == 1);
}


// --- Test 9: YAML to AMReX/PeleLMeX ParmParse adapter ------------------------

static bool contains_line(const std::string& text, const std::string& line) {
    return text.find(line + "\n") != std::string::npos;
}

void test_parmparse_writer() {
    TEST("YAML schema to ParmParse adapter");
    auto cfg = YamlParser::parse_config("test/unit/test_full.yaml");

    ParmParseWriter::Options opt;
    opt.space_dim = 2;
    opt.include_comments = false;
    const std::string pp = ParmParseWriter::to_string(cfg, opt);

    CHECK(contains_line(pp, "geometry.coord_sys = 0"));
    CHECK(contains_line(pp, "geometry.is_periodic = 0 0"));
    CHECK(contains_line(pp, "geometry.prob_lo = -10 -5"));
    CHECK(contains_line(pp, "geometry.prob_hi = 10 5"));
    CHECK(contains_line(pp, "amr.n_cell = 256 128"));
    CHECK(contains_line(pp, "amr.max_level = 3"));
    CHECK(contains_line(pp, "amr.blocking_factor = 16"));
    CHECK(contains_line(pp, "amr.max_grid_size = 64"));
    CHECK(contains_line(pp, "amr.cfl = 0.5"));
    CHECK(contains_line(pp, "amr.max_step = 50000"));
    CHECK(contains_line(pp, "amr.stop_time = 30"));
    CHECK(contains_line(pp, "amr.plot_int = 50"));
    CHECK(contains_line(pp, "amr.check_int = 200"));
    CHECK(contains_line(pp, "peleLM.les_model = kepsilon"));
    CHECK(contains_line(pp, "peleLM.aux_vars = k epsilon"));
    CHECK(contains_line(pp, "my_pele.geometry.type = stl"));
    CHECK(contains_line(pp, "my_pele.geometry.file = test/tanks.stl"));
    CHECK(contains_line(pp, "my_pele.species.tracked = CH4 C3H8 H2"));
    CHECK(contains_line(pp, "my_pele.boundaries.xlo = inlet"));
    CHECK(contains_line(pp, "my_pele.boundaries.yhi = symmetry"));
    CHECK(contains_line(pp, "my_pele.wind.model = power_law"));
    CHECK(contains_line(pp, "my_pele.wind.direction = 1 0"));
    CHECK(contains_line(pp, "my_pele.pool.enabled = 1"));
    CHECK(contains_line(pp, "my_pele.pool.species = C8H18"));
    CHECK(contains_line(pp, "my_pele.ignition.enabled = 0"));
    CHECK(contains_line(pp, "my_pele.leaks.count = 2"));
    CHECK(contains_line(pp, "my_pele.leaks.0.name = leak_main"));
    CHECK(contains_line(pp, "my_pele.leaks.0.species.CH4 = 0.90000000000000002"));
    CHECK(contains_line(pp, "my_pele.leaks.1.species.H2 = 1"));
    CHECK(contains_line(pp, "amr.derive_plot_vars = avg_pressure mag_vort"));
    CHECK(contains_line(pp, "peleLM.lo_bc = Inflow NoSlipWallAdiab"));
    CHECK(contains_line(pp, "peleLM.hi_bc = Outflow Symmetry"));
    CHECK(contains_line(pp, "prob.meanFlowMag = 4"));
}

void test_boundary_tags_to_pelelmex_bc() {
    TEST("Typed boundary tags to PeleLMeX BC lines");
    YamlSchema::Config cfg;
    cfg.domain.xmin = 0.0;
    cfg.domain.xmax = 2.0;
    cfg.domain.ymin = 0.0;
    cfg.domain.ymax = 1.0;
    cfg.domain.zmin = 0.0;
    cfg.domain.zmax = 1.0;
    cfg.mesh.n_cell = {16, 8, 4};
    cfg.boundaries.faces.xlo = "inlet";
    cfg.boundaries.faces.xhi = "outlet";
    cfg.boundaries.faces.ylo = "wall";
    cfg.boundaries.faces.yhi = "symmetry";
    cfg.boundaries.faces.zlo = "slip_wall";
    cfg.boundaries.faces.zhi = "outflow";

    ParmParseWriter::Options opt;
    opt.space_dim = 3;
    opt.include_comments = false;
    const std::string pp = ParmParseWriter::to_string(cfg, opt);

    CHECK(contains_line(pp, "peleLM.lo_bc = Inflow NoSlipWallAdiab SlipWallAdiab"));
    CHECK(contains_line(pp, "peleLM.hi_bc = Outflow Symmetry Outflow"));
    CHECK(contains_line(pp, "my_pele.boundaries.zlo = slip_wall"));
    CHECK(contains_line(pp, "my_pele.boundaries.zhi = outflow"));
}

// ─── main ───────────────────────────────────────────────────────────────────

int main() {
    std::cout << "=== Phase 2.1 YAML Parser Tests ===\n" << std::endl;

    test_full_yaml();
    test_minimal_yaml();
    test_missing_required();
    test_multiple_leaks();
    test_optional_modules_disabled();
    test_type_error();
    test_stl_no_file();
    test_ncell_wrong_size();
    test_parmparse_writer();
    test_boundary_tags_to_pelelmex_bc();

    std::cout << "\n=== Results: " << pass_count << " passed, "
              << fail_count << " failed ===" << std::endl;

    return fail_count > 0 ? 1 : 0;
}
