#!/usr/bin/env python3
"""
validate_bfs.py — Phase 2.7 Backward-Facing Step Validation.

Reads a PeleLMeX AMReX plotfile and validates against Driver & Seegmiller
(1985) experimental data for turbulent flow over a backward-facing step.

Key metrics:
  - Reattachment length X_R/H  (reference: 6.26 ± 0.10)
  - Wall friction coefficient Cf along bottom wall
  - Step-face pressure coefficient Cp
  - Velocity profiles at select stations

Usage:
    python3 validate_bfs.py <plotfile_directory>
    python3 validate_bfs.py --test

Output: VERDICT: PASS / FAIL
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from amrex_reader import read_plotfile, PlotfileError


# ─── Constants ───────────────────────────────────────────────────────────────

H = 0.0381           # Step height [m]
X_R_REF = 6.26       # Reference reattachment length X_R/H
X_R_TOL = 0.10       # ±10% tolerance, aligned with the engineering master plan
U_REF = 13.47        # Reference velocity [m/s] (Driver & Seegmiller 44.2 ft/s)
RHO = 1.225          # Air density [kg/m³]
NU = 1.5e-5          # Kinematic viscosity [m²/s]

# Recirculation zone: minimum Cf < 0 region length
MIN_RECIRC_LENGTH = 3.0  # in units of H


# ─── Computation functions ───────────────────────────────────────────────────

def compute_cf(tau_w, rho=RHO, u_ref=U_REF):
    """Skin friction coefficient: Cf = tau_w / (0.5 * rho * U_ref^2)."""
    denom = 0.5 * rho * u_ref * u_ref
    return np.where(denom > 0, tau_w / denom, 0.0)


def compute_cp(p, p_ref, rho=RHO, u_ref=U_REF):
    """Pressure coefficient: Cp = (p - p_ref) / (0.5 * rho * U_ref^2)."""
    denom = 0.5 * rho * u_ref * u_ref
    return np.where(denom > 0, (p - p_ref) / denom, 0.0)


def find_reattachment(x, cf):
    """Find reattachment point from Cf distribution.

    Reattachment occurs where Cf crosses from negative to positive
    (i.e., where wall shear stress changes sign).

    Args:
        x: x-coordinate array
        cf: Cf array (can contain NaN)

    Returns:
        x_reattach, x_actual (H units), or (nan, nan) if not found
    """
    # Find valid points
    valid = np.isfinite(cf) & np.isfinite(x)
    x_v = x[valid]
    cf_v = cf[valid]

    if len(cf_v) < 2:
        return np.nan, np.nan

    # Look for sign change: cf negative then positive
    for i in range(1, len(cf_v)):
        if cf_v[i - 1] < 0 and cf_v[i] >= 0:
            # Linear interpolation for zero-crossing
            x0, x1 = x_v[i - 1], x_v[i]
            c0, c1 = cf_v[i - 1], cf_v[i]
            if abs(c1 - c0) > 1e-15:
                x_r = x0 - c0 * (x1 - x0) / (c1 - c0)
            else:
                x_r = (x0 + x1) / 2.0
            return x_r, x_r / H

    return np.nan, np.nan


def find_recirculation_zone(x, cf):
    """Find recirculation zone (region of negative Cf).

    Returns:
        (start_x, end_x, length) in meters, and (start_x/H, end_x/H, length/H)
    """
    valid = np.isfinite(cf) & np.isfinite(x)
    x_v = x[valid]
    cf_v = cf[valid]

    if len(cf_v) < 2:
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

    neg_mask = cf_v < 0
    if not np.any(neg_mask):
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

    # Find the first contiguous negative region starting from step (x >= 0)
    neg_from_step = neg_mask & (x_v >= -1e-6)

    if not np.any(neg_from_step):
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

    neg_indices = np.where(neg_from_step)[0]
    start = x_v[neg_indices[0]]
    end = x_v[neg_indices[-1]]
    length = end - start

    return start, end, length, start / H, end / H, length / H


def extract_bottom_cf(pf, rho=RHO, u_ref=U_REF, nu=NU):
    """Extract Cf along bottom wall from plotfile.

    Uses first cell above wall and log-law inversion to estimate tau_w.

    Returns:
        dict with: x, cf, x_h (x/H), valid mask
    """
    fields = pf['fields']
    x = pf['x']
    dy = pf['dx'][1]
    y_p = dy / 2.0

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

    u_wall = u[:, 0]  # first row above wall (y=0)
    rho_wall = rho_field[:, 0]

    valid = np.isfinite(u_wall) & (rho_wall > 0) & np.isfinite(rho_wall)
    cf_arr = np.full_like(u_wall, np.nan)
    tau_arr = np.full_like(u_wall, np.nan)

    KAPPA = 0.41
    B = 5.0

    for ix in range(len(u_wall)):
        if not valid[ix]:
            continue
        uw = abs(u_wall[ix])
        rhow = rho_wall[ix]

        # Newton-Raphson for u_tau
        u_tau = max(uw, 1e-10) / 25.0
        for _ in range(20):
            yp = y_p * u_tau / nu
            if yp < 1.0:
                u_tau = np.sqrt(nu * uw / y_p)
                break
            f = u_tau * (np.log(yp) / KAPPA + B) - uw
            df = (np.log(yp) / KAPPA + B) + 1.0 / KAPPA
            delta = f / df if abs(df) > 1e-15 else 0.0
            u_tau -= delta
            if abs(delta) < 1e-8 * abs(u_tau):
                break

        tau_w = rhow * u_tau * u_tau
        # Sign: positive if flow is in +x direction
        tau_arr[ix] = np.sign(u_wall[ix]) * tau_w
        cf_arr[ix] = compute_cf(tau_arr[ix], rho, u_ref)

    return {
        'x': x,
        'x_h': x / H,
        'cf': cf_arr,
        'tau_w': tau_arr,
        'valid': valid,
    }


def extract_velocity_profile(pf, x_target):
    """Extract velocity profile at a specified x station."""
    fields = pf['fields']
    x_cells = pf['x']
    y_cells = pf['y']

    ix = np.argmin(np.abs(x_cells - x_target))

    if 'x_velocity' in fields:
        u = fields['x_velocity'][ix, :]
    elif 'velocityx' in fields:
        u = fields['velocityx'][ix, :]
    else:
        raise KeyError("No velocity field found")

    return {
        'x_target': x_target,
        'x_actual': x_cells[ix],
        'y': y_cells,
        'u': u,
        'y_h': y_cells / H,
        'u_norm': u / U_REF,
    }


def extract_step_cp(pf, rho=RHO, u_ref=U_REF):
    """Extract pressure coefficient along the step face (x=0, 0≤y≤H).

    Returns:
        dict with: y, y_h, cp
    """
    fields = pf['fields']
    y_cells = pf['y']
    x_cells = pf['x']

    # Find x=0 index
    ix = np.argmin(np.abs(x_cells - 0.0))

    if 'pressure' in fields:
        p = fields['pressure'][ix, :]
    elif 'avg_pressure' in fields:
        p = fields['avg_pressure'][ix, :]
    elif 'p' in fields:
        p = fields['p'][ix, :]
    else:
        # Approximate from RhoRT or rhoh
        if 'RhoRT' in fields:
            p = fields['RhoRT'][ix, :]
        elif 'rhoh' in fields:
            p = fields['rhoh'][ix, :]
        else:
            raise KeyError("No pressure field found")

    # Reference pressure: average at top of step
    step_mask = y_cells <= H
    if np.any(step_mask):
        p_ref_candidates = p[~step_mask] if np.any(~step_mask) else p
        p_ref = np.mean(p_ref_candidates[np.isfinite(p_ref_candidates)])
    else:
        p_ref = np.mean(p[np.isfinite(p)])

    cp = compute_cp(p, p_ref, rho, u_ref)

    return {
        'y': y_cells,
        'y_h': y_cells / H,
        'cp': cp,
        'p_ref': p_ref,
    }


# ─── Verdict ─────────────────────────────────────────────────────────────────

def determine_verdict_bfs(xr_h, recirc_length_h, cp_valid=False):
    """Determine BFS validation verdict.

    Args:
        xr_h: X_R/H (reattachment length)
        recirc_length_h: recirculation zone length / H
        cp_valid: whether Cp distribution looks qualitatively correct

    Returns:
        (verdict_string, notes_list)
    """
    notes = []
    failures = []

    # Reattachment length
    if not np.isnan(xr_h):
        dev = (xr_h - X_R_REF) / X_R_REF
        if abs(dev) <= X_R_TOL:
            notes.append(f'X_R/H = {xr_h:.2f} (ref {X_R_REF:.2f}, dev {dev*100:+.1f}%) — PASS')
        else:
            failures.append(f'X_R/H = {xr_h:.2f} deviates {dev*100:+.1f}% from ref {X_R_REF:.2f}')
            notes.append(f'X_R/H = {xr_h:.2f} — FAIL')
    else:
        failures.append('X_R/H could not be determined (no Cf zero-crossing found)')
        notes.append('X_R/H — FAIL (not found)')

    # Recirculation zone
    if not np.isnan(recirc_length_h):
        if recirc_length_h >= MIN_RECIRC_LENGTH:
            notes.append(f'Recirculation zone length = {recirc_length_h:.2f}H — PASS')
        else:
            failures.append(f'Recirculation zone too short: {recirc_length_h:.2f}H < {MIN_RECIRC_LENGTH}H')
            notes.append(f'Recirculation zone length = {recirc_length_h:.2f}H — FAIL')
    else:
        notes.append('Recirculation zone not detected')

    verdict = 'PASS' if not failures else 'FAIL'

    return verdict, notes


# ─── Main validation ─────────────────────────────────────────────────────────

def validate(plotfile_dir):
    """Run full BFS validation."""
    print(f"Reading plotfile: {plotfile_dir}")
    pf = read_plotfile(plotfile_dir)
    print(f"  Time: {pf['time']:.4f}")
    print(f"  Grid: {pf['grid']['nx']} x {pf['grid']['ny']}")

    # ── Cf along bottom wall ──
    print("\nExtracting Cf along bottom wall...")
    cf_data = extract_bottom_cf(pf)

    # Find reattachment
    x_r, xr_h = find_reattachment(cf_data['x'], cf_data['cf'])
    print(f"  Reattachment: X_R = {x_r:.5f} m  (X_R/H = {xr_h:.2f})"
          if not np.isnan(x_r) else "  Reattachment: not found")

    # Find recirculation zone
    _, _, recirc_len, _, _, recirc_len_h = find_recirculation_zone(
        cf_data['x'], cf_data['cf'])
    print(f"  Recirculation zone length: {recirc_len_h:.2f}H"
          if not np.isnan(recirc_len_h) else "  Recirculation zone: not detected")

    # ── Velocity profiles ──
    stations = [-4.0, 0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 15.0]  # x/H
    print("\nExtracting velocity profiles...")
    profiles = {}
    for s in stations:
        try:
            prof = extract_velocity_profile(pf, s * H)
            profiles[s] = prof
            u_max = np.max(np.abs(prof['u'][np.isfinite(prof['u'])]))
            print(f"  x/H = {s:5.1f}: U_max = {u_max:.2f} m/s")
        except Exception as e:
            print(f"  x/H = {s:5.1f}: error - {e}")

    # ── Step-face Cp ──
    print("\nExtracting step-face Cp...")
    try:
        cp_data = extract_step_cp(pf)
        cp_step = cp_data['cp'][cp_data['y_h'] <= 1.0]
        cp_valid = np.any(np.isfinite(cp_step))
        print(f"  Cp on step face: {np.nanmin(cp_step):.3f} to {np.nanmax(cp_step):.3f}"
              if cp_valid else "  Cp: no valid data")
    except Exception as e:
        print(f"  Cp: error - {e}")
        cp_valid = False

    # ── Verdict ──
    verdict, notes = determine_verdict_bfs(xr_h, recirc_len_h, cp_valid)

    # ── Report ──
    print("\n" + "=" * 60)
    print("  BACKWARD-FACING STEP VALIDATION REPORT")
    print("=" * 60)
    print(f"\n  Parameters:")
    print(f"    H = {H:.4f} m")
    print(f"    U_ref = {U_REF:.1f} m/s")
    print(f"    Re_H = {U_REF * H / NU:.0f}")
    print(f"\n  Reattachment:")
    print(f"    X_R/H = {xr_h:.2f}" if not np.isnan(xr_h) else "    X_R/H = N/A")
    print(f"    Reference: {X_R_REF:.2f} ± {X_R_TOL*X_R_REF:.2f}")
    print(f"\n  Recirculation zone:")
    print(f"    Length = {recirc_len_h:.2f}H" if not np.isnan(recirc_len_h)
          else "    Length = N/A")
    print(f"    Minimum required: {MIN_RECIRC_LENGTH}H")
    print(f"\n  Notes:")
    for note in notes:
        print(f"    - {note}")
    print(f"\n  VERDICT: {verdict}")
    print("=" * 60)

    return {
        'verdict': verdict,
        'notes': notes,
        'xr_h': xr_h,
        'xr': x_r,
        'recirc_length_h': recirc_len_h,
        'cf_data': cf_data,
        'profiles': profiles,
    }


def run_synthetic_test():
    """Run with synthetic test data."""
    print("Running BFS synthetic test...\n")

    # Test Cf computation
    cf = compute_cf(0.5, 1.225, 44.2)
    print(f"Cf (tau=0.5, rho=1.225, U=44.2) = {cf:.6f}")

    # Test Cp computation
    cp = compute_cp(101400, 101325, 1.225, 44.2)
    print(f"Cp (p=101400, p_ref=101325) = {cp:.4f}")

    # Test reattachment finding
    x = np.linspace(0, 1.0, 100)
    cf_test = (x - 0.3) * 0.01  # crosses zero at x=0.3
    xr, xrh = find_reattachment(x * H, cf_test)
    print(f"Reattachment: X_R = {xr:.5f} m, X_R/H = {xrh:.2f} (expected ~0.0114, ~0.30)")

    # Test recirculation zone
    s, e, l, sh, eh, lh = find_recirculation_zone(x * H, cf_test)
    print(f"Recirculation zone: {sh:.2f}H to {eh:.2f}H, length = {lh:.2f}H")

    # Test verdict
    v1, n1 = determine_verdict_bfs(6.26, 5.0, True)
    v2, n2 = determine_verdict_bfs(7.0, 2.5, True)
    v3, n3 = determine_verdict_bfs(10.0, 1.0, False)
    print(f"\nVerdict (perfect): {v1}")
    print(f"Verdict (marginal): {v2}")
    print(f"Verdict (bad): {v3}")

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
