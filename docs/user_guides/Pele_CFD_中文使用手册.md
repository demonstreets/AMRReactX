> **运行诊断修正（2026-09-09）：** 下文错误检查只针对 `RUN_DIR` 指定的本次运行，不扫描整个 `/tmp` 或历史证据库。运行器必须把本次进程退出码保存到 `RUN_DIR/exit_code`；不能把错误后的下一条命令退出码当成求解器退出码。日志健康检查与原始场的物理验证分别进行，正常的 CVODE 初始化不算错误。

# Pele CFD 中文使用手册

适用仓库：`/home/cj/my-pele`

本手册说明如何从用户角度使用当前 PeleC/PeleLMeX CFD 平台。它不替代代码审计报告，而是回答一个更实际的问题：文件在哪里，输入怎么写，算例怎么跑，结果怎么看，出错怎么查。

如果你要从零设置一个完整算例，先读这份：

```bash
sed -n '1,260p' docs/user_guides/从零设置完整算例_工程H2泄漏火灾与学术爆轰.md
```

它选定 `examples/engineering/h2_leak_3d` 和 `examples/academic/detonation_2D`，逐步说明要复制哪些 input、改哪些参数、如何用 CPU/MPI/GPU/MPI+CUDA 跑，以及输出怎么看。

## 1. 项目目录

进入项目：

```bash
cd /home/cj/my-pele
```

常用目录：

```text
/home/cj/my-pele
├── examples/
│   ├── engineering/        # 工程场景算例，低马赫 PeleLMeX 为主
│   └── academic/           # 学术场景算例，PeleC 爆轰/两相为主
├── tools/                  # 运行、验证、报告生成脚本
├── docs/
│   ├── user_guides/        # 中文使用教程
│   └── codex_audit/        # 审计、验证、证据链
├── external/               # AMReX/PeleC/PeleLMeX/PelePhysics 等依赖
└── build/ 或算例目录内      # 编译产物，具体视算例 Makefile 而定
```

工程场景重点目录：

```text
examples/engineering/h2_leak_3d
examples/engineering/h2_ignition
examples/engineering/backward_facing_step
examples/engineering/bfs_kepsilon
examples/engineering/spray_combust_3d
```

学术场景重点目录：

```text
examples/academic/detonation_2D
examples/academic/bench_1gpu
examples/academic/bench_2gpu
examples/academic/spray_test
examples/academic/shock_droplet
examples/academic/rayleigh_taylor
examples/academic/vof_advection_1D
```

## 2. 输入文件

当前项目有两类输入文件：

1. Pele/AMReX 原生 `inputs` 或 `input.xxx` 文件
2. 工程前处理用 YAML 文件

### 2.1 AMReX/Pele 原生输入文件

这类文件通常没有扩展名，例如：

```text
examples/academic/detonation_2D/inputs.codex_wave_smoke
examples/academic/bench_1gpu/input.codex_cuda_smoke
```

典型结构：

```text
max_step = 20
stop_time = 1.0e-7

geometry.is_periodic = 0 0 1
geometry.coord_sys = 0
geometry.prob_lo = 0.0 0.0 0.0
geometry.prob_hi = 3.0 2.0 0.16

amr.n_cell = 48 16 4
amr.max_level = 0
amr.max_grid_size = 32
amr.plot_int = 1

pelec.do_hydro = 1
pelec.do_react = 1
pelec.chem_integrator = ReactorRK64
```

常见字段含义：

```text
max_step             最大步数
stop_time            终止物理时间
geometry.prob_lo     计算域下边界
geometry.prob_hi     计算域上边界
amr.n_cell           基础网格数
amr.max_level        AMR 最大层级
amr.max_grid_size    单个 grid 最大尺寸
amr.plot_int         plotfile 输出间隔
amr.check_int        checkpoint 输出间隔
```

PeleC 常见字段：

```text
pelec.do_hydro       是否求解流动
pelec.do_react       是否开启化学反应
pelec.chem_integrator 反应积分器
pelec.cfl            CFL 数
pelec.weno_scheme    WENO 相关选择
```

PeleLMeX 常见字段：

```text
peleLM.do_react                 是否开启反应
peleLM.chem_integrator          反应积分器
peleLM.user_defined_ext_sources 是否使用用户源项
peleLM.sdc_iterMax              SDC 迭代次数
peleLM.lo_bc / peleLM.hi_bc     边界条件
```

### 2.2 YAML 输入文件

工程前处理和部分模型配置使用 YAML，例如：

```text
examples/engineering/backward_facing_step/input.yaml
examples/engineering/bfs_kepsilon/input.yaml
examples/engineering/h2_leak_3d/*.yaml 或生成型 input 文件
```

YAML 通常描述几何、网格、物理模型、边界条件、源项和输出。实际运行时很多 smoke 脚本会把 YAML 或模板转换成 PeleLMeX 原生 input。

## 3. 推荐运行方式

最稳妥的用户入口不是手写很长的 `mpirun` 命令，而是先运行仓库里已经封装好的脚本。

工程 H2 泄漏 MPI：

```bash
cd /home/cj/my-pele
MPI_RANKS=2 bash tools/codex_smoke_engineering_h2_leak_open_domain_mpi.sh
```

工程 H2 管廊障碍物着火 CUDA：

```bash
cd /home/cj/my-pele
CUDA_VISIBLE_DEVICES=0 bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh
```

学术 PeleC 气相爆轰 CPU：

```bash
cd /home/cj/my-pele
bash tools/codex_smoke_academic_detonation_wave.sh
```

学术 PeleC 气相爆轰 MPI：

```bash
cd /home/cj/my-pele
MPI_RANKS=2 bash tools/codex_smoke_academic_pelec_mpi.sh
```

学术 PeleC CUDA：

```bash
cd /home/cj/my-pele
export SUNDIALS_CUDA_DIR=$HOME/local/sundials-cuda
CUDA_VISIBLE_DEVICES=0 bash tools/codex_smoke_academic_pelec_cuda.sh
```

完整当前范围验证：

```bash
cd /home/cj/my-pele
bash tools/run_current_scope_release_refresh.sh
```

这个命令较重，会重建/验证当前 scope 的主要证据链，不建议每改一个小输入都跑。

## 4. CPU、GPU、MPI 运行

### 4.1 单 CPU/串行

很多脚本默认可以串行运行，例如：

```bash
bash tools/codex_smoke_academic_detonation_wave.sh
```

### 4.2 多核 CPU/MPI

常用形式：

```bash
MPI_RANKS=2 bash tools/codex_smoke_engineering_h2_leak_open_domain_mpi.sh
```

如果手动运行可执行文件，常见形式是：

```bash
mpirun --oversubscribe -np 2 ./xxx.gnu.MPI.ex inputs
```

### 4.3 单 GPU

常用环境变量：

```bash
CUDA_VISIBLE_DEVICES=0
SUNDIALS_CUDA_DIR=$HOME/local/sundials-cuda
```

运行前检查：

```bash
nvidia-smi
nvcc --version
```

### 4.4 MPI + CUDA

常见形式：

```bash
CUDA_VISIBLE_DEVICES=0,1 MPI_RANKS=2 bash tools/codex_smoke_engineering_h2_reacting_mpi_cuda.sh
```

注意：

- MPI 版本要和编译时一致。
- CUDA/SUNDIALS 动态库要在 `LD_LIBRARY_PATH` 中。
- 多卡时需要确认每个 rank 能看到对应 GPU。

## 5. 输出怎么看

常见输出位置：

```text
/tmp/codex_*/run.log
/tmp/codex_*/validation.log
/tmp/codex_*/summary.json
/tmp/codex_*/run/plt00000
/tmp/codex_*/run/plt00020
```

Pele/AMReX 标准 plotfile：

```text
plt00000/
plt00001/
plt00020/
```

关键文件：

```text
plt00020/Header      plotfile 头信息
plt00020/job_info    编译、运行、MPI 信息
plt00020/Level_0/    网格数据
```

判断算例是否正常结束：

```bash
grep -i "AMReX .* finalized" run.log
: "${RUN_DIR:?请先设置 RUN_DIR 为本次运行目录}"
python3 tools/check_cfd_run_log.py --log "$RUN_DIR/run.log" --exit-code "$(cat "$RUN_DIR/exit_code")"
```

如果第一条能找到、第二条没有危险命中，说明至少运行层面是稳定结束的。

可视化建议：

- ParaView：打开 AMReX plotfile 目录或转换后的数据。
- VisIt：直接读取 AMReX plotfile。
- yt/amrex 工具：适合 Python 后处理。

## 6. 常见错误排查

### 6.1 找不到可执行文件

现象：

```text
missing executable
No such file or directory
```

处理：

```bash
cd /home/cj/my-pele
make -C examples/academic/detonation_2D -j 4
```

具体 Make 参数要看脚本中使用的 `EBASE`、`USE_MPI`、`USE_CUDA`。

### 6.2 CUDA 库找不到

现象：

```text
libcudart.so not found
libsundials... not found
CUDA error
```

处理：

```bash
export SUNDIALS_CUDA_DIR=$HOME/local/sundials-cuda
export LD_LIBRARY_PATH=$SUNDIALS_CUDA_DIR/lib:/usr/local/cuda/lib64:$LD_LIBRARY_PATH
nvidia-smi
```

### 6.3 MPI 版本不匹配

现象：

```text
Open MPI required
MPI initialized 数量不对
libmpi.so not found
```

处理：

```bash
which mpirun
mpirun --version
ldd ./your_executable | grep mpi
```

### 6.4 输入文件有未使用参数

现象：

```text
Unused ParmParse Variables
```

处理：

- 检查参数前缀是否写错，例如 `pelec.` 与 `peleLM.` 不能混。
- 检查当前可执行文件是否支持该功能。
- 从已有 smoke input 复制，再逐项修改。

### 6.5 数值发散、NaN、Inf

现象：

```text
nan
inf
Abort
Backtrace
```

优先检查：

```text
时间步是否过大
CFL 是否过大
源项质量流量是否过强
初始温度/压力/组分是否非物理
边界条件是否和流动方向冲突
AMR 网格是否太粗
化学积分器是否适合当前刚性
```

保守调参：

```text
减小 fixed_dt
减小 cfl
先关闭反应只跑扩散
先降低源项强度
先 max_level=0 跑通，再打开 AMR
```

## 7. 当前能力边界

已经可用于当前优先工程链路：

- H2 泄漏、扩散、着火
- 管廊/障碍物 CUDA smoke
- 多燃料气相源项边界：H2、CH4、C3H8
- LNG/LPG 外部气化源项代理
- CPU/MPI、单 GPU、MPI+CUDA 当前场景验证

尚不能严格宣称完全闭合：

- 真实 CAD 清理包和真实边界标签尚未由用户提供。
- SBEPV5 D27 严格外部 plume 目标包尚未齐。
- 火灾辐射/超压已有指标文件，但严格 case alignment 尚未完全满足。

因此，当前平台适合继续做工程应用和算例准备；最终生产级严格验收需要真实算例包配合。
