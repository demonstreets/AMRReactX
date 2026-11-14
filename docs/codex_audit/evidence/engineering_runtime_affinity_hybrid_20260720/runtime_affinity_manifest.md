# Engineering Runtime Affinity Manifest

Status: `PASS`
Generated UTC: `2026-07-20T07:32:51+00:00`
Host: `xiaochun-4028`
Requested ranks x threads: `4` x `2`
Logical CPUs: `56`
MPI launcher: `/usr/bin/mpirun`

## CPU Summary

- Architecture: `x86_64`
- CPU(s): `56`
- Model name: `Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz`
- Thread(s) per core: `2`
- Core(s) per socket: `14`
- Socket(s): `2`
- CPU max MHz: `3300.0000`
- CPU min MHz: `1200.0000`
- NUMA node(s): `2`

## MPI Probe

- rank `0` host `xiaochun-4028` affinity_count `28` affinity `0,1,2,3,4,5,6,7,...`
- rank `1` host `xiaochun-4028` affinity_count `28` affinity `14,15,16,17,18,19,20,21,...`
- rank `2` host `xiaochun-4028` affinity_count `28` affinity `0,1,2,3,4,5,6,7,...`
- rank `3` host `xiaochun-4028` affinity_count `28` affinity `14,15,16,17,18,19,20,21,...`

## Warnings

- none

## Recommended Policy

- mpi: Use scheduler-native launch when available; otherwise record mpirun/mpiexec command and rank count.
- openmp: Set OMP_NUM_THREADS explicitly. For hybrid runs, set OMP_PROC_BIND=spread and OMP_PLACES=cores unless the site scheduler provides a stronger binding policy.
- evidence: Preserve this manifest next to campaign summaries for production handoff.

## Limitations

- This is a runtime/affinity preflight and does not prove CFD numerical accuracy.
- The MPI probe is a lightweight Python launch; it does not replace production-size CFD scaling, scheduler allocation testing, or overnight stability.
- Absence of scheduler environment variables means this evidence was collected from an interactive shell rather than a managed batch allocation.
