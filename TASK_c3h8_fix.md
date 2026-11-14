# 修复 C3H8 泄漏方向

当前算例在 /home/cj/my-pele/examples/engineering/c3h8_flacs/

## 问题
FLACS 条件：
- 风向 SSW，风速 8 m/s → vx=3.06, vy=7.39
- 泄漏方向 S（射流指向南=vy负）
- 射流逆风，产生强剪切混合

当前算例射流指向 +x（水平），没有逆风效应。

## 修改 pelelmex_prob.H
1. wind_u = 3.06, wind_v = 7.39
2. 射流方向 S：vy = -v_jet, vx = 0, vz = 0
3. bcnormal sgn=1 是 lo 面（已确认正确，不要改）
4. 入口湍流度保持 5%

## 修改 input.3d
1. wind_u = 3.06, wind_v = 7.39

## 重新编译运行
rm -rf plt* run.log Backtrace* tmp_build_dir PeleLMeX3d.gnu.ex
make -j8
nohup ./PeleLMeX3d.gnu.ex input.3d amr.max_step=30 amr.plot_int=10 > run.log 2>&1 &

## 验证
plt00030 中 C3H8 应有横向扩散，k 尾迹更宽
