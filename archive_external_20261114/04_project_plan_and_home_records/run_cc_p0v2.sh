#!/bin/bash
export PATH=/home/cj/.npm-global/bin:/home/cj/.local/bin:/usr/bin:/bin
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY=*** /home/cj

echo "=== CC Phase 0 Start ===" 

claude --dangerously-skip-permissions -p '
You are on a Linux server at /home/cj/my-pele/.
Read /home/cj/pele_cfd_master_plan.md section 4.2 for the Phase 0 task list.

Complete these 3 tasks ONE AT A TIME:

TASK 1 (0.2): Run PeleLMeX FlameSheet
- cd ~/my-pele/external/PeleLMeX/build/Exec/RegTests/FlameSheet
- cp ~/my-pele/external/PeleLMeX/Exec/RegTests/FlameSheet/input.2d-regt .
- cp ~/my-pele/external/PeleLMeX/Exec/RegTests/FlameSheet/drm19_pmf.dat .
- mpirun -n 2 ./PeleLMeX-FlameSheet input.2d-regt
- Check if plt* files are generated, report final step count

TASK 2 (0.3): Run PeleC zeroD reactor
- cd ~/my-pele/external/PeleC/build/Exec/RegTests/zeroD
- Find input file at ~/my-pele/external/PeleC/Exec/RegTests/zeroD/
- mpirun -n 1 ./PeleC-zeroD <input_file>
- Report result

TASK 3 (0.4): Write Cantera ignition delay script
- mkdir -p ~/my-pele/test/verification
- Write ~/my-pele/test/verification/ignition_delay.py
- Use Python cantera, H2/air, T=1200K, P=1atm, phi=1.0, constant volume
- Run and report the ignition delay time

After all 3 tasks, write summary to ~/my-pele/PHASE0_CC_REPORT.md
' --model claude-sonnet --max-turns 25 < /dev/null 2>&1

echo "=== CC DONE ==="
