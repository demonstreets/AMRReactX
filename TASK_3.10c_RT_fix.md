# TASK 3.10c: 修复 RT 不稳定性 NaN — EOS 初始化不一致

## 根因

`prob.H` 中 `pc_initdata` 对液相用 `gamma=1.4` (ideal gas) 算内能，但求解器用 StiffenedGas (γ_l=4.4, p_∞=6.0e8) 反解压力 → 液体柱压力全为负 → clamp 到 1.0 → 静力平衡被破坏 → NaN。

## 修复

**文件**: `/home/cj/my-pele/examples/academic/rayleigh_taylor/prob.H`

**改动**: 在 `pc_initdata` 中，对重流体 (in_heavy==true) 用 StiffenedGas 公式算内能，对轻流体保持 ideal gas。

```cpp
// 在函数开头加入:
#include "StiffenedGas.H"  // 如果没有的话

// 替换 energy 计算部分 (约第32行):
//  原来: const amrex::Real e = p_hydro / ((gamma - 1.0) * rho);
//  改为:
    constexpr amrex::Real gamma_gas = 1.4;
    constexpr StiffenedGasParams sg = {4.4, 6.0e8};  // gamma_l, p_inf [dyn/cm²]
    const amrex::Real e = in_heavy ?
        sg_e(sg, rho, p_hydro) :                            // 液相: StiffenedGas
        p_hydro / ((gamma_gas - 1.0) * rho);                // 气相: ideal gas
```

**注意**: 
- `StiffenedGas.H` 路径是 `src/academic/twophase/StiffenedGas.H`
- 需要确认 `prob.H` 是否已有 `#include "StiffenedGas.H"`，如果没有就加上
- `sg_e(sg, rho, p)` 返回 `e = (p + gamma*p_inf) / ((gamma-1)*rho)`
- `StiffenedGasParams` 和 `sg_e` 都有 `AMREX_GPU_DEVICE` 标记，ParallelFor 兼容

## 验证

1. 在 `/home/cj/my-pele/examples/academic/rayleigh_taylor/` 执行 `make -j8`
2. 编译通过后运行 `./PeleC2d.gnu.ex inputs`，跑 200 步
3. 确认: 无 NaN、密度范围保持 ~1.0-2.0、alpha 界面扰动正常增长
