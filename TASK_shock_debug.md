# TASK: 调试 shock_droplet dt→0 崩溃

## 当前问题
spray 全禁用状态下激波管在第 7 步 dt→0。

## 调试步骤

**Step 1: 先确认纯激波管（无喷雾）能跑 500 步**
恢复洁净状态:
```bash
cd /home/cj/my-pele/examples/academic/shock_droplet
# 备份当前 inputs
cp inputs inputs.bak

# 修改: 确保 do_spray_particles=0, n_cell=1024 1 (单格y)
# 跑500步: ./PeleC2d.gnu.ex inputs max_step=500 amr.plot_int=-1 > run.log 2>&1
# 报告 PASS/FAIL
```

如果纯激波管 PASS, 则问题在喷雾粒子的初始化/网格交互。

**Step 2: 开喷雾，用单粒子，简化参数**
- `particles.fixed_parts = 1`, 其他传输全关
- 粒子文件只含 1 个粒子，放在 x=40cm, y=0.0
- `particles.use_breakup_model = None`
- `n_cell = 1024 1` (真正的伪1D)
- `pelec.cfl = 0.05`
- `pelec.init_shrink = 0.1`

**Step 3: 逐步加功能**
如果 Step 2 跑通:
- 加 mass_transfer=1
- 加 mom_transfer=1  
- 加 breakup=KHRT
- 加回 100个粒子

每步跑 20 步验证。

## 注意
每次改 inputs 后重新编译，清理旧 plt/Backtrace。
