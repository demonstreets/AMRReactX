// Manufactured geometry/integration test: no leak or fire time advance.
#include "pelelmex_prob.H"
#include <AMReX.H>
#include <AMReX_EB2.H>
#include <AMReX_EB2_IF_Plane.H>
#include <AMReX_EB2_GeometryShop.H>
#include <AMReX_MultiFabUtil.H>
#include <iostream>

int main(int argc,char** argv) {
  amrex::Initialize(argc,argv);
  {
    const amrex::Box domain({0,0,0},{7,7,7});
    const amrex::Box fine_domain=amrex::refine(domain,2);
    const amrex::RealBox physical({0.,0.,0.},{1.,1.,1.});
    const int periodic[3]={0,0,0};
    amrex::Geometry coarse_geom(domain,&physical,0,periodic);
    amrex::Geometry fine_geom(fine_domain,&physical,0,periodic);
    // Fluid above y=0.3; exact fluid volume is 0.7 in a unit cube.
    amrex::EB2::PlaneIF plane({0.,0.3,0.},{0.,-1.,0.},true);
    amrex::EB2::Build(amrex::EB2::makeShop(plane),fine_geom,1,1);
    amrex::BoxArray coarse_ba(domain);coarse_ba.maxSize(4);
    amrex::BoxArray fine_ba(amrex::Box({8,0,0},{15,15,15}));fine_ba.maxSize(8);
    amrex::DistributionMapping coarse_dm(coarse_ba),fine_dm(fine_ba);
    auto coarse_factory=amrex::makeEBFabFactory(coarse_geom,coarse_ba,coarse_dm,{2,2,2},amrex::EBSupport::full);
    auto fine_factory=amrex::makeEBFabFactory(fine_geom,fine_ba,fine_dm,{2,2,2},amrex::EBSupport::full);
    amrex::MultiFab coarse(coarse_ba,coarse_dm,1,0,amrex::MFInfo(),*coarse_factory);
    amrex::MultiFab fine(fine_ba,fine_dm,1,0,amrex::MFInfo(),*fine_factory);
    auto owner=amrex::makeFineMask(coarse_ba,coarse_dm,fine_ba,amrex::IntVect(2),1,0,amrex::MFInfo());
    pelelmex::SourceGeometry geometry{{&coarse,&owner,coarse_geom.data()},
                                     {&fine,nullptr,fine_geom.data()}};
    namespace Leak=MyPele::Engineering::LeakSource;
    Leak::SphericalLeakSource region;
    region.center[0]=region.center[1]=region.center[2]=0.5;
    region.radius=2.;region.mass_flow_rate=1.;
    const double volume=MyProblemSpecificFunctions::source_fluid_volume(region,geometry);
    AMREX_ALWAYS_ASSERT_WITH_MESSAGE(std::abs(volume-.7)<1.e-12,
      "EB/composite-AMR source volume differs from exact 0.7");
    region.normalization_volume=volume;
    AMREX_ALWAYS_ASSERT_WITH_MESSAGE(std::abs(Leak::volumetric_mass_source(region)*.7-1.)<1.e-12,
      "fluid-integrated mass injection does not equal requested 1 kg/s");
    // Entire sphere in solid must have no active source volume.
    region.center[0]=region.center[1]=region.center[2]=0.1;
    region.radius=.05;
    const double solid_volume=MyProblemSpecificFunctions::source_fluid_volume(region,geometry);
    AMREX_ALWAYS_ASSERT_WITH_MESSAGE(solid_volume==0.,"solid source has nonzero fluid volume");
    amrex::Print()<<"PASS source-volume manufactured AMR+EB integration: fluid_volume="
      <<volume<<", mass_rate=1, solid_volume="<<solid_volume
      <<", ranks="<<amrex::ParallelDescriptor::NProcs()<<"\n";
  }
  amrex::Finalize();
}
