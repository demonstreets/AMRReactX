import subprocess,json
from pathlib import Path
jobs=[['python3', '/home/cj/my-pele/tools/analyze_spray_detonation.py', '/home/cj/my-pele/repair_validation/twophase_20260910/detonation_wet_1d_600_tol6_continuation_v3', '/home/cj/my-pele/repair_validation/twophase_20260910/native88_wet_completed_analysis_v4', '--previous-run', '/home/cj/my-pele/repair_validation/twophase_20260910/detonation_wet_1d_600_cublas_cfl10_v1', '--previous-run', '/home/cj/my-pele/repair_validation/twophase_20260910/detonation_wet_1d_600_cpu_continuation_v1', '--previous-run', '/home/cj/my-pele/repair_validation/twophase_20260910/detonation_wet_1d_600_cpu24_continuation_v2'], ['python3', '/home/cj/my-pele/tools/analyze_spray_detonation.py', '/home/cj/my-pele/repair_validation/twophase_20260910/detonation_dry_1d_600_strang_v1', '/home/cj/my-pele/repair_validation/twophase_20260910/native88_dry_strict_completed_analysis_v4']]
status=[]
for cmd in jobs:
 r=subprocess.run(cmd,stdout=subprocess.DEVNULL);status.append({"command":cmd,"exit":r.returncode})
Path('/home/cj/my-pele/repair_validation/twophase_20260910/render_native_final_v4.json').write_text(json.dumps(status,indent=2))
