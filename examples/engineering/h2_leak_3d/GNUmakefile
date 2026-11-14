# AMReX
DIM = 3
COMP = gnu
PRECISION = DOUBLE
USE_EB = TRUE
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

# PeleLMeX
USE_PLASMA = FALSE

# PelePhysics
Chemistry_Model = LiDryer
Eos_Model = Fuego
Transport_Model = Simple

PELE_HOME ?= ../../../external/PeleLMeX

MY_PELE_HOME ?= ../../..
INCLUDE_LOCATIONS += $(MY_PELE_HOME)/src/engineering/leak_source
INCLUDE_LOCATIONS += $(MY_PELE_HOME)/src/geometry
VPATH_LOCATIONS += $(MY_PELE_HOME)/src/geometry
CEXE_sources += eb2_factory.cpp

include $(PELE_HOME)/Exec/Make.PeleLMeX
