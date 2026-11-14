# Phase 2.9b — k-ε 物理激活规格文档

**版本：** v1.0（初稿）
**日期：** 2026-06-10
**状态：** 待审查

---

## 1. 背景

Phase 2.9 已将 k-ε 模块编译进 PeleLMeX（头文件可见），但湍流物理尚未接入求解器。本阶段完成物理激活。

## 2. 需要激活的功能

| 功能 | 现状 | 目标 |
|------|------|------|
| 状态变量注册 | 无 | k 和 ε 作为额外输运标量 |
| 涡粘修正 | 只用 μ_lam | μ_eff = μ_lam + μ_t 注入扩散算子 |
| 源项积分 | 无 | P_k - ρε, C_ε1 ε/k P_k - C_ε2 ρ ε²/k |
| 壁面函数 | 无 | Launder-Spalding 壁面 k/ε |

## 3. 实现方案

### 3.1 状态变量注册

PeleLMeX 通过 Passive Scalar 机制支持额外输运标量。在 `pelelmex_prob.cpp` 中利用现有的 scalar 注册接口：

```cpp
// pelelmex_prob.cpp — 在初始化时注册 k 和 ε
// PeleLMeX 已有 mechanism 中可添加 StateDescriptor
// k 索引 = FIRST_SCALAR, ε 索引 = FIRST_SCALAR + 1
```

参考 PeleLMeX 的 PassiveScalar 例子——它通过 YAML 配置即可添加额外标量，不需要改 C++。k 和 ε 可以走同样的路径。

### 3.2 涡粘修正

在 `pelelmex_prob.H` 中添加 hook 函数，在扩散系数计算时注入 μ_t：

```cpp
// 在每个时间步的扩散阶段
// mu_eff = mu_lam + mu_t
// D_eff = D_lam + D_t (scalar diffusion)
// mu_t = C_mu * rho * k^2 / epsilon  (clamp epsilon > eps_min)
// D_t = mu_t / (rho * Sc_t)
```

PeleLMeX 的低马赫求解器在 `PeleLMeX_Diffusion.cpp` 中有 `getDiffusivity` 类型的函数可以挂载。

### 3.3 源项

利用 PeleLMeX 已有的 `problem_modify_ext_sources()` 钩子：

```cpp
void problem_modify_ext_sources(...) {
    // 对每个 cell 计算:
    //   P_k = mu_t * S^2  (S = strain rate magnitude)
    //   S_k = P_k - rho * epsilon
    //   S_eps = C_eps1 * epsilon/k * P_k - C_eps2 * rho * epsilon^2/k
    // 写入 ext_src_arr(FIRST_SCALAR) 和 ext_src_arr(FIRST_SCALAR+1)
}
```

### 3.4 壁面函数

在 `pelelmex_prob.H` 中，对近壁第一层网格：
- `k_wall = u_tau^2 / sqrt(C_mu)`
- `eps_wall = u_tau^3 / (kappa * y_p)`
- `mu_t_wall = rho * kappa * u_tau * y_p * (1 - exp(-y^+/26))^2`

`u_tau` 通过牛顿迭代从 `u_par` 反算（Phase 2.3 已有实现）。

## 4. 文件改动

```
examples/engineering/multi_module_test/
├── pelelmex_prob.H         # 添加涡粘hook + 源项hook + 壁面函数hook
├── pelelmex_prob.cpp       # 注册 k/ε 标量
└── input.yaml              # 添加湍流参数段
```

## 5. 分步验证

### Step A: 注册 + 对流扩散
- 添加 k, ε 为被动标量
- k 初始为均匀小值（1% turbulence intensity）
- 跑 50 步 → 确认 k, ε 出现在 plotfile 中

### Step B: 加源项
- 激活 P_k 生成项
- 跑 50 步 → 确认 k 增长（壁面附近生成）
- 确认不 NaN

### Step C: 加涡粘
- mu_t 注入扩散算子
- 跑 50 步 → 确认速度剖面变化

### Step D: 加壁面函数
- 壁面函数修正 k_wall, eps_wall, mu_t_wall
- 跑 50 步 → 确认不崩溃

### Step E: 全激活 + 验证
- 跑 2.7 平板算例 → 验证对数律
- 跑 2.7 后台阶算例 → 验证再附长度

## 6. 风险

| 风险 | 等级 | 缓解 |
|------|------|------|
| PeleLMeX Passive Scalar 注册方式不明 | HIGH | 先读 PassiveScalar 源码确认注册路径 |
| 涡粘修改影响其他扩散项 | MEDIUM | 只改标量扩散，不动动量方程 |
| 壁面函数需要访问壁面数据 | HIGH | PeleLMeX 是否有壁面数据接口待确认 |

## 7. 回退方案

如果 PeleLMeX 内部 hook 太复杂无法挂载 k-ε，转为**完全 external 方式**：
- k 和 ε 作为外部 ODE 在每个 cell 独立求解
- μ_t 在 `problem_modify_ext_sources()` 以外部分不介入
- 即：我们只做"diagnostic k-ε"，不影响流场
