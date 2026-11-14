#!/bin/bash
export PATH=/home/cj/.npm-global/bin:/home/cj/.local/bin:/usr/bin:/bin
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY=*** /home/cj

echo "CC_START" 
claude -p '
Complete these Phase 0 tasks for the Pele dual-scenario combustion platform at /home/cj/my-pele/.
Read /home/cj/pele_cfd_master_plan.md Section 4.2 for context.

TASK 0.2: Run PeleLMeX FlameSheet
- The pmf data file is needed. Find drm19_pmf.dat and copy it to the build dir.
- Build dir: ~/my-pele/external/PeleLMeX/build/Exec/RegTests/FlameSheet
- Source: ~/my-pele/external/PeleLMeX/Exec/RegTests/FlameSheet/
- Run: mpirun -n 2 ./PeleLMeX-FlameSheet input.2d-regt

TASK 0.3: Run PeleC zeroD
- This is a 0D reactor test with LiDryer mechanism
- Build dir: ~/my-pele/external/PeleC/build/Exec/RegTests/zeroD
- Source: ~/my-pele/external/PeleC/Exec/RegTests/zeroD/
- Find and run with correct input file

TASK 0.4: Write Cantera ignition delay script
- Write to ~/my-pele/test/verification/ignition_delay.py
- Use Python cantera to compute H2/air 0D constant-volume ignition delay at T=1200K, P=1atm, phi=1.0
- Print the result

Work one task at a time. After each task, report status.
' --model claude-sonnet --max-turns 20 2>&1
