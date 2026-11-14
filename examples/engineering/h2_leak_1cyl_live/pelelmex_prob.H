#ifndef PELELM_PROB_H
#define PELELM_PROB_H
#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>
#include <PeleLMeX_ProblemSpecificFunctions.H>
#include <PeleLMeX_Index.H>
#include <PelePhysics.H>

struct MyProbParm : public ProbParmDefault {
  amrex::Real P_mean=101325.0, T_mean=300.0;
  amrex::Real wind_u=8.485, wind_v=8.485;
  amrex::Real leak_xc=25.0, leak_yc=6.19, leak_zc=15.0;
  amrex::Real leak_rate=0.104, leak_radius=1.0;
  amrex::Real leak_vel_x=0.0, leak_vel_y=-20.0, leak_vel_z=0.0;
  amrex::Real leak_T=233.15;
};

struct MyProblemSpecificFunctions : public DefaultProblemSpecificFunctions {
  AMREX_GPU_DEVICE AMREX_FORCE_INLINE
  static void initdata(int i,int j,int k,int is_incompressible,
    amrex::Array4<amrex::Real> const& state,amrex::Array4<amrex::Real> const&,
    amrex::GeometryData const&,MyProbParm const& pp,
    pele::physics::PMF::PmfData::DataContainer const*){
    auto eos=pele::physics::PhysicsType::eos();
    amrex::Real mf[NUM_SPECIES]={0.0}; mf[O2_ID]=0.233; mf[N2_ID]=0.767;
    state(i,j,k,TEMP)=pp.T_mean;
    state(i,j,k,VELX)=pp.wind_u; state(i,j,k,VELY)=pp.wind_v; state(i,j,k,VELZ)=0.0;
    amrex::Real P=pp.P_mean*10.0, rho=0.0;
    eos.PYT2R(P,mf,state(i,j,k,TEMP),rho); state(i,j,k,DENSITY)=rho*1e3;
    amrex::Real h=0.0; eos.TY2H(state(i,j,k,TEMP),mf,h);
    state(i,j,k,RHOH)=h*1e-4*state(i,j,k,DENSITY);
    for(int n=0;n<NUM_SPECIES;n++)state(i,j,k,FIRSTSPEC+n)=mf[n]*state(i,j,k,DENSITY);
    state(i,j,k,RHORT)=0.0;
  }
  AMREX_GPU_DEVICE AMREX_FORCE_INLINE
  static void bcnormal(const amrex::Real*,const amrex::CellData<amrex::Real>&,
    amrex::Real q[NVAR],const int idir,const int sgn,const amrex::Real,
    amrex::GeometryData const&,MyProbParm const& pp,
    pele::physics::PMF::PmfData::DataContainer const*){
    auto eos=pele::physics::PhysicsType::eos();
    amrex::Real mf[NUM_SPECIES]={0.0}; mf[O2_ID]=0.233; mf[N2_ID]=0.767;
    if((idir==0&&sgn==1)||(idir==1&&sgn==1)){
      amrex::Real P=pp.P_mean*10.0, rho=0.0;
      eos.PYT2R(P,mf,pp.T_mean,rho);
      q[TEMP]=pp.T_mean; q[DENSITY]=rho*1e3;
      q[VELX]=pp.wind_u; q[VELY]=pp.wind_v; q[VELZ]=0.0;
      amrex::Real h=0.0; eos.TY2H(q[TEMP],mf,h);
      q[RHOH]=h*1e-4*q[DENSITY];
      for(int n=0;n<NUM_SPECIES;n++)q[FIRSTSPEC+n]=mf[n]*q[DENSITY];
      q[RHORT]=0.0;
    }
  }
  static void modify_ext_sources(amrex::Real,amrex::Real dt,
    const amrex::MultiFab&,const amrex::MultiFab&,
    std::unique_ptr<amrex::MultiFab>& ext_src,
    const amrex::GeometryData& geomdata,const MyProbParm* pp){
    auto eos=pele::physics::PhysicsType::eos();
    const amrex::Real cx=pp->leak_xc,cy=pp->leak_yc,cz=pp->leak_zc;
    const amrex::Real r2=pp->leak_radius*pp->leak_radius;
    constexpr amrex::Real PI=3.141592653589793;
    const amrex::Real src_vol=(4.0/3.0)*PI*pp->leak_radius*pp->leak_radius*pp->leak_radius;
    const amrex::Real src_str=pp->leak_rate/src_vol;
    amrex::Real mf[NUM_SPECIES]={0.0}; mf[H2_ID]=1.0;
    amrex::Real P=pp->P_mean*10.0, h_cgs=0.0;
    eos.TY2H(pp->leak_T,mf,h_cgs);
    amrex::Real vx=pp->leak_vel_x,vy=pp->leak_vel_y,vz=pp->leak_vel_z;
    amrex::Real ke=0.5*(vx*vx+vy*vy+vz*vz);
    amrex::Real h_inj=h_cgs*1e-4;
    const amrex::Real* plo=geomdata.ProbLo();
    const amrex::Real* dx=geomdata.CellSize();
    auto const& src_arrs=ext_src->arrays();
    amrex::ParallelFor(*ext_src,[=]AMREX_GPU_DEVICE(int nbx,int i,int j,int k)noexcept{
      amrex::Real x=plo[0]+(i+0.5)*dx[0], y=plo[1]+(j+0.5)*dx[1], z=plo[2]+(k+0.5)*dx[2];
      amrex::Real dist2=(x-cx)*(x-cx)+(y-cy)*(y-cy)+(z-cz)*(z-cz);
      if(dist2<r2){
        src_arrs[nbx](i,j,k,FIRSTSPEC+H2_ID)+=src_str;
        src_arrs[nbx](i,j,k,VELX)+=src_str*vx;
        src_arrs[nbx](i,j,k,VELY)+=src_str*vy;
        src_arrs[nbx](i,j,k,VELZ)+=src_str*vz;
        src_arrs[nbx](i,j,k,RHOH)+=src_str*(h_inj+ke);
      }
    });
    amrex::Gpu::streamSynchronize();
  }
};
using ProblemSpecificFunctions=MyProblemSpecificFunctions;
using ProbParm=MyProbParm;
#endif