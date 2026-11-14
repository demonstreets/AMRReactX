# AGENTS.md — PeleLMeX / AMReX 项目笔记

## EB2 多圆柱 MPI 死锁修复（2026-06-28）

### 问题
c3h8_flacs_mpi 算例，3圆柱 EB + MPI 多核运行时在 EB 初始化阶段死锁。

### 根因
AMReX_EB2_Level.H 中 GShopLevel::define_fine 的迭代修复循环中，
直接调用 ls.FillBoundary(geom.periodicity())。
当某个 MPI rank 的 MultiGFab 有空盒（local_size()==0）时，
FillBoundary 内部 MPI 通信死等不存在的邻居数据。

### 修复（3行新增）
文件: Src/EB/AMReX_EB2_Level.H 第612-618行

原代码:
    } else {
        auto ls = m_mgf.getLevelSet();
        ls.FillBoundary(geom.periodicity());

修复后:
    } else {
        auto ls = m_mgf.getLevelSet();
        bool has_local = (ls.local_size() > 0);
        bool all_have = has_local;
        ParallelAllReduce::And(all_have, ParallelContext::CommunicatorSub());
        if (all_have) {
            ls.FillBoundary(geom.periodicity());
        }

同样修复: Src/EB/AMReX_EB2_Level.cpp buildCellFlag() 第403行

### 验证矩阵（全部通过）
2核10步/4核10步/4核20步/8核10步/4核AMR10步/8核AMR10步/4核AMR20步/8核AMR50步(开初始投影)
16核 AMR 会 OOM（125GB不够），非死锁。

### 关键路径
算例: ~/my-pele/examples/engineering/c3h8_flacs_mpi/
源码: ~/my-pele/external/PeleLMeX/Submodules/PelePhysics/Submodules/amrex/Src/EB/
编译: make USE_MPI=TRUE -j8
运行: OMP_NUM_THREADS=1 mpirun -np N ./PeleLMeX3d.gnu.MPI.ex input.3d amr.max_step=N peleLM.les_model=None

### 注意事项
- 初始投影(initialProjection)有独立概率性死锁，可加 peleLM.do_init_proj=0 绕过
- 退出时的 Segfault 是 MPI_Finalize 析构顺序问题，不影响结果


---

# AGENTS.md — PeleC 2D 爆轰胞格 GPU 算例调试 (2026-07-01)

## 算例概要
- 目录: ~/my-pele/examples/academic/detonation_hotspot/
- 域: 30×10×0.16 cm, 600×200×16 网格
- 初始: 背景 20 kPa/300K H2/O2，4个热点 x=0/y=1.5,3.5,5.5,8.0 cm/r=3mm
- 热点参数: p=1.8 MPa, T=2214 K, u=2840 m/s, 100% H2O
- BC: 左/上/下 NoSlipWall, 右 FOExtrap, z 周期
- 化学: LiDryer 9组分, CVODE sparse_direct (GPU)
- 二进制: PeleC3d.gnu.CUDA.ex (231MB, CUDA 12.6 + SUNDIALS-CUDA)

## GPU 编译关键配置
GNUmakefile 必须包含:
```
USE_CUDA = TRUE
CUDA_ARCH = 60              # ← P100 = compute_60, 缺失导致反应器初始化崩溃
CUDA_HOME = /home/cj/local/cuda-12.6  # ← 缺失导致 nvcc 用错版本
PELE_CVODE_FORCE_YCORDER = TRUE
USE_EXPLICIT_REACT = TRUE
```
LD_LIBRARY_PATH 必须含: $HOME/local/cuda-12.6/targets/x86_64-linux/lib:$HOME/local/sundials-cuda/lib

## 常见 BUG 及修复

### 1. do_react=0 静默关闭反应 🔴
inputs 中如果有两个 `pele.do_react` 行，ParmParse 取最后一个。
症状: CVODE t=0 flag=-4，即使热点初值正确也会崩。
修复: 确保只有一行 `pele.do_react = 1`

### 2. 背景 UMX 误设为热点值 🔴
prob.H pc_initdata 的 else(背景)分支，UMX 必须 = 0.0，不能复制热点分支的 rho_hot*u_hot。
症状: 整个域 Mach 131 → 通量计算 NaN。
修复: `state(i,j,k,UMX) = 0.0;`

### 3. 热点组分 N2 违反元素守恒
纯 H2/O2 反应没有 N2，热点用 100% H2O 即可。
修复: `mf_hot[H2O_ID] = 1.0;`

### 4. 压力单位混淆
PeleC EOS (PYT2R/RYP2E) 使用 CGS 单位 (dyn/cm²)，inputs 必须用 CGS。
20 kPa = 2.0e5 dyn/cm², 1.8 MPa = 1.8e7 dyn/cm²

### 5. 增量编译 vs 全量重编
- 改 prob.H → 触发所有 PeleC 源文件重编 (~20个, nvcc×, 10-15min)
- 只改 prob.cpp → 只重编 prob.cpp + 链接 (2-3min)
- 改 inputs → 不需重编
- 利用已有 tmp_build_dir 缓存可避免重编 AMReX/PeLePhysics

## CVODE solve_type 在 GPU 上的选项
| solve_type | GPU 可用? | 备注 |
|-----------|----------|------|
| sparse_direct | ✅ | 需要 KLU 库，GPU SUNDIALS 带 KLU |
| dense_direct | ❌ | PeleC GPU 不支持 |
| fixed_point | ✅ (但不推荐) | 易 CVODE flag=-4 |
| GMRES | ✅ | 已知在 GPU 上挂死 |
| precGMRES | 需 YCorder | 未验证 |
| custom_direct | ❌ | 求解器内核被注释(BUG) |

## GPU vs CPU CVODE 行为差异
- GPU: 批量模式，所有单元打包为一个大 ODE 系统，单点失败全局崩溃
- CPU: 逐单元独立求解，一个单元崩其他继续

## 文件位置
- detonation_hotspot: ~/my-pele/examples/academic/detonation_hotspot/
- ZND 参考: ~/my-pele/examples/academic/detonation_znd_gpu/
- PeleC 源码: ~/my-pele/external/PeleC/
- 调试记录: ~/my-pele/examples/academic/detonation_hotspot/DEBUG_LOG.md

🔴 不确定的功能参数请查源码后再确认，严禁瞎编（2026-07-05）

涉及 PeleLMeX/PeleC 的 input 参数、GNUmakefile 编译选项、API 开关时：
1. 不知道参数是否存在 → grep pp.query <Source/*.cpp> 先查源码
2. 不知道参数默认值 → 看 Setup.cpp 中的赋值
3. 不知道编译选项是否支持 → 看 GNUmakefile 或 Make.PeleLMeX
4. 严禁凭空编一个参数写进 inputs（案例：do_diffuse_spec/do_diffuse_temp 在 PeleLMeX 中不存在）
