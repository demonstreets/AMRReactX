#pragma once

#include <AMReX_GpuQualifiers.H>
#include <AMReX_REAL.H>
#include <AMReX_SPACE.H>

#include <cmath>
#include <string>

namespace amrreactx {

enum StateIndex {
    Rho = 0,
    Uvel,
    Vvel,
    Wvel,
    YLeak,
    Porosity,
    NumState
};

enum InitType {
    Zero = 0,
    Gaussian
};

enum BoundaryType {
    BcInlet = 0,
    BcOutlet,
    BcWall,
    BcOpen
};

enum SourceType {
    SourceGaussian = 0,
    SourceBox
};

enum ConcentrationBasis {
    BasisMassFraction = 0,
    BasisVolumeFraction
};

enum PorosityType {
    PorosityBox = 0,
    PorosityCylinder
};

enum DiagIndex {
    SourceRate = 0,
    OutletRate,
    OutletXLoRate,
    OutletXHiRate,
    OutletYLoRate,
    OutletYHiRate,
    OutletZLoRate,
    OutletZHiRate,
    InflowRate,
    InflowXLoRate,
    InflowXHiRate,
    InflowYLoRate,
    InflowYHiRate,
    InflowZLoRate,
    InflowZHiRate,
    XMoment,
    YMoment,
    ZMoment,
    CloudIndicator,
    FlammableIndicator,
    CloudMassDensity,
    FlammableMassDensity,
    CloudConcentrationSum,
    FlammableConcentrationSum,
    NumDiag
};

enum TagIndex {
    GradYTag = 0,
    SourceRegionTag,
    PorosityInterfaceTag,
    RefineTag,
    NumTag
};

struct RuntimeParams {
    int max_grid_size = 32;
    int max_step = 80;
    int plot_int = 20;
    amrex::Real dt = 0.01;
    amrex::Real stop_time = -1.0;
    amrex::Real cfl = 0.8;
    amrex::Real diff_cfl = 0.4;
    int use_auto_dt = 0;
    amrex::Real diffusion = 0.01;
    amrex::Real rho0 = 1.0;
    amrex::Real inlet_y = 0.0;
    amrex::Real ambient_y = 0.0;
    amrex::Real wind[AMREX_SPACEDIM] = {AMREX_D_DECL(1.0, 0.0, 0.0)};
    amrex::Real source_center[AMREX_SPACEDIM] = {AMREX_D_DECL(1.0, 2.0, 2.0)};
    amrex::Real source_box_lo[AMREX_SPACEDIM] = {AMREX_D_DECL(0.9, 1.9, 1.9)};
    amrex::Real source_box_hi[AMREX_SPACEDIM] = {AMREX_D_DECL(1.1, 2.1, 2.1)};
    amrex::Real source_sigma = 0.15;
    amrex::Real source_strength = 0.2;
    amrex::Real source_total_rate = -1.0;
    int source_type = SourceGaussian;
    int porosity_enabled = 0;
    int porosity_type = PorosityBox;
    amrex::Real porosity_box_lo[AMREX_SPACEDIM] = {AMREX_D_DECL(1.5, 1.5, 1.5)};
    amrex::Real porosity_box_hi[AMREX_SPACEDIM] = {AMREX_D_DECL(2.5, 2.5, 2.5)};
    amrex::Real porosity_cylinder_center[AMREX_SPACEDIM] = {AMREX_D_DECL(2.0, 2.0, 2.0)};
    amrex::Real porosity_cylinder_radius = 0.5;
    int porosity_cylinder_axis = 2;
    amrex::Real porosity_cylinder_axis_lo = 1.0;
    amrex::Real porosity_cylinder_axis_hi = 3.0;
    amrex::Real porosity_transition = 0.0;
    amrex::Real porosity_solid_value = 0.0;
    amrex::Real porosity_resistance = 100.0;
    int init_type = Zero;
    amrex::Real init_center[AMREX_SPACEDIM] = {AMREX_D_DECL(2.0, 2.0, 2.0)};
    amrex::Real init_sigma = 0.25;
    amrex::Real init_amplitude = 0.25;
    int bc_lo[AMREX_SPACEDIM] = {AMREX_D_DECL(BcInlet, BcOpen, BcWall)};
    int bc_hi[AMREX_SPACEDIM] = {AMREX_D_DECL(BcOutlet, BcOpen, BcOpen)};
    amrex::Real cloud_threshold = 0.01;
    amrex::Real lel = 0.05;
    amrex::Real uel = 0.15;
    amrex::Real leak_molecular_weight = 16.04;
    amrex::Real air_molecular_weight = 28.97;
    int diagnostic_basis = BasisMassFraction;
    int tagging_enabled = 0;
    amrex::Real tag_grad_y = 0.05;
    int tag_source_region = 0;
    amrex::Real tag_source_radius = -1.0;
    amrex::Real tag_source_box_buffer = 0.0;
    int tag_porosity_interface = 0;
    amrex::Real tag_porosity_threshold = 0.1;
    int tag_buffer = 1;
    int tag_ref_ratio = 2;
    int tag_max_grid_size = 16;
    amrex::Real tag_grid_efficiency = 0.7;
    int amr_regrid_interval = 0;
    int amr_restrict_after_advance = 0;
    int amr_reflux_after_advance = 0;
    std::string history_file = "history.csv";
    std::string plotfile_prefix = "plt_leak";
};

struct KernelParams {
    amrex::Real dt;
    amrex::Real diffusion;
    amrex::Real rho0;
    amrex::Real inlet_y;
    amrex::Real ambient_y;
    amrex::Real wind[AMREX_SPACEDIM];
    amrex::Real source_center[AMREX_SPACEDIM];
    amrex::Real source_box_lo[AMREX_SPACEDIM];
    amrex::Real source_box_hi[AMREX_SPACEDIM];
    amrex::Real source_sigma;
    amrex::Real source_strength;
    int source_type;
    int porosity_enabled;
    int porosity_type;
    amrex::Real porosity_box_lo[AMREX_SPACEDIM];
    amrex::Real porosity_box_hi[AMREX_SPACEDIM];
    amrex::Real porosity_cylinder_center[AMREX_SPACEDIM];
    amrex::Real porosity_cylinder_radius;
    int porosity_cylinder_axis;
    amrex::Real porosity_cylinder_axis_lo;
    amrex::Real porosity_cylinder_axis_hi;
    amrex::Real porosity_transition;
    amrex::Real porosity_solid_value;
    amrex::Real porosity_resistance;
    int bc_lo[AMREX_SPACEDIM];
    int bc_hi[AMREX_SPACEDIM];
};

struct StabilityInfo {
    amrex::Real advective_cfl = 0.0;
    amrex::Real max_directional_cfl = 0.0;
    amrex::Real diffusion_number = 0.0;
    amrex::Real dt_advective_limit = 1.0e200;
    amrex::Real dt_diffusion_limit = 1.0e200;
    amrex::Real recommended_dt = 1.0e200;
};

struct TransportDiagnostics {
    amrex::Real scalar_mass = 0.0;
    amrex::Real source_rate = 0.0;
    amrex::Real outlet_rate = 0.0;
    amrex::Real outlet_xlo_rate = 0.0;
    amrex::Real outlet_xhi_rate = 0.0;
    amrex::Real outlet_ylo_rate = 0.0;
    amrex::Real outlet_yhi_rate = 0.0;
    amrex::Real outlet_zlo_rate = 0.0;
    amrex::Real outlet_zhi_rate = 0.0;
    amrex::Real boundary_inflow_rate = 0.0;
    amrex::Real inflow_xlo_rate = 0.0;
    amrex::Real inflow_xhi_rate = 0.0;
    amrex::Real inflow_ylo_rate = 0.0;
    amrex::Real inflow_yhi_rate = 0.0;
    amrex::Real inflow_zlo_rate = 0.0;
    amrex::Real inflow_zhi_rate = 0.0;
    amrex::Real x_centroid = 0.0;
    amrex::Real y_centroid = 0.0;
    amrex::Real z_centroid = 0.0;
    amrex::Real max_y = 0.0;
    amrex::Real max_y_x = 0.0;
    amrex::Real max_y_y = 0.0;
    amrex::Real max_y_z = 0.0;
    amrex::Real max_concentration = 0.0;
    amrex::Real cloud_volume = 0.0;
    amrex::Real flammable_volume = 0.0;
    amrex::Real cloud_mass = 0.0;
    amrex::Real flammable_mass = 0.0;
    amrex::Real cloud_mean_concentration = 0.0;
    amrex::Real flammable_mean_concentration = 0.0;
    amrex::Real cloud_x_min = 0.0;
    amrex::Real cloud_x_max = 0.0;
    amrex::Real cloud_y_min = 0.0;
    amrex::Real cloud_y_max = 0.0;
    amrex::Real cloud_z_min = 0.0;
    amrex::Real cloud_z_max = 0.0;
    amrex::Real flammable_x_min = 0.0;
    amrex::Real flammable_x_max = 0.0;
    amrex::Real flammable_y_min = 0.0;
    amrex::Real flammable_y_max = 0.0;
    amrex::Real flammable_z_min = 0.0;
    amrex::Real flammable_z_max = 0.0;
    amrex::Real porosity_min = 1.0;
    amrex::Real porosity_mean = 1.0;
    amrex::Real solid_volume = 0.0;
    amrex::Real solid_scalar_mass = 0.0;
    amrex::Real tag_grad_y_volume = 0.0;
    amrex::Real tag_source_volume = 0.0;
    amrex::Real tag_porosity_volume = 0.0;
    amrex::Real tag_refine_volume = 0.0;
    amrex::Real tag_candidate_level1_volume = 0.0;
    amrex::Real amr_level1_x_min = 0.0;
    amrex::Real amr_level1_x_max = 0.0;
    amrex::Real amr_level1_y_min = 0.0;
    amrex::Real amr_level1_y_max = 0.0;
    amrex::Real amr_level1_z_min = 0.0;
    amrex::Real amr_level1_z_max = 0.0;
    amrex::Real amr_restrict_max_abs_y_error = 0.0;
    amrex::Real amr_restrict_l1_y_error = 0.0;
    amrex::Real amr_level1_mass = 0.0;
    amrex::Real amr_level1_solid_volume = 0.0;
    amrex::Real amr_level1_solid_scalar_mass = 0.0;
    amrex::Real amr_covered_level0_mass = 0.0;
    amrex::Real amr_mass_delta = 0.0;
    amrex::Real amr_applied_restriction_mass_delta = 0.0;
    amrex::Real amr_applied_reflux_mass_delta = 0.0;
    amrex::Real amr_cumulative_restriction_mass_delta = 0.0;
    amrex::Real amr_cumulative_reflux_mass_delta = 0.0;
    amrex::Real amr_cf_advective_flux_mismatch = 0.0;
    amrex::Real amr_cf_advective_abs_mismatch = 0.0;
    amrex::Real amr_cf_diffusive_flux_mismatch = 0.0;
    amrex::Real amr_cf_diffusive_abs_mismatch = 0.0;
    amrex::Real amr_cf_advective_mismatch_mass = 0.0;
    amrex::Real amr_cf_advective_abs_mismatch_mass = 0.0;
    amrex::Real amr_cf_diffusive_mismatch_mass = 0.0;
    amrex::Real amr_cf_diffusive_abs_mismatch_mass = 0.0;
    amrex::Real amr_cf_advective_flux_mismatch_face[2 * AMREX_SPACEDIM] = {};
    amrex::Real amr_cf_advective_abs_mismatch_face[2 * AMREX_SPACEDIM] = {};
    amrex::Real amr_cf_advective_mismatch_mass_face[2 * AMREX_SPACEDIM] = {};
    amrex::Real amr_cf_advective_abs_mismatch_mass_face[2 * AMREX_SPACEDIM] = {};
    amrex::Real amr_cf_diffusive_flux_mismatch_face[2 * AMREX_SPACEDIM] = {};
    amrex::Real amr_cf_diffusive_abs_mismatch_face[2 * AMREX_SPACEDIM] = {};
    amrex::Real amr_cf_diffusive_mismatch_mass_face[2 * AMREX_SPACEDIM] = {};
    amrex::Real amr_cf_diffusive_abs_mismatch_mass_face[2 * AMREX_SPACEDIM] = {};
    long long amr_restrict_coarse_cell_count = 0;
    long long amr_cf_interface_face_count = 0;
    long long amr_cf_interface_face_count_face[2 * AMREX_SPACEDIM] = {};
    long long tag_refine_cell_count = 0;
    long long tag_cluster_count = 0;
    long long tag_candidate_level1_cell_count = 0;
};

inline const char* concentration_basis_name(int basis)
{
    return basis == BasisVolumeFraction ? "volume_fraction" : "mass_fraction";
}

inline int parse_concentration_basis(const std::string& name)
{
    if (name == "mass_fraction") {
        return BasisMassFraction;
    }
    if (name == "volume_fraction") {
        return BasisVolumeFraction;
    }
    return -1;
}

inline const char* porosity_type_name(int type)
{
    return type == PorosityCylinder ? "cylinder" : "box";
}

inline int parse_porosity_type(const std::string& name)
{
    if (name == "box") {
        return PorosityBox;
    }
    if (name == "cylinder") {
        return PorosityCylinder;
    }
    return -1;
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real leak_volume_fraction(amrex::Real y_leak,
                                 amrex::Real leak_mw,
                                 amrex::Real air_mw) noexcept
{
    if (y_leak <= 0.0) {
        return 0.0;
    }
    if (y_leak >= 1.0) {
        return 1.0;
    }
    const amrex::Real leak_moles = y_leak / leak_mw;
    const amrex::Real air_moles = (1.0 - y_leak) / air_mw;
    return leak_moles / (leak_moles + air_moles);
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real diagnostic_concentration(amrex::Real y_leak,
                                     int basis,
                                     amrex::Real leak_mw,
                                     amrex::Real air_mw) noexcept
{
    return basis == BasisVolumeFraction
        ? leak_volume_fraction(y_leak, leak_mw, air_mw)
        : y_leak;
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real smoothstep01(amrex::Real x) noexcept
{
    if (x <= 0.0) {
        return 0.0;
    }
    if (x >= 1.0) {
        return 1.0;
    }
    return x * x * (3.0 - 2.0 * x);
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real porosity_at(amrex::Real x,
                        amrex::Real y,
                        amrex::Real z,
                        const KernelParams& params) noexcept
{
    if (params.porosity_enabled == 0) {
        return 1.0;
    }

    const amrex::Real p[AMREX_SPACEDIM] = {AMREX_D_DECL(x, y, z)};
    if (params.porosity_type == PorosityCylinder) {
        const int axis = params.porosity_cylinder_axis;
        const int r0 = (axis + 1) % AMREX_SPACEDIM;
        const int r1 = (axis + 2) % AMREX_SPACEDIM;
        const amrex::Real radial0 = p[r0] - params.porosity_cylinder_center[r0];
        const amrex::Real radial1 = p[r1] - params.porosity_cylinder_center[r1];
        const amrex::Real radial_distance =
            std::sqrt(radial0 * radial0 + radial1 * radial1);
        const bool inside_radial = radial_distance <= params.porosity_cylinder_radius;
        const bool inside_axis = p[axis] >= params.porosity_cylinder_axis_lo
                              && p[axis] <= params.porosity_cylinder_axis_hi;
        if (inside_radial && inside_axis) {
            return params.porosity_solid_value;
        }

        const amrex::Real radial_delta =
            radial_distance > params.porosity_cylinder_radius
                ? radial_distance - params.porosity_cylinder_radius
                : 0.0;
        amrex::Real axis_delta = 0.0;
        if (p[axis] < params.porosity_cylinder_axis_lo) {
            axis_delta = params.porosity_cylinder_axis_lo - p[axis];
        } else if (p[axis] > params.porosity_cylinder_axis_hi) {
            axis_delta = p[axis] - params.porosity_cylinder_axis_hi;
        }
        const amrex::Real outside_distance =
            std::sqrt(radial_delta * radial_delta + axis_delta * axis_delta);
        if (params.porosity_transition <= 0.0
            || outside_distance >= params.porosity_transition) {
            return 1.0;
        }
        const amrex::Real blend = smoothstep01(outside_distance / params.porosity_transition);
        return params.porosity_solid_value
            + (1.0 - params.porosity_solid_value) * blend;
    }

    amrex::Real outside_distance = 0.0;
    bool inside = true;
    for (int d = 0; d < AMREX_SPACEDIM; ++d) {
        amrex::Real delta = 0.0;
        if (p[d] < params.porosity_box_lo[d]) {
            delta = params.porosity_box_lo[d] - p[d];
            inside = false;
        } else if (p[d] > params.porosity_box_hi[d]) {
            delta = p[d] - params.porosity_box_hi[d];
            inside = false;
        }
        outside_distance += delta * delta;
    }
    if (inside) {
        return params.porosity_solid_value;
    }
    outside_distance = std::sqrt(outside_distance);
    if (params.porosity_transition <= 0.0
        || outside_distance >= params.porosity_transition) {
        return 1.0;
    }
    const amrex::Real blend = smoothstep01(outside_distance / params.porosity_transition);
    return params.porosity_solid_value
        + (1.0 - params.porosity_solid_value) * blend;
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real velocity_factor_from_porosity(amrex::Real porosity,
                                          const KernelParams& params) noexcept
{
    if (params.porosity_enabled == 0) {
        return 1.0;
    }
    if (porosity <= 0.0) {
        return 0.0;
    }
    const amrex::Real drag = params.porosity_resistance * (1.0 - porosity);
    return porosity / (porosity + drag);
}

inline void fill_kernel_params(KernelParams& kparams, const RuntimeParams& params)
{
    kparams.dt = params.dt;
    kparams.diffusion = params.diffusion;
    kparams.rho0 = params.rho0;
    kparams.inlet_y = params.inlet_y;
    kparams.ambient_y = params.ambient_y;
    kparams.source_sigma = params.source_sigma;
    kparams.source_strength = params.source_strength;
    kparams.source_type = params.source_type;
    kparams.porosity_enabled = params.porosity_enabled;
    kparams.porosity_type = params.porosity_type;
    kparams.porosity_cylinder_radius = params.porosity_cylinder_radius;
    kparams.porosity_cylinder_axis = params.porosity_cylinder_axis;
    kparams.porosity_cylinder_axis_lo = params.porosity_cylinder_axis_lo;
    kparams.porosity_cylinder_axis_hi = params.porosity_cylinder_axis_hi;
    kparams.porosity_transition = params.porosity_transition;
    kparams.porosity_solid_value = params.porosity_solid_value;
    kparams.porosity_resistance = params.porosity_resistance;
    for (int d = 0; d < AMREX_SPACEDIM; ++d) {
        kparams.wind[d] = params.wind[d];
        kparams.source_center[d] = params.source_center[d];
        kparams.source_box_lo[d] = params.source_box_lo[d];
        kparams.source_box_hi[d] = params.source_box_hi[d];
        kparams.porosity_box_lo[d] = params.porosity_box_lo[d];
        kparams.porosity_box_hi[d] = params.porosity_box_hi[d];
        kparams.porosity_cylinder_center[d] = params.porosity_cylinder_center[d];
        kparams.bc_lo[d] = params.bc_lo[d];
        kparams.bc_hi[d] = params.bc_hi[d];
    }
}

} // namespace amrreactx
