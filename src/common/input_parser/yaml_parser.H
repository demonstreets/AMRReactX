#pragma once
#include "yaml_schema.H"
#include <yaml-cpp/yaml.h>

namespace YamlParser {

// Main entry point: parse a YAML file into the full Config
YamlSchema::Config parse_config(const std::string& yaml_file_path);

// Sub-module parse functions (exposed for unit testing)
YamlSchema::GeometryConfig   parse_geometry(const YAML::Node& node);
YamlSchema::DomainConfig     parse_domain(const YAML::Node& node);
YamlSchema::MeshConfig       parse_mesh(const YAML::Node& node);
YamlSchema::PhysicsConfig    parse_physics(const YAML::Node& node);
YamlSchema::TimeConfig       parse_time(const YAML::Node& node);
YamlSchema::LeakSource       parse_leak(const YAML::Node& node);
YamlSchema::WindConfig       parse_wind(const YAML::Node& node);
YamlSchema::PoolConfig       parse_pool(const YAML::Node& node);
YamlSchema::IgnitionConfig   parse_ignition(const YAML::Node& node);
YamlSchema::TurbulenceConfig parse_turbulence(const YAML::Node& node);
YamlSchema::OutputConfig     parse_output(const YAML::Node& node);

} // namespace YamlParser
