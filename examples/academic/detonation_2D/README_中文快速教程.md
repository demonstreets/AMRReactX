# PeleC 二维气相爆轰中文快速教程

目录：`examples/academic/detonation_2D`

这个目录是学术气相爆轰的首选入口，用于 PeleC 二维爆轰波、反应、AMR 计划和 CPU/MPI/MPI+OpenMP 验证。当前学术 GPU smoke 使用 `examples/academic/bench_1gpu`，因为那是仓库已经验证的 PeleC CUDA 入口。

## 0. 从零照做清单

打开这个目录时，先把文件角色分清：

```text
prob.H             problem 类型、参数结构和初始化接口
prob.cpp           初始左右状态、热点/波系初始化、边界/源项等 problem 逻辑
prob_parm.H        prob.* 参数结构，input 中的 prob.* 会读到这里
GNUmakefile        编译入口
Make.package       编译附加文件列表
inputs.codex_*     可复制的爆轰 input 模板
ic.txt             初始条件辅助文件，当前快速教程主要改 input 参数
```

第一次从零跑，不要先改源码，按下面 7 步走：

```bash
cd "$HOME/my-pele"
REPO=$PWD

# 1. 复制一个自己的爆轰 input
cp "$REPO/examples/academic/detonation_2D/inputs.codex_wave_smoke" \
   "$REPO/examples/academic/detonation_2D/inputs.my_detonation_wave"

# 2. 查看核心参数
grep -nE "max_step|stop_time|prob_lo|prob_hi|n_cell|max_level|max_grid_size|plot_int|do_react|chem_integrator|cfl|prob\\." \
  "$REPO/examples/academic/detonation_2D/inputs.my_detonation_wave"

# 3. CPU 串行验证爆轰波
bash tools/codex_smoke_academic_detonation_wave.sh

# 4. 多核 CPU/MPI
MPI_RANKS=4 bash tools/codex_smoke_academic_pelec_mpi.sh

# 5. MPI+OpenMP
MPI_RANKS=2 OMP_NUM_THREADS=2 bash tools/codex_smoke_academic_pelec_hybrid.sh

# 6. PeleC 单 GPU 后端验证
CUDA_VISIBLE_DEVICES=0 SUNDIALS_CUDA_DIR=$HOME/local/sundials-cuda \
bash tools/codex_smoke_academic_pelec_cuda.sh

# 7. AMR 计划验证
bash tools/codex_smoke_academic_pelec_plan_amr.sh
```

如果你要把这个案例改成自己的二维/三维气相爆轰，优先改 input：

```text
max_step / stop_time                      运行步数和终止时间
geometry.prob_lo / geometry.prob_hi       计算域
amr.n_cell                                基础网格
amr.max_level                             AMR 层数，首次建议 0
amr.max_grid_size                         网格块大小，MPI 效率差时需要调整
amr.plot_int                              plotfile 输出间隔
pelec.cfl                                 CFL，强激波/爆轰建议先用 0.2 到 0.3
pelec.do_react                            是否开启反应
pelec.chem_integrator                     反应积分器，真实反应通常用 ReactorCvode
prob.x_split                              初始左右状态分界
prob.p_l / prob.p_r                       左右压力
prob.rho_l / prob.rho_r                   左右密度
prob.T_r                                  右侧温度
```

只有当你要换初始化形式、换源项或加新的诊断量时，才改 `prob.H/prob.cpp/prob_parm.H`。

## 1. 最小文件包

在这个目录中，和从零运行最相关的文件是：

```text
GNUmakefile
Make.package
prob.H
prob.cpp
prob_parm.H
inputs.codex_wave_smoke
inputs.codex_plan_amr_smoke
```

## 2. 准备自己的爆轰 input

```bash
cd "$HOME/my-pele"
REPO=$PWD
cp "$REPO/examples/academic/detonation_2D/inputs.codex_wave_smoke" \
   "$REPO/examples/academic/detonation_2D/inputs.my_detonation_wave"
```

先查看核心参数：

```bash
grep -nE "max_step|stop_time|prob_lo|prob_hi|n_cell|max_level|max_grid_size|plot_int|do_react|chem_integrator|cfl|prob\\." \
  "$REPO/examples/academic/detonation_2D/inputs.my_detonation_wave"
```

第一次只建议改这些：

```text
max_step / stop_time      运行步数和终止时间
amr.n_cell                网格数
amr.max_level             AMR 层数，首次建议 0
amr.plot_int              plotfile 输出间隔
pelec.cfl                 CFL，爆轰初期建议 0.2 到 0.3
prob.x_split              初始左右状态分界位置
prob.p_l / prob.p_r       左右压力
prob.rho_l / prob.rho_r   左右密度
```

## 3. CPU 串行运行

推荐用已验证脚本：

```bash
cd "$HOME/my-pele"
bash tools/codex_smoke_academic_detonation_wave.sh
```

如果要手动运行自己的 input：

```bash
cd "$HOME/my-pele/examples/academic/detonation_2D"
make -j 4 EBASE=codex_deton2d_cpu
CASE_DIR=$PWD
RUN_DIR="${TMPDIR:-/tmp}/my_detonation_cpu_run"
mkdir -p "$RUN_DIR"
cd "$RUN_DIR"
"$CASE_DIR/codex_deton2d_cpu2d.gnu.ex" \
  "$CASE_DIR/inputs.my_detonation_wave"
```

## 4. 多核 CPU/MPI 运行

2 个 MPI rank：

```bash
cd "$HOME/my-pele"
MPI_RANKS=2 bash tools/codex_smoke_academic_pelec_mpi.sh
```

4 个 MPI rank：

```bash
cd "$HOME/my-pele"
MPI_RANKS=4 bash tools/codex_smoke_academic_pelec_mpi.sh
```

手动 MPI：

```bash
cd "$HOME/my-pele/examples/academic/detonation_2D"
make -j 4 USE_MPI=TRUE EBASE=codex_deton2d_mpi
CASE_DIR=$PWD
RUN_DIR="${TMPDIR:-/tmp}/my_detonation_mpi_run"
mkdir -p "$RUN_DIR"
cp inputs.my_detonation_wave "$RUN_DIR/"
cp codex_deton2d_mpi2d.gnu.MPI.ex "$RUN_DIR/"
cd "$RUN_DIR"
mpirun --oversubscribe -np 2 ./codex_deton2d_mpi2d.gnu.MPI.ex inputs.my_detonation_wave
```

## 5. MPI+OpenMP 运行

```bash
cd "$HOME/my-pele"
MPI_RANKS=2 OMP_NUM_THREADS=2 bash tools/codex_smoke_academic_pelec_hybrid.sh
```

## 6. 单 GPU 运行

当前已验证的 PeleC CUDA smoke 在 `examples/academic/bench_1gpu`：

```bash
cd "$HOME/my-pele"
nvidia-smi
CUDA_VISIBLE_DEVICES=0 SUNDIALS_CUDA_DIR=$HOME/local/sundials-cuda \
bash tools/codex_smoke_academic_pelec_cuda.sh
```

如果 SUNDIALS CUDA 安装在别处，把 `$HOME/local/sundials-cuda` 换成实际路径。这个脚本会检查 `include/` 和 `lib/` 是否存在。

## 7. AMR 计划验证

```bash
cd "$HOME/my-pele"
bash tools/codex_smoke_academic_pelec_plan_amr.sh
```

对应 input：

```text
examples/academic/detonation_2D/inputs.codex_plan_amr_smoke
```

## 8. 输出怎么看

常用检查：

```bash
tail -n 80 /tmp/codex_detonation_wave_*/run.log
tail -n 80 /tmp/codex_detonation_wave_*/validation.log
grep -RniE "nan|inf|abort|backtrace|cvode|reactor failed|segmentation" /tmp/codex_detonation_wave_* | tail -n 80
find /tmp/codex_detonation_wave_* -maxdepth 3 -type d -name "plt[0-9][0-9][0-9][0-9][0-9]" | sort | tail
```

通过标准：

```text
run.log 出现目标 STEP
run.log 出现 AMReX finalized
validation.log 通过 validate_detonation_wave.py
plotfile 中有 density、Temp、pressure、rho_H2、rho_O2、rho_H2O 等变量
没有 NaN、Inf、Abort、Backtrace、CVODE failed
```

## 9. 和总教程的关系

更完整的逐步说明见：

```bash
cd "$HOME/my-pele"
sed -n '260,620p' docs/user_guides/从零设置完整算例_工程H2泄漏火灾与学术爆轰.md
```
