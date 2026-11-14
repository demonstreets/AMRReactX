# TASK: 修复 bubble_rise EOS 初始化 + 运行验证

## 问题

bubble_rise/prob.H 和 RT 一样——两相都用 `gamma=1.4` ideal gas 算内能，但求解器对液相用 StiffenedGas。同时 p0=1.0 极低。

## 修复 prob.H

参照 RT 修复（3.10c），在同一位置加：
```cpp
#include "StiffenedGas.H"
```

替换能量计算：
```cpp
// 原来: const amrex::Real e = prob_parm.p0 / ((gamma - 1.0) * rho);
// 改为:
const amrex::Real gamma_gas = 1.4;
constexpr StiffenedGasParams sg = {4.4, 6.0e8};
const amrex::Real e = in_bubble ?
    prob_parm.p0 / ((gamma_gas - 1.0) * rho) :  // 气泡(气相): ideal gas
    sg_e(sg, rho, prob_parm.p0);                  // 液体(重相): StiffenedGas
```

UTEMP 同步修复（液相用 sg_T）：
```cpp
constexpr amrex::Real cv_liquid = 4.18e7;
state(i,j,k,UTEMP) = in_bubble ?
    prob_parm.p0 / ((gamma_gas - 1.0) * rho) / (1.0/(gamma_gas-1.0)) :
    sg_T(sg, rho, e, cv_liquid);
```

## 运行

```bash
cd /home/cj/my-pele/examples/academic/bubble_rise
make -j8
rm -rf plt* Backtrace*
./PeleC2d.gnu.ex inputs max_step=500
```

验证: 无 NaN/崩溃，气泡上升，alpha 界面清晰

## 预估

32×64 格, 500 步, ~30 秒
