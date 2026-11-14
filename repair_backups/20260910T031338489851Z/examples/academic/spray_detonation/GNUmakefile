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
USE_MPI = TRUE
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
# Finite-rate vapor chemistry with native two-way coupled liquid spray.
Chemistry_Model := heptane_lu_88sk
Transport_Model := Simple

# Spray
USE_PARTICLES = TRUE
SPRAY_FUEL_NUM = 1

PELE_HOME := ../../../external/PeleC
MY_PELE_HOME := ../../..

# A mechanism changes NUM_SPECIES and generated code but GNU Make does not
# invalidate old objects merely because Chemistry_Model changed. Isolate its
# complete object/dependency cache to prevent ABI-mismatched stale linking.
TMP_BUILD_DIR ?= tmp_build_dir/$(Chemistry_Model)

# GNU Make
Bpack := ./Make.package
Blocs := .
include $(PELE_HOME)/Exec/Make.PeleC

# Use one complete SUNDIALS installation. The inherited local ThirdParty
# installation contains merged archives and CUDA-header symlinks with an
# incompatible index ABI; the validation build supplies a clean prefix.
ifndef SUNDIALS_PREFIX
$(error Supply SUNDIALS_PREFIX for a complete, consistent SUNDIALS installation)
endif
INCLUDE_LOCATIONS := $(SUNDIALS_PREFIX)/include $(INCLUDE_LOCATIONS)
LIBRARY_LOCATIONS := $(SUNDIALS_PREFIX)/lib $(LIBRARY_LOCATIONS)
LIBRARIES := $(filter-out -lsundials_%,$(LIBRARIES))
LIBRARIES += -L$(SUNDIALS_PREFIX)/lib -Wl,-rpath,$(SUNDIALS_PREFIX)/lib
LIBRARIES += -lsundials_cvode -lsundials_arkode -lsundials_nvecmanyvector
LIBRARIES += -lsundials_sunlinsoldense -lsundials_sunlinsolband -lsundials_sunlinsolspgmr
LIBRARIES += -lsundials_sunmatrixdense -lsundials_sunmatrixband -lsundials_sunmatrixsparse
LIBRARIES += -lsundials_sunnonlinsolnewton -lsundials_sunnonlinsolfixedpoint
LIBRARIES += -lsundials_nvecserial -lsundials_generic
