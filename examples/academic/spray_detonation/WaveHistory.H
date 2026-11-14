#ifndef SPRAY_DETONATION_WAVE_HISTORY_H
#define SPRAY_DETONATION_WAVE_HISTORY_H

#include <AMReX_PlotFileUtil.H>
#include <AMReX_ParmParse.H>
#include <memory>
#include <filesystem>

// Optional Eulerian numerical soot foil. Maxima are accumulated at every
// completed step, so the pressure trace is not limited by plotfile cadence.
// Each process owns its local cells; output uses normal parallel AMReX I/O.
struct SprayWaveHistory {
  bool enabled = false;
  amrex::Real interval = 2.e-6, next_time = 0., stop_time = -1.;
  int output_index = 0;
  std::unique_ptr<amrex::MultiFab> maxima;

  void initialize(const amrex::MultiFab& state, amrex::Real time, int max_level) {
    amrex::ParmParse pp("prob");
    pp.query("record_wave_history", enabled);
    if (!enabled) return;
    pp.query("wave_history_interval", interval);
    amrex::ParmParse().query("stop_time", stop_time);
    if (max_level != 0 || interval <= 0.)
      amrex::Abort("wave history requires max_level=0 and a positive output interval");
    maxima = std::make_unique<amrex::MultiFab>(state.boxArray(), state.DistributionMap(), 2, 0);
    // Release arena-backed storage before AMReX destroys its arenas. The
    // recorder itself has static storage duration and outlives Finalize().
    amrex::ExecOnFinalize([this]() { maxima.reset(); enabled = false; });
    maxima->setVal(0.);
    next_time = time;
    amrex::Print() << "Wave history begins at time " << time
                   << "; pressure/heat maxima are sampled at every completed step.\n";
  }

  void sample(const amrex::MultiFab& state, const amrex::MultiFab& reactions,
              const amrex::Geometry& geom, amrex::Real time, int step) {
    if (!enabled) return;
    if (state.boxArray() != maxima->boxArray())
      amrex::Abort("wave history does not support a changing grid");
    for (amrex::MFIter mfi(state, amrex::TilingIfNotGPU()); mfi.isValid(); ++mfi) {
      const auto s=state.const_array(mfi), r=reactions.const_array(mfi);
      const auto h=maxima->array(mfi);
      amrex::ParallelFor(mfi.tilebox(), [=] AMREX_GPU_DEVICE(int i,int j,int k) noexcept {
        const auto rho=s(i,j,k,URHO), temp=s(i,j,k,UTEMP);
        amrex::Real y[NUM_SPECIES], pressure;
        for(int n=0;n<NUM_SPECIES;++n) y[n]=s(i,j,k,UFS+n)/rho;
        auto eos=pele::physics::PhysicsType::eos();
        eos.RTY2P(rho,temp,y,pressure);
        if(!std::isfinite(pressure) || pressure<=0. ||
           !std::isfinite(r(i,j,k,NUM_SPECIES+1)))
          amrex::Abort("nonfinite pressure or heat release in wave history");
        h(i,j,k,0)=amrex::max(h(i,j,k,0),pressure);
        h(i,j,k,1)=amrex::max(h(i,j,k,1),r(i,j,k,NUM_SPECIES+1));
      });
    }
    const bool final=stop_time>0. && time>=stop_time*(1.-1.e-12);
    if(time+interval*1.e-12>=next_time || final) {
      const auto name=amrex::Concatenate("sootfoil",output_index++,5);
      if(amrex::ParallelDescriptor::IOProcessor() && std::filesystem::exists(name))
        amrex::Abort("refusing to overwrite wave history output");
      amrex::WriteSingleLevelPlotfile(name,*maxima,
        {"maximum_pressure","maximum_heat_release"},geom,time,step);
      next_time=time+interval;
    }
  }
};

#endif
