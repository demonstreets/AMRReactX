#include "eb2_factory.H"

#include <AMReX_Print.H>
#include <AMReX_REAL.H>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <limits>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

namespace {

struct STLBounds
{
    std::array<amrex::Real, 3> lo;
    std::array<amrex::Real, 3> hi;
    std::uint64_t vertices = 0;
    std::uint64_t triangles = 0;
    bool binary = false;
};

void abortWithSTLMessage(const std::string& message)
{
    amrex::Abort("buildFromSTL: " + message);
}

void updateBounds(STLBounds& bounds, amrex::Real x, amrex::Real y, amrex::Real z)
{
    const std::array<amrex::Real, 3> p{x, y, z};
    for (int d = 0; d < 3; ++d) {
        if (!std::isfinite(p[d])) {
            abortWithSTLMessage("encountered non-finite STL vertex coordinate");
        }
        bounds.lo[d] = std::min(bounds.lo[d], p[d]);
        bounds.hi[d] = std::max(bounds.hi[d], p[d]);
    }
    ++bounds.vertices;
}

bool readUInt32LE(std::ifstream& in, std::uint32_t& value)
{
    unsigned char bytes[4];
    if (!in.read(reinterpret_cast<char*>(bytes), sizeof(bytes))) {
        return false;
    }
    value = static_cast<std::uint32_t>(bytes[0]) |
            (static_cast<std::uint32_t>(bytes[1]) << 8) |
            (static_cast<std::uint32_t>(bytes[2]) << 16) |
            (static_cast<std::uint32_t>(bytes[3]) << 24);
    return true;
}

bool readFloat32LE(std::ifstream& in, float& value)
{
    unsigned char bytes[4];
    if (!in.read(reinterpret_cast<char*>(bytes), sizeof(bytes))) {
        return false;
    }
    std::uint32_t bits = static_cast<std::uint32_t>(bytes[0]) |
                         (static_cast<std::uint32_t>(bytes[1]) << 8) |
                         (static_cast<std::uint32_t>(bytes[2]) << 16) |
                         (static_cast<std::uint32_t>(bytes[3]) << 24);
    std::memcpy(&value, &bits, sizeof(value));
    return true;
}

void writeUInt16LE(std::ofstream& out, std::uint16_t value)
{
    const unsigned char bytes[2] = {
        static_cast<unsigned char>(value & 0xffU),
        static_cast<unsigned char>((value >> 8) & 0xffU)};
    out.write(reinterpret_cast<const char*>(bytes), sizeof(bytes));
}

void writeUInt32LE(std::ofstream& out, std::uint32_t value)
{
    const unsigned char bytes[4] = {
        static_cast<unsigned char>(value & 0xffU),
        static_cast<unsigned char>((value >> 8) & 0xffU),
        static_cast<unsigned char>((value >> 16) & 0xffU),
        static_cast<unsigned char>((value >> 24) & 0xffU)};
    out.write(reinterpret_cast<const char*>(bytes), sizeof(bytes));
}

void writeFloat32LE(std::ofstream& out, float value)
{
    std::uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(value));
    writeUInt32LE(out, bits);
}

struct STLTriangle
{
    std::array<std::array<amrex::Real, 3>, 3> vertex{};
};

std::vector<STLTriangle> readSTLTriangles(const std::string& stl_file);

void validateTriangleVertex(const std::array<amrex::Real, 3>& p,
                            const std::string& stl_file)
{
    for (amrex::Real value : p) {
        if (!std::isfinite(value)) {
            abortWithSTLMessage("encountered non-finite STL vertex coordinate in '" +
                                stl_file + "'");
        }
    }
}

std::array<float, 3> triangleNormal(const STLTriangle& tri,
                                    const std::string& stl_file)
{
    const auto& a = tri.vertex[0];
    const auto& b = tri.vertex[1];
    const auto& c = tri.vertex[2];
    const std::array<amrex::Real, 3> u{b[0] - a[0], b[1] - a[1], b[2] - a[2]};
    const std::array<amrex::Real, 3> v{c[0] - a[0], c[1] - a[1], c[2] - a[2]};
    const std::array<amrex::Real, 3> n{
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0]};
    const amrex::Real norm = std::sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]);
    if (!(std::isfinite(norm) && norm > 0.0)) {
        abortWithSTLMessage("encountered degenerate STL triangle in '" + stl_file + "'");
    }
    return {static_cast<float>(n[0] / norm),
            static_cast<float>(n[1] / norm),
            static_cast<float>(n[2] / norm)};
}

bool looksLikeBinarySTL(const std::string& stl_file)
{
    std::ifstream size_stream(stl_file, std::ios::binary | std::ios::ate);
    if (!size_stream) {
        abortWithSTLMessage("could not open STL file '" + stl_file + "'");
    }
    const auto file_size = size_stream.tellg();
    if (file_size < 0) {
        abortWithSTLMessage("could not determine size of STL file '" + stl_file + "'");
    }
    if (file_size < static_cast<std::streamoff>(84)) {
        return false;
    }
    size_stream.seekg(80, std::ios::beg);
    std::uint32_t triangles = 0;
    if (!readUInt32LE(size_stream, triangles)) {
        return false;
    }
    const auto expected_size = static_cast<std::streamoff>(84) +
                               static_cast<std::streamoff>(triangles) *
                               static_cast<std::streamoff>(50);
    return expected_size == file_size;
}

STLBounds emptyBounds()
{
    STLBounds bounds;
    bounds.lo = {std::numeric_limits<amrex::Real>::max(),
                 std::numeric_limits<amrex::Real>::max(),
                 std::numeric_limits<amrex::Real>::max()};
    bounds.hi = {std::numeric_limits<amrex::Real>::lowest(),
                 std::numeric_limits<amrex::Real>::lowest(),
                 std::numeric_limits<amrex::Real>::lowest()};
    return bounds;
}

STLBounds readAsciiSTLBounds(const std::string& stl_file)
{
    std::ifstream in(stl_file);
    if (!in) {
        abortWithSTLMessage("could not open STL file '" + stl_file + "'");
    }

    STLBounds bounds = emptyBounds();
    std::string token;
    while (in >> token) {
        if (token == "vertex") {
            amrex::Real x = 0.0;
            amrex::Real y = 0.0;
            amrex::Real z = 0.0;
            if (!(in >> x >> y >> z)) {
                abortWithSTLMessage("malformed ASCII STL vertex in '" + stl_file + "'");
            }
            updateBounds(bounds, x, y, z);
        }
    }
    return bounds;
}

STLBounds readBinarySTLBounds(const std::string& stl_file)
{
    std::ifstream in(stl_file, std::ios::binary);
    if (!in) {
        abortWithSTLMessage("could not open STL file '" + stl_file + "'");
    }

    char header[80];
    if (!in.read(header, sizeof(header))) {
        abortWithSTLMessage("binary STL header is incomplete in '" + stl_file + "'");
    }

    std::uint32_t triangles = 0;
    if (!readUInt32LE(in, triangles)) {
        abortWithSTLMessage("binary STL triangle count is missing in '" + stl_file + "'");
    }

    STLBounds bounds = emptyBounds();
    bounds.binary = true;
    for (std::uint32_t n = 0; n < triangles; ++n) {
        float ignored_normal[3];
        for (float& value : ignored_normal) {
            if (!readFloat32LE(in, value)) {
                abortWithSTLMessage("binary STL normal data is truncated in '" + stl_file + "'");
            }
        }
        for (int vertex = 0; vertex < 3; ++vertex) {
            float x = 0.0F;
            float y = 0.0F;
            float z = 0.0F;
            if (!readFloat32LE(in, x) || !readFloat32LE(in, y) || !readFloat32LE(in, z)) {
                abortWithSTLMessage("binary STL vertex data is truncated in '" + stl_file + "'");
            }
            updateBounds(bounds, static_cast<amrex::Real>(x),
                         static_cast<amrex::Real>(y), static_cast<amrex::Real>(z));
        }
        char attribute_count[2];
        if (!in.read(attribute_count, sizeof(attribute_count))) {
            abortWithSTLMessage("binary STL attribute data is truncated in '" + stl_file + "'");
        }
    }
    return bounds;
}

STLBounds readSTLBounds(const std::string& stl_file)
{
    STLBounds bounds = looksLikeBinarySTL(stl_file) ? readBinarySTLBounds(stl_file)
                                                    : readAsciiSTLBounds(stl_file);
    if (bounds.vertices == 0) {
        abortWithSTLMessage("STL file '" + stl_file + "' has no vertices");
    }
    bounds.triangles = static_cast<std::uint64_t>(readSTLTriangles(stl_file).size());
    return bounds;
}

std::vector<STLTriangle> readBinarySTLTriangles(const std::string& stl_file)
{
    std::ifstream in(stl_file, std::ios::binary);
    if (!in) {
        abortWithSTLMessage("could not open STL file '" + stl_file + "'");
    }
    char header[80];
    if (!in.read(header, sizeof(header))) {
        abortWithSTLMessage("binary STL header is incomplete in '" + stl_file + "'");
    }
    std::uint32_t triangles = 0;
    if (!readUInt32LE(in, triangles)) {
        abortWithSTLMessage("binary STL triangle count is missing in '" + stl_file + "'");
    }
    std::vector<STLTriangle> out;
    out.reserve(triangles);
    for (std::uint32_t n = 0; n < triangles; ++n) {
        float ignored_normal[3];
        for (float& value : ignored_normal) {
            if (!readFloat32LE(in, value)) {
                abortWithSTLMessage("binary STL normal data is truncated in '" + stl_file + "'");
            }
        }
        STLTriangle tri;
        for (int vertex = 0; vertex < 3; ++vertex) {
            float x = 0.0F;
            float y = 0.0F;
            float z = 0.0F;
            if (!readFloat32LE(in, x) || !readFloat32LE(in, y) || !readFloat32LE(in, z)) {
                abortWithSTLMessage("binary STL vertex data is truncated in '" + stl_file + "'");
            }
            tri.vertex[vertex] = {static_cast<amrex::Real>(x),
                                  static_cast<amrex::Real>(y),
                                  static_cast<amrex::Real>(z)};
            validateTriangleVertex(tri.vertex[vertex], stl_file);
        }
        char attribute_count[2];
        if (!in.read(attribute_count, sizeof(attribute_count))) {
            abortWithSTLMessage("binary STL attribute data is truncated in '" + stl_file + "'");
        }
        (void)triangleNormal(tri, stl_file);
        out.push_back(tri);
    }
    if (out.empty()) {
        abortWithSTLMessage("STL file '" + stl_file + "' has no triangles");
    }
    return out;
}

std::vector<STLTriangle> readAsciiSTLTriangles(const std::string& stl_file)
{
    std::ifstream in(stl_file);
    if (!in) {
        abortWithSTLMessage("could not open STL file '" + stl_file + "'");
    }
    std::vector<std::array<amrex::Real, 3>> vertices;
    std::string token;
    while (in >> token) {
        if (token == "vertex") {
            std::array<amrex::Real, 3> p{0.0, 0.0, 0.0};
            if (!(in >> p[0] >> p[1] >> p[2])) {
                abortWithSTLMessage("malformed ASCII STL vertex in '" + stl_file + "'");
            }
            validateTriangleVertex(p, stl_file);
            vertices.push_back(p);
        }
    }
    if (vertices.empty()) {
        abortWithSTLMessage("STL file '" + stl_file + "' has no vertices");
    }
    if (vertices.size() % 3 != 0) {
        abortWithSTLMessage("ASCII STL vertex count is not divisible by 3 in '" + stl_file + "'");
    }
    std::vector<STLTriangle> out;
    out.reserve(vertices.size() / 3);
    for (std::size_t i = 0; i < vertices.size(); i += 3) {
        STLTriangle tri;
        tri.vertex[0] = vertices[i];
        tri.vertex[1] = vertices[i + 1];
        tri.vertex[2] = vertices[i + 2];
        (void)triangleNormal(tri, stl_file);
        out.push_back(tri);
    }
    return out;
}

std::vector<STLTriangle> readSTLTriangles(const std::string& stl_file)
{
    return looksLikeBinarySTL(stl_file) ? readBinarySTLTriangles(stl_file)
                                        : readAsciiSTLTriangles(stl_file);
}

void writeMergedBinarySTL(
    const std::vector<std::string>& stl_files,
    const std::string& merged_stl_file,
    const std::vector<amrex::Real>& stl_scales,
    const std::vector<amrex::Array<amrex::Real,3>>& stl_centers)
{
    if (stl_files.empty()) {
        abortWithSTLMessage("no STL files were provided for merge");
    }

    const bool use_per_file_transforms = !stl_scales.empty() || !stl_centers.empty();
    if (use_per_file_transforms &&
        (stl_scales.size() != stl_files.size() || stl_centers.size() != stl_files.size())) {
        abortWithSTLMessage("per-file STL transforms must match prob.obstacle_stl_files count");
    }

    std::vector<STLTriangle> triangles;
    for (std::size_t file_index = 0; file_index < stl_files.size(); ++file_index) {
        const auto& stl_file = stl_files[file_index];
        if (stl_file == merged_stl_file) {
            abortWithSTLMessage("merged STL output must not overwrite input file '" +
                                stl_file + "'");
        }
        auto file_triangles = readSTLTriangles(stl_file);
        if (use_per_file_transforms) {
            const amrex::Real scale = stl_scales[file_index];
            if (!(std::isfinite(scale) && scale > 0.0)) {
                abortWithSTLMessage("per-file STL scale must be finite and positive for '" +
                                    stl_file + "'");
            }
            for (int d = 0; d < 3; ++d) {
                if (!std::isfinite(stl_centers[file_index][d])) {
                    abortWithSTLMessage("per-file STL center must contain only finite values for '" +
                                        stl_file + "'");
                }
            }
            for (auto& tri : file_triangles) {
                for (auto& vertex : tri.vertex) {
                    for (int d = 0; d < 3; ++d) {
                        vertex[d] = scale * vertex[d] + stl_centers[file_index][d];
                    }
                }
                (void)triangleNormal(tri, stl_file);
            }
        }
        triangles.insert(triangles.end(), file_triangles.begin(), file_triangles.end());
    }
    if (triangles.size() > std::numeric_limits<std::uint32_t>::max()) {
        abortWithSTLMessage("merged STL triangle count exceeds binary STL uint32 limit");
    }

    std::ofstream out(merged_stl_file, std::ios::binary | std::ios::trunc);
    if (!out) {
        abortWithSTLMessage("could not create merged STL file '" + merged_stl_file + "'");
    }
    char header[80] = {};
    const std::string label = "Pele merged binary STL obstacles";
    std::memcpy(header, label.data(), std::min(label.size(), sizeof(header)));
    out.write(header, sizeof(header));
    writeUInt32LE(out, static_cast<std::uint32_t>(triangles.size()));
    for (const auto& tri : triangles) {
        const auto normal = triangleNormal(tri, merged_stl_file);
        for (float value : normal) {
            writeFloat32LE(out, value);
        }
        for (const auto& vertex : tri.vertex) {
            for (amrex::Real value : vertex) {
                writeFloat32LE(out, static_cast<float>(value));
            }
        }
        writeUInt16LE(out, 0);
    }
    if (!out) {
        abortWithSTLMessage("failed while writing merged STL file '" + merged_stl_file + "'");
    }
}

} // namespace

namespace pele {

void buildFromSTL(const std::string& stl_file,
                  const amrex::Geometry& geom,
                  int max_coarsening_level,
                  amrex::Real stl_scale,
                  const amrex::Array<amrex::Real,3>& stl_center,
                  int stl_reverse_normal,
                  int required_coarsening_level,
                  int ngrow,
                  bool build_coarse_level_by_coarsening,
                  bool extend_domain_face,
                  int num_coarsen_opt,
                  bool bvh_optimization,
                  bool support_mvmc)
{
    if (!(std::isfinite(stl_scale) && stl_scale > 0.0)) {
        abortWithSTLMessage("stl_scale must be finite and positive");
    }
    if (ngrow < 0) {
        abortWithSTLMessage("ngrow must be non-negative");
    }
    for (int d = 0; d < 3; ++d) {
        if (!std::isfinite(stl_center[d])) {
            abortWithSTLMessage("stl_center must contain only finite values");
        }
    }

    const STLBounds raw_bounds = readSTLBounds(stl_file);
    std::array<amrex::Real, 3> scaled_lo{};
    std::array<amrex::Real, 3> scaled_hi{};
    for (int d = 0; d < 3; ++d) {
        scaled_lo[d] = stl_scale * raw_bounds.lo[d] + stl_center[d];
        scaled_hi[d] = stl_scale * raw_bounds.hi[d] + stl_center[d];
    }

    const amrex::Real* prob_lo = geom.ProbLo();
    const amrex::Real* prob_hi = geom.ProbHi();
    std::array<amrex::Real, 3> domain_lo{0.0, 0.0, 0.0};
    std::array<amrex::Real, 3> domain_hi{0.0, 0.0, 0.0};
    bool intersects_domain = true;
    for (int d = 0; d < 3; ++d) {
        if (d < AMREX_SPACEDIM) {
            domain_lo[d] = prob_lo[d];
            domain_hi[d] = prob_hi[d];
            if (scaled_hi[d] < domain_lo[d] || scaled_lo[d] > domain_hi[d]) {
                intersects_domain = false;
            }
        } else {
            domain_lo[d] = scaled_lo[d];
            domain_hi[d] = scaled_hi[d];
        }
    }
    if (!intersects_domain) {
        std::ostringstream message;
        message << "scaled STL bounds do not intersect the computational domain: "
                << "bounds=[(" << scaled_lo[0] << "," << scaled_lo[1] << "," << scaled_lo[2]
                << "),(" << scaled_hi[0] << "," << scaled_hi[1] << "," << scaled_hi[2]
                << ")] domain=[(" << domain_lo[0] << "," << domain_lo[1] << "," << domain_lo[2]
                << "),(" << domain_hi[0] << "," << domain_hi[1] << "," << domain_hi[2] << ")]";
        abortWithSTLMessage(message.str());
    }

    amrex::Print() << "buildFromSTL QA: file=" << stl_file
                   << ", format=" << (raw_bounds.binary ? "binary" : "ascii")
                   << ", vertices=" << raw_bounds.vertices
                   << ", triangles=" << raw_bounds.triangles
                   << ", raw_bounds=([" << raw_bounds.lo[0] << "," << raw_bounds.lo[1]
                   << "," << raw_bounds.lo[2] << "],[" << raw_bounds.hi[0] << ","
                   << raw_bounds.hi[1] << "," << raw_bounds.hi[2] << "])"
                   << ", scaled_bounds=([" << scaled_lo[0] << "," << scaled_lo[1]
                   << "," << scaled_lo[2] << "],[" << scaled_hi[0] << ","
                   << scaled_hi[1] << "," << scaled_hi[2] << "])"
                   << std::endl;

    auto index_space = std::make_unique<amrex::EB2::IndexSpaceSTL>(
        stl_file, stl_scale, stl_center, stl_reverse_normal, geom,
        required_coarsening_level, max_coarsening_level, ngrow,
        build_coarse_level_by_coarsening, extend_domain_face, num_coarsen_opt,
        bvh_optimization, support_mvmc);

    amrex::EB2::IndexSpace::push(std::move(index_space));
    amrex::Print() << "buildFromSTL: built AMReX EB2 IndexSpace from "
                   << stl_file << std::endl;
}

void buildFromSTLFiles(const std::vector<std::string>& stl_files,
                       const std::string& merged_stl_file,
                       const amrex::Geometry& geom,
                       int max_coarsening_level,
                       amrex::Real stl_scale,
                       const amrex::Array<amrex::Real,3>& stl_center,
                       int stl_reverse_normal,
                       int required_coarsening_level,
                       int ngrow,
                       bool build_coarse_level_by_coarsening,
                       bool extend_domain_face,
                       int num_coarsen_opt,
                       bool bvh_optimization,
                       bool support_mvmc)
{
    if (stl_files.empty()) {
        abortWithSTLMessage("prob.obstacle_stl_files must contain at least one STL file");
    }
    if (stl_files.size() == 1) {
        buildFromSTL(stl_files.front(), geom, max_coarsening_level, stl_scale, stl_center,
                     stl_reverse_normal, required_coarsening_level, ngrow,
                     build_coarse_level_by_coarsening, extend_domain_face,
                     num_coarsen_opt, bvh_optimization, support_mvmc);
        return;
    }

    amrex::Print() << "buildFromSTLFiles: merging " << stl_files.size()
                   << " STL files into " << merged_stl_file << std::endl;
    for (std::size_t i = 0; i < stl_files.size(); ++i) {
        amrex::Print() << "  stl_file[" << i << "]=" << stl_files[i] << std::endl;
    }
    writeMergedBinarySTL(stl_files, merged_stl_file,
                         std::vector<amrex::Real>{},
                         std::vector<amrex::Array<amrex::Real,3>>{});
    buildFromSTL(merged_stl_file, geom, max_coarsening_level, stl_scale, stl_center,
                 stl_reverse_normal, required_coarsening_level, ngrow,
                 build_coarse_level_by_coarsening, extend_domain_face,
                 num_coarsen_opt, bvh_optimization, support_mvmc);
}

void buildFromSTLFilesWithTransforms(
                       const std::vector<std::string>& stl_files,
                       const std::string& merged_stl_file,
                       const amrex::Geometry& geom,
                       int max_coarsening_level,
                       const std::vector<amrex::Real>& stl_scales,
                       const std::vector<amrex::Array<amrex::Real,3>>& stl_centers,
                       int stl_reverse_normal,
                       int required_coarsening_level,
                       int ngrow,
                       bool build_coarse_level_by_coarsening,
                       bool extend_domain_face,
                       int num_coarsen_opt,
                       bool bvh_optimization,
                       bool support_mvmc)
{
    if (stl_files.empty()) {
        abortWithSTLMessage("prob.obstacle_stl_files must contain at least one STL file");
    }
    if (stl_scales.size() != stl_files.size() || stl_centers.size() != stl_files.size()) {
        abortWithSTLMessage("per-file STL transforms must match prob.obstacle_stl_files count");
    }
    if (stl_files.size() == 1) {
        buildFromSTL(stl_files.front(), geom, max_coarsening_level, stl_scales.front(),
                     stl_centers.front(), stl_reverse_normal, required_coarsening_level, ngrow,
                     build_coarse_level_by_coarsening, extend_domain_face,
                     num_coarsen_opt, bvh_optimization, support_mvmc);
        return;
    }

    amrex::Print() << "buildFromSTLFilesWithTransforms: merging " << stl_files.size()
                   << " STL files into " << merged_stl_file << std::endl;
    for (std::size_t i = 0; i < stl_files.size(); ++i) {
        amrex::Print() << "  stl_file[" << i << "]=" << stl_files[i]
                       << ", scale=" << stl_scales[i]
                       << ", center=(" << stl_centers[i][0] << ","
                       << stl_centers[i][1] << "," << stl_centers[i][2] << ")"
                       << std::endl;
    }
    writeMergedBinarySTL(stl_files, merged_stl_file, stl_scales, stl_centers);
    buildFromSTL(merged_stl_file, geom, max_coarsening_level, 1.0,
                 amrex::Array<amrex::Real,3>{0.0, 0.0, 0.0},
                 stl_reverse_normal, required_coarsening_level, ngrow,
                 build_coarse_level_by_coarsening, extend_domain_face,
                 num_coarsen_opt, bvh_optimization, support_mvmc);
}

} // namespace pele
