# k-epsilon 模型行为分析与改进

## 当前 PeleLMeX k-epsilon 实现
源码位置：/home/cj/my-pele/external/PeleLMeX/Source/

### 源项计算 (PeleLMeX_Diffusion.cpp ~L1890-1945)
```
P_k = max(μ_t * S², 0)              // 无生产限制器
S_k = P_k - ρ * ε                   // 标准形式
S_ε = C_ε1 * ε/k * P_k - C_ε2 * ρ * ε²/k
μ_t = C_μ * ρ * k² / ε              // C_μ=0.09
μ_t ≤ 1e5 * μ_lam                   // 仅上限裁剪
```

### 模型常数 (PeleLMeX.H ~L2152-2160)
```
C_μ=0.09, C_ε1=1.44, C_ε2=1.92
σ_k=1.0, σ_ε=1.3, κ=0.41
```

### 入口边界条件 (bcnormal_aux, 当前算例 c3h8_flacs)
```
k_in = 1.5 * (0.05 * U)²            // 5% 湍流度
ε_in = 0.164 * k_in^1.5 / 0.5       // L=0.5m
```

## 观察到的行为问题

### 现象
算例 c3h8_flacs，t≈1s，160×100×80 网格：
```
P1  = P10 = P50 = 0.00127    ← 50%网格 k 完全相同（均匀衰减）
P90 = 0.242                  ← 仅10%网格有湍流生成
P99 = 0.450
```

### 根因
标准 k-ε 在无速度梯度的自由来流中：P_k=0 → dk/dt=-ε → 单调衰减。
入口虽然注入 k=0.24 (5% TI)，但进入域后立即开始衰减，无法自维持。
这是标准 k-ε 的已知缺陷。

## FLACS k-ε 的可能差异

FLACS 在处理类似算例时可能使用了以下一项或多项改进：

### 1. 生产限制器 (Production Limiter)
```cpp
P_k = min(mut * S2, C_lim * rho * eps)  // C_lim 通常 4-10
// 或
P_k = min(mut * S2, 10.0 * rho * eps)
```
目的：防止滞点处的过度生产，同时让剪切区更快达到平衡。

### 2. Kato-Launder 修正
```cpp
P_k = C_mu * eps * S * Omega  // S=应变率, Omega=涡量
// 或
P_k = C_mu * eps * min(S², S*Omega)
```
目的：滞点处 Omega=0 而 S>0，有效抑制非物理生产。

### 3. 改进的入口条件
- 使用更高湍流度（如 10-20%）匹配来流衰减后的目标值
- 入口 ε 匹配衰减率：ε_in = k_in^1.5 / L，L 取特征涡尺度

### 4. 可实现性修正 (Realizable k-ε, Shih 1995)
- C_μ 不再是常数，而是应变和张量的函数
- 保证正应力和可实现性约束

### 5. 考虑切换到 k-ω SST
- 在自由来流中 k-ω SST 比 k-ε 更稳定
- FLACS 可能也提供此选项

## 建议实现方案（优先级排序）

### 方案 A：生产限制器（最简单）
在 PeleLMeX_Diffusion.cpp 中添加：
```cpp
amrex::Real P_k_raw = mut * S2;
amrex::Real P_k = amrex::min(P_k_raw, 10.0_rt * rho * epsv);
P_k = amrex::max(P_k, 0.0_rt);
```

### 方案 B：合理入口条件
将 bcnormal_aux 中的湍流度从 5% 提高到 10%，L 调整为 1-2m：
```cpp
I = 0.10; L = 2.0;
k_in = 1.5*(I*U)*(I*U);
eps_in = C_mu^0.75 * k_in^1.5 / L;
```

### 方案 C：A+B 组合
同时应用生产限制器和改进的入口条件。

## 验证要求
- 修改后重新编译运行 30 步
- k 分布应有明显改善：P50 不应等于 P1/P10，中位数应与入口条件在合理范围内
- 保持代码可配置：新参数放在 input.3d 中可调

## 算例位置
/home/cj/my-pele/examples/engineering/c3h8_flacs/
