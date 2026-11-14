# TASK 3.10e-R1: 修复审查发现的 3 个问题

## 背景

Phase 3.10e 审查 FAIL，发现 1 CRITICAL + 2 MEDIUM。
改动文件: `/home/cj/my-pele/external/PeleLMeX/Source/PeleLMeX_Diffusion.cpp`

## 改动 1 (CRITICAL): computeStrainRateSq 加 dx 除法

`computeStrainRateSq()` 静态函数漏了除以网格尺寸。速度梯度如 `dudx = 0.5 * (u(i+1)-u(i-1))` 必须改为 `0.5 * (u(i+1)-u(i-1)) / dx[0]`。

**修复**: 
- `computeStrainRateSq` 签名加 `const amrex::GpuArray<amrex::Real, AMREX_SPACEDIM>& dx` 参数
- 所有速度差分项除以对应 dx
- 调用处 `addKESourceTerms` 传 dx（从 Geometry 获取：`const amrex::Real* dx = geom.CellSize()`）

## 改动 2 (MEDIUM): GPU lambda 数学函数去 std::

`applyKEWallFunctions()` 的 ParallelFor lambda 里 `std::sqrt`, `std::log`, `std::abs` 改为裸名 `sqrt`, `log`, `abs`（AMReX GPU 可移植性要求）。

## 改动 3 (MEDIUM): 加 EB 注释

在 `computeStrainRateSq()` 前加注释说明当前不检查 EB cut-cell（与 PeleLMeX 其他应变率计算一致，属于已知局限）。

## 编译验证

改完后在 `/home/cj/my-pele/examples/engineering/c3h8_flacs/` 执行 `make -j8`，确认编译通过零警告。
