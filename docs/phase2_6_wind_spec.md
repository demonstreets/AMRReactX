# Phase 2.6 — 风场边界条件规格文档

**版本：** v1.0（初稿）
**日期：** 2026-06-09
**状态：** 待审查

---

## 1. 物理背景

开放空间气体泄漏扩散场景中，大气风场是驱动可燃云团输运的主导因素。本模块实现**大气边界层风剖面 + 自动风向面类型判断**，以边界条件形式嵌入 PeleLMeX。

参考工业标准：FLACS 风场处理方式（对数律入口 + 自动出口判断）。

---

## 2. 模型设计

### 2.1 风向/风速输入

| 参数 | 说明 | 示例 |
|------|------|------|
| `direction` | 气象风向（风**来**的方向） | SSW / 202.5 |
| `speed` | 参考高度处的风速 [m/s] | 3.0 |
| `reference_height` | 风速测量的参考高度 [m] | 10.0 |
| `roughness_length` | 空气动力学粗糙长度 \(z_0\) [m] | 0.03（开阔地） |

**风向约定：**
- 气象惯例：0°=北，90°=东，顺时针
- SSW = 202.5°
- 风**吹向** = 方向角 + 180°（SSW → NNE）

### 2.2 坐标映射

默认映射（可覆盖）：

| 坐标轴 | 物理方向 |
|--------|---------|
| \(+x\) | 东 |
| \(+y\) | 垂直向上 |
| \(+z\) | 北 |

风向角 \(\theta\)（从北顺时针）→ 风速矢量：

\[
\begin{aligned}
u_{wind, x} &= -u \cdot \sin\theta \\
u_{wind, y} &= 0 \\
u_{wind, z} &= -u \cdot \cos\theta
\end{aligned}
\]

负号表示风吹**向**（气象风向来，计算域内目标速度去向）。

### 2.3 对数律风剖面

摩擦速度：

\[
u_* = \frac{\kappa \cdot u_{ref}}{\ln(z_{ref} / z_0)}
\]

其中 \(\kappa = 0.41\)（von Kármán 常数，与 Phase 2.2 一致）。

速度剖面：

\[
u(z) = \frac{u_*}{\kappa} \ln\left(\frac{\max(z, z_0)}{z_0}\right)
\]

\(z < z_0\) 时取 \(z = z_0\)（避免 ln(≤1)）。

### 2.4 k-ε 入口剖面

配合 Phase 2.2 湍流模型，入口处同时指定 \(k, \varepsilon\) 剖面。标准大气边界层维持剖面：

\[
\begin{aligned}
k(z) &= \frac{u_*^2}{\sqrt{C_\mu}} \cdot \sqrt{1 - \frac{z}{\delta}} \\
\varepsilon(z) &= \frac{u_*^3}{\kappa z} \cdot \left(1 - \frac{z}{\delta}\right)
\end{aligned}
\]

简化形式（\(\delta \gg z\)，即计算域高度远小于边界层厚度）：

\[
k(z) \approx \frac{u_*^2}{\sqrt{C_\mu}}, \quad
\varepsilon(z) \approx \frac{u_*^3}{\kappa z}
\]

其中 \(C_\mu = 0.09\)（KEpsilonConstants）。

### 2.5 面类型自动判断

对六个边界面的每一个，计算风速方向矢量 \(\mathbf{v}_{wind}\) 与该面外法向 \(\mathbf{n}\) 的点积：

\[
d = \mathbf{v}_{wind} \cdot \mathbf{n}
\]

| 条件 | 面类型 | BC |
|------|--------|-----|
| \(d < -\varepsilon\) | 入口 (inlet) | 速度剖面、\(k, \varepsilon\) 剖面、固定温度 |
| \(d > +\varepsilon\) | 出口 (outlet) | 压力出口、零梯度 |
| \(|d| \leq \varepsilon\) | 侧向 (side) | slip wall |
| — | 底面 (y=ymin) | 壁面（使用 Phase 2.3 壁面函数） |
| — | 顶面 (y=ymax) | symmetry |

\(\varepsilon = 1\times10^{-6} \cdot |\mathbf{v}_{wind}|\)。

**示例：SSW (\(\theta=202.5°\)) 风，x方向为主**

| 面 | 法向 | 点积 | 类型 |
|----|------|------|------|
| x_lo | (-1,0,0) | \(-u_x > 0\) | 出口 ✓（风吹出去） |
| x_hi | (+1,0,0) | \(u_x < 0\) | 入口 ✓（SSW→NNE，有-x分量） |
| y_lo | (0,-1,0) | 0 | 壁面 |
| y_hi | (0,+1,0) | 0 | symmetry |
| z_lo | (0,0,-1) | \(-u_z > 0\) | 出口 |
| z_hi | (0,0,+1) | \(u_z < 0\) | 入口（SSW→NNE，有-z分量） |

---

## 3. PeleLMeX 嵌入方案

### 3.1 BC 施加方式

通过 PeleLMeX 的 `prob_bc()` 或 YAML 输入文件中的 `bc` 段指定边界条件标签，然后在初始化时根据风向自动填入对应面的速度剖面。

**简化方案（Phase 2.6 推荐）：**

在 YAML 解析阶段完成面类型判断，直接生成 PeleLMeX 能识别的 BC 配置。因为 PeleLMeX 的 BC 是静态配置（编译期确定标签，运行期通过 `bcvalues` 数组查值），风场 BC 需要的是：

1. 确定每面的 BC 类型标签（inlet/outlet/slip）
2. 入口面上按高度给出速度值

**实现路径：**
- 新增 `wind_bc.H`：提供函数 `apply_wind_bc(bc_type, z_coord, bc_values)` → 根据高度填入 u, v, w, T, k, ε
- YAML 解析阶段自动生成 inlet 面上的速度剖面为数据表（或用解析函数在运行时求值）

### 3.2 接口

```cpp
namespace Wind {

struct WindConfig {
    double direction_deg;     // 气象风向 [°]
    double u_ref;             // 参考风速 [m/s]
    double z_ref;             // 参考高度 [m]
    double z0;                // 粗糙长度 [m]
    double T_inlet;           // 入口温度 [K]

    // 计算得到的
    double u_star;            // 摩擦速度 [m/s]
    double wind_x, wind_z;    // 风速矢量分量 [m/s]
};

// 从 YAML 初始化
WindConfig parse_wind_yaml(const YamlNode& node);

// 计算给定高度处的速度
double log_law_velocity(double z, double u_star, double z0, double kappa);

// 计算给定高度处的入口 k, ε
double inlet_k(double z, double u_star, double C_mu, double delta);
double inlet_epsilon(double z, double u_star, double kappa, double delta);

// 面类型枚举
enum class FaceType { INLET, OUTLET, SLIP, WALL, SYMMETRY };

// 根据风向判断面类型
FaceType classify_face(double normal_dot_wind, double eps = 1e-10);

// 入口面 BC 值填充
struct InletBC {
    double u, v, w;          // 速度 [m/s]
    double T;                // 温度 [K]
    double k, epsilon;       // 湍流变量
};
InletBC compute_inlet_bc(double z, const WindConfig& cfg);

} // namespace Wind
```

### 3.3 与已有模块关系

| 已有模块 | 关系 |
|---------|------|
| Phase 2.2 k-ε | 入口 k, ε 剖面 → 湍流变量 BC |
| Phase 2.3 壁面函数 | 底面 y=ymin 用壁面函数，与风场耦合 |
| Phase 2.4 湍流-扩散 | Sc_t 共用，入口湍流扩散自然产生 |
| Phase 2.5 蒸发源项 | 风场为蒸发提供 u_ref，驱使传质 |
| YAML 输入 | 风场参数从 YAML 读取 |

---

## 4. 代码模块设计

### 4.1 文件结构

```
src/engineering/wind/
├── wind_profile.H           # 风剖面物理（log-law, k, ε 入口剖面）
├── wind_bc.H                # 面类型判断 + BC 填充
└── wind_yaml.H              # YAML 解析
```

### 4.2 单元测试

```cpp
// test/unit/test_wind.cpp
// 测试项：
//   1. 风向→矢量: SSW(202.5°) → u_x≈-0.383, u_z≈-0.924 (归一化)
//   2. 对数律: u_*=0.185, z0=0.03, z=10 → u≈3.0 (验证参考高度闭合)
//   3. 对数律 z<z0: z=0.01 < z0=0.03 → z钳制到z0, u→0
//   4. 摩擦速度: u_ref=3, z_ref=10, z0=0.03 → u_*≈0.185
//   5. 面分类: 风x分量负→入、正→出; 侧向在内
//   6. 入口k: u_*=0.185, C_mu=0.09 → k≈0.114 (u_*²/√C_mu)
//   7. 入口ε: u_*=0.185, z=10, κ=0.41 → ε≈0.00155
//   8. 完整 InletBC 计算
//   9. z0=0 默认值 → 自动设为 1e-4
//  10. 多风向枚举: N/S/E/W/SSW/NNE 全覆盖
```

---

## 5. YAML 输入格式

```yaml
wind:
  direction: SSW           # 气象风向：N/SSW/202.5 均支持
  speed: 3.0               # 参考高度处风速 [m/s]
  reference_height: 10.0   # 参考高度 [m]
  roughness_length: 0.03   # 粗糙长度 [m]
  temperature: 293.0       # 入口温度 [K]

  # 可选：手动覆盖面类型（调试用，正常不用）
  # face_override:
  #   x_lo: inlet
  #   x_hi: outlet
  #   z_lo: slip
  #   z_hi: slip
```

### 5.1 风向解析规则

```
输入                → 输出
"N" / "North"       → 0°
"SSW"               → 202.5°
"202.5"             → 202.5°

16方位支持：N, NNE, NE, ENE, E, ESE, SE, SSE,
            S, SSW, SW, WSW, W, WNW, NW, NNW
```

### 5.2 粗糙长度参考值

| 地形 | z₀ [m] |
|------|--------|
| 开阔水面 | 0.0002 |
| 平坦草地 | 0.03 |
| 农田/低矮植被 | 0.1 |
| 郊区 | 0.5 |
| 城市 | 2.0 |

---

## 6. 风险与局限性

| 风险 | 等级 | 缓解 |
|------|------|------|
| 入口 k, ε 剖面不维持（湍流衰减） | MEDIUM | 入口剖面是标准做法，衰减速度慢；必要时 Phase 2.7 验证 |
| 风向不沿网格轴时多面入口 | LOW | PeleLMeX 支持多 inlet 面 |
| z₀ 与壁面函数 y₀ 不一致 | MEDIUM | 文档说明；z₀ 影响风剖面，y₀ 影响近壁 ∂u/∂y |
| 出口回流（涡旋从 outlet 进） | LOW | 后续如出现可加 sponge layer |
| PeleLMeX BC 框架限制（静态标签） | MEDIUM | 可能需要在 YAML 里硬编码风向对应的 BC 标签，而非纯运行时判断 |

---

## 7. 验证方案

| 验证项 | 方法 | 判据 |
|--------|------|------|
| 风向解析正确性 | 16方位全覆盖单元测试 | 100% |
| 对数律闭合 | u(z_ref) = u_ref | 偏差 < 0.1% |
| 摩擦速度 vs 文献 | u_* 与标准公式比对 | 精确一致 |
| 入口 k, ε 剖面 | 与 k-ε 标准入口公式比对 | 精确一致 |
| 面分类逻辑 | 6 面 × 8 主风向全覆盖 | 100% |

---

*注：本 spec 待审查后确定最终接口。*
