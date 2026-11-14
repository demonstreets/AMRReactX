#include "parmparse_writer.H"
#include "bc_tags.H"

#include <algorithm>
#include <iomanip>
#include <ostream>
#include <sstream>
#include <stdexcept>

namespace ParmParseWriter {
namespace {

int checked_dim(int space_dim) {
    if (space_dim != 2 && space_dim != 3) {
        throw std::invalid_argument("ParmParseWriter space_dim must be 2 or 3");
    }
    return space_dim;
}

std::string scalar(double value) {
    std::ostringstream os;
    os << std::setprecision(17) << value;
    return os.str();
}

std::string ints(const std::vector<int>& values, int dim) {
    if (static_cast<int>(values.size()) < dim) {
        throw std::invalid_argument("mesh.n_cell has fewer entries than requested space_dim");
    }
    std::ostringstream os;
    for (int i = 0; i < dim; ++i) {
        if (i) os << ' ';
        os << values[static_cast<std::size_t>(i)];
    }
    return os.str();
}

std::string vec3_prefix(const std::array<double, 3>& values, int dim) {
    std::ostringstream os;
    for (int i = 0; i < dim; ++i) {
        if (i) os << ' ';
        os << scalar(values[static_cast<std::size_t>(i)]);
    }
    return os.str();
}

std::string bool01(bool value) { return value ? "1" : "0"; }

void push(std::vector<std::string>& lines, const std::string& key,
          const std::string& value) {
    lines.push_back(key + " = " + value);
}

void push_comment(std::vector<std::string>& lines, bool enabled,
                  const std::string& text) {
    if (enabled) lines.push_back("# " + text);
}



std::string face_type_from_dot(double dot, bool low_side) {
    constexpr double eps = 1.0e-12;
    if (low_side) {
        if (dot > eps) return "Inflow";
        if (dot < -eps) return "Outflow";
    } else {
        if (dot < -eps) return "Inflow";
        if (dot > eps) return "Outflow";
    }
    return "SlipWallAdiab";
}

bool has_override(const YamlSchema::Config& cfg, const std::string& key) {
    return cfg.parmparse.find(key) != cfg.parmparse.end();
}

bool has_boundary_faces(const YamlSchema::Config& cfg) {
    const auto& f = cfg.boundaries.faces;
    return !f.xlo.empty() || !f.xhi.empty() || !f.ylo.empty() ||
           !f.yhi.empty() || !f.zlo.empty() || !f.zhi.empty();
}

std::string pelelm_bc_from_tag(const std::string& token) {
    switch (pele::parseBoundaryType(token)) {
        case pele::BoundaryType::WALL: return "NoSlipWallAdiab";
        case pele::BoundaryType::INLET: return "Inflow";
        case pele::BoundaryType::OUTLET: return "Outflow";
        case pele::BoundaryType::SYMMETRY: return "Symmetry";
        case pele::BoundaryType::SLIP_WALL: return "SlipWallAdiab";
        case pele::BoundaryType::UNKNOWN:
            throw std::invalid_argument("Unknown boundary tag: " + token);
    }
    throw std::invalid_argument("Unknown boundary tag: " + token);
}

std::string choose_boundary_tag(const std::string& explicit_tag,
                                const std::string& fallback) {
    return explicit_tag.empty() ? fallback : pelelm_bc_from_tag(explicit_tag);
}

std::string derived_lo_bc(const YamlSchema::Config& cfg, int dim) {
    const auto& f = cfg.boundaries.faces;
    const std::string xlo = choose_boundary_tag(
        f.xlo, face_type_from_dot(cfg.wind.direction[0], true));
    if (dim == 2) {
        return xlo + " " + choose_boundary_tag(f.ylo, "NoSlipWallAdiab");
    }
    const std::string ylo = choose_boundary_tag(f.ylo, "NoSlipWallAdiab");
    const std::string zlo = choose_boundary_tag(
        f.zlo, face_type_from_dot(cfg.wind.direction[2], true));
    return xlo + " " + ylo + " " + zlo;
}

std::string derived_hi_bc(const YamlSchema::Config& cfg, int dim) {
    const auto& f = cfg.boundaries.faces;
    const std::string xhi = choose_boundary_tag(
        f.xhi, face_type_from_dot(cfg.wind.direction[0], false));
    if (dim == 2) {
        return xhi + " " + choose_boundary_tag(f.yhi, "SlipWallAdiab");
    }
    const std::string yhi = choose_boundary_tag(f.yhi, "Symmetry");
    const std::string zhi = choose_boundary_tag(
        f.zhi, face_type_from_dot(cfg.wind.direction[2], false));
    return xhi + " " + yhi + " " + zhi;
}

std::string pelelm_turbulence_model(const std::string& model) {
    if (model == "k_epsilon") return "kepsilon";
    return model;
}

std::string pelelm_wind_profile_type(const std::string& model) {
    if (model == "log_law") return "1";
    return "0";
}

std::string join_species(const std::vector<std::string>& species) {
    std::ostringstream os;
    for (std::size_t i = 0; i < species.size(); ++i) {
        if (i) os << ' ';
        os << species[i];
    }
    return os.str();
}

} // namespace

std::vector<std::string> to_lines(const YamlSchema::Config& cfg,
                                  const Options& options) {
    const int dim = checked_dim(options.space_dim);
    std::vector<std::string> lines;

    push_comment(lines, options.include_comments,
                 "Generated from my-pele YAML schema for AMReX/PeleLMeX ParmParse input.");
    push(lines, "geometry.coord_sys", "0");
    push(lines, "geometry.is_periodic", dim == 2 ? "0 0" : "0 0 0");
    push(lines, "geometry.prob_lo",
         dim == 2 ? scalar(cfg.domain.xmin) + " " + scalar(cfg.domain.ymin)
                  : scalar(cfg.domain.xmin) + " " + scalar(cfg.domain.ymin) + " " + scalar(cfg.domain.zmin));
    push(lines, "geometry.prob_hi",
         dim == 2 ? scalar(cfg.domain.xmax) + " " + scalar(cfg.domain.ymax)
                  : scalar(cfg.domain.xmax) + " " + scalar(cfg.domain.ymax) + " " + scalar(cfg.domain.zmax));

    lines.push_back("");
    push(lines, "amr.n_cell", ints(cfg.mesh.n_cell, dim));
    push(lines, "amr.max_level", std::to_string(cfg.mesh.max_level));
    push(lines, "amr.blocking_factor", std::to_string(cfg.mesh.blocking_factor));
    push(lines, "amr.max_grid_size", std::to_string(cfg.mesh.max_grid_size));
    push(lines, "amr.cfl", scalar(cfg.time.cfl));
    push(lines, "amr.max_step", std::to_string(cfg.time.max_step));
    push(lines, "amr.stop_time", scalar(cfg.time.stop_time));
    push(lines, "amr.plot_int", std::to_string(cfg.output.plot_int));
    push(lines, "amr.check_int", std::to_string(cfg.output.chk_int));

    lines.push_back("");
    push(lines, "peleLM.incompressible", cfg.physics.model == "dispersion" ? "0" : "0");
    push(lines, "peleLM.les_model", pelelm_turbulence_model(cfg.turbulence.model));
    push(lines, "peleLM.ke_wall_functions", cfg.turbulence.wall_function.empty() ? "0" : "1");
    push(lines, "peleLM.aux_vars", cfg.turbulence.model == "k_epsilon" ? "k epsilon" : "");

    if (!has_override(cfg, "peleLM.lo_bc")) {
        push(lines, "peleLM.lo_bc", derived_lo_bc(cfg, dim));
    }
    if (!has_override(cfg, "peleLM.hi_bc")) {
        push(lines, "peleLM.hi_bc", derived_hi_bc(cfg, dim));
    }
    if (!has_override(cfg, "prob.meanFlowMag")) {
        push(lines, "prob.meanFlowMag", scalar(cfg.wind.reference_speed));
    }
    if (!has_override(cfg, "prob.windProfileType")) {
        push(lines, "prob.windProfileType", pelelm_wind_profile_type(cfg.wind.model));
    }
    if (!has_override(cfg, "prob.windRefHeight")) {
        push(lines, "prob.windRefHeight", scalar(cfg.wind.reference_height));
    }
    if (!has_override(cfg, "prob.windRoughnessLength")) {
        push(lines, "prob.windRoughnessLength", scalar(cfg.wind.roughness_length));
    }

    if (options.include_metadata) {
    lines.push_back("");
    push(lines, "my_pele.geometry.type", cfg.geometry.type);
    if (!cfg.geometry.file.empty()) push(lines, "my_pele.geometry.file", cfg.geometry.file);
    push(lines, "my_pele.geometry.scale", scalar(cfg.geometry.scale));
    push(lines, "my_pele.physics.model", cfg.physics.model);
    push(lines, "my_pele.chemistry.mechanism", cfg.physics.chemistry.mechanism);
    if (!cfg.physics.chemistry.mechanism_file.empty()) {
        push(lines, "my_pele.chemistry.mechanism_file", cfg.physics.chemistry.mechanism_file);
    }
    push(lines, "my_pele.species.tracked", join_species(cfg.physics.species.tracked));
    push(lines, "my_pele.transport.model", cfg.physics.transport.model);
    push(lines, "my_pele.eos.type", cfg.physics.eos.type);

    lines.push_back("");
    if (has_boundary_faces(cfg)) {
        lines.push_back("");
        push(lines, "my_pele.boundaries.xlo", cfg.boundaries.faces.xlo.empty() ? "default" : cfg.boundaries.faces.xlo);
        push(lines, "my_pele.boundaries.xhi", cfg.boundaries.faces.xhi.empty() ? "default" : cfg.boundaries.faces.xhi);
        push(lines, "my_pele.boundaries.ylo", cfg.boundaries.faces.ylo.empty() ? "default" : cfg.boundaries.faces.ylo);
        push(lines, "my_pele.boundaries.yhi", cfg.boundaries.faces.yhi.empty() ? "default" : cfg.boundaries.faces.yhi);
        if (dim == 3) {
            push(lines, "my_pele.boundaries.zlo", cfg.boundaries.faces.zlo.empty() ? "default" : cfg.boundaries.faces.zlo);
            push(lines, "my_pele.boundaries.zhi", cfg.boundaries.faces.zhi.empty() ? "default" : cfg.boundaries.faces.zhi);
        }
    }

    push(lines, "my_pele.wind.model", cfg.wind.model);
    push(lines, "my_pele.wind.reference_height", scalar(cfg.wind.reference_height));
    push(lines, "my_pele.wind.reference_speed", scalar(cfg.wind.reference_speed));
    push(lines, "my_pele.wind.roughness_length", scalar(cfg.wind.roughness_length));
    push(lines, "my_pele.wind.direction", vec3_prefix(cfg.wind.direction, dim));

    lines.push_back("");
    push(lines, "my_pele.pool.enabled", bool01(cfg.pool.enabled));
    if (cfg.pool.enabled) {
        push(lines, "my_pele.pool.position", vec3_prefix(cfg.pool.position, dim));
        push(lines, "my_pele.pool.area", scalar(cfg.pool.area));
        push(lines, "my_pele.pool.species", cfg.pool.species);
        push(lines, "my_pele.pool.temperature", scalar(cfg.pool.temperature));
    }

    lines.push_back("");
    push(lines, "my_pele.ignition.enabled", bool01(cfg.ignition.enabled));
    if (cfg.ignition.enabled) {
        push(lines, "my_pele.ignition.type", cfg.ignition.type);
        push(lines, "my_pele.ignition.position", vec3_prefix(cfg.ignition.position, dim));
        push(lines, "my_pele.ignition.time", scalar(cfg.ignition.time));
        push(lines, "my_pele.ignition.energy", scalar(cfg.ignition.energy));
        push(lines, "my_pele.ignition.radius", scalar(cfg.ignition.radius));
    }

    lines.push_back("");
    push(lines, "my_pele.leaks.count", std::to_string(cfg.leaks.size()));
    for (std::size_t i = 0; i < cfg.leaks.size(); ++i) {
        const auto& leak = cfg.leaks[i];
        const std::string prefix = "my_pele.leaks." + std::to_string(i) + ".";
        push(lines, prefix + "name", leak.name);
        push(lines, prefix + "position", vec3_prefix(leak.position, dim));
        push(lines, prefix + "radius", scalar(leak.radius));
        push(lines, prefix + "direction", vec3_prefix(leak.direction, dim));
        push(lines, prefix + "mass_flow_rate", scalar(leak.mass_flow_rate));
        push(lines, prefix + "temperature", scalar(leak.temperature));
        push(lines, prefix + "velocity", scalar(leak.velocity));
        for (const auto& kv : leak.species) {
            push(lines, prefix + "species." + kv.first, scalar(kv.second));
        }
    }


    }

    if (!cfg.parmparse.empty()) {
        lines.push_back("");
        push_comment(lines, options.include_comments,
                     "Raw solver-specific ParmParse overrides from YAML parmparse section.");
        for (const auto& kv : cfg.parmparse) {
            push(lines, kv.first, kv.second);
        }
    }

    return lines;
}

std::string to_string(const YamlSchema::Config& cfg, const Options& options) {
    std::ostringstream os;
    write(os, cfg, options);
    return os.str();
}

void write(std::ostream& os, const YamlSchema::Config& cfg,
           const Options& options) {
    const auto lines = to_lines(cfg, options);
    for (const auto& line : lines) {
        os << line << '\n';
    }
}

} // namespace ParmParseWriter
