# CUDA Revalidation Report

- Status: `PASS-MASTER-PLAN-CUDA-REVALIDATION`
- Revalidation script ready: `True`
- Current CUDA preflight ready: `True`
- Require-CUDA reproducible gate ready: `True`
- Current runtime blocker: ``

## Post-Recovery Command

`SUNDIALS_CUDA_DIR=<cuda-capable-sundials> PATH=<cuda-bin>:$PATH LD_LIBRARY_PATH=<sundials-lib>:<cuda-lib64>:$LD_LIBRARY_PATH bash tools/run_master_plan_cuda_revalidation.sh`

## Optional Long Engineering Command

`CODEX_CUDA_REVALIDATION_RUN_ENGINEERING_LONG=1 SUNDIALS_CUDA_DIR=<cuda-capable-sundials> PATH=<cuda-bin>:$PATH LD_LIBRARY_PATH=<sundials-lib>:<cuda-lib64>:$LD_LIBRARY_PATH bash tools/run_master_plan_cuda_revalidation.sh`
