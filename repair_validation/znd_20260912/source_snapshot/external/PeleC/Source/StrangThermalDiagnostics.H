#ifndef PELEC_STRANG_THERMAL_DIAGNOSTICS_H
#define PELEC_STRANG_THERMAL_DIAGNOSTICS_H

#include <AMReX_Reduce.H>
#include <AMReX_ParmParse.H>
#include <AMReX_Gpu.H>
#include <fstream>
#include <filesystem>
#include <iomanip>
#include <array>

// Read-only operator-stage diagnostics. Opt-in and uniform-grid only.
// All thermodynamic output uses the active EOS; it is not an independent
// reference or a repair of temperatures outside that EOS's fitted range.
class StrangThermalDiagnostics {
  bool initialized_ = false, enabled_ = false;
  int interval_ = 1;
  amrex::Real upper_ = 5000., band_ = .05;
  amrex::IntVect probe_ = amrex::IntVect::TheZeroVector();
  std::ofstream csv_;

  static std::array<amrex::Real,NVAR> cell(
      amrex::MultiFab const& state, amrex::IntVect const& index) {
    std::array<amrex::Real,NVAR> values{};
    for(amrex::MFIter mfi(state);mfi.isValid();++mfi) {
      if(!mfi.validbox().contains(index)) continue;
      auto const& fab=state[mfi];
      for(int n=0;n<NVAR;++n) {
        auto const* source=fab.dataPtr(n)+fab.box().index(index);
#ifdef AMREX_USE_GPU
        amrex::Gpu::dtoh_memcpy(&values[n],source,sizeof(amrex::Real));
#else
        values[n]=*source;
#endif
      }
    }
    amrex::ParallelDescriptor::ReduceRealSum(values.data(),NVAR);
    return values;
  }

public:
  void sample(amrex::MultiFab const& state,amrex::MultiFab const& original,
              amrex::Geometry const& geom,amrex::Real time,amrex::Real dt,
              int step,char const* stage) {
    if(!initialized_) {
      amrex::ParmParse pp("pelec");
      pp.query("thermal_diagnostics",enabled_);
      if(enabled_) {
        pp.query("thermal_diagnostic_interval_steps",interval_);
        pp.query("thermal_diagnostic_upper_K",upper_);
        pp.query("thermal_diagnostic_wall_band_cm",band_);
        amrex::Vector<int> probe;
        pp.getarr("thermal_diagnostic_probe",probe);
        if(probe.size()!=AMREX_SPACEDIM || interval_<1 || upper_<=0. || band_<=0.)
          amrex::Abort("invalid thermal diagnostic parameters");
        for(int d=0;d<AMREX_SPACEDIM;++d)probe_[d]=probe[d];
        if(!geom.Domain().contains(probe_))amrex::Abort("thermal probe outside domain");
        if(amrex::ParallelDescriptor::IOProcessor()) {
          if(std::filesystem::exists("thermal_stages.csv"))
            amrex::Abort("refusing to overwrite thermal_stages.csv");
          csv_.open("thermal_stages.csv");
          csv_<<std::setprecision(17);
          csv_<<"step,time_start_s,dt_s,stage,point,i,j,x_mm,y_mm,"
                "T_K,original_T_at_same_cell_K,lower_band_Tmax_K,upper_band_Tmax_K,"
                "interior_Tmax_K,cells_above_fit_upper,cells_nonfinite_T,"
                "rho_kg_m3,p_Pa,u_m_s,v_m_s,e_internal_J_kg,e_total_J_kg,"
                "stored_e_internal_J_kg,cv_J_kg_K,instantaneous_hrr_W_m3";
          amrex::Vector<std::string> names;CKSYMS_STR(names);
          for(auto const& name:names)csv_<<",Y_"<<name;
          csv_<<"\n";
        }
      }
      initialized_=true;
    }
    if(!enabled_ || step%interval_!=0)return;

    using Real=amrex::Real;using Long=amrex::Long;
    amrex::ReduceOps<amrex::ReduceOpMax,amrex::ReduceOpMax,amrex::ReduceOpMax,
                     amrex::ReduceOpSum,amrex::ReduceOpSum> ops;
    amrex::ReduceData<Real,Real,Real,Long,Long> data(ops);
    using Tuple=typename decltype(data)::Type;
    const auto lo=geom.ProbLoArray(),hi=geom.ProbHiArray(),dx=geom.CellSizeArray();
    const auto domain_lo=geom.Domain().smallEnd();
    const Real band=band_,upper=upper_;
    for(amrex::MFIter mfi(state,amrex::TilingIfNotGPU());mfi.isValid();++mfi) {
      auto const s=state.const_array(mfi);
      ops.eval(mfi.tilebox(),data,[=] AMREX_GPU_DEVICE(int i,int j,int k) noexcept -> Tuple {
        const Real T=s(i,j,k,UTEMP),y=lo[1]+(j-domain_lo[1]+.5)*dx[1];
        return {y<lo[1]+band?T:0.,y>hi[1]-band?T:0.,
          y>=lo[1]+band && y<=hi[1]-band?T:0.,Long(T>upper),Long(!std::isfinite(T))};
      });
    }
    auto stats=data.value();
    Real peaks[3]={amrex::get<0>(stats),amrex::get<1>(stats),amrex::get<2>(stats)};
    Long counts[2]={amrex::get<3>(stats),amrex::get<4>(stats)};
    amrex::ParallelDescriptor::ReduceRealMax(peaks,3);
    amrex::ParallelDescriptor::ReduceLongSum(counts,2);
    const auto peak=state.maxIndex(UTEMP,0);
    const amrex::IntVect points[2]={peak,probe_};
    for(int point=0;point<2;++point) {
      const auto s=cell(state,points[point]),old=cell(original,points[point]);
      if(!amrex::ParallelDescriptor::IOProcessor())continue;
      const Real rho=s[URHO],T=s[UTEMP];
      Real Y[NUM_SPECIES],w[NUM_SPECIES],h[NUM_SPECIES],p,cv;
      for(int n=0;n<NUM_SPECIES;++n)Y[n]=s[UFS+n]/rho;
      auto eos=pele::physics::PhysicsType::eos();
      eos.RTY2P(rho,T,Y,p);eos.TY2Cv(T,Y,cv);
      eos.RTY2WDOT(rho,T,Y,w);eos.T2Hi(T,h);
      Real heat=0.;for(int n=0;n<NUM_SPECIES;++n)heat-=w[n]*h[n];
      const Real kinetic=.5*(s[UMX]*s[UMX]+s[UMY]*s[UMY]+s[UMZ]*s[UMZ])/(rho*rho);
      const auto iv=points[point];
      csv_<<step<<','<<time<<','<<dt<<','<<stage<<','<<(point==0?"maximum":"fixed_probe")
          <<','<<iv[0]<<','<<iv[1]<<','<<(lo[0]+(iv[0]-domain_lo[0]+.5)*dx[0])*10.
          <<','<<(lo[1]+(iv[1]-domain_lo[1]+.5)*dx[1])*10.
          <<','<<T<<','<<old[UTEMP]<<','<<peaks[0]<<','<<peaks[1]<<','<<peaks[2]
          <<','<<counts[0]<<','<<counts[1]<<','<<rho*1000.<<','<<p*.1
          <<','<<s[UMX]/rho*.01<<','<<s[UMY]/rho*.01
          <<','<<(s[UEDEN]/rho-kinetic)*1.e-4<<','<<s[UEDEN]/rho*1.e-4
          <<','<<s[UEINT]/rho*1.e-4<<','<<cv*1.e-4<<','<<heat*.1;
      for(auto value:Y)csv_<<','<<value;
      csv_<<'\n';
    }
    if(amrex::ParallelDescriptor::IOProcessor())csv_.flush();
  }
};

#endif
