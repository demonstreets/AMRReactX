# Resolved compressible gas–liquid interfaces

This executable advances phase masses, gas species masses, momentum, total
energy, and liquid volume fraction on native AMReX MultiFabs. It is the entry
point for resolved-interface verification. The PeleC dilute-spray example in
`../spray_detonation` uses a different liquid representation.

## Physical and numerical model

The phases share pressure and velocity. Gas and liquid temperatures are
recovered separately; thermal equilibrium is not imposed. Gas mass fractions
are normalized by **gas mass**, not total mixture mass. The gas EOS is either
PelePhysics Fuego or a constant-gamma reference EOS. The caloric stiffened-gas
liquid EOS includes its reference-energy offset in the mixture energy solve.
The pressure solve enforces total internal energy and strict pure-phase limits.
The wave speed is the Wood mixture sound speed. The liquid volume-fraction
equation includes the mechanical-equilibrium compressibility term.

Each step performs an acoustic pressure/velocity update and geometric remap.
PLIC swept volumes are shared by phase masses, gas species, momentum and
energy. The two-dimensional reconstruction fits a plane to a 3-by-3 stencil;
three-dimensional geometry uses a Youngs normal. Internal face exchanges are
conservative. Invalid trial states cause time-step rejection. The algorithm
does not repair a completed state by clipping its phase masses or fraction.
The face solver is an acoustic relaxation solver; it is not HLLC.

The supported physical scope is inviscid compressible flow on uniform Cartesian
meshes (`amr.max_level = 0`). Chemistry, phase change, surface tension, viscosity,
gravity, AMR refinement and embedded CAD geometry are not implemented in this
driver. The stiffened-gas reference cases specify mathematical EOS parameters;
they do not constitute a fitted liquid-property model over a wide temperature
range. Do not combine a resolved liquid volume fraction with particles for the
same liquid mass.

## Build and run

Run from the repository root, with CMake, an MPI C++ compiler and the bundled
AMReX/PelePhysics source trees available:

```sh
cmake -S examples/academic/resolved_twophase -B build/resolved_cpu \
  -DCMAKE_BUILD_TYPE=Release -DAMReX_SPACEDIM=2 -DAMReX_GPU_BACKEND=NONE
cmake --build build/resolved_cpu -j 4
ctest --test-dir build/resolved_cpu --output-on-failure
mkdir -p runs/resolved_translation
cd runs/resolved_translation
mpirun -np 2 ../../build/resolved_cpu/resolved_twophase \
  ../../examples/academic/resolved_twophase/inputs.translation
echo $? > exit_code
```

Use a distinct output directory for every run. For CUDA, configure a separate
build with `-DAMReX_GPU_BACKEND=CUDA` and the architecture of the actual device.
Bind MPI ranks to distinct devices when using multiple GPUs; explicitly setting
`amrex.the_arena_init_size=67108864` avoids multiple small verification jobs
reserving most device memory.

The included inputs cover a full-period translating circle, a small-amplitude
mixture acoustic wave, a material shock tube, and a dimensional Fuego/stiffened-
gas translating contact. Plotfiles contain conservative and primitive fields.
Checkpoints store the state and configuration metadata for consistency checks.

Validate a completed translation from the repository root:

```sh
python3 tools/validate_resolved_two_phase.py runs/resolved_translation \
  --mode translation --output runs/resolved_translation/validation.json
```

For `inputs.fuego_contact`, add `--period 2e-5`. For the material shock tube,
use `--mode water_air_shock`. Its reference is an independent exact two-EOS
Riemann solution. A resolution sequence is required to assess convergence.
Use `--mode acoustic_mixture` for the small-amplitude gamma-law mixture wave;
the reference Wood speed is computed from the configured phase bulk moduli,
and the Fourier phase/amplitude are measured directly from initial/final fields.
The validator reads `RUN/inputs` (or `--inputs FILE`), command-line overrides
recorded in `command.json`, and `exit_code`. Default validation requires a
successful exit and the configured `tp.stop_time`. A wrong return period or
failed translation budget produces a nonzero status. `--partial` explicitly
permits field inspection without claiming that the requested interval completed.
Successful process exit alone is insufficient, and raw admissibility does not
constitute a universal shock/acoustic convergence test.

## Verification evidence, 2026-09-10

Evidence is stored in `repair_validation/twophase_20260910`. The final interface
implementation is identified by the `v4` run suffix. Results include:

* Full-period circle translation on 32, 64 and 128 cells per direction:
  volume-fraction L1 errors 0.00404387, 0.00109507 and 0.000377538. Observed
  refinement orders are 1.88 and 1.54. Phase-mass and energy relative errors
  are below 6.8e-14; constant-pressure relative error is below 2.4e-11.
* Single- versus two-rank CPU fields and checkpoint/restart versus uninterrupted
  fields agree exactly in the stored final plotfiles. One- and two-GPU fields
  agree exactly with each other. CPU/GPU conservative-field relative maximum
  differences are below 9e-11; derived sound-speed differences are below 8e-10.
* The dimensional Fuego contact completes its full 20 microsecond period with
  phase-mass and energy errors below 1.8e-14 and pressure error below 2e-11.
* Acoustic phase errors at 32, 64 and 128 cells are 0.00982590, 0.00239146 and
  0.000598803 radians. The measured speed converges toward the independently
  calculated Wood speed 0.0737369185 in the nondimensional case.
* At 400, 800, 1600 and 3200 axial cells, material-shock pressure L1 errors,
  normalized by the mean absolute exact pressure, decrease from 0.0105728 to
  0.00676092, 0.00429771 and 0.00265806. Density and velocity errors also
  decrease. The fraction error against point-sampled exact discontinuities is
  not monotonic; it must not be reported as demonstrated fraction convergence.
* The CTest checks 480 Fuego/liquid thermodynamic states, independent polygon
  intersections, three-dimensional plane cuts, swept-volume partitions, and
  two-dimensional planar-stencil reconstruction. It passes in the final CPU
  build.

These results verify the stated interface model and implementations. They do
not establish reactive two-phase detonation, capillary dynamics, or an AMR/CAD
application.
