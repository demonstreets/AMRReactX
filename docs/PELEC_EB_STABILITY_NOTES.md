# PeleC EB Stability Notes

## Cylinder tank side-leak NaN risk

When developing or testing PeleC with embedded boundaries (EB), pay special
attention to side-leak cases where a hydrogen plume edge contacts EB cut cells.

Observed failure pattern from a parallel Hermes/DeepSeek agent investigation:

- EB cut cells with `0 < vfrac < 1`, especially small `vfrac`, are present.
- The H2 cloud edge reaches the EB boundary.
- Runs can diverge to NaN under both MOL/RK and Godunov integration.
- Local refinement near the leak hole may delay the failure but does not
  guarantee stability once the plume grows onto coarser EB regions.

Likely mechanism:

- Small EB cells amplify finite-volume updates through the effective
  `1 / vfrac` volume factor.
- Species diffusion, heat conduction, viscous terms, and source injection can
  become locally too stiff for the global explicit timestep.
- If the leak source is deposited into only one or two small cut cells, the
  source term can be over-concentrated. However, follow-up testing showed that
  even better-resolved leak diameters can still diverge, so under-resolution of
  the hole is not the sole cause.
- EB ghost-state or boundary-gradient treatment can create excessive species
  gradients if the solid-side state is not handled consistently with the
  intended wall/no-flux condition.

This should not be treated as proof that EB is inherently unusable. Treat it as
a small-cell/source/gradient stabilization problem.

## Development checks before enabling EB production cases

- Track minimum `vfrac` near the leak and plume edge.
- Log max/min `Y_H2`, `rhoY_H2`, density, pressure, temperature, diffusion RHS,
  source RHS, and their locations before NaN.
- Verify source normalization against physical fluid volume or leak area; avoid
  depositing a total leak rate directly into tiny cut-cell volume.
- Test the pieces separately:
  - EB geometry with no leak.
  - Passive H2 cloud near EB with diffusion off.
  - Passive H2 cloud near EB with diffusion on.
  - Leak source away from EB.
  - Leak source on/near EB.
- Require enough grid resolution across the effective leak diameter as a basic
  modeling check, but do not treat this as a complete fix; tests indicate that
  resolved holes can still NaN when the plume edge interacts with EB cut cells.
- Consider conservative/state redistribution, small-cell merging, minimum
  effective `vfrac`, local timestep restriction, or EB-neighborhood limiters.
- Confirm wall species boundary conditions are no-flux where appropriate.

## Current fallback direction

The porosity plus resistance-source approach is a valid engineering workaround
for near-term tank-obstacle simulations:

- Keep all cells at full volume (`vfrac = 1`).
- Represent solid blockage with a porosity field.
- Damp velocity smoothly in solid/transition regions.
- Use a transition thickness of at least a few grid cells.

When using this fallback, also prevent nonphysical scalar storage or diffusion
through the nominal solid region.

The AMRReactX Stage 4 implementation and verification matrix are documented in
`docs/STAGE4_POROSITY_FALLBACK.md`.
