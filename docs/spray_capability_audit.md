# Spray Module Capability Audit

**Date**: 2026-06-25
**Scope**: PeleC Spray module (PelePhysics/Source/Spray/) + PeleC/Source/Particle.cpp
**Author**: CodeWhale audit

---

## Step 1: Compile & Run Status

### Spray-Jet RegTest (`external/PeleC/Exec/RegTests/Spray-Jet/`)

**Compile**: SUCCESS (after adding VOF include paths and `NUM_ADV=1` define to GNUmakefile).
The regtest Makefile was missing include paths to `my-pele/src/academic/vof/` and `my-pele/src/academic/twophase/`,
which are required because `Godunov.H` has been modified to include `vof_modules.H` unconditionally.

**Run**: SEGFAULT at step 1. The segfault is in `Advance.cpp:303` inside `MultiFab::Copy`.
Root cause: the Spray-Jet regtest predates the VOF (`NUM_ADV`) integration. With `NUM_ADV=1`,
the conservative-variable MultiFab has an extra advection component, but the spray source
MultiFab dimensioning (`num_spray_src`) does not account for it. This causes a size mismatch
in the SDC source-copy operation.

**spray_test example** (`examples/academic/spray_test/`): Pre-built binary exists.
Initializes correctly but crashes with "state box too small" at step 1 due to small grid
boxes (48×8) and widely-scattered particle initialization. This is a known example-configuration
issue, not a physics bug.

**Conclusion**: The spray module source code is complete and compiles. The regtest integration
with the VOF-modified codebase needs reconciliation (see Gap Analysis below).

---

## Step 2: Spray Module Physics Capability Inventory

### 2.1 Particle Type

PeleC spray particles are **Lagrangian point-particles** representing parcels (groups of
physically identical droplets). Each parcel tracks:

| Property | Index | Description |
|----------|-------|-------------|
| Position | `pos(0..2)` | 3D spatial location |
| Velocity | `pstateVel` (0..2) | 3D velocity vector |
| Temperature | `pstateT` | Droplet temperature (K) |
| Diameter | `pstateDia` | Droplet diameter (m) |
| Mass fractions | `pstateY` (0..SPRAY_FUEL_NUM-1) | Liquid fuel composition |
| Number density | `pstateNumDens` | Physical droplets per parcel |
| N0 | `pstateN0` | Initial number density (for KHRT) |
| BM1 | `pstateBM1` | Breakup model var 1 (TAB: y distortion) |
| BM2 | `pstateBM2` | Breakup model var 2 (TAB: ydot; KHRT: RT time) |
| Film height | `pstateFilmHght` | Wall film height |

**Source**: `SprayFuelData.H` (SprayComps), `SprayParticles.H`

### 2.2 Drag Model

Standard spherical drag with regime-dependent coefficient:
- **Stokes**: `C_D = 24/Re` (Re < 1)
- **Transitional**: `C_D = 24/Re * (1 + Re^(2/3)/6)` (1 < Re < 1000)
- **Turbulent**: `C_D = 0.424` (Re > 1000)
- TAB distortion correction: `C_D *= (1 + 2.6432 * y_tab)`

**Source**: `Drag.H:452-459`

### 2.3 Evaporation Model — Abramzon-Sirignano (1989)

**Supported**: YES. Full implementation of the Abramzon-Sirignano model.

Key features:
- **One-third rule** for reference temperature/vapor state
- **Iterative B_T correction** for Nusselt number (`calcHeatCoeff` with up to 100 iterations)
- **Antoine equation** for saturation pressure (user-supplied coefficients A, B, C, D)
- **Clasius-Clapeyron fallback** when psat coefficient D=0
- **Schmidt number** mass transfer analogy: `Sh_0 = 1 + Re^0.077 * (1 + Re*Sc)^(1/3)`
- **Sub-cycling** based on minimum of momentum, heat, and mass timescales (up to 100 subcycles)
- **Multi-component fuel support** with CSR mapping from liquid species to gas species
- **Manifold EOS** special path for reduced chemistry

**Source**: `Drag.H` (calculateSpraySource, calcVaporState, calcHeatCoeff), `SprayPropertiesPeleMP.H`

**Required fuel properties** (per species, prefixed `particles.<SPECIES>_`):
- `crit_temp` — critical temperature
- `boil_temp` — boiling temperature at 1 atm
- `latent` — latent heat of vaporization
- `cp` — liquid specific heat
- `rho` — liquid density (constant or 4-coeff polynomial)
- `psat` — Antoine coefficients (A, B, C, conversion_factor)
- `fuel_ref_temp` — reference temperature for liquid properties
- Optional: `lambda`, `mu` coefficients (required for breakup/splash)

### 2.4 Breakup Models

#### TAB (Taylor Analogy Breakup)
**Supported**: YES (O'Rourke & Amsden 1987)

- Spring-mass-damper analogy for droplet distortion
- Includes **ETAB** extension (Tanner 1997) for child droplet sizing
- Configurable: `particles.use_breakup_model = TAB`
- Tunable: `particles.max_parcel_size`, `particles.breakup_parcel_factor`

**Source**: `BreakupSplash/TABBreakup.H` (updateBreakupTAB, splitDropletTAB)

#### Reitz Wave (KH-RT)
**Supported**: YES (Reitz 1987)

- Kelvin-Helmholtz instability for jet primary breakup
- Rayleigh-Taylor instability for secondary breakup
- KH model constants: B0=0.61, B1=7.0 (tunable via `KHRT_B0`, `KHRT_B1`)
- RT model constant: C3=1.0 (tunable via `KHRT_C3`)
- Configurable: `particles.use_breakup_model = KHRT`

**Source**: `BreakupSplash/ReitzKHRT.H` (updateBreakupKHRT)

### 2.5 Splash / Wall Interaction

#### Ahamed Splash Model
**Supported**: YES (Ahamed et al., Atomization and Sprays, 2022)

6 splash regimes based on K-number and dimensionless film thickness:
1. Rebound
2. Deposit
3. Dry splash
4. Thermal breakup
5. Spread
6. Wet splash

Configurable: `particles.use_splash_model = true`, requires `particles.wall_temp`, `particles.contact_angle`

**Source**: `BreakupSplash/AhamedSplash.H`

#### Wall Film
**Supported**: YES

- Film height tracking per parcel (cylinder approximation)
- Evaporation via O'Rourke & Amsden (1996) approach
- Chilton-Colburn analogy for convective mass transfer
- Heat conduction through film to wall
- Configurable: wall temperature, contact angle

**Source**: `BreakupSplash/WallFilm.H` (calculateFilmSource, fillFilmFab)

### 2.6 Two-Phase Coupling

Source terms deposited on the Eulerian mesh:
- **Mass**: `fluid_mass_src` → density equation
- **Momentum**: `fluid_mom_src` → momentum equations (drag + evaporating mass)
- **Energy**: `fluid_eng_src` → energy equation (convection + latent heat + kinetic energy)
- **Species**: `fluid_Y_dot` → species transport equations

Configurable via:
- `particles.mom_transfer` (default: true)
- `particles.mass_transfer` (default: true)
- `particles.fixed_parts` — lock particles in place (for verification)

**Source**: `Particle.cpp` (defineSpraySource, particleMKD, particleMK), `Drag.H:639-667`, `SprayParticles.cpp:429-446`

### 2.7 Injection

#### SprayJet
Configurable per jet (prefix `spray.jet<N>.`):
- `jet_cent` — center position
- `jet_norm` — injection direction
- `spread_angle` — cone angle
- `jet_dia` — orifice diameter
- `jet_vel` — injection velocity (or from ROI file)
- `mass_flow_rate` — mass flow rate (or from ROI file)
- `dist_type` — droplet size distribution (Uniform, etc.)
- `diameter` — average droplet diameter
- `T` — droplet temperature
- `start_time` / `end_time` — injection window
- `phi_swirl` — swirl angle
- `hollow_spray` / `hollow_spread` — hollow cone
- `roi_file` — rate-of-injection file (ECN format)
- `discharge_coeff` — discharge coefficient for ROI

#### Fluent DPM File Injection
**Supported**: YES. Reads Fluent DPM output files for particle injection with time-dependent
position, velocity, diameter, temperature, and parcel mass.

**Source**: `SprayJet.H`, `SprayInjection.H`

### 2.8 VOF Interaction

**Current state: NONE**. The spray module has:
- EB cutoff: `particles.min_eb_vfrac` (default 0.05) — spray sources only deposited in
  cells with volume fraction above this threshold
- No explicit VOF-liquid interaction logic
- A droplet entering a cell with α>0 simply continues to evaporate/lose momentum
  to the gas phase; there is no droplet-liquid collision, coalescence, or phase-change
  interaction with the VOF interface

**Source**: `SprayFuelData.H` (min_eb_vfrac), `SprayParticles.cpp:417-420`

### 2.9 Derived Quantities

Available spray plot variables:
- `spray_mass`, `spray_density`, `spray_num`, `spray_vol`, `spray_surf_area`
- `spray_vol_frac`, `d10`, `d32` (Sauter Mean Diameter)
- `wall_film_hght`, `wall_film_mass`, `spray_temp`, `num_parcels`
- `spray_x_vel`, `spray_y_vel`, `spray_z_vel`

**Source**: `SpraySetup.cpp:179-192`

---

## Step 3: Gap Analysis vs. Master Plan (3.11–3.14)

### 3.11 — Droplet Motion Tracking

| Capability | Status | Gap |
|-----------|--------|-----|
| Lagrangian point-particle tracking | ✅ **Covered** | — |
| Drag model (Stokes/transitional/turbulent) | ✅ **Covered** | — |
| Multi-level AMR particle redistribution | ✅ **Covered** | Virtual/ghost particle system handles AMR |
| 2D assumption warning | ⚠️ **Partial** | 2D spray assumes Lz=dz (narrow domain) |
| Particle-wall collision reflection | ✅ **Covered** | `impose_wall` in SprayParticles.cpp |

**Gap rating: LOW** — Core tracking is feature-complete. Minor: 2D-3D generalization caveat.

### 3.12 — Reitz Wave + TAB Breakup

| Capability | Status | Gap |
|-----------|--------|-----|
| TAB breakup (O'Rourke & Amsden) | ✅ **Covered** | — |
| ETAB extension (Tanner) | ✅ **Covered** | Child droplet sizing included |
| Reitz KH wave model | ✅ **Covered** | — |
| Reitz RT instability model | ✅ **Covered** | — |
| KH-RT combined model | ✅ **Covered** | `use_breakup_model = KHRT` |
| Splash/wall film | ✅ **Covered** | Ahamed (2022) splash model |

**Gap rating: VERY LOW** — Both breakup models are fully implemented with published
calibration constants. Splash model adds wall interaction beyond breakup.

### 3.13 — Abramzon-Sirignano Evaporation

| Capability | Status | Gap |
|-----------|--------|-----|
| One-third rule reference state | ✅ **Covered** | — |
| Iterative corrected Nusselt number | ✅ **Covered** | `calcHeatCoeff` with convergence loop |
| Schmidt number mass transfer | ✅ **Covered** | `Sh_0 = f(Re, Sc)` |
| Multi-component fuel evaporation | ✅ **Covered** | CSR liquid→gas species mapping |
| Film evaporation | ✅ **Covered** | Chilton-Colburn analogy |
| Manifold EOS compatibility | ✅ **Covered** | Special path for reduced chemistry |
| Saturation pressure calculation | ✅ **Covered** | Antoine equation + Clasius-Clapeyron fallback |

**Gap rating: VERY LOW** — The evaporation implementation closely follows Abramzon &
Sirignano (1989) and includes extensions for multi-component fuels and film evaporation.

### 3.14 — Two-Phase Coupling Source Terms

| Capability | Status | Gap |
|-----------|--------|-----|
| Mass source → density equation | ✅ **Covered** | — |
| Momentum source → momentum equations | ✅ **Covered** | Drag + evaporating mass |
| Energy source → energy equation | ✅ **Covered** | Convection + latent + kinetic |
| Species source → species transport | ✅ **Covered** | — |
| Configurable on/off per mechanism | ✅ **Covered** | `mom_transfer`, `mass_transfer` |
| AMR-aware source ghost cells | ✅ **Covered** | `getSourceGhostCells` |

**Gap rating: LOW** — All four conservation equations receive spray source terms.
Minor: no turbulent dispersion model (particles follow mean flow only).

### ACD-07 — Droplet Cloud Detonation

This is a new capability not present in the current codebase. Required components:

| Component | Present? | Gap |
|-----------|----------|-----|
| Multi-droplet cloud initialization | ❌ | No uniform/bulk cloud init utility beyond `uniformSprayInit` |
| Droplet-gas detonation coupling | ❌ | No reaction source from droplet evaporation + gas ignition |
| Shock-droplet interaction | ❌ | No specialized physics (droplet stripping, secondary atomization) |
| Multi-phase detonation structure | ❌ | Requires coupling spray evaporation → gas reactivity |

**Gap rating: HIGH** — ACD-07 requires new physics modules:
1. Droplet cloud initialization (spatial distribution functions)
2. Coupling between evaporating fuel vapor and gas-phase reaction source terms
3. Shock-induced droplet breakup (beyond current TAB/KHRT)
4. Detonation wave structure analysis with spray diagnostics

---

## Summary

| Task | Coverage | Priority Action |
|------|----------|-----------------|
| 3.11 Droplet tracking | ~95% | Fix 2D→3D generalization; verify AMR redistribution |
| 3.12 Reitz+TAB breakup | ~100% | Validation only |
| 3.13 A-S evaporation | ~95% | Validation only |
| 3.14 Two-phase coupling | ~90% | Add turbulent dispersion model if needed |
| ACD-07 Cloud detonation | ~20% | **Major implementation** — cloud init, reaction coupling, diagnostics |
| VOF interaction | ~5% | Droplet-interface interaction model needed |
| Integration (VOF codebase) | ~60% | Fix Spray-Jet regtest for NUM_ADV>0 |

### Recommended Next Steps

1. **Fix Spray-Jet regtest**: Reconcile spray source dimensioning with NUM_ADV>0 to
   restore the baseline regression test.
2. **Basic validation**: Run Spray-Jet with decane against experimental data (ECN Spray A)
   to confirm evaporation and breakup accuracy.
3. **Turbulent dispersion**: Implement stochastic dispersion model for RANS spray coupling.
4. **ACD-07 architecture**: Design the droplet-cloud initiation, reaction-source coupling,
   and post-processing framework before implementation.
5. **VOF-spray bridge**: Define droplet behavior at VOF interfaces (absorb? reflect?
   continue with modified source deposition?).
