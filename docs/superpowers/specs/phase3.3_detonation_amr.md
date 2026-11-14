# Phase 3.3 Spec: 爆轰波面 AMR Refine Criteria

**版本:** v1.0  
**日期:** 2026-06-12  
**状态:** 待审阅  
**范围:** 配置 PeleC 现有 tagging 参数追踪爆轰波面（零代码开发）

---

## 1. 背景

PeleC 已内置完整的 AMR tagging 框架（`Tagging.cpp`），支持：

| 物理量 | 参数 | 类型 |
|--------|------|------|
| 密度 | `tagging.dengrad` | 梯度阈值 |
| 压力 | `tagging.pressgrad` | 梯度阈值 |
| 温度 | `tagging.tempgrad` | 梯度阈值 |
| 涡量 | `tagging.vorterr` | 相对误差阈值 |
| 组分 | `tagging.ftracerr` / `ftracgrad` | 误差/梯度阈值 |

以及自定义 `refinement_indicators`（支持 `adjacent_difference_greater` = GRAD 标记）。

**结论：爆轰波面 AMR 不需要写任何新代码。** 只需在算例 inputs 中配置合适的 tagging 参数。

## 2. 爆轰波面物理特征

ZND 爆轰结构：
```
     von Neumann spike
         /\
        /  \___ 反应区 (~0.1mm)
       /       \___ 平衡区
______/            \________ 
← 激波              爆轰产物 →
```

需要加密两个区域：
1. **激波波面**（密度/压力跳变）→ `dengrad` + `pressgrad`
2. **反应区**（温度快速上升 + 组分变化）→ `tempgrad` + `ftracgrad`

## 3. 参数配置

### 3.1 推荐初始值

```
tagging.dengrad = 0.05       # 密度梯度阈值（无量纲，针对 ρ~O(1) 背景）
tagging.max_dengrad_lev = 3  # 最大加密层级

tagging.pressgrad = 0.5      # 压力梯度阈值
tagging.max_pressgrad_lev = 3

tagging.tempgrad = 10.0      # 温度梯度阈值（无量纲 T~O(1)）
tagging.max_tempgrad_lev = 2 # 反应区不需要太多层级
```

### 3.2 为什么这些参数

- **dengrad=0.05**：典型爆轰密度比 ~5-8，跨 2-3 格点 → 梯度 ~0.5-2，0.05 足够捕获
- **pressgrad=0.5**：压力跳变 ~100，跨 2-3 格点 → 梯度 ~10-50，0.5 保守
- **tempgrad=10**：反应区温升 ~2000K，但温度场在低分辨率下较平滑
- **max_lev**：激波面加密 3 层（dx/8），反应区 2 层——反应区比激波面宽，不需要太多层级

## 4. 验证算例

用 1D/2D H₂/O₂ 爆轰算例验证：

1. **1D ZND 爆轰**：验证激波面 + 反应区都被正确标记
2. **2D 胞格爆轰**：验证 AMR 能追踪爆轰波面的弯曲结构

### 验证项

| # | 验证项 | 通过条件 |
|---|--------|----------|
| 1 | 激波面被标记 | 密度梯度最大区域在 max_level 层级 |
| 2 | 反应区被标记 | 温度梯度最大区域在中等级别 |
| 3 | 平滑区不被标记 | 远离波面的区域保持 level 0 |
| 4 | 层级过渡合理 | 无单层孤岛（被粗网格包围的细网格） |
| 5 | 性能 | 加密后总格点数 ≤ 不做 AMR 的 3 倍 |

## 5. 实现方式

### 5.1 仅配置文件

在爆轰算例的 `inputs` 中添加 tagging 参数即可，不需要修改源码：

```
# AMR tagging for detonation
tagging.dengrad = 0.05
tagging.max_dengrad_lev = 3
tagging.pressgrad = 0.5
tagging.max_pressgrad_lev = 3
tagging.tempgrad = 10.0
tagging.max_tempgrad_lev = 2

amr.max_level = 3
amr.ref_ratio = 2 2 2 2
amr.regrid_int = 2
```

### 5.2 可选增强（高级）

如果默认 tagging 不够精确，用 `refinement_indicators` 自定义：

```
tagging.refinement_indicators = shock_front flame_zone

tagging.shock_front.field_name = density
tagging.shock_front.adjacent_difference_greater = 0.05

tagging.flame_zone.field_name = Temp
tagging.flame_zone.adjacent_difference_greater = 10.0
```

这等价于上面的全局参数——全局参数更简洁。

## 6. 与 Phase 3.4 的关系

Phase 3.3 提供 tagging 配置，Phase 3.4 用这些配置跑 H₂/O₂ 2D 胞格爆轰。两者可以合并推进：

1. 写爆轰算例输入文件（含 tagging）
2. 跑 2D 胞格爆轰
3. 验证 AMR 追踪效果

## 7. 交付物

- [ ] 1D ZND 爆轰算例配置（含 tagging 参数）
- [ ] 2D 胞格爆轰算例配置（含 tagging 参数）
- [ ] 验证报告：AMR 层级分布图 + 格点数统计
- [ ] code-reviewer Type A 审查 PASS

## 8. 风险评估

| 风险 | 影响 | 缓解 |
|------|------|------|
| 梯度阈值过高 → 波面不加密 | 低精度 | 降低阈值，重跑 |
| 梯度阈值过低 → 全域加密 | 性能降级 | 提高阈值，限制 max_level |
| 反应区太窄 → 单格点标记 | 无效 AMR | 加 buffer（`amr.n_error_buf`）|
| regrid 过于频繁 | 性能开销 | 增大 `amr.regrid_int` |
