# TASK: BFS k-ε 湍流验证算例

## 背景

`/home/cj/my-pele/examples/engineering/backward_facing_step/` 已有层流 BFS 算例。
需创建湍流版本验证 k-ε + 壁面函数。

## 设计

基于 Driver & Seegmiller (1985), Re_H ≈ 37400:
- 台阶高度 H=0.0381 m
- 入口速度 U=13.47 m/s (44.2 ft/s → 13.47 m/s)
- 空气 ν≈1.54e-5 → Re_H ≈ 33,300 (接近目标)

## 操作

1. **复制**: `cp -r backward_facing_step bfs_kepsilon`

2. **修改 input.yaml**:
   - `peleLM.les_model = kepsilon`
   - `peleLM.ke_wall_functions = 1`
   - 入口湍流: `peleLM.ke_inlet_TI = 0.05`, `peleLM.ke_inlet_L = 0.0381`
   - 细化网格: `amr.n_cell = 256 64` (y方向至少8格跨台阶高度)
   - `peleLM.cfl = 0.5`
   - `peleLM.stop_time = 0.5` (约5个流动通过时间, 1.3m/13.47≈0.1s)
   - `peleLM.max_step = 10000`

3. **修改 pelelmex_prob.H**: 添加 bcnormal 中 k/ε 入口值（如果默认不够）

4. **编译**: `make -j8`

5. **运行**: `mpirun -np 4 ./PeleLMeX2d.gnu.MPI.ex input.yaml` (或用单核)

6. **验证**: `python3 /home/cj/my-pele/tools/validate_bfs.py plt<final>/`
   - 再附长度 xr/H 应在 5-8 范围内
   - 如果 validate_bfs.py 需要调整，先不改代码，报告现状

## 预估
5000-10000 步，单核 ~8-15 分钟

## 先评估再动手
先读 input.yaml 和 pelelmex_prob.H，评估当前设置是否够用，报告需要改什么。
