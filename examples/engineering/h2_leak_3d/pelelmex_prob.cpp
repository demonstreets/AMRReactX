#include <PeleLMeX.H>
#include <AMReX_ParmParse.H>
#include <AMReX.H>
#include <AMReX_Vector.H>
#include "pelelmex_prob.H"
#include <cmath>
#include <cstdio>
#include <string>
#ifdef AMREX_USE_EB
#include <AMReX_EB2.H>
#include <AMReX_EB2_IF.H>
#include "eb2_factory.H"
#endif

void PeleLM::readProbParm() {
  amrex::ParmParse pp("prob");
  pp.query("P_mean",prob_parm->P_mean); pp.query("T_mean",prob_parm->T_mean);
  pp.query("wind_u",prob_parm->wind_u); pp.query("wind_v",prob_parm->wind_v);
  pp.query("leak_xc",prob_parm->leak_xc); pp.query("leak_yc",prob_parm->leak_yc); pp.query("leak_zc",prob_parm->leak_zc);
  pp.query("leak_rate",prob_parm->leak_rate); pp.query("leak_radius",prob_parm->leak_radius);
  prob_parm->leak0_xc = prob_parm->leak_xc;
  prob_parm->leak0_yc = prob_parm->leak_yc;
  prob_parm->leak0_zc = prob_parm->leak_zc;
  prob_parm->leak0_radius = prob_parm->leak_radius;
  pp.query("leak_count",prob_parm->leak_count);
  pp.query("leak_source_count",prob_parm->leak_count);
  if (prob_parm->leak_count < 1 || prob_parm->leak_count > MyProbParm::max_leak_sources) {
    amrex::Abort("prob.leak_count must be between 1 and 4 for h2_leak_3d");
  }
  pp.query("leak0_xc",prob_parm->leak0_xc); pp.query("leak0_yc",prob_parm->leak0_yc); pp.query("leak0_zc",prob_parm->leak0_zc);
  pp.query("leak0_radius",prob_parm->leak0_radius); pp.query("leak0_fraction",prob_parm->leak0_fraction);
  pp.query("leak0_orifice_diameter",prob_parm->leak0_orifice_diameter); pp.query("leak0_orifice_area",prob_parm->leak0_orifice_area);
  pp.query("leak1_xc",prob_parm->leak1_xc); pp.query("leak1_yc",prob_parm->leak1_yc); pp.query("leak1_zc",prob_parm->leak1_zc);
  pp.query("leak1_radius",prob_parm->leak1_radius); pp.query("leak1_fraction",prob_parm->leak1_fraction);
  pp.query("leak1_orifice_diameter",prob_parm->leak1_orifice_diameter); pp.query("leak1_orifice_area",prob_parm->leak1_orifice_area);
  pp.query("leak2_xc",prob_parm->leak2_xc); pp.query("leak2_yc",prob_parm->leak2_yc); pp.query("leak2_zc",prob_parm->leak2_zc);
  pp.query("leak2_radius",prob_parm->leak2_radius); pp.query("leak2_fraction",prob_parm->leak2_fraction);
  pp.query("leak2_orifice_diameter",prob_parm->leak2_orifice_diameter); pp.query("leak2_orifice_area",prob_parm->leak2_orifice_area);
  pp.query("leak3_xc",prob_parm->leak3_xc); pp.query("leak3_yc",prob_parm->leak3_yc); pp.query("leak3_zc",prob_parm->leak3_zc);
  pp.query("leak3_radius",prob_parm->leak3_radius); pp.query("leak3_fraction",prob_parm->leak3_fraction);
  pp.query("leak3_orifice_diameter",prob_parm->leak3_orifice_diameter); pp.query("leak3_orifice_area",prob_parm->leak3_orifice_area);
  pp.query("leak_vel_x",prob_parm->leak_vel_x); pp.query("leak_vel_y",prob_parm->leak_vel_y); pp.query("leak_vel_z",prob_parm->leak_vel_z);
  pp.query("leak_T",prob_parm->leak_T);
  std::string fuel_species = "H2";
  pp.query("fuel_species", fuel_species);
  pp.query("leak_species", fuel_species);
  pp.query("source_species", fuel_species);
  std::snprintf(
    prob_parm->fuel_species_name, MyProbParm::fuel_species_name_len, "%s",
    fuel_species.c_str());
  amrex::Vector<std::string> species_names;
  CKSYMS_STR(species_names);
  prob_parm->fuel_species_index = -1;
  for (int n = 0; n < static_cast<int>(species_names.size()); ++n) {
    if (species_names[n] == fuel_species) {
      prob_parm->fuel_species_index = n;
      break;
    }
  }
  if (prob_parm->fuel_species_index < 0 ||
      prob_parm->fuel_species_index >= NUM_SPECIES) {
    amrex::Abort("prob.fuel_species was not found in the compiled chemistry mechanism");
  }
  amrex::Print() << "Engineering leak fuel species: name=" << fuel_species
                 << ", index=" << prob_parm->fuel_species_index
                 << ", mechanism_species_count=" << species_names.size() << "\n";
  std::string leak_model = "fixed_mass_flow";
  pp.query("leak_model", leak_model);
  if (leak_model == "fixed_mass_flow" || leak_model == "fixed" || leak_model == "constant_mdot") {
    prob_parm->leak_model = 0;
  } else if (leak_model == "pressure_orifice" || leak_model == "orifice" || leak_model == "tank_orifice") {
    prob_parm->leak_model = 1;
  } else if (leak_model == "tank_blowdown" || leak_model == "transient_tank" || leak_model == "blowdown") {
    prob_parm->leak_model = 2;
  } else if (leak_model == "linepack_blowdown" || leak_model == "pipe_blowdown" || leak_model == "linepack") {
    prob_parm->leak_model = 3;
  } else {
    amrex::Abort("prob.leak_model must be fixed_mass_flow, pressure_orifice, tank_blowdown, or linepack_blowdown");
  }
  pp.query("leak_use_orifice_velocity",prob_parm->leak_use_orifice_velocity);
  pp.query("leak_tank_pressure",prob_parm->leak_tank_pressure);
  pp.query("leak_ambient_pressure",prob_parm->leak_ambient_pressure);
  pp.query("leak_orifice_diameter",prob_parm->leak_orifice_diameter);
  pp.query("leak_orifice_area",prob_parm->leak_orifice_area);
  pp.query("leak_discharge_coeff",prob_parm->leak_discharge_coeff);
  pp.query("leak_line_diameter",prob_parm->leak_line_diameter);
  pp.query("leak_line_length",prob_parm->leak_line_length);
  pp.query("leak_line_friction_factor",prob_parm->leak_line_friction_factor);
  pp.query("leak_line_loss_coeff",prob_parm->leak_line_loss_coeff);
  pp.query("leak_linepack_pressure",prob_parm->leak_linepack_pressure);
  pp.query("leak_pipe_pressure",prob_parm->leak_linepack_pressure);
  pp.query("leak_linepack_volume",prob_parm->leak_linepack_volume);
  pp.query("leak_pipe_volume",prob_parm->leak_linepack_volume);
  pp.query("leak_valve_open_time",prob_parm->leak_valve_open_time);
  pp.query("leak_valve_ramp_time",prob_parm->leak_valve_ramp_time);
  pp.query("leak_valve_initial_fraction",prob_parm->leak_valve_initial_fraction);
  pp.query("leak_valve_final_fraction",prob_parm->leak_valve_final_fraction);
  pp.query("leak_rupture_time",prob_parm->leak_valve_open_time);
  pp.query("leak_rupture_ramp_time",prob_parm->leak_valve_ramp_time);
  int declared_leak_schedule_count = -1;
  pp.query("leak_schedule_count", declared_leak_schedule_count);
  amrex::Vector<amrex::Real> leak_schedule_times;
  amrex::Vector<amrex::Real> leak_schedule_rates;
  amrex::Vector<amrex::Real> leak_schedule_temperatures;
  amrex::Vector<amrex::Real> leak_schedule_vel_x;
  amrex::Vector<amrex::Real> leak_schedule_vel_y;
  amrex::Vector<amrex::Real> leak_schedule_vel_z;
  amrex::Vector<amrex::Real> leak_schedule_radius;
  amrex::Vector<amrex::Real> leak_schedule_x;
  amrex::Vector<amrex::Real> leak_schedule_y;
  amrex::Vector<amrex::Real> leak_schedule_z;
  pp.queryarr("leak_schedule_times", leak_schedule_times);
  pp.queryarr("leak_schedule_rates", leak_schedule_rates);
  pp.queryarr("leak_schedule_temperatures", leak_schedule_temperatures);
  pp.queryarr("leak_schedule_vel_x", leak_schedule_vel_x);
  pp.queryarr("leak_schedule_vel_y", leak_schedule_vel_y);
  pp.queryarr("leak_schedule_vel_z", leak_schedule_vel_z);
  pp.queryarr("leak_schedule_radius", leak_schedule_radius);
  pp.queryarr("leak_schedule_x", leak_schedule_x);
  pp.queryarr("leak_schedule_y", leak_schedule_y);
  pp.queryarr("leak_schedule_z", leak_schedule_z);
  pp.queryarr("leak_schedule_temps", leak_schedule_temperatures);
  pp.queryarr("leak_mdot_times", leak_schedule_times);
  pp.queryarr("leak_mdot_rates", leak_schedule_rates);
  pp.queryarr("leak_temperature_schedule", leak_schedule_temperatures);
  pp.queryarr("leak_velocity_x_schedule", leak_schedule_vel_x);
  pp.queryarr("leak_velocity_y_schedule", leak_schedule_vel_y);
  pp.queryarr("leak_velocity_z_schedule", leak_schedule_vel_z);
  pp.queryarr("leak_radius_schedule", leak_schedule_radius);
  pp.queryarr("leak_x_schedule", leak_schedule_x);
  pp.queryarr("leak_y_schedule", leak_schedule_y);
  pp.queryarr("leak_z_schedule", leak_schedule_z);
  if (!leak_schedule_times.empty() || !leak_schedule_rates.empty() ||
      !leak_schedule_temperatures.empty() ||
      !leak_schedule_vel_x.empty() || !leak_schedule_vel_y.empty() ||
      !leak_schedule_vel_z.empty() ||
      !leak_schedule_radius.empty() || !leak_schedule_x.empty() ||
      !leak_schedule_y.empty() || !leak_schedule_z.empty() ||
      declared_leak_schedule_count >= 0) {
    if (leak_schedule_times.empty() || leak_schedule_rates.empty()) {
      amrex::Abort("prob.leak_schedule_times and prob.leak_schedule_rates must be provided together");
    }
    if (leak_schedule_times.size() != leak_schedule_rates.size()) {
      amrex::Abort("prob.leak_schedule_times and prob.leak_schedule_rates must have the same length");
    }
    if (leak_schedule_times.size() < 2 ||
        leak_schedule_times.size() > MyProbParm::max_leak_schedule_points) {
      amrex::Abort("prob.leak_schedule_times/rates must contain 2 to 64 points");
    }
    if (!leak_schedule_temperatures.empty() &&
        leak_schedule_temperatures.size() != leak_schedule_times.size()) {
      amrex::Abort("prob.leak_schedule_temperatures must match leak_schedule_times/rates length");
    }
    if ((!leak_schedule_vel_x.empty() &&
         leak_schedule_vel_x.size() != leak_schedule_times.size()) ||
        (!leak_schedule_vel_y.empty() &&
         leak_schedule_vel_y.size() != leak_schedule_times.size()) ||
        (!leak_schedule_vel_z.empty() &&
         leak_schedule_vel_z.size() != leak_schedule_times.size())) {
      amrex::Abort("prob.leak_schedule_vel_x/y/z must match leak_schedule_times/rates length");
    }
    if (!leak_schedule_radius.empty() &&
        leak_schedule_radius.size() != leak_schedule_times.size()) {
      amrex::Abort("prob.leak_schedule_radius must match leak_schedule_times/rates length");
    }
    const bool has_location_schedule =
      !leak_schedule_x.empty() || !leak_schedule_y.empty() || !leak_schedule_z.empty();
    if (has_location_schedule &&
        (leak_schedule_x.size() != leak_schedule_times.size() ||
         leak_schedule_y.size() != leak_schedule_times.size() ||
         leak_schedule_z.size() != leak_schedule_times.size())) {
      amrex::Abort("prob.leak_schedule_x/y/z must be provided together and match leak_schedule_times/rates length");
    }
    if ((!leak_schedule_radius.empty() || has_location_schedule) &&
        prob_parm->leak_count != 1) {
      amrex::Abort("prob.leak_schedule_radius and prob.leak_schedule_x/y/z are supported only for single-source leaks");
    }
    if (leak_schedule_temperatures.empty()) {
      leak_schedule_temperatures.resize(leak_schedule_times.size(), prob_parm->leak_T);
    }
    if (leak_schedule_vel_x.empty()) {
      leak_schedule_vel_x.resize(leak_schedule_times.size(), prob_parm->leak_vel_x);
    }
    if (leak_schedule_vel_y.empty()) {
      leak_schedule_vel_y.resize(leak_schedule_times.size(), prob_parm->leak_vel_y);
    }
    if (leak_schedule_vel_z.empty()) {
      leak_schedule_vel_z.resize(leak_schedule_times.size(), prob_parm->leak_vel_z);
    }
    prob_parm->leak_schedule_has_radius = leak_schedule_radius.empty() ? 0 : 1;
    prob_parm->leak_schedule_has_location = has_location_schedule ? 1 : 0;
    if (leak_schedule_radius.empty()) {
      leak_schedule_radius.resize(leak_schedule_times.size(), prob_parm->leak0_radius);
    }
    if (!has_location_schedule) {
      leak_schedule_x.resize(leak_schedule_times.size(), prob_parm->leak0_xc);
      leak_schedule_y.resize(leak_schedule_times.size(), prob_parm->leak0_yc);
      leak_schedule_z.resize(leak_schedule_times.size(), prob_parm->leak0_zc);
    }
    if (declared_leak_schedule_count >= 0 &&
        declared_leak_schedule_count != static_cast<int>(leak_schedule_times.size())) {
      amrex::Abort("prob.leak_schedule_count must match leak_schedule_times/rates length");
    }
    prob_parm->leak_schedule_count = static_cast<int>(leak_schedule_times.size());
    amrex::Real last_time = -1.0;
    for (int n = 0; n < prob_parm->leak_schedule_count; ++n) {
      const amrex::Real t = leak_schedule_times[n];
      const amrex::Real r = leak_schedule_rates[n];
      const amrex::Real temp = leak_schedule_temperatures[n];
      const amrex::Real vx = leak_schedule_vel_x[n];
      const amrex::Real vy = leak_schedule_vel_y[n];
      const amrex::Real vz = leak_schedule_vel_z[n];
      const amrex::Real radius = leak_schedule_radius[n];
      const amrex::Real x = leak_schedule_x[n];
      const amrex::Real y = leak_schedule_y[n];
      const amrex::Real z = leak_schedule_z[n];
      if (!std::isfinite(t) || !std::isfinite(r) || !std::isfinite(temp) ||
          !std::isfinite(vx) || !std::isfinite(vy) || !std::isfinite(vz) ||
          !std::isfinite(radius) || !std::isfinite(x) || !std::isfinite(y) ||
          !std::isfinite(z)) {
        amrex::Abort("prob.leak_schedule_times/rates/temperatures/velocities/geometry must be finite");
      }
      if (t < 0.0 || (n > 0 && t <= last_time)) {
        amrex::Abort("prob.leak_schedule_times must be nonnegative and strictly increasing");
      }
      if (r < 0.0) {
        amrex::Abort("prob.leak_schedule_rates must be nonnegative");
      }
      if (temp <= 0.0) {
        amrex::Abort("prob.leak_schedule_temperatures must be positive");
      }
      if (radius <= 0.0) {
        amrex::Abort("prob.leak_schedule_radius must be positive");
      }
      prob_parm->leak_schedule_times[n] = t;
      prob_parm->leak_schedule_rates[n] = r;
      prob_parm->leak_schedule_temperatures[n] = temp;
      prob_parm->leak_schedule_vel_x[n] = vx;
      prob_parm->leak_schedule_vel_y[n] = vy;
      prob_parm->leak_schedule_vel_z[n] = vz;
      prob_parm->leak_schedule_radius[n] = radius;
      prob_parm->leak_schedule_x[n] = x;
      prob_parm->leak_schedule_y[n] = y;
      prob_parm->leak_schedule_z[n] = z;
      last_time = t;
    }
  }
  pp.query("leak_gamma",prob_parm->leak_gamma);
  pp.query("leak_gas_constant",prob_parm->leak_gas_constant);
  pp.query("leak_compressibility_factor",prob_parm->leak_compressibility_factor);
  pp.query("leak_Z",prob_parm->leak_compressibility_factor);
  pp.query("leak_real_gas_Z",prob_parm->leak_compressibility_factor);
  if (prob_parm->leak_compressibility_factor <= 0.0) {
    amrex::Abort("prob.leak_compressibility_factor must be positive");
  }
  pp.query("leak_tank_volume",prob_parm->leak_tank_volume);
  pp.query("leak_blowdown_substeps",prob_parm->leak_blowdown_substeps);
  if (prob_parm->leak_valve_open_time < 0.0 ||
      prob_parm->leak_valve_ramp_time < 0.0 ||
      prob_parm->leak_valve_initial_fraction < 0.0 ||
      prob_parm->leak_valve_initial_fraction > 1.0 ||
      prob_parm->leak_valve_final_fraction < 0.0 ||
      prob_parm->leak_valve_final_fraction > 1.0) {
    amrex::Abort("prob.leak valve schedule requires nonnegative open/ramp times and fractions in [0,1]");
  }
  pp.query("obstacle_radius",prob_parm->obstacle_radius);
  pp.query("obstacle_height",prob_parm->obstacle_height);
  pp.query("obstacle_xc",prob_parm->obstacle_xc); pp.query("obstacle_yc",prob_parm->obstacle_yc); pp.query("obstacle_zc",prob_parm->obstacle_zc);
  pp.query("obstacle_count",prob_parm->obstacle_count);
  pp.query("obstacle_direction",prob_parm->obstacle_direction);
  pp.query("obstacle_has_fluid_inside",prob_parm->obstacle_has_fluid_inside);
  pp.query("initial_flammable_cloud",prob_parm->initial_flammable_cloud);
  pp.query("cloud_xc",prob_parm->cloud_xc); pp.query("cloud_yc",prob_parm->cloud_yc); pp.query("cloud_zc",prob_parm->cloud_zc);
  pp.query("cloud_rx",prob_parm->cloud_rx); pp.query("cloud_ry",prob_parm->cloud_ry); pp.query("cloud_rz",prob_parm->cloud_rz);
  pp.query("cloud_T",prob_parm->cloud_T);
  pp.query("cloud_YH2",prob_parm->cloud_YFuel);
  pp.query("cloud_YFuel",prob_parm->cloud_YFuel);
  pp.query("cloud_fuel_mass_fraction",prob_parm->cloud_YFuel);
  pp.query("cloud_YO2",prob_parm->cloud_YO2); pp.query("cloud_YN2",prob_parm->cloud_YN2);
  pp.query("ignition_hotspot",prob_parm->ignition_hotspot);
  pp.query("ignition_xc",prob_parm->ignition_xc); pp.query("ignition_yc",prob_parm->ignition_yc); pp.query("ignition_zc",prob_parm->ignition_zc);
  pp.query("ignition_radius",prob_parm->ignition_radius);
  pp.query("ignition_T",prob_parm->ignition_T);
  pp.query("ignition_source",prob_parm->ignition_source);
  pp.query("delayed_ignition",prob_parm->ignition_source);
  pp.query("ignition_start_time",prob_parm->ignition_start_time);
  pp.query("ignition_delay_time",prob_parm->ignition_start_time);
  pp.query("ignition_duration",prob_parm->ignition_duration);
  pp.query("ignition_power",prob_parm->ignition_power);
  if (prob_parm->ignition_source != 0 &&
      (prob_parm->ignition_start_time < 0.0 ||
       prob_parm->ignition_duration <= 0.0 ||
       prob_parm->ignition_power <= 0.0 ||
       prob_parm->ignition_radius <= 0.0)) {
    amrex::Abort("prob.ignition_source requires nonnegative start_time and positive duration/power/radius");
  }
}
void PeleLM::freeProbParm(){}
void pc_prob_close(){}
extern "C"{void amrex_probinit(const int*,const int*,const int*,const amrex::Real*,const amrex::Real*){}}
#ifdef AMREX_USE_EB
void MyProblemSpecificFunctions::EBUserDefined(const amrex::Geometry& geom,const int req,const int max_coarse){
  amrex::ParmParse pp("prob");
  amrex::Real radius=0.125, height=1.0, xc=2.5, yc=1.25, zc=1.25;
  int count=1, direction=2, has_fluid_inside=0;
  pp.query("obstacle_radius", radius);
  pp.query("obstacle_height", height);
  pp.query("obstacle_xc", xc); pp.query("obstacle_yc", yc); pp.query("obstacle_zc", zc);
  pp.query("obstacle_count", count);
  pp.query("obstacle_direction", direction);
  pp.query("obstacle_has_fluid_inside", has_fluid_inside);
  std::string obstacle_geometry = "cylinder";
  pp.query("obstacle_geometry", obstacle_geometry);
  if (obstacle_geometry == "stl" || obstacle_geometry == "STL") {
    std::string stl_file = "cube.stl";
    std::string merged_stl_file = "codex_merged_stl_obstacles.stl";
    amrex::Real stl_scale = 1.0, stl_xc = xc, stl_yc = yc, stl_zc = zc;
    int stl_reverse_normal = 0, stl_ngrow = 4;
    pp.query("obstacle_stl_file", stl_file);
    pp.query("obstacle_stl_merged_file", merged_stl_file);
    pp.query("obstacle_stl_scale", stl_scale);
    pp.query("obstacle_stl_xc", stl_xc);
    pp.query("obstacle_stl_yc", stl_yc);
    pp.query("obstacle_stl_zc", stl_zc);
    pp.query("obstacle_stl_reverse_normal", stl_reverse_normal);
    pp.query("obstacle_stl_ngrow", stl_ngrow);

    amrex::Vector<std::string> stl_files;
    const int stl_file_count = pp.countval("obstacle_stl_files");
    if (stl_file_count > 0) {
      stl_files.resize(stl_file_count);
      pp.getarr("obstacle_stl_files", stl_files, 0, stl_file_count);
    }

    if (!stl_files.empty()) {
      const int stl_scale_count = pp.countval("obstacle_stl_scales");
      const int stl_xc_count = pp.countval("obstacle_stl_xcs");
      const int stl_yc_count = pp.countval("obstacle_stl_ycs");
      const int stl_zc_count = pp.countval("obstacle_stl_zcs");
      const bool use_stl_file_transforms =
        stl_scale_count > 0 || stl_xc_count > 0 ||
        stl_yc_count > 0 || stl_zc_count > 0;

      amrex::Print() << "Engineering leak UserDefined EB STL files: count=" << stl_files.size()
                     << ", merged=" << merged_stl_file
                     << ", scale=" << stl_scale
                     << ", center=(" << stl_xc << "," << stl_yc << "," << stl_zc << ")"
                     << ", reverse_normal=" << stl_reverse_normal
                     << ", ngrow=" << stl_ngrow
                     << ", per_file_transforms=" << (use_stl_file_transforms ? 1 : 0)
                     << "\n";

      if (use_stl_file_transforms) {
        if (stl_scale_count != stl_file_count ||
            stl_xc_count != stl_file_count ||
            stl_yc_count != stl_file_count ||
            stl_zc_count != stl_file_count) {
          amrex::Abort("prob.obstacle_stl_scales/xcs/ycs/zcs must all match prob.obstacle_stl_files count");
        }
        amrex::Vector<amrex::Real> stl_file_scales(stl_file_count);
        amrex::Vector<amrex::Real> stl_file_xcs(stl_file_count);
        amrex::Vector<amrex::Real> stl_file_ycs(stl_file_count);
        amrex::Vector<amrex::Real> stl_file_zcs(stl_file_count);
        pp.getarr("obstacle_stl_scales", stl_file_scales, 0, stl_file_count);
        pp.getarr("obstacle_stl_xcs", stl_file_xcs, 0, stl_file_count);
        pp.getarr("obstacle_stl_ycs", stl_file_ycs, 0, stl_file_count);
        pp.getarr("obstacle_stl_zcs", stl_file_zcs, 0, stl_file_count);

        std::vector<amrex::Real> file_scales(stl_file_scales.begin(),
                                             stl_file_scales.end());
        std::vector<amrex::Array<amrex::Real,3>> file_centers;
        file_centers.reserve(stl_file_count);
        for (int i = 0; i < stl_file_count; ++i) {
          file_centers.push_back(
            amrex::Array<amrex::Real,3>{stl_file_xcs[i], stl_file_ycs[i], stl_file_zcs[i]});
        }
        pele::buildFromSTLFilesWithTransforms(
          std::vector<std::string>(stl_files.begin(), stl_files.end()),
          merged_stl_file, geom, max_coarse, file_scales, file_centers,
          stl_reverse_normal, req, stl_ngrow);
        return;
      }

      pele::buildFromSTLFiles(std::vector<std::string>(stl_files.begin(), stl_files.end()),
                              merged_stl_file, geom, max_coarse, stl_scale,
                              amrex::Array<amrex::Real,3>{stl_xc, stl_yc, stl_zc},
                              stl_reverse_normal, req, stl_ngrow);
      return;
    }

    amrex::Print() << "Engineering leak UserDefined EB STL: file=" << stl_file
                   << ", scale=" << stl_scale
                   << ", center=(" << stl_xc << "," << stl_yc << "," << stl_zc << ")"
                   << ", reverse_normal=" << stl_reverse_normal
                   << ", ngrow=" << stl_ngrow << "\n";
    pele::buildFromSTL(stl_file, geom, max_coarse, stl_scale,
                       amrex::Array<amrex::Real,3>{stl_xc, stl_yc, stl_zc},
                       stl_reverse_normal, req, stl_ngrow);
    return;
  }
  if (obstacle_geometry != "cylinder" && obstacle_geometry != "cylinders") {
    amrex::Abort("prob.obstacle_geometry must be cylinder, cylinders, or stl for h2_leak_3d UserDefined EB");
  }
  if (count < 1 || count > 3) {
    amrex::Abort("prob.obstacle_count must be between 1 and 3 for h2_leak_3d UserDefined EB");
  }

  amrex::Real r0=radius, r1=radius, r2=radius;
  amrex::Real x0=xc, y0=yc, z0=zc;
  amrex::Real x1=xc, y1=yc, z1=zc;
  amrex::Real x2=xc, y2=yc, z2=zc;
  pp.query("obstacle0_radius", r0); pp.query("obstacle0_xc", x0); pp.query("obstacle0_yc", y0); pp.query("obstacle0_zc", z0);
  pp.query("obstacle1_radius", r1); pp.query("obstacle1_xc", x1); pp.query("obstacle1_yc", y1); pp.query("obstacle1_zc", z1);
  pp.query("obstacle2_radius", r2); pp.query("obstacle2_xc", x2); pp.query("obstacle2_yc", y2); pp.query("obstacle2_zc", z2);

  if (count == 1) {
    amrex::Print() << "Engineering leak UserDefined EB cylinder: radius=" << r0
                   << ", height=" << height
                   << ", direction=" << direction
                   << ", center=(" << x0 << "," << y0 << "," << z0 << ")"
                   << ", has_fluid_inside=" << has_fluid_inside << "\n";
  } else {
    amrex::Print() << "Engineering leak UserDefined EB cylinders: count=" << count
                   << ", height=" << height
                   << ", direction=" << direction
                   << ", has_fluid_inside=" << has_fluid_inside << "\n";
  }
  amrex::Print() << "  obstacle0: radius=" << r0 << ", center=(" << x0 << "," << y0 << "," << z0 << ")\n";
  if (count >= 2) {
    amrex::Print() << "  obstacle1: radius=" << r1 << ", center=(" << x1 << "," << y1 << "," << z1 << ")\n";
  }
  if (count >= 3) {
    amrex::Print() << "  obstacle2: radius=" << r2 << ", center=(" << x2 << "," << y2 << "," << z2 << ")\n";
  }

  amrex::EB2::CylinderIF cyl0(r0,height,direction,amrex::RealArray{x0,y0,z0},has_fluid_inside != 0);
  amrex::EB2::CylinderIF cyl1(r1,height,direction,amrex::RealArray{x1,y1,z1},has_fluid_inside != 0);
  amrex::EB2::CylinderIF cyl2(r2,height,direction,amrex::RealArray{x2,y2,z2},has_fluid_inside != 0);
  if (count == 1) {
    auto gshop=amrex::EB2::makeShop(cyl0);
    amrex::EB2::Build(gshop,geom,req,max_coarse);
  } else if (count == 2) {
    auto obstacles=amrex::EB2::makeUnion(cyl0,cyl1);
    auto gshop=amrex::EB2::makeShop(obstacles);
    amrex::EB2::Build(gshop,geom,req,max_coarse);
  } else {
    auto obstacles=amrex::EB2::makeUnion(cyl0,cyl1,cyl2);
    auto gshop=amrex::EB2::makeShop(obstacles);
    amrex::EB2::Build(gshop,geom,req,max_coarse);
  }
}
#endif
