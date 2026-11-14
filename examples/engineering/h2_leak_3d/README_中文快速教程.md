# H2 泄漏、扩散、管廊着火中文快速教程

目录：`examples/engineering/h2_leak_3d`

这个目录是工程场景的首选入口，用于开放区域或管廊中的 H2 泄漏、扩散、可燃云团和着火测试。第一次使用时不要直接改模板 input，先复制一份自己的 input。

## 0. 从零照做清单

打开这个目录时，先把文件角色分清：

```text
pelelmex_prob.H      声明 problem 参数，input 中 prob.* 最终会读到这里
pelelmex_prob.cpp    泄漏源项、风场、可燃云团、点火、障碍物处理逻辑
GNUmakefile          编译入口，脚本会调用它生成 PeleLMeX 可执行文件
input.codex_*.       可复制的 input 模板
*.stl                障碍物几何；管廊着火脚本会自动生成自己的 STL 到 /tmp
```

第一次从零跑，不要碰源码，按下面 6 步走：

```bash
cd "$HOME/my-pele"
REPO=$PWD

# 1. 复制一个自己的 input
cp "$REPO/examples/engineering/h2_leak_3d/input.codex_open_domain_flammable_smoke" \
   "$REPO/examples/engineering/h2_leak_3d/input.my_h2_open_domain"

# 2. 查看要改的参数
grep -nE "prob_lo|prob_hi|n_cell|max_step|fixed_dt|plot_int|lo_bc|hi_bc|leak|wind|do_react|chem_integrator" \
  "$REPO/examples/engineering/h2_leak_3d/input.my_h2_open_domain"

# 3. 先用 CPU 串行确认 input 没问题
CODEX_H2_LEAK_PROFILE_INPUT=input.my_h2_open_domain \
bash tools/codex_smoke_engineering_h2_leak_open_domain.sh

# 4. 再用多核 CPU/MPI 跑同一个 input
MPI_RANKS=4 CODEX_H2_LEAK_PROFILE_INPUT=input.my_h2_open_domain \
bash tools/codex_smoke_engineering_h2_leak_open_domain_mpi.sh

# 5. 管廊障碍物 + 点火 + 真实反应火焰，单 GPU
CUDA_VISIBLE_DEVICES=0 \
bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh

# 6. MPI+CUDA+restart 更严格链路
bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_mpi_cuda_restart.sh
```

如果你要把这个案例改成自己的储罐区/管廊泄漏，优先改 input：

```text
geometry.prob_lo / geometry.prob_hi   厂区或管廊计算域
amr.n_cell                            基础网格
amr.max_level                         AMR 层数，首次建议 0
amr.max_step / amr.fixed_dt           运行步数和时间步
amr.plot_int                          输出间隔
peleLM.lo_bc / peleLM.hi_bc           入口、出口、壁面
prob.wind_u / prob.wind_v             风速
prob.leak_xc / leak_yc / leak_zc       泄漏点坐标
prob.leak_rate / leak_radius           泄漏质量源和源区半径
prob.obstacle_geometry                 all_regular 或 stl
prob.obstacle_stl_files                多个 STL 文件名
```

只有在 input 参数无法表达新物理时，才改 `pelelmex_prob.H/cpp`。

## 1. 最小文件包

在这个目录中，和从零运行最相关的文件是：

```text
GNUmakefile
pelelmex_prob.H
pelelmex_prob.cpp
input.codex_open_domain_flammable_smoke
input.codex_tank_farm_smoke
input.codex_stl_multifile_obstacle_smoke
```

工程管廊着火的 STL 和 input 由脚本自动写到 `/tmp` 运行目录，不需要手动准备。

## 2. 准备自己的泄漏扩散 input

```bash
cd "$HOME/my-pele"
REPO=$PWD
cp "$REPO/examples/engineering/h2_leak_3d/input.codex_open_domain_flammable_smoke" \
   "$REPO/examples/engineering/h2_leak_3d/input.my_h2_open_domain"
```

先查看可改参数：

```bash
grep -nE "prob_lo|prob_hi|n_cell|max_step|fixed_dt|plot_int|lo_bc|hi_bc|leak|wind|do_react|chem_integrator" \
  "$REPO/examples/engineering/h2_leak_3d/input.my_h2_open_domain"
```

第一次只建议改这些：

```text
geometry.prob_lo / geometry.prob_hi   计算域大小
amr.n_cell                            基础网格数
amr.max_step                          运行步数
amr.fixed_dt                          时间步长
amr.plot_int                          plotfile 输出间隔
prob.wind_u / prob.wind_v             环境风
prob.leak_xc / leak_yc / leak_zc       泄漏口位置
prob.leak_rate / leak_radius           泄漏强度和半径
```

## 3. CPU 串行运行泄漏扩散

```bash
cd "$HOME/my-pele"
REPO=$PWD
CODEX_H2_LEAK_PROFILE_INPUT=input.my_h2_open_domain \
bash tools/codex_smoke_engineering_h2_leak_open_domain.sh
```

通过标准：

```text
终端最后出现 PASS
run.log 没有 NaN、Inf、Abort、Backtrace
生成 hazard_timeseries.csv
生成 plt00000 和后续 plotfile
```

## 4. 多核 CPU/MPI 运行泄漏扩散

2 个 MPI rank：

```bash
cd "$HOME/my-pele"
REPO=$PWD
MPI_RANKS=2 CODEX_H2_LEAK_PROFILE_INPUT=input.my_h2_open_domain \
bash tools/codex_smoke_engineering_h2_leak_open_domain_mpi.sh
```

4 个 MPI rank：

```bash
cd "$HOME/my-pele"
REPO=$PWD
MPI_RANKS=4 CODEX_H2_LEAK_PROFILE_INPUT=input.my_h2_open_domain \
bash tools/codex_smoke_engineering_h2_leak_open_domain_mpi.sh
```

如果 MPI 增加后负载不均，优先调整：

```text
amr.max_grid_size = 16 或 32
amr.blocking_factor = 8 或 16
```

## 5. 单 GPU 运行管廊障碍物着火

这个入口会自动生成立方体、圆柱体和管线组成的管廊障碍物，并启用真实反应：

```bash
cd "$HOME/my-pele"
REPO=$PWD
CUDA_VISIBLE_DEVICES=0 bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh
```

更长时间测试：

```bash
cd "$HOME/my-pele"
REPO=$PWD
CUDA_VISIBLE_DEVICES=0 \
CODEX_PIPE_RACK_REACTING_MAX_STEP=150 \
CODEX_PIPE_RACK_REACTING_PLOT_INT=25 \
CODEX_PIPE_RACK_REACTING_N_CELL="64 32 32" \
bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh
```

通过标准：

```text
日志出现 CUDA initialized
日志出现 ReactorCvode
点火后 temp、HeatRelease、Y(H2O) 有变化
火焰在多个 plot 输出间隔内维持
没有 NaN、Inf、CVODE failed、CUDA error
```

## 6. MPI+CUDA restart 运行

这个入口用于更严格地检查 MPI+CUDA 和 checkpoint/restart：

```bash
cd "$HOME/my-pele"
REPO=$PWD
bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_mpi_cuda_restart.sh
```

可调参数：

```bash
CODEX_PIPE_RACK_RESTART_MPI_RANKS=2 \
CODEX_PIPE_RACK_RESTART_INITIAL_STEP=150 \
CODEX_PIPE_RACK_RESTART_FINAL_STEP=450 \
CODEX_PIPE_RACK_RESTART_N_CELL="64 32 32" \
bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_mpi_cuda_restart.sh
```

## 7. 输出怎么看

脚本会打印 `log_root=/tmp/...` 或把日志放到 `/tmp/codex_*`。常用检查：

```bash
tail -n 80 /tmp/codex_h2_*/*run.log
grep -RniE "nan|inf|abort|backtrace|cvode|cuda error|segmentation" /tmp/codex_h2_* | tail -n 80
find /tmp/codex_h2_* -maxdepth 3 -type d -name "plt[0-9][0-9][0-9][0-9][0-9]" | sort | tail
```

如果你要看可燃云团：

```bash
find /tmp/codex_h2_* -name "hazard_timeseries.csv" -print
head -n 20 /tmp/codex_h2_*/hazard_timeseries.csv
```

## 8. 和总教程的关系

更完整的逐步说明见：

```bash
cd "$HOME/my-pele"
REPO=$PWD
sed -n '1,260p' docs/user_guides/从零设置完整算例_工程H2泄漏火灾与学术爆轰.md
```
