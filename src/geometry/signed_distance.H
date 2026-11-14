#ifndef PELE_SDF_H
#define PELE_SDF_H
#include "stl_parser.H"
#if __has_include(<AMReX_Config.H>)
#include <AMReX_MultiFab.H>
#include <AMReX_Geometry.H>
#include <AMReX_Array.H>
#include <AMReX_IntVect.H>
#endif
#include <cmath>
#include <vector>
namespace pele {
template <typename T>
T sdf_sphere(T x, T y, T z, T cx, T cy, T cz, T r) {
    return std::sqrt((x-cx)*(x-cx) + (y-cy)*(y-cy) + (z-cz)*(z-cz)) - r;
}

#if __has_include(<AMReX_Config.H>)
void computeSphereSDF(amrex::MultiFab& sdf,
                      const amrex::Geometry& geom,
                      const amrex::Array<amrex::Real,3>& center,
                      amrex::Real radius,
                      const amrex::IntVect& ng);
#endif

class SDFComputer {
public:
    void setFacets(const std::vector<STLFacet>& f) { m_facets = f; }
    double computePoint(double x, double y, double z) const;
private:
    std::vector<STLFacet> m_facets;
};
}
#endif