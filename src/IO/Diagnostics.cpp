#include "IO/Diagnostics.H"

#include "AMR/BoundaryConditions.H"
#include "AMR/Hierarchy.H"
#include "AMR/Tagging.H"
#include "Physics/SourceTerms.H"

#include <AMReX_Array4.H>
#include <AMReX_Box.H>
#include <AMReX_DistributionMapping.H>
#include <AMReX_MFIter.H>
#include <AMReX_ParallelDescriptor.H>
#include <AMReX_PlotFileUtil.H>
#include <AMReX_Vector.H>

#include <cmath>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <string>

namespace amrreactx {

namespace {

std::string plotfile_name(const std::string& prefix, int step)
{
    std::ostringstream os;
    os << prefix << std::setw(5) << std::setfill('0') << step;
    return os.str();
}

amrex::Vector<std::string> plot_var_names()
{
    return {"rho", "u", "v", "w", "Y_leak", "C_leak_diag",
            "tag_grad_y", "tag_source", "tag_refine"};
}

void fill_diagnostic_plot_components(amrex::MultiFab& plot_state,
                                     const RuntimeParams& params)
{
    for (amrex::MFIter mfi(plot_state); mfi.isValid(); ++mfi) {
        const amrex::Box& bx = mfi.validbox();
        const amrex::Array4<amrex::Real> p = plot_state.array(mfi);
        const int basis = params.diagnostic_basis;
        const amrex::Real leak_mw = params.leak_molecular_weight;
        const amrex::Real air_mw = params.air_molecular_weight;

        amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
            p(i, j, k, NumState) = diagnostic_concentration(p(i, j, k, YLeak),
                                                            basis, leak_mw, air_mw);
        });
    }
}

void fill_level1_bounds(TransportDiagnostics& diag,
                        const ScalarAmrHierarchy& hierarchy)
{
    if (!hierarchy.has_level1()) {
        return;
    }

    amrex::Box level1_box = hierarchy.level1_box_array.minimalBox();
    level1_box &= hierarchy.level1_geom.Domain();
    const auto prob_lo = hierarchy.level1_geom.ProbLoArray();
    const auto dx = hierarchy.level1_geom.CellSizeArray();
    const auto lo = level1_box.smallEnd();
    const auto hi = level1_box.bigEnd();
    diag.amr_level1_x_min = prob_lo[0] + static_cast<amrex::Real>(lo[0]) * dx[0];
    diag.amr_level1_x_max = prob_lo[0] + static_cast<amrex::Real>(hi[0] + 1) * dx[0];
    diag.amr_level1_y_min = prob_lo[1] + static_cast<amrex::Real>(lo[1]) * dx[1];
    diag.amr_level1_y_max = prob_lo[1] + static_cast<amrex::Real>(hi[1] + 1) * dx[1];
    diag.amr_level1_z_min = prob_lo[2] + static_cast<amrex::Real>(lo[2]) * dx[2];
    diag.amr_level1_z_max = prob_lo[2] + static_cast<amrex::Real>(hi[2] + 1) * dx[2];
}

} // namespace

amrex::Real scalar_mass(const amrex::MultiFab& state,
                        const amrex::Geometry& geom,
                        const RuntimeParams& params)
{
    const auto dx = geom.CellSizeArray();
    const amrex::Real cell_volume = AMREX_D_TERM(dx[0], * dx[1], * dx[2]);
    return params.rho0 * state.sum(YLeak) * cell_volume;
}

TransportDiagnostics compute_diagnostics(const amrex::MultiFab& state,
                                         amrex::MultiFab& diag,
                                         const amrex::Geometry& geom,
                                         const RuntimeParams& params)
{
    const auto dx = geom.CellSizeArray();
    const auto prob_lo = geom.ProbLoArray();
    const auto dom_lo = geom.Domain().smallEnd();
    const auto dom_hi = geom.Domain().bigEnd();
    const amrex::Real cell_volume = AMREX_D_TERM(dx[0], * dx[1], * dx[2]);
    const int diagnostic_basis = params.diagnostic_basis;
    const amrex::Real leak_mw = params.leak_molecular_weight;
    const amrex::Real air_mw = params.air_molecular_weight;
    const amrex::Real cloud_threshold = params.cloud_threshold;
    const amrex::Real lel = params.lel;
    const amrex::Real uel = params.uel;
    const amrex::Real face_area[AMREX_SPACEDIM] = {
        AMREX_D_DECL(dx[1] * dx[2], dx[0] * dx[2], dx[0] * dx[1])
    };
    const amrex::Real rho0 = params.rho0;
    KernelParams kparams{};
    fill_kernel_params(kparams, params);

    diag.setVal(0.0);
    for (amrex::MFIter mfi(state); mfi.isValid(); ++mfi) {
        const amrex::Box& bx = mfi.validbox();
        const amrex::Array4<const amrex::Real> s = state.const_array(mfi);
        const amrex::Array4<amrex::Real> d = diag.array(mfi);

        amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE(int i, int j, int k) noexcept {
            const amrex::Real x = prob_lo[0] + (static_cast<amrex::Real>(i) + 0.5) * dx[0];
            const amrex::Real y = prob_lo[1] + (static_cast<amrex::Real>(j) + 0.5) * dx[1];
            const amrex::Real z = prob_lo[2] + (static_cast<amrex::Real>(k) + 0.5) * dx[2];
            const amrex::Real y_leak = s(i, j, k, YLeak);
            const amrex::Real concentration =
                diagnostic_concentration(y_leak, diagnostic_basis, leak_mw, air_mw);

            const amrex::Real source = scalar_source(x, y, z, kparams);

            d(i, j, k, SourceRate) = rho0 * source;
            d(i, j, k, OutletRate) = 0.0;
            d(i, j, k, OutletXLoRate) = 0.0;
            d(i, j, k, OutletXHiRate) = 0.0;
            d(i, j, k, OutletYLoRate) = 0.0;
            d(i, j, k, OutletYHiRate) = 0.0;
            d(i, j, k, OutletZLoRate) = 0.0;
            d(i, j, k, OutletZHiRate) = 0.0;
            d(i, j, k, InflowRate) = 0.0;
            d(i, j, k, InflowXLoRate) = 0.0;
            d(i, j, k, InflowXHiRate) = 0.0;
            d(i, j, k, InflowYLoRate) = 0.0;
            d(i, j, k, InflowYHiRate) = 0.0;
            d(i, j, k, InflowZLoRate) = 0.0;
            d(i, j, k, InflowZHiRate) = 0.0;
            if (i == dom_lo[0] && kparams.wind[0] < 0.0 && kparams.bc_lo[0] != BcWall) {
                d(i, j, k, OutletXLoRate) = rho0 * (-kparams.wind[0]) * y_leak * face_area[0] / cell_volume;
            }
            if (i == dom_lo[0] && kparams.wind[0] > 0.0 && kparams.bc_lo[0] != BcWall) {
                const amrex::Real exterior_y = boundary_advective_y(y_leak, kparams.bc_lo[0], kparams);
                d(i, j, k, InflowXLoRate) = rho0 * kparams.wind[0] * exterior_y * face_area[0] / cell_volume;
            }
            if (i == dom_hi[0] && kparams.wind[0] > 0.0 && kparams.bc_hi[0] != BcWall) {
                d(i, j, k, OutletXHiRate) = rho0 * kparams.wind[0] * y_leak * face_area[0] / cell_volume;
            }
            if (i == dom_hi[0] && kparams.wind[0] < 0.0 && kparams.bc_hi[0] != BcWall) {
                const amrex::Real exterior_y = boundary_advective_y(y_leak, kparams.bc_hi[0], kparams);
                d(i, j, k, InflowXHiRate) = rho0 * (-kparams.wind[0]) * exterior_y * face_area[0] / cell_volume;
            }
            if (j == dom_lo[1] && kparams.wind[1] < 0.0 && kparams.bc_lo[1] != BcWall) {
                d(i, j, k, OutletYLoRate) = rho0 * (-kparams.wind[1]) * y_leak * face_area[1] / cell_volume;
            }
            if (j == dom_lo[1] && kparams.wind[1] > 0.0 && kparams.bc_lo[1] != BcWall) {
                const amrex::Real exterior_y = boundary_advective_y(y_leak, kparams.bc_lo[1], kparams);
                d(i, j, k, InflowYLoRate) = rho0 * kparams.wind[1] * exterior_y * face_area[1] / cell_volume;
            }
            if (j == dom_hi[1] && kparams.wind[1] > 0.0 && kparams.bc_hi[1] != BcWall) {
                d(i, j, k, OutletYHiRate) = rho0 * kparams.wind[1] * y_leak * face_area[1] / cell_volume;
            }
            if (j == dom_hi[1] && kparams.wind[1] < 0.0 && kparams.bc_hi[1] != BcWall) {
                const amrex::Real exterior_y = boundary_advective_y(y_leak, kparams.bc_hi[1], kparams);
                d(i, j, k, InflowYHiRate) = rho0 * (-kparams.wind[1]) * exterior_y * face_area[1] / cell_volume;
            }
            if (k == dom_lo[2] && kparams.wind[2] < 0.0 && kparams.bc_lo[2] != BcWall) {
                d(i, j, k, OutletZLoRate) = rho0 * (-kparams.wind[2]) * y_leak * face_area[2] / cell_volume;
            }
            if (k == dom_lo[2] && kparams.wind[2] > 0.0 && kparams.bc_lo[2] != BcWall) {
                const amrex::Real exterior_y = boundary_advective_y(y_leak, kparams.bc_lo[2], kparams);
                d(i, j, k, InflowZLoRate) = rho0 * kparams.wind[2] * exterior_y * face_area[2] / cell_volume;
            }
            if (k == dom_hi[2] && kparams.wind[2] > 0.0 && kparams.bc_hi[2] != BcWall) {
                d(i, j, k, OutletZHiRate) = rho0 * kparams.wind[2] * y_leak * face_area[2] / cell_volume;
            }
            if (k == dom_hi[2] && kparams.wind[2] < 0.0 && kparams.bc_hi[2] != BcWall) {
                const amrex::Real exterior_y = boundary_advective_y(y_leak, kparams.bc_hi[2], kparams);
                d(i, j, k, InflowZHiRate) = rho0 * (-kparams.wind[2]) * exterior_y * face_area[2] / cell_volume;
            }
            d(i, j, k, OutletRate) = d(i, j, k, OutletXLoRate)
                                   + d(i, j, k, OutletXHiRate)
                                   + d(i, j, k, OutletYLoRate)
                                   + d(i, j, k, OutletYHiRate)
                                   + d(i, j, k, OutletZLoRate)
                                   + d(i, j, k, OutletZHiRate);
            d(i, j, k, InflowRate) = d(i, j, k, InflowXLoRate)
                                   + d(i, j, k, InflowXHiRate)
                                   + d(i, j, k, InflowYLoRate)
                                   + d(i, j, k, InflowYHiRate)
                                   + d(i, j, k, InflowZLoRate)
                                   + d(i, j, k, InflowZHiRate);
            d(i, j, k, XMoment) = rho0 * y_leak * x;
            d(i, j, k, YMoment) = rho0 * y_leak * y;
            d(i, j, k, ZMoment) = rho0 * y_leak * z;
            d(i, j, k, CloudIndicator) = concentration >= cloud_threshold ? 1.0 : 0.0;
            d(i, j, k, FlammableIndicator) =
                (concentration >= lel && concentration <= uel) ? 1.0 : 0.0;
            d(i, j, k, CloudMassDensity) = d(i, j, k, CloudIndicator) * rho0 * y_leak;
            d(i, j, k, FlammableMassDensity) = d(i, j, k, FlammableIndicator) * rho0 * y_leak;
            d(i, j, k, CloudConcentrationSum) = d(i, j, k, CloudIndicator) * concentration;
            d(i, j, k, FlammableConcentrationSum) = d(i, j, k, FlammableIndicator) * concentration;
        });
    }

    TransportDiagnostics out;
    out.scalar_mass = scalar_mass(state, geom, params);
    out.source_rate = diag.sum(SourceRate) * cell_volume;
    out.outlet_rate = diag.sum(OutletRate) * cell_volume;
    out.outlet_xlo_rate = diag.sum(OutletXLoRate) * cell_volume;
    out.outlet_xhi_rate = diag.sum(OutletXHiRate) * cell_volume;
    out.outlet_ylo_rate = diag.sum(OutletYLoRate) * cell_volume;
    out.outlet_yhi_rate = diag.sum(OutletYHiRate) * cell_volume;
    out.outlet_zlo_rate = diag.sum(OutletZLoRate) * cell_volume;
    out.outlet_zhi_rate = diag.sum(OutletZHiRate) * cell_volume;
    out.boundary_inflow_rate = diag.sum(InflowRate) * cell_volume;
    out.inflow_xlo_rate = diag.sum(InflowXLoRate) * cell_volume;
    out.inflow_xhi_rate = diag.sum(InflowXHiRate) * cell_volume;
    out.inflow_ylo_rate = diag.sum(InflowYLoRate) * cell_volume;
    out.inflow_yhi_rate = diag.sum(InflowYHiRate) * cell_volume;
    out.inflow_zlo_rate = diag.sum(InflowZLoRate) * cell_volume;
    out.inflow_zhi_rate = diag.sum(InflowZHiRate) * cell_volume;
    const amrex::Real x_moment = diag.sum(XMoment) * cell_volume;
    const amrex::Real y_moment = diag.sum(YMoment) * cell_volume;
    const amrex::Real z_moment = diag.sum(ZMoment) * cell_volume;
    if (out.scalar_mass > 0.0) {
        out.x_centroid = x_moment / out.scalar_mass;
        out.y_centroid = y_moment / out.scalar_mass;
        out.z_centroid = z_moment / out.scalar_mass;
    }
    out.max_y = state.norm0(YLeak);
    out.max_concentration = diagnostic_concentration(out.max_y,
                                                     params.diagnostic_basis,
                                                     params.leak_molecular_weight,
                                                     params.air_molecular_weight);
    amrex::Real max_location[AMREX_SPACEDIM] = {
        AMREX_D_DECL(std::numeric_limits<amrex::Real>::max(),
                     std::numeric_limits<amrex::Real>::max(),
                     std::numeric_limits<amrex::Real>::max())
    };
    amrex::Real cloud_min[AMREX_SPACEDIM] = {
        AMREX_D_DECL(std::numeric_limits<amrex::Real>::max(),
                     std::numeric_limits<amrex::Real>::max(),
                     std::numeric_limits<amrex::Real>::max())
    };
    amrex::Real cloud_max[AMREX_SPACEDIM] = {
        AMREX_D_DECL(-std::numeric_limits<amrex::Real>::max(),
                     -std::numeric_limits<amrex::Real>::max(),
                     -std::numeric_limits<amrex::Real>::max())
    };
    amrex::Real flammable_min[AMREX_SPACEDIM] = {
        AMREX_D_DECL(std::numeric_limits<amrex::Real>::max(),
                     std::numeric_limits<amrex::Real>::max(),
                     std::numeric_limits<amrex::Real>::max())
    };
    amrex::Real flammable_max[AMREX_SPACEDIM] = {
        AMREX_D_DECL(-std::numeric_limits<amrex::Real>::max(),
                     -std::numeric_limits<amrex::Real>::max(),
                     -std::numeric_limits<amrex::Real>::max())
    };
    const amrex::Real max_tol = std::max(amrex::Real(1.0e-14), std::abs(out.max_y) * amrex::Real(1.0e-12));
    for (amrex::MFIter mfi(state); mfi.isValid(); ++mfi) {
        const amrex::Box& bx = mfi.validbox();
        const amrex::Array4<const amrex::Real> s = state.const_array(mfi);
        const auto lo = bx.smallEnd();
        const auto hi = bx.bigEnd();
        for (int k = lo[2]; k <= hi[2]; ++k) {
            for (int j = lo[1]; j <= hi[1]; ++j) {
                for (int i = lo[0]; i <= hi[0]; ++i) {
                    if (std::abs(s(i, j, k, YLeak) - out.max_y) <= max_tol) {
                        const amrex::Real x = prob_lo[0] + (static_cast<amrex::Real>(i) + 0.5) * dx[0];
                        const amrex::Real y = prob_lo[1] + (static_cast<amrex::Real>(j) + 0.5) * dx[1];
                        const amrex::Real z = prob_lo[2] + (static_cast<amrex::Real>(k) + 0.5) * dx[2];
                        if (x < max_location[0]
                            || (x == max_location[0] && y < max_location[1])
                            || (x == max_location[0] && y == max_location[1] && z < max_location[2])) {
                            max_location[0] = x;
                            max_location[1] = y;
                            max_location[2] = z;
                        }
                    }
                    const amrex::Real x = prob_lo[0] + (static_cast<amrex::Real>(i) + 0.5) * dx[0];
                    const amrex::Real y = prob_lo[1] + (static_cast<amrex::Real>(j) + 0.5) * dx[1];
                    const amrex::Real z = prob_lo[2] + (static_cast<amrex::Real>(k) + 0.5) * dx[2];
                    const amrex::Real concentration =
                        diagnostic_concentration(s(i, j, k, YLeak),
                                                 params.diagnostic_basis,
                                                 params.leak_molecular_weight,
                                                 params.air_molecular_weight);
                    if (concentration >= params.cloud_threshold) {
                        cloud_min[0] = std::min(cloud_min[0], x);
                        cloud_min[1] = std::min(cloud_min[1], y);
                        cloud_min[2] = std::min(cloud_min[2], z);
                        cloud_max[0] = std::max(cloud_max[0], x);
                        cloud_max[1] = std::max(cloud_max[1], y);
                        cloud_max[2] = std::max(cloud_max[2], z);
                    }
                    if (concentration >= params.lel && concentration <= params.uel) {
                        flammable_min[0] = std::min(flammable_min[0], x);
                        flammable_min[1] = std::min(flammable_min[1], y);
                        flammable_min[2] = std::min(flammable_min[2], z);
                        flammable_max[0] = std::max(flammable_max[0], x);
                        flammable_max[1] = std::max(flammable_max[1], y);
                        flammable_max[2] = std::max(flammable_max[2], z);
                    }
                }
            }
        }
    }
    amrex::ParallelDescriptor::ReduceRealMin(max_location, AMREX_SPACEDIM);
    amrex::ParallelDescriptor::ReduceRealMin(cloud_min, AMREX_SPACEDIM);
    amrex::ParallelDescriptor::ReduceRealMax(cloud_max, AMREX_SPACEDIM);
    amrex::ParallelDescriptor::ReduceRealMin(flammable_min, AMREX_SPACEDIM);
    amrex::ParallelDescriptor::ReduceRealMax(flammable_max, AMREX_SPACEDIM);
    if (max_location[0] < std::numeric_limits<amrex::Real>::max()) {
        out.max_y_x = max_location[0];
        out.max_y_y = max_location[1];
        out.max_y_z = max_location[2];
    }
    out.cloud_volume = diag.sum(CloudIndicator) * cell_volume;
    out.flammable_volume = diag.sum(FlammableIndicator) * cell_volume;
    out.cloud_mass = diag.sum(CloudMassDensity) * cell_volume;
    out.flammable_mass = diag.sum(FlammableMassDensity) * cell_volume;
    if (out.cloud_volume > 0.0) {
        out.cloud_mean_concentration =
            diag.sum(CloudConcentrationSum) * cell_volume / out.cloud_volume;
    }
    if (out.flammable_volume > 0.0) {
        out.flammable_mean_concentration =
            diag.sum(FlammableConcentrationSum) * cell_volume / out.flammable_volume;
    }
    if (out.cloud_volume > 0.0) {
        out.cloud_x_min = cloud_min[0];
        out.cloud_x_max = cloud_max[0];
        out.cloud_y_min = cloud_min[1];
        out.cloud_y_max = cloud_max[1];
        out.cloud_z_min = cloud_min[2];
        out.cloud_z_max = cloud_max[2];
    }
    if (out.flammable_volume > 0.0) {
        out.flammable_x_min = flammable_min[0];
        out.flammable_x_max = flammable_max[0];
        out.flammable_y_min = flammable_min[1];
        out.flammable_y_max = flammable_max[1];
        out.flammable_z_min = flammable_min[2];
        out.flammable_z_max = flammable_max[2];
    }
    if (params.tagging_enabled != 0) {
        amrex::MultiFab tags(state.boxArray(), state.DistributionMap(), NumTag, 0);
        fill_tagging_indicators(state, tags, geom, params);
        out.tag_grad_y_volume = tags.sum(GradYTag) * cell_volume;
        out.tag_source_volume = tags.sum(SourceRegionTag) * cell_volume;
        out.tag_refine_volume = tags.sum(RefineTag) * cell_volume;
        const AmrTaggingSummary tag_summary = build_candidate_level1_grids(tags, geom, params);
        out.tag_refine_cell_count = tag_summary.refine_cell_count;
        out.tag_cluster_count = tag_summary.cluster_count;
        out.tag_candidate_level1_cell_count = tag_summary.candidate_level1_cell_count;
        out.tag_candidate_level1_volume = tag_summary.candidate_level1_volume;
    }
    return out;
}

void print_stability_report(const StabilityInfo& info)
{
    amrex::Print() << "stability adv_cfl_sum " << info.advective_cfl
                   << " max_dir_cfl " << info.max_directional_cfl
                   << " diffusion_number " << info.diffusion_number
                   << " dt_adv_limit " << info.dt_advective_limit
                   << " dt_diff_limit " << info.dt_diffusion_limit
                   << " recommended_dt " << info.recommended_dt << "\n";
    if (info.advective_cfl > 1.0) {
        amrex::Print() << "WARNING: advective CFL sum exceeds 1.0 for the current explicit upwind update.\n";
    }
    if (info.diffusion_number > 0.5) {
        amrex::Print() << "WARNING: diffusion number exceeds 0.5 for the current explicit diffusion update.\n";
    }
}

void print_boundary_report(const RuntimeParams& params)
{
    amrex::Print() << "scalar_bc lo "
                   << boundary_type_name(params.bc_lo[0]) << " "
                   << boundary_type_name(params.bc_lo[1]) << " "
                   << boundary_type_name(params.bc_lo[2])
                   << " hi "
                   << boundary_type_name(params.bc_hi[0]) << " "
                   << boundary_type_name(params.bc_hi[1]) << " "
                   << boundary_type_name(params.bc_hi[2])
                   << " inlet_y " << params.inlet_y
                   << " ambient_y " << params.ambient_y << "\n";
}

void print_source_report(const RuntimeParams& params)
{
    amrex::Print() << "scalar_source type " << source_type_name(params.source_type)
                   << " strength " << params.source_strength
                   << " total_rate " << params.source_total_rate
                   << " center " << params.source_center[0]
                   << " " << params.source_center[1]
                   << " " << params.source_center[2]
                   << " sigma " << params.source_sigma
                   << " box_lo " << params.source_box_lo[0]
                   << " " << params.source_box_lo[1]
                   << " " << params.source_box_lo[2]
                   << " box_hi " << params.source_box_hi[0]
                   << " " << params.source_box_hi[1]
                   << " " << params.source_box_hi[2] << "\n";
}

void print_concentration_report(const RuntimeParams& params)
{
    amrex::Print() << "engineering_diagnostics basis "
                   << concentration_basis_name(params.diagnostic_basis)
                   << " cloud_threshold " << params.cloud_threshold
                   << " lel " << params.lel
                   << " uel " << params.uel
                   << " leak_molecular_weight " << params.leak_molecular_weight
                   << " air_molecular_weight " << params.air_molecular_weight << "\n";
}

void print_tagging_report(const RuntimeParams& params)
{
    amrex::Print() << "amr_tagging enabled " << params.tagging_enabled
                   << " tag_grad_y " << params.tag_grad_y
                   << " tag_source_region " << params.tag_source_region
                   << " tag_source_radius " << params.tag_source_radius
                   << " tag_source_box_buffer " << params.tag_source_box_buffer
                   << " tag_buffer " << params.tag_buffer
                   << " tag_ref_ratio " << params.tag_ref_ratio
                   << " tag_max_grid_size " << params.tag_max_grid_size
                   << " tag_grid_efficiency " << params.tag_grid_efficiency
                   << " amr_regrid_interval " << params.amr_regrid_interval
                   << " amr_restrict_after_advance "
                   << params.amr_restrict_after_advance
                   << " amr_reflux_after_advance "
                   << params.amr_reflux_after_advance << "\n";
}

void initialize_history_file(const RuntimeParams& params)
{
    if (!amrex::ParallelDescriptor::IOProcessor()) {
        return;
    }
    std::ofstream history(params.history_file);
    history << "step,time,mass,injected,boundary_inflow,outlet,balance_error,"
            << "source_rate,boundary_inflow_rate,outlet_rate,max_Y,"
            << "max_Y_x,max_Y_y,max_Y_z,max_concentration,centroid_x,centroid_y,centroid_z,"
            << "inflow_xlo_rate,inflow_xhi_rate,inflow_ylo_rate,inflow_yhi_rate,"
            << "inflow_zlo_rate,inflow_zhi_rate,"
            << "outlet_xlo_rate,outlet_xhi_rate,outlet_ylo_rate,outlet_yhi_rate,"
            << "outlet_zlo_rate,outlet_zhi_rate,"
            << "cloud_volume,cloud_mass,cloud_mean_concentration,"
            << "cloud_x_min,cloud_x_max,cloud_y_min,cloud_y_max,cloud_z_min,cloud_z_max,"
            << "flammable_volume,flammable_mass,flammable_mean_concentration,"
            << "flammable_x_min,flammable_x_max,flammable_y_min,flammable_y_max,"
            << "flammable_z_min,flammable_z_max,"
            << "tag_grad_y_volume,tag_source_volume,tag_refine_volume,"
            << "tag_refine_cell_count,tag_cluster_count,"
            << "tag_candidate_level1_cell_count,tag_candidate_level1_volume,"
            << "amr_level1_x_min,amr_level1_x_max,"
            << "amr_level1_y_min,amr_level1_y_max,"
            << "amr_level1_z_min,amr_level1_z_max,"
            << "amr_restrict_max_abs_y_error,amr_restrict_l1_y_error,"
            << "amr_restrict_coarse_cell_count,amr_level1_mass,"
            << "amr_covered_level0_mass,amr_mass_delta,"
            << "amr_applied_restriction_mass_delta,"
            << "amr_applied_reflux_mass_delta,"
            << "amr_cumulative_restriction_mass_delta,"
            << "amr_cumulative_reflux_mass_delta,"
            << "amr_cf_advective_flux_mismatch,"
            << "amr_cf_advective_abs_mismatch,"
            << "amr_cf_diffusive_flux_mismatch,"
            << "amr_cf_diffusive_abs_mismatch,"
            << "amr_cf_advective_mismatch_mass,"
            << "amr_cf_advective_abs_mismatch_mass,"
            << "amr_cf_diffusive_mismatch_mass,"
            << "amr_cf_diffusive_abs_mismatch_mass,"
            << "amr_cf_interface_face_count,"
            << "amr_cf_advective_flux_mismatch_xlo,"
            << "amr_cf_advective_flux_mismatch_xhi,"
            << "amr_cf_advective_flux_mismatch_ylo,"
            << "amr_cf_advective_flux_mismatch_yhi,"
            << "amr_cf_advective_flux_mismatch_zlo,"
            << "amr_cf_advective_flux_mismatch_zhi,"
            << "amr_cf_advective_abs_mismatch_xlo,"
            << "amr_cf_advective_abs_mismatch_xhi,"
            << "amr_cf_advective_abs_mismatch_ylo,"
            << "amr_cf_advective_abs_mismatch_yhi,"
            << "amr_cf_advective_abs_mismatch_zlo,"
            << "amr_cf_advective_abs_mismatch_zhi,"
            << "amr_cf_diffusive_flux_mismatch_xlo,"
            << "amr_cf_diffusive_flux_mismatch_xhi,"
            << "amr_cf_diffusive_flux_mismatch_ylo,"
            << "amr_cf_diffusive_flux_mismatch_yhi,"
            << "amr_cf_diffusive_flux_mismatch_zlo,"
            << "amr_cf_diffusive_flux_mismatch_zhi,"
            << "amr_cf_diffusive_abs_mismatch_xlo,"
            << "amr_cf_diffusive_abs_mismatch_xhi,"
            << "amr_cf_diffusive_abs_mismatch_ylo,"
            << "amr_cf_diffusive_abs_mismatch_yhi,"
            << "amr_cf_diffusive_abs_mismatch_zlo,"
            << "amr_cf_diffusive_abs_mismatch_zhi,"
            << "amr_cf_advective_mismatch_mass_xlo,"
            << "amr_cf_advective_mismatch_mass_xhi,"
            << "amr_cf_advective_mismatch_mass_ylo,"
            << "amr_cf_advective_mismatch_mass_yhi,"
            << "amr_cf_advective_mismatch_mass_zlo,"
            << "amr_cf_advective_mismatch_mass_zhi,"
            << "amr_cf_advective_abs_mismatch_mass_xlo,"
            << "amr_cf_advective_abs_mismatch_mass_xhi,"
            << "amr_cf_advective_abs_mismatch_mass_ylo,"
            << "amr_cf_advective_abs_mismatch_mass_yhi,"
            << "amr_cf_advective_abs_mismatch_mass_zlo,"
            << "amr_cf_advective_abs_mismatch_mass_zhi,"
            << "amr_cf_diffusive_mismatch_mass_xlo,"
            << "amr_cf_diffusive_mismatch_mass_xhi,"
            << "amr_cf_diffusive_mismatch_mass_ylo,"
            << "amr_cf_diffusive_mismatch_mass_yhi,"
            << "amr_cf_diffusive_mismatch_mass_zlo,"
            << "amr_cf_diffusive_mismatch_mass_zhi,"
            << "amr_cf_diffusive_abs_mismatch_mass_xlo,"
            << "amr_cf_diffusive_abs_mismatch_mass_xhi,"
            << "amr_cf_diffusive_abs_mismatch_mass_ylo,"
            << "amr_cf_diffusive_abs_mismatch_mass_yhi,"
            << "amr_cf_diffusive_abs_mismatch_mass_zlo,"
            << "amr_cf_diffusive_abs_mismatch_mass_zhi,"
            << "amr_cf_interface_face_count_xlo,"
            << "amr_cf_interface_face_count_xhi,"
            << "amr_cf_interface_face_count_ylo,"
            << "amr_cf_interface_face_count_yhi,"
            << "amr_cf_interface_face_count_zlo,"
            << "amr_cf_interface_face_count_zhi,"
            << "amr_sync_corrected_balance_error\n";
}

void print_diagnostics(int step,
                       amrex::Real time,
                       const TransportDiagnostics& diag,
                       amrex::Real injected_mass,
                       amrex::Real boundary_inflow_mass,
                       amrex::Real outlet_mass,
                       amrex::Real initial_mass)
{
    const amrex::Real balance_error =
        diag.scalar_mass - initial_mass - injected_mass - boundary_inflow_mass + outlet_mass;
    const amrex::Real amr_sync_corrected_balance_error =
        balance_error - diag.amr_cumulative_restriction_mass_delta
        - diag.amr_cumulative_reflux_mass_delta;
    amrex::Print() << "step " << step
                   << " time " << time
                   << " mass " << diag.scalar_mass
                   << " injected " << injected_mass
                   << " boundary_inflow " << boundary_inflow_mass
                   << " outlet " << outlet_mass
                   << " balance_error " << balance_error
                   << " amr_sync_corrected_balance_error "
                   << amr_sync_corrected_balance_error
                   << " source_rate " << diag.source_rate
                   << " boundary_inflow_rate " << diag.boundary_inflow_rate
                   << " outlet_rate " << diag.outlet_rate
                   << " inflow_face_rates xlo " << diag.inflow_xlo_rate
                   << " xhi " << diag.inflow_xhi_rate
                   << " ylo " << diag.inflow_ylo_rate
                   << " yhi " << diag.inflow_yhi_rate
                   << " zlo " << diag.inflow_zlo_rate
                   << " zhi " << diag.inflow_zhi_rate
                   << " outlet_face_rates xlo " << diag.outlet_xlo_rate
                   << " xhi " << diag.outlet_xhi_rate
                   << " ylo " << diag.outlet_ylo_rate
                   << " yhi " << diag.outlet_yhi_rate
                   << " zlo " << diag.outlet_zlo_rate
                   << " zhi " << diag.outlet_zhi_rate
                   << " max_Y " << diag.max_y
                   << " max_Y_location " << diag.max_y_x
                   << " " << diag.max_y_y
                   << " " << diag.max_y_z
                   << " max_concentration " << diag.max_concentration
                   << " cloud_volume " << diag.cloud_volume
                   << " cloud_bounds x " << diag.cloud_x_min
                   << " " << diag.cloud_x_max
                   << " y " << diag.cloud_y_min
                   << " " << diag.cloud_y_max
                   << " z " << diag.cloud_z_min
                   << " " << diag.cloud_z_max
                   << " cloud_mass " << diag.cloud_mass
                   << " cloud_mean_concentration " << diag.cloud_mean_concentration
                   << " flammable_volume " << diag.flammable_volume
                   << " flammable_bounds x " << diag.flammable_x_min
                   << " " << diag.flammable_x_max
                   << " y " << diag.flammable_y_min
                   << " " << diag.flammable_y_max
                   << " z " << diag.flammable_z_min
                   << " " << diag.flammable_z_max
                   << " flammable_mass " << diag.flammable_mass
                   << " flammable_mean_concentration " << diag.flammable_mean_concentration
                   << " tag_volumes grad_y " << diag.tag_grad_y_volume
                   << " source " << diag.tag_source_volume
                   << " refine " << diag.tag_refine_volume
                   << " tag_candidate_level1 boxes " << diag.tag_cluster_count
                   << " tagged_cells " << diag.tag_refine_cell_count
                   << " fine_cells " << diag.tag_candidate_level1_cell_count
                   << " volume " << diag.tag_candidate_level1_volume
                   << " amr_level1_bounds x " << diag.amr_level1_x_min
                   << " " << diag.amr_level1_x_max
                   << " y " << diag.amr_level1_y_min
                   << " " << diag.amr_level1_y_max
                   << " z " << diag.amr_level1_z_min
                   << " " << diag.amr_level1_z_max
                   << " amr_restrict max_abs_y_error " << diag.amr_restrict_max_abs_y_error
                   << " l1_y_error " << diag.amr_restrict_l1_y_error
                   << " coarse_cells " << diag.amr_restrict_coarse_cell_count
                   << " amr_mass level1 " << diag.amr_level1_mass
                   << " covered_level0 " << diag.amr_covered_level0_mass
                   << " delta " << diag.amr_mass_delta
                   << " applied_restriction_delta "
                   << diag.amr_applied_restriction_mass_delta
                   << " applied_reflux_delta "
                   << diag.amr_applied_reflux_mass_delta
                   << " cumulative_restriction_delta "
                   << diag.amr_cumulative_restriction_mass_delta
                   << " cumulative_reflux_delta "
                   << diag.amr_cumulative_reflux_mass_delta
                   << " cf_advective_flux_mismatch "
                   << diag.amr_cf_advective_flux_mismatch
                   << " cf_advective_abs_mismatch "
                   << diag.amr_cf_advective_abs_mismatch
                   << " cf_diffusive_flux_mismatch "
                   << diag.amr_cf_diffusive_flux_mismatch
                   << " cf_diffusive_abs_mismatch "
                   << diag.amr_cf_diffusive_abs_mismatch
                   << " cf_advective_mismatch_mass "
                   << diag.amr_cf_advective_mismatch_mass
                   << " cf_advective_abs_mismatch_mass "
                   << diag.amr_cf_advective_abs_mismatch_mass
                   << " cf_diffusive_mismatch_mass "
                   << diag.amr_cf_diffusive_mismatch_mass
                   << " cf_diffusive_abs_mismatch_mass "
                   << diag.amr_cf_diffusive_abs_mismatch_mass
                   << " cf_interface_faces "
                   << diag.amr_cf_interface_face_count
                   << " cf_face_mismatch xlo "
                   << diag.amr_cf_advective_flux_mismatch_face[0]
                   << " xhi " << diag.amr_cf_advective_flux_mismatch_face[1]
                   << " ylo " << diag.amr_cf_advective_flux_mismatch_face[2]
                   << " yhi " << diag.amr_cf_advective_flux_mismatch_face[3]
                   << " zlo " << diag.amr_cf_advective_flux_mismatch_face[4]
                   << " zhi " << diag.amr_cf_advective_flux_mismatch_face[5]
                   << " centroid " << diag.x_centroid
                   << " " << diag.y_centroid
                   << " " << diag.z_centroid << "\n";
}

void append_history(int step,
                    amrex::Real time,
                    const TransportDiagnostics& diag,
                    amrex::Real injected_mass,
                    amrex::Real boundary_inflow_mass,
                    amrex::Real outlet_mass,
                    amrex::Real initial_mass,
                    const RuntimeParams& params)
{
    if (!amrex::ParallelDescriptor::IOProcessor()) {
        return;
    }
    const amrex::Real balance_error =
        diag.scalar_mass - initial_mass - injected_mass - boundary_inflow_mass + outlet_mass;
    const amrex::Real amr_sync_corrected_balance_error =
        balance_error - diag.amr_cumulative_restriction_mass_delta
        - diag.amr_cumulative_reflux_mass_delta;
    std::ofstream history(params.history_file, std::ios::app);
    history << step << ","
            << std::setprecision(17) << time << ","
            << diag.scalar_mass << ","
            << injected_mass << ","
            << boundary_inflow_mass << ","
            << outlet_mass << ","
            << balance_error << ","
            << diag.source_rate << ","
            << diag.boundary_inflow_rate << ","
            << diag.outlet_rate << ","
            << diag.max_y << ","
            << diag.max_y_x << ","
            << diag.max_y_y << ","
            << diag.max_y_z << ","
            << diag.max_concentration << ","
            << diag.x_centroid << ","
            << diag.y_centroid << ","
            << diag.z_centroid << ","
            << diag.inflow_xlo_rate << ","
            << diag.inflow_xhi_rate << ","
            << diag.inflow_ylo_rate << ","
            << diag.inflow_yhi_rate << ","
            << diag.inflow_zlo_rate << ","
            << diag.inflow_zhi_rate << ","
            << diag.outlet_xlo_rate << ","
            << diag.outlet_xhi_rate << ","
            << diag.outlet_ylo_rate << ","
            << diag.outlet_yhi_rate << ","
            << diag.outlet_zlo_rate << ","
            << diag.outlet_zhi_rate << ","
            << diag.cloud_volume << ","
            << diag.cloud_mass << ","
            << diag.cloud_mean_concentration << ","
            << diag.cloud_x_min << ","
            << diag.cloud_x_max << ","
            << diag.cloud_y_min << ","
            << diag.cloud_y_max << ","
            << diag.cloud_z_min << ","
            << diag.cloud_z_max << ","
            << diag.flammable_volume << ","
            << diag.flammable_mass << ","
            << diag.flammable_mean_concentration << ","
            << diag.flammable_x_min << ","
            << diag.flammable_x_max << ","
            << diag.flammable_y_min << ","
            << diag.flammable_y_max << ","
            << diag.flammable_z_min << ","
            << diag.flammable_z_max << ","
            << diag.tag_grad_y_volume << ","
            << diag.tag_source_volume << ","
            << diag.tag_refine_volume << ","
            << diag.tag_refine_cell_count << ","
            << diag.tag_cluster_count << ","
            << diag.tag_candidate_level1_cell_count << ","
            << diag.tag_candidate_level1_volume << ","
            << diag.amr_level1_x_min << ","
            << diag.amr_level1_x_max << ","
            << diag.amr_level1_y_min << ","
            << diag.amr_level1_y_max << ","
            << diag.amr_level1_z_min << ","
            << diag.amr_level1_z_max << ","
            << diag.amr_restrict_max_abs_y_error << ","
            << diag.amr_restrict_l1_y_error << ","
            << diag.amr_restrict_coarse_cell_count << ","
            << diag.amr_level1_mass << ","
            << diag.amr_covered_level0_mass << ","
            << diag.amr_mass_delta << ","
            << diag.amr_applied_restriction_mass_delta << ","
            << diag.amr_applied_reflux_mass_delta << ","
            << diag.amr_cumulative_restriction_mass_delta << ","
            << diag.amr_cumulative_reflux_mass_delta << ","
            << diag.amr_cf_advective_flux_mismatch << ","
            << diag.amr_cf_advective_abs_mismatch << ","
            << diag.amr_cf_diffusive_flux_mismatch << ","
            << diag.amr_cf_diffusive_abs_mismatch << ","
            << diag.amr_cf_advective_mismatch_mass << ","
            << diag.amr_cf_advective_abs_mismatch_mass << ","
            << diag.amr_cf_diffusive_mismatch_mass << ","
            << diag.amr_cf_diffusive_abs_mismatch_mass << ","
            << diag.amr_cf_interface_face_count << ","
            << diag.amr_cf_advective_flux_mismatch_face[0] << ","
            << diag.amr_cf_advective_flux_mismatch_face[1] << ","
            << diag.amr_cf_advective_flux_mismatch_face[2] << ","
            << diag.amr_cf_advective_flux_mismatch_face[3] << ","
            << diag.amr_cf_advective_flux_mismatch_face[4] << ","
            << diag.amr_cf_advective_flux_mismatch_face[5] << ","
            << diag.amr_cf_advective_abs_mismatch_face[0] << ","
            << diag.amr_cf_advective_abs_mismatch_face[1] << ","
            << diag.amr_cf_advective_abs_mismatch_face[2] << ","
            << diag.amr_cf_advective_abs_mismatch_face[3] << ","
            << diag.amr_cf_advective_abs_mismatch_face[4] << ","
            << diag.amr_cf_advective_abs_mismatch_face[5] << ","
            << diag.amr_cf_diffusive_flux_mismatch_face[0] << ","
            << diag.amr_cf_diffusive_flux_mismatch_face[1] << ","
            << diag.amr_cf_diffusive_flux_mismatch_face[2] << ","
            << diag.amr_cf_diffusive_flux_mismatch_face[3] << ","
            << diag.amr_cf_diffusive_flux_mismatch_face[4] << ","
            << diag.amr_cf_diffusive_flux_mismatch_face[5] << ","
            << diag.amr_cf_diffusive_abs_mismatch_face[0] << ","
            << diag.amr_cf_diffusive_abs_mismatch_face[1] << ","
            << diag.amr_cf_diffusive_abs_mismatch_face[2] << ","
            << diag.amr_cf_diffusive_abs_mismatch_face[3] << ","
            << diag.amr_cf_diffusive_abs_mismatch_face[4] << ","
            << diag.amr_cf_diffusive_abs_mismatch_face[5] << ","
            << diag.amr_cf_advective_mismatch_mass_face[0] << ","
            << diag.amr_cf_advective_mismatch_mass_face[1] << ","
            << diag.amr_cf_advective_mismatch_mass_face[2] << ","
            << diag.amr_cf_advective_mismatch_mass_face[3] << ","
            << diag.amr_cf_advective_mismatch_mass_face[4] << ","
            << diag.amr_cf_advective_mismatch_mass_face[5] << ","
            << diag.amr_cf_advective_abs_mismatch_mass_face[0] << ","
            << diag.amr_cf_advective_abs_mismatch_mass_face[1] << ","
            << diag.amr_cf_advective_abs_mismatch_mass_face[2] << ","
            << diag.amr_cf_advective_abs_mismatch_mass_face[3] << ","
            << diag.amr_cf_advective_abs_mismatch_mass_face[4] << ","
            << diag.amr_cf_advective_abs_mismatch_mass_face[5] << ","
            << diag.amr_cf_diffusive_mismatch_mass_face[0] << ","
            << diag.amr_cf_diffusive_mismatch_mass_face[1] << ","
            << diag.amr_cf_diffusive_mismatch_mass_face[2] << ","
            << diag.amr_cf_diffusive_mismatch_mass_face[3] << ","
            << diag.amr_cf_diffusive_mismatch_mass_face[4] << ","
            << diag.amr_cf_diffusive_mismatch_mass_face[5] << ","
            << diag.amr_cf_diffusive_abs_mismatch_mass_face[0] << ","
            << diag.amr_cf_diffusive_abs_mismatch_mass_face[1] << ","
            << diag.amr_cf_diffusive_abs_mismatch_mass_face[2] << ","
            << diag.amr_cf_diffusive_abs_mismatch_mass_face[3] << ","
            << diag.amr_cf_diffusive_abs_mismatch_mass_face[4] << ","
            << diag.amr_cf_diffusive_abs_mismatch_mass_face[5] << ","
            << diag.amr_cf_interface_face_count_face[0] << ","
            << diag.amr_cf_interface_face_count_face[1] << ","
            << diag.amr_cf_interface_face_count_face[2] << ","
            << diag.amr_cf_interface_face_count_face[3] << ","
            << diag.amr_cf_interface_face_count_face[4] << ","
            << diag.amr_cf_interface_face_count_face[5] << ","
            << amr_sync_corrected_balance_error << "\n";
}

void attach_restriction_diagnostics(TransportDiagnostics& diag,
                                    const amrex::MultiFab& level0_state,
                                    const ScalarAmrHierarchy& hierarchy,
                                    const amrex::Geometry& level0_geom,
                                    const RuntimeParams& params)
{
    const RestrictionDiagnostics restriction =
        compute_restriction_diagnostics(level0_state, hierarchy, level0_geom, params.tag_ref_ratio);
    diag.amr_restrict_max_abs_y_error = restriction.max_abs_y_error;
    diag.amr_restrict_l1_y_error = restriction.l1_y_error;
    diag.amr_restrict_coarse_cell_count = restriction.coarse_cell_count;
}

void attach_amr_mass_diagnostics(TransportDiagnostics& diag,
                                 const amrex::MultiFab& level0_state,
                                 const ScalarAmrHierarchy& hierarchy,
                                 const amrex::Geometry& level0_geom,
                                 const RuntimeParams& params,
                                 amrex::Real applied_restriction_mass_delta,
                                 amrex::Real applied_reflux_mass_delta)
{
    const AmrMassDiagnostics mass =
        compute_amr_mass_diagnostics(level0_state, hierarchy, level0_geom, params);
    fill_level1_bounds(diag, hierarchy);
    diag.amr_level1_mass = mass.level1_mass;
    diag.amr_covered_level0_mass = mass.covered_level0_mass;
    diag.amr_mass_delta = mass.mass_delta;
    diag.amr_applied_restriction_mass_delta = applied_restriction_mass_delta;
    diag.amr_applied_reflux_mass_delta = applied_reflux_mass_delta;
}

void attach_coarse_fine_flux_diagnostics(TransportDiagnostics& diag,
                                         const amrex::MultiFab& level0_state,
                                         const ScalarAmrHierarchy& hierarchy,
                                         const amrex::Geometry& level0_geom,
                                         const RuntimeParams& params)
{
    const CoarseFineFluxDiagnostics flux =
        compute_coarse_fine_flux_diagnostics(level0_state, hierarchy, level0_geom, params);
    CoarseFineFluxDiagnostics accumulated_flux = hierarchy.last_step_flux_register.totals();
    amrex::Long accumulated_face_count =
        static_cast<amrex::Long>(accumulated_flux.interface_face_count);
    amrex::ParallelDescriptor::ReduceRealSum(accumulated_flux.advective_mismatch);
    amrex::ParallelDescriptor::ReduceRealSum(accumulated_flux.advective_abs_mismatch);
    amrex::ParallelDescriptor::ReduceRealSum(accumulated_flux.diffusive_mismatch);
    amrex::ParallelDescriptor::ReduceRealSum(accumulated_flux.diffusive_abs_mismatch);
    amrex::ParallelDescriptor::ReduceLongSum(accumulated_face_count);
    for (int idx = 0; idx < 2 * AMREX_SPACEDIM; ++idx) {
        amrex::Long face_count =
            static_cast<amrex::Long>(accumulated_flux.interface_face_count_by_face[idx]);
        amrex::ParallelDescriptor::ReduceRealSum(accumulated_flux.advective_mismatch_by_face[idx]);
        amrex::ParallelDescriptor::ReduceRealSum(accumulated_flux.advective_abs_mismatch_by_face[idx]);
        amrex::ParallelDescriptor::ReduceRealSum(accumulated_flux.diffusive_mismatch_by_face[idx]);
        amrex::ParallelDescriptor::ReduceRealSum(accumulated_flux.diffusive_abs_mismatch_by_face[idx]);
        amrex::ParallelDescriptor::ReduceLongSum(face_count);
        accumulated_flux.interface_face_count_by_face[idx] =
            static_cast<long long>(face_count);
    }
    diag.amr_cf_advective_flux_mismatch = flux.advective_mismatch;
    diag.amr_cf_advective_abs_mismatch = flux.advective_abs_mismatch;
    diag.amr_cf_diffusive_flux_mismatch = flux.diffusive_mismatch;
    diag.amr_cf_diffusive_abs_mismatch = flux.diffusive_abs_mismatch;
    diag.amr_cf_advective_mismatch_mass = accumulated_flux.advective_mismatch;
    diag.amr_cf_advective_abs_mismatch_mass = accumulated_flux.advective_abs_mismatch;
    diag.amr_cf_diffusive_mismatch_mass = accumulated_flux.diffusive_mismatch;
    diag.amr_cf_diffusive_abs_mismatch_mass = accumulated_flux.diffusive_abs_mismatch;
    diag.amr_cf_interface_face_count = flux.interface_face_count;
    for (int idx = 0; idx < 2 * AMREX_SPACEDIM; ++idx) {
        diag.amr_cf_advective_flux_mismatch_face[idx] =
            flux.advective_mismatch_by_face[idx];
        diag.amr_cf_advective_abs_mismatch_face[idx] =
            flux.advective_abs_mismatch_by_face[idx];
        diag.amr_cf_diffusive_flux_mismatch_face[idx] =
            flux.diffusive_mismatch_by_face[idx];
        diag.amr_cf_diffusive_abs_mismatch_face[idx] =
            flux.diffusive_abs_mismatch_by_face[idx];
        diag.amr_cf_advective_mismatch_mass_face[idx] =
            accumulated_flux.advective_mismatch_by_face[idx];
        diag.amr_cf_advective_abs_mismatch_mass_face[idx] =
            accumulated_flux.advective_abs_mismatch_by_face[idx];
        diag.amr_cf_diffusive_mismatch_mass_face[idx] =
            accumulated_flux.diffusive_mismatch_by_face[idx];
        diag.amr_cf_diffusive_abs_mismatch_mass_face[idx] =
            accumulated_flux.diffusive_abs_mismatch_by_face[idx];
        diag.amr_cf_interface_face_count_face[idx] =
            flux.interface_face_count_by_face[idx];
    }
}

void write_plotfile(const amrex::MultiFab& state,
                    const amrex::Geometry& geom,
                    const RuntimeParams& params,
                    int step,
                    amrex::Real time,
                    const ScalarAmrHierarchy* hierarchy)
{
    amrex::MultiFab tags(state.boxArray(), state.DistributionMap(), NumTag, 0);
    fill_tagging_indicators(state, tags, geom, params);
    const CandidateLevel1Grids candidate = make_candidate_level1_grids(tags, geom, params);

    amrex::MultiFab plot_state(state.boxArray(), state.DistributionMap(), NumState + 1 + NumTag, 0);
    amrex::MultiFab::Copy(plot_state, state, 0, 0, NumState, 0);
    amrex::MultiFab::Copy(plot_state, tags, 0, NumState + 1, NumTag, 0);
    fill_diagnostic_plot_components(plot_state, params);

    const amrex::Vector<std::string> var_names = plot_var_names();
    const std::string name = plotfile_name(params.plotfile_prefix, step);
    if (hierarchy != nullptr && hierarchy->has_level1()) {
        amrex::MultiFab fine_tags(hierarchy->level1_state->boxArray(),
                                  hierarchy->level1_state->DistributionMap(),
                                  NumTag,
                                  0);
        fill_tagging_indicators(*hierarchy->level1_state, fine_tags, hierarchy->level1_geom, params);

        amrex::MultiFab fine_plot_state(hierarchy->level1_state->boxArray(),
                                        hierarchy->level1_state->DistributionMap(),
                                        plot_state.nComp(),
                                        0);
        amrex::MultiFab::Copy(fine_plot_state, *hierarchy->level1_state, 0, 0, NumState, 0);
        amrex::MultiFab::Copy(fine_plot_state, fine_tags, 0, NumState + 1, NumTag, 0);
        fill_diagnostic_plot_components(fine_plot_state, params);

        const amrex::Vector<const amrex::MultiFab*> mfs{&plot_state, &fine_plot_state};
        const amrex::Vector<amrex::Geometry> geoms{geom, hierarchy->level1_geom};
        const amrex::Vector<int> level_steps{step, step};
        const amrex::Vector<amrex::IntVect> ref_ratio{amrex::IntVect(params.tag_ref_ratio)};
        amrex::WriteMultiLevelPlotfile(name, 2, mfs, var_names, geoms, time, level_steps, ref_ratio);
        return;
    }

    if (candidate.summary.cluster_count == 0) {
        amrex::WriteSingleLevelPlotfile(name, plot_state, var_names, geom, time, step);
        return;
    }

    const amrex::DistributionMapping fine_dm(candidate.box_array);
    amrex::MultiFab fine_plot_state(candidate.box_array, fine_dm, plot_state.nComp(), 0);
    initialize_refined_level_from_coarse(plot_state, fine_plot_state, geom, params.tag_ref_ratio);
    const amrex::Geometry fine_geom = make_refined_geometry(geom, params.tag_ref_ratio);

    const amrex::Vector<const amrex::MultiFab*> mfs{&plot_state, &fine_plot_state};
    const amrex::Vector<amrex::Geometry> geoms{geom, fine_geom};
    const amrex::Vector<int> level_steps{step, step};
    const amrex::Vector<amrex::IntVect> ref_ratio{amrex::IntVect(params.tag_ref_ratio)};
    amrex::WriteMultiLevelPlotfile(name, 2, mfs, var_names, geoms, time, level_steps, ref_ratio);
}

} // namespace amrreactx
