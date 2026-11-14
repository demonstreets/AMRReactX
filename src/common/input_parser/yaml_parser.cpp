#include "yaml_parser.H"
#include <iostream>
#include <fstream>
#include <cstdlib>

namespace YamlParser {

// ─── helpers ─────────────────────────────────────────────────────────────────

static void fatal(const std::string& msg) {
    std::cerr << "[YAMLPARSER ERROR] " << msg << std::endl;
    std::exit(1);
}

/// Require a child node to exist; abort with context if not.
static YAML::Node require_node(const YAML::Node& parent, const std::string& key) {
    if (!parent[key]) {
        fatal("Missing required section/field: " + key);
    }
    return parent[key];
}

/// Read a required scalar value with type checking.
template <typename T>
static T require_scalar(const YAML::Node& parent, const std::string& key,
                        const std::string& type_name) {
    auto n = parent[key];
    if (!n) {
        fatal("Missing required field: " + key);
    }
    try {
        return n.as<T>();
    } catch (const YAML::Exception&) {
        fatal("Type error: " + key + " expected " + type_name);
    }
    return T{}; // unreachable
}

/// Read an optional scalar; return default_val when missing or null.
template <typename T>
static T optional_scalar(const YAML::Node& parent, const std::string& key,
                         T default_val, const std::string& type_name) {
    auto n = parent[key];
    if (!n) return default_val;
    try {
        return n.as<T>();
    } catch (const YAML::Exception&) {
        fatal("Type error: " + key + " expected " + type_name);
    }
    return default_val;
}

/// Read an optional string scalar.
static std::string optional_string(const YAML::Node& parent, const std::string& key,
                                   const std::string& default_val) {
    return optional_scalar<std::string>(parent, key, default_val, "string");
}

/// Read an optional double scalar.
static double optional_double(const YAML::Node& parent, const std::string& key,
                              double default_val) {
    return optional_scalar<double>(parent, key, default_val, "double");
}

/// Read an optional int scalar.
static int optional_int(const YAML::Node& parent, const std::string& key,
                        int default_val) {
    return optional_scalar<int>(parent, key, default_val, "int");
}

/// Read an optional bool scalar.
static bool optional_bool(const YAML::Node& parent, const std::string& key,
                          bool default_val) {
    return optional_scalar<bool>(parent, key, default_val, "bool");
}

/// Read a required int vector (size must be 3 for n_cell).
static std::vector<int> require_int_vec(const YAML::Node& parent,
                                        const std::string& key,
                                        size_t expected_size) {
    auto n = parent[key];
    if (!n) {
        fatal("Missing required field: " + key);
    }
    if (!n.IsSequence()) {
        fatal("Type error: " + key + " expected sequence");
    }
    std::vector<int> result;
    try {
        for (const auto& v : n) {
            result.push_back(v.as<int>());
        }
    } catch (const YAML::Exception&) {
        fatal("Type error: " + key + " expected int sequence");
    }
    if (expected_size > 0 && result.size() != expected_size) {
        fatal("Type error: " + key + " expected " +
              std::to_string(expected_size) + " elements, got " +
              std::to_string(result.size()));
    }
    return result;
}

/// Read a required 3-element double sequence into std::array<double,3>.
static std::array<double, 3> require_vec3(const YAML::Node& parent,
                                          const std::string& key) {
    auto n = parent[key];
    if (!n) {
        fatal("Missing required field: " + key);
    }
    if (!n.IsSequence()) {
        fatal("Type error: " + key + " expected sequence");
    }
    if (n.size() != 3) {
        fatal("Type error: " + key + " expected 3 elements, got " +
              std::to_string(n.size()));
    }
    try {
        return {n[0].as<double>(), n[1].as<double>(), n[2].as<double>()};
    } catch (const YAML::Exception&) {
        fatal("Type error: " + key + " expected double[3]");
    }
    return {0, 0, 0};
}

/// Read an optional 3-element double sequence.
static std::array<double, 3> optional_vec3(const YAML::Node& parent,
                                           const std::string& key,
                                           std::array<double, 3> default_val) {
    auto n = parent[key];
    if (!n) return default_val;
    if (!n.IsSequence()) {
        fatal("Type error: " + key + " expected sequence");
    }
    if (n.size() != 3) {
        fatal("Type error: " + key + " expected 3 elements, got " +
              std::to_string(n.size()));
    }
    try {
        return {n[0].as<double>(), n[1].as<double>(), n[2].as<double>()};
    } catch (const YAML::Exception&) {
        fatal("Type error: " + key + " expected double[3]");
    }
    return default_val;
}

/// Read an optional string vector.
static std::vector<std::string> optional_string_vec(
    const YAML::Node& parent, const std::string& key,
    const std::vector<std::string>& default_val) {
    auto n = parent[key];
    if (!n) return default_val;
    if (!n.IsSequence()) {
        fatal("Type error: " + key + " expected sequence");
    }
    std::vector<std::string> result;
    try {
        for (const auto& v : n)
            result.push_back(v.as<std::string>());
    } catch (const YAML::Exception&) {
        fatal("Type error: " + key + " expected string sequence");
    }
    return result;
}


static std::string node_to_parmparse_value(const YAML::Node& node,
                                           const std::string& key) {
    try {
        if (node.IsScalar()) return node.as<std::string>();
        if (node.IsSequence()) {
            std::string value;
            for (std::size_t i = 0; i < node.size(); ++i) {
                if (i) value += " ";
                value += node[i].as<std::string>();
            }
            return value;
        }
    } catch (const YAML::Exception&) {
        fatal("Type error: parmparse." + key + " expected scalar or scalar sequence");
    }
    fatal("Type error: parmparse." + key + " expected scalar or scalar sequence");
    return {};
}

static std::map<std::string, std::string> parse_parmparse_overrides(const YAML::Node& node) {
    std::map<std::string, std::string> values;
    auto pp = node["parmparse"];
    if (!pp) return values;
    if (!pp.IsMap()) fatal("Type error: parmparse expected a mapping");
    for (const auto& kv : pp) {
        std::string key;
        try {
            key = kv.first.as<std::string>();
        } catch (const YAML::Exception&) {
            fatal("Type error: parmparse keys expected strings");
        }
        if (key.empty()) fatal("Type error: parmparse key must not be empty");
        values[key] = node_to_parmparse_value(kv.second, key);
    }
    return values;
}

// ─── parse_geometry ─────────────────────────────────────────────────────────

YamlSchema::GeometryConfig parse_geometry(const YAML::Node& node) {
    YamlSchema::GeometryConfig g;
    auto geom = require_node(node, "geometry");

    g.type  = require_scalar<std::string>(geom, "type", "string");
    g.scale = optional_double(geom, "scale", 1.0);

    // file: required when type == "stl", optional otherwise
    if (g.type == "stl" || g.type == "builtin") {
        g.file = optional_string(geom, "file", "");
        if (g.type == "stl" && g.file.empty()) {
            fatal("geometry.file is required when geometry.type = \"stl\"");
        }
    } else {
        g.file = optional_string(geom, "file", "");
    }

    return g;
}

// ─── parse_domain ───────────────────────────────────────────────────────────

YamlSchema::DomainConfig parse_domain(const YAML::Node& node) {
    YamlSchema::DomainConfig d;
    auto dom = require_node(node, "domain");

    d.xmin = require_scalar<double>(dom, "xmin", "double");
    d.xmax = require_scalar<double>(dom, "xmax", "double");
    d.ymin = require_scalar<double>(dom, "ymin", "double");
    d.ymax = require_scalar<double>(dom, "ymax", "double");
    d.zmin = require_scalar<double>(dom, "zmin", "double");
    d.zmax = require_scalar<double>(dom, "zmax", "double");

    return d;
}

// ─── parse_mesh ─────────────────────────────────────────────────────────────

YamlSchema::MeshConfig parse_mesh(const YAML::Node& node) {
    YamlSchema::MeshConfig m;
    auto mesh = require_node(node, "mesh");

    m.n_cell          = require_int_vec(mesh, "n_cell", 3);
    m.max_level       = optional_int(mesh,    "max_level",       2);
    m.blocking_factor = optional_int(mesh,    "blocking_factor", 8);
    m.max_grid_size   = optional_int(mesh,    "max_grid_size",   32);

    // refine sub-node
    auto ref = mesh["refine"];
    if (ref) {
        m.refine.near_wall = optional_bool(ref, "near_wall", true);
        m.refine.near_leak = optional_bool(ref, "near_leak", true);
    }

    return m;
}

// ─── parse_physics ──────────────────────────────────────────────────────────

YamlSchema::PhysicsConfig parse_physics(const YAML::Node& node) {
    YamlSchema::PhysicsConfig p;
    auto phys = node["physics"];
    if (!phys) return p; // use all defaults

    p.model = optional_string(phys, "model", "dispersion");

    // chemistry sub-node
    auto chem = phys["chemistry"];
    if (chem) {
        p.chemistry.mechanism      = optional_string(chem, "mechanism",      "drm19");
        p.chemistry.mechanism_file = optional_string(chem, "mechanism_file", "");
    }

    // species sub-node
    auto spec = phys["species"];
    if (spec) {
        p.species.tracked = optional_string_vec(spec, "tracked", {"CH4"});
    }

    // transport sub-node
    auto trans = phys["transport"];
    if (trans) {
        p.transport.model = optional_string(trans, "model", "Simple");
    }

    // eos sub-node
    auto eos = phys["eos"];
    if (eos) {
        p.eos.type = optional_string(eos, "type", "ideal_gas");
    }

    return p;
}

// ─── parse_time ─────────────────────────────────────────────────────────────

YamlSchema::TimeConfig parse_time(const YAML::Node& node) {
    YamlSchema::TimeConfig t;
    auto time = node["time"];
    if (!time) return t;

    t.stop_time = optional_double(time, "stop_time", 10.0);
    t.max_step  = optional_int(time,    "max_step",  10000);
    t.cfl       = optional_double(time, "cfl",       0.7);
    t.dt_init   = optional_double(time, "dt_init",   1.0e-6);
    t.dt_max    = optional_double(time, "dt_max",    0.01);

    return t;
}

// ─── parse_leak ─────────────────────────────────────────────────────────────

YamlSchema::LeakSource parse_leak(const YAML::Node& node) {
    YamlSchema::LeakSource l;

    l.name = require_scalar<std::string>(node, "name", "string");
    l.position      = optional_vec3(node, "position",       {0.0, 0.0, 0.0});
    l.radius        = optional_double(node, "radius",        0.01);
    l.direction     = optional_vec3(node, "direction",      {0.0, 0.0, 1.0});
    l.mass_flow_rate = optional_double(node, "mass_flow_rate", 0.1);
    l.temperature   = optional_double(node, "temperature",   300.0);
    l.velocity      = optional_double(node, "velocity",      10.0);

    // species map
    auto spec = node["species"];
    if (spec) {
        if (spec.IsMap()) {
            for (const auto& kv : spec) {
                try {
                    l.species[kv.first.as<std::string>()] = kv.second.as<double>();
                } catch (const YAML::Exception&) {
                    fatal("Type error: leak.species values expected double");
                }
            }
        } else {
            fatal("Type error: leak.species expected a mapping (key-value pairs)");
        }
    }

    return l;
}

// ─── parse_wind ─────────────────────────────────────────────────────────────

YamlSchema::WindConfig parse_wind(const YAML::Node& node) {
    YamlSchema::WindConfig w;
    auto wind = node["wind"];
    if (!wind) return w;

    w.model            = optional_string(wind, "model",            "log_law");
    w.reference_height = optional_double(wind, "reference_height", 10.0);
    w.reference_speed  = optional_double(wind, "reference_speed",  5.0);
    w.roughness_length = optional_double(wind, "roughness_length", 0.03);
    w.direction        = optional_vec3(wind,  "direction",        {1.0, 0.0, 0.0});

    return w;
}

// ─── parse_boundaries ───────────────────────────────────────────────────────

YamlSchema::BoundaryConfig parse_boundaries(const YAML::Node& node) {
    YamlSchema::BoundaryConfig b;
    auto boundaries = node["boundaries"];
    if (!boundaries) return b;
    auto faces = boundaries["faces"];
    if (!faces) return b;
    if (!faces.IsMap()) fatal("Type error: boundaries.faces expected a mapping");

    b.faces.xlo = optional_string(faces, "xlo", "");
    b.faces.xhi = optional_string(faces, "xhi", "");
    b.faces.ylo = optional_string(faces, "ylo", "");
    b.faces.yhi = optional_string(faces, "yhi", "");
    b.faces.zlo = optional_string(faces, "zlo", "");
    b.faces.zhi = optional_string(faces, "zhi", "");
    return b;
}

// ─── parse_pool ─────────────────────────────────────────────────────────────

YamlSchema::PoolConfig parse_pool(const YAML::Node& node) {
    YamlSchema::PoolConfig p;
    auto pool = node["pool"];
    if (!pool) return p;

    p.enabled = optional_bool(pool, "enabled", false);

    // When disabled, ignore other fields
    if (p.enabled) {
        p.position    = optional_vec3(pool,   "position",    {0.0, 0.0, 0.0});
        p.area        = optional_double(pool, "area",        1.0);
        p.species     = optional_string(pool, "species",     "C8H18");
        p.temperature = optional_double(pool, "temperature", 300.0);
    }

    return p;
}

// ─── parse_ignition ─────────────────────────────────────────────────────────

YamlSchema::IgnitionConfig parse_ignition(const YAML::Node& node) {
    YamlSchema::IgnitionConfig ig;
    auto ign = node["ignition"];
    if (!ign) return ig;

    ig.enabled = optional_bool(ign, "enabled", false);

    if (ig.enabled) {
        ig.type     = optional_string(ign, "type",     "spark");
        ig.position = optional_vec3(ign,   "position", {0.0, 0.0, 0.0});
        ig.time     = optional_double(ign, "time",     0.0);
        ig.energy   = optional_double(ign, "energy",   0.0);
        ig.radius   = optional_double(ign, "radius",   0.0);
    }

    return ig;
}

// ─── parse_turbulence ───────────────────────────────────────────────────────

YamlSchema::TurbulenceConfig parse_turbulence(const YAML::Node& node) {
    YamlSchema::TurbulenceConfig t;
    auto turb = node["turbulence"];
    if (!turb) return t;

    t.model         = optional_string(turb, "model",         "k_epsilon");
    t.wall_function = optional_string(turb, "wall_function", "launder_spalding");

    // constants sub-node
    auto cons = turb["constants"];
    if (cons) {
        t.constants.C_mu    = optional_double(cons, "C_mu",    0.09);
        t.constants.C_eps1  = optional_double(cons, "C_eps1",  1.44);
        t.constants.C_eps2  = optional_double(cons, "C_eps2",  1.92);
        t.constants.sigma_k = optional_double(cons, "sigma_k", 1.0);
        t.constants.sigma_eps = optional_double(cons, "sigma_eps", 1.3);
    }

    return t;
}

// ─── parse_output ───────────────────────────────────────────────────────────

YamlSchema::OutputConfig parse_output(const YAML::Node& node) {
    YamlSchema::OutputConfig o;
    auto out = node["output"];
    if (!out) return o;

    o.plot_int             = optional_int(out,    "plot_int",             100);
    o.chk_int              = optional_int(out,    "chk_int",              500);
    o.diagnostics          = optional_bool(out,   "diagnostics",          true);
    o.diagnostics_interval = optional_int(out,    "diagnostics_interval",  10);
    o.format               = optional_string(out, "format",               "plotfile");

    return o;
}

// ─── parse_config (main entry) ──────────────────────────────────────────────

YamlSchema::Config parse_config(const std::string& yaml_file_path) {
    // Check file existence
    std::ifstream check(yaml_file_path);
    if (!check.good()) {
        fatal("Cannot open YAML file: " + yaml_file_path);
    }
    check.close();

    YAML::Node root;
    try {
        root = YAML::LoadFile(yaml_file_path);
    } catch (const YAML::Exception& e) {
        fatal("YAML parse error: " + std::string(e.what()));
    }

    if (!root.IsMap()) {
        fatal("YAML root must be a mapping");
    }

    YamlSchema::Config config;

    config.geometry   = parse_geometry(root);
    config.domain     = parse_domain(root);
    config.mesh       = parse_mesh(root);
    config.physics    = parse_physics(root);
    config.time       = parse_time(root);

    // leaks array
    auto leaks_node = root["leaks"];
    if (leaks_node) {
        if (leaks_node.IsSequence()) {
            for (const auto& l : leaks_node) {
                config.leaks.push_back(parse_leak(l));
            }
        } else {
            fatal("Type error: leaks expected a sequence (list)");
        }
    }

    config.boundaries = parse_boundaries(root);
    config.wind       = parse_wind(root);
    config.pool       = parse_pool(root);
    config.ignition   = parse_ignition(root);
    config.turbulence = parse_turbulence(root);
    config.output     = parse_output(root);
    config.parmparse  = parse_parmparse_overrides(root);

    return config;
}

} // namespace YamlParser
