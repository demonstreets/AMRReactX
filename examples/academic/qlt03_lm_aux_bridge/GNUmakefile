# AMReX
DIM = 2
COMP = gnu
PRECISION = DOUBLE
USE_EB = FALSE
USE_HYPRE = FALSE

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

# PelePhysics is still required by PeleLMeX, even though this smoke is
# run in incompressible mode and only advances velocity plus auxiliaries.
Chemistry_Model = air
Eos_Model = Fuego
Transport_Model = Simple

PELE_HOME ?= ../../../external/PeleLMeX
include $(PELE_HOME)/Exec/Make.PeleLMeX
