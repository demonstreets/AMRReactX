#ifndef AMREX_HAVE_NO_CONFIG_H
#define AMREX_HAVE_NO_CONFIG_H
#ifndef MOD_REACTOR
#define MOD_REACTOR 1
#endif
#ifndef BL_NO_FORT
#define BL_NO_FORT 1
#endif
#ifndef AMREX_GPU_MAX_THREADS
#define AMREX_GPU_MAX_THREADS 0
#endif
#ifndef BL_SPACEDIM
#define BL_SPACEDIM 2
#endif
#ifndef AMREX_SPACEDIM
#define AMREX_SPACEDIM 2
#endif
#ifndef BL_FORT_USE_UNDERSCORE
#define BL_FORT_USE_UNDERSCORE 1
#endif
#ifndef AMREX_FORT_USE_UNDERSCORE
#define AMREX_FORT_USE_UNDERSCORE 1
#endif
#ifndef BL_Linux
#define BL_Linux 1
#endif
#ifndef AMREX_Linux
#define AMREX_Linux 1
#endif
#ifndef NDEBUG
#define NDEBUG 1
#endif
#ifndef CRSEGRNDOMP
#define CRSEGRNDOMP 1
#endif
#ifndef USE_FUEGO_EOS
#define USE_FUEGO_EOS 1
#endif
#ifndef USE_SIMPLE_TRANSPORT
#define USE_SIMPLE_TRANSPORT 1
#endif
#ifndef AMREX_USE_SUNDIALS
#define AMREX_USE_SUNDIALS 1
#endif
#ifdef __cplusplus
#endif
#if defined(AMREX_USE_OMP) && !defined(_OPENMP) && !defined(AMREX_USE_HIP)
#error libamrex was built with OpenMP
#endif
#endif
