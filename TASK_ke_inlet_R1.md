# TASK: 修复 k-ε 入口湍流审查 3 个问题

## 修复 1 (HIGH): aux 索引硬编码 → 加运行时检查

在 PeleLMeX_BC.cpp 的 inlet BC 代码块开头加：
```cpp
// k-ε aux convention: aux[0]=k, aux[1]=ε (established in 3.10d)
AMREX_ASSERT(m_aux_names.size() >= 2);
AMREX_ASSERT(m_aux_names[0] == "k" || m_aux_names[0] == "turb_kin_energy");
AMREX_ASSERT(m_aux_names[1] == "epsilon" || m_aux_names[1] == "turb_diss_rate");
```
不改索引，只加断言保护。与 3.10d 其他硬编码处一致。

## 修复 2 (MEDIUM): 默认 TI 改 0

PeleLMeX.H: `m_ke_inlet_TI = 0.0` (原 0.01)
BC 条件从 `TI > 0` 改为 `TI > 1e-10`

## 修复 3 (MEDIUM): L_t 除零防护

BC 代码中 `1.0 / m_ke_inlet_L` 前加：
```cpp
amrex::Real L_t = amrex::max(m_ke_inlet_L, 1e-10_rt);
```

## 文件
- `/home/cj/my-pele/external/PeleLMeX/Source/PeleLMeX.H` (默认值)
- `/home/cj/my-pele/external/PeleLMeX/Source/PeleLMeX_BC.cpp` (断言+防护)

## 验证
编译: `cd bfs_kepsilon && make -j8`
运行: 100步确认 TI=0.05 时入口 k/ε 正确，TI=0 时 BC 不施加
