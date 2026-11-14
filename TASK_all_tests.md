# TASK: 全部单元测试编译运行（只报告，不修复）

## 测试清单

编译运行以下所有测试文件，只报告 PASS/FAIL，**不要修改任何代码**：

### Phase 2 工程模块
| 测试 | 源文件 | 依赖 |
|------|------|------|
| k-ε 核心 | test_k_epsilon.cpp | k_epsilon_core.H, amrex_stubs |
| 壁面函数 | test_wall_functions.cpp | wall_functions.H, amrex_stubs |
| 湍流输运 | test_turbulent_transport.cpp | turbulent_transport.H |
| 蒸发模型 | test_evaporation.cpp | evaporation_model.H, antoine_data.H |
| 风场 BC | test_wind.cpp | wind_bc.H |
| YAML 解析 | test_yaml_parser.cpp | yaml_parser.H, yaml_schema.H |

### Phase 3 学术模块
| 测试 | 源文件 | 依赖 |
|------|------|------|
| 两相 EOS | test_twophase_eos.cpp | StiffenedGas.H, TwoPhaseEOS.H |
| 两相 HLLC | test_twophase_hllc.cpp | TwoPhaseHLLC.H, StiffenedGas.H |
| CSF 表面张力 | test_csf.cpp | 纯算法，无 AMReX |
| VOF FCT | test_vof_fct.cpp | 纯算法 |
| WENO5 | test_weno5.cpp | weno5.H |

## 编译方法

所有测试都在 `/home/cj/my-pele/test/unit/` 目录。
工程模块源码在 `/home/cj/my-pele/src/engineering/`。
学术模块源码在 `/home/cj/my-pele/src/academic/`。

对于依赖 amrex_stubs 的测试：
```bash
g++ -std=c++17 -I. -I../../src/engineering/turbulence -I../../src/engineering/dispersion -I../../src/engineering/bc_factory -I../../src/common/input_parser -o test_xxx test_xxx.cpp <对应的源文件.cpp>
```

对于纯算法测试（无 AMReX 依赖）：
```bash
g++ -std=c++17 -I../../src/academic/vof -I../../src/academic/twophase -o test_xxx test_xxx.cpp
```

## 运行与报告

每个测试运行后输出：`PASS: N/N` 或 `FAIL: M/N`

编译失败的单独标注：`BUILD FAIL`

## 重要
- 不要修改任何.cpp/.H 文件
- 编译失败不要修，直接报告
- 运行 crash 不要修，直接报告
- 我们需要完整的失败清单
