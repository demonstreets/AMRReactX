# External comparison and interpretation

The primary external source is Zhao and Zhang, *Numerical simulation of
two-dimensional detonation propagation in partially pre-vaporized n-heptane sprays*, ICLASS 2021:
[author manuscript](https://arxiv.org/pdf/2103.12525). It is a conference paper;
do not identify it as a Combustion and Flame journal article.

The paper uses a 1 m by 40 mm domain, 0.1 mm grid, 0.5 atm and 300 K gas, and
slip transverse walls. The wave develops over 800 mm of gas before entering a
200 mm droplet cloud. Its gas-only Table 1 reports, at equivalence ratio 0.6,
a numerical cell range of 5–26 mm, speed 1657 ± 323 m/s and CJ speed 1603 m/s.
The corresponding gas-only values at equivalence ratio 1 are 4–10 mm,
1894 ± 251 m/s and 1802 m/s. These are numerical gas results, not measured
wet-spray reference values. The wet case with gas/liquid equivalence ratios
0.6/0.4 and 10 micrometre droplets supplies qualitative wave, heat-release,
evaporation and pressure-trace comparisons in the paper's figures.

The present verification cases have the following independently recorded scope:

* The 2D WD6 runs use a 140 mm by 40 mm domain, an initialized front at 40 mm,
  and 50 microseconds of propagation. Coarse and fine cell widths are 0.1 and
  0.05 mm. Droplets start beyond the entire perturbed front: `x > 40.8 mm`
  for the 0.8 mm perturbation used here. This is a shorter development distance
  and a different ignition history than the paper.
* The starting profile comes from an independent equilibrium Hugoniot and
  finite-rate ZND calculation. The initial wave is overdriven by 2% in speed.
  Its subsequent speed is not prescribed. Report the transient, later fitting
  windows and boundary distances rather than calling every measured speed CJ.
* The six-species WD mechanism, its rate units, thermodynamic source and
  positive concentration regularization are documented in
  `external/PelePhysics/Mechanisms/heptane_wd6/README.md` and `provenance.json`.
  Native rates/Jacobians and reactor histories are independently checked.
  The regularized implementation is not literally the unmodified published
  rate law at concentrations approaching zero.
* Detailed 88-species reactor and one-dimensional wave calculations are a
  separate chemistry validation layer. The WD6 two-dimensional cellular runs
  must not be described as 88-species cellular simulations.
* The native particle model uses constant liquid density 681.4 kg/m3, finite
  heat and mass transfer and momentum exchange. Its liquid-property treatment
  differs from a thermal-expansion droplet model. The 2D effective depth changes
  with grid spacing; total masses across grids require normalization per depth.

## What each observable can establish

The numerical pressure trace records maximum pressure at every completed step.
Visible intersecting tracks, transverse shock displacement, persistence over
the propagated distance and grid sensitivity must be examined together.
Autocorrelation maxima alone are pressure-pattern repeat distances. They do
not automatically give a statistically converged cell-width distribution.

`tools/analyze_wd6_reaction_sequence.py` reconstructs fuel-oxidation and net
CO-oxidation powers in each cell, independently checks their sum against native
heat release, then averages after aligning each transverse column to its local
shock. The evaporation source and liquid density are aligned the same way.
This avoids computing nonlinear reaction rates from a mean thermodynamic state.

Spatially separated peaks establish spatial ordering within the chosen
mechanism. They do not establish Lagrangian reaction times, distinguish every
fuel molecule's liquid/gas origin, or prove a separate relay detonation. A
persistent finite shock-to-reaction distance supports wave/reaction coupling
over the reported time interval; a growing separation or a decaying shock is
contrary evidence and must also be reported.

Use the observed numerical sensitivities and physical differences when
comparing to the external source. Agreement with a broad published speed or
cell range is a consistency check, not an experimental uncertainty bound or
proof that the initialization and submodels are equivalent.
