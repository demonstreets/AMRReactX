"""Prepare an explicit, reproducible native gas/spray detonation case."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess

import cantera as ct

here = Path(__file__).resolve().parent
root = here.parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("output", type=Path)
p.add_argument("--reference", type=Path, required=True,
               help="directory containing profile_SI.txt and metadata.json")
p.add_argument("--binary", type=Path)
p.add_argument("--nx", type=int, default=400)
p.add_argument("--ny", type=int, default=80)
p.add_argument("--length-cm", type=float, default=20.)
p.add_argument("--height-cm", type=float, default=4.)
p.add_argument("--front-cm", type=float, default=2.)
p.add_argument("--end-time", type=float, default=8.e-5)
p.add_argument("--cfl", type=float, default=.1)
p.add_argument("--perturbation-cm", type=float, default=.04)
p.add_argument("--multimode", action="store_true")
p.add_argument("--walls", action="store_true")
p.add_argument("--dry", action="store_true")
p.add_argument("--diameter-um", type=float, default=10.)
p.add_argument("--liquid-phi", type=float, default=.4)
p.add_argument("--gpu", action="store_true")
p.add_argument("--linear-solver", choices=["sparse_direct", "custom_direct"],
               default="sparse_direct", help="GPU QR or opt-in cuBLAS batched LU")
p.add_argument("--wd6-regularization", type=float, default=0., help="compiled concentration epsilon in mol/m^3; zero is original WD")
p.add_argument("--ranks", type=int, default=1)
p.add_argument("--devices", default="0", help="CUDA device indices in rank order")
p.add_argument("--cuda-home", type=Path)
p.add_argument("--wave-history", action="store_true")
p.add_argument("--output-interval", type=float, default=5.e-7)
p.add_argument("--history-interval", type=float, default=2.e-6)
p.add_argument("--max-grid-size", type=int, nargs=2, metavar=("NX", "NY"),
               help="maximum AMReX box dimensions; GPU chemistry batches one box at a time")
p.add_argument("--chemistry-tile-size",type=int,nargs=2,metavar=("NX","NY"),
               help="subdivide chemistry batches independently of hydro boxes")
p.add_argument("--cell-chemistry-integrator",choices=["cvode","wd6_extrapolated"],default="cvode")
p.add_argument("--cell-chemistry-rtol",type=float,default=1.e-6)
p.add_argument("--cell-chemistry-atol-y",type=float,default=1.e-13)
p.add_argument("--run", action="store_true", help="launch after preparing the case")
args = p.parse_args()
if args.nx <= 0 or args.ny <= 0 or args.nx % 4 or args.ny % 4:
    p.error("cell counts must be positive multiples of four")
dx, dy = args.length_cm / args.nx, args.height_cm / args.ny
if dx <= 0. or dy <= 0. or not math.isclose(dx, dy, rel_tol=1.e-12):
    p.error("the two-dimensional spray depth convention requires square cells")
if not (0. < args.cfl <= .5 and args.end_time > 0. and args.ranks > 0):
    p.error("require 0 < CFL <= 0.5, a positive end time and a positive rank count")
if any(not math.isfinite(v) or v<=0. for v in [args.output_interval,args.history_interval]):
    p.error("output intervals must be finite and positive")
if args.diameter_um <= 0. or args.liquid_phi < 0.:
    p.error("require positive diameter and nonnegative liquid equivalence ratio")
if args.max_grid_size and any(n < 4 or n % 4 for n in args.max_grid_size):
    p.error("maximum grid sizes must be positive multiples of four")
if args.chemistry_tile_size and any(n<=0 for n in args.chemistry_tile_size):
    p.error("chemical batch dimensions must be positive")
if any(not math.isfinite(v) or v<=0. for v in [args.cell_chemistry_rtol,args.cell_chemistry_atol_y]):
    p.error("cell chemistry tolerances must be finite and positive")
if not abs(args.perturbation_cm) < args.front_cm < args.length_cm-abs(args.perturbation_cm):
    p.error("the perturbed initial front must lie inside the domain")
devices = args.devices.split(",")
if args.gpu and (any(not v.isdigit() for v in devices) or
                 len(devices) != args.ranks or len(set(devices)) != len(devices)):
    p.error("provide one distinct CUDA device index per MPI rank")
reference = args.reference.resolve()
meta = json.loads((reference / "metadata.json").read_text())
mechanism_name = meta["mechanism"]
if mechanism_name not in ["heptane_lu_88sk","heptane_wd6"]:
    p.error("unsupported reference mechanism")
gas = ct.Solution(str(root / "external/PeleC/Submodules/PelePhysics/Mechanisms" / mechanism_name / "mechanism.yaml"))
if meta["species_names"] != gas.species_names:
    p.error("reference and compiled mechanism must use the same species ordering")
upstream = meta["upstream"]
gas.TPY = upstream["T"], upstream["p"], upstream["Y"]
gas_phi = gas.equivalence_ratio("nc7h16", {"o2": 1., "n2": 3.76})
if gas_phi <= 0.:
    p.error("reference must contain a fuel-bearing upstream gas")
liquid_phi = 0. if args.dry else args.liquid_phi
rho_liquid_per_volume = gas.density*.001*gas.Y[gas.species_index("nc7h16")]*liquid_phi/gas_phi
diameter = args.diameter_um*1.e-4
rho_liquid = .6814
drop_mass = rho_liquid*math.pi/6.*diameter**3
weight = rho_liquid_per_volume*dx*dy*dx/drop_mass
binary = (args.binary or here / ("spray_detonation2d.gnu.MPI.CUDA.ex" if args.gpu
                                else "spray_detonation2d.gnu.MPI.ex")).resolve()
if args.run and not binary.is_file():
    p.error(f"missing binary: {binary}")
text = (here / "inputs.detonation").read_text()

def set_input(key, value):
    global text
    pattern = r"^"+re.escape(key)+r"\s*=.*$"
    text, count = re.subn(pattern, key+" = "+str(value), text, flags=re.M)
    if count != 1:
        raise ValueError(f"expected one template entry for {key}, got {count}")

set_input("geometry.prob_hi", f"{args.length_cm:.17g} {args.height_cm:.17g}")
set_input("amr.n_cell", f"{args.nx} {args.ny}")
set_input("amr.max_grid_size", "128 32" if args.gpu else "32 16")
if args.max_grid_size:
    set_input("amr.max_grid_size", " ".join(map(str, args.max_grid_size)))
set_input("stop_time", format(args.end_time, ".17g"))
set_input("pelec.cfl", args.cfl)
set_input("prob.front", args.front_cm)
set_input("prob.perturbation", args.perturbation_cm)
set_input("prob.p0", format(upstream["p"]*10., ".17g"))
set_input("prob.T0", upstream["T"])
set_input("prob.upstream_Y", " ".join(format(v, ".17g") for v in upstream["Y"]))
set_input("pelec.do_spray_particles", int(liquid_phi > 0.))
if args.walls:
    set_input("geometry.is_periodic", "0 0")
    set_input("pelec.lo_bc", "FOExtrap SlipWall")
    set_input("pelec.hi_bc", "FOExtrap SlipWall")
if args.multimode:
    text += "prob.perturbation_mode = 2\n"
if args.gpu:
    set_input("cvode.solve_type", args.linear_solver)
    text += "amrex.the_arena_init_size = 268435456\n"
if args.wave_history:
    text += "prob.record_wave_history = 1\nprob.wave_history_interval = "+format(args.history_interval,".17g")+"\n"
set_input("amr.plot_per",format(args.output_interval,".17g"))
if args.chemistry_tile_size:
    text += "pelec.chemistry_tile_size = "+" ".join(map(str,args.chemistry_tile_size))+"\n"
if args.cell_chemistry_integrator == "wd6_extrapolated" and (mechanism_name != "heptane_wd6" or args.wd6_regularization<=0.):
    p.error("wd6_extrapolated requires heptane_wd6 and positive regularization")
text += "pelec.cell_chemistry_integrator = "+args.cell_chemistry_integrator+"\n"
text += "pelec.cell_chemistry_rtol = "+format(args.cell_chemistry_rtol,".17g")+"\n"
text += "pelec.cell_chemistry_atol_y = "+format(args.cell_chemistry_atol_y,".17g")+"\n"
if mechanism_name == "heptane_wd6":
    if not math.isfinite(args.wd6_regularization) or args.wd6_regularization < 0.:
        p.error("WD6 concentration epsilon must be finite and nonnegative")
    text += "prob.expected_wd6_regularization = "+format(args.wd6_regularization,".17g")+"\n"
if liquid_phi == 0.:
    text = "\n".join(line for line in text.splitlines() if not line.startswith("particles."))+"\n"
rows = []
if liquid_phi > 0.:
    for j in range(args.ny):
        for i in range(args.nx):
            x, y = (i+.5)*dx, (j+.5)*dy
            if x <= args.front_cm+abs(args.perturbation_cm):
                continue
            row = [x, y, 0., 0., 300., diameter, 1., weight, weight, 0., 0., 0.]
            rows.append(" ".join(format(v, ".17g") for v in row))
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
shutil.copyfile(reference / "profile_SI.txt", out / "profile_SI.txt")
if rows:
    (out / "droplets.dat").write_text(str(len(rows))+"\n"+"\n".join(rows)+"\n")
(out / "inputs").write_text(text)
command = ["mpirun", "-np", str(args.ranks), str(binary), "inputs"]
env = os.environ.copy()
env["OMP_NUM_THREADS"] = "1"
if args.gpu:
    if args.cuda_home:
        env["LD_LIBRARY_PATH"] = str(args.cuda_home.resolve()/"lib64")+":"+env.get("LD_LIBRARY_PATH", "")
    binding = out/"bind_rank.sh"
    binding.write_text("#!/bin/bash\ndevices=("+" ".join(devices)+")\n"
                       "export CUDA_VISIBLE_DEVICES=${devices[$OMPI_COMM_WORLD_LOCAL_RANK]}\nexec \"$@\"\n")
    command = ["mpirun", "-np", str(args.ranks), "bash", str(binding), str(binary), "inputs"]
manifest = {"command": command, "binary": str(binary),
            "mechanism": mechanism_name, "species_names": gas.species_names,
            "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest() if binary.is_file() else None,
            "profile_sha256": hashlib.sha256((out/"profile_SI.txt").read_bytes()).hexdigest(),
            "input_sha256": hashlib.sha256((out/"inputs").read_bytes()).hexdigest(),
            "gas_phi": gas_phi, "liquid_phi": liquid_phi,
            "diameter_um": args.diameter_um, "effective_depth_cm": dx,
            "liquid_mass_density_g_cm3": rho_liquid_per_volume,
            "parcel_count": len(rows), "real_droplets_per_parcel": weight,
            "transverse_boundary": "slip walls" if args.walls else "periodic",
            "chemistry_transport_split": "strang", "reference": str(reference),
            "linear_solver": args.linear_solver if args.gpu else "dense_direct"}
manifest["wd6_concentration_epsilon_mol_m3"] = args.wd6_regularization if mechanism_name == "heptane_wd6" else None
manifest["output_interval_s"]=args.output_interval
manifest["chemistry_tile_size"]=args.chemistry_tile_size
manifest["cell_chemistry_integrator"]=args.cell_chemistry_integrator
manifest["cell_chemistry_rtol"]=args.cell_chemistry_rtol
manifest["cell_chemistry_atol_y"]=args.cell_chemistry_atol_y
manifest["history_output_interval_s"]=args.history_interval if args.wave_history else None
(out/"case.json").write_text(json.dumps(manifest, indent=2))
if args.run:
    process = subprocess.Popen(["bash", "-c", shlex.join(command)+"; rc=$?; echo $rc > exit_code; exit $rc"],
                               cwd=out, env=env, stdout=(out/"run.log").open("w"),
                               stderr=subprocess.STDOUT, start_new_session=True)
    print(json.dumps({"case": str(out), "pid": process.pid}))
else:
    print(json.dumps({"case": str(out), "command": command, "launched": False}))
