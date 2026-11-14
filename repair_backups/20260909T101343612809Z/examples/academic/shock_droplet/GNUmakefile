# AMReX
DIM = 2
COMP = gnu
PRECISION = DOUBLE

# Profiling
PROFILE = FALSE
TINY_PROFILE = FALSE
COMM_PROFILE = FALSE
TRACE_PROFILE = FALSE
MEM_PROFILE = FALSE
USE_GPROF = FALSE

# Performance
USE_MPI = FALSE
USE_OMP = FALSE
USE_CUDA = FALSE
USE_HIP = FALSE
USE_SYCL = FALSE

# Debugging
DEBUG = FALSE
FSANITIZER = FALSE
THREAD_SANITIZER = FALSE

# PeleC
PELE_CVODE_FORCE_YCORDER = FALSE
PELE_USE_MAGMA = FALSE
PELE_COMPILE_AJACOBIAN = FALSE
Eos_Model := Fuego
# Default is an explicitly NONREACTING transport/breakup benchmark.
# For chemistry smoke testing build with Chemistry_Model=heptane_lu_88sk
# and use inputs.reacting_smoke. The zero-reaction runtime guard remains.
Chemistry_Model := heptane_3sp
Transport_Model := Simple

# Spray
USE_PARTICLES = TRUE
SPRAY_FUEL_NUM = 1

PELE_HOME := ../../../external/PeleC
MY_PELE_HOME := ../../..

# GNU Make
Bpack := ./Make.package
Blocs := .
include $(PELE_HOME)/Exec/Make.PeleC
