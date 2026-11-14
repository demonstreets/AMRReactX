# 一维爆轰核验证据包

结论入口：[一维爆轰基础核验报告](一维爆轰基础核验报告.md)。当前一维耦合验证未整体通过，二维爆轰定量结论未建立。

- 本轮 16 组正式算例及 4 组短冒烟检查均正常退出。正常退出不代表物理验证通过。
- results/verification_status.json 包含逐项检查、网格与时间步对照；frozen_startup_results.json 保存三个无反应激波的温度启动误差。
- 每个 case 目录保留原始 inputs、哈希、run.log、exit_code、全部原生 AMReX plotfiles 和派生分析。analysis_partial 是中间分析，正式判断使用 analysis。
- frame_build_source/ 包含坐标平移初始化及精确二进制；frame_build_command.json、frame_build.log、frame_build_exit_code 记录完整独立编译。构建中间对象不打包。
- dependencies/ 保留原近 CJ 参考、旧二进制、前轮算子核查及原始证据包的哈希；共享物理源码的来源链见 original_source_manifest.json 和 original_archive_info.json。
- vendor/ 保存本次使用的 AMReX 读取器和 LiDryer YAML。脚本按原服务器环境运行；原始 inputs 和 case.json 的绝对路径保持不变以便核对哈希，离线迁移时用 source_path_map.json 查找包内对应位置。
- startup_packet_paths.json 是基于保存速度场的近似轨迹，不是原生守恒示踪标签；它没有证明启动热气团就是最终前方放热尖峰。
- archive_manifest.json 逐文件记录大小和 SHA-256。完整包在本地 Windows 工作区保存；服务器 repair_validation/one_dimensional_repair_20260913 是报告副本，临时计算场在 /dev/shm。
