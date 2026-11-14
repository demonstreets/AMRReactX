# 01 - bench_1gpu：H₂/O₂ 4热点爆轰（单GPU）

## 基本配置
| 项目 | 设置 |
|------|------|
| 求解器 | PeleC（可压缩） |
| 并行 | **单 GPU** (USE_CUDA=TRUE, USE_MPI=FALSE) |
| GPU | 1×P100 16GB |
| 域 | 30×10×0.16 cm, 600×200×16 = 192万网格 |
| 机理 | H₂/O₂ LiDryer (9组分) |
| 化学 | **ReactorRK64（显式）** |
| 离散 | PLM 2阶 (ppm_type=0, plm_iorder=2, flattening=1) |
| CFL | 0.1 |
| 起爆 | 4热点：p=6.08e6 CGS, T=2000K, u=2.0e5 |
| 热点位置 | y=1.5, 4.0, 6.5, 8.5 |

## 结果
- **状态**：✅ 完成
- **步数**：50000 步
- **耗时**：76.3 秒
- **输出**：plt00000~plt05000（每 200 步出图）
- **稳定性**：无 NaN，无崩溃，正常结束

## 路径
`~/my-pele/examples/academic/bench_1gpu/`
