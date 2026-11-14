REPO_ROOT ?= $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)
CUDA_HOME ?= /usr/local/cuda
SUNDIALS_HOME ?= $(or $(SUNDIALS_CUDA_DIR),$(SUNDIALS_DIR))
# AMReX
DIM = 2
COMP = gnu
GPU_ARENA_SIZE = 8000
PRECISION = DOUBLE
USE_EB = FALSE
USE_HYPRE = FALSE

# Performance
USE_MPI = FALSE
USE_OMP = FALSE
USE_CUDA = TRUE
CUDA_ARCH = 60
CUDA_HOME ?= /usr/local/cuda

# Debug
DEBUG = FALSE

# PeleLMeX
USE_PLASMA = FALSE
USE_PARTICLES = TRUE
SPRAY_FUEL_NUM = 1

# PelePhysics
Chemistry_Model = C12H23
Eos_Model = Fuego
Transport_Model = Simple

PELE_HOME := $(REPO_ROOT)/external/PeleLMeX
SUNDIALS_HOME ?= $(or $(SUNDIALS_CUDA_DIR),$(SUNDIALS_DIR))


include $(PELE_HOME)/Exec/Make.PeleLMeX
