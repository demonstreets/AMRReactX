# TASK: 修复 Advance.cpp 中 spray source Copy 的 ncomp

## 问题
`Advance.cpp:303` 对所有 source MF 用 NVAR 做 Copy，但 spray source MF 只有 `num_spray_src` 个分量。

## 修复
**文件**: `/home/cj/my-pele/external/PeleC/Source/Advance.cpp`  
**行号**: ~303

**当前**:
```cpp
for (int src : src_list) {
    amrex::MultiFab::Copy(
        *new_sources[src], *old_sources[src], 0, 0, NVAR, 0);
}
```

**改为**:
```cpp
for (int src : src_list) {
    int ncomp_src = (src == spray_src) ? num_spray_src : NVAR;
    amrex::MultiFab::Copy(
        *new_sources[src], *old_sources[src], 0, 0, ncomp_src, 0);
}
```

## 同时恢复 Particle.cpp
第 85 行恢复为原始值:
```cpp
PeleC::num_spray_src = AMREX_SPACEDIM + 2 + SprayParticleContainer::m_sprayData->N_pc;
```

## 验证
1. `cd /home/cj/my-pele/examples/academic/shock_droplet && make -j8`
2. `./PeleC2d.gnu.ex inputs max_step=200` → 无死机/NaN
3. `cd /home/cj/my-pele/external/PeleC/Exec/RegTests/Spray-Jet && make -j8 && ./PeleC3d.gnu.ex example.inp max_step=10` → 无死机
