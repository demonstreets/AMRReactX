#ifndef PELELM_PROB_H
#define PELELM_PROB_H
#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>
#include <AMReX_Array.H>
#include <AMReX_Gpu.H>
#include <PeleLMeX_ProblemSpecificFunctions.H>
#include <PeleLMeX_Index.H>
#include <PelePhysics.H>
#include <leak_source.H>
#include <cmath>

struct MyProbParm : public ProbParmDefault {
  amrex::Real P_mean=101325.0, T_mean=300.0;
  amrex::Real wind_u=2.0, wind_v=0.0;
  amrex::Real leak_xc=2.66, leak_yc=1.25, leak_zc=1.25;
  amrex::Real leak_rate=0.104, leak_radius=0.03;
  static constexpr int max_leak_sources = 4;
  int leak_count=1;
  amrex::Real leak0_xc=2.66, leak0_yc=1.25, leak0_zc=1.25, leak0_radius=0.03, leak0_fraction=1.0;
  amrex::Real leak1_xc=2.66, leak1_yc=1.25, leak1_zc=1.25, leak1_radius=0.03, leak1_fraction=1.0;
  amrex::Real leak2_xc=2.66, leak2_yc=1.25, leak2_zc=1.25, leak2_radius=0.03, leak2_fraction=1.0;
  amrex::Real leak3_xc=2.66, leak3_yc=1.25, leak3_zc=1.25, leak3_radius=0.03, leak3_fraction=1.0;
  amrex::Real leak0_orifice_diameter=0.0, leak0_orifice_area=0.0;
  amrex::Real leak1_orifice_diameter=0.0, leak1_orifice_area=0.0;
  amrex::Real leak2_orifice_diameter=0.0, leak2_orifice_area=0.0;
  amrex::Real leak3_orifice_diameter=0.0, leak3_orifice_area=0.0;
  amrex::Real leak_vel_x=0.0, leak_vel_y=0.0, leak_vel_z=0.0;
  amrex::Real leak_T=300.0;
  int leak_model=0; // 0=fixed_mass_flow, 1=pressure_orifice, 2=tank_blowdown, 3=linepack_blowdown
  int leak_use_orifice_velocity=1;
  amrex::Real leak_tank_pressure=5.0e5, leak_ambient_pressure=101325.0;
  amrex::Real leak_orifice_diameter=0.01, leak_orifice_area=0.0;
  amrex::Real leak_discharge_coeff=0.80, leak_gamma=1.405;
  amrex::Real leak_line_diameter=0.0, leak_line_length=0.0;
  amrex::Real leak_line_friction_factor=0.0, leak_line_loss_coeff=0.0;
  amrex::Real leak_linepack_pressure=0.0, leak_linepack_volume=0.0;
  amrex::Real leak_valve_open_time=0.0, leak_valve_ramp_time=0.0;
  amrex::Real leak_valve_initial_fraction=1.0, leak_valve_final_fraction=1.0;
  static constexpr int max_leak_schedule_points = 64;
  int leak_schedule_count=0;
  amrex::Real leak_schedule_times[max_leak_schedule_points] = {0.0};
  amrex::Real leak_schedule_rates[max_leak_schedule_points] = {0.0};
  amrex::Real leak_schedule_temperatures[max_leak_schedule_points] = {0.0};
  amrex::Real leak_schedule_vel_x[max_leak_schedule_points] = {0.0};
  amrex::Real leak_schedule_vel_y[max_leak_schedule_points] = {0.0};
  amrex::Real leak_schedule_vel_z[max_leak_schedule_points] = {0.0};
  int leak_schedule_has_radius=0, leak_schedule_has_location=0;
  amrex::Real leak_schedule_radius[max_leak_schedule_points] = {0.0};
  amrex::Real leak_schedule_x[max_leak_schedule_points] = {0.0};
  amrex::Real leak_schedule_y[max_leak_schedule_points] = {0.0};
  amrex::Real leak_schedule_z[max_leak_schedule_points] = {0.0};
  amrex::Real leak_gas_constant=4124.0;
  amrex::Real leak_compressibility_factor=1.0;
  amrex::Real leak_tank_volume=0.10;
  int leak_blowdown_substeps=64;
  int fuel_species_index=0;
  static constexpr int fuel_species_name_len = 32;
  char fuel_species_name[fuel_species_name_len] = "H2";
  amrex::Real obstacle_radius=0.125, obstacle_height=1.0;
  amrex::Real obstacle_xc=2.5, obstacle_yc=1.25, obstacle_zc=1.25;
  int obstacle_count=1, obstacle_direction=2, obstacle_has_fluid_inside=0;
  int initial_flammable_cloud=0;
  amrex::Real cloud_xc=1.25, cloud_yc=0.50, cloud_zc=0.50;
  amrex::Real cloud_rx=0.36, cloud_ry=0.22, cloud_rz=0.22;
  amrex::Real cloud_T=300.0, cloud_YFuel=0.0283, cloud_YO2=0.2264, cloud_YN2=0.7453;
  int ignition_hotspot=0;
  amrex::Real ignition_xc=1.25, ignition_yc=0.50, ignition_zc=0.50;
  amrex::Real ignition_radius=0.08, ignition_T=2000.0;
  int ignition_source=0;
  amrex::Real ignition_start_time=0.0, ignition_duration=0.0;
  amrex::Real ignition_power=0.0;
};

struct MyProblemSpecificFunctions : public DefaultProblemSpecificFunctions {
  static void EBUserDefined(const amrex::Geometry&,const int,const int);
  AMREX_GPU_DEVICE AMREX_FORCE_INLINE
  static void initdata(int i,int j,int k,int is_incompressible,
    amrex::Array4<amrex::Real> const& state,amrex::Array4<amrex::Real> const&,
    amrex::GeometryData const& geomdata,MyProbParm const& pp,
    pele::physics::PMF::PmfData::DataContainer const*){
    auto eos=pele::physics::PhysicsType::eos();
    amrex::Real mf[NUM_SPECIES]={0.0}; mf[O2_ID]=0.233; mf[N2_ID]=0.767;
    state(i,j,k,TEMP)=pp.T_mean;
    const amrex::Real* prob_lo = geomdata.ProbLo();
    const amrex::Real* dx = geomdata.CellSize();
    const amrex::Real x = prob_lo[0] + (i + 0.5) * dx[0];
    const amrex::Real y = prob_lo[1] + (j + 0.5) * dx[1];
    const amrex::Real z = prob_lo[2] + (k + 0.5) * dx[2];
    if (pp.initial_flammable_cloud != 0) {
      const amrex::Real rx = pp.cloud_rx > 0.0 ? pp.cloud_rx : dx[0];
      const amrex::Real ry = pp.cloud_ry > 0.0 ? pp.cloud_ry : dx[1];
      const amrex::Real rz = pp.cloud_rz > 0.0 ? pp.cloud_rz : dx[2];
      const amrex::Real ell =
        ((x - pp.cloud_xc) * (x - pp.cloud_xc)) / (rx * rx) +
        ((y - pp.cloud_yc) * (y - pp.cloud_yc)) / (ry * ry) +
        ((z - pp.cloud_zc) * (z - pp.cloud_zc)) / (rz * rz);
      if (ell <= 1.0) {
        for(int n=0;n<NUM_SPECIES;n++) mf[n]=0.0;
        mf[pp.fuel_species_index]=pp.cloud_YFuel; mf[O2_ID]=pp.cloud_YO2; mf[N2_ID]=pp.cloud_YN2;
        const amrex::Real ysum = mf[pp.fuel_species_index] + mf[O2_ID] + mf[N2_ID];
        if (ysum > 0.0) {
          mf[pp.fuel_species_index] /= ysum; mf[O2_ID] /= ysum; mf[N2_ID] /= ysum;
        }
        state(i,j,k,TEMP)=pp.cloud_T;
      }
    }
    if (pp.ignition_hotspot != 0) {
      const amrex::Real dr2 =
        (x - pp.ignition_xc) * (x - pp.ignition_xc) +
        (y - pp.ignition_yc) * (y - pp.ignition_yc) +
        (z - pp.ignition_zc) * (z - pp.ignition_zc);
      if (dr2 <= pp.ignition_radius * pp.ignition_radius) {
        state(i,j,k,TEMP)=pp.ignition_T;
      }
    }
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

  static void modify_ext_sources(amrex::Real time,amrex::Real dt,
    const amrex::MultiFab&,const amrex::MultiFab&,
    std::unique_ptr<amrex::MultiFab>& ext_src,
    const amrex::GeometryData& geomdata,const MyProbParm* pp)
  {
    auto eos=pele::physics::PhysicsType::eos();
    namespace Leak = MyPele::Engineering::LeakSource;
    if (pp == nullptr) {
      amrex::Abort("h2_leak_3d modify_ext_sources received a null ProbParm pointer");
    }
#ifdef AMREX_USE_GPU
    MyProbParm pp_host;
    amrex::Gpu::copy(amrex::Gpu::deviceToHost, pp, pp + 1, &pp_host);
    amrex::Gpu::streamSynchronize();
    pp = &pp_host;
#endif
    const int leak_count = pp->leak_count;
    if (leak_count < 1 || leak_count > MyProbParm::max_leak_sources) {
      amrex::Abort("prob.leak_count must be between 1 and 4 for h2_leak_3d");
    }
    amrex::Real leak_x[MyProbParm::max_leak_sources] = {
      pp->leak0_xc, pp->leak1_xc, pp->leak2_xc, pp->leak3_xc};
    amrex::Real leak_y[MyProbParm::max_leak_sources] = {
      pp->leak0_yc, pp->leak1_yc, pp->leak2_yc, pp->leak3_yc};
    amrex::Real leak_z[MyProbParm::max_leak_sources] = {
      pp->leak0_zc, pp->leak1_zc, pp->leak2_zc, pp->leak3_zc};
    amrex::Real leak_radius[MyProbParm::max_leak_sources] = {
      pp->leak0_radius, pp->leak1_radius, pp->leak2_radius, pp->leak3_radius};
    const amrex::Real leak_fraction[MyProbParm::max_leak_sources] = {
      pp->leak0_fraction, pp->leak1_fraction, pp->leak2_fraction,
      pp->leak3_fraction};
    const amrex::Real leak_orifice_diameter[MyProbParm::max_leak_sources] = {
      pp->leak0_orifice_diameter, pp->leak1_orifice_diameter,
      pp->leak2_orifice_diameter, pp->leak3_orifice_diameter};
    const amrex::Real leak_orifice_area[MyProbParm::max_leak_sources] = {
      pp->leak0_orifice_area, pp->leak1_orifice_area,
      pp->leak2_orifice_area, pp->leak3_orifice_area};
    amrex::Real fraction_sum = 0.0;
    for (int n = 0; n < leak_count; ++n) {
      if (leak_radius[n] <= 0.0) {
        amrex::Abort("configured fuel leak source has nonpositive radius");
      }
      if (leak_fraction[n] < 0.0) {
        amrex::Abort("configured fuel leak source has negative mass-flow fraction");
      }
      fraction_sum += leak_fraction[n];
    }
    if (fraction_sum <= 0.0) {
      amrex::Abort("sum of configured fuel leak source fractions must be positive");
    }
    amrex::Real mf[NUM_SPECIES]={0.0}; mf[pp->fuel_species_index]=1.0;
    amrex::Real P=pp->P_mean*10.0, h_cgs=0.0;
    amrex::Real source_mdot[MyProbParm::max_leak_sources] = {0.0, 0.0, 0.0, 0.0};
    amrex::Real source_pressure_mdot[MyProbParm::max_leak_sources] = {0.0, 0.0, 0.0, 0.0};
    amrex::Real source_orifice_area[MyProbParm::max_leak_sources] = {0.0, 0.0, 0.0, 0.0};
    amrex::Real effective_mdot=pp->leak_rate;
    amrex::Real orifice_exit_velocity=0.0;
    bool pressure_driven_multihole = false;
    const char* leak_model_name = "fixed_mass_flow";
    Leak::ValveSchedule valve_schedule;
    valve_schedule.open_time = pp->leak_valve_open_time;
    valve_schedule.ramp_time = pp->leak_valve_ramp_time;
    valve_schedule.initial_fraction = pp->leak_valve_initial_fraction;
    valve_schedule.final_fraction = pp->leak_valve_final_fraction;
    if (!Leak::valid_valve_schedule(valve_schedule)) {
      amrex::Abort("prob.leak valve schedule requires nonnegative open/ramp times and fractions in [0,1]");
    }
    const bool scheduled_valve = !Leak::valve_schedule_is_always_open(valve_schedule);
    const amrex::Real valve_fraction_start =
      Leak::valve_schedule_fraction(valve_schedule, time);
    const amrex::Real valve_fraction_mid =
      Leak::valve_schedule_fraction(valve_schedule, time + 0.5 * dt);
    const amrex::Real valve_fraction_end =
      Leak::valve_schedule_fraction(valve_schedule, time + dt);
    const amrex::Real sample_time = time + 0.5 * dt;
    amrex::Real scheduled_reference_mdot = pp->leak_rate;
    amrex::Real scheduled_leak_T = pp->leak_T;
    amrex::Real scheduled_leak_vel_x = pp->leak_vel_x;
    amrex::Real scheduled_leak_vel_y = pp->leak_vel_y;
    amrex::Real scheduled_leak_vel_z = pp->leak_vel_z;
    amrex::Real scheduled_leak_radius = leak_radius[0];
    amrex::Real scheduled_leak_x = leak_x[0];
    amrex::Real scheduled_leak_y = leak_y[0];
    amrex::Real scheduled_leak_z = leak_z[0];
    if (pp->leak_schedule_count > 0) {
      if (sample_time <= pp->leak_schedule_times[0]) {
        scheduled_reference_mdot = pp->leak_schedule_rates[0];
        scheduled_leak_T = pp->leak_schedule_temperatures[0];
        scheduled_leak_vel_x = pp->leak_schedule_vel_x[0];
        scheduled_leak_vel_y = pp->leak_schedule_vel_y[0];
        scheduled_leak_vel_z = pp->leak_schedule_vel_z[0];
        scheduled_leak_radius = pp->leak_schedule_radius[0];
        scheduled_leak_x = pp->leak_schedule_x[0];
        scheduled_leak_y = pp->leak_schedule_y[0];
        scheduled_leak_z = pp->leak_schedule_z[0];
      } else if (
        sample_time >= pp->leak_schedule_times[pp->leak_schedule_count - 1]) {
        scheduled_reference_mdot =
          pp->leak_schedule_rates[pp->leak_schedule_count - 1];
        scheduled_leak_T =
          pp->leak_schedule_temperatures[pp->leak_schedule_count - 1];
        scheduled_leak_vel_x =
          pp->leak_schedule_vel_x[pp->leak_schedule_count - 1];
        scheduled_leak_vel_y =
          pp->leak_schedule_vel_y[pp->leak_schedule_count - 1];
        scheduled_leak_vel_z =
          pp->leak_schedule_vel_z[pp->leak_schedule_count - 1];
        scheduled_leak_radius =
          pp->leak_schedule_radius[pp->leak_schedule_count - 1];
        scheduled_leak_x =
          pp->leak_schedule_x[pp->leak_schedule_count - 1];
        scheduled_leak_y =
          pp->leak_schedule_y[pp->leak_schedule_count - 1];
        scheduled_leak_z =
          pp->leak_schedule_z[pp->leak_schedule_count - 1];
      } else {
        for (int n = 0; n < pp->leak_schedule_count - 1; ++n) {
          const amrex::Real t0 = pp->leak_schedule_times[n];
          const amrex::Real t1 = pp->leak_schedule_times[n + 1];
          if (sample_time >= t0 && sample_time <= t1) {
            const amrex::Real f = (sample_time - t0) / (t1 - t0);
            scheduled_reference_mdot =
              pp->leak_schedule_rates[n] +
              f * (pp->leak_schedule_rates[n + 1] - pp->leak_schedule_rates[n]);
            scheduled_leak_T =
              pp->leak_schedule_temperatures[n] +
              f * (pp->leak_schedule_temperatures[n + 1] -
                   pp->leak_schedule_temperatures[n]);
            scheduled_leak_vel_x =
              pp->leak_schedule_vel_x[n] +
              f * (pp->leak_schedule_vel_x[n + 1] -
                   pp->leak_schedule_vel_x[n]);
            scheduled_leak_vel_y =
              pp->leak_schedule_vel_y[n] +
              f * (pp->leak_schedule_vel_y[n + 1] -
                   pp->leak_schedule_vel_y[n]);
            scheduled_leak_vel_z =
              pp->leak_schedule_vel_z[n] +
              f * (pp->leak_schedule_vel_z[n + 1] -
                   pp->leak_schedule_vel_z[n]);
            scheduled_leak_radius =
              pp->leak_schedule_radius[n] +
              f * (pp->leak_schedule_radius[n + 1] -
                   pp->leak_schedule_radius[n]);
            scheduled_leak_x =
              pp->leak_schedule_x[n] +
              f * (pp->leak_schedule_x[n + 1] -
                   pp->leak_schedule_x[n]);
            scheduled_leak_y =
              pp->leak_schedule_y[n] +
              f * (pp->leak_schedule_y[n + 1] -
                   pp->leak_schedule_y[n]);
            scheduled_leak_z =
              pp->leak_schedule_z[n] +
              f * (pp->leak_schedule_z[n + 1] -
                   pp->leak_schedule_z[n]);
            break;
          }
        }
      }
    }
    if (pp->leak_schedule_has_radius != 0) {
      leak_radius[0] = scheduled_leak_radius;
    }
    if (pp->leak_schedule_has_location != 0) {
      leak_x[0] = scheduled_leak_x;
      leak_y[0] = scheduled_leak_y;
      leak_z[0] = scheduled_leak_z;
    }
    eos.TY2H(scheduled_leak_T,mf,h_cgs);
    amrex::Real vx=scheduled_leak_vel_x, vy=scheduled_leak_vel_y, vz=scheduled_leak_vel_z;
    amrex::Real source_vx[MyProbParm::max_leak_sources] = {vx, vx, vx, vx};
    amrex::Real source_vy[MyProbParm::max_leak_sources] = {vy, vy, vy, vy};
    amrex::Real source_vz[MyProbParm::max_leak_sources] = {vz, vz, vz, vz};
    if (pp->leak_model == 0) {
      effective_mdot = scheduled_reference_mdot * valve_fraction_mid;
      if (pp->leak_schedule_count > 0) {
        leak_model_name = scheduled_valve
          ? "fixed_mass_flow_timeseries_scheduled"
          : "fixed_mass_flow_timeseries";
      } else {
        leak_model_name = scheduled_valve ? "fixed_mass_flow_scheduled" : "fixed_mass_flow";
      }
      amrex::Print() << pp->fuel_species_name << " leak fixed-mass-flow schedule: time=" << time
                     << ", dt=" << dt
                     << ", reference_leak_rate=" << pp->leak_rate
                     << ", schedule_count=" << pp->leak_schedule_count
                     << ", scheduled_reference_mdot=" << scheduled_reference_mdot
                     << ", scheduled_leak_T=" << scheduled_leak_T
                     << ", scheduled_velocity=(" << scheduled_leak_vel_x
                     << "," << scheduled_leak_vel_y
                     << "," << scheduled_leak_vel_z << ")"
                     << ", scheduled_radius=" << scheduled_leak_radius
                     << ", scheduled_center=(" << scheduled_leak_x
                     << "," << scheduled_leak_y
                     << "," << scheduled_leak_z << ")"
                     << ", valve_scheduled=" << scheduled_valve
                     << ", valve_open_time=" << pp->leak_valve_open_time
                     << ", valve_ramp_time=" << pp->leak_valve_ramp_time
                     << ", valve_fraction_start=" << valve_fraction_start
                     << ", valve_fraction_mid=" << valve_fraction_mid
                     << ", valve_fraction_end=" << valve_fraction_end
                     << ", effective_mdot=" << effective_mdot << "\n";
    }
    if (pp->leak_model == 1 || pp->leak_model == 2 || pp->leak_model == 3) {
      Leak::PressureOrificeLeakModel model;
      const amrex::Real initial_supply_pressure =
        (pp->leak_model == 3 && pp->leak_linepack_pressure > 0.0)
          ? pp->leak_linepack_pressure
          : pp->leak_tank_pressure;
      model.upstream_pressure = initial_supply_pressure;
      model.downstream_pressure = pp->leak_ambient_pressure;
      model.temperature = pp->leak_T;
      model.diameter = pp->leak_orifice_diameter;
      model.area = pp->leak_orifice_area;
      model.discharge_coefficient = pp->leak_discharge_coeff;
      model.line_diameter = pp->leak_line_diameter;
      model.line_length = pp->leak_line_length;
      model.line_friction_factor = pp->leak_line_friction_factor;
      model.line_loss_coefficient = pp->leak_line_loss_coeff;
      model.gamma = pp->leak_gamma;
      model.gas_constant = pp->leak_gas_constant;
      model.compressibility_factor = pp->leak_compressibility_factor;
      amrex::Real pressure_for_velocity = initial_supply_pressure;
      amrex::Real tank_supply_pressure = initial_supply_pressure;
      amrex::Real combined_orifice_area = 0.0;
      for (int n = 0; n < leak_count; ++n) {
        Leak::PressureOrificeLeakModel source_model = model;
        if (leak_orifice_area[n] > 0.0) {
          source_model.area = leak_orifice_area[n];
          source_model.diameter = leak_orifice_diameter[n];
          pressure_driven_multihole = pressure_driven_multihole || leak_count > 1;
        } else if (leak_orifice_diameter[n] > 0.0) {
          source_model.area = 0.0;
          source_model.diameter = leak_orifice_diameter[n];
          pressure_driven_multihole = pressure_driven_multihole || leak_count > 1;
        }
        source_orifice_area[n] = Leak::positive_orifice_area(source_model);
        combined_orifice_area += source_orifice_area[n];
      }
      if (pressure_driven_multihole && combined_orifice_area <= 0.0) {
        amrex::Abort("pressure-driven multi-hole leak has no positive orifice area");
      }
      if (pressure_driven_multihole) {
        if (scheduled_valve) {
          amrex::Abort("valve schedule is currently supported only for single-hole pressure/tank/linepack leaks");
        }
        model.area = combined_orifice_area;
        model.diameter = 0.0;
      }
      if (pp->leak_model == 2 || pp->leak_model == 3) {
        const bool linepack_blowdown = pp->leak_model == 3;
        const amrex::Real blowdown_volume = linepack_blowdown
          ? Leak::linepack_volume(model, pp->leak_linepack_volume)
          : pp->leak_tank_volume;
        if (blowdown_volume <= 0.0) {
          amrex::Abort(
            linepack_blowdown
              ? "prob.leak_linepack_volume must be positive or prob.leak_line_diameter/length must define a positive linepack volume"
              : "prob.leak_tank_volume must be positive for tank_blowdown");
        }
        const auto blowdown = Leak::tank_blowdown_interval_scheduled(
          model, blowdown_volume, time, dt, pp->leak_blowdown_substeps,
          valve_schedule);
        effective_mdot = blowdown.average_mass_flow_rate;
        tank_supply_pressure = blowdown.pressure_start;
        model.upstream_pressure = blowdown.pressure_start;
        {
          const auto pressure_model = Leak::valve_scaled_orifice_model(
            model, valve_fraction_mid);
          pressure_for_velocity =
            Leak::pressure_orifice_effective_upstream_pressure(pressure_model);
        }
        leak_model_name = linepack_blowdown ? "linepack_blowdown" : "tank_blowdown";
        if (linepack_blowdown) {
          amrex::Print() << pp->fuel_species_name << " leak linepack-blowdown model: time=" << time
                         << ", dt=" << dt
                         << ", linepack_volume=" << blowdown_volume
                         << ", configured_linepack_volume=" << pp->leak_linepack_volume
                         << ", linepack_pressure=" << initial_supply_pressure
                         << ", line_diameter=" << pp->leak_line_diameter
                         << ", line_length=" << pp->leak_line_length
                         << ", compressibility_factor=" << pp->leak_compressibility_factor
                         << ", initial_pressure=" << initial_supply_pressure
                         << ", pressure_start=" << blowdown.pressure_start
                         << ", pressure_end=" << blowdown.pressure_end
                         << ", injected_interval=" << blowdown.injected_mass
                         << ", cumulative_injected=" << blowdown.cumulative_injected_mass
                         << ", substeps=" << pp->leak_blowdown_substeps
                         << ", valve_open_time=" << pp->leak_valve_open_time
                         << ", valve_ramp_time=" << pp->leak_valve_ramp_time
                         << ", valve_fraction_start=" << valve_fraction_start
                         << ", valve_fraction_mid=" << valve_fraction_mid
                         << ", valve_fraction_end=" << valve_fraction_end << "\n";
        } else {
          amrex::Print() << pp->fuel_species_name << " leak tank-blowdown model: time=" << time
                         << ", dt=" << dt
                         << ", tank_volume=" << pp->leak_tank_volume
                         << ", compressibility_factor=" << pp->leak_compressibility_factor
                         << ", initial_pressure=" << pp->leak_tank_pressure
                         << ", pressure_start=" << blowdown.pressure_start
                         << ", pressure_end=" << blowdown.pressure_end
                         << ", injected_interval=" << blowdown.injected_mass
                         << ", cumulative_injected=" << blowdown.cumulative_injected_mass
                         << ", substeps=" << pp->leak_blowdown_substeps
                         << ", valve_open_time=" << pp->leak_valve_open_time
                         << ", valve_ramp_time=" << pp->leak_valve_ramp_time
                         << ", valve_fraction_start=" << valve_fraction_start
                         << ", valve_fraction_mid=" << valve_fraction_mid
                         << ", valve_fraction_end=" << valve_fraction_end << "\n";
        }
      } else {
        if (pressure_driven_multihole) {
          effective_mdot = 0.0;
        } else {
          const auto flow_model = Leak::valve_scaled_orifice_model(
            model, valve_fraction_mid);
          effective_mdot = Leak::pressure_orifice_mass_flow_rate(flow_model);
          pressure_for_velocity =
            Leak::pressure_orifice_effective_upstream_pressure(flow_model);
        }
        leak_model_name = "pressure_orifice";
      }
      if (pressure_driven_multihole) {
        amrex::Real pressure_mdot_sum = 0.0;
        for (int n = 0; n < leak_count; ++n) {
          Leak::PressureOrificeLeakModel source_model = model;
          source_model.area = source_orifice_area[n];
          source_model.diameter = 0.0;
          source_model.upstream_pressure = tank_supply_pressure;
          source_pressure_mdot[n] = Leak::pressure_orifice_mass_flow_rate(source_model);
          pressure_mdot_sum += source_pressure_mdot[n];
        }
        if (pressure_mdot_sum <= 0.0) {
          amrex::Abort("pressure-driven multi-hole leak produced nonpositive total mdot");
        }
        if (pp->leak_model == 1) {
          effective_mdot = pressure_mdot_sum;
        }
        for (int n = 0; n < leak_count; ++n) {
          Leak::PressureOrificeLeakModel source_model = model;
          source_model.area = source_orifice_area[n];
          source_model.diameter = 0.0;
          source_model.upstream_pressure = tank_supply_pressure;
          source_mdot[n] = effective_mdot * source_pressure_mdot[n] / pressure_mdot_sum;
          const amrex::Real source_exit_velocity =
            Leak::pressure_orifice_exit_velocity(source_model);
          if (n == 0) {
            orifice_exit_velocity = source_exit_velocity;
          }
          if (source_mdot[n] <= 0.0 || source_exit_velocity <= 0.0) {
            amrex::Abort("pressure-driven multi-hole source produced nonpositive mdot or exit velocity");
          }
          if (pp->leak_use_orifice_velocity != 0) {
            const amrex::Real vmag = std::sqrt(vx*vx + vy*vy + vz*vz);
            if (vmag <= 0.0) {
              source_vx[n] = source_exit_velocity;
              source_vy[n] = 0.0;
              source_vz[n] = 0.0;
            } else {
              const amrex::Real scale = source_exit_velocity / vmag;
              source_vx[n] = vx * scale;
              source_vy[n] = vy * scale;
              source_vz[n] = vz * scale;
            }
          }
          amrex::Print() << pp->fuel_species_name << " leak pressure-driven source[" << n << "]: orifice_area="
                         << source_orifice_area[n]
                         << ", pressure_mdot=" << source_pressure_mdot[n]
                         << ", assigned_mdot=" << source_mdot[n]
                         << ", mdot_fraction=" << source_mdot[n] / effective_mdot
                         << "\n";
        }
      } else {
        model.upstream_pressure = tank_supply_pressure;
        orifice_exit_velocity = Leak::pressure_orifice_exit_velocity(model);
        if ((effective_mdot <= 0.0 && valve_fraction_mid > 0.0) ||
            orifice_exit_velocity <= 0.0) {
          amrex::Abort("orifice leak model produced nonpositive mdot or exit velocity");
        }
        if (pp->leak_use_orifice_velocity != 0) {
          const amrex::Real vmag = std::sqrt(vx*vx + vy*vy + vz*vz);
          if (vmag <= 0.0) {
            vx = orifice_exit_velocity;
            vy = 0.0;
            vz = 0.0;
          } else {
            const amrex::Real scale = orifice_exit_velocity / vmag;
            vx *= scale;
            vy *= scale;
            vz *= scale;
          }
        }
      }
      amrex::Print() << pp->fuel_species_name << " leak pressure-orifice model: tank_pressure=" << pressure_for_velocity
                     << ", supply_pressure=" << tank_supply_pressure
                     << ", ambient_pressure=" << pp->leak_ambient_pressure
                     << ", temperature=" << pp->leak_T
                     << ", diameter=" << pp->leak_orifice_diameter
                     << ", area=" << Leak::positive_orifice_area(model)
                     << ", discharge_coeff=" << pp->leak_discharge_coeff
                     << ", line_diameter=" << pp->leak_line_diameter
                     << ", line_length=" << pp->leak_line_length
                     << ", line_friction_factor=" << pp->leak_line_friction_factor
                     << ", line_loss_coeff=" << pp->leak_line_loss_coeff
                     << ", linepack_pressure=" << initial_supply_pressure
                     << ", linepack_volume=" << Leak::linepack_volume(model, pp->leak_linepack_volume)
                     << ", line_loss_total=" << Leak::pipe_loss_coefficient(model)
                     << ", valve_scheduled=" << scheduled_valve
                     << ", valve_open_time=" << pp->leak_valve_open_time
                     << ", valve_ramp_time=" << pp->leak_valve_ramp_time
                     << ", valve_fraction_start=" << valve_fraction_start
                     << ", valve_fraction_mid=" << valve_fraction_mid
                     << ", valve_fraction_end=" << valve_fraction_end
                     << ", gamma=" << pp->leak_gamma
                     << ", gas_constant=" << pp->leak_gas_constant
                     << ", compressibility_factor=" << pp->leak_compressibility_factor
                     << ", choked=" << Leak::pressure_orifice_is_choked(model)
                     << ", exit_velocity=" << orifice_exit_velocity << "\n";
    } else if (pp->leak_model != 0) {
      amrex::Abort("prob.leak_model must be fixed_mass_flow, pressure_orifice, tank_blowdown, or linepack_blowdown");
    }
    amrex::Real ke=0.5*(vx*vx+vy*vy+vz*vz);
    amrex::Real h_inj=h_cgs*1e-4;
    amrex::Print() << "Applying " << pp->fuel_species_name << " leak source: model=" << leak_model_name
                   << ", mdot=" << effective_mdot
                   << ", reference_leak_rate=" << pp->leak_rate
                   << ", radius=" << pp->leak_radius
                   << ", leak_T=" << scheduled_leak_T
                   << ", leak_count=" << leak_count
                   << ", pressure_driven_multihole=" << pressure_driven_multihole
                   << ", velocity=(" << vx << "," << vy << "," << vz << ")"
                   << ", fuel_species_index=" << pp->fuel_species_index << "\n";
    amrex::Print() << pp->fuel_species_name << " leak effective mass flow rate=" << effective_mdot << "\n";
    amrex::Print() << pp->fuel_species_name << " leak source interval: time=" << time
                   << ", dt=" << dt
                   << ", model=" << leak_model_name
                   << ", mdot=" << effective_mdot
                   << ", leak_T=" << scheduled_leak_T
                   << ", injected_interval=" << effective_mdot * dt
                   << ", valve_fraction_mid=" << valve_fraction_mid << "\n";
    const amrex::GpuArray<amrex::Real, 3> plo = {
      geomdata.ProbLo(0), geomdata.ProbLo(1), geomdata.ProbLo(2)};
    const amrex::GpuArray<amrex::Real, 3> dx = {
      geomdata.CellSize(0), geomdata.CellSize(1), geomdata.CellSize(2)};
    double leak_prob_lo[3] = {plo[0], plo[1], plo[2]};
    double leak_dx[3] = {dx[0], dx[1], dx[2]};
    int leak_lo[3] = {geomdata.Domain().smallEnd(0), geomdata.Domain().smallEnd(1),
                      geomdata.Domain().smallEnd(2)};
    int leak_hi[3] = {geomdata.Domain().bigEnd(0), geomdata.Domain().bigEnd(1),
                      geomdata.Domain().bigEnd(2)};

    amrex::GpuArray<Leak::SphericalLeakSource, MyProbParm::max_leak_sources>
      leak_sources;
    amrex::Real total_active_volume = 0.0;
    for (int n = 0; n < leak_count; ++n) {
      auto& source = leak_sources[n];
      source.center[0] = leak_x[n];
      source.center[1] = leak_y[n];
      source.center[2] = leak_z[n];
      source.radius = leak_radius[n];
      source.mass_flow_rate = pressure_driven_multihole
        ? source_mdot[n]
        : effective_mdot * leak_fraction[n] / fraction_sum;
      source.velocity[0] = pressure_driven_multihole ? source_vx[n] : vx;
      source.velocity[1] = pressure_driven_multihole ? source_vy[n] : vy;
      source.velocity[2] = pressure_driven_multihole ? source_vz[n] : vz;
      const amrex::Real source_ke = 0.5 * (
        source.velocity[0] * source.velocity[0] +
        source.velocity[1] * source.velocity[1] +
        source.velocity[2] * source.velocity[2]);
      source.specific_enthalpy = h_inj + source_ke;
      source.species_index = pp->fuel_species_index;
      const amrex::Real active_volume =
        Leak::cell_centered_active_volume(source, leak_prob_lo, leak_dx, leak_lo,
                                          leak_hi);
      if (active_volume <= 0.0) {
        amrex::Abort("configured fuel leak source has no active cells on this grid");
      }
      source.normalization_volume = active_volume;
      total_active_volume += active_volume;
      amrex::Print() << pp->fuel_species_name << " leak source[" << n << "]: center=("
                     << source.center[0] << "," << source.center[1] << ","
                     << source.center[2] << ")"
                     << ", radius=" << source.radius
                     << ", fraction=" << leak_fraction[n] / fraction_sum
                     << ", pressure_fraction="
                     << (effective_mdot > 0.0 ? source.mass_flow_rate / effective_mdot : 0.0)
                     << ", mdot=" << source.mass_flow_rate
                     << ", active_volume=" << active_volume
                     << ", mdot_vol=" << Leak::volumetric_mass_source(source)
                     << "\n";
    }
    amrex::Print() << pp->fuel_species_name << " leak discrete active volume=" << total_active_volume
                   << ", leak_count=" << leak_count
                   << ", fraction_sum=" << fraction_sum << "\n";
    const bool timed_ignition_configured = pp->ignition_source != 0;
    if (timed_ignition_configured) {
      if (pp->ignition_radius <= 0.0) {
        amrex::Abort("prob.ignition_radius must be positive when prob.ignition_source is enabled");
      }
      if (pp->ignition_duration <= 0.0) {
        amrex::Abort("prob.ignition_duration must be positive when prob.ignition_source is enabled");
      }
      if (pp->ignition_power <= 0.0) {
        amrex::Abort("prob.ignition_power must be positive when prob.ignition_source is enabled");
      }
    }
    amrex::Real ignition_active_volume = 0.0;
    amrex::Real ignition_time_fraction = 0.0;
    amrex::Real ignition_qdot = 0.0;
    if (timed_ignition_configured) {
      Leak::SphericalLeakSource ignition_region;
      ignition_region.center[0] = pp->ignition_xc;
      ignition_region.center[1] = pp->ignition_yc;
      ignition_region.center[2] = pp->ignition_zc;
      ignition_region.radius = pp->ignition_radius;
      ignition_region.mass_flow_rate = 1.0;
      ignition_region.velocity[0] = 0.0;
      ignition_region.velocity[1] = 0.0;
      ignition_region.velocity[2] = 0.0;
      ignition_region.specific_enthalpy = 0.0;
      ignition_region.species_index = pp->fuel_species_index;
      ignition_active_volume =
        Leak::cell_centered_active_volume(ignition_region, leak_prob_lo, leak_dx,
                                          leak_lo, leak_hi);
      if (ignition_active_volume <= 0.0) {
        amrex::Abort("configured fuel ignition source has no active cells on this grid");
      }
      const amrex::Real ignition_end_time =
        pp->ignition_start_time + pp->ignition_duration;
      const amrex::Real active_start =
        time > pp->ignition_start_time ? time : pp->ignition_start_time;
      const amrex::Real active_end =
        (time + dt) < ignition_end_time ? (time + dt) : ignition_end_time;
      if (active_end > active_start && dt > 0.0) {
        ignition_time_fraction = (active_end - active_start) / dt;
        ignition_qdot = pp->ignition_power * ignition_time_fraction /
                        ignition_active_volume;
      }
      amrex::Print() << pp->fuel_species_name << " delayed ignition source: enabled=1"
                     << ", time=" << time
                     << ", dt=" << dt
                     << ", start_time=" << pp->ignition_start_time
                     << ", duration=" << pp->ignition_duration
                     << ", power=" << pp->ignition_power
                     << ", active_volume=" << ignition_active_volume
                     << ", time_fraction=" << ignition_time_fraction
                     << ", qdot=" << ignition_qdot << "\n";
    }
    const amrex::Real ignition_xc = pp->ignition_xc;
    const amrex::Real ignition_yc = pp->ignition_yc;
    const amrex::Real ignition_zc = pp->ignition_zc;
    const amrex::Real ignition_radius = pp->ignition_radius;
    const amrex::Real ignition_radius2 = ignition_radius * ignition_radius;
    auto const& src_arrs=ext_src->arrays();
    amrex::ParallelFor(*ext_src,[=]AMREX_GPU_DEVICE(int nbx,int i,int j,int k)noexcept{
      amrex::Real x=plo[0]+(i+0.5)*dx[0], y=plo[1]+(j+0.5)*dx[1], z=plo[2]+(k+0.5)*dx[2];
      for (int n = 0; n < leak_count; ++n) {
        Leak::apply_single_species_source(
          src_arrs[nbx], i, j, k, x, y, z, leak_sources[n], DENSITY, VELX, VELY,
          VELZ, RHOH, FIRSTSPEC, NUM_SPECIES);
      }
      if (timed_ignition_configured && ignition_qdot > 0.0) {
        const amrex::Real dr2 =
          (x - ignition_xc) * (x - ignition_xc) +
          (y - ignition_yc) * (y - ignition_yc) +
          (z - ignition_zc) * (z - ignition_zc);
        if (dr2 <= ignition_radius2) {
          src_arrs[nbx](i, j, k, RHOH) += ignition_qdot;
        }
      }
    });
    amrex::Gpu::streamSynchronize();
  }
};
using ProblemSpecificFunctions=MyProblemSpecificFunctions; using ProbParm=MyProbParm;
#endif
