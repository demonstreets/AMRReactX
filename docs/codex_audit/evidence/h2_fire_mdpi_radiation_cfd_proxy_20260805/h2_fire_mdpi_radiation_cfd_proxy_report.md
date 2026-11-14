# H2 Fire MDPI Radiation CFD-Derived Proxy

- Status: `PASS-H2-FIRE-MDPI-RADIATION-CFD-PROXY`
- CFD proxy extracted: `True`
- CPU/GPU proxy parity relative diff: `1.30329661e-02`
- Case-aligned agreement: `False`
- Strict fire blocker cleared: `False`

## Comparison

| Metric | Distance m | Reference W/m2 | CUDA proxy W/m2 | CPU/MPI proxy W/m2 | CUDA rel error |
| --- | ---: | ---: | ---: | ---: | ---: |
| `mdpi_jet_fire_1p5mm_0p6mpa_0p23m` | 0.23 | 1.36050000e+03 | 1.48234465e+02 | 1.50191912e+02 | 8.91044127e-01 |
| `mdpi_jet_fire_1p5mm_0p6mpa_0p50m` | 0.5 | 4.12100000e+02 | 3.13664129e+01 | 3.17806085e+01 | 9.23886404e-01 |
| `mdpi_jet_fire_max_1p2mm_0p23m` | 0.23 | 9.52800000e+02 | 1.48234465e+02 | 1.50191912e+02 | 8.44422266e-01 |
| `mdpi_jet_fire_max_2p0mm_0p23m` | 0.23 | 3.37810000e+03 | 1.48234465e+02 | 1.50191912e+02 | 9.56118982e-01 |

## Limitations

- Uses one-cell peak HeatRelease as a radiation proxy, not integrated flame emissive power.
- Does not model flame surface, soot, gas radiation, view factor, obstruction shielding, or radiometer geometry.
- Does not clear strict MDPI radiation agreement; it only proves a finite CFD-derived observable path.
