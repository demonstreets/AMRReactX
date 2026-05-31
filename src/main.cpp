#include "AMR/Hierarchy.H"
#include "Core/ProblemSetup.H"
#include "Core/State.H"
#include "IO/Diagnostics.H"
#include "Numerics/ScalarTransport.H"

#include <AMReX.H>
#include <AMReX_BoxArray.H>
#include <AMReX_DistributionMapping.H>
#include <AMReX_Geometry.H>
#include <AMReX_MultiFab.H>
#include <AMReX_ParallelDescriptor.H>

int main(int argc, char* argv[])
{
    amrex::Initialize(argc, argv);
    {
        const amrex::Geometry geom = amrreactx::make_geometry();
        const amrreactx::RuntimeParams params = amrreactx::read_params(geom);

        amrex::BoxArray ba(geom.Domain());
        ba.maxSize(params.max_grid_size);
        const amrex::DistributionMapping dm(ba);

        amrex::MultiFab state(ba, dm, amrreactx::NumState, 1);
        amrex::MultiFab old_state(ba, dm, amrreactx::NumState, 1);
        amrex::MultiFab next_state(ba, dm, amrreactx::NumState, 1);
        amrex::MultiFab diag(ba, dm, amrreactx::NumDiag, 0);
        amrreactx::initialize_state(state, geom, params);
        amrreactx::ScalarAmrHierarchy hierarchy =
            amrreactx::rebuild_scalar_amr_hierarchy(state, geom, params,
                                                    amrreactx::NumState, 1);

        amrex::Real time = 0.0;
        amrex::Real injected_mass = 0.0;
        amrex::Real boundary_inflow_mass = 0.0;
        amrex::Real outlet_mass = 0.0;
        amrreactx::TransportDiagnostics current_diag =
            amrreactx::compute_diagnostics(state, diag, geom, params);
        amrreactx::attach_restriction_diagnostics(current_diag, state, hierarchy, geom, params);
        amrreactx::attach_amr_mass_diagnostics(current_diag, state, hierarchy, geom, params, 0.0);
        const amrex::Real initial_mass = current_diag.scalar_mass;
        amrreactx::initialize_history_file(params);
        amrreactx::write_plotfile(state, geom, params, 0, time, &hierarchy);

        amrex::Print() << "AMRReactX scalar transport\n";
        amrex::Print() << "MPI ranks: " << amrex::ParallelDescriptor::NProcs() << "\n";
        amrreactx::print_boundary_report(params);
        amrreactx::print_source_report(params);
        amrreactx::print_concentration_report(params);
        amrreactx::print_tagging_report(params);
        amrreactx::print_stability_report(amrreactx::compute_stability(geom, params));
        amrreactx::print_diagnostics(0, time, current_diag, injected_mass,
                                     boundary_inflow_mass, outlet_mass, initial_mass);
        amrreactx::append_history(0, time, current_diag, injected_mass,
                                  boundary_inflow_mass, outlet_mass, initial_mass, params);

        for (int step = 1; step <= params.max_step; ++step) {
            const amrex::Real step_dt = amrreactx::compute_dt(geom, params, time);
            if (step_dt <= 0.0) {
                break;
            }
            amrreactx::RuntimeParams step_params = params;
            step_params.dt = step_dt;

            current_diag = amrreactx::compute_diagnostics(state, diag, geom, step_params);
            injected_mass += current_diag.source_rate * step_dt;
            boundary_inflow_mass += current_diag.boundary_inflow_rate * step_dt;
            outlet_mass += current_diag.outlet_rate * step_dt;
            amrex::MultiFab::Copy(old_state, state, 0, 0, amrreactx::NumState, 0);
            amrreactx::advance_scalar(state, next_state, geom, step_params);
            amrex::MultiFab::Copy(state, next_state, 0, 0, amrreactx::NumState, 0);
            amrreactx::advance_scalar_amr_hierarchy(hierarchy, old_state, state,
                                                    geom, step_params);
            amrex::Real applied_restriction_mass_delta = 0.0;
            if (step_params.amr_restrict_after_advance != 0) {
                const amrreactx::AmrMassDiagnostics restriction_update =
                    amrreactx::restrict_scalar_amr_hierarchy_to_coarse(
                        hierarchy, state, geom, step_params);
                applied_restriction_mass_delta = restriction_update.mass_delta;
            }
            time += step_dt;

            const bool last_time_step = params.stop_time >= 0.0 && time >= params.stop_time;
            if (step % params.plot_int == 0 || step == params.max_step || last_time_step) {
                current_diag = amrreactx::compute_diagnostics(state, diag, geom, step_params);
                if (!hierarchy.has_level1()) {
                    hierarchy = amrreactx::rebuild_scalar_amr_hierarchy(state, geom, step_params,
                                                                        amrreactx::NumState, 1);
                }
                amrreactx::attach_restriction_diagnostics(current_diag, state, hierarchy,
                                                          geom, step_params);
                amrreactx::attach_amr_mass_diagnostics(current_diag, state, hierarchy,
                                                       geom, step_params,
                                                       applied_restriction_mass_delta);
                amrreactx::write_plotfile(state, geom, params, step, time, &hierarchy);
                amrreactx::print_diagnostics(step, time, current_diag, injected_mass,
                                             boundary_inflow_mass, outlet_mass, initial_mass);
                amrreactx::append_history(step, time, current_diag, injected_mass,
                                          boundary_inflow_mass, outlet_mass, initial_mass, params);
            }
            if (last_time_step) {
                break;
            }
        }
    }
    amrex::Finalize();
}
