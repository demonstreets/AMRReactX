# 04 - spray_heptane_1gpu：庚烷喷雾 EB 热壁（PeleC 单GPU）

## 基本配置
| 项目 | 设置 |
|------|------|
| 求解器 | PeleC |
| 并行 | **单 GPU** (USE_CUDA=TRUE) |
| 域 | 10×10×10 cm, 64³ = 262K 网格 |
| EB | 倾斜平面, 1500K 等温壁 |
| 机理 | heptane_3sp |
| 燃料 | n-C₇H₁₆（正庚烷），从文件读粒子 |
| 初始 | 1500K, 10 bar, 空气 |

## 状态
- **状态**：⏸️ 搁置
- **原因**：发现 PeleC 为可压缩求解器，不适合低速喷雾燃烧（声速 CFL 限制）。改用 PeleLMeX（算例 05）

## 路径
`~/my-pele/examples/engineering/spray_heptane_1gpu/`
