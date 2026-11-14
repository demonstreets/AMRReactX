# TASK: Phase 3.11 前期侦察 — Spray 模块能力评估

## 目标
确认 PeleC 现有 Spray 模块对主计划 3.11-3.14 的覆盖度，跑通基线算例。

## Step 1: 编译+运行 Spray-Jet RegTest

目录: `/home/cj/my-pele/external/PeleC/Exec/RegTests/Spray-Jet/`

```bash
make -j8
./PeleC3d.gnu.ex example.inp max_step=100
```

验证: 无崩溃、粒子正确注入和运动

## Step 2: 列出 Spray 模块的物理能力清单

检查 Particle.cpp 和相关源码，总结:
- 粒子类型（质量点/液滴?）
- 支持的破碎模型（TAB/Reitz Wave?）
- 支持的蒸发模型（Abramzon-Sirignano?）
- 两相耦合方式（源项施加在哪些方程上）
- VOF 交互（液滴遇到液相 α>0 时的行为）
- 可配置参数（直径、速度、注入频率等）

输出到: `/home/cj/my-pele/docs/spray_capability_audit.md`

## Step 3: 评估与主计划的差距

对照主计划 3.11-3.14 需求:
- 3.11 液滴运动追踪 — PeleC 支持? 差距?
- 3.12 Reitz 波+TAB 破碎 — PeleC 支持? 差距?
- 3.13 Abramzon-Sirignano 蒸发 — PeleC 支持? 差距?
- 3.14 两相耦合源项 — PeleC 支持? 差距?
- ACD-07 液滴云雾爆轰 — 缺少什么?
