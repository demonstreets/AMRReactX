#pragma once
#include <string>
#include <vector>
#include <array>
#include <map>

namespace YamlSchema {

// --- Geometry ---
struct GeometryConfig {
    std::string type  = "stl";   // "stl" | "builtin"
    std::string file  = "";
    double      scale = 1.0;
};

// --- Domain ---
struct DomainConfig {
    double xmin = -5.0, xmax = 5.0;
    double ymin = -3.0, ymax = 3.0;
    double zmin =  0.0, zmax = 8.0;
};

// --- Mesh ---
struct RefineConfig {
    bool near_wall = true;
    bool near_leak = true;
};

struct MeshConfig {
    std::vector<int> n_cell          = {128, 64, 96};
    int              max_level       = 2;
    int              blocking_factor = 8;
    int              max_grid_size   = 32;
    RefineConfig     refine;
};

// --- Physics ---
struct ChemistryConfig {
    std::string mechanism      = "drm19";
    std::string mechanism_file = "";
};

struct SpeciesConfig {
    std::vector<std::string> tracked = {"CH4"};
};

struct TransportConfig {
    std::string model = "Simple";   // "Simple" | "Constant" | "Sutherland"
};

struct EOSConfig {
    std::string type = "ideal_gas";
};

struct PhysicsConfig {
    std::string     model = "dispersion";  // "dispersion" | "fire" | "full"
    ChemistryConfig chemistry;
    SpeciesConfig   species;
    TransportConfig transport;
    EOSConfig       eos;
};

// --- Time ---
struct TimeConfig {
    double stop_time = 10.0;
    int    max_step  = 10000;
    double cfl       = 0.7;
    double dt_init   = 1.0e-6;
    double dt_max    = 0.01;
};

// --- Leak source ---
struct LeakSource {
    std::string                     name;
    std::array<double, 3>           position      = {0.0, 0.0, 0.0};
    double                          radius        = 0.01;
    std::array<double, 3>           direction     = {0.0, 0.0, 1.0};
    std::map<std::string, double>   species;          // species_name -> mass_fraction
    double                          mass_flow_rate = 0.1;
    double                          temperature    = 300.0;
    double                          velocity       = 10.0;
};

// --- Boundary conditions ---
struct BoundaryFaces {
    std::string xlo = "";
    std::string xhi = "";
    std::string ylo = "";
    std::string yhi = "";
    std::string zlo = "";
    std::string zhi = "";
};

struct BoundaryConfig {
    BoundaryFaces faces;
};

// --- Wind BC ---
struct WindConfig {
    std::string           model            = "log_law";   // "log_law" | "power_law" | "uniform"
    double                reference_height = 10.0;
    double                reference_speed  = 5.0;
    double                roughness_length = 0.03;
    std::array<double, 3> direction        = {1.0, 0.0, 0.0};
};

// --- Liquid pool ---
struct PoolConfig {
    bool                  enabled     = false;
    std::array<double, 3> position    = {0.0, 0.0, 0.0};
    double                area        = 1.0;
    std::string           species     = "C8H18";
    double                temperature = 300.0;
};

// --- Ignition ---
struct IgnitionConfig {
    bool                  enabled  = false;
    std::string           type     = "spark";   // "spark" | "hot_surface"
    std::array<double, 3> position = {0.0, 0.0, 0.0};
    double                time     = 0.0;
    double                energy   = 0.0;
    double                radius   = 0.0;
};

// --- Turbulence ---
struct TurbulenceConstants {
    double C_mu    = 0.09;
    double C_eps1  = 1.44;
    double C_eps2  = 1.92;
    double sigma_k = 1.0;
    double sigma_eps = 1.3;
};

struct TurbulenceConfig {
    std::string          model         = "k_epsilon";  // "k_epsilon" | "none"
    TurbulenceConstants  constants;
    std::string          wall_function = "launder_spalding";
};

// --- Output ---
struct OutputConfig {
    int         plot_int             = 100;
    int         chk_int              = 500;
    bool        diagnostics          = true;
    int         diagnostics_interval = 10;
    std::string format               = "plotfile";
};

// --- Top-level config ---
struct Config {
    GeometryConfig   geometry;
    DomainConfig     domain;
    MeshConfig       mesh;
    PhysicsConfig    physics;
    TimeConfig       time;
    std::vector<LeakSource> leaks;
    BoundaryConfig   boundaries;
    WindConfig       wind;
    PoolConfig       pool;
    IgnitionConfig   ignition;
    TurbulenceConfig turbulence;
    OutputConfig     output;
    std::map<std::string, std::string> parmparse; // extra raw ParmParse keys for solver-specific options
};

} // namespace YamlSchema
