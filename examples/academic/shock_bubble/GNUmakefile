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

# PeleC
PELE_CVODE_FORCE_YCORDER = FALSE
PELE_USE_MAGMA = FALSE
PELE_COMPILE_AJACOBIAN = FALSE
Eos_Model := GammaLaw
Transport_Model := Constant
Chemistry_Model := Null

# One advected VOF-like alpha scalar.
# Keep the custom two-phase HLLC EOS consistent with this gas-gas scout.
DEFINES += -DNUM_ADV=1
DEFINES += -DMYPELE_TWOPHASE_GAS_GAMMA=1.4
DEFINES += -DMYPELE_TWOPHASE_GAS_PINF=0.0
DEFINES += -DMYPELE_TWOPHASE_LIQUID_GAMMA=1.4
DEFINES += -DMYPELE_TWOPHASE_LIQUID_PINF=0.0

PELE_HOME := ../../../external/PeleC
MY_PELE_HOME := ../../..
INCLUDE_LOCATIONS += $(MY_PELE_HOME)/src/academic/vof
INCLUDE_LOCATIONS += $(MY_PELE_HOME)/src/academic/twophase
VPATH_LOCATIONS += $(MY_PELE_HOME)/src/academic/vof
VPATH_LOCATIONS += $(MY_PELE_HOME)/src/academic/twophase

Bpack := ./Make.package
Blocs := .
include $(PELE_HOME)/Exec/Make.PeleC
