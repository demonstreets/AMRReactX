# Stage 4 Porosity Fallback

Stage 4 implements a full-volume-grid porosity fallback for near-term
obstacle/tank-like scalar transport studies. It is intended as a practical
route around EB plus MOL small-cell NaN failures while EB stabilization remains
under investigation.

This stage is complete as a porosity fallback. It is not a complete embedded
boundary implementation.

## Scope

Implemented:

- Static porosity obstacles on the regular AMReX grid.
- Axis-aligned box and finite-cylinder obstacle geometry.
- Velocity damping in low-porosity and transition cells through
  `porosity_resistance`.
- Scalar advection and diffusion face apertures based on neighboring porosity.
- Source deposition suppressed by local porosity.
- `source_total_rate` normalization over porosity-weighted accessible source
  volume.
- Porosity-interface AMR tagging through `tag_porosity`.
- Maintained level-1 AMR advance with porosity-tagged patches.
- Optional average-down restriction after level-1 advance.
- Optional advective and diffusive coarse-fine reflux corrections.
- Level-0 and level-1 solid-region diagnostics.

Out of scope:

- AMReX EB volume fractions or cut-cell geometry.
- EB wall ghost states, EB no-flux boundary gradients, or small-cell
  redistribution.
- General CAD or STL geometry import.
- Momentum or pressure solve through porous media.
- Turbulence, buoyancy, combustion, or thermal coupling.

## Key Parameters

- `porosity_enabled = 1`: enable the Stage 4 fallback.
- `porosity_type = box`: use `porosity_box_lo` and `porosity_box_hi`.
- `porosity_type = cylinder`: use `porosity_cylinder_center`,
  `porosity_cylinder_radius`, `porosity_cylinder_axis`,
  `porosity_cylinder_axis_lo`, and `porosity_cylinder_axis_hi`.
- `porosity_transition`: smooth transition thickness outside the solid core.
- `porosity_solid_value`: solid-core porosity, normally `0`.
- `porosity_resistance`: damping strength used by local velocity factors.
- `tag_porosity_interface = 1`: tag porosity jumps and transition cells for
  candidate level-1 refinement.
- `tag_porosity_threshold`: threshold for porosity interface tagging.
- `amr_restrict_after_advance = 1`: average maintained level-1 state back to
  covered level-0 cells.
- `amr_reflux_after_advance = 1`: apply coarse-fine scalar flux mismatch
  corrections to adjacent level-0 cells.

Recommended fallback settings for tank-like studies:

- Keep `porosity_solid_value = 0` for an impermeable obstacle core.
- Use a `porosity_transition` at least a few grid cells thick when possible.
- Enable `tag_porosity_interface = 1` when the obstacle boundary should be
  refined.
- Use `amr_restrict_after_advance = 1` when level-0 output/state consistency is
  more important than exposing raw coarse-fine divergence.
- Add `amr_reflux_after_advance = 1` when coarse-fine flux mismatch accounting
  is needed.
- Keep `solid_scalar_mass` and `amr_level1_solid_scalar_mass` at zero in
  engineering obstacle cases.

## Diagnostics

Stage 4 adds or relies on these history fields:

- `porosity_min`, `porosity_mean`: global porosity summary.
- `solid_volume`: level-0 near-zero-porosity volume.
- `solid_scalar_mass`: scalar mass stored in level-0 near-zero-porosity cells.
- `tag_porosity_volume`: volume selected by porosity-interface tags.
- `amr_level1_solid_volume`: maintained level-1 near-zero-porosity volume.
- `amr_level1_solid_scalar_mass`: scalar mass stored in level-1
  near-zero-porosity cells.
- `amr_cf_advective_*`, `amr_cf_diffusive_*`: coarse-fine mismatch diagnostics
  used to verify optional reflux corrections.
- `amr_sync_corrected_balance_error`: scalar mass balance after subtracting
  optional AMR restriction and reflux corrections.

## Verification Matrix

Run the full suite with:

```bash
bash tools/run_stage4_verification.sh
```

The runner builds `build-stage4`, executes all Stage 4 cases, validates each
history CSV with `tools/check_history.py`, and removes passing plotfiles and
histories by default.

| Case | Purpose | Key checks |
| --- | --- | --- |
| `verify_porosity_obstacle_3d.in` | Box obstacle passive transport | Mass conservation, nonzero solid volume, zero solid scalar mass, slowed centroid, single-level plotfile |
| `verify_porosity_source_total_rate_3d.in` | Source total-rate normalization with a solid core | Requested source rate, final mass/injected mass, zero solid scalar mass |
| `verify_porosity_cylinder_3d.in` | Finite-cylinder obstacle geometry | Mass conservation, cylinder solid volume, zero solid scalar mass, slowed centroid |
| `verify_porosity_tagging_3d.in` | Porosity-interface AMR tagging without time advance | Positive `tag_porosity_volume`, no grad/source tags, candidate level-1 boxes, multilevel plotfile |
| `verify_porosity_level1_advance_3d.in` | Porosity-tagged maintained level-1 advance | Level-1 coverage, coarse-fine faces, positive level-1 solid volume, zero fine solid scalar mass |
| `verify_porosity_level1_restriction_update_3d.in` | Porosity level-1 advance plus average-down restriction | Restriction error returns to zero, AMR mass delta removed, sync-corrected balance closes |
| `verify_porosity_level1_reflux_update_3d.in` | Porosity level-1 advance plus advective reflux | Applied reflux matches signed face mismatch, corrected balance closes, solid regions stay scalar-free |
| `verify_porosity_level1_diffusive_reflux_update_3d.in` | Porosity level-1 advance plus diffusive reflux | Advective mismatch stays zero, diffusive mismatch is positive, applied correction matches signed face mismatch |

Stage 3 regression should also pass after Stage 4 changes:

```bash
bash tools/run_stage3_verification.sh
```

## Completion Criteria

Stage 4 is considered complete when:

- All Stage 4 verification cases pass.
- Stage 3 regression still passes.
- `git diff --check` reports no whitespace errors.
- No `Backtrace.*` files remain after test runs.
- README links to this Stage 4 scope document.
- `docs/PELEC_EB_STABILITY_NOTES.md` records why this fallback exists.

These criteria were satisfied at Stage 4 closeout.

## Known Limitations

- This fallback does not model true cut-cell geometry or exact wall surface
  area.
- Flux blocking is based on cell-centered porosity and face aperture, not EB
  face fractions.
- The velocity field is prescribed and damped locally; it is not a solved
  porous-flow momentum field.
- The cylinder model is finite and axis-aligned to one coordinate direction.
- AMR support is limited to the maintained level-1 helper already present in
  this research code path.
- Verification cases are compact regression tests, not production-resolution
  tank simulations.

## Next Stage Entry Points

Good follow-up work after Stage 4:

- Add production-like tank input templates using the porosity fallback.
- Compare porosity fallback outputs against selected EB or analytic reference
  cases where EB remains stable.
- Add optional geometry composition if multiple obstacles are needed.
- Revisit EB small-cell stabilization separately from this fallback path.
