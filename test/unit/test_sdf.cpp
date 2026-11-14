#include <signed_distance.H>
#include <stl_parser.H>

#include <AMReX.H>
#include <AMReX_Print.H>

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <vector>

using namespace amrex;

namespace {

// -----------------------------------------------------------------------
// Write a binary STL file for a unit sphere approximated with an icosahedron.
// We subdivide once to get 80 triangles — enough for a basic test.
// -----------------------------------------------------------------------
struct Vec3 {
    double x, y, z;
};

Vec3 normalize(Vec3 v) {
    double len = std::sqrt(v.x*v.x + v.y*v.y + v.z*v.z);
    return {v.x/len, v.y/len, v.z/len};
}

void writeSphereSTL(const std::string& path, double radius, int subdivisions)
{
    // Start with icosahedron vertices (normalized)
    const double t = (1.0 + std::sqrt(5.0)) / 2.0;

    std::vector<Vec3> verts = {
        {-1,  t,  0}, { 1,  t,  0}, {-1, -t,  0}, { 1, -t,  0},
        { 0, -1,  t}, { 0,  1,  t}, { 0, -1, -t}, { 0,  1, -t},
        { t,  0, -1}, { t,  0,  1}, {-t,  0, -1}, {-t,  0,  1}
    };
    for (auto& v : verts) v = normalize(v);

    // Icosahedron triangles (20)
    std::vector<std::array<int,3>> tris = {
        {0, 11, 5}, {0, 5, 1}, {0, 1, 7}, {0, 7, 10}, {0, 10, 11},
        {1, 5, 9}, {5, 11, 4}, {11, 10, 2}, {10, 7, 6}, {7, 1, 8},
        {3, 9, 4}, {3, 4, 2}, {3, 2, 6}, {3, 6, 8}, {3, 8, 9},
        {4, 9, 5}, {2, 4, 11}, {6, 2, 10}, {8, 6, 7}, {9, 8, 1}
    };

    // Subdivide
    for (int s = 0; s < subdivisions; ++s) {
        std::vector<Vec3> new_verts = verts;
        std::vector<std::array<int,3>> new_tris;
        for (const auto& tri : tris) {
            Vec3 a = verts[tri[0]], b = verts[tri[1]], c = verts[tri[2]];
            Vec3 ab = normalize({(a.x+b.x)/2, (a.y+b.y)/2, (a.z+b.z)/2});
            Vec3 ac = normalize({(a.x+c.x)/2, (a.y+c.y)/2, (a.z+c.z)/2});
            Vec3 bc = normalize({(b.x+c.x)/2, (b.y+c.y)/2, (b.z+c.z)/2});
            int ia = tri[0], ib = tri[1], ic = tri[2];
            int iab = new_verts.size(); new_verts.push_back(ab);
            int iac = new_verts.size(); new_verts.push_back(ac);
            int ibc = new_verts.size(); new_verts.push_back(bc);
            new_tris.push_back({ia, iab, iac});
            new_tris.push_back({ib, ibc, iab});
            new_tris.push_back({ic, iac, ibc});
            new_tris.push_back({iab, ibc, iac});
        }
        verts = new_verts;
        tris = new_tris;
    }

    // Scale by radius
    for (auto& v : verts) {
        v.x *= radius; v.y *= radius; v.z *= radius;
    }

    // Write binary STL
    std::ofstream f(path, std::ios::binary);
    char header[80] = {};
    std::snprintf(header, 80, "Sphere STL radius=%f subdiv=%d", radius, subdivisions);
    f.write(header, 80);

    uint32_t ntri = static_cast<uint32_t>(tris.size());
    f.write(reinterpret_cast<const char*>(&ntri), 4);

    for (const auto& tri : tris) {
        const Vec3& a = verts[tri[0]];
        const Vec3& b = verts[tri[1]];
        const Vec3& c = verts[tri[2]];

        // Normal
        Vec3 ab = {b.x-a.x, b.y-a.y, b.z-a.z};
        Vec3 ac = {c.x-a.x, c.y-a.y, c.z-a.z};
        Vec3 n = {
            ab.y*ac.z - ab.z*ac.y,
            ab.z*ac.x - ab.x*ac.z,
            ab.x*ac.y - ab.y*ac.x
        };
        n = normalize(n);

        float fn[3] = {static_cast<float>(n.x),
                       static_cast<float>(n.y),
                       static_cast<float>(n.z)};
        f.write(reinterpret_cast<const char*>(fn), 12);

        float fv[9] = {
            static_cast<float>(a.x), static_cast<float>(a.y), static_cast<float>(a.z),
            static_cast<float>(b.x), static_cast<float>(b.y), static_cast<float>(b.z),
            static_cast<float>(c.x), static_cast<float>(c.y), static_cast<float>(c.z)
        };
        f.write(reinterpret_cast<const char*>(fv), 36);

        uint16_t attr = 0;
        f.write(reinterpret_cast<const char*>(&attr), 2);
    }
}

// -----------------------------------------------------------------------
static int check(bool condition, const std::string& msg)
{
    if (!condition) {
        amrex::Print() << "  FAIL: " << msg << "\n";
        return 1;
    }
    amrex::Print() << "  PASS: " << msg << "\n";
    return 0;
}

} // anonymous namespace

int main(int argc, char* argv[])
{
    amrex::Initialize(argc, argv);
    int nfail = 0;

    // ------------------------------------------------------------------
    // Test 1: Analytic sdf_sphere
    // ------------------------------------------------------------------
    {
        amrex::Print() << "\n--- Test 1: Analytic sdf_sphere ---\n";
        double cx = 0.0, cy = 0.0, cz = 0.0, r = 1.0;

        // Point at centre
        double d = pele::sdf_sphere(0.0, 0.0, 0.0, cx, cy, cz, r);
        nfail += check(std::abs(d + 1.0) < 1e-14, "centre: sdf = -r");

        // Point on surface
        d = pele::sdf_sphere(1.0, 0.0, 0.0, cx, cy, cz, r);
        nfail += check(std::abs(d) < 1e-14, "surface: sdf = 0");

        // Point outside
        d = pele::sdf_sphere(2.0, 0.0, 0.0, cx, cy, cz, r);
        nfail += check(std::abs(d - 1.0) < 1e-14, "outside: sdf = +1");

        // Arbitrary point
        d = pele::sdf_sphere(0.5, 0.5, 0.5, cx, cy, cz, r);
        double expected = std::sqrt(0.75) - 1.0;
        nfail += check(std::abs(d - expected) < 1e-14, "arbitrary point matches");
    }

    // ------------------------------------------------------------------
    // Test 2: SDFComputer on a sphere STL
    // ------------------------------------------------------------------
    {
        amrex::Print() << "\n--- Test 2: SDFComputer with sphere STL ---\n";

        const double radius = 1.0;
        const std::string stl_path = "test/unit/sphere_test.stl";

        // Write a sphere STL (one subdivision = 80 triangles)
        writeSphereSTL(stl_path, radius, 1);
        amrex::Print() << "  Wrote sphere STL to " << stl_path << "\n";

        // Read the STL
        pele::STLReader reader;
        reader.read(stl_path);
        amrex::Print() << "  Facets: " << reader.numFacets() << "\n";

        pele::SDFComputer sdf(reader.getFacets());

        // Sweep a 10x10x10 grid over [-2, 2]^3 and compare with analytic
        const int npts = 10;
        double lo = -2.0, hi = 2.0;
        double cx = 0.0, cy = 0.0, cz = 0.0;
        int total = 0, good = 0;

        for (int i = 0; i < npts; ++i) {
            double x = lo + (hi - lo) * i / (npts - 1);
            for (int j = 0; j < npts; ++j) {
                double y = lo + (hi - lo) * j / (npts - 1);
                for (int k = 0; k < npts; ++k) {
                    double z = lo + (hi - lo) * k / (npts - 1);

                    double sdf_mesh = sdf.computePoint(x, y, z);
                    double sdf_analytic = pele::sdf_sphere(x, y, z, cx, cy, cz, radius);

                    // Allow tolerance. The icosphere with 1 subdivision is only
                    // an approximation of a sphere, so the mesh SDF will deviate
                    // near the surface. Use a loose tolerance for the coarse mesh.
                    constexpr double tol = 0.15;
                    double err = std::abs(sdf_mesh - sdf_analytic);
                    if (err > tol) {
                        amrex::Print() << "  Mismatch at (" << x << "," << y << "," << z
                                       << "): mesh=" << sdf_mesh
                                       << " analytic=" << sdf_analytic
                                       << " err=" << err << "\n";
                    } else {
                        ++good;
                    }
                    ++total;
                }
            }
        }

        double pct = 100.0 * good / total;
        amrex::Print() << "  " << good << "/" << total << " points within tol ("
                       << pct << "%)\n";
        nfail += check(good >= total * 0.9,
                       ">= 90% of grid points within tolerance");
    }

    amrex::Print() << "\n=== " << (nfail ? "FAILED" : "ALL PASSED") << " ===\n";
    amrex::Finalize();
    return nfail ? 1 : 0;
}
