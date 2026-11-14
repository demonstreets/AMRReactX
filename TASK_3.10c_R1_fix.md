# TASK 3.10c-R1: 修复审查发现的 UTEMP + 静水压力问题

## 文件
`/home/cj/my-pele/examples/academic/rayleigh_taylor/prob.H`

## 修复 1 (HIGH): UTEMP EOS 一致化 (~line 49)

当前代码对两相都用 `gamma_gas=1.4` 算 UTEMP，但液相内能已用 StiffenedGas：
```cpp
state(i,j,k,UTEMP) = e / (1.0 / (gamma_gas - 1.0));  // 两相同公式
```

修复：液相用 `sg_T(sg, rho, e, cv_liquid)`，气相保持原公式。
```cpp
// 在 StiffenedGasParams sg 定义后加:
constexpr amrex::Real cv_liquid = 4.18e7;  // CGS: erg/(g·K), water-like

// 替换 UTEMP 行:
state(i,j,k,UTEMP) = in_heavy ?
    sg_T(sg, rho, e, cv_liquid) :           // 液相: StiffenedGas 温度
    e / (1.0 / (gamma_gas - 1.0));           // 气相: ideal gas 温度
```

## 修复 2 (MEDIUM): 静水压力不用硬编码 Ly (~line 38-41)

当前代码：
```cpp
const amrex::Real p_hydro = in_heavy ?
    prob_parm.p0 + prob_parm.rho_heavy * gravity * (Ly - y) :
    prob_parm.p0 + prob_parm.rho_heavy * gravity * 0.5 + prob_parm.rho_light * gravity * (0.5 - y);
```

修复：用 `Ly` 替代硬编码的 `0.5`（Ly 已在前面定义为 `prob_hi[1] - prob_lo[1]`），使域高度改变时压力连续：
```cpp
const amrex::Real half_Ly = 0.5 * Ly;
const amrex::Real p_hydro = in_heavy ?
    prob_parm.p0 + prob_parm.rho_heavy * gravity * (Ly - y) :
    prob_parm.p0 + prob_parm.rho_heavy * gravity * half_Ly + prob_parm.rho_light * gravity * (half_Ly - y);
```

## 编译验证
`cd /home/cj/my-pele/examples/academic/rayleigh_taylor && make -j8`
