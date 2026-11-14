#!/bin/bash
export PATH=$HOME/.npm-global/bin:$HOME/.local/bin:$PATH
cd /home/cj/my-pele

timeout 600 script -q -c 'deepcode -p "
Complete these Phase 0 tasks for the Pele dual-scenario combustion platform.
The master plan is at /home/cj/pele_cfd_master_plan.md (read section 4.2).

TASK 1 (0.2): Run PeleLMeX FlameSheet
- Build dir: ~/my-pele/external/PeleLMeX/build/Exec/RegTests/FlameSheet
- Copy input.2d-regt from ~/my-pele/external/PeleLMeX/Exec/RegTests/FlameSheet/
- Copy drm19_pmf.dat from same source
- Run: mpirun -n 2 ./PeleLMeX-FlameSheet input.2d-regt
- Check if plotfile generated, report step count

TASK 2 (0.3): Run PeleC zeroD reactor
- Build dir: ~/my-pele/external/PeleC/build/Exec/RegTests/zeroD
- Find input file in ~/my-pele/external/PeleC/Exec/RegTests/zeroD/
- Run with mpirun -n 1
- Report result

TASK 3 (0.4): Write Cantera ignition delay script
- mkdir -p ~/my-pele/test/verification
- Write ~/my-pele/test/verification/ignition_delay.py
- Python cantera, H2/air phi=1.0 T=1200K P=1atm constant volume
- Run it and report ignition delay time

TASK 4 (0.5): AMR sensitivity on HotBubble
- HotBubble dir: ~/my-pele/external/PeleLMeX/build/Exec/RegTests/HotBubble
- Run with amr.max_level=1, then 2, then 3 (edit input.2d-regt each time)
- Record steps, runtime for each

TASK 5 (0.6): my-pele structure
- Check ~/my-pele/ against plan section 3
- Write README.md

After all tasks, write ~/my-pele/PHASE0_REPORT.md with summary.
Work one task at a time.
" --dangerously-skip-permissions' /dev/null 2>&1 | tee /tmp/dc_phase0.log
