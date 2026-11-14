# Finite-rate gas–liquid spray detonation verification

This example uses native PeleC gas dynamics, the 88-species/729-reaction
`heptane_lu_88sk` mechanism, CVODE chemistry, and Lagrangian n-heptane droplets.
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

The mechanism's two device molecular-weight arrays use C++ inline variables.
They must be shared across translation units: separate internal-linkage copies
overflowed 64 KB of device constant memory in the full native executable.
The numerical molecular weights and kinetic rates are unchanged.
The CUDA 12.6 linker also requires the included debug-link workaround for this
full executable. It links the same release device objects and does not enable
`nvcc -G` kernel compilation. `CUDA_NVLINK_DEBUG_WORKAROUND=FALSE` disables the
workaround when independently testing a different toolchain.

## Prepare a case

`prepare_case.py` reads the named species and physical state from an independent
reference directory containing `profile_SI.txt` and `metadata.json`. It creates
a new directory, writes the gas and particle inputs, and records hashes and
parcel weighting in `case.json`. The output directory must not already exist.

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

Resolved liquid interfaces use the separate `../resolved_twophase` executable,
which has its own mixed EOS and conservative PLIC advance. Do not count the
same liquid as both a resolved volume fraction and spray particles.
