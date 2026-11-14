# PeleC/PeleLMeX 算例测试记录

> 记录日期：2026-07-03  
> 服务器：192.168.31.147 (cj, SSH密钥)  
> GPU：4×P100 16GB | CPU：56核 Xeon, 125GB RAM  
> CUDA 12.6 | SUNDIALS-CUDA | g++ 13.3

---

## 索引

| 编号 | 算例 | 求解器 | 物理 | 状态 | 并行 |
|------|------|--------|------|------|------|
| 01 | bench_1gpu | PeleC | H₂/O₂ 4热点爆轰 | ✅ | 1 GPU |
| 02 | bench_2gpu | PeleC | H₂/O₂ 4热点爆轰 | ✅ | 2 GPU MPI |
| 03 | bench_cpu16 | PeleC | H₂/O₂ 4热点爆轰 | ⚠️ | 16 CPU MPI |
| 04 | spray_heptane_1gpu | PeleC | 庚烷喷雾+EB热壁 | ⏸️ | 1 GPU |
| 05 | spray_combust_3d | PeleLMeX | C12H23喷雾自燃 | 🔄 | 1 GPU |
| 06 | c3h8_leak | PeleLMeX | C₃H₈泄漏扩散+EB+k-ε | ✅ | 1 GPU / CPU |

## 关键教训

### PeleLMeX GPU 兼容性
| 组合 | 结果 |
|------|------|
| EB + 反应 + 湍流 | ✅ 正常 |
| EB + 喷雾（无反应） | ❌ CUDA 700 |
| CVODE + 21组分 | ❌ 显存溢出 |
| RK64 + 21组分 | 🔄 测试中 |

### 机理教训
- `heptane_3sp`/`decane_3sp` = 无反应机理（仅蒸发专用）
- 最小反应机理：`heptane_fc` (~50组分)
- 自定义机理：Chemkin → ck2yaml → Fuego → C++

### 编译教训
- 机理切换 = 全量重编
- PeleLMeX CUDA 首次编译 ~100min, CPU ~15min
