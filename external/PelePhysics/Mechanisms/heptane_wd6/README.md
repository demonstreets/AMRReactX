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
Post-generation source edits add `inline` on the two CUDA molecular-weight
arrays, to share their constant-memory storage across translation units, and
the explicitly selectable concentration regularization described below.

This is an explicitly named global-model benchmark. It contains no radicals,
low-temperature intermediates or elementary ignition chemistry, and does not
replace the separate 88-species verification. Comparisons to published spray
detonation work must also identify differences in thermodynamics, transport,
domain, boundaries, mesh and initial excitation.

Generated activation energies use R = 1.9872042586408316 cal/(mol K), consistent with Cantera. The generator process overrides the legacy CEPTR Rc value in memory; the shared generator and existing 88-species mechanism are unchanged.

## Optional concentration regularization

The default `PELE_WD6_REGULARIZATION=0` retains the original fractional rate
laws. The fuel's quarter-order law has a singular derivative at finite-time
depletion. Native unconstrained CVODE trials produced inadmissible negative
fuel; trials with nonnegative constraints stopped with convergence failures
at depletion. Neither result is a successful propagation validation.

For a separately labeled numerical approximation, compile with
`WD6_REGULARIZATION=epsilon`, in mol/m^3. Fractional factors with exponent
`a < 1` become `f(c)=c*(c+epsilon)^(a-1)` for nonnegative concentration. Their
analytic Jacobians use the exact derivative
`f'(c)=(c+epsilon)^(a-2)*(epsilon+a*c)`. Negative Newton trial concentrations
use a signed linear continuation with slope `epsilon^(a-1)`. No accepted mass
fraction is clipped, and the reaction stoichiometry and thermodynamics remain
unchanged. This is a modification of the rate law near depletion, not the
unmodified published mechanism.

The prepared case must declare the same epsilon using
`--wd6-regularization`; startup aborts on a mismatch with the binary. The default
build cache separates epsilon values. If explicitly reusing a cache, force all
mechanism-header dependencies to rebuild with `make -W /absolute/path/mechanism.H`.
Report epsilon and its sensitivity alongside any regularized results.

`tools/validate_wd6_rates.py` compares native rates and Jacobians with Cantera
and an independent Python implementation of the stated regularization. Its
positive-epsilon mode adds trace-fuel states around depletion. Separate closed
reactor, time-step and concentration-threshold checks are required before
accepting a regularized propagation calculation.
