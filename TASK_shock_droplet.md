# TASK: 创建 1D 激波-液滴交互验证算例

## 目标
构建 PeleC 1D 激波管 + 液滴验证算例，验证 Spray 模块在激波后高温高压条件下的破碎+蒸发行为。

## 物理设置

**激波管** (1D, 0-50cm):
- 左侧 (x<25cm): p=1.0e7 dyn/cm² (~10bar), T=2000K, 空气
- 右侧 (x>25cm): p=1.0e6 dyn/cm² (~1bar), T=300K, 空气  
- 激波向右传播，马赫数 ~2.5

**液滴**:
- 100 个正庚烷液滴，均匀分布在 x=35-45cm
- D₀=50μm, T=300K, 初始静止
- 使用 KHRT 破碎模型 + A-S 蒸发
- `particles.fixed_parts = 0`（允许运动）

## 文件结构

在 `/home/cj/my-pele/examples/academic/shock_droplet/` 创建:
- GNUmakefile (DIM=1, Chemistry_Model=heptane_3sp, USE_PARTICLES=TRUE, SPRAY_FUEL_NUM=1)
- inputs (1D设置)
- prob.H, prob_parm.H (激波管初始化)
- prob.cpp (空桩)
- SprayParticlesInitInsert.cpp (液滴初始化)
- Make.package

## 参考

从 `/home/cj/my-pele/external/PeleC/Exec/RegTests/Spray-A-Wbreakup/` 复制框架，修改为1D激波管。

## 验证
- 编译: `make -j8`
- 运行: `./PeleC1d.gnu.ex inputs max_step=1000`  
- 预期: 激波传播+液滴直径减小+燃料蒸气出现在下游

## 关键参数 (inputs)
```
max_step = 2000
stop_time = 0.001  # ~100μs, covers shock transit
geometry.prob_lo = 0.0
geometry.prob_hi = 50.0
amr.n_cell = 1024
pelec.cfl = 0.3
particles.use_breakup_model = KHRT
particles.fixed_parts = 0
```
