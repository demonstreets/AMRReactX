# TASK: 修复 Spray source MF 维度不匹配

## 问题

`Advance.cpp:303` 对所有 source 做 `Copy(*new_sources[src], *old_sources[src], 0, 0, NVAR, 0)`，但 spray source MF 只有 `num_spray_src = AMREX_SPACEDIM+2+N_pc`（~5）个分量，而 NVAR=NTHERM+NUM_ADV+NUM_SPECIES=10。

## 修复

**文件**: `/home/cj/my-pele/external/PeleC/Source/Particle.cpp` 第 85 行

**当前**:
```cpp
PeleC::num_spray_src = AMREX_SPACEDIM + 2 + SprayParticleContainer::m_sprayData->N_pc;
```

**改为**:
```cpp
PeleC::num_spray_src = NVAR;
```

原因: spray source 只需要填充少量分量（spray 索引对应的质量/动量/能量），但 MF 维度必须与 state MF 一致才能通过 Copy/算术操作。多余分量自然为 0。

## 编译+验证
```bash
cd /home/cj/my-pele/external/PeleC/Exec/RegTests/Spray-Jet
make clean && make -j8
./PeleC3d.gnu.ex example.inp max_step=10
```

验证: 无 segfault，正常完成 10 步。
