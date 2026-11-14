> **运行诊断修正（2026-09-09）：** 下文错误检查只针对 `RUN_DIR` 指定的本次运行，不扫描整个 `/tmp` 或历史证据库。运行器必须把本次进程退出码保存到 `RUN_DIR/exit_code`；不能把错误后的下一条命令退出码当成求解器退出码。日志健康检查与原始场的物理验证分别进行，正常的 CVODE 初始化不算错误。

# 学术场景 Tutorial：气相爆轰、GPU/MPI、两相与液滴验证

适用目录：`/home/cj/my-pele`

本教程面向实验室尺度、小尺度学术算例，核心是 PeleC 可压缩反应流。当前优先级是气相爆轰，其次是气液两相、液滴、VOF、CSF 等能力。

## 1. 推荐起步路线

建议按以下顺序：

1. 跑 2D 气相爆轰 CPU wave smoke
2. 跑 2D 气相爆轰 MPI smoke
3. 跑 PeleC CUDA smoke
4. 跑 MPI+CUDA reacting smoke
5. 再改机理、网格、AMR、初始热点
6. 最后接两相/液滴/VOF 验证

## 2. 气相爆轰 CPU 基础算例

运行：

```bash
cd /home/cj/my-pele
bash tools/codex_smoke_academic_detonation_wave.sh
```

该脚本使用：

```text
examples/academic/detonation_2D
examples/academic/detonation_2D/inputs.codex_wave_smoke
```

会构建：

```text
codex_deton2d_cpu2d.gnu.ex
```

会运行到：

```text
STEP = 20
plt00020
```

检查：

```bash
grep "STEP = 20" /tmp/codex_detonation_wave_*/run.log
grep -i "AMReX .* finalized" /tmp/codex_detonation_wave_*/run.log
```

验证脚本：

```text
tools/validate_detonation_wave.py
```

它会比较 `plt00000` 和 `plt00020`，确认波面/状态变化符合预期 smoke 标准。

## 3. 气相爆轰 MPI

运行：

```bash
cd /home/cj/my-pele
MPI_RANKS=2 bash tools/codex_smoke_academic_pelec_mpi.sh
```

脚本会：

```text
make -C examples/academic/detonation_2D USE_MPI=TRUE EBASE=codex_deton2d_mpi
mpirun --oversubscribe -np 2 ./codex_deton2d_mpi2d.gnu.MPI.ex inputs.codex_smoke
```

检查：

```bash
grep "MPI initialized with 2 MPI processes" /tmp/codex_smoke_academic_mpi_*/run.log
grep "STEP = 1" /tmp/codex_smoke_academic_mpi_*/run.log
grep -i "AMReX .* finalized" /tmp/codex_smoke_academic_mpi_*/run.log
```

## 4. PeleC CUDA

运行前设置：

```bash
cd /home/cj/my-pele
export SUNDIALS_CUDA_DIR=$HOME/local/sundials-cuda
CUDA_VISIBLE_DEVICES=0 bash tools/codex_smoke_academic_pelec_cuda.sh
```

脚本使用：

```text
examples/academic/bench_1gpu
examples/academic/bench_1gpu/input.codex_cuda_smoke
PeleC3d.gnu.CUDA.ex
```

输出：

```text
/tmp/codex_pelec_cuda_smoke_*/run.log
/tmp/codex_pelec_cuda_smoke_*/validation.log
/tmp/codex_pelec_cuda_smoke_*/run/plt00001
```

关键检查：

```bash
grep "CUDA initialized with" /tmp/codex_pelec_cuda_smoke_*/run.log
grep -i "AMReX .* finalized" /tmp/codex_pelec_cuda_smoke_*/run.log
```

## 5. MPI+CUDA 反应 smoke

运行：

```bash
cd /home/cj/my-pele
export SUNDIALS_CUDA_DIR=$HOME/local/sundials-cuda
CUDA_VISIBLE_DEVICES=0,1 CODEX_REACTING_MPI_CUDA_RANKS=2 \
bash tools/codex_smoke_engineering_h2_reacting_mpi_cuda.sh
```

虽然脚本名在 engineering 下，但它运行的是 PeleC H2/O2 reacting MPI+CUDA smoke，用于验证反应、MPI、CUDA、PelePhysics/SUNDIALS 链路。

输入片段：

```text
pelec.do_hydro = 1
pelec.do_react = 1
pelec.chem_integrator = ReactorRK64
pelec.weno_scheme = 1
amr.plot_vars = density Temp pressure rho_H2 rho_O2 rho_H2O ...
```

关键检查：

```text
MPI initialized with 2 MPI processes
CUDA initialized with 2 devices
Creating ReactorBase instance: ReactorRK64
AMReX finalized
```

## 6. 如何修改爆轰输入文件

从这个文件复制：

```bash
cp examples/academic/detonation_2D/inputs.codex_wave_smoke /tmp/my_detonation_inputs
```

常改参数：

```text
max_step
stop_time
geometry.prob_lo / geometry.prob_hi
amr.n_cell
amr.max_level
amr.max_grid_size
amr.plot_int
pelec.cfl
pelec.do_react
pelec.chem_integrator
prob.p_0 / prob.T_0
prob.T_hot / prob.p_hot / prob.r_hot
```

保守建议：

- 先固定 `amr.max_level = 0` 跑通。
- 确认没有 NaN/Inf 后再开 AMR。
- 先小步数跑 `max_step = 20`，再延长。
- 反应刚性强时减小 CFL 或时间步。

## 7. 两相、VOF、液滴相关入口

已有算例目录：

```text
examples/academic/vof_advection_1D
examples/academic/spray_test
examples/academic/shock_droplet
examples/academic/rayleigh_taylor
examples/academic/bubble_rise
```

常用 smoke：

```bash
bash tools/codex_smoke_academic_vof_advection.sh
bash tools/codex_smoke_academic_d2_law.sh
bash tools/codex_smoke_academic_shock_droplet_spray.sh
bash tools/codex_smoke_academic_rayleigh_taylor.sh
```

这些入口更适合验证两相基础模块，不建议一开始就用来宣称完整气液两相爆轰生产能力。两相爆轰需要同时检查：

```text
气相反应
液滴蒸发/破碎
VOF 或 Euler-Lagrange 质量守恒
激波捕捉
界面/粒子源项耦合
AMR 标记
CPU/GPU 一致性
```

## 8. 输出怎么看

爆轰重点看：

```text
pressure
Temp
density
velocity
rho_H2 / rho_O2 / rho_H2O
反应进度或热释放相关变量，如输出中存在
```

日志检查：

```bash
grep "STEP =" run.log | tail
grep -i "PLOTFILE" run.log
grep -i "AMReX .* finalized" run.log
: "${RUN_DIR:?请先设置 RUN_DIR 为本次运行目录}"
python3 tools/check_cfd_run_log.py --log "$RUN_DIR/run.log" --exit-code "$(cat "$RUN_DIR/exit_code")"
```

plotfile：

```text
plt00000
plt00020
pltxxxxx/Header
pltxxxxx/job_info
```

## 9. 常见问题

### CUDA smoke 要求 SUNDIALS_CUDA_DIR

如果看到：

```text
set SUNDIALS_CUDA_DIR or SUNDIALS_DIR
```

设置：

```bash
export SUNDIALS_CUDA_DIR=$HOME/local/sundials-cuda
```

### 反应积分器失败

处理顺序：

```text
减小 CFL
降低热点温度或压力梯度
减小 fixed_dt
先 do_react=0 跑纯流动
检查组分质量分数是否合理
```

### MPI 进程残留

检查：

```bash
pgrep -af 'PeleC|mpirun|codex_deton'
```

如果确认是自己的残留测试进程，再手动结束。

### plotfile 没输出

检查：

```text
amr.plot_int 是否大于 max_step
运行是否提前失败
run.log 是否出现 Abort/Backtrace
输出目录是否在 /tmp/codex_* 下，而不是算例目录
```

## 10. 学术算例扩展建议

要做正式气相爆轰：

```text
明确机理：H2/O2 或其他
明确初始压力/温度/当量比
明确热点或激波初始化方式
明确通道尺寸、边界条件
明确网格收敛计划
明确 CPU/GPU/MPI 对比计划
```

要做气液两相爆轰：

```text
液滴粒径分布
液滴初始速度和温度
液滴质量负载
蒸发/破碎模型
两相源项守恒检查
气相反应机理
激波/爆轰判据
```

当前建议优先用气相爆轰作为稳定主线，两相爆轰作为扩展验证线。
