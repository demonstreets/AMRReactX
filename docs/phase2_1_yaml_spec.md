# Phase 2.1 — YAML 输入文件解析器 Spec

**日期**: 2026-06-09  
**位置**: `~/my-pele/src/common/input_parser/`  
**依赖**: `libyaml-cpp-dev`（系统包）

---

## 1. 模块职责

将用户编写的 YAML 配置文件解析为 C++ 结构体，供后续模块（k-ε、蒸发、风场 BC、泄漏源项等）读取参数。不包含任何物理逻辑——纯数据解析。

---

## 2. YAML Schema

### 顶层结构

```yaml
geometry:
  type: stl           # stl | builtin
  file: "tanks.stl"   # STL 文件路径（type=stl 时必须）
  scale: 1.0          # 几何缩放因子

domain:
  xmin: -5.0
  xmax: 5.0
  ymin: -3.0
  ymax: 3.0
  zmin: 0.0
  zmax: 8.0

mesh:
  n_cell: [128, 64, 96]        # base grid resolution
  max_level: 2                  # AMR max refinement level
  blocking_factor: 8
  max_grid_size: 32
  refine:
    near_wall: true             # refine near EB walls
    near_leak: true             # refine near leak sources

physics:
  model: dispersion              # dispersion | fire | full
  chemistry:
    mechanism: drm19             # mechanism name
    mechanism_file: ""           # optional override
  species:
    tracked: [CH4, C3H8, H2]     # which species to track
  transport:
    model: Simple                # Simple | Constant | Sutherland
  eos:
    type: ideal_gas              # ideal_gas

time:
  stop_time: 10.0
  max_step: 10000
  cfl: 0.7
  dt_init: 1.0e-6
  dt_max: 0.01

# 泄漏源项（可多个）
leaks:
  - name: leak_main
    position: [0.0, 0.3, 1.5]    # x, y, z
    radius: 0.01                   # 泄漏孔半径 (m)
    direction: [0.0, 0.0, 1.0]    # 注入方向单位向量
    species:
      CH4: 0.9
      C3H8: 0.1
    mass_flow_rate: 0.1            # kg/s
    temperature: 300.0             # K
    velocity: 10.0                 # m/s (注入速度)

# 风场边界条件
wind:
  model: log_law                   # log_law | power_law | uniform
  reference_height: 10.0           # m
  reference_speed: 5.0             # m/s at reference_height
  roughness_length: 0.03           # m (log_law)
  direction: [1.0, 0.0, 0.0]     # wind direction unit vector

# 液体池蒸发（可选）
pool:
  enabled: false
  position: [0.0, -0.5, 0.0]
  area: 1.0                       # m²
  species: "C8H18"                # liquid species
  temperature: 300.0              # K

# 着火/燃烧（可选）
ignition:
  enabled: false
  type: spark                      # spark | hot_surface
  position: [1.0, 0.0, 0.5]
  time: 5.0                       # ignition time
  energy: 100.0                   # J
  radius: 0.05                    # m

# 湍流模型
turbulence:
  model: k_epsilon                 # k_epsilon | none
  constants:                       # 可选覆盖默认常数
    C_mu: 0.09
    C_eps1: 1.44
    C_eps2: 1.92
    sigma_k: 1.0
    sigma_eps: 1.3
  wall_function: launder_spalding  # launder_spalding | none

output:
  plot_int: 100                   # plotfile interval (steps)
  chk_int: 500                    # checkpoint interval
  diagnostics: true               # enable runtime diagnostics
  diagnostics_interval: 10       # diagnostic CSV output every N steps
  format: plotfile                # plotfile | hdf5
```

---

## 3. C++ 数据结构设计

### 3.1 头文件结构

```
src/common/input_parser/
├── yaml_schema.H         # 所有数据结构的定义
├── yaml_parser.H         # YAML → struct 解析函数声明
└── yaml_parser.cpp       # 解析实现
```

### 3.2 核心结构体

```cpp
// yaml_schema.H

#pragma once
#include <string>
#include <vector>
#include <array>
#include <AMReX_REAL.H>
#include <AMReX_Vector.H>

namespace YamlSchema {

// --- 几何 ---
struct GeometryConfig {
    std::string type = "stl";        // "stl" | "builtin"
    std::string file = "";
    amrex::Real scale = 1.0;
};

// --- 计算域 ---
struct DomainConfig {
    amrex::Real xmin = -5.0, xmax = 5.0;
    amrex::Real ymin = -3.0, ymax = 3.0;
    amrex::Real zmin = 0.0, zmax = 8.0;
};

// --- 网格 ---
struct RefineConfig {
    bool near_wall = true;
    bool near_leak = true;
};

struct MeshConfig {
    amrex::Vector<int> n_cell = {128, 64, 96};
    int max_level = 2;
    int blocking_factor = 8;
    int max_grid_size = 32;
    RefineConfig refine;
};

// --- 物理 ---
struct ChemistryConfig {
    std::string mechanism = "drm19";
    std::string mechanism_file = "";
};

struct SpeciesConfig {
    std::vector<std::string> tracked = {"CH4"};
};

struct TransportConfig {
    std::string model = "Simple";  // "Simple" | "Constant" | "Sutherland"
};

struct EOSConfig {
    std::string type = "ideal_gas";
};

struct PhysicsConfig {
    std::string model = "dispersion";  // "dispersion" | "fire" | "full"
    ChemistryConfig chemistry;
    SpeciesConfig species;
    TransportConfig transport;
    EOSConfig eos;
};

// --- 时间控制 ---
struct TimeConfig {
    amrex::Real stop_time = 10.0;
    int max_step = 10000;
    amrex::Real cfl = 0.7;
    amrex::Real dt_init = 1.0e-6;
    amrex::Real dt_max = 0.01;
};

// --- 泄漏源 ---
struct LeakSource {
    std::string name;
    std::array<amrex::Real, 3> position = {0.0, 0.0, 0.0};
    amrex::Real radius = 0.01;
    std::array<amrex::Real, 3> direction = {0.0, 0.0, 1.0};
    std::map<std::string, amrex::Real> species;  // species_name -> mass_fraction
    amrex::Real mass_flow_rate = 0.1;
    amrex::Real temperature = 300.0;
    amrex::Real velocity = 10.0;
};

// --- 风场 BC ---
struct WindConfig {
    std::string model = "log_law";    // "log_law" | "power_law" | "uniform"
    amrex::Real reference_height = 10.0;
    amrex::Real reference_speed = 5.0;
    amrex::Real roughness_length = 0.03;
    std::array<amrex::Real, 3> direction = {1.0, 0.0, 0.0};
};

// --- 液体池 ---
struct PoolConfig {
    bool enabled = false;
    std::array<amrex::Real, 3> position = {0.0, 0.0, 0.0};
    amrex::Real area = 1.0;
    std::string species = "C8H18";
    amrex::Real temperature = 300.0;
};

// --- 着火 ---
struct IgnitionConfig {
    bool enabled = false;
    std::string type = "spark";       // "spark" | "hot_surface"
    std::array<amrex::Real, 3> position = {0.0, 0.0, 0.0};
    amrex::Real time = 0.0;
    amrex::Real energy = 0.0;
    amrex::Real radius = 0.0;
};

// --- 湍流模型 ---
struct TurbulenceConstants {
    amrex::Real C_mu = 0.09;
    amrex::Real C_eps1 = 1.44;
    amrex::Real C_eps2 = 1.92;
    amrex::Real sigma_k = 1.0;
    amrex::Real sigma_eps = 1.3;
};

struct TurbulenceConfig {
    std::string model = "k_epsilon";   // "k_epsilon" | "none"
    TurbulenceConstants constants;
    std::string wall_function = "launder_spalding";
};

// --- 输出 ---
struct OutputConfig {
    int plot_int = 100;
    int chk_int = 500;
    bool diagnostics = true;
    int diagnostics_interval = 10;
    std::string format = "plotfile";
};

// --- 顶层配置 ---
struct Config {
    GeometryConfig geometry;
    DomainConfig domain;
    MeshConfig mesh;
    PhysicsConfig physics;
    TimeConfig time;
    std::vector<LeakSource> leaks;
    WindConfig wind;
    PoolConfig pool;
    IgnitionConfig ignition;
    TurbulenceConfig turbulence;
    OutputConfig output;
};

} // namespace YamlSchema
```

### 3.3 解析函数签名

```cpp
// yaml_parser.H
#pragma once
#include "yaml_schema.H"
#include <yaml-cpp/yaml.h>

namespace YamlParser {

// 主入口：从 YAML 文件解析为 Config
YamlSchema::Config parse_config(const std::string& yaml_file_path);

// 各子模块的解析函数（便于单元测试）
YamlSchema::GeometryConfig   parse_geometry(const YAML::Node& node);
YamlSchema::DomainConfig     parse_domain(const YAML::Node& node);
YamlSchema::MeshConfig       parse_mesh(const YAML::Node& node);
YamlSchema::PhysicsConfig    parse_physics(const YAML::Node& node);
YamlSchema::TimeConfig       parse_time(const YAML::Node& node);
YamlSchema::LeakSource       parse_leak(const YAML::Node& node);
YamlSchema::WindConfig       parse_wind(const YAML::Node& node);
YamlSchema::PoolConfig       parse_pool(const YAML::Node& node);
YamlSchema::IgnitionConfig   parse_ignition(const YAML::Node& node);
YamlSchema::TurbulenceConfig parse_turbulence(const YAML::Node& node);
YamlSchema::OutputConfig     parse_output(const YAML::Node& node);

} // namespace YamlParser
```

---

## 4. 错误处理策略

| 场景 | 行为 |
|------|------|
| 文件不存在 | `amrex::Abort("Cannot open YAML file: " + path)` |
| 必填字段缺失 | `amrex::Abort("Missing required field: xxx")` |
| 类型错误（期望 int 得到 string）| `amrex::Abort("Type error: xxx expected int")` |
| 可选字段缺失 | 使用默认值，打印 `amrex::Print() << "Using default for: xxx"` |
| STL 文件路径不存在 | 解析时不检查（由后续 geometry 模块检查） |

---

## 5. 单元测试

文件：`~/my-pele/test/unit/test_yaml_parser.cpp`

测试用例：
1. **完整 YAML 解析**：解析一个完整配置文件，逐字段验证
2. **最小 YAML**：仅有必填字段，验证默认值正确填充
3. **缺失必填字段**：验证 Abort 被触发
4. **多泄漏源**：验证 `leaks` 数组解析多个条目
5. **可选模块关闭**：`pool.enabled=false` 时其他 pool 字段被忽略
6. **类型错误**：期望 int 给 string，验证 Abort

测试框架：手写 `assert()`，不需要外部测试库。测试通过打印 `[PASS]` / `[FAIL]` 到 stdout。

编译：
```bash
cd ~/my-pele
g++ -std=c++17 -Isrc/common/input_parser \
    test/unit/test_yaml_parser.cpp \
    src/common/input_parser/yaml_parser.cpp \
    -lyaml-cpp -o build_test/test_yaml && ./build_test/test_yaml
```

---

## 6. 与 PeleLMeX 的接口

Phase 2 现阶段 YAML 解析器是独立模块。后续 PeleLMeX 集成时：

- PeleLMeX 使用 AMReX ParmParse 读取 `input.3d`
- 在 `prob.cpp` 中调用 `YamlParser::parse_config("case.yaml")`，得到 `Config` 结构体
- 将 Config 中的值填入 PeleLMeX 所需的变量（泄漏源位置→`prob.leak_*`，域大小→`geometry.prob_lo/hi` 等）
- 这个"桥接"是 2.9 端到端验证的内容，不在此 spec 范围

---

## 7. 交付物

| 文件 | 行数估计 |
|------|---------|
| `src/common/input_parser/yaml_schema.H` | ~120 |
| `src/common/input_parser/yaml_parser.H` | ~40 |
| `src/common/input_parser/yaml_parser.cpp` | ~200 |
| `test/unit/test_yaml_parser.cpp` | ~150 |
| `test/unit/test_minimal.yaml` | ~15 |
| `test/unit/test_full.yaml` | ~50 |
| **总计** | **~575 行** |
