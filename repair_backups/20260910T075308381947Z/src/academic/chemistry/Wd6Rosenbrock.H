#ifndef MY_PELE_WD6_ROSENBROCK_H
#define MY_PELE_WD6_ROSENBROCK_H
#include <mechanism.H>
#include <cmath>
#include <algorithm>

// A model-specific, locally adaptive linearly implicit Euler integrator.
// Step doubling controls error; the two-half-step solution is accepted.
// Variables are mol/m^3. Temperature is determined by conserved internal
// energy, rather than advanced as an independent seventh unknown.
namespace academic::wd6 {
static_assert(NUM_SPECIES==6 && nc7h16_ID==0 && o2_ID==1 && co_ID==2 &&
              h2o_ID==3 && co2_ID==4 && n2_ID==5);
using Real=amrex::Real;
constexpr Real R=8.31446261815324;

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
void thermo(const Real* c,Real T,Real& energy,Real& capacity,Real* molar_u) {
  Real u[6],cv[6];speciesInternalEnergy(u,T);cv_R(cv,T);
  energy=0.;capacity=0.;
  for(int n=0;n<6;++n) {
    molar_u[n]=u[n]*R*T;energy+=c[n]*molar_u[n];capacity+=c[n]*cv[n]*R;
  }
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
bool temperature(const Real* c,Real target,Real& T) {
  Real lo=90.,hi=10000.,energy,capacity,u[6];
  if(!std::isfinite(T)||T<lo||T>hi)return false;
  for(int it=0;it<60;++it) {
    thermo(c,T,energy,capacity,u);
    if(!std::isfinite(energy)||!std::isfinite(capacity)||capacity<=0.)return false;
    Real scale=std::abs(target);
    for(int n=0;n<6;++n)scale+=std::abs(c[n]*u[n]);
    Real residual=energy-target;
    if(std::abs(residual)<=1.e-12*std::max(scale,1.))return true;
    if(residual>0.)hi=T;else lo=T;
    Real proposal=T-residual/capacity;
    T=(proposal>lo&&proposal<hi)?proposal:0.5*(lo+hi);
  }
  return false;
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
bool solve6(Real A[6][6],Real* rhs) {
  for(int k=0;k<6;++k) {
    int pivot=k;
    for(int i=k+1;i<6;++i)if(std::abs(A[i][k])>std::abs(A[pivot][k]))pivot=i;
    if(!std::isfinite(A[pivot][k])||std::abs(A[pivot][k])<1.e-250)return false;
    if(pivot!=k) {
      for(int j=k;j<6;++j) {Real v=A[k][j];A[k][j]=A[pivot][j];A[pivot][j]=v;}
      Real v=rhs[k];rhs[k]=rhs[pivot];rhs[pivot]=v;
    }
    for(int i=k+1;i<6;++i) {
      const Real multiplier=A[i][k]/A[k][k];
      for(int j=k+1;j<6;++j)A[i][j]-=multiplier*A[k][j];
      rhs[i]-=multiplier*rhs[k];
    }
  }
  for(int i=5;i>=0;--i) {
    for(int j=i+1;j<6;++j)rhs[i]-=A[i][j]*rhs[j];
    rhs[i]/=A[i][i];if(!std::isfinite(rhs[i]))return false;
  }
  return true;
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
bool step(const Real* c,Real T,Real h,Real target,Real mass,
          const Real* weights,Real* out,Real& Tout) {
  Real rates[6],jac[49],energy,capacity,u[6];
  productionRate(rates,c,T);aJacobian(jac,c,T,0);thermo(c,T,energy,capacity,u);
  if(!std::isfinite(capacity)||capacity<=0.)return false;
  Real A[6][6],delta[6];
  for(int i=0;i<6;++i) {
    delta[i]=h*rates[i];
    for(int j=0;j<6;++j) {
      // Exact chain rule for T(c,U): dT/dc_j=-u_j/sum(c*Cv).
      const Real derivative=jac[7*j+i]-jac[42+i]*u[j]/capacity;
      A[i][j]=(i==j?1.:0.)-h*derivative;
    }
  }
  if(!solve6(A,delta))return false;
  Real sum=0.;
  for(int n=0;n<6;++n) {
    out[n]=c[n]+delta[n];const Real y=out[n]*weights[n]/mass;
    if(!std::isfinite(y)||y< -1.e-12||y>1.+1.e-12)return false;
    sum+=out[n]*weights[n];
  }
  if(std::abs(sum-mass)>1.e-10*mass)return false;
  Tout=T;return temperature(out,target,Tout);
}

struct Statistics {int accepted=0,rejected=0;};

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
bool integrate(Real* c,Real& T,Real duration,Real target,Real mass,
               Real rtol,Real atol_y,Statistics& statistics) {
  Real weights[6];get_mw(weights);
  Real elapsed=0.,h=duration;
  if(!(duration>0.)||!(mass>0.)||!(rtol>0.)||!(atol_y>0.))return false;
  for(int iteration=0;iteration<20000 && elapsed<duration;++iteration) {
    h=std::min(h,duration-elapsed);
    if(elapsed+h==elapsed)return false;
    Real coarse[6],half[6],fine[6],Tc,Th,Tf;
    const bool valid=step(c,T,h,target,mass,weights,coarse,Tc) &&
      step(c,T,0.5*h,target,mass,weights,half,Th) &&
      step(half,Th,0.5*h,target,mass,weights,fine,Tf);
    if(!valid) {h*=0.25;++statistics.rejected;continue;}
    Real error=std::abs(Tf-Tc)/(1.e-6+rtol*std::max(std::abs(T),std::abs(Tf)));
    for(int n=0;n<6;++n) {
      const Real y0=c[n]*weights[n]/mass,yf=fine[n]*weights[n]/mass;
      const Real difference=std::abs(fine[n]-coarse[n])*weights[n]/mass;
      error=std::max(error,difference/(atol_y+rtol*std::max(std::abs(y0),std::abs(yf))));
    }
    if(!std::isfinite(error))return false;
    if(error<=1.) {
      for(int n=0;n<6;++n)c[n]=fine[n];T=Tf;elapsed+=h;++statistics.accepted;
    } else ++statistics.rejected;
    const Real factor=error>0.?0.85/std::sqrt(error):4.;
    h*=std::min(4.,std::max(0.1,factor));
  }
  return elapsed>=duration;
}
} // namespace academic::wd6
#endif
