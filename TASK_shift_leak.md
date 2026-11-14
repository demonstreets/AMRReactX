# 修改泄漏位置，使羽流撞入后柱尾流

## 当前问题
泄漏 y=25，后柱间隙 y=22.5~27.5，丙烷从缝隙溜走。

## 修改
文件 /home/cj/my-pele/examples/engineering/c3h8_flacs/pelelmex_prob.H 和 input.3d：
- leak_yc 从 25.0 改为 20.0（或 30.0，任选一根后柱对准）
- 其他参数不变

## 编译运行
make -j8，500 步 amr.plot_int=100
