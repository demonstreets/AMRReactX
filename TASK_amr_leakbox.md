# TASK: AMR 泄漏源局部加密

## 目标

只加密泄漏源附近，不全加密圆柱。减少网格量，提升速度。

## 方案 A: refine_box（优先）

在 input.3d 中添加泄漏源附近的加密框：
```
amr.refine_boxes = x_lo y_lo z_lo x_hi y_hi z_hi
```

c3h8_flacs 的泄漏位置: prob.leak_xc=25.5, leak_yc=20.0, leak_zc=20.0
加密框建议: 24 17 17 27 23 23（3m×6m×6m 包围泄漏源+下游）

## 方案 B: 用 refinement_indicators（备选）

如果 refine_boxes 不生效，试：
```
amr.refinement_indicators = box1
tagging.box1.type = Box
tagging.box1.lo = 24 17 17
tagging.box1.hi = 27 23 23
```

## 修改 input.3d

```yaml
# 移除 EB 全局加密
peleLM.EB_refine_type = Static
peleLM.EB_refine_LevMax = 0

# 泄漏源局部加密
amr.refine_boxes = 24 17 17 27 23 23

# 保留 AMR 骨架
amr.max_level = 1
amr.ref_ratio = 2 2 2
amr.regrid_int = 5
amr.max_step = 10
```

## 编译运行

```bash
cd /home/cj/my-pele/examples/engineering/c3h8_flacs_amr
make -j8
rm -rf plt* Backtrace* run.log chk*
./PeleLMeX3d.gnu.ex input.3d
```

## 验证

- 10 步无崩溃
- Ncells < 1,500,000（比之前的 1,648,640 少）
- 步骤时间对比

如果 refine_boxes 语法不对，参考 AMReX 文档试其他变体。
