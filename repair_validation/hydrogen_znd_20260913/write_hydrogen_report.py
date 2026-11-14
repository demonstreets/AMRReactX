"""Write the final Chinese report from completed numerical evidence."""
from pathlib import Path
import json

b = Path(__file__).resolve().parent
a = json.loads((b / 'results/assessment.json').read_text())
quality = json.loads((b / 'reference_quality.json').read_text())
native = json.loads((b / 'native_rates_comparison.json').read_text())
boundary = json.loads((b / 'boundary_reach.json').read_text())
transverse = json.loads((b / 'transverse_smoke_comparison.json').read_text())
meta = json.loads((b / 'reference_v1/metadata.json').read_text())
rows = a['rows']
fine = rows[2]
passed = a['all_preregistered_targets_met']
verdict = '达到本次设定的误差目标' if passed else '未通过本次近 CJ 稳态 ZND 保持验证'
lines = [
    '# 氢气–空气 ZND 数值验证报告',
    '',
    f'**结论：{verdict}。** 四组正式算例均运行到 4 μs 后正常退出。正常结束、守恒及组分有界性与稳态 ZND 匹配是不同的检验项目，以下分别报告。',
    '',
    '## 算例与比较方法',
    '',
    '- 上游：H₂:O₂:N₂ = 2:1:3.76（摩尔比），当量比 1，300 K，101325 Pa。',
    '- 化学：PelePhysics LiDryer，9 组分、21 个可逆反应。重新构建独立 CPU 可执行文件，使用原生 PeleC 流动推进和 CVODE 化学积分；不修改共用求解器源代码。',
    '- 模型：无黏单相反应 Euler；24 mm × 0.2 mm 周期窄条，横向 2 单元，轴向 2400/4800/9600 单元，空间步长 10/5/2.5 μm；无 AMR、无喷雾、无扩散。',
    '- 时间：三档网格采用 CFL 0.30；另在 5 μm 网格采用 CFL 0.15。CVODE 相对/绝对容差为 1e-8/1e-18。每组使用 16 个 MPI 进程。',
    '- 初始化：激波位于 x = 8 mm，下游使用独立有限速率 ZND 剖面，初始波速为 1.00001 倍 CJ 波速，以避开严格 CJ 尾端奇异点。初始化后不强制波速。',
    '- 以压力跨越上游与 VN 压力中值的位置定位前导激波。波速由 2–4 μs 的波前位置线性拟合得到，另列 3–4 μs 拟合值检查非定常性。',
    '- 最终剖面均按数值激波位置对齐，在同一物理窗口 ξ = 0.05–3 mm 比较；ξ 为激波后距离。压力、温度、密度、实验室系速度的平均绝对误差分别除以参考压力跃升、参考最高温度与上游温差、参考密度跃升和初始参考波速。组分误差直接使用质量分数平均绝对误差。',
    '- 半消耗长度是沿激波向下游遇到的第一个 Y(H₂) = 0.5Y₀(H₂) 位置；温升半程是温度首次达到 VN 温度与参考剖面尾端温度中值的位置。均采用线性插值。',
    '',
    '## 独立参考解和热化学一致性',
    '',
    f'- CJ 波速：{meta["CJ"]:.8f} m/s；初始 ZND 波速：{meta["D"]:.8f} m/s。VN 压力 {meta["von_neumann"]["p"]/1e6:.8f} MPa，温度 {meta["von_neumann"]["T"]:.6f} K。',
    f'- 氢气半消耗长度 {quality["reference_fuel_half"]["x_m"]*1e3:.9f} mm，对应流体质点停留时间 {quality["reference_fuel_half"]["residence_s"]*1e6:.9f} μs；温升半程 {quality["reference_thermal_half"]["x_m"]*1e3:.9f} mm，对应 {quality["reference_thermal_half"]["residence_s"]*1e6:.9f} μs。',
    f'- 沿参考解到 ξ = 3 mm 的质点停留时间为 {quality["residence_to_comparison_end_s"]*1e6:.6f} μs，小于 4 μs 总时长。这是参考解给出的换流时间估计，并非数值流场的示踪粒子证明。',
    f'- CJ 声速条件相对误差 {a["reference"]["CJ_sonic_relative_error"]:.3e}；参考解最大总能量守恒相对残差 {a["reference"]["max_energy_relative_residual"]:.3e}。积分相对容差从 2e-9 收紧到 2e-10 后，0.05–3 mm 内温度剖面最大变化 {quality["reference_tolerance_max_abs"]["T"]:.3e} K。',
    f'- Cantera 在 CJ 平衡态的最大 |dY/dt| 为 {quality["detailed_balance_max_abs_dY_dt_s_inv"]:.3e} s⁻¹；绝热定容继续积分 100 μs，温度变化 {quality["CJ_UV_relaxation_100us_delta_T_K"]:.3e} K。',
    f'- 直接编译原生机制头文件，在 {native["sample_count"]} 个 ZND 状态与 Cantera 比较：比热最大绝对差 {native["cp_max_abs_J_kg_K"]:.3e} J/(kg·K)，内能最大绝对差 {native["internal_energy_max_abs_J_kg"]:.3e} J/kg；摩尔生成速率最大绝对差除以全样本速率峰值为 {native["molar_rate_max_difference_over_global_peak"]:.3e}，逐状态按当地速率峰值归一化的最大差为 {native["molar_rate_max_row_scaled_difference"]:.3e}。没有把速率差异表述为严格为零。',
    '- 该混合物的平衡解含剩余氢气，因此参考解中“99% 初始燃料消耗位置”为 null；这不是参考解积分失败。',
    '',
    '## 四组正式计算结果',
    '',
    '| Δx (μm) | CFL | 波速 2–4 μs (m/s) | CJ 偏差 | 波速 3–4 μs (m/s) | 氢气半消耗长度 (mm) | 长度偏差 |',
    '|---:|---:|---:|---:|---:|---:|---:|',
]
for r in rows:
    lines.append(f'| {r["dx_mm"]*1000:g} | {r["cfl"]:.2f} | {r["speed_m_s"]:.3f} | {r["speed_error_percent"]:+.3f}% | {r["speed_3_4_m_s"]:.3f} | {r["fuel_half_mm"]:.6f} | {r["fuel_half_error_percent"]:+.2f}% |')
lines += ['', '| Δx (μm) | CFL | p 归一化 L1 | T 归一化 L1 | ρ 归一化 L1 | u 归一化 L1 | 温升半程偏差 |', '|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
    lines.append(f'| {r["dx_mm"]*1000:g} | {r["cfl"]:.2f} | {r["p_L1_percent"]:.3f}% | {r["T_L1_percent"]:.3f}% | {r["rho_L1_percent"]:.3f}% | {r["u_L1_percent"]:.3f}% | {r["thermal_half_error_percent"]:+.2f}% |')
lines += ['', '| 检查项 | 结果 |', '|---|---|']
labels = {'CJ_sonic':'参考 CJ 声速条件（< 1e-6）','reference_energy':'参考能量残差（< 1e-7）','fine_wave_speed':'最细网格平均波速相对误差 < 1%','fine_flow_profile':'最细网格 p/T/ρ/u 归一化 L1 均 < 5%','fine_major_species':'最细网格 H₂/O₂/OH/H₂O 质量分数 MAE 均 < 0.005','fine_fuel_half_length':'最细网格氢气半消耗长度相对误差 < 10%','fine_thermal_half_length':'最细网格温升半程相对误差 < 10%','all_cases_finite':'全部原始输出场无 NaN/Inf','all_cases_species_sum':'全部算例组分和偏差 < 1e-8','all_cases_exit_zero':'全部正式算例运行到 4 μs 且退出码为 0'}
for key, value in a['checks'].items():
    lines.append(f'| {labels[key]} | {"通过" if value else "未通过"} |')
lines += [
    '',
    '流动、组分和反应长度的目标在正式矩阵开始前写入 validation_scope.json。参考声速和能量阈值是额外的参考质量诊断。0.05–0.5 mm 反应区误差另存 metrics.csv 的 core 列，不替换事先指定的比较窗口。',
    '',
    '## 非定常性、时间步与守恒',
    '',
    f'- 在最细网格，2–4 μs 与 3–4 μs 拟合波速分别为 {fine["speed_m_s"]:.3f} 与 {fine["speed_3_4_m_s"]:.3f} m/s；结合下方波前及反应长度历史判断非定常程度，不能用全时段平均波速掩盖后段变化。',
    f'- 在同一 5 μm 网格，CFL 从 0.30 改为 0.15 后，2–4 μs 拟合波速变化 {rows[3]["speed_m_s"]-rows[1]["speed_m_s"]:+.3f} m/s，最终氢气半消耗长度变化 {rows[3]["fuel_half_mm"]-rows[1]["fuel_half_mm"]:+.6f} mm。完整同窗口剖面差异见 assessment.json。',
    f'- 四组算例最大的质量守恒残差/初始库存为 {max(r["mass_balance_relative"] for r in rows):.3e}，总能量守恒残差/初始库存为 {max(r["energy_balance_relative"] for r in rows):.3e}。残差已扣除两端边界净通量；时间积分采用保存时刻上的梯形公式。',
    f'- 最大组分和偏差为 {max(r["max_species_sum_error"] for r in rows):.3e}；所有保存场的 NaN/Inf 计数为 0，横向相对差异最大值为 {max(r["transverse_relative_spread"] for r in rows):.3e}。',
    f'- 另外用相同设置分别在横向 2/4 单元推进 40 步，时间差 {transverse["time_difference_s"]:.3e} s，逐场横向平均值的最大相对差为 {transverse["maximum_relative_difference"]:.3e}。这只验证短时横向离散等价性。',
    '',
    '边界影响估计：用全部保存场的最大 |u|+c（冻结声速）乘以总时长，检查左边界特征传播范围是否覆盖最终比较窗口；这是保存数据上的估计，不是连续时间的严格证明。',
    '',
    '| Δx (μm) / CFL | 最大保存特征速度 (m/s) | 左边界预计影响范围 (mm) | 比较窗口左边界 (mm) | 剩余距离 (mm) |',
    '|---|---:|---:|---:|---:|',
]
for rec, r in zip(boundary['cases'], rows):
    lines.append(f'| {r["dx_mm"]*1000:g} / {r["cfl"]:.2f} | {rec["max_saved_abs_u_plus_frozen_c_m_s"]:.2f} | {rec["estimated_left_boundary_reach_m"]*1000:.3f} | {rec["final_comparison_window_left_m"]*1000:.3f} | {rec["estimated_margin_m"]*1000:.3f} |')
lines += [
    '',
    '10 μm 粗网格的该保守估计覆盖最终比较窗口尾部约 0.309 mm，因此本次不能用这项估计排除其尾部边界影响；5 μm、2.5 μm 及减半时间步算例仍有约 1.74–1.81 mm 的估计余量。这项限制不改变最细网格未满足目标的判定。',
    '',
    '## 解释范围',
    '',
    '本次验证检验的是原生 CPU 单相、无黏、平面近 CJ 波能否维持并匹配给定的稳态 ZND 结构。若波速、反应长度与剖面目标未满足，就不能据此宣布 ZND 验证通过。正常退出及守恒通过也不代替这些目标。',
    '',
    '观察到的波前和反应区变化本身不能单独证明存在程序错误，也不能单独证明是物理爆轰不稳定性：激波捕捉误差、反应–流动分裂误差以及近 CJ 解对扰动的放大仍需区分。三档有限网格和一次时间步减半不足以完成线性稳定性或渐近收敛论证。本报告保留所有未通过项，不通过修改验收阈值或选择某个时刻来宣称成功。',
    '',
    '本结果不验证 GPU、喷雾、多相耦合、扩散、AMR、二维胞格结构或其他化学机理，也不覆盖长期传播稳定性。若进一步定位原因，可先做独立的一维稳定性分析及更细网格/更小分裂步长对照，再用较强过驱动的平面 ZND 波作补充验证。',
    '',
    '## 图与可复现证据',
    '',
    '![最终流动剖面](results/znd_structure.png)',
    '',
    '![反应区放大](results/znd_structure_reaction_zone.png)',
    '',
    '![主要组分](results/znd_species.png)',
    '',
    '![波前与反应长度历史](results/znd_history.png)',
    '',
    '- results/metrics.csv、results/assessment.json：完整误差、目标判定、网格和时间步差异。',
    '- 各 case/inputs、case.json、run.log、exit_code、timing.json 与 analysis/：实际输入、二进制及初始化数据 SHA-256、正常退出证据、原始时间历史及提取剖面。',
    '- reference_v1、reference_tight_v1、reference_quality.json：独立 CJ/ZND 参考与收紧积分容差对照。',
    '- native_rates.cpp、native_rates_build.json、audit_native_rates.py：直接调用原生机制热化学的独立比对；source_snapshot、source_manifest.json、git_revisions.json 与 build_source：相关源码快照、版本和构建证据，含实际运行的二进制。',
    '- native_plotfile_manifest.json：全部正式及横向短时对照原生 plotfile 的逐文件 SHA-256。原始场归档位于 ZIP 的 native_plotfiles/，分析报告及脚本位于 evidence/。',
    '',
    '归档完成后另行记录 ZIP 大小、SHA-256、CRC 检查结果，并在本地解包后逐一核验所有原生场文件。',
]
(b / '氢气ZND验证报告.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps({'report': str(b / '氢气ZND验证报告.md'), 'verdict': verdict}, ensure_ascii=False))
