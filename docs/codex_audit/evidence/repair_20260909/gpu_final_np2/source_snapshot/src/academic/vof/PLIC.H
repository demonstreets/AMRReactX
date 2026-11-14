#ifndef PLIC_H
#define PLIC_H

#include <algorithm>
#include <array>
#include <cmath>
#include <vector>

namespace MyPele::Academic::VOF {

struct Vec2 {
    double x = 0.0;
    double y = 0.0;
};

struct PLICLine2D {
    Vec2 normal{};
    double constant = 0.0;
};

inline double dot(const Vec2 a, const Vec2 b)
{
    return a.x * b.x + a.y * b.y;
}

inline double norm(const Vec2 a)
{
    return std::sqrt(dot(a, a));
}

inline Vec2 normalize_or_x(Vec2 n)
{
    const double mag = norm(n);
    if (!std::isfinite(mag) || mag <= 0.0) {
        return {1.0, 0.0};
    }
    return {n.x / mag, n.y / mag};
}

inline std::vector<Vec2> clip_polygon_less_equal(
    const std::vector<Vec2>& polygon, const Vec2 normal, const double constant)
{
    std::vector<Vec2> out;
    if (polygon.empty()) {
        return out;
    }

    auto signed_distance = [&](const Vec2 p) { return dot(normal, p) - constant; };
    Vec2 previous = polygon.back();
    double d_previous = signed_distance(previous);
    bool previous_inside = d_previous <= 0.0;

    for (const Vec2 current : polygon) {
        const double d_current = signed_distance(current);
        const bool current_inside = d_current <= 0.0;

        if (previous_inside != current_inside) {
            const double denom = d_previous - d_current;
            const double theta = std::abs(denom) > 1.0e-30 ? d_previous / denom : 0.0;
            out.push_back({previous.x + theta * (current.x - previous.x),
                           previous.y + theta * (current.y - previous.y)});
        }
        if (current_inside) {
            out.push_back(current);
        }
        previous = current;
        d_previous = d_current;
        previous_inside = current_inside;
    }
    return out;
}

inline double polygon_area(const std::vector<Vec2>& polygon)
{
    if (polygon.size() < 3) {
        return 0.0;
    }
    double twice_area = 0.0;
    for (std::size_t i = 0; i < polygon.size(); ++i) {
        const Vec2 a = polygon[i];
        const Vec2 b = polygon[(i + 1) % polygon.size()];
        twice_area += a.x * b.y - a.y * b.x;
    }
    return 0.5 * std::abs(twice_area);
}

inline double unit_square_area_less_equal(Vec2 normal, const double constant)
{
    normal = normalize_or_x(normal);
    const std::vector<Vec2> square{{0.0, 0.0}, {1.0, 0.0}, {1.0, 1.0}, {0.0, 1.0}};
    return std::clamp(polygon_area(clip_polygon_less_equal(square, normal, constant)), 0.0, 1.0);
}

inline std::array<double, 2> unit_square_projection_bounds(Vec2 normal)
{
    normal = normalize_or_x(normal);
    const double p00 = 0.0;
    const double p10 = normal.x;
    const double p01 = normal.y;
    const double p11 = normal.x + normal.y;
    return {std::min({p00, p10, p01, p11}), std::max({p00, p10, p01, p11})};
}

inline PLICLine2D reconstruct_plic_2d(Vec2 normal, const double volume_fraction)
{
    normal = normalize_or_x(normal);
    const double vf = std::clamp(volume_fraction, 0.0, 1.0);
    const auto bounds = unit_square_projection_bounds(normal);
    if (vf <= 0.0) {
        return {normal, bounds[0]};
    }
    if (vf >= 1.0) {
        return {normal, bounds[1]};
    }

    double lo = bounds[0];
    double hi = bounds[1];
    for (int iter = 0; iter < 80; ++iter) {
        const double mid = 0.5 * (lo + hi);
        const double area = unit_square_area_less_equal(normal, mid);
        if (area < vf) {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    return {normal, 0.5 * (lo + hi)};
}

inline double plic_area_fraction(const PLICLine2D& line)
{
    return unit_square_area_less_equal(line.normal, line.constant);
}

inline std::vector<Vec2> unit_square_liquid_polygon(const PLICLine2D& line)
{
    const std::vector<Vec2> square{{0.0, 0.0}, {1.0, 0.0}, {1.0, 1.0}, {0.0, 1.0}};
    return clip_polygon_less_equal(square, normalize_or_x(line.normal), line.constant);
}

inline double plic_box_area_fraction(
    const PLICLine2D& line,
    const double xmin, const double xmax,
    const double ymin, const double ymax)
{
    const double xlo = std::clamp(std::min(xmin, xmax), 0.0, 1.0);
    const double xhi = std::clamp(std::max(xmin, xmax), 0.0, 1.0);
    const double ylo = std::clamp(std::min(ymin, ymax), 0.0, 1.0);
    const double yhi = std::clamp(std::max(ymin, ymax), 0.0, 1.0);
    if (xhi <= xlo || yhi <= ylo) {
        return 0.0;
    }

    std::vector<Vec2> poly = unit_square_liquid_polygon(line);
    poly = clip_polygon_less_equal(poly, {-1.0, 0.0}, -xlo);
    poly = clip_polygon_less_equal(poly, {1.0, 0.0}, xhi);
    poly = clip_polygon_less_equal(poly, {0.0, -1.0}, -ylo);
    poly = clip_polygon_less_equal(poly, {0.0, 1.0}, yhi);
    return std::clamp(polygon_area(poly), 0.0, 1.0);
}

inline double plic_swept_area_x(const PLICLine2D& line, const double cfl)
{
    const double width = std::clamp(std::abs(cfl), 0.0, 1.0);
    if (width <= 0.0) {
        return 0.0;
    }
    if (cfl > 0.0) {
        return plic_box_area_fraction(line, 1.0 - width, 1.0, 0.0, 1.0);
    }
    return plic_box_area_fraction(line, 0.0, width, 0.0, 1.0);
}

inline double plic_swept_area_y(const PLICLine2D& line, const double cfl)
{
    const double width = std::clamp(std::abs(cfl), 0.0, 1.0);
    if (width <= 0.0) {
        return 0.0;
    }
    if (cfl > 0.0) {
        return plic_box_area_fraction(line, 0.0, 1.0, 1.0 - width, 1.0);
    }
    return plic_box_area_fraction(line, 0.0, 1.0, 0.0, width);
}

struct PLICFaceUpdate {
    double left = 0.0;
    double right = 0.0;
    double flux = 0.0;
};

inline PLICFaceUpdate plic_apply_x_face_update(
    const PLICLine2D& left_line, const double left_alpha,
    const PLICLine2D& right_line, const double right_alpha,
    const double cfl)
{
    const double left = std::clamp(left_alpha, 0.0, 1.0);
    const double right = std::clamp(right_alpha, 0.0, 1.0);
    if (cfl > 0.0) {
        const double flux = std::clamp(plic_swept_area_x(left_line, cfl), 0.0, left);
        return {left - flux, right + flux, flux};
    }
    if (cfl < 0.0) {
        const double flux = std::clamp(plic_swept_area_x(right_line, cfl), 0.0, right);
        return {left + flux, right - flux, -flux};
    }
    return {left, right, 0.0};
}

inline PLICFaceUpdate plic_apply_y_face_update(
    const PLICLine2D& bottom_line, const double bottom_alpha,
    const PLICLine2D& top_line, const double top_alpha,
    const double cfl)
{
    const double bottom = std::clamp(bottom_alpha, 0.0, 1.0);
    const double top = std::clamp(top_alpha, 0.0, 1.0);
    if (cfl > 0.0) {
        const double flux = std::clamp(plic_swept_area_y(bottom_line, cfl), 0.0, bottom);
        return {bottom - flux, top + flux, flux};
    }
    if (cfl < 0.0) {
        const double flux = std::clamp(plic_swept_area_y(top_line, cfl), 0.0, top);
        return {bottom + flux, top - flux, -flux};
    }
    return {bottom, top, 0.0};
}

inline int plic_grid_index(const int i, const int j, const int nx)
{
    return j * nx + i;
}

inline std::vector<double> plic_periodic_x_update_2d(
    const std::vector<double>& alpha, const int nx, const int ny,
    const double cfl, const Vec2 normal = {1.0, 0.0})
{
    if (nx <= 0 || ny <= 0 || static_cast<int>(alpha.size()) != nx * ny) {
        return alpha;
    }

    std::vector<double> delta(alpha.size(), 0.0);
    for (int j = 0; j < ny; ++j) {
        std::vector<double> flux(nx, 0.0);
        for (int i = 0; i < nx; ++i) {
            const int left = plic_grid_index(i, j, nx);
            const int right = plic_grid_index((i + 1) % nx, j, nx);
            if (cfl > 0.0) {
                const double donor = std::clamp(alpha[left], 0.0, 1.0);
                const PLICLine2D line = reconstruct_plic_2d(normal, donor);
                flux[i] = std::clamp(plic_swept_area_x(line, cfl), 0.0, donor);
            } else if (cfl < 0.0) {
                const double donor = std::clamp(alpha[right], 0.0, 1.0);
                const PLICLine2D line = reconstruct_plic_2d(normal, donor);
                flux[i] = -std::clamp(plic_swept_area_x(line, cfl), 0.0, donor);
            }
        }
        for (int i = 0; i < nx; ++i) {
            const int left = plic_grid_index(i, j, nx);
            const int right = plic_grid_index((i + 1) % nx, j, nx);
            delta[left] -= flux[i];
            delta[right] += flux[i];
        }
    }
    std::vector<double> next(alpha.begin(), alpha.end());
    for (std::size_t idx = 0; idx < next.size(); ++idx) {
        next[idx] = std::clamp(next[idx] + delta[idx], 0.0, 1.0);
    }
    return next;
}

inline std::vector<double> plic_periodic_y_update_2d(
    const std::vector<double>& alpha, const int nx, const int ny,
    const double cfl, const Vec2 normal = {0.0, 1.0})
{
    if (nx <= 0 || ny <= 0 || static_cast<int>(alpha.size()) != nx * ny) {
        return alpha;
    }

    std::vector<double> delta(alpha.size(), 0.0);
    for (int i = 0; i < nx; ++i) {
        std::vector<double> flux(ny, 0.0);
        for (int j = 0; j < ny; ++j) {
            const int bottom = plic_grid_index(i, j, nx);
            const int top = plic_grid_index(i, (j + 1) % ny, nx);
            if (cfl > 0.0) {
                const double donor = std::clamp(alpha[bottom], 0.0, 1.0);
                const PLICLine2D line = reconstruct_plic_2d(normal, donor);
                flux[j] = std::clamp(plic_swept_area_y(line, cfl), 0.0, donor);
            } else if (cfl < 0.0) {
                const double donor = std::clamp(alpha[top], 0.0, 1.0);
                const PLICLine2D line = reconstruct_plic_2d(normal, donor);
                flux[j] = -std::clamp(plic_swept_area_y(line, cfl), 0.0, donor);
            }
        }
        for (int j = 0; j < ny; ++j) {
            const int bottom = plic_grid_index(i, j, nx);
            const int top = plic_grid_index(i, (j + 1) % ny, nx);
            delta[bottom] -= flux[j];
            delta[top] += flux[j];
        }
    }
    std::vector<double> next(alpha.begin(), alpha.end());
    for (std::size_t idx = 0; idx < next.size(); ++idx) {
        next[idx] = std::clamp(next[idx] + delta[idx], 0.0, 1.0);
    }
    return next;
}

} // namespace MyPele::Academic::VOF

#endif
