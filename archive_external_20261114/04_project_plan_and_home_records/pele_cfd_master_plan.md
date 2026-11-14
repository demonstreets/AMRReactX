# Pele 双场景燃烧模拟平台 — 需求、架构与开发计划

**项目名称：** Pele 双场景燃烧模拟平台
**版本：** v1.1（含 2026-06-08 补充）
**日期：** 2026-06-06（起草），2026-06-08（补充）
**作者：** 个人研究项目
**状态：** Pre-Phase 完成，Phase 0 待启动

---

## 目录

1. [项目概述](#1-项目概述)
2. [需求规格](#2-需求规格)
3. [程序架构](#3-程序架构)
4. [开发计划与里程碑](#4-开发计划与里程碑)
5. [审查体系](#5-审查体系)
6. [联调方案](#6-联调方案)
7. [进度管理体系](#7-进度管理体系)
8. [开发工具链](#8-开发工具链)
9. [风险管理](#9-风险管理)
10. [附录](#10-附录)

---

## 1. 项目概述

### 1.1 项目目标

基于 AMReX-Combustion 开源代码库（PeleLMeX、PeleC、PelePhysics），构建一个面向两种场景的燃烧与流体力学数值模拟平台：

- **工程场景：** 大尺度、开放空间及复杂构型障碍物环境下的气体或液相蒸发气体泄漏扩散及着火问题模拟
- **学术场景：** 小尺度、实验室尺度下的气相或气液两相爆轰问题模拟

### 1.2 运行环境

| 阶段 | 环境 |
|------|------|
| 开发与验证 | 单机工作站（128-192 核 CPU） |
| 后期扩展 | HPC 集群（MPI + GPU 节点） |

### 1.3 开发模式

- 个人研究项目，单人开发
- 采用 AI 辅助开发（Cowork 平台）
- 使用 Superpowers 开发方法论（设计 → 计划 → 子代理执行 → 审查 → 收尾）

---

## 2. 需求规格

### 2.1 工程场景需求（基于 PeleLMeX）

| ID | 需求 | 优先级 | 说明 |
|----|------|--------|------|
| ENG-01 | STL/STEP 几何文件读取 | P0 | 支持二进制和 ASCII STL 格式；STEP 先走 Python 离线转换 |
| ENG-02 | 自动网格生成 | P0 | 基于几何包围盒自动确定计算域；生成 AMReX BoxArray + DistributionMapping |
| ENG-03 | 网格自适应加密 (AMR) | P0 | 基于物面曲率和流场梯度特征的自适应网格细化 |
| ENG-04 | Embedded Boundary 障碍物表示 | P0 | STL 三角面片 → signed distance function → AMReX EB2 GeometryShop |
| ENG-05 | 边界条件标签系统 | P0 | 面片级别 BC 类型映射：wall, inlet, outlet, symmetry |
| ENG-06 | 多组分气体扩散 | P0 | 利用 PeleLMeX 现有能力，验证大尺度扩散场景 |
| ENG-07 | RANS k-ε 湍流模型 | P0 | 标准 Jones-Launder k-ε + Launder-Spalding 壁面函数 |
| ENG-08 | 液体池蒸发源项 | P1 | 基于蒸气压差的蒸发模型 |
| ENG-09 | 风场边界条件 | P1 | 对数律/幂律风剖面进口 |
| ENG-10 | 着火/燃烧模拟 | P1 | 利用 PelePhysics 详细/简化机理，SDC 时间推进 |
| ENG-11 | 统一 YAML 输入文件 | P0 | 单文件配置：几何、网格、物理模型、边界条件、输出 |
| ENG-12 | 二阶精度格式 | P0 | PeleLMeX 高阶 Godunov 已满足 |
| ENG-13 | CPU 加速（近期） | P0 | MPI + OpenMP 混合并行 |
| ENG-14 | GPU 加速接口（后期） | P2 | AMReX GPU backend 预留，代码 GPU 合规 |

### 2.2 学术场景需求（基于 PeleC）

| ID | 需求 | 优先级 | 说明 |
|----|------|--------|------|
| ACD-01 | WENO5/WENO5-Z 高阶重构 | P0 | 有限体积框架，GPU 兼容，替换 PeleC 默认二阶重构 |
| ACD-02 | 多步化学反应机理读取 | P0 | Chemkin/Cantera 格式，小规模 H2/O2 <20 组分 |
| ACD-03 | 气相爆轰模拟 | P0 | 基于密度梯度 + 反应进度的 AMR refine criteria |
| ACD-04 | VOF 气液界面捕捉 | P0 | PLIC 界面重构 + 两相状态方程 + 两相 HLLC Riemann 求解器 |
| ACD-05 | 欧拉-拉格朗日液滴追踪 | P0 | 液滴运动 + Reitz 波破碎 + Abramzon-Sirignano 蒸发 |
| ACD-06 | 表面张力模型 | P1 | CSF (Continuum Surface Force) |
| ACD-07 | 气液两相爆轰 | P1 | 液滴云雾爆轰端到端验证 |
| ACD-08 | 网格自适应 (AMR) | P0 | PeleC 已有，扩展至爆轰波面 + 界面密集区 |
| ACD-09 | CPU 加速（近期） | P0 | MPI + OpenMP |
| ACD-10 | GPU 加速（后期） | P2 | AMReX CUDA/HIP/SYCL backend |

### 2.3 质量需求

| ID | 需求 | 说明 |
|----|------|------|
| QLT-01 | 单模块审查 | 每个子任务完成后必须通过独立 agent 的 Type A 审查 |
| QLT-02 | 联调审查 | 每个 Phase 完成后必须通过 Type B 联调审查 |
| QLT-03 | 验证算例 | 标准验证算例（Sod 管、MMS、双马赫反射、气泡上升等） |
| QLT-04 | 断点记录 | 每个子任务完成后保存 checkpoint |
| QLT-05 | GPU 合规性 | 所有自定义代码使用 AMReX 并行原语，无裸指针 |

---

### 2.4 🆕 工程内核选型说明（补充于 2026-06-08）

> **备注**：以下内容基于 PeleC 工程算例调试经验补充，帮助 Claude Code 理解为什么工程场景直接选 PeleLMeX 而非从 PeleC 过渡。

**PeleC 低速工程场景的核心教训**：

| 问题 | 根因 | 性质 |
|------|------|------|
| H₂ EB 壁面注入 22 步 NaN | 密度比 14:1，可压缩 Riemann 求解器中间状态非物理 | 可压缩框架原生问题 |
| 声学 CFL 限制 | 声速 ~340 m/s，低速流场被声学波限制 Δt | 低马赫求解器天然解除 |
| 密度比导致数值刚度 | ρ 突变 → p/T 梯度野值 → EOS 崩溃 | 低马赫框架更鲁棒 |

**结论**：工程内核直接从 PeleLMeX 起步，不走 PeleC 过渡。PeleC 仅用于学术场景（激波/爆轰）。

**PeleC 学习经验可复用的部分**：AMReX 框架理解、PelePhysics 接口、泄漏源项设计思路、诊断框架——这些与求解器解耦，双内核共享。

**PeleLMeX Phase 0 需追加验证**：
- EB 障碍物 + 泄漏源项在低马赫框架下密度比 14:1 的稳定性
- PeleLMeX 使用 AMReX ParmParse（非 YAML），输入文件格式需适配
- SDC 时间推进与化学反应耦合表现

---

## 3. 程序架构

### 3.1 分层架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      用户输入层 (Input Layer)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│  │ YAML 配置文件│  │ Chemkin/     │  │ STL / STEP 几何模型  │    │
│  │              │  │ Cantera 机理 │  │                      │    │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘    │
├─────────┼─────────────────┼─────────────────────┼────────────────┤
│         ▼                 ▼                     ▼                │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                 前处理层 (Preprocessing)                      │ │
│  │  · 几何解析 (STL/STEP → AMReX EB 表示)                       │ │
│  │  · 化学机理解析 (Chemkin → PelePhysics)                      │ │
│  │  · 网格自动生成 + 初始条件 / 边界条件分配                     │ │
│  └────────────────────────┬─────────────────────────────────────┘ │
├───────────────────────────┼──────────────────────────────────────┤
│                           ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    求解器层 (Solver Layer)                    │ │
│  │                                                              │ │
│  │  ┌─────────────────────┐   ┌─────────────────────┐           │ │
│  │  │ PeleLMeX (工程场景) │   │  PeleC (学术场景)    │           │ │
│  │  │                     │   │                     │           │ │
│  │  │ · 低速泄漏/扩散     │   │ · 气相爆轰          │           │ │
│  │  │ · 着火/燃烧         │   │ · DDT (爆燃转爆轰)  │           │ │
│  │  │ · RANS k-ε 湍流     │   │ · WENO5 高阶格式    │           │ │
│  │  │ · EB 障碍物         │   │ · VOF 界面捕捉      │           │ │
│  │  │ · 二阶精度          │   │ · Euler-Lagrange 液滴│           │ │
│  │  └──────────┬──────────┘   └──────────┬──────────┘           │ │
│  │             │                         │                       │ │
│  │             └──────────┬──────────────┘                       │ │
│  │                        ▼                                      │ │
│  │  ┌──────────────────────────────────────────────────────┐    │ │
│  │  │              共享数值基础设施                         │    │ │
│  │  │  · PelePhysics (化学/输运/热力学)                     │    │ │
│  │  │  · AMReX (AMR, EB, 并行, GPU 后端)                  │    │ │
│  │  │  · 自定义高阶重构库 (WENO5, WENO5-Z)                 │    │ │
│  │  │  · 多相流状态方程模块 (stiffened-gas, 理想气体)       │    │ │
│  │  └──────────────────────────────────────────────────────┘    │ │
│  └──────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────┤
│                      后处理层 (Post Processing)                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  · AMReX PlotFile → ParaView / VisIt / yt                   │ │
│  │  · 探针 / 线 / 面 时间历程输出 (CSV/HDF5)                    │ │
│  │  · 自定义诊断 (火焰面、释热率、组分浓度)                     │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 代码目录结构

```
my-pele/
├── README.md
├── PROGRESS.md                    # 进度索引（What's done 只增不删）
├── CMakeLists.txt                 # 顶层 CMake 构建
├── cmake/
│   └── FindAMReX.cmake
├── external/                      # git submodule 上游依赖
│   ├── amrex/                     # AMReX 框架
│   ├── PelePhysics/               # 化学/输运库
│   ├── PeleLMeX/                  # 低马赫数求解器（工程）
│   └── PeleC/                     # 可压缩求解器（学术）
├── src/
│   ├── common/                    # 共享代码
│   │   ├── input_parser/          # YAML 解析
│   │   ├── chemistry/             # 化学机理管理
│   │   ├── eos/                   # 扩展状态方程
│   │   ├── reconstruction/        # WENO5, WENO5-Z
│   │   │   ├── weno5.H
│   │   │   ├── weno5z.H
│   │   │   └── reconstruction_factory.H
│   │   └── io/                    # 数据 I/O
│   ├── geometry/                  # 几何处理
│   │   ├── stl_reader/            # STL 解析
│   │   ├── eb_builder/            # AMReX EB 构建
│   │   │   ├── sdf_generator.H
│   │   │   └── eb_geometry_shop.H
│   │   └── mesh_generator/        # 自动网格
│   ├── engineering/               # 工程场景
│   │   ├── dispersion/            # 泄漏/扩散
│   │   ├── fire/                  # 着火/燃烧
│   │   ├── turbulence/            # k-ε 模型
│   │   │   ├── k_epsilon.H
│   │   │   ├── k_epsilon_sources.H
│   │   │   ├── wall_functions.H
│   │   │   └── turbulent_transport.H
│   │   └── bc_factory/            # 工程 BC
│   └── academic/                  # 学术场景
│       ├── detonation/            # 爆轰物理
│       ├── two_phase/             # 两相流
│       │   ├── vof/               # VOF 方法
│       │   │   ├── volume_fraction.H
│       │   │   ├── plic_reconstruction.H
│       │   │   ├── two_phase_eos.H
│       │   │   ├── two_phase_riemann.H
│       │   │   └── surface_tension.H
│       │   └── lagrange/          # 欧拉-拉格朗日方法
│       │       ├── droplet_particle.H
│       │       ├── droplet_motion.H
│       │       ├── breakup_wave.H
│       │       ├── breakup_tab.H
│       │       ├── evaporation.H
│       │       └── two_way_coupling.H
│       └── high_order/            # 高精度格式
├── test/
│   ├── unit/                      # 单元测试
│   ├── regression/                # 回归测试
│   └── verification/              # MMS 验证
├── examples/                      # 算例
│   ├── engineering/
│   │   ├── gas_leak_open/         # 开放空间泄漏
│   │   ├── tank_farm_dispersion/  # 储罐群扩散
│   │   └── confined_fire/         # 受限空间着火
│   └── academic/
│       ├── sod_shock_tube/        # Sod 激波管
│       ├── double_mach_reflection/# 双马赫反射
│       ├── ddt_channel/           # DDT 通道
│       ├── detonation_2d/         # 二维爆轰胞格
│       ├── bubble_rise/           # 气泡上升
│       ├── rayleigh_taylor/       # RT 不稳定
│       ├── shock_bubble/          # 激波-气泡
│       └── spray_detonation/      # 液滴云雾爆轰
├── docs/
│   ├── theory/                    # 理论手册
│   ├── user_guide/                # 用户手册
│   ├── reviews/                   # 审查报告存档
│   │   ├── single_module/
│   │   └── integration/
│   └── superpowers/               # Superpowers 设计/计划文档
│       ├── specs/                 # 设计规格文档
│       └── plans/                 # 实现计划文档
└── CHECKPOINTS/                   # 详细断点快照
    ├── checkpoint-000.md
    ├── checkpoint-001.md
    └── ...
```

### 3.3 关键模块设计摘要

#### 3.3.1 RANS k-ε 湍流模型（工程场景）

控制方程：

```
∂(ρk)/∂t + ∇·(ρu k) = ∇·[(μ + μ_t/σ_k) ∇k] + P_k - ρε
∂(ρε)/∂t + ∇·(ρu ε) = ∇·[(μ + μ_t/σ_ε) ∇ε] + C_ε1 (ε/k) P_k - C_ε2 ρ ε²/k
μ_t = C_μ ρ k² / ε
```

常数：C_μ=0.09, C_ε1=1.44, C_ε2=1.92, σ_k=1.0, σ_ε=1.3

k 和 ε 作为两个额外标量输运方程接入 PeleLMeX 的 advection-diffusion 框架，通过涡粘修正扩散系数。

壁面函数：Launder-Spalding 标准壁面函数（y⁺ > 30 区域），避免近壁面高分辨率网格。

#### 3.3.2 VOF 气液界面方法（学术场景）

核心组件：
- 体积分数输运：∂α/∂t + ∇·(α u) = 0
- PLIC 界面重构：从 α 计算法向 → 确定平面截距 → 计算对流通量
- 两相状态方程：气相为理想气体，液相为 stiffened-gas，等熵混合压力闭合
- 两相 HLLC Riemann 求解器：气-液界面三层波结构
- CSF 表面张力：F_s = σ κ n δ_s，以体积力形式加入

#### 3.3.3 欧拉-拉格朗日液滴方法（学术场景）

核心组件：
- 液滴运动：Basset-Boussinesq-Oseen 框架
- 气动破碎：Reitz 波模型（高 We）+ TAB 回退（低 We）
- 蒸发模型：Abramzon-Sirignano 扩展薄膜模型
- 两相耦合：粒子定位 → cell 映射 → 源项累加（质量/动量/能量）

#### 3.3.4 WENO5 重构

有限体积框架，GPU 兼容（AMREX_GPU_HOST_DEVICE）。同时在 PeleC 中实现 WENO5 和 WENO5-Z，后者在强间断处非振荡性更好，对爆轰波面更合适。

> 🆕 **备注（2026-06-08）**：WENO5 集成到 PeleC 的关键难点是特征变量投影——需要从守恒变量变换到特征空间做重构再反投影，涉及修改 PeleC `Source/hydro/` 模块核心逻辑。建议拆分：先做独立 WENO5 库 → 守恒变量重构 → 特征变量重构 + hydro 改造。

#### 3.3.5 🆕 泄漏/注入源项模块（工程场景核心，补充于 2026-06-08）

工程场景的核心物理行为是"从障碍物表面某点连续泄漏可燃气体"——这是 Pele 系列的原生空白，需要独立模块。

**模块设计**（`src/engineering/leak_source/`）：
- `leak_geometry.H` — 泄漏孔几何定义（位置、半径、方向）
- `leak_mass_flow.H` — 质量流量模型（孔口公式、蒸发模型）
- `leak_eulerian_source.H` — 欧拉源项施加
- `leak_wall_injection.H` — 壁面注入（EB，备选）

**注入方案矩阵**：

| 方案 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 欧拉体积源项 | 工程场景 | 简单稳定 | 源项空间展宽 |
| EB 壁面注入 | 学术场景（小密度比） | 通量物理清晰 | 密度比 14:1 时 NaN |
| 孔隙率+源项混合 | 工程场景（鲁棒优先） | 最鲁棒 | 扩散精度下降 |

**关键接口**：通过 `problem_modify_ext_sources()` 钩子在求解器时间步内施加源项。注意 ext_src 不与 dt 相乘；修改密度后必须同步缩放 UEINT/UEDEN 保持 EOS 自洽。

#### 3.3.6 🆕 运行时诊断与监控框架（补充于 2026-06-08）

工程算例运行时间长，需要运行时监控。设计独立于求解器的诊断模块：

| 诊断量 | 用途 |
|--------|------|
| 总质量/组分/能量全域积分 | 检测守恒性漂移 |
| 可燃云团质量与体积 | 安全评估核心指标 |
| 泄漏累积质量 vs 源项积分 | 注入自洽性验证 |
| 每 N 步 NaN 扫描 | 崩溃预警 |

输出格式：每 N 步一行 CSV（step, time, total_mass, H2_mass, energy, cloud_mass, cloud_volume, max_T, min_rho）。

代码位置：`src/common/diagnostics/`，双内核共享。

---

## 4. 开发计划与里程碑

### 4.1 总览

```
Phase 0: 环境搭建      ██░░░░░░░░ (1-2月)
Phase 1: 几何管线      ░░███░░░░░ (3-5月)
Phase 2: 工程场景      ░░░░░█████░ (6-11月)
Phase 3: 学术场景      ░░░░░██░░░░ (9-15月)  ← 与 Phase 2 重叠
Phase 4: GPU 加速      ░░░░░░████░ (16-20月)
Phase 5: HPC 移植      ░░░░░░░░██░ (21-26月)
```

### 4.2 Phase 0 — 环境搭建与学习（第 1-2 个月）

**目标：** 编译上游代码，跑通基本算例，建立项目仓库。

| 任务 | 说明 | 交付物 |
|------|------|--------|
| 0.1 | 在工作站上编译 AMReX + PelePhysics + PeleLMeX + PeleC | 可编译的代码 |
| 0.2 | 跑通 PeleLMeX 自带算例 | FlameSheet 等运行截图 |
| 0.3 | 跑通 PeleC 自带算例 | 激波管、2D 爆轰结果 |
| 0.4 | Cantera 机理替换验证 | Chemkin → Cantera YAML → PelePhysics |
| 0.5 | AMR 参数敏感性实验 | 理解 tagging criteria |
| 0.6 | 建立 my-pele/ 仓库 | 目录结构 + submodule + CMake |

**🍂 Gate Review — Phase 0 出口审查（Type B 联调）:**
- 审查项：CMake 构建正确性、submodule 版本锁定、目录结构完整性
- 通过条件：所有上游算例可复现，my-pele 目录结构就绪

> 🆕 **备注（2026-06-08）**：v1.0 列出的验证算例（Sod 管、MMS、双马赫反射）均为无反应验证。反应流需要独立的渐进验证链——**0D 点火延迟（vs Cantera）→ 1D 层流预混火焰（vs 文献）→ 2D 胞格爆轰（vs 实验胞格宽度）→ 3D 爆轰传播**。Phase 0 至少完成 0D 点火延迟的 Cantera 比对，验证化学机理接入正确。

### 4.3 Phase 1 — 几何处理管线（第 3-5 个月）

**目标：** STL → AMReX EB 完整管线。

| 任务 | 说明 |
|------|------|
| 1.1 | STL 解析器（ASCII + 二进制） |
| 1.2 | Signed distance function 生成 |
| 1.3 | AMReX EB2 GeometryShop 构建 |
| 1.4 | 边界条件标签系统 |
| 1.5 | 简单几何验证（球/圆柱绕流） |
| 1.6 | 储罐群算例验证 |

**🍂 Gate Review — Phase 1 出口审查（Type B 联调）:**
- 审查项：STL 解析器 → SDF 生成 → EB 构建 数据流完整性
- 审查项：BC 标签在 AMR 层级间正确传递
- 审查项：多物体组合（union/intersection）的 signed distance 正确性
- 通过条件：球/圆柱绕流与解析解对比误差 < 5%

### 4.4 Phase 2 — 工程场景核心功能（第 6-11 个月）

**目标：** 泄漏/扩散/着火 + RANS k-ε 全流程。

| 任务 | 说明 |
|------|------|
| 2.1 | YAML 输入文件解析器 |
| 2.2 | k-ε 湍流模型核心实现 |
| 2.3 | Launder-Spalding 壁面函数 |
| 2.4 | 湍流-扩散耦合（湍流 Schmidt 数修正） |
| 2.5 | 液体池蒸发源项 |
| 2.6 | 风场边界条件 |
| 2.7 | k-ε 验证：平板边界层、后台阶流动 |
| 2.8 | 着火/燃烧验证 |
| 2.9 | 储罐群泄漏全流程端到端验证 |
| 2.10 | CPU 性能 profiling + 热点优化 |

**🍂 Gate Review — Phase 2 出口审查（Type B 联调）:**
- 审查项：YAML → 几何 → 网格 → 求解器 全链路数据流
- 审查项：k-ε 模型与 PeleLMeX 的对流-扩散框架的接口一致性
- 审查项：壁面函数在 EB 壁面上的正确性（y⁺ 范围检查）
- 审查项：多组分扩散系数修正后的组分守恒
- 通过条件：储罐群泄漏算例全流程跑通，k-ε 验证算例误差 ≤ 文献参考值 ±10%

### 4.5 Phase 3 — 学术场景核心功能（第 9-15 个月）

**目标：** WENO5 + 爆轰 + VOF + 欧拉-拉格朗日两相流。

| 任务 | 说明 |
|------|------|
| 3.1 | WENO5/WENO5-Z 重构实现（1D 验证） |
| 3.2 | WENO5 集成到 PeleC（2D 等熵涡、双马赫反射） |
| 3.3 | 爆轰波面 AMR refine criteria |
| 3.4 | H2/O2 详细机理 2D 胞格爆轰 |
| 3.5 | VOF 体积分数输运方程 |
| 3.6 | PLIC 界面重构 |
| 3.7 | 两相状态方程（理想气体 + stiffened-gas） |
| 3.8 | 两相 HLLC Riemann 求解器 |
| 3.9 | CSF 表面张力 |
| 3.10 | VOF 验证（气泡上升、RT 不稳定、激波-气泡） |
| 3.11 | Euler-Lagrange 液滴追踪 |
| 3.12 | Reitz 波 + TAB 破碎 |
| 3.13 | Abramzon-Sirignano 蒸发 |
| 3.14 | 两相耦合源项 |
| 3.15 | 液滴云雾爆轰端到端验证 |
| 3.16 | MMS 精度验证（WENO5 - 5 阶精度确认） |

**🍂 Gate Review — Phase 3 出口审查（Type B 联调）:**
- 审查项：WENO5 → PeleC hydro 模块接口（重构面值 → Riemann 求解器的数据流）
- 审查项：VOF PLIC → 两相 EOS → 两相 Riemann 的物理一致性
- 审查项：欧拉-拉格朗日 粒子→网格映射 在 AMR 层级间的通信正确性
- 审查项：两相源项的能量守恒（∑源项 = 0）
- 通过条件：双马赫反射与文献对比误差 < 3%，激波-气泡验证跑通，MMS 确认 5 阶精度

### 4.6 Phase 4 — GPU 加速与优化（第 16-20 个月）

| 任务 | 说明 |
|------|------|
| 4.1 | 代码 GPU 合规性审计 |
| 4.2 | CUDA 编译配置 |
| 4.3 | GPU vs CPU 逐位正确性验证 |
| 4.4 | GPU 性能 profiling (nsight/rocprof) |
| 4.5 | Kernel 优化（内存合并、occupancy） |
| 4.6 | 多 GPU 扩展测试（2-4 GPU） |

**🍂 审查要点：**
- 审查项：所有自定义 kernel 的 GPU 合规性（无 std::vector, std::cout）
- 审查项：GPU vs CPU 结果的逐位一致性（允许浮点舍入误差）
- 审查项：单 GPU vs 多 GPU 的 MPI 通信正确性

### 4.7 Phase 5 — HPC 移植与进阶（第 21-26 个月）

| 任务 | 说明 |
|------|------|
| 5.1 | HPC 集群编译适配 |
| 5.2 | 强/弱可扩展性测试（至 128-512 核） |
| 5.3 | STEP 直接读取（OpenCASCADE 集成） |
| 5.4 | 在线可视化（Ascent/Sensei） |
| 5.5 | 不确定性量化接口 |

---

## 5. 审查体系

### 5.1 两种审查类型

| 类型 | 触发时机 | 审查者 | 审查范围 |
|------|---------|--------|---------|
| **Type A 单模块** | 每个子任务完成后 | 独立 agent（code-review skill） | 1-3 个源文件，算法正确性、GPU 合规、数值鲁棒性、内存 |
| **Type B 联调** | 每个 Phase 末尾（Phase Gate） | 独立 agent（code-review skill） | 跨模块接口契约、数据流、并行一致性、物理守恒 |

### 5.2 审查者独立性保证

审查通过 Agent 工具启动**独立 agent 实例**，拥有独立上下文窗口：
- 不知道代码是怎么写的 → 只知道代码是什么
- 不参与架构讨论 → 只对照规范和代码找问题
- 不写代码 → 只产出审查报告（Critical Issues / Warnings / Observations）

### 5.3 审查报告格式

```
## Review Report: [模块名]
**Scope:** [single-module / integration]
**Verdict:** [APPROVED / APPROVED WITH WARNINGS / CHANGES REQUESTED]

### Critical Issues (must fix)
[FAIL] file:line — 问题 — 后果 — 修复方向

### Warnings (should fix)
[WARN] file:line — 问题 — 影响

### Observations (FYI)
[PASS] 检查项 — 结果
```

审查报告存档于 `docs/reviews/single_module/` 和 `docs/reviews/integration/`。

### 5.4 AMReX/Pele 高频审查陷阱

审查者会特别关注：

- 忘记 `FillBoundary()` 在 ghost cell 模板操作前
- `ParallelFor` 的 box 未 grow 到覆盖模板 ghost 范围
- AMReX 索引顺序 `(i, j, k, n)` 混淆
- EB cut-cell 的 `volfrac` 缩放遗漏
- PelePhysics EOS 使用内能 `e` 而非总能量 `E = e + 0.5*u²`
- 物种排序在机理文件 vs PelePhysics 内部重排后不一致
- 输运系数默认 mixture-averaged 而非 multicomponent

### 5.5 每 Phase Gate Review 审查清单

#### Phase 0 Gate
- [ ] CMake 可编译通过（含 submodule）
- [ ] 所有上游自带算例可复现
- [ ] my-pele/ 目录结构完整

#### Phase 1 Gate
- [ ] STL 解析器 → SDF → EB 数据链路完整
- [ ] BC 标签在 AMR 层级间正确传递
- [ ] 球/圆柱绕流验证误差 < 5%

#### Phase 2 Gate
- [ ] YAML → 几何 → 网格 → 求解器 全链路数据流正确
- [ ] k-ε 与 PeleLMeX advection-diffusion 框架接口一致
- [ ] 壁面函数在 EB 壁面上 y⁺ 范围正确
- [ ] 多组分扩散修正后组分守恒

#### Phase 3 Gate
- [ ] WENO5 面值 → Riemann 求解器数据流正确
- [ ] VOF PLIC → 两相 EOS → 两相 Riemann 物理一致
- [ ] 粒子→网格映射在 AMR 层级间通信正确
- [ ] MMS 确认 5 阶精度

#### Phase 4 Gate
- [ ] 所有自定义 kernel GPU 合规
- [ ] GPU vs CPU 逐位一致
- [ ] 多 GPU MPI 通信正确

### 5.6 🆕 CFD 专用审查体系（补充于 2026-06-08）

> 已创建独立 skill：`cfd-code-review`（`~/.hermes/skills/cfd/cfd-code-review/SKILL.md`）。Claude Code 编写的代码需经过此审查流程方可合并。

**与通用代码审查的区别**：通用审查关注安全漏洞/SQL注入/lint；CFD 审查关注**物理正确性与数值稳定性**。

**Type A 单模块核心检查项**：

| 类别 | 检查项 | 严重度 |
|------|--------|--------|
| 守恒性 | 质量/组分/能量/动量在所有路径下守恒 | CRITICAL |
| EOS 自洽 | URHO→UFS→UEINT→UEDEN 转化链自洽；修改密度后同步缩放能量 | CRITICAL |
| NaN 风险 | 除法/开方/对数前正性检查；volfrac > 0；ρ > 0 | CRITICAL |
| AMReX 模式 | FillBoundary 调用顺序；ParallelFor box 覆盖 ghost cells；EB volfrac 缩放 | HIGH |
| GPU 合规 | AMREX_GPU_HOST_DEVICE；无 std 容器在 device 路径 | HIGH |
| 化学反应 | 物种排序一致性；反应率符号；能量源项自洽 | HIGH |

**Type B 联调 Gate**：增补跨模块接口契约检查（数据格式、维度、单位一致性），详见 `cfd-code-review` skill 中各 Phase 的专项接口检查清单。

**执行方式**：通过 `delegate_task` 启动独立 agent 审查，审查者不知道代码是怎么写的，只对照规范和代码找问题。

---

## 6. 联调方案

### 6.1 联调触发条件

每个 Phase 所有子任务完成后，触发 Type B 联调审查。联调审查是 **Gate** — 不通过不能进入下一 Phase。

### 6.2 关键联调接口矩阵

#### Phase 1 → Phase 2 接口

| 输出模块 (Phase 1) | 输入模块 (Phase 2) | 接口契约 |
|--------------------|--------------------|---------|
| `stl_reader` | `eb_builder` | STL 三角面片数据格式、法向量方向约定 |
| `eb_builder` | PeleLMeX EB infrastructure | `EB2::GeometryShop` 对象、`IntersectionIF` 多物体索引 |
| `mesh_generator` | PeleLMeX `AmrCore` | `BoxArray`, `DistributionMapping`, `Geometry` |
| `bc_factory` | PeleLMeX BC infrastructure | BC 类型枚举、面片 ID → BC 映射表 |

#### Phase 2 内部联调接口

| 模块 A | 模块 B | 接口契约 |
|--------|--------|---------|
| `k_epsilon` | PeleLMeX advection-diffusion | 标量输运方程注册、源项接口 |
| `wall_functions` | `k_epsilon` + EB wall | y⁺ 计算、u_τ 接口、壁面 k/ε 边界值 |
| `turbulent_transport` | PeleLMeX diffusion | 有效扩散系数修正、湍流 Schmidt 数 |
| `input_parser` | 所有模块 | YAML schema、参数传递路径 |

#### Phase 3 内部联调接口

| 模块 A | 模块 B | 接口契约 |
|--------|--------|---------|
| `weno5` | PeleC `hydro/riemann` | 重构面值格式、特征变量投影 |
| `plic_reconstruction` | `volume_fraction` | α 场 → 法向 → 截距 → 通量 |
| `two_phase_eos` | `two_phase_riemann` | 压力、声速查询接口 |
| `droplet_motion` | `two_way_coupling` | 粒子位置 → cell 映射 → 源项累加 |
| `evaporation` | `droplet_motion` + PelePhysics | 输运系数查询、组分索引 |
| `breakup_wave` | `droplet_motion` | 破碎后新粒子生成、动量重分配 |

### 6.3 联调测试方法

- **接口契约测试：** 调用方和被调用方分别运行单元测试，验证接口预期的输入/输出范围
- **数据流追踪：** 选取一个简单算例，追踪一个物理量从输入到输出的完整路径
- **守恒性检查：** 跨模块边界追踪质量/动量/能量是否守恒
- **对称性测试：** 利用问题对称性验证跨模块结果的对称性

---

## 7. 进度管理体系

### 7.1 双文件断点系统

```
my-pele/
├── PROGRESS.md          # 快速恢复索引 + 累积进度地图
└── CHECKPOINTS/         # 详细断点快照
    ├── checkpoint-000.md
    ├── checkpoint-001.md
    └── ...
```

### 7.2 PROGRESS.md 结构

PROGRESS.md 是"现在在哪"的单一真相来源，新会话打开先读它。三个区域各有生命周期：

| 区域 | 生命周期 | 规则 |
|------|---------|------|
| **What's done** | **只增不删** | 每完成一个任务追加一行，含 checkpoint 引用。跨模块联调时依赖它查找历史模块 |
| **What's in progress** | 每次保存轮换 | 始终只有一条，描述精确状态（文件、行号、阻塞原因） |
| **Next session** | 每次保存重写 | 具体到新会话能直接开工，含文件路径和操作步骤 |

### 7.3 断点保存时机

**必须保存：**
- 每完成一个路线图任务
- 任何与架构文档有出入的重要决策
- 任何花了时间才发现走不通的尝试（负结果也是知识）
- 会话结束前（即使任务未完成）
- 上下文压缩警告出现时

**可以跳过：**
- 纯问答/讨论（无代码产出）
- 只读代码浏览
- 微小修复（typo）

### 7.4 新会话恢复流程

```
1. 读 PROGRESS.md → 了解当前状态和项目历史
2. 看 "Next session" → 直接告诉你做什么
3. 如需上下文 → 读最近 1-2 个 CHECKPOINTS/
4. 如需跨模块联调 → 在 "What's done" 找相关模块 checkpoint，读详细设计决策
5. 如需全局视野 → 读 architecture_plan.md
6. 直接开工
```

### 7.5 完整开发循环（单任务粒度）

```
设计阶段
  brainstorming → 产出 spec 文档
  writing-plans → 产出可执行计划

实施阶段
  subagent-driven-development (每任务)
    ├── 派 implementer subagent
    ├── TDD: RED → GREEN → REFACTOR → COMMIT
    ├── Gate 1: Spec compliance review
    ├── Gate 2: Code quality review
    └── 修复 → 重新审查 → 通过

检查点
  写 checkpoint-NNN.md
  更新 PROGRESS.md (What's done 追加, Next session 重写)

单模块审查
  启动 Type A 审查 agent
  └── 通过 → 下一个子任务
  └── 不通过 → 修复 → 重新审查

Phase 收尾
  写 Phase checkpoint
  启动 Type B 联调审查
  finishing-a-development-branch → 决定分支命运

出问题
  systematic-debugging → 三次失败自动停 → 重新分析
```

### 7.6 开发工具链（Skills 总览）

| Skill | 用途 | 阶段 |
|-------|------|------|
| `brainstorming` | 9 步 Socratic 设计，产 spec | 设计 |
| `writing-plans` | spec → 2-5 min 粒度可执行计划，零 TBD | 计划 |
| `subagent-driven-development` | 每任务独立 subagent + 两轮审查 | 实施 |
| `test-driven-development` | RED-GREEN-REFACTOR 铁律 | 实施 |
| `code-review` | Type A 单模块 + Type B 联调审查 | 审查 |
| `systematic-debugging` | 四阶段科学调试，3 次失败规则 | 调试 |
| `checkpoint` | 断点保存 + PROGRESS.md 维护 | 进度 |
| `finishing-a-development-branch` | 收尾：validate → review → merge/discard | 收尾 |

---

## 8. 开发工具链

### 8.1 外部依赖

| 依赖 | 必要性 | 说明 |
|------|--------|------|
| AMReX | 必须 | AMR 框架，GPU 抽象 |
| PelePhysics | 必须 | 化学/输运/热力学 |
| PeleLMeX | 必须 (工程) | 低马赫数求解器 |
| PeleC | 必须 (学术) | 可压缩求解器 |
| yaml-cpp | 强烈推荐 | 输入文件解析 |
| Cantera | 强烈推荐 | 机理转换/验证 |
| openmpi / mpich | 必须 | MPI 并行 |
| CUDA / HIP / SYCL | 可选 (后期) | GPU 加速 |
| OpenCASCADE | 可选 (后期) | STEP 直接读取 |

### 8.2 构建系统

CMake，与 AMReX 上游一致：

```bash
# CPU-only
cmake -S . -B build -DAMReX_OMP=ON -DPELE_USE_CANTERA=ON
cmake --build build -j

# GPU (CUDA)
cmake -S . -B build-gpu -DAMReX_GPU_BACKEND=CUDA -DAMReX_CUDA_ARCH=8.0 -DPELE_USE_CANTERA=ON
cmake --build build-gpu -j
```

### 8.3 推荐开发环境

```
OS:       Ubuntu 22.04 / RHEL 8+
编译器:   GCC 12+ 或 Clang 16+
MPI:      OpenMPI 4.1+ 或 MPICH 4+
Python:   3.10+ (Cantera 机理转换、后处理)
```

---

## 9. 风险管理

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|---------|
| PeleLMeX EB 压力投影矩阵严重病态 | 中 | 高 | 预留代数多重网格 (AMG) 预处理器；关注上游 EB solver 研究进展 |
| WENO5 GPU kernel 性能不足 | 低 | 中 | 小规模机理（<20 组分）降低 kernel 复杂度；预留 WENO3 作为轻量回退 |
| VOF + 可压缩框架耦合困难 | 中 | 高 | 先从不可压缩 VOF 验证开始，逐步加入可压缩效应 |
| 单人开发进度落后 | 中 | 中 | Phase 独立、gate 机制，任何 Phase 完成都产生可交付物 |
| 上游 Pele 代码 breaking change | 低 | 低 | submodule 锁定版本；Phase 0 记录可编译的 commit hash |
| 🆕 PeleLMeX 无法处理着火后压力波 | 中 | 高 | 工程场景如需模拟爆炸后果，评估是否需要保留 PeleC 作为工程内核备选 |
| 🆕 大尺度下孔隙率扩散精度不足 | 中 | 中 | 混合方案：孔隙率挡固体 + 局部 EB 细化注入孔附近 |
| 🆕 SUNDIALS 版本兼容性 | 中 | 中 | Phase 0 锁定 SUNDIALS 6.4（系统安装版），CMake 优先用 find_package 而非 bundled |

---

## 10. 附录

### A. 上游代码状态（截至 2026-06-06）

| 代码库 | 状态 | 关键特性 |
|--------|------|---------|
| PeleLMeX | 活跃开发 | 低马赫数，无 subcycling，EB 支持，GPU (CUDA/HIP/SYCL) |
| PeleC | 活跃开发 | 可压缩反应流，AMR，GPU |
| PeleLM | 已停滞 | 被 PeleLMeX 取代，不要使用 |
| PelePhysics | 活跃开发 | Cantera 接口，GPU-ready，共享基础设施 |
| AMReX | 活跃开发 | BSD-3 许可，NREL/LBNL 维护 |

Pele 家族属于 ECP (Exascale Computing Project)，已在 ORNL Frontier 超算上验证了 600 亿网格、4096 GPU 节点的 scaling。

### B. 关键技术决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 工程场景求解器 | PeleLMeX | PeleLM 已停滞，PeleLMeX 无 subcycling 且 GPU 好 |
| 湍流模型 | RANS k-ε | 工程快速评估优先 |
| 两相流方法 | VOF + Euler-Lagrange 双方法 | 互补覆盖解析界面和亚网格液滴 |
| 反应机理 | H2/O2 <20 组分 | GPU kernel 简单，后续可模板化扩展 |
| 高阶格式 | WENO5 + WENO5-Z | Z 权重在强间断处更好 |
| 两相 EOS | 理想气体 + stiffened-gas | 覆盖核心场景 |
| 审查机制 | 独立 agent，Type A + Type B | 天然新鲜眼光，避免作者盲区 |
| 断点机制 | PROGRESS.md + CHECKPOINTS/ | 快速索引 + 详细快照 |
| 输入格式 | YAML | 人类可读写，yaml-cpp 成熟 |
| STEP 处理 | Python 离线转换 → 后期 OpenCASCADE | 快速验证优先 |
| 🆕 工程几何方案 | 孔隙率优先，EB 备选 | 孔隙率更鲁棒，适合大尺度；EB 用于需要高精度的局部区域 |
| 🆕 泄漏注入方式 | 体积源项法（工程），EB 壁面注入（学术） | PeleC 实测 EB 注入 14:1 密度比 NaN；低马赫框架待 PeleLMeX 验证 |
| 🆕 SUNDIALS | 系统安装 6.4，禁止 bundled 7.x | 7.x 编译报错，6.4 唯一验证可用版本 |
| 🆕 审查体系 | cfd-code-review skill + code-reviewer profile | 独立 agent 消除作者盲区，CFD 专项检查物理正确性 |

### C. 文件索引

| 文件 | 用途 |
|------|------|
| `PROGRESS.md` | 当前进度（只增不删） |
| `CHECKPOINTS/checkpoint-NNN.md` | 详细断点快照 |
| `docs/superpowers/specs/` | 设计规格文档 |
| `docs/superpowers/plans/` | 实现计划文档 |
| `docs/reviews/single_module/` | Type A 审查报告 |
| `docs/reviews/integration/` | Type B 审查报告 |

---

*本文档随项目推进持续更新。下次更新机会：Phase 0 完成后。*
