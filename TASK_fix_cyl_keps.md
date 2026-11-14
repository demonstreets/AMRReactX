# 修复 c3h8_flacs 算例：圆柱间距 + k/ε 边界

## 1. 圆柱位置修正
文件：/home/cj/my-pele/examples/engineering/c3h8_flacs/pelelmex_prob.cpp
三圆柱，半径 5m，间距改为 15m（当前是 10m）：
- c1(前)：保持 (20, 25, 20)
- c2(后左)：(35, 17.5, 20) — 当前是 (30, 20, 20)
- c3(后右)：(35, 32.5, 20) — 当前是 (30, 30, 20)

## 2. k/ε 上下边界条件修复
文件：/home/cj/my-pele/examples/engineering/c3h8_flacs/pelelmex_prob.H
bcnormal_aux 当前仅对入口面（lo-x, lo-y）设值，其他面（上下 z 面、出口面）为垃圾值。
修复：给 else 分支增加默认值 aux_ext[n]=1e-6。

注意：该文件当前可能有语法错误（之前的修改遗留），请先恢复干净状态再改。

## 3. 编译运行
make -j8，然后 500 步 amr.plot_int=100。

## 验证
plt00100 中 volFrac 应有品字形三圆柱，上下边界 k 分布应对称。
