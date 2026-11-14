# TASK: c3h8_flacs 壁面函数 3D 验证

## 目标

验证 `ke_wall_functions=1` 在真实 3D EB 工程场景下生效且不崩溃。

## 操作

1. **复制算例**: `cp -r c3h8_flacs c3h8_flacs_wall`

2. **修改 input.3d**:
   添加一行: `peleLM.ke_wall_functions = 1`
   (k-ε 已经启用: `peleLM.les_model = kepsilon`)

3. **编译**: `make -j8`

4. **运行**: 50 步即可（不追求流场发展，只验证壁面函数生效）
   参照原算例的运行方式（注意 EB 初始化慢，需要耐心等待）

5. **验证**:
   - 无 Backtrace/NaN 崩溃
   - y_lo 壁面处 k > 0, ε > 0（不是均匀衰减到极小值）
   - 如果有 plotfile，检查 y_lo 第一层网格的 k/ε 值

## 预估

编译 ~2 分钟，EB 初始化 ~5 分钟，50 步 ~10-15 分钟。总计 ~20 分钟。

## 注意

- 不要改原 c3h8_flacs 目录
- EB 初始化慢、内存大(~4GB)，需要耐心等
- 如果 50 步崩溃，看 backtrace 并报告
