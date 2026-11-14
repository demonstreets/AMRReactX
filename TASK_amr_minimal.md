# TASK: 最小 AMR 测试 — 只用 EB 加密

在 `/home/cj/my-pele/examples/engineering/c3h8_flacs_amr/input.3d` 中：

1. **删除** `amr.refinement_indicators = density_grad`（可能格式不兼容）
2. **删除** `tagging.dengrad = 0.01`（同上）
3. 保留 AMR 骨架和 EB 加密

最终保留的 AMR 参数：
```
amr.max_level = 1
amr.ref_ratio = 2 2 2
amr.regrid_int = 5
amr.n_error_buf = 2 2 2 2
amr.blocking_factor = 16
amr.max_grid_size = 64
peleLM.EB_refine_type = Static
peleLM.EB_refine_LevMax = 1
amr.max_step = 10
```

清理重试:
```bash
cd /home/cj/my-pele/examples/engineering/c3h8_flacs_amr
rm -rf plt* Backtrace* run.log chk*
./PeleLMeX3d.gnu.ex input.3d
```

验证: 10 步无崩溃即 PASS
