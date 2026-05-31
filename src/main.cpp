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
        amrex::MultiFab next_state(ba, dm, amrreactx::NumState, 1);
        amrex::MultiFab diag(ba, dm, amrreactx::NumDiag, 0);
        amrreactx::initialize_state(state, geom, params);

        amrex::Real time = 0.0;
        amrex::Real injected_mass = 0.0;
        amrex::Real outlet_mass = 0.0;
        amrreactx::TransportDiagnostics current_diag =
            amrreactx::compute_diagnostics(state, diag, geom, params);
        const amrex::Real initial_mass = current_diag.scalar_mass;
        amrreactx::initialize_history_file(params);
        amrreactx::write_plotfile(state, geom, params, 0, time);

        amrex::Print() << "AMRReactX Stage 1 scalar transport\n";
        amrex::Print() << "MPI ranks: " << amrex::ParallelDescriptor::NProcs() << "\n";
        amrreactx::print_boundary_report(params);
        amrreactx::print_source_report(params);
        amrreactx::print_concentration_report(params);
        amrreactx::print_stability_report(amrreactx::compute_stability(geom, params));
        amrreactx::print_diagnostics(0, time, current_diag, injected_mass, outlet_mass, initial_mass);
        amrreactx::append_history(0, time, current_diag, injected_mass, outlet_mass, initial_mass, params);

        for (int step = 1; step <= params.max_step; ++step) {
            const amrex::Real step_dt = amrreactx::compute_dt(geom, params, time);
            if (step_dt <= 0.0) {
                break;
            }
            amrreactx::RuntimeParams step_params = params;
            step_params.dt = step_dt;

            current_diag = amrreactx::compute_diagnostics(state, diag, geom, step_params);
            injected_mass += current_diag.source_rate * step_dt;
            outlet_mass += current_diag.outlet_rate * step_dt;
            amrreactx::advance_scalar(state, next_state, geom, step_params);
            amrex::MultiFab::Copy(state, next_state, 0, 0, amrreactx::NumState, 0);
            time += step_dt;

            const bool last_time_step = params.stop_time >= 0.0 && time >= params.stop_time;
            if (step % params.plot_int == 0 || step == params.max_step || last_time_step) {
                current_diag = amrreactx::compute_diagnostics(state, diag, geom, step_params);
                amrreactx::write_plotfile(state, geom, params, step, time);
                amrreactx::print_diagnostics(step, time, current_diag, injected_mass, outlet_mass, initial_mass);
                amrreactx::append_history(step, time, current_diag, injected_mass, outlet_mass, initial_mass, params);
            }
            if (last_time_step) {
                break;
            }
        }
    }
    amrex::Finalize();
}
