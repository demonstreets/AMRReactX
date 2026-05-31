# AMRReactX

AMRReactX is the working name for a research-oriented AMReX-based compressible
flow and reacting-flow solver.

The current version is Stage 1 of the solver: a fixed-wind scalar
advection-diffusion leakage model with an explicit finite-volume update and a
selectable leakage source. It includes stability checks, mass-balance and
engineering diagnostics, explicit scalar boundary-condition types, automatic
timestep control, and a Stage 1/2 verification suite. It writes AMReX plotfiles
with:

- `rho`: density
- `u`, `v`, `w`: velocity components
- `Y_leak`: leaked-gas mass-fraction-like scalar
- `C_leak_diag`: concentration in the selected diagnostic basis

This first program verifies the development chain and starts the leakage
transport physics:

- WSL Ubuntu 24.04
- CMake
- OpenMPI
- AMReX
- AMReX plotfile output

## Build

```bash
cmake -S . -B build \
  -DCMAKE_PREFIX_PATH=/home/demonstreets/amrex-install \
  -DCMAKE_BUILD_TYPE=Release

cmake --build build -j $(nproc)
```

## Run

```bash
mpirun -np 2 ./build/amrreactx inputs/leak_3d_open.in
```

The output directories are named from `plotfile_prefix`, for example
`plt_leak_00000`, `plt_leak_00030`, and so on.

Verification cases:

```bash
mpirun -np 2 ./build/amrreactx inputs/verify_advection_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_diffusion_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_wall_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_box_source_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_source_total_rate_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_auto_dt_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_volume_fraction_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_boundary_faces_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_inlet_scalar_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_open_backflow_3d.in
```

Run the Stage 1 verification suite:

```bash
bash tools/run_stage1_verification.sh
```

Useful Stage 1 input parameters:

- `wind`: prescribed velocity vector.
- `diffusion`: scalar diffusivity.
- `source_type = gaussian`: Gaussian leakage source using `source_center`,
  `source_sigma`, and `source_strength`.
- `source_type = box`: uniform box source using `source_box_lo`,
  `source_box_hi`, and `source_strength`.
- `source_total_rate`: optional engineering total scalar mass release rate. If
  set to a non-negative value, it overrides `source_strength` by normalizing the
  selected `gaussian` or `box` source to the requested total rate.
- `init_type = 0`: start from zero scalar field.
- `init_type = 1`: start from a Gaussian scalar cloud using `init_center`,
  `init_sigma`, and `init_amplitude`.
- `bc_lo`, `bc_hi`: scalar boundary types for x/y/z low and high faces.
  Supported values are `inlet`, `outlet`, `wall`, and `open`.
- `inlet_y`: scalar value imposed at `inlet` boundary inflow.
- `ambient_y`: scalar value used when `open` or `outlet` boundaries advect
  back into the domain.
- `cloud_threshold`: threshold used to report cloud volume.
- `lel`, `uel`: lower/upper threshold pair used to report flammable cloud
  volume.
- `diagnostic_basis = mass_fraction`: evaluate `cloud_threshold`, `lel`, and
  `uel` directly from `Y_leak`.
- `diagnostic_basis = volume_fraction`: convert `Y_leak` to gas volume fraction
  using `leak_molecular_weight` and `air_molecular_weight` before applying
  `cloud_threshold`, `lel`, and `uel`.
- `history_file`: CSV time-history output path.
- `dt`, `max_step`, `plot_int`: explicit time stepping controls.
- `use_auto_dt = 1`: choose `dt` from `cfl`, `diff_cfl`, wind, diffusion,
  and grid spacing.
- `stop_time`: optional physical end time; negative values disable it.

Boundary-condition meaning:

- `inlet`: Dirichlet scalar value using `inlet_y`.
- `outlet`: zero-gradient scalar boundary for diffusion/outflow; advective
  backflow uses `ambient_y`.
- `open`: zero-gradient scalar boundary for diffusion/outflow, usable for
  side/top far-field faces; advective backflow uses `ambient_y`.
- `wall`: zero-gradient scalar diffusion with zero normal advective scalar flux.

Runtime diagnostics:

- `adv_cfl_sum`, `max_dir_cfl`: explicit upwind advection stability indicators.
- `diffusion_number`: explicit centered-diffusion stability indicator.
- `mass`, `injected`, `boundary_inflow`, `outlet`, `balance_error`: scalar
  mass budget.
- `inflow_xlo_rate`, `inflow_xhi_rate`, `inflow_ylo_rate`,
  `inflow_yhi_rate`, `inflow_zlo_rate`, `inflow_zhi_rate`: per-face scalar
  boundary-inflow rates whose sum equals `boundary_inflow_rate`.
- `outlet_xlo_rate`, `outlet_xhi_rate`, `outlet_ylo_rate`,
  `outlet_yhi_rate`, `outlet_zlo_rate`, `outlet_zhi_rate`: per-face scalar
  outlet rates whose sum equals `outlet_rate`.
- `max_Y`, `max_Y_location`: maximum scalar value and one deterministic cell
  center where it occurs.
- `max_concentration`: maximum `C_leak_diag` in either mass-fraction or
  volume-fraction basis.
- `centroid`: scalar-cloud center of mass, useful for advection verification.
- `cloud_volume`: volume where `C_leak_diag >= cloud_threshold`.
- `flammable_volume`: volume where `lel <= C_leak_diag <= uel`.
- `cloud_mass`, `flammable_mass`: leaked scalar mass inside the threshold
  cloud and the flammable band.
- `cloud_mean_concentration`, `flammable_mean_concentration`: volume-averaged
  diagnostic concentration inside those regions.
- `cloud_*_min/max`, `flammable_*_min/max`: axis-aligned bounds of the
  threshold cloud and flammable cloud, reported from cell-center locations.

## Current Source Layout

- `src/main.cpp`: program orchestration.
- `src/Core`: runtime parameters, state indices, and AMReX geometry/input setup.
- `src/AMR`: scalar boundary-condition definitions and face flux helpers.
- `src/Numerics`: scalar initialization, explicit advection-diffusion update, and
  stability metrics.
- `src/IO`: plotfile output and runtime diagnostics.
- `tools`: verification runner and CSV history checker.
