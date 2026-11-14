#include <AMReX.H>
#include <AMReX_MultiFab.H>
#include <AMReX_MFIter.H>
#include <AMReX_ParmParse.H>
#include <AMReX_PlotFileUtil.H>
#include <AMReX_VisMF.H>
#include <AMReX_ParallelDescriptor.H>
#include "ResolvedState.H"
#include "GeometricPLIC.H"
#include <fstream>
#include <iomanip>
#include <filesystem>
#include <sstream>

using namespace amrex;
using namespace MyPele::Academic::TwoPhase;
using namespace MyPele::Academic::VOF;

namespace {
constexpr int NQ=16+NUM_SPECIES;

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
ResolvedPrimitive get_q(Array4<const Real> const& a,IntVect const& iv) {
    ResolvedPrimitive q;q.rho=a(iv,0);q.alpha=a(iv,1);q.thermo.p=a(iv,2);
    for(int d=0;d<3;++d)q.u[d]=a(iv,3+d);
    q.thermo.rhog=a(iv,6);q.thermo.rhol=a(iv,7);q.thermo.eg=a(iv,8);q.thermo.el=a(iv,9);
    q.thermo.c=a(iv,10);q.thermo.K_liquid=a(iv,11);q.thermo.Tg=a(iv,12);q.thermo.Tl=a(iv,13);
    q.thermo.cg=a(iv,14);q.thermo.cl=a(iv,15);
    for(int n=0;n<NUM_SPECIES;++n)q.Y[n]=a(iv,16+n);
    return q;
}

void fill_physical(MultiFab& U,Geometry const& geom,GpuArray<int,3> const& wall_lo,GpuArray<int,3> const& wall_hi) {
    U.FillBoundary(geom.periodicity());
    const int ncomp=U.nComp();
    const auto domain=geom.Domain();const auto low=domain.smallEnd(),high=domain.bigEnd();
    GpuArray<int,3> periodic{0,0,0};for(int d=0;d<AMREX_SPACEDIM;++d)periodic[d]=geom.isPeriodic(d);
    for(MFIter mfi(U);mfi.isValid();++mfi) {
        const auto box=mfi.fabbox();const auto a=U.array(mfi);
        ParallelFor(box,[=] AMREX_GPU_DEVICE(int i,int j,int k) noexcept {
            IntVect iv(AMREX_D_DECL(i,j,k)),src=iv;bool outside=false;
            int reflection[3]={0,0,0};
            for(int d=0;d<AMREX_SPACEDIM;++d) {
                if(periodic[d])continue;
                if(iv[d]<low[d]) {outside=true;reflection[d]=wall_lo[d];src[d]=wall_lo[d] ? 2*low[d]-iv[d]-1:low[d];}
                if(iv[d]>high[d]) {outside=true;reflection[d]=wall_hi[d];src[d]=wall_hi[d] ? 2*high[d]-iv[d]+1:high[d];}
            }
            if(outside)for(int n=0;n<ncomp;++n) {
                Real value=a(src,n);
                if(n>=MX && n<=MZ && reflection[n-MX])value=-value;
                a(iv,n)=value;
            }
        });
    }
}

bool recover(MultiFab const& U,MultiFab& Q,ResolvedGasEOS gas,LiquidCaloricEOS liquid,int nghost=0) {
    MultiFab invalid(U.boxArray(),U.DistributionMap(),1,0);invalid.setVal(0);
    for(MFIter mfi(U);mfi.isValid();++mfi) {
        const auto a=U.const_array(mfi);const auto q=Q.array(mfi),bad=invalid.array(mfi);
        const auto valid=mfi.validbox();const auto box=grow(valid,nghost);
        ParallelFor(box,[=] AMREX_GPU_DEVICE(int i,int j,int k) noexcept {
            Real state[NSTATE];for(int n=0;n<NSTATE;++n)state[n]=a(i,j,k,n);
            const auto p=primitive(state,gas,liquid);
            if(!p.thermo.valid) {
                if(valid.contains(IntVect(AMREX_D_DECL(i,j,k))))bad(i,j,k)=1;
                // Ghost validity follows from valid cells and the physical fill.
            }
            q(i,j,k,0)=p.rho;q(i,j,k,1)=p.alpha;q(i,j,k,2)=p.thermo.p;
            for(int d=0;d<3;++d)q(i,j,k,3+d)=p.u[d];
            q(i,j,k,6)=p.thermo.rhog;q(i,j,k,7)=p.thermo.rhol;
            q(i,j,k,8)=p.thermo.eg;q(i,j,k,9)=p.thermo.el;
            q(i,j,k,10)=p.thermo.c;q(i,j,k,11)=p.thermo.K_liquid;
            q(i,j,k,12)=p.thermo.Tg;q(i,j,k,13)=p.thermo.Tl;
            q(i,j,k,14)=p.thermo.cg;q(i,j,k,15)=p.thermo.cl;
            for(int n=0;n<NUM_SPECIES;++n)q(i,j,k,16+n)=p.Y[n];
        });
    }
    return invalid.max(0)==0;
}

// One conservative acoustic/Lagrangian step and geometric remap. All phasic
// masses, species, momentum and energy use the very same swept phase volumes.
bool directional_step(MultiFab const& in,MultiFab& out,Geometry const& geom,
    ResolvedGasEOS gas,LiquidCaloricEOS liquid,GpuArray<int,3> wl,GpuArray<int,3> wh,
    int direction,Real dt) {
    const auto ba=in.boxArray();const auto dm=in.DistributionMap();
    MultiFab work(ba,dm,NSTATE,2);MultiFab::Copy(work,in,0,0,NSTATE,0);
    fill_physical(work,geom,wl,wh);
    MultiFab q(ba,dm,NQ,2);if(!recover(work,q,gas,liquid,2))return false;
    const auto dv=IntVect::TheDimensionVector(direction);const Real h=geom.CellSize(direction),C=dt/h;
    BoxArray fb=convert(ba,IntVect::TheDimensionVector(direction));
    MultiFab face(fb,dm,2,0);
    for(MFIter mfi(face);mfi.isValid();++mfi) {
        const auto f=face.array(mfi);const auto qa=q.const_array(mfi);
        ParallelFor(mfi.validbox(),[=] AMREX_GPU_DEVICE(int i,int j,int k) noexcept {
            IntVect iv(AMREX_D_DECL(i,j,k));
            const auto result=acoustic_face(get_q(qa,iv-dv),get_q(qa,iv),direction);
            f(iv,0)=result.velocity;f(iv,1)=result.pressure;
        });
    }
    MultiFab lag(ba,dm,NSTATE,2),jacobian(ba,dm,1,2),bad(ba,dm,1,0);bad.setVal(0);
    for(MFIter mfi(lag);mfi.isValid();++mfi) {
        const auto a=work.const_array(mfi);const auto l=lag.array(mfi),jcb=jacobian.array(mfi);
        const auto f=face.const_array(mfi),qa=q.const_array(mfi);const auto b=bad.array(mfi);
        ParallelFor(mfi.validbox(),[=] AMREX_GPU_DEVICE(int i,int j,int k) noexcept {
            IntVect iv(AMREX_D_DECL(i,j,k));const Real div=C*(f(iv+dv,0)-f(iv,0));
            const Real J=1+div;jcb(iv)=J;
            if(!(J>.2 && std::isfinite(J))) {b(iv)=1;return;}
            for(int n=0;n<NSTATE;++n)l(iv,n)=a(iv,n)/J;
            l(iv,MX+direction)=(a(iv,MX+direction)-C*(f(iv+dv,1)-f(iv,1)))/J;
            l(iv,ET)=(a(iv,ET)-C*(f(iv+dv,0)*f(iv+dv,1)-f(iv,0)*f(iv,1)))/J;
            l(iv,ALPHA)=a(iv,ALPHA)+qa(iv,11)*div/J;
        });
    }
    if(bad.max(0)>0)return false;
    fill_physical(lag,geom,wl,wh);
    // J is a scalar: extrapolate it without reflecting any component.
    fill_physical(jacobian,geom,wl,wh);
    MultiFab qlag(ba,dm,NQ,2);if(!recover(lag,qlag,gas,liquid,2))return false;
    MultiFab planes(ba,dm,4,1);
    for(MFIter mfi(planes);mfi.isValid();++mfi) {
        const auto l=lag.const_array(mfi);const auto p=planes.array(mfi);
        ParallelFor(grow(mfi.validbox(),1),[=] AMREX_GPU_DEVICE(int i,int j,int k) noexcept {
            const IntVect iv(AMREX_D_DECL(i,j,k));Real normal[3]={0,0,0};
            for(int d=0;d<AMREX_SPACEDIM;++d) {
                const auto e=IntVect::TheDimensionVector(d);
                normal[d]=l(iv-e,ALPHA)-l(iv+e,ALPHA);
            }
            const auto result=reconstruct_geometric_plane(normal,l(iv,ALPHA),AMREX_SPACEDIM);
            for(int d=0;d<3;++d)p(iv,d)=result.n[d];p(iv,3)=result.c;
        });
    }
    // Integrated transported quantities per reference cell volume, with the
    // sign of the face velocity. Extra component stores swept gas volume.
    MultiFab flux(fb,dm,NSTATE+1,0);
    for(MFIter mfi(flux);mfi.isValid();++mfi) {
        const auto f=face.const_array(mfi),p=planes.const_array(mfi);const auto fl=flux.array(mfi);
        const auto qa=qlag.const_array(mfi),jcb=jacobian.const_array(mfi);
        ParallelFor(mfi.validbox(),[=] AMREX_GPU_DEVICE(int i,int j,int k) noexcept {
            const IntVect iv(AMREX_D_DECL(i,j,k));const Real courant=f(iv,0)*C;
            const IntVect donor=courant>=0 ? iv-dv:iv;const Real J=jcb(donor);
            GeometricPlane plane;plane.dim=AMREX_SPACEDIM;
            for(int d=0;d<3;++d)plane.n[d]=p(donor,d);plane.c=p(donor,3);
            const auto state=get_q(qa,donor);
            const Real liquid_v=state.alpha==0 ? 0:(state.alpha==1 ? std::abs(courant):
                J*geometric_swept_volume(plane,direction,courant/J));
            const Real gas_v=std::abs(courant)-liquid_v,sign=courant>=0 ? 1:-1;
            const Real mg=gas_v*state.thermo.rhog,ml=liquid_v*state.thermo.rhol;
            fl(iv,MG)=sign*mg;fl(iv,ML)=sign*ml;fl(iv,ALPHA)=sign*liquid_v;fl(iv,NSTATE)=sign*gas_v;
            Real kinetic=0;
            for(int d=0;d<3;++d) {fl(iv,MX+d)=sign*(mg+ml)*state.u[d];kinetic+=.5*state.u[d]*state.u[d];}
            fl(iv,ET)=sign*(mg*state.thermo.eg+ml*state.thermo.el+(mg+ml)*kinetic);
            for(int n=0;n<NUM_SPECIES;++n)fl(iv,SPEC+n)=sign*mg*state.Y[n];
        });
    }
    for(MFIter mfi(out);mfi.isValid();++mfi) {
        const auto a=out.array(mfi),b=bad.array(mfi);const auto fl=flux.const_array(mfi),p=planes.const_array(mfi);
        const auto qa=qlag.const_array(mfi),jcb=jacobian.const_array(mfi),f=face.const_array(mfi);
        ParallelFor(mfi.validbox(),[=] AMREX_GPU_DEVICE(int i,int j,int k) noexcept {
            const IntVect iv(AMREX_D_DECL(i,j,k));const Real J=jcb(iv);
            const Real left=f(iv,0)<0 ? -f(iv,0)*C/J:0;
            const Real right=f(iv+dv,0)>0 ? f(iv+dv,0)*C/J:0;
            const Real width=1-left-right;
            if(!(width>=0)) {b(iv)=1;return;}
            Real normal[3]={p(iv,0),p(iv,1),p(iv,2)};
            const Real constant=p(iv,3)-normal[direction]*left;normal[direction]*=width;
            const auto state=get_q(qa,iv);
            const Real vf=state.alpha==0 ? 0:(state.alpha==1 ? 1:plane_unit_volume(normal,constant,AMREX_SPACEDIM));
            const Real vl=J*width*vf,vg=J*width*(1-vf);
            const Real mg=vg*state.thermo.rhog,ml=vl*state.thermo.rhol;
            a(iv,MG)=mg;a(iv,ML)=ml;a(iv,ALPHA)=vl;Real kinetic=0;
            for(int d=0;d<3;++d) {a(iv,MX+d)=(mg+ml)*state.u[d];kinetic+=.5*state.u[d]*state.u[d];}
            a(iv,ET)=mg*state.thermo.eg+ml*state.thermo.el+(mg+ml)*kinetic;
            for(int n=0;n<NUM_SPECIES;++n)a(iv,SPEC+n)=mg*state.Y[n];
            Real gas_volume=vg;
            if(f(iv,0)>0) {for(int n=0;n<NSTATE;++n)a(iv,n)+=fl(iv,n);gas_volume+=fl(iv,NSTATE);}
            if(f(iv+dv,0)<0) {for(int n=0;n<NSTATE;++n)a(iv,n)-=fl(iv+dv,n);gas_volume-=fl(iv+dv,NSTATE);}
            const Real total_volume=a(iv,ALPHA)+gas_volume;
            if(!(std::abs(total_volume-1)<1.e-10)) {b(iv)=1;return;}
            // Normalization of a geometrically unit volume removes only roundoff,
            // not mass. Both phase volumes are nonnegative by construction.
            a(iv,ALPHA)/=total_volume;
        });
    }
    return bad.max(0)==0 && recover(out,q,gas,liquid);
}

struct Setup {
    ResolvedGasEOS gas;
    LiquidCaloricEOS liquid{4.4,6.e9,4.18e7,0};
    GpuArray<Real,3> velocity{0,0,0},center{.5,.5,.5};
    GpuArray<Real,NUM_SPECIES> Y{};
    GpuArray<int,3> wall_lo{0,0,0},wall_hi{0,0,0};
    Real pressure=1.e6,gas_density=.001,liquid_density=1,alpha=.5,radius=.15;
    Real pressure_right=1.e6,gas_density_right=.001,liquid_density_right=1,alpha_right=0,diaphragm=.5;
    Real wave_amplitude=1.e-4;
    int shape=0;
};

void initialize(MultiFab& U,Geometry const& geom,Setup s) {
    const auto dx=geom.CellSizeArray(),lo=geom.ProbLoArray();
    const Real length=geom.ProbHi(0)-geom.ProbLo(0);
    for(MFIter mfi(U);mfi.isValid();++mfi) {
        const auto a=U.array(mfi);
        ParallelFor(mfi.validbox(),[=] AMREX_GPU_DEVICE(int i,int j,int k) noexcept {
            Real x[3]={0,0,0};x[0]=lo[0]+(i+.5)*dx[0];x[1]=lo[1]+(j+.5)*dx[1];
#if AMREX_SPACEDIM==3
            x[2]=lo[2]+(k+.5)*dx[2];
#endif
            Real alpha=s.alpha,p=s.pressure,rg=s.gas_density,rl=s.liquid_density;
            if(s.shape==1) {
                // Initial cell volume is integrated by deterministic subcells.
                // It is not a center-point mask whose mass changes with resolution.
                int inside=0;constexpr int sub=8;
                for(int sy=0;sy<sub;++sy)for(int sx=0;sx<sub;++sx) {
                    Real r2=0;
                    const Real xx=x[0]+((sx+.5)/sub-.5)*dx[0]-s.center[0];
                    const Real yy=x[1]+((sy+.5)/sub-.5)*dx[1]-s.center[1];
                    r2=xx*xx+yy*yy;
#if AMREX_SPACEDIM==3
                    // A cylindrical interface is the explicitly defined 3-D extrusion.
#endif
                    if(r2<s.radius*s.radius)++inside;
                }
                alpha=Real(inside)/(sub*sub);
            } else if(s.shape==2) {
                const Real fraction=(s.diaphragm-(x[0]-.5*dx[0]))/dx[0];
                if(fraction<=0) {alpha=s.alpha_right;p=s.pressure_right;rg=s.gas_density_right;rl=s.liquid_density_right;}
                else if(fraction<1) {
                    // Discontinuities with unequal pressure must align to a face.
                    alpha=s.alpha*fraction+s.alpha_right*(1-fraction);
                }
            }
            Real state[NSTATE];initialize_state(state,alpha,p,rg,rl,s.velocity.data(),s.Y.data(),s.gas,s.liquid);
            if(s.shape==3) {
                const auto base=primitive(state,s.gas,s.liquid);
                const Real dp=s.pressure*s.wave_amplitude*std::sin(2*3.14159265358979323846*(x[0]-lo[0])/length);
                const Real bulk=base.rho*base.thermo.c*base.thermo.c;
                Real v[3]={s.velocity[0],s.velocity[1],s.velocity[2]};
                v[0]+=dp/(base.rho*base.thermo.c);
                alpha-=base.thermo.K_liquid*dp/bulk;
                rg+=dp/(base.thermo.cg*base.thermo.cg);
                rl+=dp/(base.thermo.cl*base.thermo.cl);
                initialize_state(state,alpha,p+dp,rg,rl,v,s.Y.data(),s.gas,s.liquid);
            }
            for(int n=0;n<NSTATE;++n)a(i,j,k,n)=state[n];
        });
    }
}

void plot(MultiFab const& U,Geometry const& geom,Setup const& s,int step,Real time) {
    MultiFab q(U.boxArray(),U.DistributionMap(),NQ,0);
    if(!recover(U,q,s.gas,s.liquid))Abort("invalid state before output");
    MultiFab fields(U.boxArray(),U.DistributionMap(),NSTATE+NQ,0);
    MultiFab::Copy(fields,U,0,0,NSTATE,0);MultiFab::Copy(fields,q,0,NSTATE,NQ,0);
    Vector<std::string> names{"gas_mass_density","liquid_mass_density","x_momentum","y_momentum","z_momentum","total_energy_density","alpha_liquid"};
    for(int n=0;n<NUM_SPECIES;++n)names.push_back("gas_species_mass_"+std::to_string(n));
    Vector<std::string> primitives{"density","volume_fraction_liquid","pressure","x_velocity","y_velocity","z_velocity","gas_density","liquid_density","gas_internal_energy","liquid_internal_energy","sound_speed","K_liquid","gas_temperature","liquid_temperature","gas_sound_speed","liquid_sound_speed"};
    for(auto const& name:primitives)names.push_back(name);
    for(int n=0;n<NUM_SPECIES;++n)names.push_back("gas_Y_"+std::to_string(n));
    WriteSingleLevelPlotfile(Concatenate("plt",step,7),fields,names,geom,time,step);
}

void diagnostics(MultiFab const& U,Geometry const& geom,Setup const& s,int step,Real time,Real dt,int retries) {
    MultiFab q(U.boxArray(),U.DistributionMap(),NQ,0);if(!recover(U,q,s.gas,s.liquid))Abort("invalid diagnostic state");
    Real volume=1;for(int d=0;d<AMREX_SPACEDIM;++d)volume*=geom.CellSize(d);
    Real mg=U.sum(MG)*volume,ml=U.sum(ML)*volume,E=U.sum(ET)*volume;
    Real mx=U.sum(MX)*volume,my=U.sum(MY)*volume,vl=U.sum(ALPHA)*volume;
    Real amin=U.min(ALPHA),amax=U.max(ALPHA),pmin=q.min(2),pmax=q.max(2),umin=q.min(3),umax=q.max(3);
    if(ParallelDescriptor::IOProcessor()) {
        std::ofstream f("diagnostics.csv",std::ios::app);
        if(f.tellp()==0)f<<"step,time,dt,retries,gas_mass,liquid_mass,total_energy,momentum_x,momentum_y,liquid_volume,alpha_min,alpha_max,p_min,p_max,u_min,u_max\n";
        f<<std::setprecision(17)<<step<<','<<time<<','<<dt<<','<<retries<<','<<mg<<','<<ml<<','<<E<<','<<mx<<','<<my<<','<<vl<<','<<amin<<','<<amax<<','<<pmin<<','<<pmax<<','<<umin<<','<<umax<<'\n';
    }
}

std::string physics_signature(Geometry const& geom,Setup const& s) {
    std::ostringstream out;out<<std::setprecision(17)<<s.gas.fuego<<' '<<s.gas.gamma<<' '<<s.gas.cv<<' '
        <<s.liquid.gamma<<' '<<s.liquid.pinf<<' '<<s.liquid.cv<<' '<<s.liquid.reference_energy;
    for(int d=0;d<AMREX_SPACEDIM;++d)out<<' '<<geom.Domain().length(d)<<' '<<geom.ProbLo(d)<<' '<<geom.ProbHi(d)
        <<' '<<geom.isPeriodic(d)<<' '<<s.wall_lo[d]<<' '<<s.wall_hi[d];
    return out.str();
}

void checkpoint(MultiFab const& U,Geometry const& geom,Setup const& s,int step,Real time) {
    const auto path=Concatenate("chk",step,7);
    if(ParallelDescriptor::IOProcessor()) {
        if(std::filesystem::exists(path))Abort("checkpoint already exists");
        std::filesystem::create_directory(path);
        std::ofstream f(path+"/Header");f<<"ResolvedTwoPhase-v1\n"<<NSTATE<<' '<<AMREX_SPACEDIM<<' '<<step<<' '<<std::setprecision(17)<<time<<'\n';
        f<<physics_signature(geom,s)<<'\n';
    }
    ParallelDescriptor::Barrier();VisMF::Write(U,path+"/State");
}

void run() {
    ParmParse pp("tp");Setup s;
    std::string eos="fuego",shape="uniform";pp.query("gas_eos",eos);pp.query("shape",shape);
    if(eos!="fuego" && eos!="gamma_law")Abort("tp.gas_eos must be fuego or gamma_law");s.gas.fuego=eos=="fuego";
    pp.query("gas_gamma",s.gas.gamma);pp.query("gas_cv",s.gas.cv);
    pp.query("liquid_gamma",s.liquid.gamma);pp.query("liquid_pinf",s.liquid.pinf);
    pp.query("liquid_cv",s.liquid.cv);pp.query("liquid_reference_energy",s.liquid.reference_energy);
    pp.query("pressure",s.pressure);pp.query("gas_density",s.gas_density);pp.query("liquid_density",s.liquid_density);
    pp.query("alpha",s.alpha);pp.query("radius",s.radius);pp.query("diaphragm",s.diaphragm);pp.query("wave_amplitude",s.wave_amplitude);
    s.pressure_right=s.pressure;s.gas_density_right=s.gas_density;s.liquid_density_right=s.liquid_density;
    pp.query("pressure_right",s.pressure_right);pp.query("gas_density_right",s.gas_density_right);
    pp.query("liquid_density_right",s.liquid_density_right);pp.query("alpha_right",s.alpha_right);
    if(shape=="circle")s.shape=1;else if(shape=="interface")s.shape=2;else if(shape=="acoustic_wave")s.shape=3;else if(shape!="uniform")Abort("unknown tp.shape");
    if(s.shape==3 && !(s.alpha>0 && s.alpha<1))Abort("acoustic mixture benchmark needs both phases");
    Vector<Real> velocity(AMREX_SPACEDIM,0),center(AMREX_SPACEDIM,.5);pp.queryarr("velocity",velocity);pp.queryarr("center",center);
    Vector<int> walllo(AMREX_SPACEDIM,0),wallhi(AMREX_SPACEDIM,0);pp.queryarr("wall_lo",walllo);pp.queryarr("wall_hi",wallhi);
    for(int d=0;d<AMREX_SPACEDIM;++d) {s.velocity[d]=velocity[d];s.center[d]=center[d];s.wall_lo[d]=walllo[d];s.wall_hi[d]=wallhi[d];}
    s.Y[N2_ID]=1;Vector<Real> Y(NUM_SPECIES);if(pp.queryarr("gas_mass_fractions",Y)) {
        if(Y.size()!=NUM_SPECIES)Abort("wrong gas_mass_fractions length");for(int n=0;n<NUM_SPECIES;++n)s.Y[n]=Y[n];
    }
    Real ysum=0;for(auto y:s.Y){if(y<0)Abort("negative input gas species");ysum+=y;}if(std::abs(ysum-1)>1.e-12)Abort("gas composition must sum to one");
    Vector<int> ncell(AMREX_SPACEDIM,64);ParmParse amr("amr");amr.getarr("n_cell",ncell);int maxgrid=64;amr.query("max_grid_size",maxgrid);
    int maxlevel=0;amr.query("max_level",maxlevel);if(maxlevel!=0)Abort("resolved driver currently requires amr.max_level=0");
    IntVect hi;for(int d=0;d<AMREX_SPACEDIM;++d){if(ncell[d]<4)Abort("at least four cells per direction required");hi[d]=ncell[d]-1;}
    Geometry geom(Box(IntVect::TheZeroVector(),hi));BoxArray ba(geom.Domain());ba.maxSize(maxgrid);DistributionMapping dm(ba);
    MultiFab U(ba,dm,NSTATE,0),trial(ba,dm,NSTATE,0),buffer(ba,dm,NSTATE,0),q(ba,dm,NQ,0);
    int maxstep=100,plotint=20,checkint=0;Real stop=1,cfl=.3;pp.query("max_step",maxstep);pp.query("stop_time",stop);pp.query("cfl",cfl);pp.query("plot_int",plotint);pp.query("check_int",checkint);
    if(!(cfl>0 && cfl<=.4))Abort("tp.cfl must be in (0,0.4]");
    if(ParallelDescriptor::IOProcessor() && std::filesystem::exists("diagnostics.csv"))Abort("refusing to reuse an existing run directory");
    int step=0;Real time=0;std::string restart;pp.query("restart",restart);
    if(restart.empty())initialize(U,geom,s);
    else {
        std::ifstream header(restart+"/Header");std::string version,saved_signature;int nstate=0,dim=0;
        std::getline(header,version);header>>nstate>>dim>>step>>time;header.ignore(std::numeric_limits<std::streamsize>::max(),'\n');
        std::getline(header,saved_signature);
        if(!header || version!="ResolvedTwoPhase-v1" || nstate!=NSTATE || dim!=AMREX_SPACEDIM || saved_signature!=physics_signature(geom,s))
            Abort("checkpoint format/physics/geometry mismatch");
        MultiFab saved;VisMF::Read(saved,restart+"/State");
        if(saved.nComp()!=NSTATE)Abort("checkpoint component count mismatch");
        U.ParallelCopy(saved,0,0,NSTATE);
    }
    if(!recover(U,q,s.gas,s.liquid))Abort("inadmissible initial/restart state");
    diagnostics(U,geom,s,step,time,0,0);plot(U,geom,s,step,time);
    Print()<<"ResolvedTwoPhase: geometric PLIC; separate phase masses; mechanical equilibrium; MPI ranks="<<ParallelDescriptor::NProcs()<<"\n";
    while(step<maxstep && time<stop) {
        if(!recover(U,q,s.gas,s.liquid))Abort("inadmissible accepted state");
        Real dt=stop-time;
        // A global upper bound also covers non-monotone equilibrium sound speed
        // at mixed interfaces; phase acoustic CFL is intentionally conservative.
        const Real sound=std::max(q.max(10),std::max(q.max(14),q.max(15)));
        for(int d=0;d<AMREX_SPACEDIM;++d) {
            const Real speed=sound+std::max(std::abs(q.min(3+d)),std::abs(q.max(3+d)));
            if(speed>0)dt=std::min(dt,cfl*geom.CellSize(d)/speed);
        }
        bool accepted=false;int retries=0;
        for(;retries<16;++retries) {
            MultiFab::Copy(trial,U,0,0,NSTATE,0);accepted=true;
            for(int split=0;split<AMREX_SPACEDIM;++split) {
                const int dir=(split+step)%AMREX_SPACEDIM;
                if(!directional_step(trial,buffer,geom,s.gas,s.liquid,s.wall_lo,s.wall_hi,dir,dt)) {accepted=false;break;}
                MultiFab::Copy(trial,buffer,0,0,NSTATE,0);
            }
            if(accepted)break;dt*=.5;
        }
        if(!accepted || !(dt>1.e-20))Abort("two-phase step failed positivity/geometry; no state clipping performed");
        MultiFab::Copy(U,trial,0,0,NSTATE,0);time+=dt;++step;
        diagnostics(U,geom,s,step,time,dt,retries);
        if(step%10==0)Print()<<"step="<<step<<" time="<<std::setprecision(12)<<time<<" dt="<<dt<<" retries="<<retries<<'\n';
        if(plotint>0 && step%plotint==0)plot(U,geom,s,step,time);
        if(checkint>0 && step%checkint==0)checkpoint(U,geom,s,step,time);
    }
    if(plotint<=0 || step%plotint!=0)plot(U,geom,s,step,time);
    Print()<<"COMPLETE step="<<step<<" time="<<std::setprecision(17)<<time<<'\n';
}
}

int main(int argc,char** argv) {amrex::Initialize(argc,argv);{run();}amrex::Finalize();}
