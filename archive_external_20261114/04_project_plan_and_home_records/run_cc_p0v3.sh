#!/bin/bash
export PATH=/home/cj/.npm-global/bin:/home/cj/.local/bin:/usr/bin:/bin
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY=***

cd /home/cj

echo "=== CC Phase 0 Start ===" 

claude --dangerously-skip-permissions -p '
You are on a Linux server at /home/cj/my-pele/.
Read /home/cj/pele_cfd_master_plan.md section 4.2 for Phase 0 tasks.

Complete these 3 tasks ONE AT A TIME:

TASK 1 (0.2 Run PeleLMeX FlameSheet):
  cd ~/my-pele/external/PeleLMeX/build/Exec/RegTests/FlameSheet
  cp ~/my-pele/external/PeleLMeX/Exec/RegTests/FlameSheet/input.2d-regt .
  cp ~/my-pele/external/PeleLMeX/Exec/RegTests/FlameSheet/drm19_pmf.dat .
  mpirun -n 2 ./PeleLMeX-FlameSheet input.2d-regt
  Check plotfile output, report final step count

TASK 2 (0.3 Run PeleC zeroD):
  cd ~/my-pele/external/PeleC/build/Exec/RegTests/zeroD
  ls ~/my-pele/external/PeleC/Exec/RegTests/zeroD/ to find input file
  mpirun -n 1 ./PeleC-zeroD <input_file>
  Report result

TASK 3 (0.4 Cantera ignition delay):
  mkdir -p ~/my-pele/test/verification
  Write Python script to ~/my-pele/test/verification/ignition_delay.py
  Compute H2/air 0D constant-volume ignition delay (T=1200K, P=1atm, phi=1.0)
  Run: python3 ~/my-pele/test/verification/ignition_delay.py
  Report ignition delay time

After ALL 3 tasks done, write a summary to ~/my-pele/PHASE0_CC_REPORT.md
' --model claude-sonnet --max-turns 25 < /dev/null 2>&1

echo "=== CC DONE ==="
