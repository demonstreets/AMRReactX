# TASK: k-ε AMR regrid 后 aux 一致性修复

## 问题

AMR regrid 时 `fillcoarsepatch_aux` / `fillpatch_aux` 独立插值 k 和 ε，破坏 μ_t = C_μ ρ k²/ε 关系。

## 修复

**文件**: `/home/cj/my-pele/external/PeleLMeX/Source/PeleLMeX_Regrid.cpp`

在 `RemakeLevel` (约355行) 和 `MakeNewLevelFromCoarse` (约476行) 的 aux fillpatch 之后，加：

```cpp
// k-epsilon: floor aux after regrid interpolation to prevent
// negative values and maintain physical realizability.
// Note: independent interpolation of k and ε temporarily
// breaks the μ_t = C_μ ρ k²/ε relationship; the source
// terms in the next SDC iteration will restore it.
if (m_les_model == "kepsilon" && m_nAux >= 2) {
    auto const& aux_arrs = n_leveldata_new->auxiliaries.arrays();
    amrex::ParallelFor(n_leveldata_new->auxiliaries,
        [=] AMREX_GPU_DEVICE(int box_no, int i, int j, int k) {
            aux_arrs[box_no](i,j,k,0) = amrex::max(aux_arrs[box_no](i,j,k,0), 1e-14_rt);
            aux_arrs[box_no](i,j,k,1) = amrex::max(aux_arrs[box_no](i,j,k,1), 1e-14_rt);
        });
    amrex::Gpu::streamSynchronize();
}
```

两处 fillpatch_aux 之后各加一份（RemakeLevel + MakeNewLevelFromCoarse）。

## 为什么这样修

- k-ε 源项 P_k = μ_t·S² 和 ρε 会在一两个 SDC 迭代内拉回 μ_t 一致性
- 核心风险是插值产生的负 k/ε 值，floor 到 1e-14 解决了这个问题
- 不尝试在插值层"精确修复" μ_t 关系，因为这需要访问粗网格 μ_t 值，代价太高

## 验证

编译: `cd bfs_kepsilon && make -j8`

（当前 BFS 算例是单层网格，需额外建一个 AMR 测试来验证：2 层网格，跑 50 步确认无 NaN）

## 注意

如果已有 `floorKEpsilon` 函数可复用，优先调用它而非内联代码。
