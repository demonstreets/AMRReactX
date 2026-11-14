#ifndef AMREX_GPU_STUB_H
#define AMREX_GPU_STUB_H
#define AMREX_GPU_DEVICE
#define AMREX_FORCE_INLINE inline
namespace amrex {
template <typename... Ts> void ignore_unused(const Ts&...) {}
template <typename T> T max(T a, T b) { return (a > b) ? a : b; }
}
#endif
