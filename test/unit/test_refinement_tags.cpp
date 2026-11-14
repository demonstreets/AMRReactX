#include "refinement_tags.H"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
#include <cstddef>

namespace {

void require(bool condition, const std::string& message)
{
    if (!condition) {
        std::cerr << "FAIL: " << message << "\n";
        std::exit(1);
    }
}

void require_near(double value, double expected, double tolerance,
                  const std::string& message)
{
    if (std::abs(value - expected) > tolerance) {
        std::cerr << "FAIL: " << message << ": got " << value
                  << ", expected " << expected << " +/- " << tolerance << "\n";
        std::exit(1);
    }
}

} // namespace

int main()
{
    namespace AMR = MyPele::Engineering::AMR;

    const AMR::CellSize h{0.5, 0.25, 1.0};

    AMR::ScalarStencil temperature{};
    temperature.x_lo = 290.0;
    temperature.x_hi = 310.0;
    temperature.y_lo = 300.0;
    temperature.y_hi = 300.0;
    temperature.z_lo = 300.0;
    temperature.z_hi = 300.0;
    require_near(AMR::gradient_magnitude(temperature, h), 20.0, 1.0e-12,
                 "temperature central gradient uses physical dx");

    AMR::ScalarStencil species{};
    species.x_lo = 0.0;
    species.x_hi = 0.2;
    species.y_lo = 0.1;
    species.y_hi = 0.1;
    species.z_lo = 0.1;
    species.z_hi = 0.1;
    require_near(AMR::gradient_magnitude(species, h), 0.2, 1.0e-12,
                 "species central gradient is normalized by spacing");

    AMR::VectorStencil velocity{};
    velocity.x.x_lo = 0.0;
    velocity.x.x_hi = 4.0;
    velocity.y.y_lo = -1.0;
    velocity.y.y_hi = 1.0;
    velocity.z.z_lo = 0.0;
    velocity.z.z_hi = 0.0;
    const double expected_velocity_grad = std::sqrt(4.0 * 4.0 + 4.0 * 4.0);
    require_near(AMR::vector_gradient_magnitude(velocity, h),
                 expected_velocity_grad, 1.0e-12,
                 "velocity gradient combines component gradients");

    AMR::ScalarStencil phi{};
    phi.center = 1.0;
    phi.x_lo = 0.0;
    phi.x_hi = 0.0;
    phi.y_lo = 1.0;
    phi.y_hi = 1.0;
    phi.z_lo = 1.0;
    phi.z_hi = 1.0;
    require_near(AMR::curvature_indicator(phi, h), 8.0, 1.0e-12,
                 "curvature indicator uses second derivative with grid spacing");

    AMR::RefinementCriteria criteria{};
    criteria.velocity_gradient = 5.0;
    criteria.temperature_gradient = 10.0;
    criteria.species_gradient = 0.25;
    criteria.interface_curvature = 4.0;

    const unsigned tags = AMR::evaluate_refinement_tags(
        AMR::vector_gradient_magnitude(velocity, h),
        AMR::gradient_magnitude(temperature, h),
        AMR::gradient_magnitude(species, h),
        AMR::curvature_indicator(phi, h),
        criteria);
    require(AMR::has_tag(tags, AMR::TAG_VELOCITY_GRADIENT),
            "large velocity gradient triggers AMR tag");
    require(AMR::has_tag(tags, AMR::TAG_TEMPERATURE_GRADIENT),
            "large temperature gradient triggers AMR tag");
    require(!AMR::has_tag(tags, AMR::TAG_SPECIES_GRADIENT),
            "species gradient below threshold is not tagged");
    require(AMR::has_tag(tags, AMR::TAG_INTERFACE_CURVATURE),
            "large interface curvature triggers AMR tag");

    criteria.velocity_gradient = 0.0;
    criteria.temperature_gradient = 0.0;
    criteria.species_gradient = 0.0;
    criteria.interface_curvature = 0.0;
    require(AMR::evaluate_refinement_tags(100.0, 100.0, 100.0, 100.0, criteria) ==
                AMR::TAG_NONE,
            "zero thresholds disable individual AMR criteria");



    const AMR::StructuredGrid2D grid{5, 5, 0.5, 0.25};
    const auto idx = [&](int i, int j) {
        return AMR::structured_index(i, j, grid.nx);
    };
    std::vector<double> u(static_cast<std::size_t>(grid.nx * grid.ny), 0.0);
    std::vector<double> v(static_cast<std::size_t>(grid.nx * grid.ny), 0.0);
    std::vector<double> temp(static_cast<std::size_t>(grid.nx * grid.ny), 300.0);
    std::vector<double> yfuel(static_cast<std::size_t>(grid.nx * grid.ny), 0.1);
    std::vector<double> alpha(static_cast<std::size_t>(grid.nx * grid.ny), 1.0);
    std::vector<unsigned> grid_tags(static_cast<std::size_t>(grid.nx * grid.ny),
                                    AMR::TAG_NONE);

    u[idx(1, 2)] = 0.0;
    u[idx(3, 2)] = 4.0;
    v[idx(2, 1)] = -1.0;
    v[idx(2, 3)] = 1.0;
    temp[idx(1, 2)] = 290.0;
    temp[idx(3, 2)] = 310.0;
    yfuel[idx(1, 2)] = 0.0;
    yfuel[idx(3, 2)] = 0.2;
    alpha[idx(2, 2)] = 1.0;
    alpha[idx(1, 2)] = 0.0;
    alpha[idx(3, 2)] = 0.0;

    AMR::StructuredFields2D fields{};
    fields.velocity_x = u.data();
    fields.velocity_y = v.data();
    fields.temperature = temp.data();
    fields.species = yfuel.data();
    fields.volume_fraction = alpha.data();

    criteria.velocity_gradient = 5.0;
    criteria.temperature_gradient = 10.0;
    criteria.species_gradient = 0.25;
    criteria.interface_curvature = 4.0;
    AMR::apply_structured_tags_2d(fields, grid, criteria, grid_tags.data());

    const unsigned center_tags = grid_tags[idx(2, 2)];
    require(AMR::has_tag(center_tags, AMR::TAG_VELOCITY_GRADIENT),
            "structured adapter tags velocity gradients");
    require(AMR::has_tag(center_tags, AMR::TAG_TEMPERATURE_GRADIENT),
            "structured adapter tags temperature gradients");
    require(!AMR::has_tag(center_tags, AMR::TAG_SPECIES_GRADIENT),
            "structured adapter leaves subthreshold species untagged");
    require(AMR::has_tag(center_tags, AMR::TAG_INTERFACE_CURVATURE),
            "structured adapter tags interface curvature");
    require(grid_tags[idx(0, 2)] == AMR::TAG_NONE,
            "structured adapter does not tag boundary cells without neighbors");

    AMR::StructuredFields2D temperature_only{};
    temperature_only.temperature = temp.data();
    require(AMR::evaluate_structured_cell_2d(temperature_only, grid, 2, 2,
                                            criteria) ==
                AMR::TAG_TEMPERATURE_GRADIENT,
            "structured adapter handles missing optional fields independently");

    std::vector<unsigned> unchanged(9, 123u);
    const AMR::StructuredGrid2D bad_grid{2, 2, 1.0, 1.0};
    AMR::apply_structured_tags_2d(fields, bad_grid, criteria, unchanged.data());
    require(unchanged[0] == 123u && unchanged[8] == 123u,
            "invalid structured grid leaves output untouched");


    std::vector<char> tagbox(static_cast<std::size_t>(grid.nx * grid.ny), '?');
    std::vector<unsigned> reasons(static_cast<std::size_t>(grid.nx * grid.ny),
                                  777u);
    AMR::apply_structured_tagbox_2d(fields, grid, criteria, tagbox.data(),
                                    'C', 'S', nullptr, reasons.data());
    require(tagbox[idx(2, 2)] == 'S',
            "TagBox-compatible adapter sets tagged interior cells");
    require(tagbox[idx(0, 2)] == 'C',
            "TagBox-compatible adapter clears boundary cells");
    require(AMR::has_tag(reasons[idx(2, 2)], AMR::TAG_VELOCITY_GRADIENT),
            "TagBox-compatible adapter can mirror reason bitmasks");

    std::vector<unsigned char> covered(static_cast<std::size_t>(grid.nx * grid.ny),
                                       0u);
    covered[idx(2, 2)] = 1u;
    AMR::apply_structured_tagbox_2d(fields, grid, criteria, tagbox.data(),
                                    'C', 'S', covered.data(), reasons.data());
    require(tagbox[idx(2, 2)] == 'C' && reasons[idx(2, 2)] == AMR::TAG_NONE,
            "TagBox-compatible adapter clears covered cells");

    std::vector<char> invalid_tagbox(9, '?');
    AMR::apply_structured_tagbox_2d(fields, bad_grid, criteria,
                                    invalid_tagbox.data(), 'C', 'S');
    require(invalid_tagbox[0] == '?' && invalid_tagbox[8] == '?',
            "invalid grid leaves TagBox-compatible output untouched");

    const AMR::CellSize bad_h{0.0, 1.0, 1.0};
    require(AMR::gradient_magnitude(temperature, bad_h) == 0.0,
            "nonpositive grid spacing disables scalar gradient");
    require(AMR::curvature_indicator(phi, bad_h) == 0.0,
            "nonpositive grid spacing disables curvature indicator");

    std::cout << "refinement_tags_smoke PASS: scalar/vector gradients, curvature, structured-grid adapter, and TagBox-compatible output" << "\n";
    return 0;
}
