# C3H8 泄漏扩散算例设置 + PeleLMeX bug 修复

## 背景
- PeleLMeX 是基于 AMReX 的低马赫数反应流求解器，源码在 /home/cj/my-pele/external/PeleLMeX/
- 工作目录：/home/cj/my-pele/examples/engineering/
- 已有一个能跑的 H2 算例：h2_leak_3cyl_kepsilon/（LiDryer 9组分，H2泄漏+3圆柱+k-epsilon）
- 已创建最小C3H8机理：/home/cj/my-pele/external/PeleLMeX/Submodules/PelePhysics/Mechanisms/c3h8_mini/（3组分：N2,O2,C3H8，已验证能编译）
- 已有测试目录：test_c3h8/（基于H2算例，换上c3h8_mini机理+H2_ID→C3H8_ID，能初始化，正在跑初始迭代中）

## 需完成目标
创建丙烷泄漏扩散算例，FLACS对标条件：

1. 机理：优先 GRI 3.0 (grimech30, 53组分，已预编译在 Mechanisms/grimech30/)。如果 PeleLMeX 大组分数有 bug 就修，修不了用 c3h8_mini (3组分，在 Mechanisms/c3h8_mini/)
2. 泄漏气体：C3H8，质量流量 0.104 kg/s
3. 泄漏孔径：22mm（半径0.011m）
4. 泄漏位置：(33.5, 15.0, 15.0) m，温度 300K
5. 射流速度：由 mdot/(rho*area) 计算，不显式写死数值
6. 风速：8 m/s，左下→右上（wind_u=wind_v=5.657）
7. 入口面：lo-x 和 lo-y（bcnormal 中 sgn==-1，这是之前反复搞错的！）
8. 出口面：hi-x 和 hi-y = Outflow
9. 湍流模型：k-epsilon，入口湍流度 1%
10. 化学反应：关（纯混合 do_react=0）
11. 计算域：80x50x40 m, 160x100x80 网格
12. 无圆柱（eb2.geom_type = all_regular）

## 已知 Bug
PeleLMeX 在组分数>9时，getScalarAdvForce→build_arrays→const_arrays 处段错误（PeleLMeX_Advection.cpp:284，AMReX_FabArray.H:1826）。
LiDryer (9组分,NVAR=16) 能跑；c3h8_mini (3组分,NVAR=10) 能跑（test_c3h8已验证初始化通过）；grimech30 (53组分)、propane_fc (35组分)、C3MechLite (61组分) 都崩在同一位置。
请诊断并修复，或者用 c3h8_mini。

## 期望结果
- 算例能跑 30 步 (amr.max_step=30, plot_int=10)
- 生成 plt 文件，C3H8 质量分数分布合理
