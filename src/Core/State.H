#pragma once

#include <AMReX_GpuQualifiers.H>
#include <AMReX_REAL.H>
#include <AMReX_SPACE.H>

#include <string>

namespace amrreactx {

enum StateIndex {
    Rho = 0,
    Uvel,
    Vvel,
    Wvel,
    YLeak,
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

enum DiagIndex {
    SourceRate = 0,
    OutletRate,
    XMoment,
    YMoment,
    ZMoment,
    CloudIndicator,
    FlammableIndicator,
    NumDiag
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
    amrex::Real wind[AMREX_SPACEDIM] = {AMREX_D_DECL(1.0, 0.0, 0.0)};
    amrex::Real source_center[AMREX_SPACEDIM] = {AMREX_D_DECL(1.0, 2.0, 2.0)};
    amrex::Real source_box_lo[AMREX_SPACEDIM] = {AMREX_D_DECL(0.9, 1.9, 1.9)};
    amrex::Real source_box_hi[AMREX_SPACEDIM] = {AMREX_D_DECL(1.1, 2.1, 2.1)};
    amrex::Real source_sigma = 0.15;
    amrex::Real source_strength = 0.2;
    int source_type = SourceGaussian;
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
    std::string history_file = "history.csv";
    std::string plotfile_prefix = "plt_leak";
};

struct KernelParams {
    amrex::Real dt;
    amrex::Real diffusion;
    amrex::Real rho0;
    amrex::Real inlet_y;
    amrex::Real wind[AMREX_SPACEDIM];
    amrex::Real source_center[AMREX_SPACEDIM];
    amrex::Real source_box_lo[AMREX_SPACEDIM];
    amrex::Real source_box_hi[AMREX_SPACEDIM];
    amrex::Real source_sigma;
    amrex::Real source_strength;
    int source_type;
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

inline void fill_kernel_params(KernelParams& kparams, const RuntimeParams& params)
{
    kparams.dt = params.dt;
    kparams.diffusion = params.diffusion;
    kparams.rho0 = params.rho0;
    kparams.inlet_y = params.inlet_y;
    kparams.source_sigma = params.source_sigma;
    kparams.source_strength = params.source_strength;
    kparams.source_type = params.source_type;
    for (int d = 0; d < AMREX_SPACEDIM; ++d) {
        kparams.wind[d] = params.wind[d];
        kparams.source_center[d] = params.source_center[d];
        kparams.source_box_lo[d] = params.source_box_lo[d];
        kparams.source_box_hi[d] = params.source_box_hi[d];
        kparams.bc_lo[d] = params.bc_lo[d];
        kparams.bc_hi[d] = params.bc_hi[d];
    }
}

} // namespace amrreactx
