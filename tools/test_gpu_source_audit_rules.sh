#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
tmpdir=$(mktemp -d "${TMPDIR:-/tmp}/codex_gpu_audit_rules.XXXXXX")
trap 'rm -rf "$tmpdir"' EXIT

mkdir -p "$tmpdir/src/common" "$tmpdir/examples/engineering/c3h8_gpu_test"
cat > "$tmpdir/src/common/good.H" <<'EOF'
#define AMREX_GPU_DEVICE
namespace amrex { using Real = double; }
AMREX_GPU_DEVICE inline void good_device(int i, double* out) noexcept { out[i] = 1.0; }
EOF
cat > "$tmpdir/examples/engineering/c3h8_gpu_test/bad_prob.H" <<'EOF'
#define AMREX_GPU_DEVICE
namespace amrex { using Real = double; }
struct MyProbParm { amrex::Real leak_xc; };
struct GeometryDataLike { const amrex::Real* ProbLo() const; };
struct FabLike {};
namespace amrex { template <typename F> void ParallelFor(FabLike&, F); }
static void modify_ext_sources(FabLike& fab, const GeometryDataLike& geomdata, const MyProbParm* pp) {
  const amrex::Real cx = pp->leak_xc;
  const amrex::Real* plo = geomdata.ProbLo();
  amrex::ParallelFor(fab, [=] AMREX_GPU_DEVICE (int i, int j, int k) noexcept {
    auto x = plo[0] + cx;
  });
}
EOF

python3 "$repo_root/tools/check_gpu_source_audit.py" --root "$tmpdir" >/tmp/codex_gpu_audit_default.out
if ! grep -q "gpu_source_audit PASS profile=default" /tmp/codex_gpu_audit_default.out; then
  cat /tmp/codex_gpu_audit_default.out
  exit 1
fi

set +e
python3 "$repo_root/tools/check_gpu_source_audit.py" --root "$tmpdir" --profile extended >/tmp/codex_gpu_audit_extended.out 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  cat /tmp/codex_gpu_audit_extended.out
  echo "expected extended profile to fail on synthetic CUDA host/device misuse" >&2
  exit 1
fi
grep -q "possible device ProbParm host dereference" /tmp/codex_gpu_audit_extended.out
grep -q "GeometryData host pointer may be captured by GPU lambda" /tmp/codex_gpu_audit_extended.out
printf 'gpu_source_audit_rules PASS\n'
