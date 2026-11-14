# 工程场景 Tutorial：泄漏、扩散、障碍物、着火和火灾后果

适用目录：`/home/cj/my-pele`

本教程面向化工厂、储罐区、管廊、开放区域中的可燃气泄漏扩散与火灾计算。当前工程链路主要基于 PeleLMeX，并配套工程源项、障碍物、GPU/MPI smoke 和审计报告。

## 1. 推荐起步路线

建议按以下顺序跑：

1. 冷态泄漏扩散，不开反应
2. 加障碍物/管廊
3. 加点火和反应
4. 改成 CPU/MPI 或 CUDA
5. 增加风场、监测点、输出变量

不要一开始就把真实 CAD、大质量流量、强反应、多级 AMR 全打开。工程算例最稳的方式是逐层加复杂度。

## 2. H2 开放区域泄漏扩散 MPI

运行：

```bash
cd /home/cj/my-pele
MPI_RANKS=2 bash tools/codex_smoke_engineering_h2_leak_open_domain_mpi.sh
```

脚本会设置：

```text
CODEX_H2_LEAK_HISTORY_USE_MPI=TRUE
CODEX_H2_LEAK_PROFILE_INPUT=input.codex_open_domain_flammable_smoke
```

输出通常在：

```text
/tmp/codex_h2_leak_open_domain_mpi_YYYYMMDDTHHMMSSZ/
├── run.log
├── mpi_validation.log
└── run/
    ├── input.codex_open_domain_flammable_smoke
    └── plt000XX/
```

检查：

```bash
grep -i "MPI initialized" /tmp/codex_h2_leak_open_domain_mpi_*/run.log
grep -i "AMReX .* finalized" /tmp/codex_h2_leak_open_domain_mpi_*/run.log
grep -i "nan\\|inf\\|Backtrace\\|CUDA error\\|Abort" /tmp/codex_h2_leak_open_domain_mpi_*/run.log
```

如果 `mpi_validation.log` 里有 PASS，并且 `pltxxxxx/Level_0/Cell_H` 中 Fab 数量不少于 MPI rank 数，说明 MPI 输出分布也通过了基本检查。

## 3. H2 管廊障碍物着火 CUDA

运行：

```bash
cd /home/cj/my-pele
CUDA_VISIBLE_DEVICES=0 bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh
```

这个脚本会自动生成一个小型 3D 管廊障碍物场景，包括：

```text
codex_cube_block.stl
codex_vertical_cylinder.stl
codex_pipe_rack.stl
input.codex_pipe_rack_reacting_single_cuda_20step
```

主要物理设置：

```text
peleLM.do_react = 1
peleLM.chem_integrator = ReactorCvode
peleLM.user_defined_ext_sources = 1
prob.wind_u = 0.50
amr.fixed_dt = 1.0e-8
```

可通过环境变量调整：

```bash
CODEX_PIPE_RACK_REACTING_MAX_STEP=100 \
CODEX_PIPE_RACK_REACTING_PLOT_INT=10 \
CUDA_VISIBLE_DEVICES=0 \
bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh
```

保守延长时长时，建议先只增大：

```text
CODEX_PIPE_RACK_REACTING_MAX_STEP
CODEX_PIPE_RACK_REACTING_PLOT_INT
```

不要同时大幅加密网格和增强源项。

## 4. H2 反应场 MPI+CUDA

运行：

```bash
cd /home/cj/my-pele
CUDA_VISIBLE_DEVICES=0,1 MPI_RANKS=2 bash tools/codex_smoke_engineering_h2_reacting_mpi_cuda.sh
```

用途：

- 验证反应算例在 MPI+CUDA 下能启动、输出、结束。
- 检查 AMReX/Pele/PelePhysics/CUDA/SUNDIALS 动态链接。

如果失败，先看：

```bash
tail -100 /tmp/codex_*/run.log
tail -100 /tmp/codex_*/launcher.log
```

## 5. 多燃料和液化气源项

当前已建立的工程边界能力：

```bash
bash tools/verify_engineering_multi_fuel_capability_boundary.sh
bash tools/verify_engineering_multi_fuel_template_catalog.sh
bash tools/verify_engineering_gasified_lng_lpg_surrogate.sh
bash tools/verify_engineering_liquefied_breach_source_contract.sh
bash tools/verify_engineering_liquefied_release_source_balance.sh
```

这些验证说明：

- H2、CH4、C3H8 的气相源项可以配置。
- LNG/LPG 目前走外部气化源项代理。
- CFD 内部尚不宣称直接求解完整闪蒸、液池铺展和相变。

实际项目中，如果你有液化气储罐破裂场景，建议输入：

```text
物质：LNG_CH4 或 LPG_C3H8
破口位置
破口面积或等效孔径
储罐压力、温度
总库存或可泄漏库存
外部气化模型给出的 mdot(t)
风速、风向、大气稳定度
点火时间和位置
```

当前 CFD 侧最稳做法是使用外部气化源项时间序列 `mdot(t)`，再进入气相扩散/火灾计算。

## 6. 工程输入文件怎么改

建议从脚本生成的 input 文件开始改，不要从空白文件写。

常改参数：

```text
geometry.prob_lo / geometry.prob_hi   计算域大小
amr.n_cell                            基础网格
amr.max_level                         AMR 层级
amr.max_step                          步数
amr.fixed_dt 或 amr.cfl               时间步控制
amr.plot_int                          输出频率
prob.wind_u / prob.wind_v             风场
prob.leak_*                           泄漏源项
peleLM.do_react                       是否着火反应
```

加真实几何时，需要整理：

```text
source CAD/STL/STEP 文件
清理后的 STL 文件
边界标签：inlet/outlet/wall/leak_source/obstacle/monitor
几何坐标单位
几何包围盒
泄漏点坐标
监测点坐标
```

严格生产验收不能只给 STL，必须同时给 provenance、hash、清理记录和边界标签。

## 7. 输出与后处理

工程算例重点看：

```text
run.log                    是否稳定结束
summary.json               脚本生成的统计摘要
validation.log             自动验证结果
pltxxxxx/                  AMReX plotfile
history/probe CSV          如脚本生成
```

火灾/着火重点变量：

```text
Temp
pressure
mass_fractions
rho_H2 或对应燃料组分
heat release rate，如输出中存在
derived velocity
```

泄漏扩散重点指标：

```text
可燃云体积
LFL/UFL 范围
传感器浓度时间序列
最大浓度
云团到达时间
```

## 8. 从真实工程项目开始时给我的最小资料包

如果你要让我把真实工厂/储罐区算例接入，最小资料包建议包括：

```text
1. 几何：CAD/STL/STEP，带单位说明
2. 边界：入口、出口、地面、墙、障碍物、泄漏点、监测点标签
3. 泄漏：物质、压力、温度、孔径或质量流量、持续时间
4. 环境：风速、风向、温度、压力
5. 点火：点火位置、时间、能量或温度源设定
6. 输出：你关心的监测点、浓度阈值、热辐射、超压、温度区域
7. 验收：希望跑多久、最大网格规模、CPU/GPU 资源
```

有这些信息后，可以把 synthetic 管廊测试推进到真实工程 case。
