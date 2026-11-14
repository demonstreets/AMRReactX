# TASK: d²-law 液滴蒸发验证

## 目标

验证 Abramzon-Sirignano 蒸发模型的 d²-law：
D²(t) = D₀² - K·t, K ≈ 0.01 cm²/s (庚烷, 300K 空气)

## 算例设计

基于 `/home/cj/my-pele/external/PeleC/Exec/RegTests/Spray-Evaporation/`

创建 `/home/cj/my-pele/examples/academic/d2_law/`:

**尺寸**: 2D, 1×1 cm, 16×16 格
- dx = 0.0625 cm, dt ≈ 1.8×10⁻⁶ s（比原 regtest 的 dx=1.56 快 25 倍）

**液滴**: 单颗庚烷, D₀=0.057 cm, T=300K, 固定在域中心
- `particles.fixed_parts = 1`
- `particles.mass_transfer = 1`
- `particles.mom_transfer = 0`
- `particles.use_breakup_model = None`

**运行**: stop_time=0.3 s, max_step=200000, CFL=0.5
预计 ~50000 步能在 ~10 分钟内跑完

**验证**:
- 从 ASCII 粒子文件提取 D(t)
- 拟合 D²(t) 线性段确认 K ≈ 0.01
- 报告: 线性相关系数 R² ≥ 0.99 即 PASS

## 操作

1. 复制 Spray-Evaporation → d2_law
2. 改 input: 域 1×1, 16×16, stop_time=0.3
3. 粒子文件: 单颗液滴在 (0.5, 0.5)
4. 编译运行
5. 提取 D² vs t 数据
6. 线性拟合, 报告 K 和 R²
