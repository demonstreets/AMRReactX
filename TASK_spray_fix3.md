# TASK: 修复 Particle.cpp 第 85 行

第 20 行的声明已改为 NVAR，但 `spraySetup()` 函数内第 85 行又把值覆盖回了旧值。

**只改一行**:

文件: `/home/cj/my-pele/external/PeleC/Source/Particle.cpp`  
第 85 行, 当前:
```
  PeleC::num_spray_src =
    AMREX_SPACEDIM + 2 + SprayParticleContainer::m_sprayData->N_pc;
```
改为:
```
  PeleC::num_spray_src = NVAR;
```

改完立即: `cd /home/cj/my-pele/external/PeleC/Exec/RegTests/Spray-Jet && make -j8 && ./PeleC3d.gnu.ex example.inp max_step=10`
