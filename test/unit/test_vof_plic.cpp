#include "vof_modules.H"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

using MyPele::Academic::VOF::PLICFaceUpdate;
using MyPele::Academic::VOF::PLICLine2D;
using MyPele::Academic::VOF::Vec2;
using MyPele::Academic::VOF::plic_apply_x_face_update;
using MyPele::Academic::VOF::plic_apply_y_face_update;
using MyPele::Academic::VOF::plic_area_fraction;
using MyPele::Academic::VOF::plic_box_area_fraction;
using MyPele::Academic::VOF::plic_periodic_x_update_2d;
using MyPele::Academic::VOF::plic_periodic_y_update_2d;
using MyPele::Academic::VOF::plic_swept_area_x;
using MyPele::Academic::VOF::plic_swept_area_y;
using MyPele::Academic::VOF::reconstruct_plic_2d;
using MyPele::Academic::VOF::unit_square_area_less_equal;

namespace {

int n_pass = 0;
int n_fail = 0;

void require(bool condition, const std::string& message)
{
    if (!condition) {
        std::cerr << "FAIL: " << message << "\n";
        ++n_fail;
        std::exit(1);
    }
}

void require_near(double value, double expected, double tolerance,
                  const std::string& message)
{
    if (std::abs(value - expected) > tolerance) {
        std::cerr << "FAIL: " << message << ": got " << value
                  << ", expected " << expected << " +/- " << tolerance << "\n";
        ++n_fail;
        std::exit(1);
    }
}

void pass(const std::string& name)
{
    std::cout << "  TEST: " << name << " ... PASS\n";
    ++n_pass;
}

void test_axis_aligned_exact_cases()
{
    PLICLine2D line = reconstruct_plic_2d({1.0, 0.0}, 0.25);
    require_near(line.constant, 0.25, 1.0e-14, "x-normal alpha=0.25 constant");
    require_near(plic_area_fraction(line), 0.25, 1.0e-14, "x-normal alpha=0.25 area");

    line = reconstruct_plic_2d({0.0, 1.0}, 0.75);
    require_near(line.constant, 0.75, 1.0e-14, "y-normal alpha=0.75 constant");
    require_near(plic_area_fraction(line), 0.75, 1.0e-14, "y-normal alpha=0.75 area");
    pass("axis-aligned exact PLIC reconstruction");
}

void test_diagonal_half_cell()
{
    const PLICLine2D line = reconstruct_plic_2d({1.0, 1.0}, 0.5);
    require_near(line.constant, std::sqrt(0.5), 1.0e-13,
                 "diagonal half-cell normalized constant");
    require_near(plic_area_fraction(line), 0.5, 1.0e-13,
                 "diagonal half-cell area fraction");
    pass("diagonal half-cell PLIC reconstruction");
}

void test_round_trip_for_mixed_normals()
{
    const Vec2 normals[] = {{1.0, 2.0}, {-1.5, 0.75}, {0.25, -1.0}, {-2.0, -1.0}};
    const double fractions[] = {0.05, 0.2, 0.5, 0.8, 0.95};
    for (const Vec2 normal : normals) {
        for (const double fraction : fractions) {
            const PLICLine2D line = reconstruct_plic_2d(normal, fraction);
            require_near(plic_area_fraction(line), fraction, 2.0e-13,
                         "PLIC area round-trip for mixed normal");
        }
    }
    pass("mixed-normal area fraction round-trip");
}

void test_bounds_and_monotonicity()
{
    const Vec2 normal{1.25, -0.5};
    const PLICLine2D empty = reconstruct_plic_2d(normal, -1.0);
    const PLICLine2D full = reconstruct_plic_2d(normal, 2.0);
    require_near(plic_area_fraction(empty), 0.0, 1.0e-14, "empty clamp area");
    require_near(plic_area_fraction(full), 1.0, 1.0e-14, "full clamp area");

    double previous = unit_square_area_less_equal(normal, -10.0);
    for (int i = 0; i <= 32; ++i) {
        const double constant = -1.0 + i * (3.0 / 32.0);
        const double area = unit_square_area_less_equal(normal, constant);
        require(area + 1.0e-14 >= previous, "PLIC clipped area is monotone in plane constant");
        previous = area;
    }
    pass("bounds and monotone area response");
}

void test_geometric_swept_area_fluxes()
{
    const PLICLine2D full = reconstruct_plic_2d({1.0, 0.0}, 1.0);
    const PLICLine2D empty = reconstruct_plic_2d({1.0, 0.0}, 0.0);
    require_near(plic_swept_area_x(full, 0.25), 0.25, 1.0e-14,
                 "full cell positive-x swept area equals CFL width");
    require_near(plic_swept_area_y(full, -0.40), 0.40, 1.0e-14,
                 "full cell negative-y swept area equals CFL width");
    require_near(plic_swept_area_x(empty, 0.25), 0.0, 1.0e-14,
                 "empty cell has no swept area");

    const PLICLine2D left_half = reconstruct_plic_2d({1.0, 0.0}, 0.5);
    require_near(plic_swept_area_x(left_half, 0.25), 0.0, 1.0e-14,
                 "left half-cell has no liquid at the right outflow face");
    require_near(plic_swept_area_x(left_half, -0.25), 0.25, 1.0e-14,
                 "left half-cell negative-x swept area clips to the liquid slab");

    const PLICLine2D right_fraction = reconstruct_plic_2d({-1.0, 0.0}, 0.35);
    require_near(plic_swept_area_x(right_fraction, 0.20), 0.20, 1.0e-14,
                 "right-side liquid exports one positive-x CFL slab");
    require_near(plic_area_fraction(right_fraction) - plic_swept_area_x(right_fraction, 0.20),
                 0.15, 1.0e-14,
                 "positive-x swept area leaves the correct donor-cell remainder");

    const PLICLine2D diagonal = reconstruct_plic_2d({1.0, 1.0}, 0.5);
    require_near(plic_swept_area_x(diagonal, 0.25), 0.03125, 1.0e-13,
                 "diagonal half-cell positive-x swept triangular area");
    require_near(plic_swept_area_y(diagonal, 0.25), 0.03125, 1.0e-13,
                 "diagonal half-cell positive-y swept triangular area");
    require_near(plic_box_area_fraction(diagonal, 0.0, 0.25, 0.0, 1.0),
                 0.21875, 1.0e-13,
                 "diagonal half-cell left slab area");
    pass("geometric PLIC swept-area fluxes");
}

std::vector<double> plic_periodic_x_update(const std::vector<double>& alpha, const double cfl)
{
    const int n = static_cast<int>(alpha.size());
    std::vector<double> next(alpha.begin(), alpha.end());
    std::vector<double> flux(n, 0.0);
    for (int face = 0; face < n; ++face) {
        const int left = face;
        const int right = (face + 1) % n;
        if (cfl > 0.0) {
            const PLICLine2D donor = reconstruct_plic_2d({1.0, 0.0}, alpha[left]);
            flux[face] = plic_swept_area_x(donor, cfl);
        } else if (cfl < 0.0) {
            const PLICLine2D donor = reconstruct_plic_2d({1.0, 0.0}, alpha[right]);
            flux[face] = -plic_swept_area_x(donor, cfl);
        }
    }
    for (int face = 0; face < n; ++face) {
        const int left = face;
        const int right = (face + 1) % n;
        next[left] -= flux[face];
        next[right] += flux[face];
    }
    return next;
}

void test_face_update_conservation_and_bounds()
{
    const PLICLine2D left_full = reconstruct_plic_2d({1.0, 0.0}, 1.0);
    const PLICLine2D right_empty = reconstruct_plic_2d({1.0, 0.0}, 0.0);
    PLICFaceUpdate update = plic_apply_x_face_update(left_full, 1.0, right_empty, 0.0, 0.35);
    require_near(update.flux, 0.35, 1.0e-14, "positive x face update flux");
    require_near(update.left, 0.65, 1.0e-14, "positive x donor remainder");
    require_near(update.right, 0.35, 1.0e-14, "positive x receiver gain");
    require_near(update.left + update.right, 1.0, 1.0e-14, "positive x face update conservation");

    const PLICLine2D bottom_empty = reconstruct_plic_2d({0.0, 1.0}, 0.0);
    const PLICLine2D top_full = reconstruct_plic_2d({0.0, 1.0}, 1.0);
    update = plic_apply_y_face_update(bottom_empty, 0.0, top_full, 1.0, -0.20);
    require_near(update.flux, -0.20, 1.0e-14, "negative y face update signed flux");
    require_near(update.left, 0.20, 1.0e-14, "negative y receiver gain");
    require_near(update.right, 0.80, 1.0e-14, "negative y donor remainder");
    require_near(update.left + update.right, 1.0, 1.0e-14, "negative y face update conservation");

    update = plic_apply_x_face_update(reconstruct_plic_2d({1.0, 0.0}, 0.10), 0.10,
                                      right_empty, 0.0, 1.0);
    require(update.left >= -1.0e-14 && update.right <= 1.0 + 1.0e-14,
            "single-face update remains bounded for CFL=1 donor drain");
    require_near(update.left + update.right, 0.10, 1.0e-14,
                 "single-face update conserves a partial donor");
    pass("PLIC face-update conservation and bounds");
}

void test_periodic_geometric_advection_step()
{
    const std::vector<double> alpha{0.0, 0.0, 1.0, 1.0, 0.0, 0.0};
    const std::vector<double> shifted = plic_periodic_x_update(alpha, 1.0);
    const std::vector<double> expected{0.0, 0.0, 0.0, 1.0, 1.0, 0.0};
    for (std::size_t i = 0; i < shifted.size(); ++i) {
        require_near(shifted[i], expected[i], 1.0e-14,
                     "CFL=1 periodic PLIC update shifts a top-hat exactly");
    }
    require_near(std::accumulate(shifted.begin(), shifted.end(), 0.0),
                 std::accumulate(alpha.begin(), alpha.end(), 0.0), 1.0e-14,
                 "periodic PLIC update conserves total alpha");

    const std::vector<double> fractional{0.0, 0.25, 0.75, 0.0};
    const std::vector<double> advanced = plic_periodic_x_update(fractional, 0.5);
    require_near(std::accumulate(advanced.begin(), advanced.end(), 0.0), 1.0, 1.0e-14,
                 "fractional periodic update conserves total alpha");
    for (const double value : advanced) {
        require(value >= -1.0e-14 && value <= 1.0 + 1.0e-14,
                "fractional periodic PLIC update remains bounded");
    }
    pass("periodic geometric PLIC advection step");
}

void require_vector_near(const std::vector<double>& value, const std::vector<double>& expected,
                         const double tolerance, const std::string& message)
{
    require(value.size() == expected.size(), message + " size");
    for (std::size_t i = 0; i < value.size(); ++i) {
        require_near(value[i], expected[i], tolerance, message);
    }
}

void test_periodic_2d_grid_updates()
{
    const std::vector<double> alpha_x{
        0.0, 1.0, 1.0, 0.0,
        0.0, 0.5, 1.0, 0.0,
    };
    const std::vector<double> shifted_x = plic_periodic_x_update_2d(alpha_x, 4, 2, 1.0);
    require_vector_near(shifted_x, {
        0.0, 0.0, 1.0, 1.0,
        0.0, 0.0, 0.5, 1.0,
    }, 1.0e-14, "2D periodic x update shifts each row exactly at CFL=1");
    require_near(std::accumulate(shifted_x.begin(), shifted_x.end(), 0.0),
                 std::accumulate(alpha_x.begin(), alpha_x.end(), 0.0), 1.0e-14,
                 "2D periodic x update conserves total alpha");

    const std::vector<double> alpha_y{
        0.0, 0.0, 0.0,
        1.0, 0.5, 0.0,
        1.0, 1.0, 0.0,
        0.0, 0.0, 0.0,
    };
    const std::vector<double> shifted_y = plic_periodic_y_update_2d(alpha_y, 3, 4, 1.0);
    require_vector_near(shifted_y, {
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        1.0, 0.5, 0.0,
        1.0, 1.0, 0.0,
    }, 1.0e-14, "2D periodic y update shifts each column exactly at CFL=1");
    require_near(std::accumulate(shifted_y.begin(), shifted_y.end(), 0.0),
                 std::accumulate(alpha_y.begin(), alpha_y.end(), 0.0), 1.0e-14,
                 "2D periodic y update conserves total alpha");

    const std::vector<double> fractional{
        0.0, 0.2, 0.9, 0.0,
        0.1, 0.6, 0.3, 0.0,
    };
    const std::vector<double> advanced = plic_periodic_x_update_2d(fractional, 4, 2, 0.4);
    require_near(std::accumulate(advanced.begin(), advanced.end(), 0.0),
                 std::accumulate(fractional.begin(), fractional.end(), 0.0), 1.0e-14,
                 "2D fractional periodic update conserves total alpha");
    for (const double value : advanced) {
        require(value >= -1.0e-14 && value <= 1.0 + 1.0e-14,
                "2D fractional periodic update remains bounded");
    }
    pass("periodic 2D PLIC grid updates");
}

} // namespace

int main()
{
    std::cout << "\n=== VOF PLIC Unit Tests ===\n";
    test_axis_aligned_exact_cases();
    test_diagonal_half_cell();
    test_round_trip_for_mixed_normals();
    test_bounds_and_monotonicity();
    test_geometric_swept_area_fluxes();
    test_face_update_conservation_and_bounds();
    test_periodic_geometric_advection_step();
    test_periodic_2d_grid_updates();
    std::cout << "\n=== Results: " << n_pass << " passed, " << n_fail << " failed ===\n";
    return n_fail == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
