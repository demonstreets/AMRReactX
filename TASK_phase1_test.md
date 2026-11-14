# TASK: 编译并运行 Phase 1 几何管线全部测试

## 测试文件

### Unit tests (`/home/cj/my-pele/test/unit/`)
- `test_stl_parser.cpp`
- `test_sdf.cpp`  
- `test_eb2_factory.cpp`
- `test_bc_tags.cpp`
- `test_signed_distance.cpp`

使用 `test/unit/amrex_stubs/` 中的桩头文件

### Verification (`/home/cj/my-pele/test/verification/`)
- `sphere_flow.cpp` — 球 SDF+vfrac 验证（链接 AMReX 库）
- `tank_flow.cpp` — 储罐群验证（链接 AMReX 库）

## 编译方法

Unit tests 用桩头文件独立编译：
```bash
cd /home/cj/my-pele/test/unit
g++ -std=c++17 -I. -I../../src/geometry -o test_stl test_stl_parser.cpp ../../src/geometry/stl_parser.cpp
# 类似编译其他 test_*.cpp
```

Verification 用 AMReX 库编译：
```bash
# sphere_flow 参考 EB regtest 的 GNUmakefile 设置 include/link 路径
```

## 运行

每个测试运行后报告 PASS/FAIL。汇总所有结果。

## 注意
- 如果 stl_parser.cpp 有 .bak 备份文件，只编译原始 .cpp
- sphere_flow 和 tank_flow 如果链接 AMReX 太复杂，至少确认能编译
