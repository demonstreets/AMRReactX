#include "parmparse_writer.H"
#include "yaml_parser.H"

#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

void usage(const char* argv0) {
    std::cerr << "usage: " << argv0 << " <input.yaml> <output.inputs> [--dim 2|3] [--solver-only]\n";
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        usage(argv[0]);
        return 2;
    }

    ParmParseWriter::Options options;
    for (int i = 3; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--dim") {
            if (++i >= argc) {
                usage(argv[0]);
                return 2;
            }
            options.space_dim = std::stoi(argv[i]);
        } else if (arg == "--solver-only") {
            options.include_metadata = false;
        } else {
            usage(argv[0]);
            return 2;
        }
    }

    try {
        const auto cfg = YamlParser::parse_config(argv[1]);
        std::ofstream out(argv[2]);
        if (!out.good()) {
            std::cerr << "cannot open output file: " << argv[2] << '\n';
            return 1;
        }
        ParmParseWriter::write(out, cfg, options);
    } catch (const std::exception& e) {
        std::cerr << "yaml-to-parmparse error: " << e.what() << '\n';
        return 1;
    }

    return 0;
}
