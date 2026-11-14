# Checkpoint 000 — Phase 0.1-0.2 完成

> 日期: 2026-06-08
> Phase: 0
> 任务: 0.1 (编译 PeleC) + 0.2 (Sod 验证)
> Agent: hermes-agent (CFD 研究助手)

## 完成内容

### 编译环境
- Ubuntu 24.04.3, gcc 13.3.0
- MPICH 4.2.0 (56 核可用)
- SUNDIALS 6.7.0 源码编译 (32位索引, CVODE only, ~/.local 安装)
- AMReX 26.05

### 编译结果
- PeleC 31 个可执行文件，全部通过
- Sod 激波管 2 进程跑通 (0.1s, plt 文件正常)

### 关键决策
1. SUNDIALS 选型: 6.7.0 源码编译而非 6.4.1 deb（代码要 7.x API）
2. 禁用 ARKode: PelePhysics 代码引用了 7.x 专有 API，适配成本高
3. 自定义 FindSUNDIALS.cmake: deb 的 cmake 配置路径不兼容

### 已知问题
- Claude Code 在远程 SSH+PTY 下工具执行不稳定
- GitHub 从国内下载慢（AMReX 用本地 scp 绕过）
- PeleLMeX 的 AMReX-Hydro 子模块为空，需 clone

## 文件修改清单
1. PeleC/CMake/BuildPelePhysicsLib.cmake (移除 ARKode)
2. PelePhysics/Source/Reactions/ReactorCvode.cpp (SUN_SUCCESS 兼容)
3. PelePhysics/Source/Reactions/ReactorCvodeCustomLinSolver.cpp (同上)
4. PelePhysics/Source/Reactions/ReactorUtils.H (ARKode→CVode)
5. PelePhysics/Source/Reactions/Make.package (移除 ARKode)
6. my-pele/cmake/FindSUNDIALS.cmake (新建)
7. PeleC/CMakeLists.txt (find_package SUNDIALS)
