# Phase 3.2 Spec: WENO5 验证算例

**版本:** v1.0  
**日期:** 2026-06-12  
**状态:** 待审阅  
**范围:** PeleC 内建 WENO5 的精度和非振荡性验证

---

## 1. 背景

PeleC 已内建 WENO5-JS (`weno_scheme=0`) 和 WENO5-Z (`weno_scheme=1`)，通过 `ppm_type=1` + `use_hybrid_weno=1` 启用。Phase 3.2 不需要写集成代码，而是建立标准验证算例确认 WENO5 正确性。

## 2. 算例 A：等熵涡 (Isentropic Vortex)

### 2.1 物理描述

2D 光滑等熵涡在均匀流中平流，验证 WENO5 高阶精度。

- 域：[0, 10] × [0, 10]，周期性 BC
- 涡强度 ε = 5.0，涡半径 R = 1.0
- 背景：ρ∞=1, u∞=1, v∞=1, p∞=1/γ, γ=1.4
- 涡扰动（叠加到背景）：
  - δu = -ε·(y-y₀)/R · exp(-r²/2)
  - δv =  ε·(x-x₀)/R · exp(-r²/2)
  - δT = -(γ-1)ε²/(4γ) · exp(-r²)，δp 通过等熵关系
- 涡心 (x₀, y₀) = (5, 5)
- 运行至 t = 10（涡平流回原位）

### 2.2 验证项

| 网格 | 预期 L₁ 误差 | WENO5 收敛阶 |
|------|:---:|:---:|
| 32² | ~1e-3 | — |
| 64² | ~3e-5 | ~5 |
| 128² | ~1e-6 | ~5 |
| 256² | ~3e-8 | ~5 |

### 2.3 文件

```
my-pele/examples/academic/
└── isentropic_vortex/
    ├── CMakeLists.txt
    ├── GNUmakefile
    ├── Make.package
    ├── prob_parm.H
    ├── prob.H
    ├── prob.cpp
    └── inputs_weno5
```

## 3. 算例 B：双马赫反射 (Double Mach Reflection)

### 3.1 物理描述

Mach 10 激波以 60° 角冲击 30° 斜劈，验证 WENO5 在强激波处的非振荡性。

- 域：[0, 4] × [0, 1]
- 斜劈从 (x=1/6, y=0) 开始，与下边界成 30°
- 初始激波：x = 1/6 + y/√3，激波前 (右/上) 静止 ρ=1.4, p=1, u=v=0
- 激波后 (左/下)：Mach 10 → 由 Rankine-Hugoniot 关系确定
- BC：上边界跟随激波运动，左右入流/出流，下边界 x<x_wedge 为激波后条件、x≥x_wedge 为滑移壁面
- γ = 1.4
- 网格：960×240（或类似分辨率），AMR max_level=2
- 运行至 t = 0.2

### 3.2 验证项

- 马赫杆清晰可见
- 滑移线处的 Kelvin-Helmholtz 涡卷
- 无 post-shock 振荡（区别于低阶格式）
- 与 Woodward & Colella (1984) 经典结果定性一致

### 3.3 文件

```
my-pele/examples/academic/
└── double_mach_reflection/
    ├── CMakeLists.txt
    ├── GNUmakefile
    ├── Make.package
    ├── prob_parm.H
    ├── prob.H
    ├── prob.cpp
    └── inputs_weno5
```

## 4. 技术要点

### 4.1 PeleC 算例结构

从 `Exec/RegTests/Shu-Osher/` 复制模板，修改：
- CMakeLists.txt：`GammaLaw` EOS + `Null` chemistry + `Constant` transport
- prob_parm.H：定义算例参数
- prob.cpp：`amrex_probinit()` 解析参数 + `pc_initdata()` 初始化流场
- inputs：启用 WENO5

### 4.2 WENO 配置

```
pelec.ppm_type = 1
pelec.use_hybrid_weno = 1
pelec.weno_scheme = 0   # 0=WENO5-JS, 1=WENO5-Z
```

### 4.3 编译

```bash
cd ~/my-pele/external/PeleC/Exec/RegTests
# 复制模板
cp -r Shu-Osher IsentropicVortex
# 修改文件...
# 编译
make -j
```

或者在 `~/my-pele/examples/academic/` 下独立放置，通过 PeleC 的 CMake 构建。

### 4.4 双马赫反射 BC 处理

PeleC 支持 `UserBC` 类型（见 Shu-Osher 用 `Hard`）。双马赫反射需要：
- 上边界：时变 Dirichlet（激波运动 → 激波后/前条件随时间切换）
- 用 `"UserBC"` 在 prob.cpp 中实现

## 5. 验收标准

- [ ] 等熵涡：WENO5 在 64²→256² 网格上确认 ≥4.5 阶收敛
- [ ] 双马赫反射：马赫杆 + 滑移线涡卷清晰，无 post-shock 振荡
- [ ] 两个算例均可一键编译运行
- [ ] code-reviewer Type A 审查 PASS

## 6. 与 Phase 3.1 独立 WENO5 库的关系

Phase 3.1 的 `src/common/reconstruction/weno5.H` 是独立数学库，与 PeleC 内建 WENO 并行存在：
- 我们的库：独立验证、可脱离 PeleC 使用
- PeleC 内建：已在 hydro 模块深度集成
- 两者不冲突，各自服务不同场景
