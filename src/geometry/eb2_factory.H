#ifndef PELE_EB2_FACTORY_H
#define PELE_EB2_FACTORY_H

#include <AMReX_EB2.H>
#include <AMReX_EB2_GeometryShop.H>
#include <AMReX_EB2_IndexSpace_STL.H>
#include <AMReX_EB2_IF_Base.H>
#include <AMReX_Geometry.H>
#include <AMReX_Array.H>
#include <AMReX_Vector.H>

#include <string>
#include <memory>
#include <vector>

namespace pele {

//! Implicit function functor for a sphere.
//!
//! Derives from amrex::GPUable so it works inside AMReX EB2 GPU kernels.
//! Convention: SDF = |x - center| - radius  (negative = fluid, positive = solid)
class SphereIF
    : public amrex::GPUable
{
public:
    SphereIF(amrex::Real radius,
             const amrex::Array<amrex::Real,3>& center,
             bool inside = false)
        : m_radius(radius),
          m_cx(center[0]), m_cy(center[1]), m_cz(center[2]),
          m_sign(inside ? 1.0 : -1.0)
    {}

    AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
    amrex::Real operator() (AMREX_D_DECL(amrex::Real x, amrex::Real y, amrex::Real z)) const noexcept
    {
        amrex::Real d2 = AMREX_D_TERM((x-m_cx)*(x-m_cx),
                                      +(y-m_cy)*(y-m_cy),
                                      +(z-m_cz)*(z-m_cz));
        return m_sign * (std::sqrt(d2) - m_radius);
    }

    AMREX_FORCE_INLINE
    amrex::Real operator() (const amrex::RealArray& p) const noexcept {
        return this->operator()(AMREX_D_DECL(p[0], p[1], p[2]));
    }

private:
    amrex::Real m_radius, m_cx, m_cy, m_cz, m_sign;
};

//! Build an EB2 IndexSpace for a sphere.
inline void
buildSphereEB(amrex::Real radius,
              const amrex::Array<amrex::Real,3>& center,
              const amrex::Geometry& geom,
              bool inside = false,
              int required_coarsening_level = 0,
              int max_coarsening_level = 0)
{
    SphereIF sphere(radius, center, inside);
    amrex::EB2::GeometryShop<SphereIF> gshop(sphere);
    amrex::EB2::Build(gshop, geom, required_coarsening_level, max_coarsening_level);
}

//! Build an EB2 IndexSpace from STL geometry using AMReX's STL-backed EB2 path.
//!
//! The STL mesh is loaded by amrex::STLtools and registered as the top EB2
//! IndexSpace via amrex::EB2::IndexSpace::push().
void buildFromSTL(const std::string& stl_file,
                  const amrex::Geometry& geom,
                  int max_coarsening_level = 0,
                  amrex::Real stl_scale = 1.0,
                  const amrex::Array<amrex::Real,3>& stl_center = {0.0, 0.0, 0.0},
                  int stl_reverse_normal = 0,
                  int required_coarsening_level = 0,
                  int ngrow = 4,
                  bool build_coarse_level_by_coarsening = true,
                  bool extend_domain_face = amrex::EB2::ExtendDomainFace(),
                  int num_coarsen_opt = amrex::EB2::NumCoarsenOpt(),
                  bool bvh_optimization = true,
                  bool support_mvmc = false);

//! Merge multiple STL files into one temporary binary STL, then build an EB2 IndexSpace.
//!
//! This supports multi-component industrial layouts where CAD export naturally
//! produces one STL per obstacle/body. All source STL files share the same
//! scale/center transform used by buildFromSTL().
void buildFromSTLFiles(const std::vector<std::string>& stl_files,
                       const std::string& merged_stl_file,
                       const amrex::Geometry& geom,
                       int max_coarsening_level = 0,
                       amrex::Real stl_scale = 1.0,
                       const amrex::Array<amrex::Real,3>& stl_center = {0.0, 0.0, 0.0},
                       int stl_reverse_normal = 0,
                       int required_coarsening_level = 0,
                       int ngrow = 4,
                       bool build_coarse_level_by_coarsening = true,
                       bool extend_domain_face = amrex::EB2::ExtendDomainFace(),
                       int num_coarsen_opt = amrex::EB2::NumCoarsenOpt(),
                       bool bvh_optimization = true,
                       bool support_mvmc = false);

//! Merge multiple STL files after applying one scale/center transform per file.
//!
//! This is intended for industrial CAD exports where each body may arrive in a
//! different local coordinate frame. The merged output is already in physical
//! coordinates, so it is handed to buildFromSTL() with identity scale/center.
void buildFromSTLFilesWithTransforms(
                       const std::vector<std::string>& stl_files,
                       const std::string& merged_stl_file,
                       const amrex::Geometry& geom,
                       int max_coarsening_level,
                       const std::vector<amrex::Real>& stl_scales,
                       const std::vector<amrex::Array<amrex::Real,3>>& stl_centers,
                       int stl_reverse_normal = 0,
                       int required_coarsening_level = 0,
                       int ngrow = 4,
                       bool build_coarse_level_by_coarsening = true,
                       bool extend_domain_face = amrex::EB2::ExtendDomainFace(),
                       int num_coarsen_opt = amrex::EB2::NumCoarsenOpt(),
                       bool bvh_optimization = true,
                       bool support_mvmc = false);

//! Build an EB2 IndexSpace from a custom implicit function.
template <typename F>
void
buildEBFromImplicitFunction(const F& impfunc,
                            const amrex::Geometry& geom,
                            int required_coarsening_level = 0,
                            int max_coarsening_level = 0)
{
    amrex::EB2::GeometryShop<F> gshop(impfunc);
    amrex::EB2::Build(gshop, geom, required_coarsening_level, max_coarsening_level);
}

} // namespace pele

#endif // PELE_EB2_FACTORY_H
