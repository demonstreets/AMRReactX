set(PELE_PHYSICS_EOS_MODEL Fuego)
set(PELE_PHYSICS_CHEMISTRY_MODEL air)
set(PELE_PHYSICS_TRANSPORT_MODEL Simple)
set(PELE_PHYSICS_ENABLE_SPRAY OFF)
set(PELE_PHYSICS_SPRAY_FUEL_NUM 0)
set(PELE_PHYSICS_SPRAY_GCM OFF)
set(PELE_PHYSICS_ENABLE_SOOT OFF)
set(PELE_PHYSICS_ENABLE_RADIATION OFF)
include(BuildExeAndLib)

# --- Phase 2 工程模块集成 ---
# 添加自定义模块的 include 目录和编译单元
# 注: evaporation/ 和 wind/ 为 header-only 模块，无需添加 .cpp
target_include_directories(${EXE_NAME} PRIVATE
    ${CMAKE_SOURCE_DIR}/../../../src/engineering/turbulence
    ${CMAKE_SOURCE_DIR}/../../../src/engineering/evaporation
    ${CMAKE_SOURCE_DIR}/../../../src/engineering/wind
)

target_sources(${EXE_NAME} PRIVATE
    ${CMAKE_SOURCE_DIR}/../../../src/engineering/turbulence/k_epsilon_core.cpp
    ${CMAKE_SOURCE_DIR}/../../../src/engineering/turbulence/wall_functions.cpp
)
