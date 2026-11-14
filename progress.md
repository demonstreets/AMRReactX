# Pele 双场景燃烧模拟平台 — 开发进度

**更新日期：** 2026-06-10

## Phase 1 — 几何管线

| 任务 | 说明 | 状态 |
|------|------|------|
| 1.1 | STL 解析器 | ✅ |
| 1.2 | SDF 生成 | ✅ |
| 1.3 | EB2 GeometryShop | ✅ |
| 1.4 | BC 标签系统 | ✅ |
| 1.5 | 简单几何验证 | ⏳ |
| 1.6 | 储罐群验证 | ⏳ |

## Phase 2 — 工程场景

| 任务 | 说明 | 状态 |
|------|------|------|
| 2.1 | YAML 解析器 | ✅ |
| 2.2 | k-ε 湍流模型 | ✅ |
| 2.3 | 壁面函数 | ✅ |
| 2.4 | 湍流-扩散耦合 | ✅ |
| 2.5 | 蒸发源项 | ✅ |
| 2.6 | 风场边界条件 | ✅ |
| 2.7 | 流动验证算例 | ⏳ (算例文件+验证脚本就绪，待运行) |
| 2.8 | 着火/燃烧验证 | ⏳ |
| 2.9 | 端到端集成 | ✅ (PeleLMeX + k-ε 编译通过) |
| 2.10 | CPU profiling | ⏳ |

## 代码统计

| 类别 | 文件数 | 行数 |
|------|--------|------|
| C++ 工程源码 | 11 | 1,040 |
| C++ 单元测试 | 12 | 2,477 |
| Python 工具+测试 | 4 | 1,693 |
| 算例配置 | 4 | 285 |
| Spec 文档 | 8 | ~2,200 |
| **总计** | **39** | **~7,700** |

## PeleLMeX 修改

| 文件 | 修改 | 保护 |
|------|------|------|
| `PeleLMeX_Advance.cpp` | k-ε aux 源项 + 壁面函数 hook | `#ifdef PELE_USE_KEPSILON` |
| `PeleLMeX_TransportProp.cpp` | k-ε μ_t 计算（kepsilon 模式） | `#ifdef PELE_USE_KEPSILON` |
| `PeleLMeX_Setup.cpp` | kepsilon 模式注册 | 运行时匹配 |

## 算例目录

```
examples/engineering/
├── multi_module_test/      # 集成基准 (k-ε + 风场 + 蒸发)
├── bf_sink/                # 后台阶动量汇方案 (待完成几何)
├── backward_facing_step/   # 后台阶 EB 方案 (已弃用)
├── flat_plate_bl/          # 平板边界层 (BC 待调)
└── flat_plate_bl/          # Phase 2.7 原算例文件
    └── backward_facing_step/
```

## 已知问题

1. 平板边界层：PeleLMeX incompressible 模式 dx=dy 约束 + 入口角点 MLMG 发散
2. 后台阶 EB：PeleLMeX EB + 壁面 BC 组合导致 MLMG 发散
3. 后台阶动量汇：待实现台阶区域阻尼力

## 下一步

1. bfs_sink: 添加 x<0, y<H 区域动量汇实现台阶几何
2. 运行后台阶算例验证再附长度
3. 平板边界层降低 Re 至 ~3×10⁴ 重新验证
