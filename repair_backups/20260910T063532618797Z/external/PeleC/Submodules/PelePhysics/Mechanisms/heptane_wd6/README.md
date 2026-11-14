# WD6: a separate global n-heptane comparison model

This mechanism implements the two global steps described by Westbrook and
Dryer, *Combustion Science and Technology* 27 (1981), 31–43,
DOI [10.1080/00102208108946970](https://doi.org/10.1080/00102208108946970).
The empirical reverse CO rate is stored as a third directional reaction so
that its independent rate law is preserved.

With concentrations in mol/cm³ and time in seconds:

* Fuel oxidation: C7H16 + 7.5 O2 → 7 CO + 8 H2O; A = 6.3e11,
  E = 30 kcal/mol; orders 0.25 in fuel and 1.5 in O2 (Table IV).
* CO oxidation: CO + 0.5 O2 → CO2; A = 10^14.6, E = 40 kcal/mol;
  orders 1 in CO, 0.5 in H2O and 0.25 in O2 (Eq. 10).
* CO2 dissociation: CO2 → CO + 0.5 O2; A = 5e8, E = 40 kcal/mol;
  order 1 in CO2 (Eq. 11).

All temperature exponents are zero. Cantera's YAML writer converts these
explicit units to SI. The generated PelePhysics source internally uses
mol/m³, and its Chemkin interface converts back to mol/cm³. Direct rate,
thermodynamic and Jacobian comparisons are required to check this boundary.

The six NASA thermodynamic and transport records are copied without changing
their values from `heptane_lu_88sk`. The original WD paper did not supply these
polynomials. The empirical CO forward/reverse rates do not enforce the
thermodynamic equilibrium constant. A Gibbs-equilibrium CJ calculation is
therefore a comparison value, not automatically the kinetic eigenvalue.

CEPTR generates `mechanism.H` and `mechanism.cpp`. Its fractional-order rates
use zero on negative trial concentrations; its Jacobian regularizes singular
derivatives at zero. Those are generator conventions for nonlinear iterations;
the solver's raw accepted species still undergo the same admissibility checks.
The only post-generation source edit is `inline` on the two CUDA molecular-
weight arrays, to share their constant-memory storage across translation units.

This is an explicitly named global-model benchmark. It contains no radicals,
low-temperature intermediates or elementary ignition chemistry, and does not
replace the separate 88-species verification. Comparisons to published spray
detonation work must also identify differences in thermodynamics, transport,
domain, boundaries, mesh and initial excitation.
