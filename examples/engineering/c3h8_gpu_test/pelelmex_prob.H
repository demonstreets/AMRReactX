#ifndef PELELM_PROB_H
#define PELELM_PROB_H
#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>
#include <PeleLMeX_ProblemSpecificFunctions.H>
#include <PeleLMeX_Index.H>
#include <PelePhysics.H>
#include <cmath>

struct MyProbParm : public ProbParmDefault {
  amrex::Real P_mean=101325.0, T_mean=300.0;
  amrex::Real wind_u=8.0, wind_v=0.0;
  amrex::Real leak_xc=25.5, leak_yc=20.0, leak_zc=20.0;
  amrex::Real leak_rate=0.104, leak_radius=0.011;
  amrex::Real leak_T=300.0;
  amrex::Real ke_inlet_TI=0.10;
  amrex::Real ke_inlet_L=2.0;
};

struct MyProblemSpecificFunctions : public DefaultProblemSpecificFunctions {
  // 3 cylinders EB geometry via UserDefined
  static void EBUserDefined(const amrex::Geometry&, const int, const int);

  AMREX_GPU_DEVICE AMREX_FORCE_INLINE
  static void initdata(int i,int j,int k,int is_incompressible,
    amrex::Array4<amrex::Real> const& state,amrex::Array4<amrex::Real> const&,
    amrex::GeometryData const&,MyProbParm const& pp,
    pele::physics::PMF::PmfData::DataContainer const*){
    auto eos=pele::physics::PhysicsType::eos();
    // Air composition: 23.3% O2, 76.7% N2
    amrex::Real mf[NUM_SPECIES]={0.0};
    mf[O2_ID]=0.233; mf[N2_ID]=0.767;
    state(i,j,k,TEMP)=pp.T_mean;
    state(i,j,k,VELX)=pp.wind_u;
    state(i,j,k,VELY)=pp.wind_v;
    state(i,j,k,VELZ)=0.0;
    amrex::Real P=pp.P_mean*10.0, rho=0.0;  // pressure in dyn/cm²
    eos.PYT2R(P,mf,state(i,j,k,TEMP),rho);
    state(i,j,k,DENSITY)=rho*1e3;            // g/cm³ → kg/m³
    amrex::Real h=0.0;
    eos.TY2H(state(i,j,k,TEMP),mf,h);
    state(i,j,k,RHOH)=h*1e-4*state(i,j,k,DENSITY);  // erg/g → J/kg
    for(int n=0;n<NUM_SPECIES;n++)
      state(i,j,k,FIRSTSPEC+n)=mf[n]*state(i,j,k,DENSITY);
    state(i,j,k,RHORT)=0.0;
  }

  AMREX_GPU_DEVICE AMREX_FORCE_INLINE
  static void bcnormal(const amrex::Real*,const amrex::CellData<amrex::Real>&,
    amrex::Real q[NVAR],const int idir,const int sgn,const amrex::Real,
    amrex::GeometryData const&,MyProbParm const& pp,
    pele::physics::PMF::PmfData::DataContainer const*){
    auto eos=pele::physics::PhysicsType::eos();
    // Air composition
    amrex::Real mf[NUM_SPECIES]={0.0};
    mf[O2_ID]=0.233; mf[N2_ID]=0.767;
    // Inflow on lo-x and lo-y (sgn==1 per PeleLMeX convention)
    if((idir==0 && sgn==1) || (idir==1 && sgn==1)){
      amrex::Real P=pp.P_mean*10.0, rho=0.0;
      eos.PYT2R(P,mf,pp.T_mean,rho);
      q[TEMP]=pp.T_mean;
      q[DENSITY]=rho*1e3;
      q[VELX]=pp.wind_u;
      q[VELY]=pp.wind_v;
      q[VELZ]=0.0;
      amrex::Real h=0.0;
      eos.TY2H(q[TEMP],mf,h);
      q[RHOH]=h*1e-4*q[DENSITY];
      for(int n=0;n<NUM_SPECIES;n++)
        q[FIRSTSPEC+n]=mf[n]*q[DENSITY];
      q[RHORT]=0.0;
    }
  }

  static void modify_ext_sources(amrex::Real,amrex::Real dt,
    const amrex::MultiFab&,const amrex::MultiFab&,
    std::unique_ptr<amrex::MultiFab>& ext_src,
    const amrex::GeometryData& geomdata,const MyProbParm* pp){
    amrex::ignore_unused(dt);
    if (!ext_src) return;
#ifdef AMREX_USE_GPU
    MyProbParm pp_host;
    amrex::Gpu::copy(amrex::Gpu::deviceToHost, pp, pp + 1, &pp_host);
    amrex::Gpu::streamSynchronize();
    const MyProbParm& prob = pp_host;
#else
    const MyProbParm& prob = *pp;
#endif
    auto eos=pele::physics::PhysicsType::eos();
    const amrex::Real cx=prob.leak_xc,cy=prob.leak_yc,cz=prob.leak_zc;
    const amrex::Real* plo=geomdata.ProbLo();
    const amrex::Real* dx=geomdata.CellSize();
    const amrex::Real plo0=plo[0], plo1=plo[1], plo2=plo[2];
    const amrex::Real dx0=dx[0], dx1=dx[1], dx2=dx[2];
    // Ensure source radius >= 1 grid cell for numerical stability
    const amrex::Real r_phys=prob.leak_radius;
    const amrex::Real dx_min=std::min({dx0,dx1,dx2});
    const amrex::Real r_eff=std::max(r_phys, dx_min);
    const amrex::Real r2=r_eff*r_eff;
    // Jet velocity = mdot/(rho*area)
    // For source term: src_strength = mdot / volume_of_source_region
    constexpr amrex::Real PI=3.141592653589793;
    const amrex::Real src_vol=(4.0/3.0)*PI*r_eff*r_eff*r_eff;
    const amrex::Real src_str=prob.leak_rate/src_vol;  // kg/(m³·s)
    // Leak gas: pure C3H8
    amrex::Real mf[NUM_SPECIES]={0.0};
    mf[C3H8_ID]=1.0;
    // Compute enthalpy of injected gas
    amrex::Real h_cgs=0.0;
    eos.TY2H(prob.leak_T,mf,h_cgs);
    amrex::Real h_inj=h_cgs*1e-4;  // erg/g → J/kg
    // Compute density and velocity for momentum injection
    amrex::Real P=prob.P_mean*10.0, rho_inj=0.0;
    eos.PYT2R(P,mf,prob.leak_T,rho_inj);
    rho_inj*=1e3;  // g/cm³ → kg/m³
    const amrex::Real area=PI*r_phys*r_phys;
    const amrex::Real v_jet=prob.leak_rate/(rho_inj*area);  // m/s
    const amrex::Real ke=0.5*v_jet*v_jet;
    const amrex::Real vx=v_jet, vy=0.0, vz=0.0;
    auto const& src_arrs=ext_src->arrays();
    amrex::ParallelFor(*ext_src,[=]AMREX_GPU_DEVICE(int nbx,int i,int j,int k)noexcept{
      amrex::Real x=plo0+(i+0.5)*dx0;
      amrex::Real y=plo1+(j+0.5)*dx1;
      amrex::Real z=plo2+(k+0.5)*dx2;
      amrex::Real dist2=(x-cx)*(x-cx)+(y-cy)*(y-cy)+(z-cz)*(z-cz);
      if(dist2<r2){
        src_arrs[nbx](i,j,k,FIRSTSPEC+C3H8_ID)+=src_str;
        src_arrs[nbx](i,j,k,VELX)+=src_str*vx;
        src_arrs[nbx](i,j,k,VELY)+=src_str*vy;
        src_arrs[nbx](i,j,k,VELZ)+=src_str*vz;
        src_arrs[nbx](i,j,k,RHOH)+=src_str*(h_inj+ke);
      }
    });
    amrex::Gpu::streamSynchronize();
  }

  AMREX_GPU_DEVICE AMREX_FORCE_INLINE
  static void bcnormal_aux(
    const amrex::Real[AMREX_SPACEDIM],
    amrex::CellData<amrex::Real>& aux_ext,
    const int idir, const int sgn,
    const amrex::Real,
    amrex::GeometryData const&,
    MyProbParm const& pp,
    pele::physics::PMF::PmfData::DataContainer const*)
  {
    if((idir==0 && sgn==1) || (idir==1 && sgn==1)){
      const amrex::Real U=std::sqrt(pp.wind_u*pp.wind_u + pp.wind_v*pp.wind_v);
      const amrex::Real I=pp.ke_inlet_TI;
      aux_ext[0]=1.5*(I*U)*(I*U);
      aux_ext[1]=0.164316767*std::pow(aux_ext[0],1.5)/pp.ke_inlet_L;
      for (int n=2; n<aux_ext.ncomp; ++n) aux_ext[n]=1.0e-6;
    } else {
      for (int n=0; n<aux_ext.ncomp; ++n) aux_ext[n]=1.0e-6;
    }
  }
};
using ProblemSpecificFunctions=MyProblemSpecificFunctions;
using ProbParm=MyProbParm;
#endif
