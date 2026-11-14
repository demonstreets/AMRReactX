# Finite-rate gas–liquid spray detonation verification

This example couples native PeleC gas dynamics and Lagrangian n-heptane droplets.
The default detailed chemistry uses the 88-species/729-reaction
`heptane_lu_88sk` mechanism with CVODE. A separately named six-species
`heptane_wd6` option is used for the two-dimensional cellular benchmarks below;
those are not 88-species cellular calculations.
It initializes a finite-rate ZND profile. Subsequent wave motion comes from
the conservative flow, chemistry and droplet updates. There is no prescribed
moving heat source or front-speed constraint.

The gas starts at 300 K and 0.5 atm, with gas equivalence ratio 0.6. Wet cases
add cold 10-micrometre droplets equivalent to another 0.4 in fuel equivalence
ratio. The reference is initially overdriven by 2% in speed relative to the
independent equilibrium CJ calculation for the **gas** mixture. These are
initial-value numerical benchmarks with extrapolation boundaries in x;
do not identify their measured speed with an unforced CJ eigenvalue without
checking the initial transient and boundary influence.

The archived production inputs and manifests identify the exact run segments,
binary hashes and restart joins used for the reported figures. The following
WD6 commands reproduce their physical/numerical settings from a fresh start;
floating-point partition changes need not preserve the phase of nonlinear
cellular patterns over a long interval.

## Build

Use a consistent SUNDIALS installation for both headers and libraries. This
example's current native interface uses 32-bit SUNDIALS indices. The verification
build used official SUNDIALS 6.7.0 with `SUNDIALS_INDEX_SIZE=32`. Mixing those
headers with an older 64-bit-index library is an ABI error.

From this directory:

```sh
make -j8 USE_MPI=TRUE Chemistry_Model=heptane_lu_88sk \
  SUNDIALS_PREFIX=/absolute/path/to/sundials/install \
  SUNDIALS_HOME=/absolute/path/to/sundials/install EBASE=spray_detonation
```

For CUDA, use a separate `TMP_BUILD_DIR`, add `USE_CUDA=TRUE`, set `CUDA_HOME`
and the actual device's `CUDA_ARCH`, and use a matching CUDA-enabled SUNDIALS
installation. This verification uses `PELE_CVODE_FORCE_YCORDER=TRUE` and
`PELE_COMPILE_AJACOBIAN=TRUE`. CUDA inputs select `cvode.solve_type=sparse_direct`;
CPU inputs select `denseAJ_direct`. Bind each MPI rank to its intended device.

The CUDA build also provides an explicitly selected `custom_direct` path using
cuBLAS batched double-precision LU with partial pivoting. The example defines
`PELE_USE_CUBLAS_BATCHED_LU` and links cuBLAS; other native examples must opt in
with the same definition and library to use this path. Without that build
option, selecting CUDA `custom_direct` aborts. The former CUDA implementation
returned success without solving the system; it must not be used from an older
binary. The replacement checks each factorization for singularity, preserves
the CSR input matrix, and reuses the LU factors between CVODE setup calls.

`test/unit/test_cublas_batched_lu.cu` checks independent known solutions and
residuals, nontrivial pivots, multiple right-hand sides using the same factors,
in-place right-hand sides, and rejection of a singular member of a batch.
Native chemistry and coupled-flow comparisons are additionally required.

The mechanism's two device molecular-weight arrays use C++ inline variables.
They must be shared across translation units: separate internal-linkage copies
overflowed 64 KB of device constant memory in the full native executable.
The numerical molecular weights and kinetic rates are unchanged.
The CUDA 12.6 linker also requires the included debug-link workaround for this
full executable. It links the same release device objects and does not enable
`nvcc -G` kernel compilation. `CUDA_NVLINK_DEBUG_WORKAROUND=FALSE` disables the
workaround when independently testing a different toolchain.

An explicit WD6 CUDA build uses the following flags (set the paths and
architecture to the selected machine; the validation devices used architecture 60):

```sh
make -j4 USE_MPI=TRUE USE_CUDA=TRUE Chemistry_Model=heptane_wd6 \
  WD6_REGULARIZATION=1e-10 WD6_STOICH_SOLVE=TRUE \
  PELE_CVODE_FORCE_YCORDER=TRUE PELE_COMPILE_AJACOBIAN=TRUE \
  CUDA_HOME=/absolute/path/to/cuda CUDA_ARCH=60 \
  SUNDIALS_PREFIX=/absolute/path/to/cuda_sundials/install \
  SUNDIALS_HOME=/absolute/path/to/cuda_sundials/install EBASE=spray_wd6
```

## Prepare a case

First run the uniform closed coupling test, with the reference generated below:

```sh
python3 examples/academic/spray_detonation/prepare_closed_case.py runs/closed_wet \
  --reference runs/reference --binary /absolute/path/to/native_binary --run
python3 tools/validate_closed_spray.py runs/closed_wet \
  --output runs/closed_wet/validation.json
```

Run the validator after the solver exits. Repeat in a new directory with
`--dt 5e-8` to compare against the default `1e-7` seconds. Both runs cover
200 microseconds at gas temperature 1400 K and pressure 1 bar. Use `--dry`
for the gas-only control, `--nonreacting` for evaporation without gas chemistry,
and `--droplet-u-ms 10` for nonzero initial slip. The gas-only reactive validator
accepts `--cantera` for an independent constant-volume reactor calculation.
CUDA preparation accepts `--gpu --device 0 --cuda-home /absolute/cuda/path`;
`--linear-solver custom_direct` explicitly selects the opt-in cuBLAS path.
Without `--run`, preparation writes inputs and a manifest but launches nothing.

The closed validator integrates all gas species and native droplet records,
checks every sampled raw state, and checks combined mass, energy, momentum and
element drift throughout the interval. It returns a nonzero status for invalid
fields, excessive drift, an unsuccessful solver exit, or an incomplete interval.
The documented liquid model uses `h_vapor(300 K) - latent + cp*(T-300 K)`;
changing its thermodynamic reference requires changing the budget consistently.

`prepare_case.py` reads the named species and physical state from an independent
reference directory containing `profile_SI.txt` and `metadata.json`. It creates
a new directory, writes the gas and particle inputs, and records hashes and
parcel weighting in `case.json`. The output directory must not already exist.
Generate that reference with Cantera, NumPy and SciPy installed:

```sh
python3 generate_reference.py /absolute/path/to/new_reference
```

The reference generator independently solves the equilibrium Hugoniot and the
finite-rate ZND equations, checks the energy residual, and records raw BDF
composition errors separately from its admissible exported initial profile.

```sh
python3 prepare_case.py /absolute/path/to/new_case \
  --reference /absolute/path/to/reference_znd_v1 \
  --binary /absolute/path/to/spray_detonation2d.gnu.MPI.ex \
  --nx 400 --ny 80 --length-cm 20 --height-cm 4 \
  --walls --multimode --wave-history --end-time 8e-5 --ranks 8
```

This command prepares the case. Add `--run` to launch it, or run the command
recorded in `case.json` from that case directory. For CUDA, add `--gpu`, provide
one device index per rank through `--devices`, and set `--cuda-home` if its shared
libraries are outside the system loader path. `--dry` creates the gas-only
control with otherwise matching geometry and initialization. All lengths in
this generator are explicitly centimetres except `--diameter-um`.

For the fine WD6 benchmark, prepare the independently generated WD6 reference
and then the 2800 by 800 case:

```sh
python3 generate_reference.py runs/reference_wd6 --mechanism heptane_wd6
python3 prepare_case.py runs/wd6_wet_fine --reference runs/reference_wd6 \
  --binary /absolute/path/to/spray_wd62d.gnu.MPI.CUDA.ex \
  --nx 2800 --ny 800 --length-cm 14 --height-cm 4 --front-cm 4 \
  --perturbation-cm .08 --multimode --walls --end-time 5e-5 --cfl .2 \
  --gpu --ranks 2 --devices 0,1 --cuda-home /absolute/path/to/cuda \
  --max-grid-size 400 400 --linear-solver custom_direct \
  --cell-chemistry-integrator wd6_extrapolated --cell-chemistry-rtol 1e-4 \
  --cell-chemistry-atol-y 1e-13 --wd6-regularization 1e-10 \
  --wave-history --output-interval 2e-6 --history-interval 1e-6
```

This prepares a case without launching it. Add `--run` when executing the
calculation. Use a new output directory with `--dry` for the dry counterpart;
use `--nx 1400 --ny 400` for the coarse mesh. The generator adjusts parcel
weights for the native two-dimensional depth, preserving physical loading.

## State and coupling

Gas density and gas species partial densities contain gas mass only. Droplet
mass is represented by native particles. The transfer of gas mass, momentum
and energy uses the **actual** droplet changes, including complete evaporation.
The liquid caloric energy uses the same gas-fuel reference enthalpy as the
evaporation model. Temperature-dependent latent heat and the pressure-dependent
boiling bound are applied consistently. Formation-energy reference offsets can
make the absolute internal energy negative; this is distinct from a nonpositive
temperature or pressure, which is invalid.

The two-dimensional spray model uses an effective depth equal to the cell width.
The case generator keeps volume loading fixed when refining the grid by changing
parcel weights accordingly. Integrated masses from different resolutions must
therefore be compared per unit depth. These calculations are not three-dimensional
spray geometry reconstructions.

`pelec.chemistry_transport_split=strang` selects pure chemistry for half a step,
the native flow/droplet update for a full step, and pure chemistry for another
half step. The pure chemistry calls have zero external species/energy forcing
and retain conservative gas density, momentum and total energy. This avoids
continuing an extrapolated negative transport source after chemistry consumes
a trace species. It does not clip evolved mass fractions.

The split currently requires an all-regular uniform Cartesian grid,
`amr.max_level=0`, `pelec.do_mol=0`, `pelec.do_rf=0`, and `pelec.sdc_iters=1`.
The default native SDC path remains separately selectable as `sdc`. CVODE return
checks and raw-state admissibility guards apply to the relevant update paths.
In the Strang path, `heatRelease` and species reaction diagnostics are
instantaneous rates at the final state; the native SDC diagnostic is a
time-averaged source. Account for this distinction when comparing diagnostics.

For the six-species `heptane_wd6` mechanism, an optional cell-local chemistry
integrator is available through `--cell-chemistry-integrator wd6_extrapolated`.
It requires a positive, explicitly recorded `--wd6-regularization`. The default
remains CVODE. This option does not implement the 88-species mechanism.

The local solver advances six molar concentrations at constant internal energy.
It projects the generated concentration/temperature Jacobian onto that energy
constraint and uses pivoted 6-by-6 linear solves. One full linearly implicit
Euler step and two half steps estimate error; an admissible Richardson
extrapolation provides second-order accuracy. When extrapolation is inadmissible,
the accepted two-half-step state is retained. Failed trial steps are reduced,
without clipping or normalizing evolved species. Temperature is recovered from
the thermodynamic energy equation. Failure to find an admissible state aborts
the update. The existing raw mass and conservation checks remain active.

The optional build flag `WD6_STOICH_SOLVE=TRUE` reduces that linear algebra
to the two independent reaction-progress directions. For a stoichiometric
matrix `S` and progress rates `q`, `rates=S*q` and the energy-constrained
Jacobian is `J=S*dq/dc`. The same increment follows from
`delta=S*(I-h*dq/dc*S)^(-1)*h*q`, using a pivoted 2-by-2 solve. Reaction rates,
thermodynamics, error control, extrapolation and admissibility checks are
unchanged. Floating-point differences can change adaptive substep choices;
bitwise trajectory identity is not claimed. The default build flag is `FALSE`,
and the default build-cache path separates the two variants. When explicitly
reusing an object cache across this flag, force the header dependency with
`make -W /absolute/path/to/src/academic/chemistry/Wd6Rosenbrock.H`.

The reduced solve has been checked against the full solve over twelve initial
states and two tolerances, in native 200 microsecond dry/wet closed reactors,
and in a 20-step evolved two-dimensional spray restart. The latter preserved
every restart droplet and reduced median step time from 1.50 to 0.69 seconds
in the measured shared-GPU test; timing depends on hardware and concurrent
work. Its maximum final temperature difference was 0.00068 K. The production
continuations record the selected linear algebra and binary hash explicitly.

`--cell-chemistry-rtol` (default `1e-6`) and
`--cell-chemistry-atol-y` (default `1e-13`) control the local error estimate and
are recorded in `case.json`. Time-step, tolerance and spatial refinement must
still be assessed for each propagation benchmark. A closed-reactor comparison
alone does not validate cellular detonation. `pelec.profile_strang=1` reports
synchronized chemistry and transport timings for performance diagnosis;
`--chemistry-tile-size NX NY` subdivides CVODE batches without changing the
hydrodynamic mesh and has no effect on the cell-local solver.
The same cell-integrator and tolerance options are accepted by
`prepare_closed_case.py` for the preceding conservation/chemistry validation.
Both generators accept `--ode-rtol` and `--ode-atol` for CVODE, retaining
defaults of `1e-8` and `1e-18`; these are separate from the WD6 cell-integrator
tolerances. `prepare_case.py --max-steps` sets the computational guard, with a
default of 100000. Reaching that guard does not count as reaching the requested
physical end time. Each selected value is recorded in the case manifest.

## Evidence and interpretation

The verification sequence is:

1. Closed inert and reactive gas/droplet mass, elemental, momentum and energy
   budgets, with a time-step refinement and an independent Cantera gas reactor.
2. One-dimensional dry and wet propagation, including raw-state checks and
   time-step/grid comparisons.
3. Two-dimensional transverse-wave evolution, numerical soot foils and
   reaction/evaporation diagnostics, followed by a resolution comparison.

`prob.record_wave_history=1` accumulates maximum pressure and positive heat
release at **every completed step**. `prob.wave_history_interval` controls
writing `sootfoilNNNNN` plotfiles, not the sampling interval. A restarted
history explicitly begins at the restart time; it does not silently include
earlier maxima. Regular plotfiles retain the instantaneous fields.

Wave speed is measured from a documented leading-shock pressure crossing and
a position–time fit after an initial transient. Heat-release separation is
measured relative to that front. A soot-foil pattern alone does not establish
a steady cellular wavelength: the observation window, transverse boundary,
seed, sampling and grid comparison must also be reported. Published numerical
cell ranges are numerical reference data, not experiments.

After all four production cases complete, analyze each with
`tools/analyze_spray_detonation.py RUN OUTPUT`, then pass those output directories
to `tools/compare_spray_detonation.py` with `--dry-coarse`, `--dry-fine`,
`--wet-coarse`, `--wet-fine` and `--output`. The comparison requires successful,
complete and admissible inputs, checks matching physical parameters, and uses
a common time window. It reports observed sensitivities without inventing a
universal cell-convergence acceptance threshold.
Its pressure-track figure and repeat-distance calculations use the intersection
of the four spatial windows with complete recorded front passage. The common
colour scale and spatial crop avoid comparing different recorder histories as
if they represented a mesh effect. Cell-centre endpoints and recorder times
remain explicitly recorded for both resolutions.

For a wet case continued from another run directory, the analyzer accepts
`--previous-run PREVIOUS`. It independently compares the saved gas state and
every identified droplet at the join, then includes previous plots strictly
before that time. The output retains each segment's actual exit status and
each plot's source directory. `tools/validate_spray_restart.py SOURCE_PLOT
RESTART_PLOT --output RESULT.json` can also check the join independently.
On restart, native checkpoint particles take precedence over `init_file`, and
particle redistribution uses global exchange when the grid decomposition
changes. Numerical soot foils begin anew at restart; the trajectory analyzer
does not merge the earlier pressure maxima. It limits pressure-trace statistics
to the region beyond the restart shock plus a 5 mm margin. Multiple preceding
segments can be supplied by repeating `--previous-run` in chronological order;
each join is independently checked.

Use `tools/analyze_wd6_reaction_sequence.py RUN PLOT OUTPUT` to reconstruct
cellwise reaction powers and produce locally shock-aligned profiles. The
[external comparison notes](REFERENCE_COMPARISON.md) identify the primary
paper, the applicable gas-only reference values, differences in development
length and liquid modeling, and limits on interpreting spatial reaction peaks.

The separate `tools/validate_wd6_temporal_sequence.py PROBE OUTPUT` compares
`test/unit/probe_wd6_rosenbrock.cpp` with an independent Cantera constant-volume
history at 1400 K, 1.4 MPa and gas equivalence ratio 0.6. Compile the probe with
`PELE_WD6_REGULARIZATION=1.e-10`. The comparison records the probe hash,
input state and tolerances. It plots fuel, CO, CO2 and temperature, and reports
fuel half-consumption, CO maximum and CO2 half-formation times. These describe
overlapping reactions in a homogeneous gas reactor; they are not detonation
residence times or a determination of the original phase of fuel molecules.

`tools/compare_dry_propagation_sensitivity.py BASELINE_ANALYSIS CANDIDATE_ANALYSIS
OUTPUT` compares completed dry runs with the same physical initialization,
geometry, grid and final time. It records the numerical settings, late-time
front fits and absolute/normalized differences in final conservative and
primitive fields, with a one-dimensional profile figure. A small wave-speed
difference does not imply small pointwise errors at steep reaction fronts;
retain the field metrics when reporting time-step or chemistry tolerances.

`tools/compare_planar_spray.py DRY_ANALYSIS WET_ANALYSIS OUTPUT` compares complete
planar dry/wet histories and shock-aligned final pressure, temperature and
heat-release profiles. It checks upstream settings, grid and final time, and
reports actual differences between independently generated reference tables.
Output-to-output speeds use the saved-time intervals; a short interval near a
restart can magnify finite-grid front-location variations. Assess the later
trend and reaction separation as well as the mean speed.

For nonreacting closed cases, the generator omits inapplicable ODE and CVODE
options while preserving strict unused-input checking. The corresponding
chemistry settings are null in the manifest. A completed 200 microsecond
10 m/s initial-slip evaporation test, repeated at half the time step, checks
the combined phase momentum in addition to mass, energy and elements.

Resolved liquid interfaces use the separate `../resolved_twophase` executable,
which has its own mixed EOS and conservative PLIC advance. Do not count the
same liquid as both a resolved volume fraction and spray particles.
