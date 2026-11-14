#include "bc_tags.H"
#include "domain_builder.H"
#include "signed_distance.H"
#include "stl_parser.H"

#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

int g_failed = 0;

void check(const std::string& name, bool ok, const std::string& detail = "")
{
    std::cout << (ok ? "[PASS] " : "[FAIL] ") << name;
    if (!detail.empty()) std::cout << " (" << detail << ")";
    std::cout << '\n';
    if (!ok) ++g_failed;
}

bool near(double a, double b, double tol = 1.0e-12)
{
    return std::abs(a - b) <= tol;
}

void write_ascii_stl(const std::filesystem::path& path)
{
    std::ofstream f(path);
    f << "solid square\n"
      << "  facet normal 0 0 1\n"
      << "    outer loop\n"
      << "      vertex 0 0 0\n"
      << "      vertex 1 0 0\n"
      << "      vertex 0 1 0\n"
      << "    endloop\n"
      << "  endfacet\n"
      << "  facet normal 0 0 1\n"
      << "    outer loop\n"
      << "      vertex 1 0 0\n"
      << "      vertex 1 1 0\n"
      << "      vertex 0 1 0\n"
      << "    endloop\n"
      << "  endfacet\n"
      << "endsolid square\n";
}

void append_f32(std::ofstream& f, float value)
{
    f.write(reinterpret_cast<const char*>(&value), sizeof(float));
}

void append_u16(std::ofstream& f, std::uint16_t value)
{
    f.write(reinterpret_cast<const char*>(&value), sizeof(std::uint16_t));
}

void write_binary_stl(const std::filesystem::path& path, const std::string& prefix)
{
    std::ofstream f(path, std::ios::binary);
    std::array<char, 80> header{};
    std::memcpy(header.data(), prefix.data(), std::min(prefix.size(), header.size()));
    f.write(header.data(), header.size());
    const std::uint32_t nfacets = 2;
    f.write(reinterpret_cast<const char*>(&nfacets), sizeof(nfacets));

    const float facets[2][12] = {
        {0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f},
        {0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 0.0f, 1.0f, 0.0f},
    };
    for (const auto& facet : facets) {
        for (float value : facet) append_f32(f, value);
        append_u16(f, 0);
    }
}

void write_step_stub(const std::filesystem::path& path)
{
    std::ofstream f(path);
    f << "ISO-10303-21;\n"
      << "HEADER;\n"
      << "FILE_DESCRIPTION(('codex unsupported STEP smoke'), '2;1');\n"
      << "ENDSEC;\n"
      << "DATA;\n"
      << "ENDSEC;\n"
      << "END-ISO-10303-21;\n";
}

void write_empty_ascii_stl(const std::filesystem::path& path)
{
    std::ofstream f(path);
    f << "solid empty\nendsolid empty\n";
}

void write_unknown_geometry(const std::filesystem::path& path)
{
    std::ofstream f(path);
    f << "this is not a supported geometry format\n";
}

bool read_throws_with(pele::STLReader& reader,
                      const std::filesystem::path& path,
                      const std::string& expected)
{
    try {
        reader.read(path.string());
    } catch (const std::runtime_error& e) {
        return std::string(e.what()).find(expected) != std::string::npos;
    }
    return false;
}

void test_stl_reader(const std::filesystem::path& tmp)
{
    const auto ascii = tmp / "square_ascii.stl";
    const auto binary = tmp / "square_binary.stl";
    const auto binary_solid = tmp / "square_binary_solid_header.stl";
    const auto truncated = tmp / "truncated_binary.stl";
    const auto step = tmp / "box.step";
    const auto empty_ascii = tmp / "empty_ascii.stl";
    const auto unknown = tmp / "geometry.txt";
    write_ascii_stl(ascii);
    write_binary_stl(binary, "codex binary square");
    write_binary_stl(binary_solid, "solid binary square");
    write_step_stub(step);
    write_empty_ascii_stl(empty_ascii);
    write_unknown_geometry(unknown);
    {
        std::ofstream f(truncated, std::ios::binary);
        std::array<char, 80> header{};
        f.write(header.data(), header.size());
        const std::uint32_t nfacets = 1;
        f.write(reinterpret_cast<const char*>(&nfacets), sizeof(nfacets));
        append_f32(f, 0.0f);
    }

    pele::STLReader reader;
    reader.read(ascii.string());
    check("ASCII STL facet count", reader.numFacets() == 2);
    check("ASCII STL vertex parse", near(reader.getFacets()[1].vertices[1][0], 1.0)
                                  && near(reader.getFacets()[1].vertices[1][1], 1.0));

    reader.read(binary.string());
    check("read() clears previous facets", reader.numFacets() == 2);
    check("binary STL facet count", reader.numFacets() == 2);
    check("binary STL normal parse", near(reader.getFacets()[0].normal[2], 1.0));

    reader.read(binary_solid.string());
    check("binary STL with solid-prefixed header", reader.numFacets() == 2);

    bool threw = false;
    try {
        reader.read(truncated.string());
    } catch (const std::runtime_error&) {
        threw = true;
    }
    check("truncated binary STL rejected", threw);
    check("STEP geometry explicitly requires conversion",
          read_throws_with(reader, step, "STEP geometry requires offline conversion to STL"));
    check("empty ASCII STL rejected",
          read_throws_with(reader, empty_ascii, "STL contains no facets"));
    check("unknown geometry rejected",
          read_throws_with(reader, unknown, "Unsupported geometry format"));
}

void test_sdf()
{
    check("sphere SDF outside", near(pele::sdf_sphere(2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0), 1.0));
    check("sphere SDF surface", near(pele::sdf_sphere(1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0), 0.0));
    check("sphere SDF inside", near(pele::sdf_sphere(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0), -1.0));

    pele::STLFacet facet{};
    facet.normal[2] = 1.0;
    facet.vertices[0][0] = 0.0; facet.vertices[0][1] = 0.0; facet.vertices[0][2] = 0.0;
    facet.vertices[1][0] = 1.0; facet.vertices[1][1] = 0.0; facet.vertices[1][2] = 0.0;
    facet.vertices[2][0] = 0.0; facet.vertices[2][1] = 1.0; facet.vertices[2][2] = 0.0;

    pele::SDFComputer sdf;
    sdf.setFacets({facet});
    check("triangle SDF normal-positive side", near(sdf.computePoint(0.25, 0.25, 0.5), 0.5));
    check("triangle SDF normal-negative side", near(sdf.computePoint(0.25, 0.25, -0.5), -0.5));
}

void test_boundary_tags()
{
    check("BC wall token", pele::parseBoundaryType("wall") == pele::BoundaryType::WALL);
    check("BC no-slip alias", pele::parseBoundaryType("no-slip") == pele::BoundaryType::WALL);
    check("BC inlet token", pele::parseBoundaryType("Inlet") == pele::BoundaryType::INLET);
    check("BC outlet alias", pele::parseBoundaryType("out_flow") == pele::BoundaryType::OUTLET);
    check("BC symmetry alias", pele::parseBoundaryType("sym") == pele::BoundaryType::SYMMETRY);
    check("BC unknown token", pele::parseBoundaryType("periodic") == pele::BoundaryType::UNKNOWN);
    check("BC slip wall distinct from no-slip wall",
          pele::parseBoundaryType("slip_wall") == pele::BoundaryType::SLIP_WALL);
    check("BC canonical name", pele::boundaryTypeName(pele::BoundaryType::SYMMETRY) == "symmetry");
    check("BC slip wall canonical name",
          pele::boundaryTypeName(pele::BoundaryType::SLIP_WALL) == "slip_wall");
}

void test_domain_builder()
{
    pele::STLFacet f0{};
    f0.vertices[0][0] = 1.0; f0.vertices[0][1] = -2.0; f0.vertices[0][2] = 0.5;
    f0.vertices[1][0] = 3.0; f0.vertices[1][1] = -2.0; f0.vertices[1][2] = 0.5;
    f0.vertices[2][0] = 1.0; f0.vertices[2][1] =  2.0; f0.vertices[2][2] = 1.5;

    pele::STLFacet f1{};
    f1.vertices[0][0] = 3.0; f1.vertices[0][1] = -2.0; f1.vertices[0][2] = 0.5;
    f1.vertices[1][0] = 3.0; f1.vertices[1][1] =  2.0; f1.vertices[1][2] = 1.5;
    f1.vertices[2][0] = 1.0; f1.vertices[2][1] =  2.0; f1.vertices[2][2] = 1.5;

    const std::vector<pele::STLFacet> facets{f0, f1};
    const auto bounds = pele::computeFacetBounds(facets);
    check("geometry bounds valid", bounds.valid);
    check("geometry bounds lo", near(bounds.lo[0], 1.0) && near(bounds.lo[1], -2.0) && near(bounds.lo[2], 0.5));
    check("geometry bounds hi", near(bounds.hi[0], 3.0) && near(bounds.hi[1], 2.0) && near(bounds.hi[2], 1.5));

    const auto padded = pele::padBounds(bounds, 0.1, 0.0);
    check("padded domain lo", near(padded.lo[0], 0.8) && near(padded.lo[1], -2.4) && near(padded.lo[2], 0.4));
    check("padded domain hi", near(padded.hi[0], 3.2) && near(padded.hi[1], 2.4) && near(padded.hi[2], 1.6));

    const auto domain = pele::makeMeshDomain(padded, 0.25, 8);
    check("mesh domain carries prob_lo", near(domain.prob_lo[0], 0.8) && near(domain.prob_lo[1], -2.4));
    check("mesh domain carries prob_hi", near(domain.prob_hi[0], 3.2) && near(domain.prob_hi[2], 1.6));
    check("mesh cells rounded to blocking factor", domain.n_cell[0] == 16 && domain.n_cell[1] == 24 && domain.n_cell[2] == 8);

    pele::STLFacet flat{};
    flat.vertices[0][0] = 0.0; flat.vertices[0][1] = 0.0; flat.vertices[0][2] = 0.0;
    flat.vertices[1][0] = 1.0; flat.vertices[1][1] = 0.0; flat.vertices[1][2] = 0.0;
    flat.vertices[2][0] = 0.0; flat.vertices[2][1] = 1.0; flat.vertices[2][2] = 0.0;
    const auto flat_domain = pele::makeMeshDomainFromFacets({flat}, 0.1, 0.0, 0.05, 4);
    check("degenerate geometry gets minimum z padding", near(flat_domain.prob_lo[2], -0.05) && near(flat_domain.prob_hi[2], 0.05));
    check("degenerate geometry gets positive z cells", flat_domain.n_cell[2] == 4);

    bool threw = false;
    try {
        (void)pele::makeMeshDomainFromFacets({}, 0.1);
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    check("empty geometry rejected for mesh domain", threw);
}

} // namespace

int main()
{
    const auto tmp = std::filesystem::temp_directory_path() / "codex_geometry_pipeline_smoke";
    std::filesystem::remove_all(tmp);
    std::filesystem::create_directories(tmp);

    test_stl_reader(tmp);
    test_sdf();
    test_boundary_tags();
    test_domain_builder();

    std::filesystem::remove_all(tmp);
    return g_failed == 0 ? 0 : 1;
}
