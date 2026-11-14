"""Raw-field, front, spray and numerical-soot-foil analysis; PeleC CGS input."""
import argparse
import json
from pathlib import Path
import re
import sys
import subprocess

import numpy as np
import cantera as ct
from scipy.signal import find_peaks
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import amrex_reader
from read_native_spray import read_native_spray

def finite_window_autocorrelation(values, axis):
    """Match the finite-overlap normalized correlation without lag-sized copies."""
    n = values.shape[axis]
    lags = np.arange(1,n//2)
    spectrum = np.fft.rfft(values,n=2*n,axis=axis)
    products = np.fft.irfft(spectrum.conj()*spectrum,n=2*n,axis=axis)
    numerator = np.sum(products,axis=1-axis)[lags]
    squared = np.sum(values*values,axis=1-axis)
    cumulative = np.r_[0.,np.cumsum(squared)]
    suffix = np.r_[np.cumsum(squared[::-1])[::-1],0.]
    denominator = np.sqrt(cumulative[n-lags]*suffix[lags])
    return np.divide(numerator,denominator,out=np.zeros_like(numerator),where=denominator>0.).tolist()

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("run", type=Path)
p.add_argument("output", type=Path)
p.add_argument("--partial", action="store_true", help="inspect completed plotfiles from an ongoing run")
p.add_argument("--previous-run", type=Path, action="append", default=[],
               help="prepend checked segments; repeat this option in chronological order for multiple restarts")
args = p.parse_args()
run, out = args.run.resolve(), args.output.resolve()
exit_code = int((run/"exit_code").read_text()) if (run/"exit_code").exists() else None
if not args.partial and exit_code != 0:
    raise ValueError("a completed successful run is required; use --partial for an explicit progress analysis")
text = (run/"inputs").read_text()
profile_header = (run/"profile_SI.txt").open().readline().split()
if profile_header[:6] != ["#","distance_behind_shock_m","rho_kg_m3","p_Pa","T_K","u_m_s"]:
    raise ValueError("a named reference species header is required")
expected_species = profile_header[6:]
mechanism_root = Path(__file__).resolve().parents[1]/"external/PelePhysics/Mechanisms"
thermo = None
for mechanism_name in ["heptane_wd6", "heptane_lu_88sk"]:
    mechanism_file = mechanism_root/mechanism_name/"mechanism.yaml"
    if mechanism_file.is_file():
        candidate = ct.Solution(str(mechanism_file))
        if candidate.species_names == expected_species:
            thermo = candidate
            break
if thermo is None:
    raise ValueError("cannot identify thermodynamic validity range from the named reference species")
thermo_range = [float(thermo.min_temp), float(thermo.max_temp)]
def input_value(name):
    matches = re.findall(r"^"+re.escape(name)+r"\s*=\s*([^#\n]+)", text, flags=re.M)
    if not matches:
        raise ValueError(f"missing input {name}")
    return matches[-1].strip()
p0 = float(input_value("prob.p0"))
front0 = float(input_value("prob.front"))
stop_time = float(input_value("stop_time"))
plots = sorted(q for q in run.glob("plt*") if (q/"Header").is_file())
if not plots:
    raise ValueError("no complete native plotfiles")
out.mkdir(parents=True, exist_ok=False)
segments = [{"run": str(run), "exit_code": exit_code}]
for join_index, previous_path in enumerate(reversed(args.previous_run)):
    previous = previous_path.resolve()
    restart_time = amrex_reader.read_plotfile(str(plots[0]))["time"]
    previous_plots = sorted(q for q in previous.glob("plt*") if (q/"Header").is_file())
    previous_times = [(q, amrex_reader.read_plotfile(str(q))["time"]) for q in previous_plots]
    join = [q for q, t in previous_times if t == restart_time]
    if len(join) != 1:
        raise ValueError("previous segment must contain exactly one plot at the restart time")
    if (previous/"profile_SI.txt").read_bytes() != (run/"profile_SI.txt").read_bytes():
        raise ValueError("segments use different initialization references")
    join_name="restart_join_validation.json" if len(args.previous_run)==1 else f"restart_join_validation_{join_index}.json"
    subprocess.run([sys.executable, str(Path(__file__).with_name("validate_spray_restart.py")),
                    str(join[0]), str(plots[0]), "--output", str(out/join_name)],
                   check=True)
    plots = [q for q, t in previous_times if t < restart_time] + plots
    previous_exit = int((previous/"exit_code").read_text()) if (previous/"exit_code").exists() else None
    segments.insert(0, {"run": str(previous), "exit_code": previous_exit,
                       "included_before_time_s": restart_time,
                       "meaning": "partial source segment; continuity independently checked at restart"})
rows, fronts, profiles = [], [], []
last = None

def mean_x(value):
    return np.mean(value, axis=tuple(range(1, value.ndim)))

def front_curve(pressure, x):
    if pressure.ndim != 2:
        raise ValueError("this cellular analysis requires a two-dimensional gas field")
    curve = []
    for column in pressure.T:
        active = np.flatnonzero(column > 3.*p0)
        if not len(active) or active[-1] == len(x)-1:
            raise ValueError("leading shock is absent or touches the right boundary")
        i = active[-1]
        curve.append(x[i]+(3.*p0-column[i])/(column[i+1]-column[i])*(x[i+1]-x[i]))
    return np.asarray(curve)

for plot in plots:
    data = amrex_reader.read_plotfile(str(plot))
    fields = data["fields"]
    x = np.asarray(data["x"])
    curve = front_curve(fields["pressure"], x)
    shock = float(curve.mean())
    y_names = [name for name in fields if name.startswith("Y(")]
    if set(y_names) != {"Y("+name+")" for name in expected_species}:
        raise ValueError("all species in the named reference must be retained")
    row = {"plot": plot.name, "source_run": str(plot.parent), "time_s": data["time"], "shock_x_cm": shock,
           "shock_transverse_rms_mm": float(np.std(curve)*10.),
           "shock_transverse_span_mm": float(np.ptp(curve)*10.),
           "pressure_max_Pa": float(fields["pressure"].max()*.1),
           "pressure_min_Pa": float(fields["pressure"].min()*.1),
           "temperature_min_K": float(fields["Temp"].min()),
           "temperature_max_K": float(fields["Temp"].max()),
           "cells_below_thermo_temperature_range": int(np.count_nonzero(fields["Temp"] < thermo_range[0]-1.e-8)),
           "cells_above_thermo_temperature_range": int(np.count_nonzero(fields["Temp"] > thermo_range[1]+1.e-8)),
           "density_min_kg_m3": float(fields["density"].min()*1000.),
           "nonfinite_values": sum(int((~np.isfinite(v)).sum()) for v in fields.values()),
           "minimum_mass_fraction": min(float(fields[name].min()) for name in y_names),
           "maximum_species_sum_error": float(np.max(abs(sum(fields[name] for name in y_names)-1.)))}
    hrr = mean_x(fields["heatRelease"])
    near = (x < shock) & (x > max(x[0]-.01, shock-3.))
    ids = np.flatnonzero(near)
    ih = ids[np.argmax(hrr[ids])]
    positive = np.maximum(hrr[ids], 0.)
    row["heat_release_peak_gap_mm"] = float((shock-x[ih])*10.)
    row["positive_heat_release_centroid_gap_mm"] = float((shock-np.dot(x[ids], positive)/positive.sum())*10.) if positive.sum()>0. else None
    row["mean_heat_release_W_m3"] = float(np.mean(fields["heatRelease"])*.1)
    profile = {"time_s": data["time"], "shock_x_cm": shock, "x_cm": x.tolist(),
               "pressure_Pa": (mean_x(fields["pressure"])*.1).tolist(),
               "gas_temperature_K": mean_x(fields["Temp"]).tolist(),
               "heat_release_W_m3": (hrr*.1).tolist(),
               "gas_fuel_mass_fraction": mean_x(fields["Y(nc7h16)"]).tolist(),
               "water_mass_fraction": mean_x(fields["Y(h2o)"]).tolist()}
    row.update(liquid_mass_g=0., parcel_count=0, invalid_particles=0)
    if (plot/"particles/Header").exists():
        particles = read_native_spray(plot)
        f = particles["fields"]
        mass = f["number_density"]*.6814*np.pi/6.*f["diam"]**3
        bad = ((f["diam"]<=0.) | (f["temperature"]<=0.) | (f["number_density"]<0.) |
               ~np.isfinite(mass) | ~np.isfinite(f["temperature"]))
        for name, values in f.items():
            bad |= ~np.isfinite(values)
        row.update(liquid_mass_g=float(mass.sum()), parcel_count=particles["count"],
                   invalid_particles=int(bad.sum()))
        if particles["count"]:
            row.update(drop_temperature_max_K=float(f["temperature"].max()),
                       drop_diameter_min_um=float(f["diam"].min()*1.e4),
                       drop_diameter_max_um=float(f["diam"].max()*1.e4),
                       drop_speed_max_m_s=float(np.sqrt(f["xvel"]**2+f["yvel"]**2).max()*.01))
    if "spray_rho_src" in fields:
        evap = mean_x(fields["spray_rho_src"])*1000.
        profile["evaporation_kg_m3_s"] = evap.tolist()
        ie = ids[np.argmax(evap[ids])]
        row["evaporation_peak_gap_mm"] = float((shock-x[ie])*10.)
        profile["liquid_mass_density_kg_m3"] = (mean_x(fields["spray_density"])*1000.).tolist()
    rows.append(row)
    fronts.append(curve.tolist())
    profiles.append(profile)
    last = data

time = np.asarray([v["time_s"] for v in rows])
position = np.asarray([v["shock_x_cm"] for v in rows])*.01
tail = time >= .5*time[-1]
fit = None
if tail.sum() >= 4:
    coeff = np.polyfit(time[tail], position[tail], 1)
    velocity = np.gradient(position[tail], time[tail])
    fit = {"speed_m_s": float(coeff[0]), "start_time_s": float(time[tail][0]),
           "end_time_s": float(time[-1]), "points": int(tail.sum()),
           "position_fit_rms_m": float(np.sqrt(np.mean((position[tail]-np.polyval(coeff,time[tail]))**2))),
           "sampled_instantaneous_speed_std_m_s": float(velocity.std())}
valid = all(v["nonfinite_values"]==0 and v["temperature_min_K"]>0. and
            v["pressure_min_Pa"]>0. and
            v["density_min_kg_m3"]>0. and v["minimum_mass_fraction"]>=-1.e-12 and
            v["maximum_species_sum_error"]<1.e-8 and v["invalid_particles"]==0 for v in rows)
completed_requested_time = stop_time>0. and time[-1]>=stop_time*(1.-1.e-9)
result = {"run": str(run), "segments": segments, "species_names": expected_species, "exit_code": exit_code, "raw_fields_admissible": valid,
          "thermodynamic_temperature_range_K": thermo_range,
          "thermodynamic_extrapolation_in_saved_fields": any(r["cells_below_thermo_temperature_range"] or r["cells_above_thermo_temperature_range"] for r in rows),
          "completed_requested_time": bool(completed_requested_time), "partial_analysis": args.partial,
          "front_definition": "rightmost 3*p0 pressure crossing for each y, linearly interpolated in x, then transverse mean",
          "late_half_fit": fit, "rows": rows, "fronts_x_cm": fronts}

plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":10,
                     "axes.spines.top":False, "axes.spines.right":False})
quasi_one_dimensional = last["fields"]["pressure"].shape[1] <= 4
fig, axes = plt.subplots(2,2,figsize=(11,7.5),layout="constrained")
axes[0,0].plot(time*1.e6,position*1000.)
axes[0,0].set(xlabel="Time (microseconds)",ylabel="Mean shock position (mm)",title="A  Measured propagation")
if quasi_one_dimensional:
    axes[0,1].plot(.5*(time[1:]+time[:-1])*1.e6,np.diff(position)/np.diff(time))
    axes[0,1].set(xlabel="Time (microseconds)",ylabel="Interval shock speed (m/s)",title="B  Speed between saved outputs")
else:
    axes[0,1].plot(time*1.e6,[v["shock_transverse_span_mm"] for v in rows],label="Span")
    axes[0,1].plot(time*1.e6,[v["shock_transverse_rms_mm"] for v in rows],label="RMS")
    axes[0,1].set(xlabel="Time (microseconds)",ylabel="Transverse front displacement (mm)",title="B  Transverse-wave evolution")
    axes[0,1].legend()
axes[1,0].plot(time*1.e6,[v["heat_release_peak_gap_mm"] for v in rows],label="Heat-release peak")
if "evaporation_peak_gap_mm" in rows[-1]:
    axes[1,0].plot(time*1.e6,[v["evaporation_peak_gap_mm"] for v in rows],label="Evaporation peak")
axes[1,0].set(xlabel="Time (microseconds)",ylabel="Distance behind mean shock (mm)",title="C  Wave and source locations")
axes[1,0].legend()
if rows[0]["liquid_mass_g"]>0.:
    axes[1,1].plot(time*1.e6,[v["liquid_mass_g"]/rows[0]["liquid_mass_g"] for v in rows])
    axes[1,1].set(ylabel="Liquid mass / initial liquid mass")
else:
    axes[1,1].plot(time*1.e6,[v["temperature_max_K"] for v in rows])
    axes[1,1].set(ylabel="Maximum gas temperature (K)")
axes[1,1].set(xlabel="Time (microseconds)",title="D  Gas/liquid response")
fig.suptitle(run.name)
fig.savefig(out/"propagation_and_coupling.png",dpi=160)
plt.close(fig)

field = last["fields"]
x = np.asarray(last["x"])*10.
y = (np.arange(field["pressure"].shape[1])+.5)*last["dx"][1]*10.
extent = [x[0]-last["dx"][0]*5.,x[-1]+last["dx"][0]*5.,y[0]-last["dx"][1]*5.,y[-1]+last["dx"][1]*5.]
fig, axes = plt.subplots(3,1,figsize=(12,10),layout="constrained")
for ax,key,scale,label,cmap in zip(axes,["pressure","Temp","heatRelease"],[1.e-7,1.,.1],
                                 ["Pressure (MPa)","Gas temperature (K)","Heat release (W/m3)"],
                                 ["magma","inferno","viridis"]):
    if quasi_one_dimensional:
        ax.plot(x,np.mean(field[key],axis=1)*scale)
        ax.axvline(position[-1]*1000.,color=".4",ls="--",lw=.8,label="Leading shock")
        ax.set(xlabel="x (mm)",ylabel=label)
        ax.legend()
    else:
        im=ax.imshow((field[key]*scale).T,origin="lower",extent=extent,aspect="equal",cmap=cmap)
        fig.colorbar(im,ax=ax,label=label,pad=.01)
        ax.plot(np.asarray(fronts[-1])*10.,y,color="white",lw=.7)
        ax.set(xlabel="x (mm)",ylabel="y (mm)")
fig.suptitle(f"Instantaneous gas fields at {time[-1]*1.e6:.3f} microseconds")
fig.savefig(out/"instantaneous_fields.png",dpi=160)
plt.close(fig)

foils = sorted(q for q in run.glob("sootfoil*") if (q/"Header").is_file())
if foils:
    foil = amrex_reader.read_plotfile(str(foils[-1]))
    pm = foil["fields"]["maximum_pressure"]
    xf = np.asarray(foil["x"])
    # Exclude the initialized front and a margin at the moving shock. These
    # are pressure-pattern repeat distances, not a forced cellular label.
    foil_time = float(foil["time"])
    xstart = max(front0+2.,float(np.interp(.25*foil_time,time,position*100.)))
    history_start_row = next(v for v in rows if v["source_run"] == str(run))
    history_start_time = history_start_row["time_s"]
    if history_start_time>0.:
        # A restarted recorder does not contain earlier maxima. Use only
        # the region beyond the restart shock plus a 5 mm margin, so the
        # entire passage of the analyzed front belongs to this recorder.
        xstart=max(xstart,history_start_row["shock_x_cm"]+.5)
    xend = float(np.interp(foil_time,time,position*100.))-.5
    crop = (xf>=xstart)&(xf<=xend)
    enough_trace = crop.sum()>=12 and pm.shape[1]>=12 and foil_time>0.
    repeats = {"crop_x_cm":[xstart,xend] if xend>xstart else None,
               "history_start_time_s":history_start_time,
               "status":"evaluated" if enough_trace else "insufficient propagated trace",
               "meaning":"positive autocorrelation maxima of the pressure trace; assess with the displayed foil and a grid comparison"}
    if enough_trace:
        a = pm[crop].copy()
        a -= a.mean(axis=1,keepdims=True)
        for axis,name in [(0,"x"),(1,"y")]:
            corr=finite_window_autocorrelation(a,axis)
            peaks,properties=find_peaks(corr,height=.1,prominence=.05)
            repeats[name]={"lags_mm":((np.arange(len(corr))+1)*foil["dx"][axis]*10.).tolist(),
                           "correlation":corr,"positive_repeat_distances_mm":((peaks+1)*foil["dx"][axis]*10.).tolist()}
    result["pressure_trace_repeats"] = repeats
    fig,ax=plt.subplots(figsize=(12,4),layout="constrained")
    im=ax.imshow((pm*1.e-7).T,origin="lower",extent=extent,aspect="equal",cmap="magma")
    fig.colorbar(im,ax=ax,label="Maximum pressure (MPa)",pad=.01)
    if xend>xstart:
        ax.axvline(xstart*10.,color="white",ls="--",lw=.8)
        ax.axvline(xend*10.,color="white",ls="--",lw=.8)
    ax.set(xlabel="x (mm)",ylabel="y (mm)",title=f"Every-step numerical pressure trace, {history_start_time*1.e6:.3f} to {foil['time']*1.e6:.3f} microseconds")
    fig.savefig(out/"numerical_soot_foil.png",dpi=180)
    plt.close(fig)
    result["soot_foil"]={"plot":foils[-1].name,"time_s":foil["time"],"sampling_start_time_s":history_start_time,
                         "sampling":"each completed solver step in the current run segment; earlier maxima are not merged"}

(out/"analysis.json").write_text(json.dumps(result,indent=2))
(out/"mean_profiles.json").write_text(json.dumps(profiles,indent=2))
printed={k:v for k,v in result.items() if k not in ["rows","fronts_x_cm","pressure_trace_repeats"]}
if "pressure_trace_repeats" in result:
    repeat=result["pressure_trace_repeats"]
    printed["pressure_trace_repeats"]={k:v for k,v in repeat.items() if k not in ["x","y"]}
    for axis in ["x","y"]:
        if axis in repeat:
            printed["pressure_trace_repeats"][axis+"_positive_repeat_distances_mm"]=repeat[axis]["positive_repeat_distances_mm"]
print(json.dumps(printed))
if not valid:
    raise SystemExit(2)
if not args.partial and not completed_requested_time:
    raise SystemExit(3)
