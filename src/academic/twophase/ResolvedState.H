#pragma once
#include "MechanicalEquilibriumEOS.H"
#include "Fuego.H"

namespace MyPele::Academic::TwoPhase {

// Both EOS choices are explicit in inputs. The constant-gamma option is for
// canonical nondimensional hydrodynamic benchmarks; Fuego uses physical CGS.
struct ResolvedGasEOS {
    bool fuego=true;
    amrex::Real gamma=1.4, cv=1;
    AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
    void RTY2P(amrex::Real r,amrex::Real T,const amrex::Real* Y,amrex::Real& p) const {
        if(fuego)pele::physics::eos::Fuego::RTY2P(r,T,Y,p);else p=(gamma-1)*r*cv*T;
    }
    AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
    void PYT2R(amrex::Real p,const amrex::Real* Y,amrex::Real T,amrex::Real& r) const {
        if(fuego)pele::physics::eos::Fuego::PYT2R(p,Y,T,r);else r=p/((gamma-1)*cv*T);
    }
    AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
    void RYP2T(amrex::Real r,const amrex::Real* Y,amrex::Real p,amrex::Real& T) const {
        if(fuego)pele::physics::eos::Fuego::RYP2T(r,Y,p,T);else T=p/((gamma-1)*r*cv);
    }
    AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
    void RYP2E(amrex::Real r,const amrex::Real* Y,amrex::Real p,amrex::Real& e) const {
        if(fuego)pele::physics::eos::Fuego::RYP2E(r,Y,p,e);else e=p/((gamma-1)*r);
    }
    AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
    void RTY2E(amrex::Real r,amrex::Real T,const amrex::Real* Y,amrex::Real& e) const {
        if(fuego)pele::physics::eos::Fuego::RTY2E(r,T,Y,e);else e=cv*T;
    }
    AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
    void RTY2Cv(amrex::Real r,amrex::Real T,const amrex::Real* Y,amrex::Real& c) const {
        if(fuego)pele::physics::eos::Fuego::RTY2Cv(r,T,Y,c);else c=cv;
    }
    AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
    void RTY2Cs(amrex::Real r,amrex::Real T,const amrex::Real* Y,amrex::Real& c) const {
        if(fuego)pele::physics::eos::Fuego::RTY2Cs(r,T,Y,c);else c=std::sqrt(gamma*(gamma-1)*cv*T);
    }
};

inline constexpr int MG=0,ML=1,MX=2,MY=3,MZ=4,ET=5,ALPHA=6,SPEC=7;
inline constexpr int NSTATE=SPEC+NUM_SPECIES;

struct ResolvedPrimitive {
    MechanicalState thermo;
    amrex::Real u[3]={0,0,0};
    amrex::Real Y[NUM_SPECIES]={};
    amrex::Real rho=0, alpha=0;
};

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
ResolvedPrimitive primitive(const amrex::Real* U,const ResolvedGasEOS& gas,const LiquidCaloricEOS& liquid)
{
    ResolvedPrimitive q;
    q.rho=U[MG]+U[ML];q.alpha=U[ALPHA];
    if(!(q.rho>0))return q;
    amrex::Real kinetic=0,ysum=0;
    for(int d=0;d<3;++d) {q.u[d]=U[MX+d]/q.rho;kinetic+=.5*U[MX+d]*q.u[d];}
    for(int n=0;n<NUM_SPECIES;++n) {
        if(U[SPEC+n]<0 || !std::isfinite(U[SPEC+n]))return q;
        q.Y[n]=U[MG]>0 ? U[SPEC+n]/U[MG]:0;ysum+=q.Y[n];
    }
    if(U[MG]>0 && std::abs(ysum-1)>1.e-10)return q;
    q.thermo=recover_mechanical_state(U[MG],U[ML],q.alpha,U[ET]-kinetic,q.Y,gas,liquid,
        gas.fuego ? 1.e6:1.,gas.fuego ? 90.:1.e-12,gas.fuego ? 10000.:1.e14);
    return q;
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
void initialize_state(amrex::Real* U,amrex::Real alpha,amrex::Real p,
    amrex::Real rg,amrex::Real rl,const amrex::Real* velocity,const amrex::Real* Y,
    const ResolvedGasEOS& gas,const LiquidCaloricEOS& liquid)
{
    for(int n=0;n<NSTATE;++n)U[n]=0;
    U[MG]=(1-alpha)*rg;U[ML]=alpha*rl;U[ALPHA]=alpha;
    amrex::Real eg;gas.RYP2E(rg,Y,p,eg);
    const amrex::Real el=liquid.reference_energy+(p+liquid.gamma*liquid.pinf)/((liquid.gamma-1)*rl);
    U[ET]=U[MG]*eg+U[ML]*el;
    for(int d=0;d<3;++d) {U[MX+d]=(U[MG]+U[ML])*velocity[d];U[ET]+=.5*U[MX+d]*velocity[d];}
    for(int n=0;n<NUM_SPECIES;++n)U[SPEC+n]=U[MG]*Y[n];
}

struct AcousticFace {amrex::Real velocity,pressure;};

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
AcousticFace acoustic_face(const ResolvedPrimitive& l,const ResolvedPrimitive& r,int dir)
{
    const amrex::Real jump=std::abs(l.u[dir]-r.u[dir]);
    // Relaxation impedance includes nonlinear compression. No pressure floor
    // or cell-energy clipping is used: inadmissible trial steps are rejected.
    const amrex::Real zl=l.rho*(l.thermo.c+1.5*jump);
    const amrex::Real zr=r.rho*(r.thermo.c+1.5*jump);
    return {(zl*l.u[dir]+zr*r.u[dir]+l.thermo.p-r.thermo.p)/(zl+zr),
            (zr*l.thermo.p+zl*r.thermo.p+zl*zr*(l.u[dir]-r.u[dir]))/(zl+zr)};
}

} // namespace MyPele::Academic::TwoPhase
