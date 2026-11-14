#!/usr/bin/env python3
"""Check one completed solver log and its recorded process exit code."""
import argparse
from pathlib import Path
import re


def check_log(log, exit_code):
    if int(exit_code) != 0:
        raise ValueError(f'process exited with code {exit_code}')
    text=Path(log).read_text(errors='replace')
    patterns=(r'amrex::(?:Abort|Error)', r'Assertion.*failed', r'SIG(?:ABRT|SEGV|FPE)',
              r'Simulation stopped early',r'NaNs detected in the Solution',
              r'CVODE[^\n]*(?:failed|failure|flag\s*=\s*-\d+)',
              r'CUDA[^\n]*(?:illegal memory access|out of memory|error\s*[:=])')
    for pattern in patterns:
        match=re.search(pattern,text,re.I)
        if match: raise ValueError(f'current run has fatal marker: {match.group(0)}')
    if not re.search(r'AMReX[^\n]*finalized',text):
        raise ValueError('normal AMReX finalization marker absent')
    return 'PASS process/log health only; raw-field physical checks still required'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--log',type=Path,required=True)
    p.add_argument('--exit-code',type=int,required=True)
    a=p.parse_args()
    try: print(check_log(a.log,a.exit_code))
    except ValueError as e: raise SystemExit('FAIL: '+str(e))


if __name__=='__main__':main()
