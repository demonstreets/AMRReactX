#!/bin/bash
export PATH=$HOME/.npm-global/bin:$HOME/.local/bin:$PATH
source ~/.env
cd /home/cj/my-pele
timeout 600 script -q -c 'deepcode -p "Task 1.2: Signed Distance Function for AMReX Phase 1.

The STL parser is done at src/geometry/stl_parser.H (STLReader reads STL files and returns STLFacet vectors). Now create:

1. src/geometry/signed_distance.H:
   - template<typename T> T sdf_sphere(T x, T y, T z, T cx, T cy, T cz, T r)
   - class SDFComputer that takes STLReader facets and computes SDF on a regular grid
   - double computePoint(double x, double y, double z) — closest distance to any triangle
   - Negative inside, positive outside

2. src/geometry/signed_distance.cpp:
   - Implement closest-point-to-triangle algorithm
   - For each query point, iterate over all facets, compute min distance
   - For sign: use normal direction at closest point (dot product with vector to point)

3. test/unit/test_sdf.cpp:
   - Test with analytic sphere SDF
   - Create a sphere STL (icosphere or cube approximation)
   - Compute SDF on a 10x10x10 grid
   - Verify sdf_sphere matches analytic formula
   - Print PASS/FAIL

4. Compile and run:
   g++ -std=c++17 -Isrc/geometry test/unit/test_sdf.cpp src/geometry/stl_parser.cpp src/geometry/signed_distance.cpp -o build_test/test_sdf
   ./build_test/test_sdf

Report result. Update PROGRESS.md."' /dev/null 2>&1 | tee /tmp/dc_p1_t2.log
