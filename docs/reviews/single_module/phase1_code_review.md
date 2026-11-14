# Phase 1 Geometry Code Review

**Date:** 2026-06-09  
**Reviewed by:** CodeWhale (deepseek-v4-pro)  
**Scope:** `src/geometry/` + `test/unit/test_*` (STL, SDF, EB2, BC Tags)

---

## Executive Summary

The Phase 1 geometry module provides STL parsing, signed distance computation, EB2 integration, and cell tagging. The core algorithms are conceptually sound, but two **critical build-breaking issues** were found. Several **runtime correctness** and **robustness** issues exist in edge-case handling. No security vulnerabilities requiring immediate attention were found. The API design is clean but incomplete — `computeSphereSDF` is referenced but never defined.

**Severity counts:** 2 Critical, 3 High, 4 Medium, 5 Low.

---

## 1. Critical Issues (Build-Breaking)

### C1: Missing `SDFComputer` constructor — `test/unit/test_sdf.cpp:179`

`test_sdf.cpp` line 179:

```cpp
pele::SDFComputer sdf(reader.getFacets());
```

`SDFComputer` (declared in `signed_distance.H`) has **no constructor** that accepts a `std::vector<STLFacet>`. The only way to load facets is `setFacets(const std::vector<STLFacet>&)`. This is a compile error.

**Fix:** Either add a constructor:

```cpp
explicit SDFComputer(const std::vector<STLFacet>& f) : m_facets(f) {}
```

or change the test to:

```cpp
pele::SDFComputer sdf;
sdf.setFacets(reader.getFacets());
```

### C2: Missing `computeSphereSDF` — two call sites, zero definitions

`computeSphereSDF` is called in:

- `test/unit/test_signed_distance.cpp:47`
- `test/verification/sphere_flow.cpp:67`

No declaration exists in `signed_distance.H` (or anywhere under `src/`). No definition exists in any source file. This is a link error at both call sites.

**Fix:** Implement `computeSphereSDF` — it should fill a `MultiFab` with the analytic sphere SDF (the test clearly expects this). Suggested declaration in `signed_distance.H`:

```cpp
void computeSphereSDF(amrex::MultiFab& sdf,
                      const amrex::Geometry& geom,
                      const amrex::Array<amrex::Real,3>& center,
                      amrex::Real radius,
                      const amrex::IntVect& ng);
```

The implementation is straightforward: iterate over valid boxes, compute cell-center positions, call `sdf_sphere()`, write into the MultiFab.

---

## 2. High-Severity Issues (Runtime Correctness)

### H1: Division by zero in `closestPt` for degenerate triangles — `signed_distance.cpp`

**Location:** Two separate divisions in the anonymous-namespace `closestPt` function:

**Line ~14 — zero-area triangle:**
```cpp
double den = d00*d11 - d01*d01;
v = (d11*d20 - d01*d21) / den;
w = (d00*d21 - d01*d20) / den;
```

When all three vertices are collinear, `den == 0`, producing NaN or Inf.

**Line ~21 — zero-length edge:**
```cpp
double t = ((px-eax)*evx + (py-eay)*evy + (pz-eaz)*evz)
         / (evx*evx + evy*evy + evz*evz);
```

When two vertices coincide, `evx*evx+evy*evy+evz*evz == 0`, producing division by zero.

**Impact:** Degenerate triangles (common in CAD-exported STL files) produce NaN distances, poisoning `SDFComputer::computePoint` comparisons (`d < best` is always false for NaN), potentially returning `numeric_limits<double>::max()` (uninitialized `best` actually gets initialized to `max()` — wait, it IS initialized: `double best = std::numeric_limits<double>::max();` — so NaN just won't update it). Still, any NaN in the output is a correctness problem.

**Fix:**
- Guard `den` with `if (std::abs(den) < 1e-30)` and fall back to edge projection.
- Guard `evx*evx+evy*evy+evz*evz` with `if (len2 < 1e-30)` and skip the edge (closest point is the vertex itself).

### H2: Binary STL reader — no read-error checking — `stl_parser.cpp:44-50`

```cpp
f.read(reinterpret_cast<char*>(&fac.normal), 12);
for (int j = 0; j < 3; j++)
    f.read(reinterpret_cast<char*>(&fac.vertices[j]), 12);
f.seekg(2, std::ios::cur);
m_facets.push_back(fac);
```

No check on `f.good()` or `f.fail()` after any read. A truncated file produces silently corrupted facets (all zeros, partial data).

**Fix:** After each `read()` call, check `f.good()`. If the file is truncated mid-triangle, throw or break.

### H3: Binary STL — no bounds check on triangle count — `stl_parser.cpp:43`

```cpp
uint32_t n = 0;
f.read(reinterpret_cast<char*>(&n), 4);
for (uint32_t i = 0; i < n; i++) { ... }
```

A corrupt or malicious STL file can set `n` to 0xFFFFFFFF (4.29 billion triangles). The loop would attempt to read ~215 GB of data, allocating memory for each facet push_back. No upper bound is enforced.

**Fix:** Add a sanity check:
```cpp
constexpr uint32_t MAX_FACETS = 100'000'000;
if (n > MAX_FACETS)
    throw std::runtime_error("STL facet count " + std::to_string(n) + " exceeds maximum");
```

Also check that the file size is at least `84 + n * 50` bytes before entering the loop.

---

## 3. Medium-Severity Issues (Robustness / Edge Cases)

### M1: ASCII-vs-binary detection false positive — `stl_parser.cpp:12-14`

```cpp
f.read(h, 5);
if (std::strncmp(h, "solid", 5) == 0) readASCII(fn);
else readBinary(fn);
```

The binary STL format has an 80-byte header that can legally begin with `"solid"`. When this happens, the ASCII parser runs on binary data — it will find no valid facets (or garbage), and return an empty facet list silently. No error is raised.

**Fix:** After ASCII parsing, if `m_facets.empty()`, fall back to binary parsing with a warning. Or use a more robust heuristic (e.g., check file size: binary STL is always `84 + 50*n` bytes; ASCII STL size is not fixed).

### M2: ASCII parser — no validation of "normal" keyword or extraction success — `stl_parser.cpp:21-23`

```cpp
ss >> ni;  // reads "normal" — but doesn't check!
ss >> fac.normal[0] >> fac.normal[1] >> fac.normal[2];
```

If the STL uses a non-standard keyword (e.g., `facet normalX 0 0 1`), `ni` absorbs `normalX` and the stream silently fails extracting the first float, leaving `fac.normal[0..2]` at zero. No error is reported.

**Fix:** Check `ni == "normal"` and verify stream state after extractions.

### M3: `buildFromSTL` silent no-op with zero facets — `eb2_factory.cpp`

```cpp
amrex::Print() << "buildFromSTL: loaded " << reader.numFacets()
               << " facets from " << stl_file << std::endl;
// ... does nothing else in Phase 1
```

If the STL file is empty, malformed, or detection fails, zero facets are loaded and the function exits without error. The caller receives no indication that geometry was not loaded.

**Fix:** Add `if (reader.numFacets() == 0) amrex::Abort("buildFromSTL: zero facets loaded");` or at minimum `amrex::Warning(...)`.

### M4: `SDFComputer::computePoint` returns unsigned distance, not signed

The header is `signed_distance.H` and the class is `SDFComputer`, but `computePoint` returns `best` — the minimum Euclidean distance, always ≥ 0. It does not determine inside/outside sign. This is correctly named in the class (it computes distance to the closest point on a mesh), but the **file name** `signed_distance.H` and the namespace semantics are misleading — `SphereIF`'s convention ("negative = fluid") implies signed distance, but `SDFComputer` can't provide that.

**Recommendation:** Either rename the file to `distance_field.H` or add sign determination (e.g., ray-casting to determine inside/outside) in Phase 2. Document the limitation clearly in the header.

---

## 4. Low-Severity Issues (Style / Documentation / Non-Critical)

### L1: Endianness assumption undocumented — `stl_parser.cpp`

Binary STL uses little-endian. The code `f.read(reinterpret_cast<char*>(&n), 4)` directly reads into `uint32_t`. On a big-endian host (rare but possible), this produces wrong values. No byte-swap or documentation.

**Fix:** Add a comment: `// Assumes little-endian host (STL binary format)` and/or use `amrex::bytes_swap` if AMReX provides it. For x86_64 this is a non-issue, but document it.

### L2: Double file open in `read()` — `stl_parser.cpp:10-15`

`read()` opens the file to peek at 5 bytes, then `readASCII()`/`readBinary()` each re-open the file. This is redundant and can fail if the file disappears between calls.

**Fix:** Pass the open `ifstream` (by reference) to the format-specific methods, or read the first 5 bytes via `peek` + `unget`.

### L3: Unused includes — `eb2_factory.cpp`

```cpp
#include <AMReX_EB2_IF_Union.H>
#include <AMReX_EB2_IF_Intersection.H>
```

These are included but not used in the Phase 1 placeholder. They will be needed in Phase 2, so this is minor, but they generate unnecessary compilation work.

### L4: Hardcoded temp path in test — `test/unit/test_stl_parser.cpp:8`

```cpp
std::ofstream o("/tmp/test_tet.stl");
```

This path is Unix-specific. On Windows it fails. Prefer a relative path in the build/test directory, or use `std::filesystem::temp_directory_path()`.

### L5: `m_sign` convention clarity — `eb2_factory.H:36`

```cpp
m_sign(inside ? 1.0 : -1.0)
```

The sign computation: `m_sign * (distance - radius)`. When `inside=false` (default), `m_sign = -1.0`, so `SDF = radius - distance`, giving negative inside and positive outside — matching the AMReX EB convention (negative = fluid). When `inside=true`, the sense flips. The logic is correct but the naming is confusing — `m_sign` refers to the sign *applied to the distance difference*, not the sign of the SDF. Documentation should clarify.

---

## 5. Test Coverage Assessment

| Module | Test File | Coverage | Notes |
|--------|-----------|----------|-------|
| `stl_parser` | `test_stl_parser.cpp` | **Partial** | ASCII tetrahedron only. No binary test. No error-path tests (missing file, truncated, empty). |
| `sdf_sphere` | `test_sdf_quick.cpp`, `test_sdf.cpp` | **Good** | Analytic points + grid sweep vs analytic. |
| `SDFComputer` | `test_sdf_quick.cpp`, `test_sdf.cpp` | **Good (but broken)** | Single triangle + sphere mesh grid sweep. Suffers from Critical C1. |
| `SphereIF` / EB2 | `test_eb2_factory.cpp` | **Good** | vfrac check, cell flag classification, domain coverage. |
| `bc_tags` | `test_bc_tags.cpp` | **Good** | Classification counts, naming, corner cell check. |
| `computeSphereSDF` | `test_signed_distance.cpp` | **N/A** | Function doesn't exist (Critical C2). Test framework is well-structured. |

**Gaps to fill:**
- Binary STL read/write round-trip test
- Error-path tests: file-not-found, truncated binary STL, zero-facet STL
- Degenerate triangle test for `SDFComputer` (collinear vertices, coincident vertices)
- `buildFromSTL` with a valid small STL (once the pipeline is implemented)

---

## 6. API Consistency

| Aspect | Assessment |
|--------|------------|
| **Naming conventions** | Consistent: `PascalCase` for classes, `camelCase` for methods, `UPPER_CASE` for enums. Good. |
| **Error handling** | Inconsistent. `STLReader::read()` throws on file-open failure, silently drops malformed facets in ASCII, silently reads garbage in binary. `SDFComputer` has no error reporting. `buildCellTags` uses assertions. Pick a strategy and unify. |
| **Ownership semantics** | `STLReader` owns facets; `SDFComputer` copies them via `setFacets`. Interface is clear. |
| **Header dependencies** | Clean. Each `.H` includes what it uses. No circular dependencies. |
| **Namespace** | Everything in `pele::`. Consistent. |
| **AMReX integration** | `eb2_factory.H` and `bc_tags.H` properly use AMReX types and conventions. The standalone `stl_parser` and `signed_distance` avoid AMReX dependency (good for reusability). |

---

## 7. Recommended Fix Priority

| Priority | Issue | Effort |
|----------|-------|--------|
| **1** | C1: Add `SDFComputer` constructor | Trivial (1 line) |
| **2** | C2: Implement `computeSphereSDF` | Small (~20 lines) |
| **3** | H1: Guard degenerate triangle divisions | Small (~10 lines) |
| **4** | H2: Check `f.good()` after binary reads | Small (~5 lines) |
| **5** | H3: Bounds-check `n` in binary reader | Small (~5 lines) |
| 6 | M1: ASCII/binary detection fallback | Medium |
| 7 | M2: Validate ASCII parser tokens | Small |
| 8 | M3: Warn on zero facets in `buildFromSTL` | Trivial |
| 9 | M4: Document unsigned distance limitation | Trivial |
| 10 | L4: Fix temp path in test | Trivial |

---

## 8. Overall Assessment

The geometry module has a **solid foundation** — the algorithm choices (barycentric closest-point, AMReX EB2 integration) are appropriate, and the API factoring (standalone STL parser, reusable SDF, AMReX-bound factory/tagging) is well thought out. The critical issues are build-breakers from an incomplete implementation, not design flaws. The high-severity issues are real but affect only edge cases (degenerate geometry, truncated files) that are unlikely in normal operation but common enough in practice to warrant fixing before Phase 2.

**Verdict:** Fix C1, C2, H1, H2, H3 before merging. Address M1-M4 during Phase 2. L1-L5 are nice-to-have.
