#!/usr/bin/env python3
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import amrex_reader


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--initial', required=True)
    ap.add_argument('--final', required=True)
    ap.add_argument('--mass-rtol', type=float, default=2.0e-5)
    ap.add_argument('--alpha-tol', type=float, default=1.0e-8)
    args = ap.parse_args()

    initial = amrex_reader.read_plotfile(args.initial)
    final = amrex_reader.read_plotfile(args.final)
    required = ('density', 'rho_E', 'rho_e', 'Temp', 'rho_adv_0')
    for label, plot in (('initial', initial), ('final', final)):
        missing = [name for name in required if name not in plot['fields']]
        if missing:
            raise SystemExit(f'FAIL: {label} missing fields {missing}')

    checks = []
    for label, plot in (('initial', initial), ('final', final)):
        fields = plot['fields']
        for name in required:
            arr = np.asarray(fields[name])
            if not np.isfinite(arr).all():
                raise SystemExit(f'FAIL: non-finite {label} field {name}')
        rho = fields['density']
        rho_e = fields['rho_e']
        temp = fields['Temp']
        alpha = fields['rho_adv_0'] / rho
        if float(rho.min()) <= 0.0 or float(rho_e.min()) <= 0.0 or float(temp.min()) <= 0.0:
            raise SystemExit(
                f'FAIL: nonphysical {label} state '
                f'rho_min={rho.min():.6g} rho_e_min={rho_e.min():.6g} '
                f'T_min={temp.min():.6g}')
        if float(alpha.min()) < -args.alpha_tol or float(alpha.max()) > 1.0 + args.alpha_tol:
            raise SystemExit(
                f'FAIL: alpha out of bounds {label} '
                f'range={alpha.min():.6g}:{alpha.max():.6g}')
        checks.append((label, rho, alpha))

    rho0, alpha0 = checks[0][1:]
    rhof, alphaf = checks[1][1:]
    mass0 = float(rho0.sum())
    massf = float(rhof.sum())
    # rho_adv_0 is the conserved VOF quantity (rho * alpha).  Comparing
    # alpha=rho_adv_0/rho directly is not a conservation check for a
    # compressible flow because rho can evolve.
    vof_mass0 = float((rho0 * alpha0).sum())
    vof_massf = float((rhof * alphaf).sum())
    mass_rel = abs(massf - mass0) / max(abs(mass0), 1.0)
    vof_mass_rel = abs(vof_massf - vof_mass0) / max(abs(vof_mass0), 1.0)
    if mass_rel > args.mass_rtol or vof_mass_rel > args.mass_rtol:
        raise SystemExit(
            f'FAIL: conserved mass drift rho={mass_rel:.6g} '
            f'rho_adv_0={vof_mass_rel:.6g}')
    if float(alpha0.min()) >= 0.5 or float(alpha0.max()) <= 0.5:
        raise SystemExit('FAIL: initial field does not contain both RT phases')
    final_ymom = final['fields'].get('ymom')
    if final_ymom is None or not np.isfinite(final_ymom).all():
        raise SystemExit('FAIL: missing/non-finite final ymom')
    if float(np.max(np.abs(final_ymom))) <= 0.0:
        raise SystemExit('FAIL: gravity produced no measurable momentum response')

    print(
        'rayleigh_taylor_plotfile_validation PASS '
        f'time={final["time"]:.12g} grid={rho0.shape} '
        f'rho_range={rhof.min():.6g}:{rhof.max():.6g} '
        f'alpha_range={alphaf.min():.6g}:{alphaf.max():.6g} '
        f'mass_rel={mass_rel:.6g} vof_mass_rel={vof_mass_rel:.6g} '
        f'ymom_linf={np.max(np.abs(final_ymom)):.6g}')


if __name__ == '__main__':
    main()
