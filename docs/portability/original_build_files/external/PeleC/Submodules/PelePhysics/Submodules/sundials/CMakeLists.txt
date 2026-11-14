# Local SUNDIALS shim used by the Codex stabilization tree.
# Provide SUNDIALS_CUDA_DIR or SUNDIALS_DIR; do not bake machine-local paths into source.
if(NOT DEFINED SUNDIALS_CUDA_DIR)
  if(DEFINED ENV{SUNDIALS_CUDA_DIR})
    set(SUNDIALS_CUDA_DIR "$ENV{SUNDIALS_CUDA_DIR}")
  elseif(DEFINED ENV{SUNDIALS_DIR})
    set(SUNDIALS_CUDA_DIR "$ENV{SUNDIALS_DIR}")
  endif()
endif()

if(NOT SUNDIALS_CUDA_DIR)
  message(FATAL_ERROR "Set SUNDIALS_CUDA_DIR or SUNDIALS_DIR to a SUNDIALS install with CUDA libraries")
endif()

set(SUNDIALS_CUDA_INCLUDE_DIR "${SUNDIALS_CUDA_DIR}/include")
set(SUNDIALS_CUDA_LIB_DIR "${SUNDIALS_CUDA_DIR}/lib")

foreach(required_path IN ITEMS "${SUNDIALS_CUDA_INCLUDE_DIR}" "${SUNDIALS_CUDA_LIB_DIR}")
  if(NOT EXISTS "${required_path}")
    message(FATAL_ERROR "SUNDIALS CUDA path does not exist: ${required_path}")
  endif()
endforeach()

include_directories(${SUNDIALS_CUDA_INCLUDE_DIR})
link_directories(${SUNDIALS_CUDA_LIB_DIR})

function(add_sundials_imported_static target libname)
  set(lib_path "${SUNDIALS_CUDA_LIB_DIR}/lib${libname}.a")
  if(NOT EXISTS "${lib_path}")
    message(FATAL_ERROR "Missing SUNDIALS CUDA static library: ${lib_path}")
  endif()
  add_library(${target} STATIC IMPORTED)
  set_target_properties(${target} PROPERTIES IMPORTED_LOCATION "${lib_path}")
endfunction()

add_sundials_imported_static(sundials_cvode sundials_cvode)
add_sundials_imported_static(sundials_nveccuda sundials_nveccuda)
add_sundials_imported_static(sundials_sunlinsolcusolversp sundials_sunlinsolcusolversp)
add_sundials_imported_static(sundials_sunmatrixcusparse sundials_sunmatrixcusparse)
