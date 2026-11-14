# 06 - C3H8 泄漏扩散（PeleLMeX）

## 概述
丙烷泄漏扩散模拟——FLACS 对标算例。EB 圆柱障碍物 + 点源泄漏 + k-ε 湍流。

## 算例矩阵

| 子算例 | 路径 | 并行 | EB | 状态 | 输出 |
|--------|------|------|-----|------|------|
| c3h8_flacs | engineering/c3h8_flacs/ | CPU 单核 | 3圆柱 | ✅ | 6 plt |
| c3h8_flacs_mpi | engineering/c3h8_flacs_mpi/ | CPU 单核 | 3圆柱 | ✅ | 230 plt |
| c3h8_flacs_gpu | engineering/c3h8_flacs_gpu/ | **1 GPU** | 3圆柱 | ✅ | 78 plt |
| c3h8_flacs_wall | engineering/c3h8_flacs_wall/ | CPU | +壁面 | ✅ | 2 plt |
| c3h8_flacs_ke_wall_test | engineering/c3h8_flacs_ke_wall_test/ | CPU | +壁面+k-ε | ✅ | 1 plt |

## 公共配置

| 项目 | 设置 |
|------|------|
| 求解器 | PeleLMeX（低马赫） |
| 域 | 80×50×40 m |
| 网格 | 160×100×80 = **128 万** |
| EB | 3 个圆柱（自定义 EBUserDefined） |
| 机理 | c3h8_mini（丙烷骨架） |
| 湍流 | k-ε 模型 |
| 泄漏位置 | (25.5, 20, 20) m |
| 泄漏速率 | 0.104 kg/s |
| 泄漏孔径 | 0.011 m |
| 泄漏温度 | 300 K |
| 反应 | **关**（do_react=0，纯扩散） |
| 化学积分器 | ReactorNull |
| CFL | 0.5 |
| 步数 | max_step=500 |
| AMR | 泄漏口附近 2 级加密 |

## GPU 算例详情

| 项目 | 设置 |
|------|------|
| 并行 | 1 GPU (USE_CUDA=TRUE, USE_MPI=FALSE) |
| GPU | P100 16GB |
| 结果 | ✅ 正常跑完 500 步 |
| 输出 | 78 个 plt 文件 |
| 关键 | EB+反应+湍流在 GPU 上**全部正常**——PeleLMeX GPU 崩溃只在**喷雾**组合时出现 |

## 结论

- PeleLMeX GPU 支持 EB + 湍流 + 非反应扩散 ✅
- PeleLMeX GPU 不支持 EB + 喷雾 ❌
- GPU 泄漏算例是稳定参考基准
