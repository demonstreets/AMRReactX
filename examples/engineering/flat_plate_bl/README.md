# Flat Plate Boundary Layer — Validation Case

## Overview

Turbulent boundary layer over a smooth flat plate. Compares computed
friction coefficient Cf(x) and log-law velocity profile U+(y+) against
the empirical correlation:

- Cf = 0.027 / Rex^(1/7)  (1/7th power law for turbulent BL)
- U+ = (1/κ) ln(y+) + B   (κ=0.41, B=5.0)

Reference: Wieghardt & Tillmann (1951), ERCOFTAC Classic Database.

## Parameters

| Parameter | Value |
|-----------|-------|
| U∞ | 10 m/s |
| ν | 1.5×10⁻⁵ m²/s (air) |
| Domain | 0 ≤ x ≤ 2.0 m, 0 ≤ y ≤ 0.3 m |
| Grid | 100 × 60 |
| Plate | y=0, 0.05 ≤ x ≤ 2.0 m |
| Turbulence model | k-ε, Launder-Spalding wall function |
| CFL | 0.5 |
| Stop time | 5.0 s |

## Running

```bash
# (Phase 2.9 — PeleLMeX integration)
cd external/PeleLMeX/Exec/MyCase
# Copy input.yaml and adjust prob.cpp for this case
make -j
mpirun -np 4 ./PeleLMeX3d.gnu.MPI.ex input.yaml
```

## Validation

```bash
python3 ../../../tools/validate_flat_plate.py <plotfile_directory>
```

Expected output: `VERDICT: PASS` if Cf and log-law within tolerance.

## Verification Targets

| Metric | Reference | Tolerance |
|--------|-----------|-----------|
| Cf (Rex=10⁶) | 0.0046 | ±15% |
| Log-law slope | 1/0.41 ≈ 2.44 | ±10% |
| Log-law intercept | 5.0 | ±1.0 |
