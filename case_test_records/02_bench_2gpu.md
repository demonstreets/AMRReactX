# 02 - bench_2gpu：H₂/O₂ 4热点爆轰（双GPU MPI）

## 基本配置
| 项目 | 设置 |
|------|------|
| 求解器 | PeleC |
| 并行 | **2 GPU MPI** (USE_MPI=TRUE, USE_CUDA=TRUE) |
| 域 | 同 bench_1gpu（192万网格） |
| 机理 | H₂/O₂ LiDryer (9组分) |
| 化学 | ReactorRK64（显式） |
| CFL | 0.1 |

## 结果
- **状态**：✅ 完成
- **耗时**：168.5 秒
- **结论**：双 GPU 比单 GPU 慢（MPI 通信开销 > 并行收益，网格太小）

## 路径
`~/my-pele/examples/academic/bench_2gpu/`
