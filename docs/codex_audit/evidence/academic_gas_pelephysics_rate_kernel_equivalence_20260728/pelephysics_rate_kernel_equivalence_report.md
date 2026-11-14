# PelePhysics Compiled LiDryer Rate-Kernel Equivalence

Status: `PASS-ACADEMIC-GAS-PELEPHYSICS-RATE-KERNEL-EQUIVALENCE`
Scope: `compiled PelePhysics LiDryer mechanism.H/mechanism.cpp thermochemistry and species source terms compared to Cantera loading of the same mechanism.yaml`

## Summary

- `case_count`: `12`
- `active_species_rate_comparisons`: `60`
- `max_density_relative_error`: `3.4044001891876536e-16`
- `max_density_relative_error_limit`: `1e-11`
- `max_cp_mass_relative_error`: `1.2886230214163894e-15`
- `max_cp_mass_relative_error_limit`: `1e-10`
- `max_mass_fraction_relative_error`: `1.546513723134555e-16`
- `max_mass_fraction_relative_error_limit`: `1e-12`
- `max_active_wdot_relative_error`: `2.5923446507006696e-06`
- `max_active_wdot_relative_error_limit`: `1e-05`
- `max_wdot_abs_error_mol_cm3_s`: `4.701761461026551e-12`
- `clears_full_pelephysics_source_rate_equivalence`: `True`
- `clears_acd_02_rate_kernel_gap`: `True`

## Unit Conversions

- `pressure_pa_to_cgs_dyne_cm2`: `10.0`
- `pelephysics_cpbs_erg_g_K_to_j_kg_K`: `0.0001`
- `pelephysics_rho_g_cm3_to_kg_m3`: `1000.0`
- `cantera_net_production_kmol_m3_s_to_mol_cm3_s`: `0.001`

## Cases

| Case | T (K) | P (Pa) | Phi | rho rel | cp rel | max active wdot rel |
| --- | --- | --- | --- | --- | --- | --- |
| `lean_phi0p6_900K_1atm` | `900.0` | `101325.0` | `0.6` | `1.74837769e-16` | `1.16443324e-15` | `2.59234421e-06` |
| `lean_phi0p6_1200K_1atm` | `1200.0` | `101325.0` | `0.6` | `2.33117026e-16` | `9.55051200e-16` | `1.96705226e-06` |
| `lean_phi0p6_1600K_1atm` | `1600.0` | `101325.0` | `0.6` | `0.00000000e+00` | `1.06911185e-15` | `1.49751530e-06` |
| `stoich_phi1p0_900K_1atm` | `900.0` | `101325.0` | `1.0` | `1.96043463e-16` | `1.04720821e-15` | `2.59234438e-06` |
| `stoich_phi1p0_1200K_1atm` | `1200.0` | `101325.0` | `1.0` | `2.61391284e-16` | `1.28862302e-15` | `1.96712804e-06` |
| `stoich_phi1p0_1600K_1atm` | `1600.0` | `101325.0` | `1.0` | `1.74260856e-16` | `8.23258173e-16` | `1.50329953e-06` |
| `rich_phi1p6_900K_1atm` | `900.0` | `101325.0` | `1.6` | `3.40440019e-16` | `9.13178799e-16` | `2.59234465e-06` |
| `rich_phi1p6_1200K_1atm` | `1200.0` | `101325.0` | `1.6` | `3.02613350e-16` | `9.99076004e-16` | `1.96724171e-06` |
| `rich_phi1p6_1600K_1atm` | `1600.0` | `101325.0` | `1.6` | `0.00000000e+00` | `1.07553903e-15` | `1.51197522e-06` |
| `stoich_phi1p0_1200K_5atm` | `1200.0` | `506625.0` | `1.0` | `2.09113027e-16` | `1.28862302e-15` | `1.96712804e-06` |
| `lean_phi0p6_1200K_5atm` | `1200.0` | `506625.0` | `0.6` | `1.86493621e-16` | `9.55051200e-16` | `1.96705226e-06` |
| `rich_phi1p6_1200K_5atm` | `1200.0` | `506625.0` | `1.6` | `2.42090680e-16` | `9.99076004e-16` | `1.96724171e-06` |

## Evidence Files

- `compiled_probe_csv`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_gas_pelephysics_rate_kernel_equivalence_20260728/pelephysics_lidryer_kernel_probe.csv` sha256 `1a221375f9e7b149`
- `compiled_probe_build_log`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_gas_pelephysics_rate_kernel_equivalence_20260728/build.log` sha256 `c48633cf95aa2839`
- `compiled_probe_source`: `tools/academic_gas_pelephysics_lidryer_kernel_probe.cpp` sha256 `e44c7aa044a227f6`
- `mechanism_header`: `external/PelePhysics/Mechanisms/LiDryer/mechanism.H` sha256 `fcd00ac39099c5a3`
- `mechanism_cpp`: `external/PelePhysics/Mechanisms/LiDryer/mechanism.cpp` sha256 `3d18f8d8f0e1eb82`
- `mechanism_yaml`: `external/PelePhysics/Mechanisms/LiDryer/mechanism.yaml` sha256 `d0f5a97e56a52ef7`

## Limitations

- This validates the compiled CPU LiDryer mechanism kernels used by PelePhysics against Cantera for sampled homogeneous gas states.
- It is not a GPU device-kernel bitwise comparison and does not replace solver-level detonation/fire validation.
- It compares source terms for the same PelePhysics mechanism YAML, not cross-mechanism agreement with Cantera h2o2.yaml.
