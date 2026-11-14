"""Validated uniform-grid checkpoint refinement with unchanged physical parcels.

Native AMReX reads and writes each MultiFab. Text geometry metadata is checked
against the supported single-level 2-D Cartesian checkpoint grammar. This is a
controlled restart sensitivity test, not a refined calculation of the past flow.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('destination', type=Path)
p.add_argument('--ratio', type=int, choices=[1,2], required=True)
p.add_argument('--tool', type=Path, required=True)
p.add_argument('--audit', type=Path, required=True)
a = p.parse_args()
source, destination = a.source.resolve(), a.destination.resolve()
assert source != destination and not destination.exists()
assert destination.is_relative_to(Path('/dev/shm/my_pele_thermal_model_20260911'))
ratio = a.ratio
header = (source/'Header').read_text()
lines = header.splitlines()
assert lines[0] == 'CheckPointVersion_1.0' and lines[1] == '2'
assert lines[3] == '0' and lines[4] == '0'
checkpoint_time = float(lines[2])
pattern = re.compile(r'\(\((-?\d+),(-?\d+)\)\s*\((-?\d+),(-?\d+)\)\s*\((\d+),(\d+)\)\)')
boxes = []
def replace_box(match):
    xlo,ylo,xhi,yhi,tx,ty = map(int, match.groups())
    assert tx == ty == 0 and min(xlo,ylo) >= 0
    boxes.append([xlo,ylo,xhi,yhi])
    return f'(({xlo*ratio},{ylo*ratio}) ({(xhi+1)*ratio-1},{(yhi+1)*ratio-1}) (0,0))'
new_header = pattern.sub(replace_box, header)
assert len(boxes) == 61, len(boxes)
assert max(x[2] for x in boxes) == 2799 and max(x[3] for x in boxes) == 799
coordinate_pattern = re.compile(r'\(0 \(0,0\)\(([^,()]+),([^()]+)\) 1\)')
def replace_coordinate(match):
    dx,dy = map(float, match.groups())
    assert abs(dx-.005) < 1e-15 and abs(dy-.005) < 1e-15
    return f'(0 (0,0)({dx/ratio:.17g},{dy/ratio:.17g}) 1)'
new_header, count = coordinate_pattern.subn(replace_coordinate,new_header)
assert count == 2
# Keep physical state times and step numbers. A new CFL estimate limits the next step.
prefixes = re.findall(r'^Level_0/SD_\d+_New_MF$',header,re.M)
assert prefixes == ['Level_0/SD_0_New_MF','Level_0/SD_1_New_MF']
assert not re.findall(r'Level_[1-9]|_Old_MF',header)
destination.mkdir(parents=True)
(destination/'Level_0').mkdir()
(destination/'Header').write_text(new_header)
for name in ['CPUtime','EBMaxLevel','PeleCHeader','FabArrayHeaders.txt']:
    shutil.copyfile(source/name,destination/name)
assert (source/'EBMaxLevel').read_text().strip() == '0'
results = []
for prefix in prefixes:
    cmd = [str(a.tool), 'source='+str(source/prefix), 'destination='+str(destination/prefix),
           'ratio='+str(ratio)]
    q = subprocess.run(cmd,capture_output=True,text=True)
    log = destination/(Path(prefix).name+'_prolongation.log')
    log.write_text(q.stdout+q.stderr)
    assert q.returncode == 0,q.stderr
    line = next(s for s in q.stdout.splitlines() if s.startswith('PROLONGATION_RESULT '))
    result = json.loads(line[len('PROLONGATION_RESULT '):])
    assert result['coarse_cells'] == 2800*800 and result['fine_cells'] == 2800*800*ratio*ratio
    results.append(result)
assert [x['components'] for x in results] == [13,8]
(destination/'particles/Level_0').mkdir(parents=True)
shutil.copyfile(source/'particles/Header',destination/'particles/Header')
particle_boxes = (source/'particles/Level_0/Particle_H').read_text()
new_particle_boxes, count = pattern.subn(replace_box,particle_boxes)
assert count == 14
(destination/'particles/Level_0/Particle_H').write_text(new_particle_boxes)
particle_files = []
for f in (source/'particles/Level_0').glob('DATA_*'):
    target = destination/'particles/Level_0'/f.name
    shutil.copyfile(f,target)
    old_hash,new_hash = [hashlib.sha256(p.read_bytes()).hexdigest() for p in [f,target]]
    assert old_hash == new_hash
    particle_files.append({'file':f.name,'sha256':old_hash,'bytes':f.stat().st_size})
assert particle_files
audit = {'source':str(source),'destination':str(destination),'ratio':ratio,
         'source_header_sha256':hashlib.sha256((source/'Header').read_bytes()).hexdigest(),
         'destination_header_sha256':hashlib.sha256((destination/'Header').read_bytes()).hexdigest(),
         'time_s':checkpoint_time,'multifabs':results,'particle_data_unchanged':particle_files,
         'parcel_positions_ids_weights_and_internal_state':'Unchanged byte-for-byte; native restart redistributes grids.',
         'physical_domain_and_effective_depth':'Unchanged; do not rescale parcel weights with the new grid spacing.',
         'scope':'Conservative piecewise-constant refinement of an existing state; prior coarse trajectory is not recomputed.'}
a.audit.parent.mkdir(parents=True,exist_ok=True)
a.audit.write_text(json.dumps(audit,indent=2))
print(json.dumps(audit,indent=2))
