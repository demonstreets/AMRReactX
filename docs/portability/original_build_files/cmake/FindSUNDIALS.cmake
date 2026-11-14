set(SUNDIALS_FOUND TRUE)
set(SUNDIALS_INCLUDE_DIRS "$ENV{HOME}/.local/include")
set(SUNDIALS_LIBRARY_DIRS "$ENV{HOME}/.local/lib")

find_library(SUNDIALS_cvode_lib NAMES sundials_cvode PATHS ${SUNDIALS_LIBRARY_DIRS} NO_DEFAULT_PATH)
find_library(SUNDIALS_nvecserial_lib NAMES sundials_nvecserial PATHS ${SUNDIALS_LIBRARY_DIRS} NO_DEFAULT_PATH)
find_library(SUNDIALS_sunmatrixdense_lib NAMES sundials_sunmatrixdense PATHS ${SUNDIALS_LIBRARY_DIRS} NO_DEFAULT_PATH)
find_library(SUNDIALS_sunlinsoldense_lib NAMES sundials_sunlinsoldense PATHS ${SUNDIALS_LIBRARY_DIRS} NO_DEFAULT_PATH)
find_library(SUNDIALS_sunnonlinsolnewton_lib NAMES sundials_sunnonlinsolnewton PATHS ${SUNDIALS_LIBRARY_DIRS} NO_DEFAULT_PATH)

set(SUNDIALS_LIBRARIES
    ${SUNDIALS_cvode_lib}
    ${SUNDIALS_nvecserial_lib}
    ${SUNDIALS_sunmatrixdense_lib}
    ${SUNDIALS_sunlinsoldense_lib}
    ${SUNDIALS_sunnonlinsolnewton_lib}
)
message(STATUS "SUNDIALS found (32-bit): ${SUNDIALS_LIBRARIES}")
