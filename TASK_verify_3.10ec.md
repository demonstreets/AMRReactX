# TASK: 联合验证 3.10e + 3.10c

## 测试 A: 3.10c RT 不稳定性 (PeleC)

**目录**: `/home/cj/my-pele/examples/academic/rayleigh_taylor/`

1. 清理旧输出: `rm -rf plt* Backtrace* datlog`
2. 确认二进制是最新的: `ls -la PeleC2d.gnu.ex` (应显示 Jun 25)
3. 运行 200 步: `./PeleC2d.gnu.ex inputs max_step=200`
4. 验证:
   - 无 Backtrace 文件 (无崩溃)
   - density 范围保持 ~1.0-2.0 (不塌缩)
   - alpha 界面扰动正常增长 (plt00100/plt00200 中有明显波动)

## 测试 B: 3.10e k-ε 壁面函数 (PeleLMeX)

**目录**: `/home/cj/my-pele/examples/engineering/`

1. 复制算例: `cp -r c3h8_flacs c3h8_flacs_ke_wall_test`
2. 进入新目录，清理: `rm -rf plt* Backtrace* run*.log tmp_build_dir`
3. 修改 `input.3d`: 加一行 `peleLM.ke_wall_functions = 1`
4. 编译: `make -j8`
5. 运行 100 步: 注意 PeleLMeX 需要用低马赫启动方式，参照 c3h8_flacs 原有的运行方法

**关键**: PeleLMeX 启动需要确认:
- 运行命令（查看原来的 nohup/脚本记录）
- 如果有 EB 初始化慢的问题，耐心等

如果 PeleLMeX 启动太复杂或 120s 超时，优先完成测试 A (RT)，测试 B 只编译确认即可。

## 汇报要求

每个测试报告: 步数、状态 (PASS/FAIL/CRASH)、关键数据 (RT: density范围, 壁面: y_lo处k值)
