#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
amrex_root="$repo_root/external/amrex"
amrex_build="$amrex_root/build"
amrex_lib="$amrex_build/Src/libamrex_3d.a"
log_dir=${CODEX_SMOKE_LOG_DIR:-/tmp/codex_smoke_geometry_eb2_stl_$(date -u +%Y%m%dT%H%M%SZ)}
work_dir=${CODEX_EB2_STL_WORK_DIR:-/tmp/codex_eb2_stl_smoke_$(date -u +%Y%m%dT%H%M%SZ)}
mkdir -p "$log_dir"

if [[ ! -f "$amrex_lib" ]]; then
  echo "[codex-smoke-geometry-eb2-stl] missing AMReX library: $amrex_lib" >&2
  echo "[codex-smoke-geometry-eb2-stl] build external/amrex first or point this script at an existing 3D EB AMReX build" >&2
  exit 127
fi

rm -rf "$work_dir"
mkdir -p "$work_dir"
cp "$amrex_root/Tests/EB/MarchingCubes/cube.stl" "$work_dir/"
cp "$repo_root/src/geometry/eb2_factory.H" "$work_dir/"
cp "$repo_root/src/geometry/eb2_factory.cpp" "$work_dir/"

cat > "$work_dir/main.cpp" <<'CPP'
#include "eb2_factory.H"

#include <AMReX.H>
#include <AMReX_BoxArray.H>
#include <AMReX_BoxIterator.H>
#include <AMReX_DistributionMapping.H>
#include <AMReX_EB2.H>
#include <AMReX_EB2_Level.H>
#include <AMReX_EBCellFlag.H>
#include <AMReX_FabArray.H>
#include <AMReX_Geometry.H>
#include <AMReX_Print.H>
#include <AMReX_RealBox.H>

int main(int argc, char* argv[])
{
    amrex::Initialize(argc, argv);
    int rc = 0;
    {
        const int n = 32;
        amrex::Box domain(amrex::IntVect(0), amrex::IntVect(AMREX_D_DECL(n-1, n-1, n-1)));
        amrex::RealBox rb({AMREX_D_DECL(-1.2, -1.2, -1.2)}, {AMREX_D_DECL(1.2, 1.2, 1.2)});
        amrex::Geometry geom(domain, rb, 0, {AMREX_D_DECL(0, 0, 0)});
        amrex::BoxArray ba(domain);
        ba.maxSize(16);
        amrex::DistributionMapping dm(ba);

        pele::buildFromSTL("cube.stl", geom, 0);
        auto const& level = amrex::EB2::IndexSpace::top().getLevel(geom);
        amrex::FabArray<amrex::EBCellFlagFab> flags(ba, dm, 1, 0);
        level.fillEBCellFlag(flags, geom);

        long regular = 0;
        long covered = 0;
        long cut = 0;
        for (amrex::MFIter mfi(flags); mfi.isValid(); ++mfi) {
            const amrex::Box& bx = mfi.validbox();
            auto const& arr = flags.const_array(mfi);
            for (amrex::BoxIterator bit(bx); bit.ok(); ++bit) {
                const auto& iv = bit();
                auto f = arr(AMREX_D_DECL(iv[0], iv[1], iv[2]));
                if (f.isRegular()) ++regular;
                else if (f.isCovered()) ++covered;
                else ++cut;
            }
        }

        amrex::Print() << "regular=" << regular << " cut=" << cut << " covered=" << covered << "\n";
        if (cut <= 0 || regular <= 0 || covered <= 0) {
            amrex::Print() << "FAIL: expected regular, cut, and covered EB cell classes\n";
            rc = 2;
        }
        amrex::EB2::IndexSpace::clear();
    }
    amrex::Finalize();
    return rc;
}
CPP

cxx=${CXX:-g++}
includes=(
  -I"$work_dir"
  -I"$amrex_build"
  -I"$amrex_root/Src/Base"
  -I"$amrex_root/Src/Base/Parser"
  -I"$amrex_root/Src/Boundary"
  -I"$amrex_root/Src/AmrCore"
  -I"$amrex_root/Src/EB"
)

"$cxx" -std=c++20 -O2 -fopenmp -pthread "${includes[@]}" \
  "$work_dir/main.cpp" "$work_dir/eb2_factory.cpp" "$amrex_lib" \
  -o "$work_dir/eb2_stl_probe" >"$log_dir/build.log" 2>&1

(
  cd "$work_dir"
  OMP_NUM_THREADS=${OMP_NUM_THREADS:-2} ./eb2_stl_probe
) >"$log_dir/run.log" 2>&1

grep -q "Reading binary STL file" "$log_dir/run.log"
grep -q "buildFromSTL: built AMReX EB2 IndexSpace" "$log_dir/run.log"
grep -Eq "regular=[1-9][0-9]* cut=[1-9][0-9]* covered=[1-9][0-9]*" "$log_dir/run.log"
grep -q "AMReX .* finalized" "$log_dir/run.log"

echo "[codex-smoke-geometry-eb2-stl] PASS; logs: $log_dir"
