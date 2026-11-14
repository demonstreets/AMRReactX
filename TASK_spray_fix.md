# TASK: 修复 Spray-Jet RegTest — NUM_ADV>0 集成

## 问题

Spray-Jet 在启用 VOF (`NUM_ADV=1`) 后，`Particle.cpp` 中 spray source MultiFab 的维度与状态变量 MultiFab 不匹配，导致 `MultiFab::Copy` 崩溃。

## 修复位置

**文件**: `/home/cj/my-pele/external/PeleC/Source/Particle.cpp`

关键代码（约 290-310 行）：
```cpp
if (do_diffuse || do_spray_particles) {
    if (do_spray_particles && level > 0) {
        // spray source copy
        Sborder[lev]->copy(...)
    }
}
```

spray source MF 需要在 component count 中包含 `NUM_ADV` 个额外组分。

## 步骤

1. 检查 `Particle.cpp` 中 `spray_src` 或 `Sborder` 的 `nComp` 定义
2. 确认是否遗漏了 `NUM_ADV` 分量
3. 修复使 `nComp = NVAR`（而非 `NUM_SPECIES + 3` 之类）
4. 编译测试: `cd /home/cj/my-pele/external/PeleC/Exec/RegTests/Spray-Jet && make -j8`
5. 运行: `./PeleC3d.gnu.ex example.inp max_step=10`（只要不 segfault 即通过）

**注意**: 只修集成 bug，不改物理。运行 10 步验证即可，完整 100 步需要配置 O2_crit_temp 等燃料参数。
