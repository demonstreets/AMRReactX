# my-pele 独立审查后的修复与验证报告

日期：2026-09-09。目标：`192.168.31.89:/home/cj/my-pele`。

本轮已直接修改服务器项目，完成可独立复现的越界、通量/重构、热点、源项积分、单位、错误验收和归档流程修正，并完成针对性复验。**这不是“17 项全部闭环”或“主计划全部完成”的声明：完整混合物闭合、PLIC 主推进和气液爆轰认证仍未完成；相关误用已被默认拒绝或取消认证。** 真实 CAD 接入以及实际三维泄漏、火灾验证按本次要求暂缓。

源码、测试与说明共修改/新增 54 个文件（不含结果归档和交付报告）。每批先核对文件 SHA-256、保存原件，再替换目标文件；共 23 批备份。没有 reset/revert 用户工作树，没有删除旧算例、日志、场数据或历史报告；失败的本轮试验也保留。

## 1. 逐项整改状态

| 审查项 | 本轮状态 | 具体处理与限制 |
|---|---|---|
| F01 | 已修复 | HLLC 先写连续组分临时数组，再逐分量写回 Array4；修正相邻网格被误写。 |
| F02 | 已修复并停用伪实现 | 标量 alpha 辅助函数显式接收分量号；从主推进删除非 MULES 动量体力，use_mules=1 明确拒绝。 |
| F03 | 验收错误已修复；反应路径补充 | 旧零反应机理认证被拒绝；默认例保留非反应输运用途，增加 88 组分真实机理的显式构建、独立缓存与 CPU CVODE 输入。气液爆轰仍未认证。 |
| F04 | 已修复 | CSF 从已 FillPatch 的入参状态读取，要求至少两层幽灵单元；实际 NUM_ADV=1 CPU 单步经过该分支。 |
| F05 | 已修复 | 热点按实际域定位并检查初始化真实最高温；新 GPU 初场 Tmax=2214 K。旧冷流报告不再通过。 |
| F06 | 部分修正，模型缺口保留 | 修正 HLLC 能量跃迁、p_inf 波速和 SG 温度；混合物闭合及 PLIC 主推进未补齐，VOF 默认拒绝、显式实验许可仅供开发。 |
| F07 | 数值缺陷与验收逻辑已修复 | WENO 在 EOS 前限制特征积分，修复极低星区压力 NaN、组分面通量和壁面组分镜像；负 Y 严格验收，前缘改为压力梯度。没有授予自持爆轰认证。 |
| F08 | 源项积分实现已修复 | 归一化包含 AMR 覆盖掩码、EB 流体体积分数与 MPI 全局求和；制造解体积与源总量通过 1/2/8 rank 检查。 |
| F09 | 按本次范围暂缓 | 真实 CAD/STL 水密性和工程几何验收未开展。 |
| F10 | 按本次范围暂缓 | 现场 A/B 坐标及真实 CAD 对齐未开展。 |
| F11 | 新归档已修复；历史缺口保留 | 新结果完整保存 FAB、checkpoint、二进制与哈希；缺失的旧 C3H8/CH4/H2 场数据不能补造，未重跑本次排除的工程场景。 |
| F12 | 实际场景验证暂缓 | 短时封闭/简化算例不再被解释为工程火灾有效性；真实边界和长时工况留待实际三维验证。 |
| F13 | 单位与公式已修复 | CGS 的 sigma=72 dyn/cm、p_inf=6e9 dyn/cm²、cv=4.18e7 erg/(g·K) 明确配置；初场共用参数，记录 SG 标定仍属模型缺口。 |
| F14 | 已修复 | 按实际源树哈希记录 vendored 依赖；GPU 构建前快照并核对漂移，归档二进制/库哈希/编译日志。正庚烷归档明确缺少构建前快照，不伪称完整溯源。 |
| F15 | 按本次范围暂缓 | 真实储罐/设备尺寸与 CAD 的核验未开展。 |
| F16 | 已修复已定位脚本 | detonation_wave runner 拒绝复用日志目录，取消先 rm -rf 旧证据的行为；新归档同样拒绝覆盖。 |
| F17 | 已修复 | 教程改查单次 run 的实际退出码与具体 fatal 标记；不再把 CVODE/普通 inf 文字或其他历史任务混作错误。 |

## 2. 已通过的验证

### 2.1 单元、内存与接口

- 当前源代码重新构建的 CTest：**24/24 通过**；其中证据检查套件包含 **10 个**独立用例。
- 使用真实 AMReX Array4 的三组分、八单元接线复现通过；相邻单元哨兵保持不变。
- 标量 alpha 的 ASan/UBSan 复现通过；显式分量号区分完整状态和单分量临时场。
- 使用实际 Fuego 热化学和生产 Riemann 源码的强膨胀测试通过：原版本在星区压力约 2.2e-308 时产生 NaN，修复后通量有限；不可穿透壁面的质量、组分和能量通量为零。
- 实际 NUM_ADV=1 CPU 构建完成；启用 CSF 的单步运行正常结束。未允许实验 VOF 时正确拒绝；请求旧 MULES 时正确拒绝。它们是接口/内存回归，不是标准泡升物理验证。

### 2.2 AMR/EB 源项制造解

编译了实际 PeleLMeX 源项集成，并对单位立方体、平面 EB、部分区域细化的网格进行积分。正确复合流体体积为 **0.7**；1、2、8 MPI rank 均通过有效体积和源总量检查，覆盖单元与固体不重复计入。

这是源项函数的制造解检查，没有推进实际三维泄漏或火灾算例。

### 2.3 GPU/MPI 气相反应回归

采用相同可执行文件、96×32×4 网格、3×1×0.16 cm 域、LiDryer 9 组分机理，比较单 GPU、双 GPU，以及第 100 步切换到双 GPU 后推进至第 200 步的重启结果。热点真实存在，初始最高温度 2214 K。通过 nvidia-smi 的进程采样确认两个 MPI 进程使用两张不同 GPU。

| 指标 | 最终结果 |
|---|---:|
| 推进步数 | 200 |
| 物理时间 | 1.286147421307e-06 s |
| 最终最低/最高温度 | 300 / 3547.31899 K |
| 最终最低密度 | 2.064775892891e-05 g/cm³ |
| 最终最低压力 | 1.624714051563e+05 dyn/cm² |
| 最终组分质量分数最小值 | 0.0 |
| 最终最大组分和误差 | 4.441e-16 |
| 初末总质量相对变化 | 4.959e-16 |
| H₂ 总量消耗比例 | 9.092940% |
| 水产物净增加/初始总质量 | 5.998806% |
| 单/双 GPU 保存场最大差值 | 0 |
| 重启/连续推进保存场最大差值 | 0 |

每条完整运行保留 11 个场输出，重启后保留 5 个；已逐个读取数据，检查有限值、正密度/温度/压力、组分非负与组分和。比较覆盖所有保存字段及输出时刻，不只是某个温度峰。

壁面组分镜像修正前，这一短窗口的质量相对变化约 1.44e-7；修正后降至约 4.96e-16。没有通过放宽质量容差掩盖问题；当前闭合质量检查阈值为 1e-10。

**以上只证明本配置的有限窗口反应与并行/重启回归通过。** 压力前缘有移动，但本次没有完成 CJ/ZND 外部定量基准、网格收敛、长期自持传播或胞格统计，不能据此授予完整爆轰认证。

### 2.4 正庚烷真实反应路径

新增显式构建 `Chemistry_Model=heptane_lu_88sk`：88 组分、729 反应。修正大小写不同的生成组分索引，并将对象缓存按机理隔离；首次复验发现旧对象混入造成 NUM_SPECIES 不一致，独立完整构建后解决。

8×8 均匀气相、1400 K 初场、4×1e-8 s 的测试中，显式 RK64 未通过；交付输入改为实际通过的 **CPU ReactorCvode + GMRES**。最终正庚烷消耗比例为 0.01626480%，组分和误差 2.220e-16，最小 Y=-5.152e-14，在 1e-12 容差内。最终温度约 1399.95642069 K，略低于初温，不能解释为已经点火。

这个测试只证明真实气相化学路径连通、数据有效。喷雾已关闭，既不是气液耦合验证，也不是气液爆轰验证。旧 `heptane_3sp` 保留非反应输运用途，其零反应数不再被当作化学反应通过。

## 3. 已纠正的错误 PASS

- 旧 single-CUDA 和 MPI-CUDA 热点报告，现在都会因原始初场热点缺失而返回非零退出码。
- 旧气液爆轰认证，现在会因原始运行使用零反应机理而拒绝。
- 新的气液重新评估报告明确输出 **NOT_READY**，自持传播、胞格和外部参照相关认证均未授予。
- 负组分不再允许以 1e-3 容差通过；短时场变化与温度峰跳动不能替代反应和波前证据。

旧 JSON 保留用于追溯，README、操作说明和进展文件已明确其历史属性，不能继续作为当前权威认证。

## 4. 结果、源码与回退

服务器工作目录：`/home/cj/my-pele`。

新证据目录：`docs/codex_audit/evidence/repair_20260909/`，包含：

- `gpu_final_np1/`、`gpu_final_np2/`、`gpu_final_restart_np2/`：完整场、checkpoint、二进制、构建前源码快照和逐文件归档清单；总计约 2.276 GB。
- `gpu_final_validation.json`、`gpu_binding.json`、`gpu_build.log`、`build_environment.json`：数值对比、两张 GPU 的进程记录、编译日志及依赖库哈希。
- `heptane_final/`：实际 CVODE 运行的完整场与二进制。此附加试验没有完整构建前源码指纹，清单明确 `source_snapshot_present=false`，没有伪称与 GPU 档案等同的溯源等级。
- `gas_liquid_reassessment.json/.md`：当前 NOT_READY 结论。

本地交付：`修复状态_20260909.json` 给出逐项状态、改动文件前后哈希和备份路径；`my-pele_修复补丁_20260909.patch` 是相对于本轮修改前文件的汇总差异，**不应再直接应用到已经修复的服务器树**。

原件保存在服务器 `repair_backups/`。如需回退，应按清单先核对当前哈希和后续修改，逐项恢复；不要整库 reset，也不要把本轮汇总补丁应用到其他项目。当前源码/测试/教程经过最终哈希复核，未发现本轮未记录的并发改动。

## 5. 仍需后续完成的工作

1. 完整混合物热力学闭合、真实 VOF/PLIC 主推进及其标准两相算例验证；本轮通过显式实验门槛隔离，未补造完整模型。
2. 气液耦合爆轰、反应序列、波–反应耦合和胞格/外部基准证据；当前认证保持 NOT_READY。
3. 旧工程场数据缺口。无法从日志重建丢失的 FAB；实际三维复算属于本轮明确排除的范围。
4. 真实 CAD、现场坐标/尺寸及实际三维泄漏、火灾边界和长期工况验证，待真实资料与后续范围确定后开展。

## 附录：修改文件及最终哈希前缀

| 文件（相对服务器项目根目录） | SHA-256 前 16 位 |
|---|---|
| `external/PeleC/Source/Godunov.H` | `a94511a796156538` |
| `src/academic/vof/VOF_FCT.H` | `95ffca86594badc9` |
| `external/PeleC/Source/Hydro.cpp` | `90b68b56445eaebf` |
| `test/unit/test_vof_fct.cpp` | `9b228a4855ef7f94` |
| `tools/write_academic_gas_detonation_single_cuda_report.py` | `9acdfdf13de3e7fc` |
| `tools/write_academic_gas_detonation_mpi_cuda_report.py` | `6efe55bbd5aff61c` |
| `tools/validate_academic_gas_3d_znd.py` | `f890c3b3b3a3ab93` |
| `tools/validate_detonation_wave.py` | `47d21ea3220ae561` |
| `tools/codex_smoke_academic_detonation_wave.sh` | `a6b7e949f442eadf` |
| `tools/write_academic_gas_liquid_detonation_certification_report.py` | `3fa2920b804c0b9b` |
| `examples/academic/shock_droplet/prob.cpp` | `9c33d0708c465dd1` |
| `tools/cfd_evidence_checks.py` | `4e6db15d29c41131` |
| `examples/academic/bench_1gpu/prob_parm.H` | `b7b5e1a33d64e799` |
| `examples/academic/bench_1gpu/prob.cpp` | `bdafb278bc9282d3` |
| `examples/academic/bench_1gpu/prob.H` | `59793d256028ec2f` |
| `examples/academic/bench_2gpu/prob_parm.H` | `b7b5e1a33d64e799` |
| `examples/academic/bench_2gpu/prob.cpp` | `89d64fd5cc4d7a18` |
| `examples/academic/bench_2gpu/prob.H` | `59793d256028ec2f` |
| `external/PeleLMeX/Source/PeleLMeX_ProblemSpecificFunctions.H` | `b6fd56ee5e5a34f7` |
| `external/PeleLMeX/Source/PeleLMeX_Forces.cpp` | `c76f524a741c5fde` |
| `examples/engineering/h2_leak_3d/pelelmex_prob.H` | `542eadccc0f89d27` |
| `external/PeleC/Source/SpeciesFluxLimiter.H` | `af2238130bf4c369` |
| `CMakeLists.txt` | `da6357de206bfbc7` |
| `test/unit/test_species_flux_limiter.cpp` | `963a3b29509bf3f4` |
| `test/integration/test_source_volume_amr.cpp` | `1bf10cda518a12e4` |
| `tools/cfd_run_archive.py` | `15b59e3741150d0b` |
| `tools/test_cfd_evidence_checks.py` | `4385811bb9e861fd` |
| `external/PeleC/Source/Riemann.H` | `0de1df103ecf5b36` |
| `external/PeleC/Source/PeleC.cpp` | `303478a6dc576672` |
| `src/academic/twophase/StiffenedGas.H` | `57c97aebd5abf32a` |
| `src/academic/twophase/TwoPhaseParams.H` | `eec4bd3754699985` |
| `examples/academic/spray_test/prob.H` | `df22ceb1afa61118` |
| `examples/academic/vof_advection_1D/prob.H` | `7710d3cf9eec5186` |
| `examples/academic/bubble_rise/prob.H` | `051dda19fa534591` |
| `test/unit/test_twophase_eos.cpp` | `b72a027cf2d22a10` |
| `src/academic/twophase/TwoPhaseHLLC.H` | `6a027799df3cb13b` |
| `tools/test_cfd_core_regressions.py` | `123c32a62bd42c9b` |
| `external/PeleC/Source/PPM.cpp` | `ac80398a6fbd5095` |
| `examples/academic/shock_droplet/prob.H` | `65a8393ce547fe00` |
| `examples/academic/shock_droplet/GNUmakefile` | `9140f12a9e34e32c` |
| `examples/academic/shock_droplet/inputs.reacting_smoke` | `907e868295522102` |
| `tools/test_source_volume_integration.py` | `bd3a5bcc0492a2a3` |
| `tools/test_riemann_thermochemistry.py` | `d75d58eacd980b6a` |
| `tools/check_cfd_run_log.py` | `d312eb99964a446c` |
| `README.md` | `795b11def41aa8ff` |
| `PROGRESS.md` | `85621e548bfaaef4` |
| `AGENTS.md` | `e1236c02ddb9478c` |
| `docs/codex_audit/current_scope_operator_runbook.md` | `9a4dc69f099aa142` |
| `docs/user_guides/Pele_CFD_中文使用手册.md` | `d5cd06dd292d1668` |
| `docs/user_guides/从零设置完整算例_工程H2泄漏火灾与学术爆轰.md` | `b7c62d2dc053f72b` |
| `docs/user_guides/学术场景_气相与两相爆轰_Tutorial.md` | `aaa8a936bcc02699` |
| `docs/user_guides/从目录到排错_完整运行教程.md` | `d12ac606d07b23f1` |
| `docs/user_guides/工程场景_泄漏扩散火灾_Tutorial.md` | `c00c68cf6a815d73` |
| `docs/codex_audit/repair_20260909.md` | `fcbcc8840f3c52de` |
