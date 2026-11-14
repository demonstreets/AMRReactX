#pragma once

#include <cmath>
#include <cstddef>

namespace MyPele::Engineering::AMR {

enum TagReason : unsigned {
    TAG_NONE = 0u,
    TAG_VELOCITY_GRADIENT = 1u << 0u,
    TAG_TEMPERATURE_GRADIENT = 1u << 1u,
    TAG_SPECIES_GRADIENT = 1u << 2u,
    TAG_INTERFACE_CURVATURE = 1u << 3u
};

struct ScalarStencil {
    double center = 0.0;
    double x_lo = 0.0;
    double x_hi = 0.0;
    double y_lo = 0.0;
    double y_hi = 0.0;
    double z_lo = 0.0;
    double z_hi = 0.0;
};

struct VectorStencil {
    ScalarStencil x;
    ScalarStencil y;
    ScalarStencil z;
};

struct CellSize {
    double dx = 1.0;
    double dy = 1.0;
    double dz = 1.0;
};

struct RefinementCriteria {
    double velocity_gradient = 0.0;
    double temperature_gradient = 0.0;
    double species_gradient = 0.0;
    double interface_curvature = 0.0;
};


inline bool positive_spacing(const CellSize& h)
{
    return h.dx > 0.0 && h.dy > 0.0 && h.dz > 0.0;
}

inline double sqr(double value) { return value * value; }

inline double gradient_magnitude(const ScalarStencil& s, const CellSize& h)
{
    if (!positive_spacing(h)) return 0.0;
    const double gx = 0.5 * (s.x_hi - s.x_lo) / h.dx;
    const double gy = 0.5 * (s.y_hi - s.y_lo) / h.dy;
    const double gz = 0.5 * (s.z_hi - s.z_lo) / h.dz;
    return std::sqrt(sqr(gx) + sqr(gy) + sqr(gz));
}

inline double vector_gradient_magnitude(const VectorStencil& v, const CellSize& h)
{
    if (!positive_spacing(h)) return 0.0;
    const double gx = gradient_magnitude(v.x, h);
    const double gy = gradient_magnitude(v.y, h);
    const double gz = gradient_magnitude(v.z, h);
    return std::sqrt(sqr(gx) + sqr(gy) + sqr(gz));
}

inline double curvature_indicator(const ScalarStencil& phi, const CellSize& h)
{
    if (!positive_spacing(h)) return 0.0;
    const double d2x = (phi.x_hi - 2.0 * phi.center + phi.x_lo) / sqr(h.dx);
    const double d2y = (phi.y_hi - 2.0 * phi.center + phi.y_lo) / sqr(h.dy);
    const double d2z = (phi.z_hi - 2.0 * phi.center + phi.z_lo) / sqr(h.dz);
    return std::abs(d2x + d2y + d2z);
}

inline bool exceeds(double value, double threshold)
{
    return threshold > 0.0 && value >= threshold;
}

inline unsigned evaluate_refinement_tags(double velocity_gradient,
                                         double temperature_gradient,
                                         double species_gradient,
                                         double interface_curvature,
                                         const RefinementCriteria& criteria)
{
    unsigned tags = TAG_NONE;
    if (exceeds(velocity_gradient, criteria.velocity_gradient)) {
        tags |= TAG_VELOCITY_GRADIENT;
    }
    if (exceeds(temperature_gradient, criteria.temperature_gradient)) {
        tags |= TAG_TEMPERATURE_GRADIENT;
    }
    if (exceeds(species_gradient, criteria.species_gradient)) {
        tags |= TAG_SPECIES_GRADIENT;
    }
    if (exceeds(interface_curvature, criteria.interface_curvature)) {
        tags |= TAG_INTERFACE_CURVATURE;
    }
    return tags;
}

inline bool has_tag(unsigned tags, TagReason reason)
{
    return (tags & static_cast<unsigned>(reason)) != 0u;
}

struct StructuredGrid2D {
    int nx = 0;
    int ny = 0;
    double dx = 1.0;
    double dy = 1.0;
};

struct StructuredFields2D {
    const double* velocity_x = nullptr;
    const double* velocity_y = nullptr;
    const double* temperature = nullptr;
    const double* species = nullptr;
    const double* volume_fraction = nullptr;
};

inline bool valid_structured_grid(const StructuredGrid2D& grid)
{
    return grid.nx >= 3 && grid.ny >= 3 && grid.dx > 0.0 && grid.dy > 0.0;
}

inline std::size_t structured_index(int i, int j, int nx)
{
    return static_cast<std::size_t>(j) * static_cast<std::size_t>(nx) +
           static_cast<std::size_t>(i);
}

inline ScalarStencil scalar_stencil_2d(const double* field,
                                       const StructuredGrid2D& grid,
                                       int i,
                                       int j)
{
    ScalarStencil stencil{};
    if (field == nullptr || !valid_structured_grid(grid) || i <= 0 || j <= 0 ||
        i >= grid.nx - 1 || j >= grid.ny - 1) {
        return stencil;
    }

    stencil.center = field[structured_index(i, j, grid.nx)];
    stencil.x_lo = field[structured_index(i - 1, j, grid.nx)];
    stencil.x_hi = field[structured_index(i + 1, j, grid.nx)];
    stencil.y_lo = field[structured_index(i, j - 1, grid.nx)];
    stencil.y_hi = field[structured_index(i, j + 1, grid.nx)];
    stencil.z_lo = stencil.center;
    stencil.z_hi = stencil.center;
    return stencil;
}

inline unsigned evaluate_structured_cell_2d(const StructuredFields2D& fields,
                                            const StructuredGrid2D& grid,
                                            int i,
                                            int j,
                                            const RefinementCriteria& criteria)
{
    if (!valid_structured_grid(grid) || i <= 0 || j <= 0 ||
        i >= grid.nx - 1 || j >= grid.ny - 1) {
        return TAG_NONE;
    }

    const CellSize h{grid.dx, grid.dy, 1.0};
    VectorStencil velocity{};
    velocity.x = scalar_stencil_2d(fields.velocity_x, grid, i, j);
    velocity.y = scalar_stencil_2d(fields.velocity_y, grid, i, j);

    const double velocity_gradient =
        (fields.velocity_x != nullptr && fields.velocity_y != nullptr)
            ? vector_gradient_magnitude(velocity, h)
            : 0.0;
    const double temperature_gradient =
        (fields.temperature != nullptr)
            ? gradient_magnitude(scalar_stencil_2d(fields.temperature, grid, i, j), h)
            : 0.0;
    const double species_gradient =
        (fields.species != nullptr)
            ? gradient_magnitude(scalar_stencil_2d(fields.species, grid, i, j), h)
            : 0.0;
    const double interface_curvature =
        (fields.volume_fraction != nullptr)
            ? curvature_indicator(scalar_stencil_2d(fields.volume_fraction, grid, i, j), h)
            : 0.0;

    return evaluate_refinement_tags(velocity_gradient,
                                    temperature_gradient,
                                    species_gradient,
                                    interface_curvature,
                                    criteria);
}

inline void apply_structured_tags_2d(const StructuredFields2D& fields,
                                     const StructuredGrid2D& grid,
                                     const RefinementCriteria& criteria,
                                     unsigned* tags)
{
    if (tags == nullptr || !valid_structured_grid(grid)) {
        return;
    }

    for (int j = 0; j < grid.ny; ++j) {
        for (int i = 0; i < grid.nx; ++i) {
            tags[structured_index(i, j, grid.nx)] =
                evaluate_structured_cell_2d(fields, grid, i, j, criteria);
        }
    }
}


inline void apply_structured_tagbox_2d(const StructuredFields2D& fields,
                                       const StructuredGrid2D& grid,
                                       const RefinementCriteria& criteria,
                                       char* tagbox,
                                       char clear_value,
                                       char set_value,
                                       const unsigned char* covered = nullptr,
                                       unsigned* reason_tags = nullptr)
{
    if (tagbox == nullptr || !valid_structured_grid(grid)) {
        return;
    }

    for (int j = 0; j < grid.ny; ++j) {
        for (int i = 0; i < grid.nx; ++i) {
            const std::size_t idx = structured_index(i, j, grid.nx);
            tagbox[idx] = clear_value;
            if (reason_tags != nullptr) {
                reason_tags[idx] = TAG_NONE;
            }
            if (covered != nullptr && covered[idx] != 0u) {
                continue;
            }

            const unsigned tags =
                evaluate_structured_cell_2d(fields, grid, i, j, criteria);
            if (reason_tags != nullptr) {
                reason_tags[idx] = tags;
            }
            if (tags != TAG_NONE) {
                tagbox[idx] = set_value;
            }
        }
    }
}

} // namespace MyPele::Engineering::AMR
