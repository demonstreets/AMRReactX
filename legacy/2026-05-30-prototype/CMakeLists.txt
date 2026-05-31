cmake_minimum_required(VERSION 3.24)

project(AMRReactX LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(AMReX REQUIRED)

add_executable(amrreactx
    src/main.cpp
)

target_link_libraries(amrreactx PRIVATE AMReX::amrex_3d)
