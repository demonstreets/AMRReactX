# Phase 0 Completion Report

**Date:** 2026-06-08 (Refresh)
**Project:** Pele 双场景燃烧模拟平台
**Status:** Phase 0 ✅ 全部任务完成

---

## 任务 0.1 — 编译上游代码（Pre-Phase 已完成）

所有上游代码已在 workstation 上编译通过：
- AMReX 26.05
- PelePhysics
- PeleLMeX (13 个可执行文件, 2D+LowMach Release)
- PeleC (31 个可执行文件, 2D Release)
- SUNDIALS 6.7.0 (~/.local)

---

## 任务 0.2 — PeleLMeX FlameSheet 算例验证

| 项目 | 值 |
|------|-----|
| **位置** | `external/PeleLMeX/build/Exec/RegTests/FlameSheet/` |
| **运行** | `mpirun -n 2 ./PeleLMeX-FlameSheet input.2d-regt` |
| **结果** | ✅ 成功完成 **20 步** |
| **壁钟时间** | ~27 s (2 ranks) |
| **输出** | `plt00000`, `plt00020` |
| **配置** | 2D 槽道火焰面，DRM19 机理 (21 species)，32×64 基网格，2 级 AMR，SDC 2 次迭代，ReactorCvode |
| **最终物理时间** | 6.8 × 10⁻⁹ s |

---

## 任务 0.3 — PeleC zeroD 反应器验证

| 项目 | 值 |
|------|-----|
| **位置** | `external/PeleC/build/Exec/RegTests/zeroD/` |
| **运行** | `mpirun -n 1 ./PeleC-zeroD zerod-1.inp` |
| **结果** | ✅ 成功运行至 `stop_time = 0.001 s` |
| **步数** | 13,257 |
| **壁钟时间** | 12.87 s |
| **输出** | `plt13257` (及每 100 步中间文件) |
| **配置** | H₂/O₂/N₂ (Y=0.06/0.5/0.44), T=1000K, P=10 atm, 8³ 网格, no AMR, ReactorRK64, SDC 2 iters |

---

## 任务 0.4 — Cantera 点火延迟比对

| 项目 | 值 |
|------|-----|
| **脚本** | `test/verification/ignition_delay_h2.py` |
| **条件** | H₂/air, φ=1.0, T=1200K, P=1 atm, 定容 |
| **机理** | h2o2.yaml (Burke et al., 10 species, 29 reactions) |

**结果:**
- 点火延迟 (max dT/dt): **4.42 × 10⁻⁵ s (44.2 μs)**
- 点火温度: 1591 K
- 峰值温度: 1600 K
- 峰值 dT/dt: 1.52 × 10⁸ K/s
- 计算时间: 0.89 s, 833 步

---

## 任务 0.5 — AMR 敏感性实验 (HotBubble)

| 项目 | 值 |
|------|-----|
| **位置** | `external/PeleLMeX/build/Exec/RegTests/HotBubble/` |
| **运行** | `mpirun -n 2 ./PeleLMeX-HotBubble input.2d-regt.levelN` |
| **配置** | 32×64 基网格, ref_ratio=2, 热气泡 (T_bubble=450K), stop_time=0.1s |
| **Tagging** | temp > 350K + gtemp adjacent_difference > 10 |

| amr.max_level | 步数 | 壁钟时间 (s) | 最终 dt (s) | 最大网格数 | 相对耗时 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 55 | 1.54 | 8.68 × 10⁻⁴ | 5,120 | 1× |
| 2 | 106 | 6.75 | 4.84 × 10⁻⁴ | 16,384 | 4.4× |
| 3 | 223 | 37.9 | 1.90 × 10⁻⁴ | 39,424 | 24.6× |

**关键观察:**
- 每加一级 AMR: 步数约×2, 网格约×3-4, 耗时约×4-6
- Level-2 在精度/成本间平衡最佳
- Level-3 网格 39K 已占 ~7.7× 基网格量, dt 降为 1/4, 成本上升 ~25×

---

## 任务 0.6 — my-pele 目录结构

- **external/:** amrex, PelePhysics, PeleLMeX, PeleC ✅
- **src/:** common, geometry, engineering, academic ✅ (空目录就绪)
- **test/:** unit, regression, verification ✅ (含 Cantera 验证脚本)
- **examples/:** engineering, academic ✅
- **docs/:** theory, user_guide, reviews/single_module, reviews/integration ✅
- **CHECKPOINTS/:** checkpoint-000.md ✅
- **README.md:** 已更新 ✅
- **PROGRESS.md:** 已存在 ✅

---

## 出口检查清单 (Phase 0 Gate Review)

| 检查项 | 状态 | 备注 |
|--------|:----:|------|
| CMake 可编译通过 | ✅ | AMReX + PelePhysics + PeleLMeX + PeleC |
| PeleLMeX 算例可复现 | ✅ | FlameSheet (20 步) + HotBubble (3 级 AMR) |
| PeleC 算例可复现 | ✅ | zeroD (13257 步) |
| Cantera 比对验证 | ✅ | H₂/air, τ=44.2 μs @ 1200K/1atm/φ=1 |
| my-pele/ 目录结构完整 | ✅ | 对照 Section 3.2 |
| README.md | ✅ | 已更新 |

---

## 环境快照

| 组件 | 版本/信息 |
|------|-----------|
| OS | Ubuntu 24.04 LTS |
| 内核 | Linux 6.14.0-37-generic x86_64 |
| 编译器 | GCC 13.2.0 |
| MPI | OpenMPI (系统安装) |
| Python | 3.12.3 + Cantera 3.2.0 |
| SUNDIALS | 6.7.0 (~/.local, 32-bit, CVODE) |
| AMReX | 26.05 |
| PeleLMeX | main (含 AMReX-Hydro 9446740) |
| PeleC | main |
| PelePhysics | main |

---

## 下一步 (Phase 1: 几何处理管线)

1. STL 解析器（ASCII + 二进制）
2. Signed distance function 生成
3. AMReX EB2 GeometryShop 构建
4. 边界条件标签系统
5. 简单几何验证（球/圆柱绕流）
