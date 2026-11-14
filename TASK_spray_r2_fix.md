# TASK: 修复 Advance.cpp 中所有 spray source 的 ncomp 不匹配

## 问题

`Advance.cpp` 中多处对 spray source MF 使用 `NVAR` 做操作，但 spray source MF 只有 `num_spray_src` 个分量。

**需修复的 4 处**:

### 1. 约 108 行 — do_mol_advance() Saxpy
```cpp
// 当前: NVAR
amrex::MultiFab::Saxpy(*new_sources[src], ..., 0, 0, NVAR, 0);
// 改为: (src == spray_src) ? num_spray_src : NVAR
```

### 2. 约 142 行 — do_mol_advance() 另一个 Saxpy
```cpp
// 同样: NVAR → (src == spray_src) ? num_spray_src : NVAR
```

### 3. 约 304 行 — Copy (已修复 ✅)
```cpp
int ncomp_src = (src == spray_src) ? num_spray_src : NVAR;
```

### 4. 约 372-373 行 — construct_Snew() Saxpy
```cpp
// 当前: NVAR
amrex::MultiFab::Saxpy(S_new, ..., *new_sources[src], 0, 0, NVAR, 0);
// 改为: (src == spray_src) ? num_spray_src : NVAR
```

## 模式

在所有 `for (int src : src_list)` 循环中，任何对 `old_sources[src]`/`new_sources[src]` 使用 `NVAR` 分量数的操作，都需要改为:
```cpp
int ncomp = (src == spray_src) ? num_spray_src : NVAR;
```

## 文件
`/home/cj/my-pele/external/PeleC/Source/Advance.cpp`

## 验证
```bash
cd /home/cj/my-pele/examples/academic/shock_droplet && make -j8
./PeleC2d.gnu.ex inputs max_step=20
# 期望: 无崩溃/NaN, 正常完成
```
