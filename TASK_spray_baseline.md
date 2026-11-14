# TASK: 隔离 VOF，验证 Spray 基线

## 策略
Spray-Jet RegTest 被 VOF 无条件嵌入（Godunov.H include vof_modules.H）污染。
先移除 VOF 路径，验证纯 Spray 模块能跑通。

## 步骤

1. 在 `/home/cj/my-pele/external/PeleC/Exec/RegTests/Spray-Jet/GNUmakefile` 中:
   - 注释掉或删除 VOF 相关的 INCLUDE_LOCATIONS 和 VPATH_LOCATIONS
   - `DEFINES += -DNUM_ADV=0`（或删除 NUM_ADV=1 的 define，确保默认 0）
   - DIM 改为 3

2. `make clean && make -j8`

3. `./PeleC3d.gnu.ex example.inp max_step=20`

4. 验证: 无崩溃，粒子注入+运动正常，STEP 输出标准

## 注意
这暂时绕过了 VOF-Spray 集成问题。VOF-Spray 桥接是独立的架构任务（Phase 3.x），不在此修复范围。
