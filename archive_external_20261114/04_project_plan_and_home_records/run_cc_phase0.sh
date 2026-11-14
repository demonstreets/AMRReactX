#!/bin/bash
export PATH=/home/cj/.npm-global/bin:/home/cj/.local/bin:/usr/bin:/bin
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY=*** /home/cj

claude -p '
你需要在服务器上完成 Pele 双场景燃烧模拟平台的 Phase 0 全部剩余任务。

## 已完成
- PeleC 编译 (31 exe, ~/my-pele/external/PeleC/build)
- PeleLMeX 编译 (13 exe, ~/my-pele/external/PeleLMeX/build)
- HotBubble 验证 (PeleLMeX), Sod 验证 (PeleC)
- Cantera 3.2.0 已安装

## 剩余任务

### 0.2 PeleLMeX FlameSheet
cd ~/my-pele/external/PeleLMeX/build/Exec/RegTests/FlameSheet
cp ~/my-pele/external/PeleLMeX/Exec/RegTests/FlameSheet/input.2d-regt .
mpirun -n 2 ./PeleLMeX-FlameSheet input.2d-regt

### 0.3 PeleC TGReact
cd ~/my-pele/external/PeleC/build/Exec/RegTests/TGReact
跑通一个带化学反应的 PeleC 算例

### 0.4 Cantera 0D 点火延迟 (最重要)
用 Cantera Python 计算 H2/air 或 CH4/air 的 0D 定容点火延迟
脚本写到 ~/my-pele/test/verification/ignition_delay.py
运行后输出对比数据

### 0.5 AMR 敏感性
HotBubble 改 amr.max_level (1,2,3) 各跑一次，记录时间步数

### 0.6 my-pele 目录完善
检查 ~/my-pele/ 结构，写 README.md

完成后写 ~/my-pele/PHASE0_REPORT.md 总结。
plan: ~/pele_cfd_master_plan.md
' --model claude-sonnet --max-turns 30 2>&1 | tee /tmp/cc_phase0_full.log
