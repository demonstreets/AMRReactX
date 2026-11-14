# TASK: PeleLMeX k-ε 入口湍流便捷参数

## 目标

用户在 input.yaml 写两行就能设入口湍流：
```yaml
peleLM.ke_inlet_TI = 0.05   # 湍流强度
peleLM.ke_inlet_L = 0.0381  # 湍流长度尺度 [m]
```
默认 TI=0.01, L=1.0（不影响现有算例）

## 实现方案

### 1. PeleLMeX.H (声明)
在 k-ε 参数区域（m_ke_eps_amb 附近，~2160行）添加：
```cpp
amrex::Real m_ke_inlet_TI = 0.01;
amrex::Real m_ke_inlet_L = 1.0;
```

### 2. PeleLMeX_Setup.cpp (读取)
在 k-ε 参数读取区域（ke_eps_amb 附近，~500行）添加：
```cpp
pp.query("ke_inlet_TI", m_ke_inlet_TI);
pp.query("ke_inlet_L", m_ke_inlet_L);
```

### 3. PeleLMeX_BC.cpp (施加BC)

在 `fillPatchAux` 函数末尾，fillpatch 完成后，对 k-ε 入口边界施加 Dirichlet 值。

如果 `m_les_model == "kepsilon" && m_nAux >= 2 && m_ke_inlet_TI > 0`:

对每个 level，遍历 Inflow 类型的物理边界，将 aux 变量第 0 分量（k）和第 1 分量（ε）的 ghost cell 值覆盖为入口值。

入口值计算：
```
U_mag = sqrt(VELX² + VELY² + VELZ²)  // 从 state 读取入口速度
k_inlet = 1.5 * (m_ke_inlet_TI * U_mag)²
ε_inlet = Cμ^0.75 * k_inlet^1.5 / m_ke_inlet_L
```

### 4. 注意事项

- 如果 m_ke_inlet_TI = 0（默认）, 不施加任何入口 BC，行为与现在完全一致
- 只在 Inflow 类型物理边界施加，SlipWall/NoSlipWall 不受影响
- U_mag 从入口面的 state 值读取
- 使用 `m_phys_bc` 判断哪些方向是 Inflow

### 参考
- 物理 BC 类型判断：PeleLMeX_BC.cpp 中 `lo_bc`/`hi_bc` 变量
- Inflow BC 常量：PeleLMeX_BC.cpp 开头有各种 BC 映射表
- k-ε aux 分量：aux[0]=k, aux[1]=ε（已在 3.10d 中确立）

## 预估

4 文件, ~30 行新代码。编译 ~1 分钟。验证：向后兼容（TI=0 时不影响现有算例），TI>0 时入口设正确 k/ε。
