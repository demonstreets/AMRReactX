cmake_minimum_required(VERSION 3.22)
project(my_pele LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(MYPELE_ENABLE_UNIT_SMOKE "Configure lightweight standalone module smoke tests" ON)

find_package(yaml-cpp QUIET)

set(MYPELE_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")
set(MYPELE_SRC "${MYPELE_ROOT}/src")

add_library(my_pele_headers INTERFACE)
target_include_directories(my_pele_headers INTERFACE
  "${MYPELE_SRC}/common/input_parser"
  "${MYPELE_SRC}/common/reconstruction"
  "${MYPELE_SRC}/geometry"
  "${MYPELE_SRC}/engineering/turbulence"
  "${MYPELE_SRC}/engineering/amr"
  "${MYPELE_SRC}/engineering/evaporation"
  "${MYPELE_SRC}/engineering/dispersion"
  "${MYPELE_SRC}/engineering/leak_source"
  "${MYPELE_SRC}/engineering/wind"
  "${MYPELE_SRC}/engineering/numerics"
  "${MYPELE_SRC}/academic/vof"
  "${MYPELE_SRC}/academic/twophase"
  "${MYPELE_SRC}/academic/droplet"
  "${MYPELE_SRC}/academic/validation"
)

add_custom_target(validate_layout
  COMMAND ${CMAKE_COMMAND} -E echo "my-pele layout configured"
  COMMAND ${CMAKE_COMMAND} -E echo "Use PeleC/PeleLMeX example directories for full solver builds."
  VERBATIM
)

if(MYPELE_ENABLE_UNIT_SMOKE)
  enable_testing()
  find_package(Python3 COMPONENTS Interpreter QUIET)
  if(Python3_FOUND)
    add_test(
      NAME amrex_reader_multibox_smoke
      COMMAND ${Python3_EXECUTABLE} ${MYPELE_ROOT}/tools/test_amrex_reader_multibox.py
    )
  else()
    message(WARNING "Python3 was not found; amrex_reader multibox smoke is disabled")
  endif()
  configure_file(test/unit/AMReX_Config.H.in AMReX_Config.H COPYONLY)
  add_executable(test_weno5_smoke test/unit/test_weno5.cpp)
  target_link_libraries(test_weno5_smoke PRIVATE my_pele_headers)
  add_test(NAME weno5_smoke COMMAND test_weno5_smoke)

  add_executable(test_species_flux_limiter_smoke test/unit/test_species_flux_limiter.cpp)
  target_include_directories(test_species_flux_limiter_smoke PRIVATE
    "${MYPELE_ROOT}/test/unit/amrex_stubs"
    "${MYPELE_ROOT}/external/PeleC/Source")
  add_test(NAME species_flux_limiter_smoke COMMAND test_species_flux_limiter_smoke)

  add_executable(test_pelec_weno_smoke test/unit/test_pelec_weno.cpp)
  target_include_directories(test_pelec_weno_smoke PRIVATE
    "${MYPELE_ROOT}/external/PeleC/Source"
    "${MYPELE_ROOT}/external/PeleC/Submodules/PelePhysics/Submodules/amrex/Src/Base"
    "${CMAKE_CURRENT_BINARY_DIR}"
  )
  add_test(NAME pelec_weno_smoke COMMAND test_pelec_weno_smoke)

  add_executable(test_geometry_pipeline_smoke
    test/unit/test_geometry_pipeline.cpp
    src/geometry/stl_parser.cpp
    src/geometry/signed_distance.cpp
    src/geometry/bc_tags.cpp
  )
  target_link_libraries(test_geometry_pipeline_smoke PRIVATE my_pele_headers)
  add_test(NAME geometry_pipeline_smoke COMMAND test_geometry_pipeline_smoke)

  add_executable(test_refinement_tags_smoke test/unit/test_refinement_tags.cpp)
  target_link_libraries(test_refinement_tags_smoke PRIVATE my_pele_headers)
  add_test(NAME refinement_tags_smoke COMMAND test_refinement_tags_smoke)

  add_executable(test_evaporation_model_smoke test/unit/test_evaporation_model.cpp)
  target_link_libraries(test_evaporation_model_smoke PRIVATE my_pele_headers)
  add_test(NAME evaporation_model_smoke COMMAND test_evaporation_model_smoke)

  add_executable(test_pool_vof_coupling_smoke test/unit/test_pool_vof_coupling.cpp)
  target_compile_definitions(test_pool_vof_coupling_smoke PRIVATE
    AMREX_SPACEDIM=2
    BL_SPACEDIM=2
    AMREX_GPU_MAX_THREADS=0
    NUM_ADV=1
    NUM_SPECIES=1
  )
  target_include_directories(test_pool_vof_coupling_smoke PRIVATE
    "${MYPELE_ROOT}/test/unit"
    "${MYPELE_ROOT}/external/PeleC/Source"
    "${MYPELE_ROOT}/external/PeleC/Submodules/PelePhysics/Submodules/amrex/Src/Base"
    "${CMAKE_CURRENT_BINARY_DIR}"
  )
  target_link_libraries(test_pool_vof_coupling_smoke PRIVATE my_pele_headers)
  add_test(NAME pool_vof_coupling_smoke COMMAND test_pool_vof_coupling_smoke)

  add_executable(test_wind_profile_smoke test/unit/test_wind_profile.cpp)
  target_link_libraries(test_wind_profile_smoke PRIVATE my_pele_headers)
  add_test(NAME wind_profile_smoke COMMAND test_wind_profile_smoke)

  add_executable(test_wall_functions_smoke
    test/unit/test_wall_functions.cpp
    src/engineering/turbulence/wall_functions.cpp
  )
  target_link_libraries(test_wall_functions_smoke PRIVATE my_pele_headers)
  add_test(NAME wall_functions_smoke COMMAND test_wall_functions_smoke)

  add_executable(test_leak_source_smoke test/unit/test_leak_source.cpp)
  target_link_libraries(test_leak_source_smoke PRIVATE my_pele_headers)
  add_test(NAME leak_source_smoke COMMAND test_leak_source_smoke)

  add_executable(test_gaussian_plume_smoke test/unit/test_gaussian_plume.cpp)
  target_link_libraries(test_gaussian_plume_smoke PRIVATE my_pele_headers)
  add_test(NAME gaussian_plume_smoke COMMAND test_gaussian_plume_smoke)

  add_executable(test_csf_smoke test/unit/test_csf.cpp)
  target_compile_definitions(test_csf_smoke PRIVATE
    AMREX_SPACEDIM=2
    BL_SPACEDIM=2
    AMREX_GPU_MAX_THREADS=0
  )
  target_include_directories(test_csf_smoke PRIVATE
    "${MYPELE_ROOT}/external/PeleC/Submodules/PelePhysics/Submodules/amrex/Src/Base"
    "${CMAKE_CURRENT_BINARY_DIR}"
  )
  target_link_libraries(test_csf_smoke PRIVATE my_pele_headers)
  add_test(NAME csf_smoke COMMAND test_csf_smoke)

  add_executable(test_static_droplet_laplace_smoke test/unit/test_static_droplet_laplace.cpp)
  target_compile_definitions(test_static_droplet_laplace_smoke PRIVATE
    AMREX_SPACEDIM=2
    BL_SPACEDIM=2
    AMREX_GPU_MAX_THREADS=0
  )
  target_include_directories(test_static_droplet_laplace_smoke PRIVATE
    "${MYPELE_ROOT}/external/PeleC/Submodules/PelePhysics/Submodules/amrex/Src/Base"
    "${CMAKE_CURRENT_BINARY_DIR}"
  )
  target_link_libraries(test_static_droplet_laplace_smoke PRIVATE my_pele_headers)
  add_test(NAME static_droplet_laplace_smoke COMMAND test_static_droplet_laplace_smoke)

  add_executable(test_vof_fct_smoke test/unit/test_vof_fct.cpp)
  target_compile_definitions(test_vof_fct_smoke PRIVATE
    AMREX_SPACEDIM=2
    BL_SPACEDIM=2
    AMREX_GPU_MAX_THREADS=0
    NUM_ADV=1
    NUM_SPECIES=1
  )
  target_include_directories(test_vof_fct_smoke PRIVATE
    "${MYPELE_ROOT}/test/unit"
    "${MYPELE_ROOT}/external/PeleC/Source"
    "${MYPELE_ROOT}/external/PeleC/Submodules/PelePhysics/Submodules/amrex/Src/Base"
    "${CMAKE_CURRENT_BINARY_DIR}"
  )
  target_link_libraries(test_vof_fct_smoke PRIVATE my_pele_headers)
  add_test(NAME vof_fct_smoke COMMAND test_vof_fct_smoke)

  add_executable(test_vof_plic_smoke test/unit/test_vof_plic.cpp)
  target_compile_definitions(test_vof_plic_smoke PRIVATE
    AMREX_SPACEDIM=2
    BL_SPACEDIM=2
    AMREX_GPU_MAX_THREADS=0
    NUM_ADV=1
    NUM_SPECIES=1
  )
  target_include_directories(test_vof_plic_smoke PRIVATE
    "${MYPELE_ROOT}/test/unit"
    "${MYPELE_ROOT}/external/PeleC/Source"
    "${MYPELE_ROOT}/external/PeleC/Submodules/PelePhysics/Submodules/amrex/Src/Base"
    "${CMAKE_CURRENT_BINARY_DIR}"
  )
  target_link_libraries(test_vof_plic_smoke PRIVATE my_pele_headers)
  add_test(NAME vof_plic_smoke COMMAND test_vof_plic_smoke)


  if(yaml-cpp_FOUND)

    add_executable(my_pele_yaml_to_parmparse
      tools/codex_yaml_to_parmparse.cpp
      src/common/input_parser/yaml_parser.cpp
      src/common/input_parser/parmparse_writer.cpp
      src/geometry/bc_tags.cpp
    )
    target_link_libraries(my_pele_yaml_to_parmparse PRIVATE my_pele_headers yaml-cpp::yaml-cpp)

    add_executable(test_yaml_parser_smoke
      test/unit/test_yaml_parser.cpp
      src/common/input_parser/yaml_parser.cpp
      src/common/input_parser/parmparse_writer.cpp
      src/geometry/bc_tags.cpp
    )
    target_link_libraries(test_yaml_parser_smoke PRIVATE my_pele_headers yaml-cpp::yaml-cpp)
    add_test(NAME yaml_parser_smoke COMMAND test_yaml_parser_smoke)
    set_tests_properties(yaml_parser_smoke PROPERTIES WORKING_DIRECTORY "${MYPELE_ROOT}")
  else()
    message(WARNING "yaml-cpp was not found; YAML parser/ParmParse adapter smoke is disabled")
  endif()

  add_executable(test_twophase_eos_smoke test/unit/test_twophase_eos.cpp)
  target_compile_definitions(test_twophase_eos_smoke PRIVATE
    AMREX_SPACEDIM=2
    BL_SPACEDIM=2
    AMREX_GPU_MAX_THREADS=0
  )
  target_include_directories(test_twophase_eos_smoke PRIVATE
    "${MYPELE_ROOT}/external/PeleC/Submodules/PelePhysics/Submodules/amrex/Src/Base"
    "${CMAKE_CURRENT_BINARY_DIR}"
  )
  target_link_libraries(test_twophase_eos_smoke PRIVATE my_pele_headers)
  add_test(NAME twophase_eos_smoke COMMAND test_twophase_eos_smoke)

  add_executable(test_twophase_hllc_smoke test/unit/test_twophase_hllc.cpp)
  target_include_directories(test_twophase_hllc_smoke PRIVATE
    "${MYPELE_ROOT}/test/unit/amrex_stubs"
  )
  target_link_libraries(test_twophase_hllc_smoke PRIVATE my_pele_headers)
  add_test(NAME twophase_hllc_smoke COMMAND test_twophase_hllc_smoke)

  add_executable(test_d2_law_smoke test/unit/test_d2_law.cpp)
  target_link_libraries(test_d2_law_smoke PRIVATE my_pele_headers)
  add_test(NAME d2_law_smoke COMMAND test_d2_law_smoke)
  set_tests_properties(d2_law_smoke PROPERTIES WORKING_DIRECTORY "${MYPELE_ROOT}")


  add_executable(test_second_order_advection_smoke test/unit/test_second_order_advection.cpp)
  target_link_libraries(test_second_order_advection_smoke PRIVATE my_pele_headers)
  add_test(NAME second_order_advection_smoke COMMAND test_second_order_advection_smoke)

  add_executable(test_sod_shock_tube_smoke test/unit/test_sod_shock_tube.cpp)
  target_link_libraries(test_sod_shock_tube_smoke PRIVATE my_pele_headers)
  add_test(NAME sod_shock_tube_smoke COMMAND test_sod_shock_tube_smoke)

  add_executable(test_isentropic_vortex_smoke test/unit/test_isentropic_vortex.cpp)
  target_link_libraries(test_isentropic_vortex_smoke PRIVATE my_pele_headers)
  add_test(NAME isentropic_vortex_smoke COMMAND test_isentropic_vortex_smoke)
endif()
