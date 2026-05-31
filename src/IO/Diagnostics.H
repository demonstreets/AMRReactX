#pragma once

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
void initialize_history_file(const RuntimeParams& params);

void print_diagnostics(int step,
                       amrex::Real time,
                       const TransportDiagnostics& diag,
                       amrex::Real injected_mass,
                       amrex::Real outlet_mass,
                       amrex::Real initial_mass);

void append_history(int step,
                    amrex::Real time,
                    const TransportDiagnostics& diag,
                    amrex::Real injected_mass,
                    amrex::Real outlet_mass,
                    amrex::Real initial_mass,
                    const RuntimeParams& params);

void write_plotfile(const amrex::MultiFab& state,
                    const amrex::Geometry& geom,
                    const RuntimeParams& params,
                    int step,
                    amrex::Real time);

} // namespace amrreactx
