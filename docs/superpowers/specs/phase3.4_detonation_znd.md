# Phase 3.4 Spec: H₂/O₂ 爆轰 — 1D ZND + AMR 验证

**版本:** v1.0  
**日期:** 2026-06-12  
**状态:** 待审阅  
**范围:** 1D ZND 爆轰验证化学机理 + AMR 追踪激波/反应区

---

## 1. 背景

PeleC 的 TGReact 算例提供了反应流模板：
- EOS: Fuego（真实气体）
- 机理: LiDryer（H₂燃烧，9组分：H₂, O₂, H₂O, H, O, OH, HO₂, H₂O₂, N₂）
- 输运: Simple
- 化学积分: SUNDIALS CVODE

3.4 复用这个模板，创建 1D ZND 爆轰 + 2D 胞格爆轰算例。

## 2. 1D ZND 爆轰

### 2.1 物理设置

- 域：[0, 0.1] cm（1mm）
- 初始：左侧 CJ 爆轰后状态（p~18atm, T~3000K），右侧化学当量 H₂/空气（p=1atm, T=300K）
- 反应自发建立 ZND 结构（von Neumann spike → 反应区 → 平衡）
- 运行至稳态（约 10μs）

### 2.2 AMR 配置

```
tagging.dengrad = 0.1
tagging.max_dengrad_lev = 3
tagging.pressgrad = 0.5
tagging.max_pressgrad_lev = 3
tagging.tempgrad = 500
tagging.max_tempgrad_lev = 3
amr.max_level = 3
```

### 2.3 验证项

| # | 验证项 | 通过条件 |
|---|--------|----------|
| 1 | 激波面被标记 | Level 3 格点在密度梯度最大处 |
| 2 | 反应区被标记 | Level 2-3 格点在温度梯度最大处 |
| 3 | ZND 结构正确 | vN spike → 诱导区 → 反应区 → 平衡 |
| 4 | 无负密度/负温度 | 全程 ρ>0, T>0 |
| 5 | 组分守恒 | ∑Y_i = 1, H₂O 最终 > 0.2 |

## 3. 2D 胞格爆轰（可选，优先 1D）

### 3.1 物理设置

- 域：2×1 cm
- 初始：左侧 CJ 状态 + 横向扰动
- 运行至胞格图案稳定

## 4. 实现方式

### 4.1 文件

基于 TGReact 复制：

```
cp -r TGReact DetonationZND
```

修改：
- CMakeLists.txt：保持 Fuego + LiDryer + Simple
- inputs：1D 域，点火参数，AMR tagging
- prob_parm.H：初始状态参数
- prob.cpp/prob.H：1D ZND 初始化

### 4.2 化学当量 H₂/空气

```
H₂ + 0.5(O₂ + 3.76N₂) → H₂O + 1.88N₂
Y_H₂ = 0.0283, Y_O₂ = 0.2264, Y_N₂ = 0.7453
```

### 4.3 CJ 爆轰参数（来自 Cantera）

通过 `cantera-detonation-analysis` skill 预先计算：
- CJ 速度：~1970 m/s
- vN spike：p~30 atm, T~1800K
- 诱导区长度：~0.2mm
- CJ 平衡：p~18 atm, T~3000K

## 5. 风险

| 风险 | 缓解 |
|------|------|
| 化学刚性问题 → NaN | 减小 CFL，增大 CVODE rtol/atol |
| 1D 爆轰不启动 | 提高初始温度/压力比 |
| LiDryer 机理组分多 → 慢 | 用 1D 验证流程先过 |
| 2D 胞格需要长时程 | 先 1D，2D 后续 |

## 6. 交付物

- [ ] 1D ZND 爆轰算例（编译通过 + 能跑）
- [ ] AMR 层级分布验证
- [ ] vN spike + 反应区可视化
- [ ] code-reviewer 审查 PASS
