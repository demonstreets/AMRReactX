# Phase 3.5 Spec: VOF 体积分数输运方程

**版本:** v1.0  
**日期:** 2026-06-12  
**状态:** 待审阅  
**范围:** 在 PeleC 中添加体积分数 α 的输运方程 ∂α/∂t + ∇·(αu) = 0

---

## 1. 背景

VOF（Volume of Fluid）方法用体积分数 α ∈ [0,1] 标记气液界面：
- α=0：纯气相
- α=1：纯液相
- 0<α<1：界面过渡区

控制方程（不可压缩两相流）：
∂α/∂t + u·∇α = 0  或守恒形式  ∂α/∂t + ∇·(αu) = α∇·u

PeleC 是可压缩求解器，使用守恒形式更自然。

## 2. 嵌入方案

### 2.1 新增 State 变量

在 PeleC 的 `IndexDefines.H` 中新增：

```cpp
// After existing state indices
NVAR = NUM_STATE + 1;  // increment by 1
// Add VFRAC as last index
```

或者更干净的方案——通过 PeleC 的 `NUM_AUX` 机制添加辅助变量。

### 2.2 输运方程接入

PeleC 的对流框架在 `Hydro.cpp` / `Godunov.cpp` / `MOL.cpp` 中。α 作为被动标量参与对流：

1. **重构**：α 和其他被动标量一样，用 WENO5/PLM/PPM 重构面值
2. **Riemann 求解**：α 用被动标量通量（`pc_lax_cmpflx_passive` in MOL.H）
3. **时间推进**：跟随现有的 SDC/RK 框架

### 2.3 关键接口

```
IndexDefines.H:   #define VFRAC  (新增state索引)
Hydro.cpp:        α 参与对流通量计算
MOL.H:            α 使用被动标量通量
prob.H:           pc_initdata 设置 α 初始值
```

## 3. 实现步骤

### Step 1: 添加 VFRAC state 变量

- 修改 `IndexDefines.H`：增加 VFRAC 索引
- 修改 `Setup.cpp`：注册 VFRAC 到 state descriptor
- 修改 `Derive.cpp`：添加 α derive 函数

### Step 2: 对流通量

- 在 `MOL.H` 的 `mol_slope` 中加入 VFRAC 分量
- 在 `Godunov.cpp` 中确保 VFRAC 参与通量计算

### Step 3: 验证算例

1D 平流测试：初始 α 方波，均匀速度场平流，验证无耗散/无振荡。

## 4. 简化方案（MVP）

最小可行方案——复用 PeleC 现有的 passive scalar 机制：
- 用 `NUM_SPECIES` 之后的辅助变量槽位
- 在 `pc_initdata` 中设置
- 让 PeleC 现有的对流框架自动处理（passive scalars 已支持）

## 5. 风险

| 风险 | 缓解 |
|------|------|
| PeleC 源码修改范围大 | 先用最小侵入方案（aux variable） |
| α 在激波处不守恒 | 验证 1D 平流先 |
| 与现有 species 索引冲突 | 在 NUM_SPECIES 之后加 |

## 6. 决策点

在起草详细代码 spec 之前，需先深入研读 PeleC 的：
1. IndexDefines.H（state 变量布局）
2. MOL.H（被动标量通量路径）
3. Hydro.cpp（对流入口）

**建议**：先花 30 分钟研读这三文件，输出中文分析文档，再起草可执行的代码 spec。
