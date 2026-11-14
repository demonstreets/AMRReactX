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
Eos_Model := GammaLaw
Transport_Model := Constant
Chemistry_Model := Null

DEFINES += -DNUM_ADV=1
# Dimensionless RT reference EOS; other VOF cases keep physical defaults.
DEFINES += -DMYPELE_TWOPHASE_LIQUID_PINF=0.0

PELE_HOME := ../../../external/PeleC
MY_PELE_HOME := ../../..
INCLUDE_LOCATIONS += $(MY_PELE_HOME)/src/academic/vof
INCLUDE_LOCATIONS += $(MY_PELE_HOME)/src/academic/twophase
VPATH_LOCATIONS += $(MY_PELE_HOME)/src/academic/vof
VPATH_LOCATIONS += $(MY_PELE_HOME)/src/academic/twophase

# GNU Make
Bpack := ./Make.package
Blocs := .
include $(PELE_HOME)/Exec/Make.PeleC
