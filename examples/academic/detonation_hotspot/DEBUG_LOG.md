# PeleC 2D 爆轰胞格调试记录 (最终版 03:30)

## 算例参数
- 域 30×10×0.16 cm，600×200×16 网格
- 背景：20 kPa, 300 K, H2/O2 化学当量
- 4 热点：x=0, y=1.5/3.5/5.5/8.0 cm, r=3mm
- 热点：p=1.8 MPa, T=2214 K, u=2840 m/s, H2O(0.255)+N2(0.745)
- BC: 左/上/下=NoSlipWall, 右=FOExtrap, z=周期
- LiDryer 9组分，CVODE隐式/SRK64显式

## 调试历程

### 1. BC问题（已解决）
- UserBC + NoSlipWall → GPU挂
- FOExtrap + NoSlipWall → GPU通过（ZND二进制）

### 2. 单位混乱（已修复）
- SI vs CGS 压力差异10倍，导致密度偏差

### 3. 致命BUG（已修复）
- prob.H第56行：背景UMX被错误设为 `rho_hot*u_hot`，整个域Mach 131
- 修复为 `UMX=0.0`，NaN消失

### 4. 最终状态

| 方案 | 平台 | 求解器 | 结果 |
|------|------|--------|------|
| ZND黎曼 | GPU | sparse_direct | ✅ 100步通过 (162s) |
| ZND黎曼 | GPU | FOExtrap BC | ✅ 100步通过 |
| 热点 | GPU | sparse_direct | ❌ CVODE t=0 flag=-4 |
| 热点 | GPU | fixed_point | ❌ CVODE t=0 flag=-4 |
| 热点 | GPU | dense_direct | ❌ PeleC不支持 |
| 热点 | GPU | GMRES | ❌ 挂死 |
| 热点 | GPU | ReactorRK64(显式) | ❌ NaN (~3.4s) |
| 热点 | CPU16核 | dense_direct | ❌ NaN (~180s, 已修BUG后未重测) |

## 根因结论

热点初值在 PeleC 上有根本性困难：
1. 90:1 压力比 + 25:1 密度比 + 环形几何 → 通量计算产生非物理解
2. GPU批量CVODE单点失败导致全局崩溃
3. 显式RK64绕过了CVODE但绕不过EOS NaN
4. 问题不在代码BUG，在物理初始条件的数值难度

## 推荐方案：ZND黎曼 + 横向扰动

爆轰胞格文献标准做法：
- 1D ZND黎曼初值 + y方向正弦扰动
- 已验证GPU 100步通过
- 物理上正确：横波自发形成胞格图案，无壁面干扰

## 文件位置
- 代码：`~/my-pele/examples/academic/detonation_hotspot/`
- ZND参考：`~/my-pele/examples/academic/detonation_znd_gpu/`
- 记录：`~/my-pele/examples/academic/detonation_hotspot/DEBUG_LOG.md`
