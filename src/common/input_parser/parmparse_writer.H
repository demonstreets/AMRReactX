#pragma once

#include "yaml_schema.H"

#include <iosfwd>
#include <string>
#include <vector>

namespace ParmParseWriter {

struct Options {
    int space_dim = 3;
    bool include_comments = true;
    bool include_metadata = true;
};

std::vector<std::string> to_lines(const YamlSchema::Config& cfg,
                                  const Options& options = Options{});

std::string to_string(const YamlSchema::Config& cfg,
                      const Options& options = Options{});

void write(std::ostream& os, const YamlSchema::Config& cfg,
           const Options& options = Options{});

} // namespace ParmParseWriter
