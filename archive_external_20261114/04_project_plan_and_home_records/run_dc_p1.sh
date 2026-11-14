#!/bin/bash
export PATH=$HOME/.npm-global/bin:$HOME/.local/bin:$PATH
source ~/.env
cd /home/cj/my-pele

timeout 3600 script -q -c 'deepcode -p "You are developing Phase 1 of the Pele dual-scenario combustion platform. Reference: ~/my-pele/PHASE1_PLAN.md.

Context: AMReX at ~/my-pele/external/amrex. EB2 headers in Src/EB2/. PeleC and PeleLMeX are compiled. Code goes in src/geometry/, tests in test/.

Phase 1 Tasks (ONE AT A TIME, test each before moving on):

TASK 1.1 STL Parser: Create src/geometry/stl_parser.H and stl_parser.cpp. Read ASCII and binary STL, store vertices and faces. Write test/unit/test_stl_parser.cpp. Create test tetrahedron STL, compile with g++ -std=c++17 -I~/my-pele/external/amrex/Src/Base -I~/my-pele/src, run test.

TASK 1.2 Signed Distance: Create src/geometry/signed_distance.H and .cpp. Compute SDF from STL onto AMReX MultiFab. Test with sphere (analytic SDF = |x-x0|-R).

TASK 1.3 EB2 GeometryShop: Create src/geometry/eb2_factory.H. Wrap SDF as AMReX::EB2::GFunc, build GeometryShop and IndexSpace. Test sphere EB, verify volFrac.

TASK 1.4 BC Tags: Create src/geometry/bc_tags.H and .cpp. Label cells FLUID/SOLID/CUT/COVERED after EB build.

TASK 1.5 Sphere Verification: Create test/verification/sphere_flow.cpp. Build sphere EB, compare drag vs analytical. Document in docs/reviews/single_module/phase1_sphere_verification.md.

TASK 1.6 Tank Group: Generate STL for 2-3 cylinders. Run full pipeline STL to SDF to EB. Document in docs/reviews/integration/phase1_tank_verification.md.

After each task: verify test passes, update PROGRESS.md with [x]. When ALL done: write PHASE1_REPORT.md."' /dev/null 2>&1 | tee /tmp/dc_phase1.log
