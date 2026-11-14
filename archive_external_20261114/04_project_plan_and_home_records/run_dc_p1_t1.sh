#!/bin/bash
export PATH=$HOME/.npm-global/bin:$HOME/.local/bin:$PATH
source ~/.env
cd /home/cj/my-pele

timeout 600 script -q -c 'deepcode -p "Task 1.1: STL Parser for AMReX/PeleC Phase 1.

Create these files:
1. src/geometry/stl_parser.H - header with:
   - struct Triangle { amrex::RealVect v[3]; amrex::RealVect normal; }
   - class STLParser { public: std::vector<Triangle> read(const std::string& filepath); private: std::vector<Triangle> readASCII(...); std::vector<Triangle> readBinary(...); }

2. src/geometry/stl_parser.cpp - implementation:
   - Detect binary vs ASCII by checking if first 5 bytes are \"solid\"
   - Parse ASCII: read facet normal, outer loop, vertex lines
   - Parse binary: read 80-byte header, uint32_t count, then 50-byte triangles
   - Return vector of Triangle structs

3. test/unit/test_stl_parser.cpp - unit test:
   - Create an ASCII tetrahedron STL in /tmp/test_tet.stl
   - Parse it with STLParser
   - Verify: 4 triangles, each has 3 vertices, normals are unit length
   - Print PASS/FAIL

4. Compile and run:
   mkdir -p build_test
   g++ -std=c++17 -I/home/cj/my-pele/external/amrex/Src/Base -I/home/cj/my-pele/src test/unit/test_stl_parser.cpp src/geometry/stl_parser.cpp -o build_test/test_stl
   ./build_test/test_stl

Report result. If PASS, mark task 1.1 [x] in PROGRESS.md."' /dev/null 2>&1 | tee /tmp/dc_p1_t1.log
