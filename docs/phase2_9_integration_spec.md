# Phase 2.9 — PeleLMeX 端到端集成规格文档

**版本：** v1.0（初稿）
**日期：** 2026-06-10
**状态：** 待审查

---

## 1. 目标

将 Phase 2.2-2.6 开发的全部工程模块编译链接进 PeleLMeX，实现端到端可运行算例。

---

## 2. 需集成的模块清单

| 模块 | 源码位置 | 头文件 | 编译单元 |
|------|---------|--------|---------|
| k-ε 模型 | `src/engineering/turbulence/` | `k_epsilon_core.H` + `k_epsilon_constants.H` | `k_epsilon_core.cpp` |
| 壁面函数 | 同上 | `wall_functions.H` | `wall_functions.cpp` |
| 湍流-扩散 | 同上 | `turbulent_transport.H` | — (header-only) |
| 蒸发源项 | `src/engineering/evaporation/` | `antoine_data.H` + `evaporation_model.H` + `pool_evaporation.H` | — (header-only) |
| 风场 BC | `src/engineering/wind/` | `wind_profile.H` + `wind_bc.H` | — (header-only) |

---

## 3. 集成方案

### 3.1 目录链接

不拷贝文件，在 PeleLMeX 算例的 `CMakeLists.txt` 中通过 `target_include_directories` 和 `target_sources` 引用 my-pele 下的模块：

```cmake
# 在 PeleLMeX 算例 CMakeLists.txt 中
set(MY_PELE_ROOT ${CMAKE_SOURCE_DIR}/../../..)   # 指向 my-pele/

target_include_directories(${EXE_NAME} PRIVATE
    ${MY_PELE_ROOT}/src/engineering/turbulence
    ${MY_PELE_ROOT}/src/engineering/evaporation
    ${MY_PELE_ROOT}/src/engineering/wind
)

target_sources(${EXE_NAME} PRIVATE
    ${MY_PELE_ROOT}/src/engineering/turbulence/k_epsilon_core.cpp
    ${MY_PELE_ROOT}/src/engineering/turbulence/wall_functions.cpp
)
```

### 3.2 prob.H 入口

PeleLMeX 通过 `prob.H` 自定义物理。在算例的 `prob.H` 中：

```cpp
#include "my_pele_modules.H"  // 聚合头文件

// 使用已有的 problem_modify_ext_sources() 钩子
// 在时间步内施加蒸发源项、诊断等
```

创建聚合头文件 `src/engineering/my_pele_modules.H`：
```cpp
#pragma once
#include "k_epsilon_core.H"
#include "wall_functions.H"
#include "turbulent_transport.H"
#include "antoine_data.H"
#include "evaporation_model.H"
#include "pool_evaporation.H"
#include "wind_profile.H"
#include "wind_bc.H"
```

### 3.3 算例模板

创建 `examples/engineering/multi_module_test/`：
- 简单的 2D 域 + 风场 + 液池蒸发 → 验证所有模块同时工作
- 低分辨率快速回归测试（~100步验活）

---

## 4. 编译验证

### 4.1 Step 1: 头文件可用性

```bash
cd examples/engineering/multi_module_test
# 创建最小 prob.H，只 include 聚合头文件
# 编译 → 确认无 missing include 错误
```

### 4.2 Step 2: 链接正确性

```bash
# 编译链接 → 确认无 undefined symbol
```

### 4.3 Step 3: 运行测试

```bash
mpirun -np 4 ./PeleLMeX2d inputs.yaml
# max_step=100, 验证不崩溃
# 检查 plotfile 中 k, epsilon 等湍流变量出现
# 检查风场速度剖面方向正确
# 检查蒸发物种有质量通量
```

### 4.4 Step 4: 全量单元测试不受影响

```bash
# 在 my-pele/ 下
for t in test_k_epsilon test_wall_functions test_turbulent_transport \
         test_evaporation test_wind test_wind test_validation; do
    ./build_test/$t
done
# 全部通过
```

---

## 5. 集成后的验证链

```
Phase 2.9 集成完成
    │
    ├── 运行 2.7 平板边界层算例 → validate_flat_plate.py → PASS/FAIL
    ├── 运行 2.7 后台阶算例 → validate_bfs.py → PASS/FAIL
    ├── (Phase 2.8) 运行燃烧算例 → 点火延迟/层流火焰验证
    └── (Phase 2.10) 运行储罐群全流程 → 性能 profiling
```

---

## 6. 文件清单

```
src/engineering/
├── my_pele_modules.H          # 聚合头文件

examples/engineering/
├── multi_module_test/         # 集成测试算例
│   ├── input.yaml
│   ├── prob.H                 # 最小自定义物理
│   ├── CMakeLists.txt         # 引用 my-pele 模块
│   └── GNUmakefile            # PeleLMeX makefile 入口

external/PeleLMeX/             # 上游 PeleLMeX（不改动）
```

---

## 7. 风险

| 风险 | 等级 | 缓解 |
|------|------|------|
| PeleLMeX API 版本不兼容 | HIGH | 先编译空算例确认 API，再逐步加模块 |
| k-ε 变量需要额外的 StateData | MEDIUM | PeleLMeX 支持用户 StateDescriptor |
| 壁面函数需要访问壁面数据 | MEDIUM | 可能需要通过 prob_bc 或 derive 访问 |
| 蒸发源项需要 YAML 解析器 | LOW | Phase 2.1 的解析器已编译为独立测试 |
| 头文件命名冲突 | LOW | 所有模块在独立 namespace 下 |

---

## 8. 验收标准

- [ ] PeleLMeX 编译通过（含所有工程模块）
- [ ] `multi_module_test` 算例跑 100 步不崩溃
- [ ] plotfile 包含 k, epsilon, 风场速度分量
- [ ] 蒸发物种质量分数非零
- [ ] 全部已有单元测试零回归 (41 C++ + 41 Python = 82 tests)

---

*注：本 spec 为初稿，待审查。*
