# TASK: 从 shock_droplet 创建真 2D 算例

## 修改 `/home/cj/my-pele/examples/academic/shock_droplet/inputs`

改动以下参数，保持其他不变：

- `geometry.prob_hi = 50.0 2.0`（y 域 0-2 cm）
- `amr.n_cell = 512 128`（分辨率匹配伪1D）
- `geometry.is_periodic = 0 0`（无周期）
- `pelec.lo_bc = "FOExtrap" "SlipWall"`（y壁面）
- `pelec.hi_bc = "FOExtrap" "SlipWall"`
- `amr.blocking_factor = 32 16`
- `amr.max_grid_size = 256 64`

## 生成 200 个粒子

在 `initspraydata_2d.dat` 中：
- x=27-29 cm, y=0.5-1.5 cm（均匀随机分布）
- T=300K, D=0.005cm, 其余同原格式

## 编译测试

`make -j8 && ./PeleC2d.gnu.ex inputs max_step=10` → 报告 PASS/FAIL
