# C3H8 泄漏算例：加回圆柱

## 当前状态
/home/cj/my-pele/examples/engineering/c3h8_flacs/ 已能正常运行（生产限制器+10%TI入口）。

## 需要修改
1. 加回圆柱障碍物（参照 cylinder_kepsilon_validation 或 h2_leak_3cyl_kepsilon）
   - 3个圆柱：半径 1m，位置根据需要设置（参考原始 FLACS 算例布局）
2. eb2.geom_type 改回 UserDefined
3. 圆柱在 EBUserDefined 中定义
4. 跑 500 步（amr.max_step=500, plot_int=100）

## 参考
- 圆柱代码：/home/cj/my-pele/examples/engineering/h2_leak_3cyl_kepsilon/pelelmex_prob.cpp 的 EBUserDefined
- 已验证的圆柱算例：/home/cj/my-pele/examples/engineering/cylinder_kepsilon_validation/

## 其他参数保持不变
- wind_u=3.06, wind_v=7.39（SSW风向）
- 泄漏：C3H8, 0.104 kg/s, 22mm, 位置(33.5,15,15), 射流向S
- k-epsilon + 生产限制器 + 入口10%TI

## 验证
跑完后 plt00500 中 C3H8 应有明显横向扩散，k 分布非均匀（P1/P50 << 1.0）
