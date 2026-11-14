# my-pele 可迁移源码与验证

本目录来自真实服务器工作树，包含 my-pele、修改后的 PeleC、PeleLMeX、PelePhysics、AMReX、AMReX-Hydro、测试配置与审查材料。依赖源码直接随包提供，不依赖原服务器的 Git 子模块状态。

## Linux CPU 构建

参考系统：Ubuntu 24.04、GCC/G++ 13、CMake 3.28、Python 3。需要 C/C++ 编译器；建议安装 gfortran、libyaml-cpp-dev、python3-numpy、python3-scipy、python3-yaml。Windows 用户应在 Linux/WSL 环境构建；未验证 Windows 原生编译。

```bash
sudo apt-get install cmake g++ gfortran libyaml-cpp-dev python3-numpy python3-scipy python3-yaml
python3 tools/restore_portable_inputs.py
JOBS=4 bash tools/validate_portable_cpu.sh "${TMPDIR:-/tmp}/my-pele-clean-build"
```

该命令重新构建基础模块、PeleC-Sod、PeleLMeX-PeriodicCases，然后分别运行基础 CTest 和五步 CPU 短算例。源码位置由脚本自身定位，构建和运行输出写入指定的新目录。SUNDIALS 使用 vendor/sundials-6.4.1 源码构建，不自动借用 `$HOME/.local` 的库。

## 数据与路径

- `DELIVERY_MANIFEST.json` 记录最初暂存清单；`docs/portability/` 记录后续依赖、链接、数据补齐及验证。
- 超过 GitHub 单文件限制的液滴输入以无损 gzip 存储，首次使用先运行 `restore_portable_inputs.py`，恢复时校验 SHA-256。
- 可用的内部软链接已改为相对链接。原目录里的旧构建缓存、绝对系统库链接、已失效旧构建入口不作为可迁移运行环境复制。SUNDIALS 由源码重新构建。
- 历史报告中的原路径保留，作为证据来源；不应将这些原路径理解为新机器必须具备的目录。
- `relocate_legacy_paths.py --apply` 可在移动目录后更新已知旧项目根路径；不能自动创造缺失的外部实验数据或 GPU 驱动。
- 历史归档压缩包和大体积原始场数据不放入普通 Git 对象。归档索引记录其路径、大小和 SHA-256；发布附件是否齐全以发布清单和实际附件为准。

## 验证范围

服务器上已在独立路径重新编译基础模块，24/24 CTest 通过；PeleC-Sod 与 PeleLMeX-PeriodicCases 均完成源码编译和五步运行，进程退出码为 0。日志位于 `docs/portability/validation/`。

这些是构建与运行验证，不是反应精度、自由 CJ 爆轰、两相闭合、工程火灾、GPU 或 MPI 的全面验收。历史审查结论与限制仍以原报告为准。GitHub Actions 另在独立 Ubuntu 环境复验；是否成功应查看实际工作流结果。

## 依赖来源

SUNDIALS v6.4.1 来自 https://github.com/LLNL/sundials/tree/v6.4.1 ，下载源归档 SHA-256：`4dfc2ce680275aeb08983fff01d29cf4e0efbb579e228f43cbeba8f62ceaa027`。原许可证保留于 vendor 及各 external 组件目录。
