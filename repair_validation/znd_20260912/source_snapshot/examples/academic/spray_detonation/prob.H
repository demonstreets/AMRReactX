#ifndef PROB_H
#define PROB_H
#include <AMReX_ParmParse.H>
#include <AMReX_Geometry.H>
#include "IndexDefines.H"
#include "Constants.H"
#include "PelePhysics.H"
#include "Tagging.H"
#include "ProblemSpecificFunctions.H"
#include "prob_parm.H"
// A finite-rate ZND profile initializes a freely propagating wave. There is
// no prescribed traveling source or imposed front speed after initialization.
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void pc_initdata(int i,int j,int k,amrex::Array4<amrex::Real> const& s,
                 amrex::GeometryData const& geom,ProbParmDevice const& q) {
  auto lo=geom.ProbLo();auto dx=geom.CellSize();
  amrex::Real x=lo[0]+(i+.5)*dx[0],y=lo[1]+(j+.5)*dx[1];
  const amrex::Real theta=2*3.14159265358979323846*(y-lo[1])/q.width;
  amrex::Real seed=std::cos(theta);
  if(q.perturbation_mode==2)
    seed=(seed+.5*std::cos(2*theta+.7)+.3*std::cos(3*theta+1.9)+
          .2*std::cos(5*theta+2.6))/2.;
  amrex::Real behind=q.front+q.perturbation*seed-x;
  amrex::Real Y[NUM_SPECIES],p=q.p0,T=q.T0,u=0.;
  for(int n=0;n<NUM_SPECIES;++n)Y[n]=q.Y0[n];
  if(behind>=0.) {
    constexpr int stride=NUM_SPECIES+5;
    int a=0,b=q.rows-1;
    while(b-a>1) {int m=(a+b)/2;if(q.profile[m*stride]<=behind)a=m;else b=m;}
    amrex::Real t=(behind-q.profile[a*stride])/(q.profile[b*stride]-q.profile[a*stride]);
    t=amrex::min(1.,amrex::max(0.,t));
    p=(1-t)*q.profile[a*stride+2]+t*q.profile[b*stride+2];
    T=(1-t)*q.profile[a*stride+3]+t*q.profile[b*stride+3];
    u=(1-t)*q.profile[a*stride+4]+t*q.profile[b*stride+4];
    for(int n=0;n<NUM_SPECIES;++n)Y[n]=(1-t)*q.profile[a*stride+5+n]+t*q.profile[b*stride+5+n];
  }
  auto eos=pele::physics::PhysicsType::eos();amrex::Real rho,e;
  eos.PYT2RE(p,Y,T,rho,e);
  s(i,j,k,URHO)=rho;s(i,j,k,UMX)=rho*u;s(i,j,k,UMY)=0.;s(i,j,k,UMZ)=0.;
  s(i,j,k,UEINT)=rho*e;s(i,j,k,UEDEN)=rho*(e+.5*u*u);s(i,j,k,UTEMP)=T;
  for(int n=0;n<NUM_SPECIES;++n)s(i,j,k,UFS+n)=rho*Y[n];
}
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void bcnormal(const amrex::Real*,const amrex::Real a[NVAR],amrex::Real b[NVAR],const int,const int,
              const amrex::Real,amrex::GeometryData const&,ProbParmDevice const&,
              const amrex::GpuArray<amrex::Real,AMREX_SPACEDIM>&) {
  for(int n=0;n<NVAR;++n)b[n]=a[n];
}
void pc_prob_close();
using ProblemSpecificFunctions=DefaultProblemSpecificFunctions;
#endif
