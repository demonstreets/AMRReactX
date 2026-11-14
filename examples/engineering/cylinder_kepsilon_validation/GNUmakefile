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

# PelePhysics
Chemistry_Model = c3h8_mini
Eos_Model = Fuego
Transport_Model = Simple

PELE_HOME ?= ../../../external/PeleLMeX

# SUNDIALS (system install)
SUNDIALS_HOME ?= $(HOME)/.local

# my-pele custom modules
MY_PELE_HOME ?= ../../..
INCLUDE_LOCATIONS += $(MY_PELE_HOME)/src/engineering
INCLUDE_LOCATIONS += $(MY_PELE_HOME)/src/engineering/turbulence
VPATH_LOCATIONS += $(MY_PELE_HOME)/src/engineering/turbulence

include $(PELE_HOME)/Exec/Make.PeleLMeX
