# 品字形圆柱 C3H8 泄漏算例

## 几何参数
- 计算域：80×50×40 m，网格 160×100×80
- 三圆柱，半径各 5m，高 8m，z 中心 = 20m
- 品字形排列：
  - 前柱：(x=20, y=25, z=20) — 迎风
  - 后柱左：(x=30, y=20, z=20)
  - 后柱右：(x=30, y=30, z=20)
- 前后间距 10m，后两柱间距 10m

## 来流
- 风向：左→右，风速 8 m/s（wind_u=8.0, wind_v=0.0）
- 入口：lo-x 面（sgn=1），出口：hi-x 面
- 入口湍流度 10%，k-epsilon + 生产限制器

## 泄漏
- 气体：C3H8，质量流量 0.104 kg/s，孔径 22mm
- 位置：前柱背风面 (x=25.5, y=25, z=20)
- 方向：+x（顺风向），速度由质量流量/密度/面积计算
- 温度：300K

## 模型配置
- 机理：c3h8_mini（N2, O2, C3H8, 3组分）
- 无反应（纯混合）
- k-epsilon LES + 生产限制器（已在 PeleLMeX_Diffusion.cpp 中实现）
- eb2.geom_type = UserDefined

## 参考
- 现成 c3h8_flacs 算例框架：/home/cj/my-pele/examples/engineering/c3h8_flacs/
- c3h8_mini 机理：/home/cj/my-pele/external/PeleLMeX/Submodules/PelePhysics/Mechanisms/c3h8_mini/
- 生产限制器源码：/home/cj/my-pele/external/PeleLMeX/Source/PeleLMeX_Diffusion.cpp

## 运行
- 500 步，每 100 步输出
- 验证圆柱建模成功（plt 中 volFrac 有圆柱切割）
- 验证 C3H8 羽流在尾流中扩散
