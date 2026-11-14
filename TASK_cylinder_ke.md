# 圆柱绕流 k-epsilon 验证算例

## 目标
验证 PeleLMeX k-epsilon 模型在有真实湍流生成（圆柱尾流）时的行为。

## 算例参数
- 计算域：20×10×2 m（准2D）
- 网格：128×64×8
- 单圆柱：半径 0.5m，圆心在 (5, 5, 1)
- 来流：U=8 m/s，x 方向，入口在 lo-x 面
- 工质：空气（N2 0.767, O2 0.233），用 c3h8_mini 机理（只用 N2/O2）
- 湍流模型：k-epsilon，入口湍流度 1%
- 无反应，无泄漏
- 30 步，每 10 步输出

## 参考
- 现有圆柱 EB 代码在 /home/cj/my-pele/examples/engineering/h2_leak_3cyl_kepsilon/pelelmex_prob.cpp 的 EBUserDefined
- k-epsilon 源码在 /home/cj/my-pele/external/PeleLMeX/Source/
- c3h8_mini 机理在 /home/cj/my-pele/external/PeleLMeX/Submodules/PelePhysics/Mechanisms/c3h8_mini/

## 期望
跑完后 k 分布应该在尾流区有明显抬升（P50 ≠ P1），而不是全场均匀衰减。
