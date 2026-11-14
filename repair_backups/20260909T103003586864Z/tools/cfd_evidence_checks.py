"""Physical checks shared by CFD evidence writers. No solver execution."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np


def pressure_front_x(pressure, x):
    """Locate a right-moving compressive pressure front, never a T maximum.

    This diagnostic alone does not establish a self-sustained detonation.
    Multi-front/cellular runs require time-resolved tracking and references.
    """
    p = np.asarray(pressure, dtype=float)
    x = np.asarray(x, dtype=float)
    if p.shape[0] != x.size or x.size < 4 or not np.all(np.isfinite(p)):
        raise ValueError('invalid pressure profile or grid for shock tracking')
    if not np.all(np.diff(x) > 0):
        raise ValueError('shock tracking requires increasing x coordinates')
    profile = p.mean(axis=tuple(range(1, p.ndim))) if p.ndim > 1 else p
    contrast = float(np.max(profile) - np.min(profile))
    scale = max(float(np.max(np.abs(profile))), 1.0e-300)
    if contrast <= 1.0e-3 * scale:
        raise ValueError('no resolved pressure front: pressure is essentially uniform')
    compression = -np.diff(profile) / np.diff(x)
    index = int(np.argmax(compression))
    if compression[index] <= 0:
        raise ValueError('no right-moving compressive pressure front')
    # The discontinuity lies between adjacent cell centers. This diagnostic
    # deliberately keeps its half-cell resolution instead of claiming a
    # subcell location from a temperature plateau.
    return float(0.5 * (x[index] + x[index + 1]))


def archived_chemistry(plotfile):
    """Read run chemistry from job_info, not today's case Makefile.

    Current mechanism source is an additional cross-check. A positive count
    alone is not binary provenance, kinetics validation, or reaction proof.
    A zero count positively disqualifies reacting-flow certification.
    """
    plotfile = Path(plotfile)
    job = plotfile / 'job_info'
    text = job.read_text(encoding='utf-8', errors='replace')
    match = re.search(r'^\s*CHEMISTRY:\s*(\S+)\s*$', text, re.M)
    if not match:
        raise ValueError(f'job_info does not identify chemistry: {job}')
    name = match.group(1)
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', name):
        raise ValueError(f'invalid chemistry name in {job}')
    root = Path(__file__).resolve().parents[1]
    source = root / 'external/PeleC/Submodules/PelePhysics/Mechanisms' / name / 'mechanism.H'
    raw = source.read_bytes()
    count = re.search(rb'^\s*#define\s+NUM_GAS_REACTIONS\s+(\d+)', raw, re.M)
    if not count:
        raise ValueError(f'mechanism reaction count unavailable: {source}')
    return {'name': name, 'gas_reactions': int(count.group(1)),
            'job_info': str(job), 'mechanism_source': str(source),
            'source_sha256': hashlib.sha256(raw).hexdigest(),
            'binary_provenance_verified': False}


def reacting_pair_metrics(initial, final):
    """Require complete raw fields and chemical conversion in a closed window.

    Intended for the short, initially hot H2/O2 benchmark runtime checks.
    Advective redistribution of H2O or an initialized hot spot is insufficient.
    For open windows a measured boundary/source budget is required instead.
    """
    import amrex_reader
    p0, p1 = (amrex_reader.read_plotfile(str(path)) for path in (initial, final))
    if not p1['time'] > p0['time']:
        raise ValueError('plotfile time did not advance')
    f0, f1 = p0['fields'], p1['fields']
    for fields in (f0, f1):
        for name, values in fields.items():
            if not np.all(np.isfinite(values)):
                raise ValueError(f'non-finite raw field: {name}')
        for name in ('density', 'Temp'):
            if name not in fields or np.min(fields[name]) <= 0:
                raise ValueError(f'missing or nonpositive raw field: {name}')
        if 'volFrac' in fields and np.any(np.asarray(fields['volFrac']) < 1.0):
            raise ValueError('this closed regular-grid benchmark check does not support EB cells')
    rho0, rho1 = np.asarray(f0['density']), np.asarray(f1['density'])
    if rho0.shape != rho1.shape or not np.allclose(p0['dx'], p1['dx'], rtol=0, atol=0):
        raise ValueError('initial/final benchmark grids differ')
    temp0 = np.asarray(f0['Temp'])
    if float(np.max(temp0)) <= float(np.min(temp0)) + 50.0:
        raise ValueError('hotspot absent in raw initial temperature field (cold-flow false pass)')
    species = ('H2', 'O2', 'H2O', 'H', 'O', 'OH', 'HO2', 'H2O2', 'N2')
    sums = []
    for fields, rho in ((f0, rho0), (f1, rho1)):
        values = []
        for name in species:
            if 'rho_' + name in fields:
                y = np.asarray(fields['rho_' + name]) / rho
            elif f'Y({name})' in fields:
                y = np.asarray(fields[f'Y({name})'])
            else:
                raise ValueError(f'raw species field missing: {name}')
            if np.min(y) < -1.0e-12 or np.max(y) > 1 + 1.0e-12:
                raise ValueError(f'unphysical mass fraction {name}: [{np.min(y)}, {np.max(y)}]')
            values.append(y)
        closure = float(np.max(np.abs(sum(values) - 1)))
        if closure > 1.0e-10:
            raise ValueError(f'species closure error: {closure}')
        sums.append({name: float(np.sum(rho * y)) for name, y in zip(species, values)})
    mass0, mass1 = float(np.sum(rho0)), float(np.sum(rho1))
    mass_rel = abs(mass1 - mass0) / mass0
    if mass_rel > 1.0e-6:
        raise ValueError('nonclosed mass budget: provide measured boundary/source fluxes')
    fuel_loss = (sums[0]['H2'] - sums[1]['H2']) / max(sums[0]['H2'], 1.0e-300)
    water_gain = (sums[1]['H2O'] - sums[0]['H2O']) / mass0
    if fuel_loss <= 1.0e-8 or water_gain <= 1.0e-8:
        raise ValueError(f'no resolved chemical conversion: H2 loss={fuel_loss}, H2O gain={water_gain}')
    return {'initial_temp_max': float(np.max(temp0)), 'fuel_consumed_fraction': fuel_loss,
            'water_mass_gain_fraction': water_gain, 'mass_relative_change': mass_rel,
            'detonation_propagation_verified': False,
            'scope': 'hot initialized H2/O2 chemical-conversion runtime check only'}
