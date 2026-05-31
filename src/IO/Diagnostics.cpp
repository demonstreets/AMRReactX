#include "IO/Diagnostics.H"

#include "AMR/BoundaryConditions.H"
#include "Physics/SourceTerms.H"

#include <AMReX_Array4.H>
#include <AMReX_Box.H>
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
            if (i == dom_lo[0] && kparams.wind[0] < 0.0 && kparams.bc_lo[0] != BcWall) {
                d(i, j, k, OutletRate) += rho0 * (-kparams.wind[0]) * y_leak * face_area[0] / cell_volume;
            }
            if (i == dom_hi[0] && kparams.wind[0] > 0.0 && kparams.bc_hi[0] != BcWall) {
                d(i, j, k, OutletRate) += rho0 * kparams.wind[0] * y_leak * face_area[0] / cell_volume;
            }
            if (j == dom_lo[1] && kparams.wind[1] < 0.0 && kparams.bc_lo[1] != BcWall) {
                d(i, j, k, OutletRate) += rho0 * (-kparams.wind[1]) * y_leak * face_area[1] / cell_volume;
            }
            if (j == dom_hi[1] && kparams.wind[1] > 0.0 && kparams.bc_hi[1] != BcWall) {
                d(i, j, k, OutletRate) += rho0 * kparams.wind[1] * y_leak * face_area[1] / cell_volume;
            }
            if (k == dom_lo[2] && kparams.wind[2] < 0.0 && kparams.bc_lo[2] != BcWall) {
                d(i, j, k, OutletRate) += rho0 * (-kparams.wind[2]) * y_leak * face_area[2] / cell_volume;
            }
            if (k == dom_hi[2] && kparams.wind[2] > 0.0 && kparams.bc_hi[2] != BcWall) {
                d(i, j, k, OutletRate) += rho0 * kparams.wind[2] * y_leak * face_area[2] / cell_volume;
            }
            d(i, j, k, XMoment) = rho0 * y_leak * x;
            d(i, j, k, YMoment) = rho0 * y_leak * y;
            d(i, j, k, ZMoment) = rho0 * y_leak * z;
            d(i, j, k, CloudIndicator) = concentration >= cloud_threshold ? 1.0 : 0.0;
            d(i, j, k, FlammableIndicator) =
                (concentration >= lel && concentration <= uel) ? 1.0 : 0.0;
        });
    }

    TransportDiagnostics out;
    out.scalar_mass = scalar_mass(state, geom, params);
    out.source_rate = diag.sum(SourceRate) * cell_volume;
    out.outlet_rate = diag.sum(OutletRate) * cell_volume;
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
                }
            }
        }
    }
    amrex::ParallelDescriptor::ReduceRealMin(max_location, AMREX_SPACEDIM);
    if (max_location[0] < std::numeric_limits<amrex::Real>::max()) {
        out.max_y_x = max_location[0];
        out.max_y_y = max_location[1];
        out.max_y_z = max_location[2];
    }
    out.cloud_volume = diag.sum(CloudIndicator) * cell_volume;
    out.flammable_volume = diag.sum(FlammableIndicator) * cell_volume;
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
                   << " inlet_y " << params.inlet_y << "\n";
}

void print_source_report(const RuntimeParams& params)
{
    amrex::Print() << "scalar_source type " << source_type_name(params.source_type)
                   << " strength " << params.source_strength
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

void initialize_history_file(const RuntimeParams& params)
{
    if (!amrex::ParallelDescriptor::IOProcessor()) {
        return;
    }
    std::ofstream history(params.history_file);
    history << "step,time,mass,injected,outlet,balance_error,source_rate,outlet_rate,max_Y,"
            << "max_Y_x,max_Y_y,max_Y_z,max_concentration,centroid_x,centroid_y,centroid_z,"
            << "cloud_volume,flammable_volume\n";
}

void print_diagnostics(int step,
                       amrex::Real time,
                       const TransportDiagnostics& diag,
                       amrex::Real injected_mass,
                       amrex::Real outlet_mass,
                       amrex::Real initial_mass)
{
    const amrex::Real balance_error = diag.scalar_mass - initial_mass - injected_mass + outlet_mass;
    amrex::Print() << "step " << step
                   << " time " << time
                   << " mass " << diag.scalar_mass
                   << " injected " << injected_mass
                   << " outlet " << outlet_mass
                   << " balance_error " << balance_error
                   << " source_rate " << diag.source_rate
                   << " outlet_rate " << diag.outlet_rate
                   << " max_Y " << diag.max_y
                   << " max_Y_location " << diag.max_y_x
                   << " " << diag.max_y_y
                   << " " << diag.max_y_z
                   << " max_concentration " << diag.max_concentration
                   << " cloud_volume " << diag.cloud_volume
                   << " flammable_volume " << diag.flammable_volume
                   << " centroid " << diag.x_centroid
                   << " " << diag.y_centroid
                   << " " << diag.z_centroid << "\n";
}

void append_history(int step,
                    amrex::Real time,
                    const TransportDiagnostics& diag,
                    amrex::Real injected_mass,
                    amrex::Real outlet_mass,
                    amrex::Real initial_mass,
                    const RuntimeParams& params)
{
    if (!amrex::ParallelDescriptor::IOProcessor()) {
        return;
    }
    const amrex::Real balance_error = diag.scalar_mass - initial_mass - injected_mass + outlet_mass;
    std::ofstream history(params.history_file, std::ios::app);
    history << step << ","
            << std::setprecision(17) << time << ","
            << diag.scalar_mass << ","
            << injected_mass << ","
            << outlet_mass << ","
            << balance_error << ","
            << diag.source_rate << ","
            << diag.outlet_rate << ","
            << diag.max_y << ","
            << diag.max_y_x << ","
            << diag.max_y_y << ","
            << diag.max_y_z << ","
            << diag.max_concentration << ","
            << diag.x_centroid << ","
            << diag.y_centroid << ","
            << diag.z_centroid << ","
            << diag.cloud_volume << ","
            << diag.flammable_volume << "\n";
}

void write_plotfile(const amrex::MultiFab& state,
                    const amrex::Geometry& geom,
                    const RuntimeParams& params,
                    int step,
                    amrex::Real time)
{
    amrex::MultiFab plot_state(state.boxArray(), state.DistributionMap(), NumState + 1, 0);
    amrex::MultiFab::Copy(plot_state, state, 0, 0, NumState, 0);

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

    const amrex::Vector<std::string> var_names{
        "rho", "u", "v", "w", "Y_leak", "C_leak_diag"
    };
    amrex::WriteSingleLevelPlotfile(plotfile_name(params.plotfile_prefix, step),
                                    plot_state, var_names, geom, time, step);
}

} // namespace amrreactx
