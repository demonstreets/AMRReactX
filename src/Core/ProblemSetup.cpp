#include "Core/ProblemSetup.H"

#include "AMR/BoundaryConditions.H"
#include "Physics/SourceTerms.H"

#include <AMReX.H>
#include <AMReX_ParmParse.H>
#include <AMReX_REAL.H>
#include <AMReX_RealBox.H>
#include <AMReX_Vector.H>

#include <cmath>
#include <string>

namespace amrreactx {

amrex::Geometry make_geometry()
{
    amrex::Vector<int> n_cell(AMREX_SPACEDIM, 32);
    amrex::Vector<amrex::Real> prob_lo(AMREX_SPACEDIM, 0.0);
    amrex::Vector<amrex::Real> prob_hi(AMREX_SPACEDIM, 1.0);

    amrex::ParmParse pp;
    pp.queryarr("n_cell", n_cell, 0, AMREX_SPACEDIM);
    pp.queryarr("prob_lo", prob_lo, 0, AMREX_SPACEDIM);
    pp.queryarr("prob_hi", prob_hi, 0, AMREX_SPACEDIM);

    const amrex::IntVect dom_lo(AMREX_D_DECL(0, 0, 0));
    const amrex::IntVect dom_hi(AMREX_D_DECL(n_cell[0] - 1,
                                             n_cell[1] - 1,
                                             n_cell[2] - 1));
    const amrex::Box domain(dom_lo, dom_hi);
    const amrex::RealBox real_box(prob_lo.data(), prob_hi.data());
    const int coord_sys = 0;
    amrex::Vector<int> is_periodic(AMREX_SPACEDIM, 0);

    return amrex::Geometry(domain, &real_box, coord_sys, is_periodic.data());
}

RuntimeParams read_params(const amrex::Geometry& geom)
{
    RuntimeParams params;
    const auto prob_lo = geom.ProbLoArray();
    const auto prob_hi = geom.ProbHiArray();
    for (int d = 0; d < AMREX_SPACEDIM; ++d) {
        params.source_center[d] = 0.5 * (prob_lo[d] + prob_hi[d]);
        params.init_center[d] = 0.5 * (prob_lo[d] + prob_hi[d]);
    }
    params.source_center[0] = prob_lo[0] + 0.15 * (prob_hi[0] - prob_lo[0]);
    params.source_sigma = 0.04 * (prob_hi[0] - prob_lo[0]);
    for (int d = 0; d < AMREX_SPACEDIM; ++d) {
        const amrex::Real half_width = 0.025 * (prob_hi[d] - prob_lo[d]);
        params.source_box_lo[d] = params.source_center[d] - half_width;
        params.source_box_hi[d] = params.source_center[d] + half_width;
    }
    params.init_center[0] = prob_lo[0] + 0.25 * (prob_hi[0] - prob_lo[0]);
    params.init_sigma = 0.05 * (prob_hi[0] - prob_lo[0]);

    amrex::ParmParse pp;
    pp.query("max_grid_size", params.max_grid_size);
    pp.query("max_step", params.max_step);
    pp.query("plot_int", params.plot_int);
    pp.query("dt", params.dt);
    pp.query("stop_time", params.stop_time);
    pp.query("cfl", params.cfl);
    pp.query("diff_cfl", params.diff_cfl);
    pp.query("use_auto_dt", params.use_auto_dt);
    pp.query("diffusion", params.diffusion);
    pp.query("rho0", params.rho0);
    pp.query("inlet_y", params.inlet_y);
    pp.query("ambient_y", params.ambient_y);
    pp.query("source_sigma", params.source_sigma);
    pp.query("source_strength", params.source_strength);
    pp.query("source_total_rate", params.source_total_rate);
    pp.query("init_type", params.init_type);
    pp.query("init_sigma", params.init_sigma);
    pp.query("init_amplitude", params.init_amplitude);
    pp.query("cloud_threshold", params.cloud_threshold);
    pp.query("lel", params.lel);
    pp.query("uel", params.uel);
    pp.query("leak_molecular_weight", params.leak_molecular_weight);
    pp.query("air_molecular_weight", params.air_molecular_weight);
    pp.query("tagging_enabled", params.tagging_enabled);
    pp.query("tag_grad_y", params.tag_grad_y);
    pp.query("tag_source_region", params.tag_source_region);
    pp.query("tag_source_radius", params.tag_source_radius);
    pp.query("tag_source_box_buffer", params.tag_source_box_buffer);
    pp.query("tag_buffer", params.tag_buffer);
    pp.query("tag_ref_ratio", params.tag_ref_ratio);
    pp.query("tag_max_grid_size", params.tag_max_grid_size);
    pp.query("tag_grid_efficiency", params.tag_grid_efficiency);
    pp.query("history_file", params.history_file);
    pp.query("plotfile_prefix", params.plotfile_prefix);
    std::string source_type = source_type_name(params.source_type);
    pp.query("source_type", source_type);
    params.source_type = parse_source_type(source_type);
    std::string diagnostic_basis = concentration_basis_name(params.diagnostic_basis);
    pp.query("diagnostic_basis", diagnostic_basis);
    params.diagnostic_basis = parse_concentration_basis(diagnostic_basis);
    if (params.diagnostic_basis < 0) {
        amrex::Abort("Unknown diagnostic_basis: " + diagnostic_basis);
    }
    if (params.leak_molecular_weight <= 0.0 || params.air_molecular_weight <= 0.0) {
        amrex::Abort("Molecular weights must be positive for concentration diagnostics.");
    }

    amrex::Vector<amrex::Real> wind(AMREX_SPACEDIM);
    amrex::Vector<amrex::Real> source_center(AMREX_SPACEDIM);
    amrex::Vector<amrex::Real> source_box_lo(AMREX_SPACEDIM);
    amrex::Vector<amrex::Real> source_box_hi(AMREX_SPACEDIM);
    amrex::Vector<amrex::Real> init_center(AMREX_SPACEDIM);
    for (int d = 0; d < AMREX_SPACEDIM; ++d) {
        wind[d] = params.wind[d];
        source_center[d] = params.source_center[d];
        source_box_lo[d] = params.source_box_lo[d];
        source_box_hi[d] = params.source_box_hi[d];
        init_center[d] = params.init_center[d];
    }
    pp.queryarr("wind", wind, 0, AMREX_SPACEDIM);
    pp.queryarr("source_center", source_center, 0, AMREX_SPACEDIM);
    pp.queryarr("source_box_lo", source_box_lo, 0, AMREX_SPACEDIM);
    pp.queryarr("source_box_hi", source_box_hi, 0, AMREX_SPACEDIM);
    pp.queryarr("init_center", init_center, 0, AMREX_SPACEDIM);

    amrex::Vector<std::string> bc_lo(AMREX_SPACEDIM);
    amrex::Vector<std::string> bc_hi(AMREX_SPACEDIM);
    for (int d = 0; d < AMREX_SPACEDIM; ++d) {
        bc_lo[d] = boundary_type_name(params.bc_lo[d]);
        bc_hi[d] = boundary_type_name(params.bc_hi[d]);
    }
    pp.queryarr("bc_lo", bc_lo, 0, AMREX_SPACEDIM);
    pp.queryarr("bc_hi", bc_hi, 0, AMREX_SPACEDIM);

    for (int d = 0; d < AMREX_SPACEDIM; ++d) {
        params.wind[d] = wind[d];
        params.source_center[d] = source_center[d];
        params.source_box_lo[d] = source_box_lo[d];
        params.source_box_hi[d] = source_box_hi[d];
        params.init_center[d] = init_center[d];
        params.bc_lo[d] = parse_boundary_type(bc_lo[d]);
        params.bc_hi[d] = parse_boundary_type(bc_hi[d]);
    }

    if (params.source_total_rate >= 0.0) {
        if (params.rho0 <= 0.0) {
            amrex::Abort("rho0 must be positive when source_total_rate is used.");
        }
        if (params.source_type == SourceBox) {
            amrex::Real box_volume = 1.0;
            for (int d = 0; d < AMREX_SPACEDIM; ++d) {
                const amrex::Real width = params.source_box_hi[d] - params.source_box_lo[d];
                if (width <= 0.0) {
                    amrex::Abort("source_box_hi must be greater than source_box_lo when source_total_rate is used.");
                }
                box_volume *= width;
            }
            params.source_strength = params.source_total_rate / (params.rho0 * box_volume);
        } else if (params.source_type == SourceGaussian) {
            if (params.source_sigma <= 0.0) {
                amrex::Abort("source_sigma must be positive when source_total_rate is used.");
            }
            const amrex::Real pi = std::acos(amrex::Real(-1.0));
            const amrex::Real gaussian_volume =
                std::pow(amrex::Real(2.0) * pi, amrex::Real(1.5))
                * std::pow(params.source_sigma, AMREX_SPACEDIM);
            params.source_strength = params.source_total_rate / (params.rho0 * gaussian_volume);
        }
    }

    return params;
}

} // namespace amrreactx
