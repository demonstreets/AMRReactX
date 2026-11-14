# Pele CFD 中文用户文档入口

本目录面向实际使用者，不是审计日志。建议按以下顺序阅读：

1. `Pele_CFD_中文使用手册.md`
   - 项目目录怎么找
   - 输入文件怎么写
   - CPU/GPU/MPI 怎么跑
   - 输出怎么看
   - 常见错误怎么查

2. `从目录到排错_完整运行教程.md`
   - 按“目录、输入文件、工程泄漏/火灾、学术爆轰、CPU/GPU/MPI、输出、排错”的顺序给出完整操作流程
   - 适合第一次接手仓库、准备正式跑算例或定位运行错误时使用

3. `从零设置完整算例_工程H2泄漏火灾与学术爆轰.md`
   - 选定一个工程 H2 泄漏/火灾算例和一个学术 PeleC 爆轰算例，从复制 input、改参数、运行到看输出完整走一遍
   - 逐项给出 CPU 串行、CPU/MPI、GPU、MPI+CUDA 或 MPI+OpenMP 的运行命令
   - 两个案例目录内也放置了快速入口：`examples/engineering/h2_leak_3d/README_中文快速教程.md` 和 `examples/academic/detonation_2D/README_中文快速教程.md`

4. `命令速查与场景矩阵.md`
   - 按工程 H2、多燃料、液化气源项、学术爆轰、CPU/GPU/MPI、真实资料接收分类列出常用命令
   - 适合已经知道目标场景、需要快速选择入口脚本时使用

5. `工程场景_泄漏扩散火灾_Tutorial.md`
   - 面向储罐区、管廊、开放区域泄漏扩散和着火
   - 包含 H2、CH4、C3H8、LNG/LPG 气化源项代理的入口说明

6. `学术场景_气相与两相爆轰_Tutorial.md`
   - 面向 PeleC 气相爆轰、GPU/MPI 运行、两相/液滴相关验证入口

7. `真实工程资料交付与复验清单.md`
   - 面向真实 CAD、边界标签、外部 plume 数据、火灾/过压标定数据交付
   - 说明资料放置路径、模板、单项复验命令和 strict 闭合判断

8. `真实资料投递清单_按文件路径.md`
   - 按真实 CAD、外部 plume、火灾标定三类列出每个模板和目标文件路径
   - 适合资料准备完毕后逐项投递、运行 `bash tools/run_strict_external_artifact_receiving_preflight.sh` 轻量接收预检，并判断严格阻塞项是否可解除

严格说明：

- 这些教程只引用当前仓库中已经存在或已验证过的入口脚本、算例目录和输入文件。
- 真实生产级最终闭合仍需要真实 CAD、真实边界条件、真实 plume/火灾校准数据。
- 如果教程命令和审计报告冲突，以 `tools/run_current_scope_release_refresh.sh` 和 `docs/codex_audit/evidence/` 下最新 PASS 报告为准。
