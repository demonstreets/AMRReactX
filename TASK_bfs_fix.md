# TASK: 修复 validate_bfs.py 两个 bug

## Bug 1: FAB 数据读取 Fortran 顺序错误

**文件**: `/home/cj/my-pele/tools/amrex_reader.py` (或 validate_bfs.py 内联)
**行号**: ~156

**问题**: `(ncomp, ny, nx, order='F')` 应该是 `(nx, ny, ncomp, order='F')`

AMReX FAB 二进制格式是 Fortran 序：最内层循环是 x，所以 reshape 维度顺序是 (nx, ny, ncomp)。

## Bug 2: U_REF 单位标注错误

**文件**: `/home/cj/my-pele/tools/validate_bfs.py`
**问题**: `U_REF = 44.2` 标注为 m/s 但实际是 ft/s

Driver & Seegmiller (1985) 的 44.2 ft/s = 13.47 m/s（已在 BFS input.yaml 中使用正确值）。

修复：把 `U_REF = 44.2` 改为 `U_REF = 13.47`，注释也改为 m/s。

## 验证

修复后运行：
```bash
python3 /home/cj/my-pele/tools/validate_bfs.py /home/cj/my-pele/examples/engineering/backward_facing_step/plt<latest>/
```
确认不再报 FAB 读取错误，Cf/Cp 数值在物理合理范围。
