# H2 Fire Consequence Traceability Audit

- Status: `PASS-H2-FIRE-CONSEQUENCE-TRACEABILITY`
- Scope: internal formula and evidence traceability for screening consequence metrics.
- Calibration claim: `False`

## Linked Fire Evidence

- Single CUDA 1000-step final Y(H2O)_max: `0.1405349795432564`
- Large-grid MPI+CUDA final Y(H2O)_max: `0.016843226873556934`
- Restart MPI+CUDA Y(H2O)_max: `0.001993830787372594 -> 0.13344498290244958`

## Formula Checks

| Check | Relative error |
| --- | ---: |
| `source_limited_heat_release_w` | 0.000e+00 |
| `flammable_cloud_energy_j` | 0.000e+00 |
| `cloud_average_heat_release_w` | 0.000e+00 |
| `source_limited_radiative_power_w` | 0.000e+00 |
| `cloud_average_radiative_power_w` | 0.000e+00 |
| `tnt_equivalent_mass_kg` | 0.000e+00 |
| `source_flux_at_1m` | 0.000e+00 |
| `cloud_flux_at_1m` | 0.000e+00 |
| `source_flux_at_3m` | 0.000e+00 |
| `cloud_flux_at_3m` | 0.000e+00 |
| `source_flux_at_5m` | 0.000e+00 |
| `cloud_flux_at_5m` | 0.000e+00 |
| `source_flux_at_10m` | 0.000e+00 |
| `cloud_flux_at_10m` | 0.000e+00 |
| `source_flux_at_20m` | 0.000e+00 |
| `cloud_flux_at_20m` | 0.000e+00 |

## Limitations

- This audit proves traceability and internal consistency of screening metrics, not external calibration.
- Direct reacting plotfile heat-release extrema are linked as fire-existence evidence; they are not converted into calibrated radiative or overpressure loads.
- The fire-consequence production blocker remains until accepted external radiation and overpressure data pass the calibrated report gate.
