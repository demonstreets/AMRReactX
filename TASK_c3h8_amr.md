# TASK: c3h8_flacs AMR 局部加密验证

## 操作

1. **复制**: `cp -r c3h8_flacs c3h8_flacs_amr`

2. **修改 input.3d**，在现有配置上添加：

```yaml
# AMR 配置
amr.max_level = 1
amr.ref_ratio = 2 2 2
amr.regrid_int = 5
amr.blocking_factor = 16
amr.max_grid_size = 64
amr.n_error_buf = 2 2 2 2

# 梯度驱动加密 —— 追踪燃料云团边缘
amr.refinement_indicators = dengrad

# 梯度阈值
tagging.dengrad = 0.01

# EB 几何加密
peleLM.EB_refine_type = Static
peleLM.EB_refine_LevMax = 1

# 减小步数验证
amr.max_step = 20
```

3. **编译**: `make -j8`

4. **运行**: `./PeleLMeX3d.gnu.ex input.3d`

## 验证

- 20 步无崩溃
- `amr.v = 2` 可以看到 regrid 输出
- 对比 c3h8_flacs（均匀网格）同样的 20 步时间

## 预估

128 万格 + 1 级 EB 加密 → EB 初始化 ~10 分钟，20 步 ~10 分钟
