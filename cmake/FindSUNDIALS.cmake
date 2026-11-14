include("${CMAKE_CURRENT_LIST_DIR}/PortableSundials.cmake")
set(SUNDIALS_FOUND TRUE)
set(SUNDIALS_LIBRARIES sundials_cvode sundials_nvecserial)
