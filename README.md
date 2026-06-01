# AMRReactX

AMRReactX is the working name for a research-oriented AMReX-based compressible
flow and reacting-flow solver.

The current version has completed Stage 2, the scalar AMR Stage 3 plan, and the
Stage 4 porosity fallback on top of the Stage 1 fixed-wind scalar
advection-diffusion leakage model. It includes
stability checks, mass-balance and engineering diagnostics, explicit scalar
boundary-condition types, automatic timestep control, volume-fraction
diagnostics, source total-rate normalization, open-boundary ambient backflow
handling, scalar AMR tagging indicators, and a Stage 4 static porosity-obstacle
model for full-volume-grid engineering obstacle studies. It writes AMReX
plotfiles with:

- `rho`: density
- `u`, `v`, `w`: velocity components
- `Y_leak`: leaked-gas mass-fraction-like scalar
- `porosity`: Stage 4 static porosity field
- `C_leak_diag`: concentration in the selected diagnostic basis
- `tag_grad_y`, `tag_source`, `tag_refine`: Stage 3.1 AMR tagging indicators
- `tag_porosity`: Stage 4 porosity-interface tagging indicator

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
When AMR tagging is enabled and candidate level-1 boxes are produced, the same
plotfile path is written as a two-level AMReX plotfile with a piecewise-constant
level-1 initialization from level 0. The level-1 state is maintained through the
AMR hierarchy helper, advanced independently with `tag_ref_ratio` substeps per
level-0 step, and can optionally be restricted back onto covered level-0 cells
with `amr_restrict_after_advance = 1`.

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
mpirun -np 2 ./build/amrreactx inputs/verify_tagging_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_level1_advance_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_level1_restriction_update_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_level1_reflux_update_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_level1_diffusive_reflux_update_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_level1_regrid_update_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_level1_regrid_sync_update_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_porosity_obstacle_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_porosity_source_total_rate_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_porosity_cylinder_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_porosity_tagging_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_porosity_level1_advance_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_porosity_level1_restriction_update_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_porosity_level1_reflux_update_3d.in
mpirun -np 2 ./build/amrreactx inputs/verify_porosity_level1_diffusive_reflux_update_3d.in
```

Run the Stage 1/2 verification suite:

```bash
bash tools/run_stage2_verification.sh
```

The old `tools/run_stage1_verification.sh` entry point is kept as a
compatibility wrapper.

Run the Stage 1/2 + completed Stage 3 verification suite:

```bash
bash tools/run_stage3_verification.sh
```

Run the completed Stage 4 porosity-fallback verification suite:

```bash
bash tools/run_stage4_verification.sh
```

Stage 4 is documented in [docs/STAGE4_POROSITY_FALLBACK.md](docs/STAGE4_POROSITY_FALLBACK.md).
It is a full-volume-grid porosity fallback for EB small-cell stability work,
not a complete embedded-boundary implementation.

Verification plotfile directories are deleted after each case passes so routine
development runs do not accumulate large AMReX plot outputs. Verification
history CSV files are also deleted after their checks pass. Set
`CLEAN_PLOTFILES=0` or `CLEAN_HISTORIES=0` when a passing case's generated
outputs should be kept for manual inspection.

Useful Stage 1/2 input parameters:

- `wind`: prescribed velocity vector.
- `diffusion`: scalar diffusivity.
- `source_type = gaussian`: Gaussian leakage source using `source_center`,
  `source_sigma`, and `source_strength`.
- `source_type = box`: uniform box source using `source_box_lo`,
  `source_box_hi`, and `source_strength`.
- `source_total_rate`: optional engineering total scalar mass release rate. If
  set to a non-negative value, it overrides `source_strength` by normalizing the
  selected `gaussian` or `box` source to the requested total rate. When
  `porosity_enabled = 1`, this normalization is performed over the
  porosity-weighted accessible source volume so the requested rate is not
  deposited into the solid core.
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
- `tagging_enabled = 1`: write Stage 3 tagging indicators and tag-volume
  diagnostics.
- `tag_grad_y`: threshold for concentration-gradient tagging based on
  `|grad Y_leak|`.
- `tag_source_region = 1`: tag the current source region for AMR source
  near-field refinement.
- `tag_source_radius`, `tag_source_box_buffer`: optional source-region tagging
  controls for Gaussian and box sources.
- `tag_porosity_interface = 1`: tag Stage 4 porosity interfaces and transition
  cells for candidate AMR refinement.
- `tag_porosity_threshold`: porosity jump/transition threshold used by
  `tag_porosity_interface`.
- `tag_buffer`, `tag_ref_ratio`, `tag_max_grid_size`,
  `tag_grid_efficiency`: controls for buffering tags and clustering candidate
  level-1 AMR boxes.
- `amr_regrid_interval`: optional output-step interval for rebuilding the
  maintained level-1 hierarchy from current level-0 tagging. The default `0`
  keeps the initial level-1 patch fixed once created.
- `amr_restrict_after_advance = 1`: after independent level-1 advance, average
  the level-1 state back onto covered level-0 cells. This restores restriction
  consistency and can be combined with `amr_reflux_after_advance = 1` for the
  adjacent coarse-fine flux correction.
- `amr_reflux_after_advance = 1`: apply scalar coarse-fine reflux corrections
  to level-0 cells adjacent to the refined patch. Advective and diffusive
  mismatch mass is accumulated per coarse-fine face during level-1 subcycling
  and applied to the adjacent level-0 coarse cell.
- `porosity_enabled = 1`: enable the Stage 4 static porosity-obstacle model.
- `porosity_type = box`: use an axis-aligned box obstacle.
- `porosity_box_lo`, `porosity_box_hi`: axis-aligned obstacle box.
- `porosity_type = cylinder`: use a finite cylindrical obstacle, useful for
  near-term tank-like EB fallback studies.
- `porosity_cylinder_center`, `porosity_cylinder_radius`,
  `porosity_cylinder_axis`, `porosity_cylinder_axis_lo`,
  `porosity_cylinder_axis_hi`: finite-cylinder geometry controls.
- `porosity_transition`: smooth transition thickness outside the obstacle box.
- `porosity_solid_value`: porosity inside the obstacle core, typically `0`.
- `porosity_resistance`: velocity damping strength in partially porous cells.
  Scalar advection and diffusion use the face aperture implied by neighboring
  porosity values, and scalar source deposition is suppressed in low-porosity
  cells.
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
- `amr_sync_corrected_balance_error`: mass budget after subtracting the
  cumulative optional AMR restriction-update and reflux mass corrections. This
  should stay near zero when AMR synchronization changes level-0 cells, while the raw
  `balance_error` records the unaccounted AMR synchronization drift.
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
- `porosity_min`, `porosity_mean`, `solid_volume`, `solid_scalar_mass`: Stage 4
  porosity-obstacle diagnostics. `solid_volume` and `solid_scalar_mass`
  diagnose the near-zero-porosity obstacle core.
- `tag_grad_y_volume`, `tag_source_volume`, `tag_porosity_volume`,
  `tag_refine_volume`: Stage 3/4 single-level AMR tagging diagnostics.
- `tag_refine_cell_count`, `tag_cluster_count`,
  `tag_candidate_level1_cell_count`, `tag_candidate_level1_volume`: Stage 3
  candidate level-1 grid diagnostics generated from global tagged bounds.
- `amr_restrict_max_abs_y_error`, `amr_restrict_l1_y_error`,
  `amr_restrict_coarse_cell_count`: consistency diagnostics from restricting
  level-1 `Y_leak` back onto the covered level-0 cells. These are intentionally
  nonzero after independent fine-level advance unless
  `amr_restrict_after_advance` is enabled.
- `amr_level1_mass`, `amr_level1_solid_volume`,
  `amr_level1_solid_scalar_mass`, `amr_covered_level0_mass`,
  `amr_mass_delta`: mass in the maintained level-1 state, fine-level
  near-zero-porosity volume, scalar mass inside those fine-level solid cells,
  mass in the covered level-0 cells, and the level-1/covered-level-0 mass
  difference.
- `amr_level1_*_min/max`: physical lower and upper bounds of the maintained
  level-1 patch, useful for verifying optional regridding.
- `amr_applied_restriction_mass_delta`: mass correction applied to level 0 by
  the optional restriction update on the most recent output step. This exposes
  the average-down synchronization drift separately from the optional reflux
  correction.
- `amr_applied_reflux_mass_delta`: mass correction applied to level 0 by the
  optional coarse-fine reflux update on the most recent output step.
- `amr_cumulative_restriction_mass_delta`,
  `amr_cumulative_reflux_mass_delta`: cumulative AMR synchronization mass
  corrections used by `amr_sync_corrected_balance_error`.
- `amr_cf_advective_flux_mismatch`, `amr_cf_advective_abs_mismatch`,
  `amr_cf_diffusive_flux_mismatch`, `amr_cf_diffusive_abs_mismatch`,
  `amr_cf_interface_face_count`: coarse-fine interface diagnostics comparing
  level-1 integrated scalar flux against the matching level-0 flux, split into
  advective and diffusive contributions.
- `amr_cf_advective_mismatch_mass`,
  `amr_cf_advective_abs_mismatch_mass`,
  `amr_cf_diffusive_mismatch_mass`,
  `amr_cf_diffusive_abs_mismatch_mass`: fine-substep accumulated coarse-fine
  flux mismatch estimates. The signed advective plus diffusive mismatch drives
  the optional per-face reflux correction.
- The same coarse-fine mismatch diagnostics are also written with `_xlo`,
  `_xhi`, `_ylo`, `_yhi`, `_zlo`, and `_zhi` suffixes so reflux work can verify
  which coarse-fine patch side contributes each mismatch.

## Current Source Layout

- `src/main.cpp`: program orchestration.
- `src/Core`: runtime parameters, state indices, and AMReX geometry/input setup.
- `src/AMR`: scalar boundary-condition definitions and face flux helpers.
- `src/AMR/Hierarchy.*`: AMR hierarchy helpers for refined geometry creation,
  coarse-to-fine initialization, level-1 advance, and restriction update.
- `src/AMR/Tagging.*`: Stage 3 scalar-gradient and source-region tagging
  indicators.
- `src/Numerics`: scalar initialization, explicit advection-diffusion update, and
  stability metrics.
- `src/IO`: plotfile output and runtime diagnostics.
- `tools`: verification runner and CSV history checker.
