# 紧急：c3h8_flacs 算例圆柱不生效

## 现象
- pelelmex_prob.cpp 中有 3 个 CylinderIF（r=5m, 品字形排列）
- 可执行文件 strings 输出包含 EBUserDefined 和 CylinderIF 符号
- 但 plt 文件中 volFrac 全部 = 1.0，没有任何切割网格

## 需要
1. 诊断为什么 EB 几何代码存在但不生效
2. 检查 EB 初始化流程：编译选项 (-DAMREX_USE_EB)、EB2::Build 调用、input.3d 中 eb2 参数
3. 修复问题，重新编译，确认 plt00000 中 volFrac < 1.0
4. 确认后运行 500 步

## 算例位置
/home/cj/my-pele/examples/engineering/c3h8_flacs/
