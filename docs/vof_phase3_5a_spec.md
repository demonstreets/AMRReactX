# Phase 3.5a — VOF 纯 FCT 框架实现规格

> 日期：2026-06-12
> 状态：待 CodeWhale 实现
> 上一阶段：3.4 H2/O2 ZND 爆轰 ✅
> 前置需求：IndexDefines.H / MOL.H / MOL.cpp / Godunov.H / Hydro.cpp 分析完成

---

## 0. 架构决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 框架 | 纯 FCT（方案 C） | 3.5b 再加 MULES 压缩项 |
| 低阶通量 | 一阶迎风（复用 pc_cmpflx_passive） | 零新增代码 |
| 高阶通量 | minmod MUSCL 重构（复用 mol_slope + 面心插值） | 零新增代码 |
| 限制器 | Zalesak 1979 多维修正版 | 逐维有界性保证 |
| 代码位置 | ~/my-pele/src/academic/vof/ | 学术模块，与 weno5 同级 |
| 代码形式 | 头文件（.H） | GPU 兼容 + PeleC 调用约定 |
| α 索引 | NUM_ADV=1，UFA/QFA 插槽 | 零修改 IndexDefines.H |

---

## 1. 新增文件清单

### 1.1 `src/academic/vof/VOF_FCT.H` — 主模块（~200 行）

**必需函数：**

```cpp
// ── Zalesak 限制器（核心算法）──
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real vof_zalesak_limiter(
    int i, int j, int k, int dir,
    const amrex::Array4<const amrex::Real>& alpha,   // α 原始场（Q 空间）
    amrex::Real flux_low,                             // 低阶通量密度
    amrex::Real flux_high,                            // 高阶通量密度
    const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx,
    amrex::Real dt);

// ── FCT 组装（替换 pc_cmpflx_passive）──
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real vof_fct_flux(
    const amrex::Real ustar,           // 星态速度
    const amrex::Real flxrho,          // 星态密度通量
    const amrex::Real qL,              // 左状态 α
    const amrex::Real qR,              // 右状态 α
    int iL, int iR, int dir,           // 左右格索引（给 Zalesak 限制器）
    const amrex::Array4<const amrex::Real>& alpha,  // α 原始场
    const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx,
    amrex::Real dt);

// ── Youngs 法向（3.5b 用，3.5a 只写骨架验证）──
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void vof_youngs_normal(
    int i, int j, int k,
    const amrex::Array4<const amrex::Real>& alpha,
    amrex::Real& nx, amrex::Real& ny, amrex::Real& nz);
```

### 1.2 `src/academic/vof/VOF_Constants.H` — 常量定义（~15 行）

```cpp
#pragma once
// VOF 控制参数
constexpr amrex::Real VOF_TINY = 1.0e-12;   // 极小值阈值
constexpr amrex::Real VOF_CLIP_LO = 0.0;     // 有界性下界
constexpr amrex::Real VOF_CLIP_HI = 1.0;     // 有界性上界
```

---

## 2. 修改文件清单

### 2.1 `MOL.cpp` — 改动约 30 行

**位置**：ADV 通量计算段（L102–176 区域）

**改动内容**：
```
// 原代码（pc_cmpflx_passive）：
#if NUM_ADV > 0
  for (int n = 0; n < NUM_ADV; n++) {
    pc_cmpflx_passive(ustar, flux_tmp[URHO], qtempl[R_ADV+n], qtempr[R_ADV+n],
                       flux_tmp[UFA+n]);
  }
#endif

// 替换为：
#if NUM_ADV > 0
  // VOF (index 0) gets FCT treatment; other ADV use standard advection
  if (NUM_ADV >= 1) {
    flux_tmp[UFA] = vof_fct_flux(...);   // FCT 通量
  }
  for (int n = 1; n < NUM_ADV; n++) {
    pc_cmpflx_passive(...);              // 其余 ADV 不变
  }
#endif
```

同样修改 Lax-Friedrichs 分支（L166–176）和 EB 路径（MOL.cpp L298–331）。

### 2.2 `Godunov.H` — 改动约 20 行

**位置**：ADV 通量段（L432–445 区域）

**改动内容**：同 MOL.cpp 的替换逻辑——ADV[0] 走 VOF FCT，其余 ADV 保持不变。

### 2.3 `Godunov.H` — PLM 路径

**位置**：L729–737（transverse flux）和 L913–919（final consup）

**改动内容**：同上替换。

### 2.4 `src/academic/vof/` — 模块聚合头文件

新增 `src/academic/vof/vof_modules.H`：

```cpp
#pragma once
#include "VOF_Constants.H"
#include "VOF_FCT.H"
```

### 2.5 验证算例 GNUmakefile

新增 `examples/academic/vof_advection_1D/GNUmakefile` 和对应 `prob_parm.H`、`inputs`。

---

## 3. Zalesak 限制器算法详述

### 3.1 数学表述

```
P_i^+ = Σ max(0, A_{i+1/2}) - Σ min(0, A_{i-1/2})   // 可接受反扩散上界
P_i^- = Σ min(0, A_{i-1/2}) - Σ max(0, A_{i+1/2})   // 可接受反扩散下界
```

其中 `A_{i+1/2} = flux_high - flux_low` 是反扩散通量密度。

```
Q_i^+ = (α_max - α_i^low) * dx / dt   // 余量上界
Q_i^- = (α_i^low - α_min) * dx / dt   // 余量下界

R_i^+ = min(1, Q_i^+ / P_i^+)   (if P_i^+ > 0, else 1)
R_i^- = min(1, Q_i^- / P_i^-)   (if P_i^- > 0, else 1)

C_{i+1/2} = min(R_i^+, R_{i+1}^-)  (when A > 0)
          = min(R_i^-, R_{i+1}^+)  (when A < 0)
```

最终通量：
```
flux = flux_low + C_{i+1/2} * A_{i+1/2}
```

### 3.2 实现注意事项

- α_max / α_min 从低阶解取（i, i-1, i+1 三个格的 max/min）
- 分母除零保护：`P_i^+ < VOF_TINY` 时跳过该方向
- 所有操作均使用原始场 α（不是 ρ·α 守恒形式）

---

## 4. vof_fct_flux 接口设计

```cpp
AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real vof_fct_flux(
    amrex::Real ustar,       // 星态速度（用于迎风判断）
    amrex::Real flxrho,      // 星态密度通量
    amrex::Real qL,          // MUSCL 重构左/右 α 值
    amrex::Real qR,
    int i, int j, int k,     // 当前面索引（面心）
    int dir,                 // 方向 0=x, 1=y, 2=z
    Array4<const Real>& alpha, // α 原始场
    GpuArray<Real,3>& dx,
    Real dt)
{
    // 1. 低阶通量 = 一阶迎风
    flux_low = pc_cmpflx_passive(ustar, flxrho, alpha[L], alpha[R], unused);

    // 2. 高阶通量 = MUSCL 重构值
    flux_high = pc_cmpflx_passive(ustar, flxrho, qL, qR, unused);

    // 3. Zalesak 限制
    flux = flux_low + C * (flux_high - flux_low);

    return flux;
}
```

**关键**：`alpha[L]` 和 `alpha[R]` 是面两侧**格的原始 α 值**（不经过 MUSCL 重构），用于低阶通量。`qL` 和 `qR` 是 MUSCL 重构后的面心值，用于高阶通量。

---

## 5. 验证算例设计

### 5.1 1D 方波平流（`vof_advection_1D`）

| 参数 | 值 |
|------|-----|
| 域 | [0, 1] × [0, 0.1] × [0, 0.1]，单格 dz/dy |
| 网格 | 200 × 1 × 1 |
| 初始 α | 0.25 < x < 0.5: α=1, 其余 α=0 |
| 速度 | u=1, v=0, w=0 |
| 周期 BC | x 方向 |
| CFL | 0.2 |
| 化学 | OFF |
| 停止时间 | 1.0（刚好一个周期回到原位） |
| 评判标准 | ① α ∈ [0,1]（无越界）② 总 α 积分守恒误差 < 1e-8 ③ 界面宽度 < 4 格 |

### 5.2 1D 正弦波平流

同 5.1，α 初始化为正弦波轮廓。验证光滑区的保形性。

### 5.3 2D Zalesak 盘旋转（`vof_zalesak_disk`）

| 参数 | 值 |
|------|-----|
| 域 | [0, 1] × [0, 1] |
| 网格 | 128 × 128 |
| 盘 | 中心 (0.5, 0.75)，半径 0.15，缺口 0.05 宽 |
| 速度场 | 刚体旋转，ω = 2π → 周期 T=1 |
| BC | 所有方向周期 |
| CFL | 0.2 |
| 停止时间 | 1.0 |
| 评判 | ① α ∈ [0,1] ② 质量误差 < 1e-8 ③ 旋转一周后界面形状可辨认 |

---

## 6. 编译集成

### 6.1 NUM_ADV 设置

```
# GNUmakefile of each test case:
DEFINES += -DNUM_ADV=1
```

PeleC 的 `IndexDefines.H` 通过 `#ifndef NUM_ADV` 机制允许外部覆盖。

### 6.2 算例目录结构

```
examples/academic/vof_advection_1D/
├── GNUmakefile
├── inputs
└── prob_parm.H
```

GNUmakefile 模板：
```makefile
DIM = 2
COMP = gnu
PRECISION = DOUBLE
USE_EB = FALSE

Chemistry_Model = air
Eos_Model = Fuego
Transport_Model = Simple

DEFINES += -DNUM_ADV=1

PELE_HOME ?= ../../../external/PeleC
MY_PELE_HOME ?= ../../..
INCLUDE_LOCATIONS += $(MY_PELE_HOME)/src/academic/vof
VPATH_LOCATIONS += $(MY_PELE_HOME)/src/academic/vof

include $(PELE_HOME)/Exec/Make.PeleC
```

---

## 7. 单元测试

### 7.1 `test_vof_fct.cpp`

独立编译（不依赖 PeleC Runtime），测试 Zalesak 限制器的纯数学逻辑：

- 测试 1：所有反扩散通量为零 → C=1 → flux=flux_high
- 测试 2：高余量 → C=1 → 反扩散不被限制
- 测试 3：零余量 → C=0 → flux=flux_low（退化为纯迎风）
- 测试 4：P_i^+ 为零（分母保护）
- 测试 5：已知手算值验证

编译：
```bash
g++ -std=c++17 -I$(MY_PELE_HOME)/src/academic/vof \
    test_vof_fct.cpp -o test_vof_fct
```

### 7.2 `test_vof_advection_1D`（AMReX 集成测试）

- 跑 1D 方波平流 200 步
- 检查：无 NaN、α 不越界、总质量守恒
- 输出 PASS/FAIL

---

## 8. 交付清单

| 文件 | 位置 | 类型 |
|------|------|------|
| VOF_FCT.H | src/academic/vof/ | 新增 |
| VOF_Constants.H | src/academic/vof/ | 新增 |
| vof_modules.H | src/academic/vof/ | 新增 |
| MOL.cpp | external/PeleC/Source/ | 修改 |
| Godunov.H | external/PeleC/Source/ | 修改 |
| GNUmakefile | examples/academic/vof_advection_1D/ | 新增 |
| inputs | examples/academic/vof_advection_1D/ | 新增 |
| prob_parm.H | examples/academic/vof_advection_1D/ | 新增 |
| test_vof_fct.cpp | test/unit/ | 新增 |

**总计**：**6 新增文件 + 2 修改文件**，新增代码量约 **350 行**。

---

## 9. 验收标准

| 编号 | 条件 | 优先级 |
|:----:|------|:------:|
| AC1 | α ∈ [0,1] 在所有时间步所有网格点上成立 | 🔴 MUST |
| AC2 | 总 α 积分在周期平流中守恒（误差 < 1e-8） | 🔴 MUST |
| AC3 | α 初始值为 0/1 的网格不会自发产生中间值 | 🔴 MUST |
| AC4 | 方波界面宽度 < 4 格 after 1 周期 | 🟡 SHOULD |
| AC5 | 不影响非 ADV 变量（rho, u, p, Y_k）的正确性 | 🔴 MUST |
| AC6 | 与现有 NUM_ADV=0 算例二进制兼容（不破坏回归测试） | 🔴 MUST |
| AC7 | GPU 可编译（nvcc 不报错） | 🟡 SHOULD |
