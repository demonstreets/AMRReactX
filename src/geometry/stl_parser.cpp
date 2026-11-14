#include "stl_parser.H"
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cctype>
#include <cstring>
#include <limits>
#include <stdexcept>
namespace pele {
namespace {
bool isLittleEndian(){
    const uint32_t test=1u;
    return *reinterpret_cast<const uint8_t*>(&test)==1;
}

std::string lowerCopy(std::string value)
{
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return value;
}

bool hasSuffix(const std::string& value, const std::string& suffix)
{
    return value.size() >= suffix.size() &&
           value.compare(value.size() - suffix.size(), suffix.size(), suffix) == 0;
}

bool hasStepExtension(const std::string& fn)
{
    const auto lower = lowerCopy(fn);
    return hasSuffix(lower, ".stp") || hasSuffix(lower, ".step");
}

bool headerLooksLikeSTEP(const std::string& header)
{
    const auto lower = lowerCopy(header);
    return lower.find("iso-10303-21") != std::string::npos ||
           lower.find("header;") != std::string::npos;
}

bool headerStartsWithSolid(const std::string& header)
{
    auto first = header.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) return false;
    return header.compare(first, 5, "solid") == 0;
}
} // anon
void STLReader::read(const std::string& fn) {
    m_facets.clear();

    std::ifstream f(fn, std::ios::binary | std::ios::ate);
    if (!f) throw std::runtime_error("Cannot open: " + fn);

    const auto file_size_pos = f.tellg();
    if (file_size_pos < 0) {
        throw std::runtime_error("Cannot determine STL file size: " + fn);
    }
    const auto file_size = static_cast<std::uint64_t>(file_size_pos);
    f.seekg(0);

    std::string header(static_cast<std::size_t>(std::min<std::uint64_t>(file_size, 512)), '\0');
    if (!header.empty()) {
        f.read(header.data(), static_cast<std::streamsize>(header.size()));
        f.clear();
        f.seekg(0);
    }

    if (hasStepExtension(fn) || headerLooksLikeSTEP(header)) {
        throw std::runtime_error("STEP geometry requires offline conversion to STL; native STEP/OpenCascade import is not available in this build: " + fn);
    }

    bool size_matches_binary = false;
    if (file_size >= 84) {
        f.seekg(80);
        std::uint32_t n = 0;
        f.read(reinterpret_cast<char*>(&n), 4);
        const std::uint64_t expected = 84ull + 50ull * static_cast<std::uint64_t>(n);
        size_matches_binary = (expected == file_size);
    }

    if (size_matches_binary) {
        readBinary(fn);
    } else if (headerStartsWithSolid(header)) {
        readASCII(fn);
    } else {
        throw std::runtime_error("Unsupported geometry format; expected STL or offline-converted STEP-to-STL geometry: " + fn);
    }

    if (m_facets.empty()) {
        throw std::runtime_error("STL contains no facets: " + fn);
    }
}
void STLReader::readASCII(const std::string& fn) {
    std::ifstream f(fn);
    std::string line;
    STLFacet fac;
    int vi = 0;
    while (std::getline(f, line)) {
        std::istringstream ss(line);
        std::string kw;
        ss >> kw;
        if (kw == "facet") {
            fac = STLFacet{};
            std::string ni;
            ss >> ni;
            ss >> fac.normal[0] >> fac.normal[1] >> fac.normal[2];
        } else if (kw == "vertex") {
            ss >> fac.vertices[vi][0] >> fac.vertices[vi][1] >> fac.vertices[vi][2];
            vi++;
        } else if (kw == "endfacet") {
            if (vi == 3) m_facets.push_back(fac);
            vi = 0;
        }
    }
}
void STLReader::readBinary(const std::string& fn) {
    if(!isLittleEndian())
        throw std::runtime_error("STL binary reader supports little-endian only");
    std::ifstream f(fn, std::ios::binary | std::ios::ate);
    if (!f) throw std::runtime_error("Cannot open: " + fn);
    const auto file_size_pos = f.tellg();
    if (file_size_pos < 84) {
        throw std::runtime_error("Binary STL too small: " + fn);
    }
    const auto file_size = static_cast<std::uint64_t>(file_size_pos);
    f.seekg(80);
    uint32_t n = 0;
    f.read(reinterpret_cast<char*>(&n), 4);
    constexpr uint32_t MAX_FACETS = 100'000'000u; // 100M
    if(n>MAX_FACETS)
        throw std::runtime_error("STL facet count "+std::to_string(n)+
                                 " exceeds limit "+std::to_string(MAX_FACETS));
    const std::uint64_t expected = 84ull + 50ull * static_cast<std::uint64_t>(n);
    if (expected != file_size) {
        throw std::runtime_error("Binary STL size mismatch for " + fn);
    }
    for (uint32_t i = 0; i < n; i++) {
        STLFacet fac{};
        float normal[3] = {};
        float vertex[3] = {};
        f.read(reinterpret_cast<char*>(normal), sizeof(normal));
        for (int c = 0; c < 3; ++c) fac.normal[c] = static_cast<double>(normal[c]);
        for (int j = 0; j < 3; j++) {
            f.read(reinterpret_cast<char*>(vertex), sizeof(vertex));
            for (int c = 0; c < 3; ++c) fac.vertices[j][c] = static_cast<double>(vertex[c]);
        }
        f.seekg(2, std::ios::cur);
        if (!f) {
            throw std::runtime_error("Unexpected EOF while reading binary STL: " + fn);
        }
        m_facets.push_back(fac);
    }
}
}