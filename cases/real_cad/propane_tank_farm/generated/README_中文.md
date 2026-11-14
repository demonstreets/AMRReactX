# F4 丙烷储区 DXF 到 CFD 简化三维模型说明

## 当前结果

已从 `C:\Users\demon\Desktop\F4 总平面布置图 A1.dxf` 成功读取 DXF 几何实体，并生成第一版 CFD 障碍物简化三维模型。

本次 DXF 初扫结果：

- DXF 版本：`AC1015`
- 编码：`ANSI_936 / GBK`
- 图层数：`258`
- 实体统计：`LINE 2121`，`LWPOLYLINE 951`，`INSERT 615`，`TEXT 445`，`ARC 291`，`CIRCLE 66`，`HATCH 66`，`MTEXT 63`
- 可识别工程层：`083-管廊`、`083-管廊柱角`、`设备`、`EE-设备布置`、`Pipe`、`mainpipe`、`AF_PIPE`、`PL-围墙`、`1000围墙(TK)`、`围墙`、`罐区`、`ROAD`
- 可识别文字：液化烃库区项目、低温丙烷罐组、低温丁烷罐组、常温罐组、BOG 压缩及丙烷复热系统、火炬系统、消防水罐及泵房等

## 生成文件

- `F4_simplified_cfd_obstacles.stl`：CFD 障碍物简化 STL
- `F4_simplified_cfd_plan_preview.svg`：二维抽取预览
- `F4_simplified_cfd_manifest.json`：DXF 到简化模型生成记录
- `F4_geometry_manifest.json`：项目几何检查 manifest

服务器同步位置：

- 原始 DXF：`/home/cj/my-pele/cases/real_cad/propane_tank_farm/raw/F4 总平面布置图 A1.dxf`
- 生成模型：`/home/cj/my-pele/cases/real_cad/propane_tank_farm/generated/`

## 模型规模

- 抽取几何特征：`643`
- STL 三角面：`8676`
- 模型局部坐标范围：
  - `x = 571.3944681 .. 1270.536878 m`
  - `y = 836.7098514 .. 1396.81624 m`
  - `z = 0 .. 8 m`

## 当前工程假设

由于二维总平面图没有完整三维高度、管径和泄漏点信息，本模型采用以下占位假设：

- 设备高度：`8 m`
- 管廊高度：`8 m`
- 管廊宽度：`1.2 m`
- 管廊柱宽度：`0.8 m`
- 围墙高度：`3 m`
- 围墙宽度：`0.6 m`
- 防火堤/罐区边界高度：`2 m`
- 管线占位宽度：`0.35 m`
- 管线占位高度：`3 m`

这些参数需要后续根据真实设备表、管道表、总图说明或现场资料替换。

## 质量状态

`F4_geometry_manifest.json` 中 STL 状态为 `ready`，但质量检查显示：

- `watertight = false`
- `nonmanifold_edge_count = 208`
- `component_count = 703`
- `degenerate_triangle_count = 0`

解释：

- 这是由大量独立障碍物组成的 CFD 场景 STL，不是单一封闭实体。
- 对 EB/障碍物类导入来说，多组件模型是正常的。
- 真正进入生产算例前，仍应根据求解器几何要求决定是否合并、修复、分区或拆成多个带标签 STL。

## 下一步需要确认的数据

要把该模型升级为真实丙烷储区泄漏/扩散/火灾算例，需要补充：

- 低温丙烷罐组的真实储罐类型、直径、高度、容积
- 泄漏孔位置、孔径、方向、压力、温度、相态
- 丙烷/LPG 组成，是否考虑闪蒸、液池蒸发或两相喷放
- 管廊高度、管径、管线标高
- 围墙、防火堤、建筑物高度
- 计算域大小、风速、风向、环境温度、地面粗糙度
- 点火位置、点火时间、点火方式
- 需要对比的传感器点、浓度阈值、热辐射或超压评价点

