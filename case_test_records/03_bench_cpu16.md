# 03 - bench_cpu16：H₂/O₂ 4热点爆轰（CPU 16核）

## 基本配置
| 项目 | 设置 |
|------|------|
| 求解器 | PeleC |
| 并行 | **16 CPU MPI** (USE_MPI=TRUE, USE_CUDA=FALSE) |
| 域 | 同 bench_1gpu（192万网格） |
| 机理 | H₂/O₂ LiDryer (9组分) |
| 离散 | PLM 2阶 |

## 尝试记录

### 尝试 1：CVODE + dense_direct
- **配置**：USE_EXPLICIT_REACT=FALSE, ReactorCvode, dense_direct
- **结果**：❌ 崩溃
- **原因**：CVODE 初始化后静默退出，0 步。SUNDIALS MPI_Barrier 补丁已应用但仍失败
- **耗时**：825秒（无有效产出）

### 尝试 2：RK64 显式
- **配置**：USE_EXPLICIT_REACT=TRUE, ReactorRK64
- **结果**：⚠️ 部分成功
- **步数**：100 步 / 819 秒（~8.2 秒/步）
- **后续**：5000 步需求估算 ~11 小时，暂停

### 尝试 3：CVODE + WENO 冲突
- **报错**：`ppm_type must be 1 (PPM) to use WENO method`
- **原因**：inputs 中 use_hybrid_weno=1 但 ppm_type=0
- **修复**：关闭 WENO → 重跑成功

## 结论
- CPU 16 核 CVODE 不可靠（死锁/崩溃）
- CPU 显式 RK 慢但稳定（~5000× 比 GPU 慢）
- 爆轰场景 GPU 是唯一可行路线

## 路径
`~/my-pele/examples/academic/bench_cpu16/`
