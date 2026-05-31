#pragma once

#include "AMR/Hierarchy.H"
#include "Core/State.H"

#include <AMReX_Geometry.H>
#include <AMReX_MultiFab.H>

namespace amrreactx {

amrex::Real scalar_mass(const amrex::MultiFab& state,
                        const amrex::Geometry& geom,
                        const RuntimeParams& params);

TransportDiagnostics compute_diagnostics(const amrex::MultiFab& state,
                                         amrex::MultiFab& diag,
                                         const amrex::Geometry& geom,
                                         const RuntimeParams& params);

void print_stability_report(const StabilityInfo& info);
void print_boundary_report(const RuntimeParams& params);
void print_source_report(const RuntimeParams& params);
void print_concentration_report(const RuntimeParams& params);
void print_tagging_report(const RuntimeParams& params);
void initialize_history_file(const RuntimeParams& params);

void print_diagnostics(int step,
                       amrex::Real time,
                       const TransportDiagnostics& diag,
                       amrex::Real injected_mass,
                       amrex::Real boundary_inflow_mass,
                       amrex::Real outlet_mass,
                       amrex::Real initial_mass);

void append_history(int step,
                    amrex::Real time,
                    const TransportDiagnostics& diag,
                    amrex::Real injected_mass,
                    amrex::Real boundary_inflow_mass,
                    amrex::Real outlet_mass,
                    amrex::Real initial_mass,
                    const RuntimeParams& params);

void write_plotfile(const amrex::MultiFab& state,
                    const amrex::Geometry& geom,
                    const RuntimeParams& params,
                    int step,
                    amrex::Real time,
                    const ScalarAmrHierarchy* hierarchy = nullptr);

void attach_restriction_diagnostics(TransportDiagnostics& diag,
                                    const amrex::MultiFab& level0_state,
                                    const ScalarAmrHierarchy& hierarchy,
                                    const amrex::Geometry& level0_geom,
                                    const RuntimeParams& params);

void attach_amr_mass_diagnostics(TransportDiagnostics& diag,
                                 const amrex::MultiFab& level0_state,
                                 const ScalarAmrHierarchy& hierarchy,
                                 const amrex::Geometry& level0_geom,
                                 const RuntimeParams& params,
                                 amrex::Real applied_restriction_mass_delta);

void attach_coarse_fine_flux_diagnostics(TransportDiagnostics& diag,
                                         const amrex::MultiFab& level0_state,
                                         const ScalarAmrHierarchy& hierarchy,
                                         const amrex::Geometry& level0_geom,
                                         const RuntimeParams& params);

} // namespace amrreactx
