#!/usr/bin/env python3
"""
validate_flat_plate.py — Phase 2.7 Flat Plate Boundary Layer Validation.

Reads a PeleLMeX AMReX plotfile and validates against:
  - Cf = 0.027 / Rex^(1/7)  (turbulent BL skin friction correlation)
  - U+ = (1/kappa) * ln(y+) + B  (log-law velocity profile)

Usage:
    python3 validate_flat_plate.py <plotfile_directory>
    python3 validate_flat_plate.py --test   (run with synthetic test data)

Output: VERDICT: PASS / PASS WITH NOTES / FAIL
"""

import sys
import os
import numpy as np

# Allow import from tools/ directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from amrex_reader import read_plotfile, PlotfileError


# ─── Physical constants ──────────────────────────────────────────────────────

KAPPA = 0.41        # von Karman constant
B_LOG = 5.0         # smooth-wall log-law intercept
NU_AIR = 1.5e-5     # kinematic viscosity of air [m²/s]
RHO_AIR = 1.225     # air density [kg/m³] — nominal
U_INF = 10.0        # freestream velocity [m/s]

# Log-law tolerance
SLOPE_TOL = 0.10    # ±10% on slope (1/kappa)
B_TOL = 1.0         # ±1.0 on intercept
CF_TOL = 0.15       # ±15% on Cf


# ─── Core computation functions ──────────────────────────────────────────────

def compute_cf_empirical(re_x):
    """Empirical turbulent BL skin friction: Cf = 0.027 / Re_x^(1/7).

    Args:
        re_x: Reynolds number based on x (float or array)

    Returns:
        Cf value(s)
    """
    re_x = np.maximum(re_x, 1e3)  # avoid singularity
    return 0.027 / (re_x ** (1.0 / 7.0))


def compute_re_x(x, u_inf, nu):
    """Compute Reynolds number: Re_x = U_inf * x / nu."""
    return u_inf * x / nu


def compute_u_tau(tau_w, rho):
    """Friction velocity: u_tau = sqrt(tau_w / rho)."""
    tau_w = np.maximum(tau_w, 0.0)
    return np.sqrt(tau_w / rho)


def compute_y_plus(y, u_tau, nu):
    """Dimensionless wall distance: y+ = y * u_tau / nu."""
    return y * u_tau / nu


def compute_u_plus(u_par, u_tau):
    """Dimensionless velocity: u+ = u_par / u_tau."""
    u_tau_safe = np.maximum(u_tau, 1e-20)
    return u_par / u_tau_safe


def compute_cf_from_tau(tau_w, rho, u_inf):
    """Skin friction coefficient from wall shear stress: Cf = tau_w / (0.5 * rho * U_inf^2)."""
    return tau_w / (0.5 * rho * u_inf * u_inf)


def log_law_regression(y_plus, u_plus, yplus_min=30.0, yplus_max=300.0):
    """Perform linear regression on log-law region: U+ = (1/kappa) * ln(y+) + B.

    Args:
        y_plus: array of y+ values
        u_plus: array of U+ values
        yplus_min, yplus_max: bounds of log-law region

    Returns:
        dict with keys: slope (1/kappa), intercept (B), kappa, r_squared,
                        n_points, mask
    """
    mask = (y_plus >= yplus_min) & (y_plus <= yplus_max)
    n_points = np.sum(mask)

    if n_points < 5:
        return {
            'slope': np.nan, 'intercept': np.nan, 'kappa': np.nan,
            'r_squared': np.nan, 'n_points': n_points, 'mask': mask,
            'error': 'Insufficient points in log-law region (< 5)'
        }

    x = np.log(y_plus[mask])
    y = u_plus[mask]

    # Linear regression: y = a * x + b
    # a = slope = 1/kappa, b = intercept = B
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    a = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
    b = y_mean - a * x_mean

    # R-squared
    y_pred = a * x + b
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y_mean) ** 2)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    kappa_fit = 1.0 / a if abs(a) > 1e-10 else np.inf

    return {
        'slope': a,
        'intercept': b,
        'kappa': kappa_fit,
        'r_squared': r_squared,
        'n_points': n_points,
        'mask': mask,
    }


# ─── Data extraction ─────────────────────────────────────────────────────────

def extract_wall_profile(pf, x_target, nu=NU_AIR, rho=RHO_AIR, u_inf=U_INF):
    """Extract y+, U+ profile at a specified x station.

    Args:
        pf: plotfile dict from read_plotfile()
        x_target: x-coordinate to extract at [m]
        nu: kinematic viscosity
        rho: density
        u_inf: freestream velocity (for Cf)

    Returns:
        dict with keys: y_plus, u_plus, y, u, Cf, re_x, x_actual
    """
    fields = pf['fields']
    x_cells = pf['x']
    y_cells = pf['y']
    dx = pf['dx'][0]

    # Find closest x-index
    ix = np.argmin(np.abs(x_cells - x_target))
    x_actual = x_cells[ix]

    # Extract velocity profile at this x
    # x_velocity field shape: (ny, nx)
    if 'x_velocity' in fields:
        u = fields['x_velocity'][:, ix]
    elif 'velocityx' in fields:
        u = fields['velocityx'][:, ix]
    else:
        raise KeyError("No x_velocity or velocityx field found")

    # Get density for Cf computation
    if 'density' in fields:
        rho_field = fields['density'][:, ix]
        rho_use = np.mean(rho_field[np.isfinite(rho_field)])
    else:
        rho_use = rho

    # Wall shear stress from the first cell (using wall function assumption)
    # tau_w estimated from the near-wall velocity gradient:
    # u_tau from first cell via log-law inversion.
    # In a flat-plate BL v ≈ 0 so the x-velocity magnitude is the
    # full velocity magnitude; use u[0] directly (no fallback).
    dy = pf['dx'][1]
    u_wall = u[0]
    uw = abs(u_wall)
    y_p = dy / 2.0  # first cell center distance from wall

    # Newton-Raphson for u_tau from log-law (simplified)
    u_tau_est = uw / 25.0  # initial guess
    for _ in range(20):
        yp = y_p * u_tau_est / nu
        if yp < 1.0:
            u_tau_est = np.sqrt(nu * uw / y_p)  # viscous sublayer
            break
        f = u_tau_est * (np.log(yp) / KAPPA + B_LOG) - uw
        df = (np.log(yp) / KAPPA + B_LOG) + 1.0 / KAPPA
        delta = f / df if abs(df) > 1e-15 else 0.0
        u_tau_est -= delta
        if abs(delta) < 1e-8 * abs(u_tau_est):
            break

    tau_w_est = rho_use * u_tau_est * u_tau_est

    # Compute y+ and u+ for all cells
    u_tau_arr = np.ones_like(u) * u_tau_est
    y_plus = compute_y_plus(y_cells, u_tau_arr, nu)
    u_plus = compute_u_plus(u, u_tau_arr)

    # Compute Cf and Re_x
    re_x = compute_re_x(x_actual, u_inf, nu)
    cf = compute_cf_from_tau(tau_w_est, rho_use, u_inf)

    # Also compute Cf from velocity gradient at wall (finite difference)
    # du/dy at wall ~ u[0] / (dy/2) for first cell
    dudy_wall = u[0] / y_p if y_p > 0 else 0.0
    tau_w_fd = rho_use * nu * dudy_wall
    cf_fd = compute_cf_from_tau(tau_w_fd, rho_use, u_inf)

    return {
        'y_plus': y_plus,
        'u_plus': u_plus,
        'y': y_cells,
        'u': u,
        'cf': cf,
        'cf_fd': cf_fd,
        're_x': re_x,
        'x_actual': x_actual,
        'u_tau': u_tau_est,
        'tau_w': tau_w_est,
    }


def extract_cf_distribution(pf, nu=NU_AIR, rho=RHO_AIR, u_inf=U_INF):
    """Extract Cf(x) along the wall.

    Uses the first cell above the wall at each x station to estimate
    wall shear stress via the log-law assumption.

    Returns:
        dict with: x, cf, re_x
    """
    fields = pf['fields']
    x_cells = pf['x']
    dy = pf['dx'][1]
    y_p = dy / 2.0  # first cell center

    if 'x_velocity' in fields:
        u = fields['x_velocity']
    elif 'velocityx' in fields:
        u = fields['velocityx']
    else:
        raise KeyError("No velocity field found")

    if 'density' in fields:
        rho_field = fields['density']
    else:
        rho_field = np.ones_like(u) * rho

    # u shape: (ny, nx), first row is wall-adjacent
    u_wall = u[0, :]
    rho_wall = rho_field[0, :]

    # Filter out invalid cells (EB covered regions)
    valid = np.isfinite(u_wall) & (rho_wall > 0) & np.isfinite(rho_wall)

    cf_arr = np.zeros_like(u_wall)
    cf_arr[:] = np.nan

    for ix in range(len(u_wall)):
        if not valid[ix]:
            continue
        uw = abs(u_wall[ix])
        rhow = rho_wall[ix]

        # Estimate u_tau from first cell velocity (log-law inversion)
        u_tau_est = max(uw, 1e-10) / 25.0
        for _ in range(20):
            yp = y_p * u_tau_est / nu
            if yp < 1.0:
                u_tau_est = np.sqrt(nu * uw / y_p)
                break
            f = u_tau_est * (np.log(yp) / KAPPA + B_LOG) - uw
            df = (np.log(yp) / KAPPA + B_LOG) + 1.0 / KAPPA
            delta = f / df if abs(df) > 1e-15 else 0.0
            u_tau_est -= delta
            if abs(delta) < 1e-8 * abs(u_tau_est):
                break

        tau_w = rhow * u_tau_est * u_tau_est
        cf_arr[ix] = compute_cf_from_tau(tau_w, rho, u_inf)

    re_x = compute_re_x(x_cells, u_inf, nu)

    return {
        'x': x_cells,
        'cf': cf_arr,
        're_x': re_x,
        'valid': valid,
    }


# ─── Verdict determination ───────────────────────────────────────────────────

def determine_verdict(cf_deviation, kappa_deviation, b_deviation,
                      log_r_squared, cf_deviation_max=None):
    """Determine validation verdict based on metric deviations.

    Returns:
        (verdict_string, notes_list)
    """
    notes = []
    failures = []

    # Cf check
    if cf_deviation is not None and not np.isnan(cf_deviation):
        if abs(cf_deviation) <= CF_TOL:
            notes.append(f'Cf deviation {cf_deviation*100:+.1f}% — PASS')
        else:
            failures.append(f'Cf deviation {cf_deviation*100:+.1f}% exceeds ±{CF_TOL*100:.0f}%')
            notes.append(f'Cf deviation {cf_deviation*100:+.1f}% — FAIL')

    # Log-law slope (kappa) check
    if kappa_deviation is not None and not np.isnan(kappa_deviation):
        if abs(kappa_deviation) <= SLOPE_TOL:
            notes.append(f'kappa deviation {kappa_deviation*100:+.1f}% — PASS')
        else:
            failures.append(f'kappa deviation {kappa_deviation*100:+.1f}% exceeds ±{SLOPE_TOL*100:.0f}%')
            notes.append(f'kappa deviation {kappa_deviation*100:+.1f}% — FAIL')

    # Log-law intercept check
    if b_deviation is not None and not np.isnan(b_deviation):
        if abs(b_deviation) <= B_TOL:
            notes.append(f'B deviation {b_deviation:+.2f} — PASS')
        else:
            failures.append(f'B deviation {b_deviation:+.2f} exceeds ±{B_TOL}')
            notes.append(f'B deviation {b_deviation:+.2f} — FAIL')

    # R-squared check
    if log_r_squared is not None and not np.isnan(log_r_squared):
        if log_r_squared >= 0.9:
            notes.append(f'Log-law R²={log_r_squared:.3f} — good fit')
        elif log_r_squared >= 0.7:
            notes.append(f'Log-law R²={log_r_squared:.3f} — marginal fit')
        else:
            failures.append(f'Log-law R²={log_r_squared:.3f} — poor fit')

    if not failures:
        return 'PASS', notes
    elif len(failures) <= 1:
        return 'PASS WITH NOTES', notes + failures
    else:
        return 'FAIL', notes + failures


# ─── Main validation ─────────────────────────────────────────────────────────

def validate(plotfile_dir):
    """Run full flat plate validation.

    Args:
        plotfile_dir: Path to plotfile directory

    Returns:
        dict with validation results
    """
    print(f"Reading plotfile: {plotfile_dir}")
    pf = read_plotfile(plotfile_dir)
    print(f"  Time: {pf['time']:.4f}")
    print(f"  Grid: {pf['grid']['nx']} x {pf['grid']['ny']}")
    print(f"  Dom: [{pf['prob_lo'][0]:.2f}, {pf['prob_lo'][1]:.2f}] — "
          f"[{pf['prob_hi'][0]:.2f}, {pf['prob_hi'][1]:.2f}]")

    # ── Extract profiles ──
    x_station = 1.5  # m
    print(f"\nExtracting profile at x = {x_station} m...")
    profile = extract_wall_profile(pf, x_station)
    actual_x = profile['x_actual']

    # ── Log-law regression ──
    print("Performing log-law regression...")
    reg = log_law_regression(profile['y_plus'], profile['u_plus'])

    # ── Cf comparison ──
    print("Computing Cf distribution...")
    cf_data = extract_cf_distribution(pf)

    # Cf at the target x station
    cf_emp = compute_cf_empirical(profile['re_x'])
    cf_computed = profile['cf']
    cf_dev = (cf_computed - cf_emp) / cf_emp if cf_emp > 0 else np.nan

    # ── Compute deviations ──
    kappa_dev = (reg['kappa'] - KAPPA) / KAPPA if not np.isnan(reg['kappa']) else np.nan
    b_dev = reg['intercept'] - B_LOG if not np.isnan(reg['intercept']) else np.nan

    # ── Verdict ──
    verdict, notes = determine_verdict(cf_dev, kappa_dev, b_dev, reg['r_squared'])

    # ── Report ──
    print("\n" + "=" * 60)
    print("  FLAT PLATE BOUNDARY LAYER VALIDATION REPORT")
    print("=" * 60)
    print(f"\n  Station: x = {actual_x:.4f} m  (Re_x = {profile['re_x']:.2e})")
    print(f"\n  Cf comparison:")
    print(f"    Computed:  {cf_computed:.6f}")
    print(f"    Empirical: {cf_emp:.6f}  (0.027/Re_x^(1/7))")
    print(f"    Deviation: {cf_dev*100:+.1f}%")
    print(f"\n  Log-law fit (U+ = (1/κ)ln(y+) + B):")
    print(f"    κ = {reg['kappa']:.4f}  (ref: {KAPPA})")
    print(f"    B = {reg['intercept']:.3f}  (ref: {B_LOG})")
    print(f"    R² = {reg['r_squared']:.4f}")
    print(f"    Points in log region: {reg['n_points']}")
    print(f"\n  Deviations:")
    print(f"    κ: {kappa_dev*100:+.1f}%")
    print(f"    B: {b_dev:+.2f}")
    print(f"\n  Notes:")
    for note in notes:
        print(f"    - {note}")
    print(f"\n  VERDICT: {verdict}")
    print("=" * 60)

    return {
        'verdict': verdict,
        'notes': notes,
        'cf_computed': cf_computed,
        'cf_empirical': cf_emp,
        'cf_deviation': cf_dev,
        'kappa': reg['kappa'],
        'b': reg['intercept'],
        'kappa_deviation': kappa_dev,
        'b_deviation': b_dev,
        'r_squared': reg['r_squared'],
        're_x': profile['re_x'],
        'profile': profile,
        'regression': reg,
        'cf_data': cf_data,
    }


def run_synthetic_test():
    """Run validation on synthetic data for testing purposes."""
    print("Running synthetic test (no plotfile needed)...")
    print()

    # Generate synthetic log-law profile
    np.random.seed(42)
    y_plus = np.logspace(0, 3, 60)
    u_plus_true = np.log(y_plus) / KAPPA + B_LOG
    u_plus_noisy = u_plus_true + np.random.normal(0, 0.2, len(y_plus))

    # Test log-law regression
    reg = log_law_regression(y_plus, u_plus_noisy)
    print("Log-law regression on synthetic data:")
    print(f"  κ = {reg['kappa']:.4f} (expected {KAPPA})")
    print(f"  B = {reg['intercept']:.3f} (expected {B_LOG})")
    print(f"  R² = {reg['r_squared']:.4f}")
    print(f"  n_points = {reg['n_points']}")
    print()

    # Test Cf empirical
    re_x = 1.0e6
    cf = compute_cf_empirical(re_x)
    print(f"Cf(Re_x={re_x:.0e}) = {cf:.6f} (expected ~0.0038)")

    # Test verdict determination
    v_good, n_good = determine_verdict(0.05, 0.03, 0.2, 0.95)
    v_marginal, n_marginal = determine_verdict(0.12, 0.08, 0.8, 0.85)
    v_bad, n_bad = determine_verdict(0.30, 0.20, 2.5, 0.5)

    print(f"\nVerdict (good case): {v_good}")
    print(f"Verdict (marginal case): {v_marginal}")
    print(f"Verdict (bad case): {v_bad}")

    # Test compute_y_plus, compute_u_plus, etc.
    yp = compute_y_plus(0.01, 0.1, 1.5e-5)
    print(f"\ny+ (y=0.01, u_tau=0.1, nu=1.5e-5) = {yp:.1f} (expected ~66.7)")

    up = compute_u_plus(2.0, 0.1)
    print(f"u+ (u=2.0, u_tau=0.1) = {up:.1f} (expected 20.0)")

    re_x_test = compute_re_x(1.5, 10.0, 1.5e-5)
    print(f"Re_x (x=1.5, U=10, nu=1.5e-5) = {re_x_test:.1e} (expected 1.0e6)")

    cf_test = compute_cf_from_tau(0.012, 1.225, 10.0)
    print(f"Cf (tau_w=0.012, rho=1.225, U=10) = {cf_test:.6f}")

    print("\nSynthetic test complete.")


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] == '--help':
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == '--test':
        run_synthetic_test()
    else:
        result = validate(sys.argv[1])
        rc = 0 if result['verdict'] == 'PASS' else 1
        sys.exit(rc)
