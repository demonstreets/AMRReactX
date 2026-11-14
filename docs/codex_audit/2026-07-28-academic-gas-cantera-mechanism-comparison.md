# 2026-07-28 Academic Gas Cantera Mechanism Comparison

Scope:
- Added a maintained Cantera mechanism-comparison gate for academic gas detonation readiness.
- Compared the PelePhysics LiDryer YAML against Cantera `h2o2.yaml` through Cantera-loadable thermochemistry, finite reaction-rate samples, and paired 0D ignition-delay curves.

Evidence:
- `docs/codex_audit/evidence/academic_gas_cantera_mechanism_comparison_20260728/cantera_mechanism_comparison_report.json`
- `docs/codex_audit/evidence/academic_gas_cantera_mechanism_comparison_20260728/cantera_mechanism_comparison_report.md`
- `docs/codex_audit/evidence/academic_gas_cantera_mechanism_comparison_20260728/cantera_mechanism_comparison_curve.csv`
- `docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724/academic_gas_detonation_readiness_report.json`
- `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json`

Results:
- `academic_gas_cantera_mechanism_comparison`: `PASS-ACADEMIC-GAS-CANTERA-MECHANISM-COMPARISON`
- Paired ignition cases: 4
- Maximum LiDryer-vs-Cantera-h2o2 ignition-delay ratio: 1.4254867317045181
- `academic_gas_detonation_readiness`: still `PARTIAL-ACADEMIC-GAS-DETONATION-READINESS`, with missing/partial gate count reduced from 4 to 3.
- Remaining academic gas blockers: 2D reference-quality detonation validation, 3D detonation validation, detonation-front AMR validation.

Verification:
- `python3 tools/write_academic_gas_cantera_mechanism_comparison_report.py`
- `python3 tools/write_academic_gas_cantera_mechanism_comparison_report.py --verify-json docs/codex_audit/evidence/academic_gas_cantera_mechanism_comparison_20260728/cantera_mechanism_comparison_report.json`
- `python3 tools/write_academic_gas_detonation_readiness_report.py`
- `python3 tools/write_academic_gas_detonation_readiness_report.py --verify-json docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724/academic_gas_detonation_readiness_report.json`
- `bash tools/verify_engineering_h2_production_evidence.sh`

Limitations:
- This clears the readiness-level Cantera mechanism-comparison gap.
- It does not yet prove compiled PelePhysics C++ rate-kernel equivalence against Cantera; that remains a deeper follow-on gate.
