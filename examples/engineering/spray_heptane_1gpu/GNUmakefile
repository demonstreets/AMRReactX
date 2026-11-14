# AMReX
DIM = 3
COMP = gnu
PRECISION = DOUBLE
USE_MPI = FALSE
USE_OMP = FALSE
USE_CUDA = TRUE
USE_HIP = FALSE
USE_SYCL = FALSE

# Debug
DEBUG = FALSE

# PeleC
PELE_CVODE_FORCE_YCORDER = FALSE
PELE_USE_MAGMA = FALSE
PELE_COMPILE_AJACOBIAN = FALSE
Eos_Model := Fuego
Chemistry_Model := heptane_3sp
Transport_Model := Simple

# Spray
USE_PARTICLES = TRUE
SPRAY_FUEL_NUM = 1

# GNU Make
Bpack := ./Make.package
Blocs := .
PELE_HOME := ../../..
include $(PELE_HOME)/Exec/Make.PeleC
