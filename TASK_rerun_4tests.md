# TASK: 重跑修复后的 4 个失败测试

`k_epsilon_constants.H` 已恢复。现在重跑 Phase 2 的 4 个之前 BUILD_FAIL 的测试：

1. test_k_epsilon.cpp
2. test_wall_functions.cpp
3. test_turbulent_transport.cpp
4. test_wind.cpp

编译方法同前，使用 `/home/cj/my-pele/test/unit/amrex_stubs/` 桩头文件。

每个测试运行后报告 PASS/Fail 计数。
