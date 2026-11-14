# TASK: BFS k-ε 后台阶验证 (Driver & Seegmiller 1985)

## 算例

基于 `/home/cj/my-pele/examples/engineering/backward_facing_step/`

## 修改 input.yaml

在现有几何设置上添加：
```yaml
peleLM.les_model = kepsilon
peleLM.ke_wall_functions = 1
peleLM.ke_inlet_TI = 0.05
peleLM.ke_inlet_L = 0.0381   # H=0.0381m
```

调整运行参数：
```yaml
amr.cfl = 0.3
amr.stop_time = 0.5
amr.max_step = 5000
amr.plot_int = 500
```

## 背景知识

- 台阶 H=0.0381m, 入口槽道高 8H=0.3048m
- 入口 U=13.47 m/s, Re_H≈33,000
- 文献再附长度 X_R/H≈7.0 (Driver & Seegmiller 1985)
- 流动通过时间 t_flow = L/U ≈ 1.15/13.47 ≈ 0.085s
- stop_time=0.5s ≈ 6 个通过时间

## 编译运行

```bash
cd /home/cj/my-pele/examples/engineering/backward_facing_step
make -j8
./PeleLMeX2d.gnu.MPI.ex input.yaml   # 如果有 MPI 用单核
```

## 验证

运行后用 `python3 /home/cj/my-pele/tools/validate_bfs.py plt<final>/` 
检查再附长度是否在 5-8H 范围内。

## 预估

104×28 格, 5000步, 单核 ~5-10分钟

## 注意

- 先备份原 input.yaml 为 input_laminar.yaml
- 只改 input.yaml，不改 prob.H/prob.cpp
- 如果 validate_bfs.py 报错，只报告不修改
