# Phase 2.5 — 液体池蒸发源项规格文档

**版本：** v1.0（初稿）
**日期：** 2026-06-09
**状态：** 待审查

---

## 1. 物理背景

开放空间危险气体泄漏场景中，泄漏源常为**地面液体池**（如 LNG 泄漏、汽油泄漏）。液体在池中持续蒸发，蒸气扩散至大气形成可燃云团。蒸发速率由**传热-传质耦合**决定，受风速、池温、太阳辐射、地面导热等因素影响。

本模块提供物理蒸发模型，替代"直接指定质量流量"的简单做法，使工程算例更贴近真实物理。

---

## 2. 模型选择

### 2.1 三层模型体系

| 层级 | 模型 | 输入 | 适用场景 |
|------|------|------|---------|
| **Level 0** | 恒定蒸发率 | 用户指定 ṁ″ (kg/m²/s) | 快速测试、与已有泄漏源对接 |
| **Level 1** | 对流传质模型 | 风速 u_ref、池尺寸 L、池温 T_p、物种 | 稳态工程评估（推荐） |
| **Level 2** | 传热-传质耦合 | Level 1 + 地面/太阳/辐射 | 瞬态降温（LNG 沸腾等） |

Phase 2.5 实现 **Level 1**（对流传质模型），Level 2 预留接口后续扩展。

### 2.2 Level 1：对流传质模型

蒸发质量通量：

\[
\dot{m}'' = k_m \cdot \left( \rho_{v,sat}(T_p) - \rho_{v,\infty} \right)
\]

其中：

- \(k_m\) [m/s] — 对流传质系数
- \(\rho_{v,sat}(T_p)\) [kg/m³] — 池面温度下的饱和蒸气密度
- \(\rho_{v,\infty}\) [kg/m³] — 环境蒸气密度（通常 ≈ 0）

**传质系数 \(k_m\)（FLACS 风格）：**

基于表面更新理论（Surface Renewal Theory），由摩擦速度 \(u_*\) 驱动：

\[
k_m = \frac{u_*}{\kappa} \cdot \frac{1}{Sc_t + 5.0 \cdot Sc^{2/3} - 5.0}
\]

其中：
- \(u_* = \sqrt{C_f} \cdot u_{ref}\) — 摩擦速度 [m/s]
- \(C_f = 0.001\) — 表面摩擦系数（水面默认值，可配）
- \(\kappa = 0.41\) — von Kármán 常数
- \(Sc_t = 0.7\) — 湍流 Schmidt 数（与 Phase 2.4 一致）
- \(Sc = \nu / D\) — 层流 Schmidt 数
- \(\nu\) — 空气运动粘度 ≈ 1.5×10⁻⁵ m²/s
- \(D\) — 物种在空气中的扩散系数 [m²/s]

**饱和蒸气密度 \(\rho_{v,sat}(T_p)\)：**

通过 Antoine 方程计算饱和蒸气压，再转为密度：

\[
P_{sat}(T) = 10^{A - B/(T + C)} \quad [\text{Pa}]
\]
\[
\rho_{v,sat} = \frac{P_{sat} \cdot M_v}{R \cdot T_p}
\]

Antoine 常数 A, B, C 用户配置（常用物质预设）。
\(M_v\) — 蒸气分子量 [kg/mol]，\(R = 8.314\) J/(mol·K)。

### 2.3 简化选项：恒定蒸发率（Level 0）

用户直接指定 \(\dot{m}''\) [kg/m²/s]，绕过物理模型。实现上与 Level 1 共享下游注入管线。

---

## 3. PeleLMeX 嵌入方案

### 3.1 源项位置

液体池位于计算域底面（y = y_min），池面积由用户指定。蒸发蒸气以**体积源项**形式施加于池面上方第一层网格：

\[
S_{\rho Y_k} = \frac{\dot{m}''}{dy_{cell}} \quad [\text{kg/m³/s}]
\]

\(dy_{cell}\) 为第一层网格的 y 方向尺寸。

### 3.2 能量源项

蒸气蒸发从液体池吸收潜热，对气相是冷却效应：

\[
S_{\rho E} = -S_{\rho Y_k} \cdot h_{v,form}(T_p)
\]

其中 \(h_{v,form}(T_p)\) 为蒸气在池温下的生成焓 [J/kg]。

### 3.3 动量源项

蒸发蒸气离开液面时速度很低（≈ 0），不施加动量源项。

### 3.4 接口

通过 `problem_modify_ext_sources()` 钩子接入 PeleLMeX 时间积分：

```cpp
void problem_modify_ext_sources(
    const amrex::Box& bx,
    const amrex::Array4<amrex::Real>& ext_src_arr,
    ... // other arrays as needed
) {
    // 1. 计算蒸发通量 mdot_per_area
    // 2. 将通量转为体积源项（除以 dy）
    // 3. 写入 ext_src_arr（species + energy）
}
```

注意 AMReX ext_src 的已知规则：**不与 dt 相乘**，直接累加到 RHS。

### 3.5 与已有模块的关系

| 已有模块 | 关系 |
|---------|------|
| Phase 2.4 湍流-扩散耦合 | Sc_t 共用；D_t 增强蒸气扩散 |
| Phase 2.3 壁面函数 | u_* 从壁面函数获取（未来增强，当前用摩擦系数） |
| YAML 输入 | 池几何、物性、模型选择由 YAML 读取 |

---

## 4. 代码模块设计

### 4.1 文件结构

```
src/engineering/evaporation/
├── evaporation_model.H      # 蒸发模型（k_m、ṁ'' 计算）
├── pool_evaporation.H       # 池蒸发主类（池温、物性、热平衡）
├── antoine_data.H           # Antoine 常数数据库（常用物质预设）
├── evaporation_source.H     # AMReX ext_src 施加器
└── evaporation_yaml.H       # YAML 参数解析
```

### 4.2 头文件接口

#### `evaporation_model.H`

```cpp
namespace Evaporation {

struct EvaporationParams {
    double u_ref;          // 参考风速 [m/s]
    double T_pool;         // 池温 [K]
    double C_f;            // 摩擦系数 (默认 0.001)
    double pool_length;    // 池长度 [m]（沿风向）
    double Sc_t;           // 湍流 Schmidt 数
    // 物种物性
    double M_v;            // 蒸气分子量 [kg/mol]
    double D_air;          // 扩散系数 [m²/s]
    double L_v;            // 蒸发潜热 [J/kg]
    double h_v_form;       // 蒸气生成焓 [J/kg]
    // Antoine 常数
    double A, B, C;        // log10(P[Pa]) = A - B/(T[K] + C)
};

// 摩擦速度
inline double friction_velocity(double u_ref, double C_f);

// 传质系数（表面更新理论）
inline double mass_transfer_coefficient(double u_star, double kappa,
                                         double Sc, double Sc_t);

// 饱和蒸气压 (Antoine)
inline double saturation_pressure(double T, double A, double B, double C);

// 饱和蒸气密度
inline double saturation_density(double T, double P_atm,
                                  double M_v, double A, double B, double C);

// 蒸发质量通量 (Level 1)
inline double evaporation_flux(double k_m, double rho_sat, double rho_inf);

} // namespace Evaporation
```

#### `pool_evaporation.H`

```cpp
namespace Evaporation {

struct PoolGeometry {
    double x_lo, x_hi;     // 池范围 [m]
    double y_lo, y_hi;     // y_lo = y_hi = 底面
    double z_lo, z_hi;     // 池范围 [m]
};

class PoolEvaporation {
public:
    // 从 YAML 初始化
    void init_from_yaml(const YamlNode& yaml);

    // 返回当前蒸发质量通量 [kg/m²/s]
    double get_mass_flux() const;

    // 返回物种生成焓 [J/kg]
    double get_vapor_formation_enthalpy() const;

    // 返回蒸气物种 index
    int    get_vapor_species_index() const;

    // 判断 cell 是否在池内
    bool   cell_in_pool(double x, double y, double z) const;

private:
    PoolGeometry  geom_;
    EvaporationParams params_;
    double m_dot_per_area_;  // kg/m²/s
    int    vapor_species_idx_;
};
} // namespace Evaporation
```

### 4.3 单元测试

```cpp
// test/unit/test_evaporation.cpp
// 测试项：
//   1. friction_velocity: u_ref=5, C_f=0.001 → u* = 0.1581
//   2. mass_transfer_coefficient: u*=0.1581, Sc=1.0, Sc_t=0.7 → k_m 验证
//   3. saturation_pressure: 水 373.15K → ≈101325 Pa
//   4. saturation_density: 水 373.15K → ≈0.597 kg/m³
//   5. evaporation_flux: k_m=0.01, rho_sat=0.597, rho_inf=0 → 0.00597
//   6. cell_in_pool: 池 x=[0,2] z=[0,1] → (1, any, 0.5) = true, (3, any, 0.5) = false
//   7. 完整 PoolEvaporation init → get_mass_flux() 验证
//   8. Level 0 constant flux mode
//   9. y_lo==y_hi 断言（池必须在单一水平面上）
```

---

## 5. YAML 输入格式草案

### 5.1 方式一：内置数据库（推荐）

常用危险物质已预设 Antoine 常数。只需指定物种名：

```yaml
evaporation:
  pool:
    x_lo: 0.0
    x_hi: 2.0
    y:     0.0
    z_lo: 0.5
    z_hi: 1.5
  model: mass_transfer
  vapor_species: propane    # 从内置数据库查表
  u_ref: 3.0
  T_pool: 293.0
  C_f: 0.001
  pool_length: 2.0
```

内置数据库预设（`antoine_data.H`）：

| 物质 | 别名 | 分子式 | M_v [g/mol] | A | B | C | T_range [K] |
|------|------|--------|------------|---|---|---|---|
| methane | CH4, LNG | CH₄ | 16.04 | 6.69561 | 405.42 | 267.777 | 91–190 |
| propane | C3H8 | C₃H₈ | 44.10 | 6.95719 | 1424.255 | -45.957 | 165–370 |
| n-hexane | hexane, gasoline | C₆H₁₄ | 86.18 | 6.91058 | 1189.64 | 226.28 | 250–510 |
| ammonia | NH3 | NH₃ | 17.03 | 7.55466 | 1002.711 | 247.885 | 195–405 |
| chlorine | Cl2 | Cl₂ | 70.91 | 6.92717 | 862.72 | 221.44 | 200–420 |
| water | H2O | H₂O | 18.02 | 8.07131 | 1730.63 | 233.426 | 274–645 |

> **注**：Antoine 常数来源 NIST Chemistry WebBook。形式：\(\log_{10} P_{sat}[\text{mmHg}] = A - B/(t[°\text{C}] + C)\)。
> `saturation_pressure()` 内部将 \(T[\text{K}] \to t[°\text{C}] = T - 273.15\)，计算 mmHg 值后 \(\times 133.322\) 转为 Pa。
> 用户自定义常数时同样使用此形式（mmHg + °C），方便直接复用 NIST 查表值。

### 5.2 方式二：自定义物性（覆盖数据库）

如果内置数据库没有你的物质，或你要用自己的参数，直接在 YAML 里写全：

```yaml
evaporation:
  pool:
    x_lo: 0.0
    x_hi: 2.0
    y:     0.0
    z_lo: 0.5
    z_hi: 1.5
  model: mass_transfer
  vapor_species: my_custom_gas    # 任意名称
  u_ref: 3.0
  T_pool: 293.0
  C_f: 0.001
  pool_length: 2.0
  D_air: 1.2e-5
  L_v: 3.5e5

  # 自定义物性（覆盖内置数据库）
  custom_properties:
    M_v: 58.12          # 分子量 [g/mol]
    antoine_A: 7.01234
    antoine_B: 1580.0
    antoine_C: -35.0
    h_v_form: -2.5e6    # 蒸气生成焓 [J/kg]
```

### 5.3 方式三：恒定蒸发率（Level 0）

```yaml
evaporation:
  pool:
    x_lo: 0.0
    x_hi: 2.0
    y:     0.0
    z_lo: 0.5
    z_hi: 1.5
  model: constant
  vapor_species: C3H8
  mass_flux: 0.05       # kg/m²/s — 直接指定
  h_v_form: -2.5e6      # 需要手动给生成焓


### 5.4 运行时逻辑

```
YAML 解析 → vapor_species 查内置数据库
   ├── 找到 → 用内置 A, B, C, M_v, L_v, h_v_form
   ├── 没找到 → 检查 custom_properties 块
   │     ├── 有 → 用自定义参数
   │     └── 没有 → 报错退出
   └── 找到但 YAML 里写了 custom_properties → 自定义覆盖内置
```

---

## 6. 风险与局限性

| 风险 | 等级 | 缓解 |
|------|------|------|
| Antoine 常数与 PelePhysics 机理不匹配 | MEDIUM | 内置常见物种预设，允许用户覆盖 |
| 池面积网格分辨率不足 → 源项稀释 | LOW | 文档说明建议网格尺寸，类似泄漏源 |
| 池温恒定假设不适用瞬态 LNG 泄漏 | LOW | Level 2 预留，Phase 2.7+ 扩展 |
| ext_src 不与 dt 相乘的坑 | LOW | 已知问题，文档+测试覆盖 |
| PeleLMeX 底面 BC 与蒸发源项冲突 | MEDIUM | 池区域底面设 slip wall，不设 species BC |

---

## 7. 验证方案

| 验证项 | 方法 | 判据 |
|--------|------|------|
| Antoine 方程精度 | 查 NIST 标准值比对 | 偏差 < 1% |
| k_m 与文献对比 | Mackay & Matsugu (1973) 风洞实验 | 量级一致 |
| 蒸发质量守衡 | 积分蒸气总质量 vs 累积蒸发量 | 偏差 < 1% |
| 能量守衡 | 蒸发潜热 × 蒸发量 = 气相能量减少 | 偏差 < 1% |
| 零风速退化 | u_ref=0 → k_m→0 → ṁ''→0 | 精确 0 |

---

## 8. 后续扩展（Phase 2.x+）

- **Level 2 热平衡模型**：池温 ODE（地面导热 + 大气对流 + 辐射 + 蒸发冷却）
- **池扩展模型**：液体池随时间扩大（重力驱动铺展），与蒸发耦合
- **沸腾传热**：LNG 泄漏时池温固定于沸点，k_m 用沸腾修正
- **多组分蒸发**：混合液体（汽油）中不同组分蒸气压不同

---

*注：本 spec 为初稿，待审查后确定最终接口。*
