# k-ε PeleLMeX 集成最终方案 Spec v2.0

**产出方式**: 3 agent × 2 轮头脑风暴（2026-06-21）
**前身**: phase2_9b_kepsilon_activation_spec.md（已废弃的宏方案）
**关联审查**: cc-server-workflow/references/multi-agent-spec-review.md（2026-06-21）

---

## 0. 设计目标

用户在 input.yaml 中写：



不需要任何编译宏（）。

---

## 1. 总体架构决策

| 决策 | 结论 | 理由 |
|------|------|------|
| 宏依赖 | **零宏**，运行时  | 三 agent 强共识 |
| 放在 les_model 下 | **Pragmatic 接受** | 当前仅 1 个 RANS 模型；技术债已记录 |
| μ_t 计算位置 | 格心算 μ_t^cc，面心由扩散算子标准插值 | 避免方向性插值 bug |
| 湍流扩散增强 | calcDiffusivity() 内格心 μ_t → diff_aux_cc | 不触动 getDiffusivity 脆弱的 if-else 链 |
| 浮力修正 G_k | **推迟到 Phase 3.11** | 先验证基础链路正确性 |
| DES 限制器 | **不采纳** | 过度工程，Smagorinsky 也无此限制器 |
| 隐式源项 | **不采纳** | 与 SDC 框架冲突 |
| 双层架构 | **技术债记录** | 等第二个 RANS 模型触发 |

---

## 2. 三回合头脑风暴发现的共识与分歧

### 强共识（三 agent 一致）
1. ✅ 运行时 if/else > 编译宏
2. ✅ 面心插值方向性 bug 必须修复
3. ✅ calcDiffusivity() 缺湍流增强是核心缺失
4. ✅ aux floor clipping（扩散求解后 k/ε ≥ 1e-14）必须添加
5. ✅ 方案C(双层+DES+浮力+隐式) 当前阶段改动量过大(340-555行 vs 43行)

### 技术债清单（已记录，等触发条件）
- **RANS/LES 架构分离**: 触发条件 = 第二个 RANS 模型加入
- **浮力修正 G_k**: 触发条件 = Phase 3.11（强制对流验证通过后）
- **多壁面壁面函数**: 触发条件 = 非 y_lo 壁面算例需求
- **SDC 源项归一化**: 触发条件 = m_nSDCmax > 1 的算例

---

## 3. Phase 3.10d：基础集成（43 行，7 处改动）

### 改动清单

| # | 文件 | 改动 | 行数 |
|---|------|------|:---:|
| 1 | PeleLMeX_Setup.cpp:491 | 修复 abort 消息（\"kepsilon\" 从非法列表移除） | 3 |
| 2 | PeleLMeX_TransportProp.cpp:203-212 | 修复面心插值方向性 bug（用 idim 选偏移方向） | 5 |
| 3 | PeleLMeX_TransportProp.cpp:325-371 | calcDiffusivity() 添加格心 μ_t 湍流增强到 diff_aux_cc | 25 |
| 4 | PeleLMeX_TransportProp.cpp:195,217 | #ifdef PELE_USE_KEPSILON → } else if (m_les_model=="kepsilon") | 2 |
| 5 | PeleLMeX_Advance.cpp:209,239,370,399 | #ifdef → 运行时判断（4 处） | 6 |
| 6 | PeleLMeX_Advance.cpp: src include | 移除条件 include | 3 |
| 7 | PeleLMeX_Advance.cpp: post-diffusion | aux floor clipping: k=max(k,1e-14), ε=max(ε,1e-14) | 4 |
| **合计** | | | **~48** |

### 改动 #3 核心代码（calcDiffusivity 湍流增强）

# 0 "<stdin>"
# 0 "<built-in>"
# 0 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 0 "<command-line>" 2
# 1 "<stdin>"

### 改动 #2 核心代码（面心插值修复）

# 0 "<stdin>"
# 0 "<built-in>"
# 0 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 0 "<command-line>" 2
# 1 "<stdin>"

---

## 4. Phase 3.11：浮力修正（后续，40-70 行）

触发条件：Phase 3.10d 在后台阶/槽道流（强制对流主导）完全验证通过。

新增 G_k = -β·g_i·(μ_t/σ_t)·∂T/∂x_i 到 k 方程源项：
- 需要格心温度梯度 → 新增 MultiFab 容器（3D: 3 分量）
- β = 1/T（理想气体热膨胀系数）
- 仅对氢气泄漏/羽流场景显著（远场 G_k/P_k ~ 10-100）
- ε 方程加 C_ε3·tanh(|v_vert|/u_par)·(ε/k)·G_k

---

## 5. 验收标准

- [ ]  无需编译宏直接可用
- [ ] Smagorinsky/WALE/Sigma/None 路径零影响
- [ ] 面心插值方向正确（3D 验证各方向面 μ_t 一致）
- [ ] 编译零警告
- [ ] 100 步无崩溃
- [ ] 后台阶算例再附长度与 Driver & Seegmiller (1985) 对比，误差 < 20%

---

## 6. 对比原 scheme v1.0（2016-06-10 宏方案）

| 维度 | v1.0 宏方案 | v2.0 运行时方案 |
|------|-----------|---------------|
| 编译宏 | PELE_USE_KEPSILON | 无 |
| 崩溃根因修复 | 否（未诊断） | 是（ncomp=2 路径绕过） |
| 面心插值 | bug 存在 | 已修复 |
| 湍流扩散增强 | 缺失 | 格心 μ_t → diff_aux_cc |
| aux floor clipping | 缺失 | 已添加 |
| 浮力 | 无 | Phase 3.11 |
| 总行数 | ~51（不完整） | ~48 + Phase 3.11: ~55 |

---

## 7. 已知局限（技术债已记录）

1. RANS 放在 les_model 下——等第二个 RANS 模型触发重构
2. 壁面函数仅支持 y_lo——等非 y_lo 壁面算例触发
3. AMR regrid 后 k/ε 独立插值破坏 μ_t ∝ k²/ε 关系——已在 spec 中记录，严重程度评估为 MEDIUM
4. m_nSDCmax > 1 时 SDC 源项可能叠加——默认 m_nSDCmax=1 不影响，等需要多 SDC 时修复

---

*三回合头脑风暴参与 Agent: 架构师(Agent A) + 物理专家(Agent B) + 故障分析师(Agent C) × 2 轮交叉批判*
*最终收敛: 混合方案 = 方案1(运行时) + aux clipping + 浮力推迟 + 技术债记录*
