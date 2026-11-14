"""fix_cmake.py: 在 PeleLMeX CMake 构建中添加 ReactorNN 支持"""

# 1. CMakeLists.txt — 添加编译选项
cmake_option = '''
# ReactorNN (NN chemical kinetics surrogate)
option(PELE_ENABLE_REACTORNN "Enable neural network chemistry kinetics" OFF)
'''

# 2. BuildPelePhysicsLib.cmake — 添加源文件、头文件路径、链接
# 在 Reactor 源文件段落后添加 ReactorNN

pele_physics_reactions_nn = '''
    if(PELE_ENABLE_REACTORNN)
      target_compile_definitions(${pele_physics_lib_name} PUBLIC PELE_USE_REACTORNN)
      target_sources(${pele_physics_lib_name}
        PRIVATE
          ${PELE_PHYSICS_REACTIONS_DIR}/ReactorNN.H
          ${PELE_PHYSICS_REACTIONS_DIR}/ReactorNN.cpp
      )
      set(RNNLIB_HOME "$ENV{HOME}/NN_Project/ml_chem/h2o2/rnn_torch")
      set(TORCH_DIR "$ENV{HOME}/.local/lib/python3.12/site-packages/torch")
      target_include_directories(${pele_physics_lib_name} PUBLIC ${RNNLIB_HOME})
      target_include_directories(${pele_physics_lib_name} SYSTEM PUBLIC ${TORCH_DIR}/include)
      target_include_directories(${pele_physics_lib_name} SYSTEM PUBLIC ${TORCH_DIR}/include/torch/csrc/api/include)
      target_link_libraries(${pele_physics_lib_name} PUBLIC
        ${RNNLIB_HOME}/librnn.a
        ${TORCH_DIR}/lib/libtorch.so
        ${TORCH_DIR}/lib/libtorch_cpu.so
        ${TORCH_DIR}/lib/libc10.so
      )
    endif()
'''

import sys

# Patch CMakeLists.txt
with open(sys.argv[1]) as f:
    content = f.read()

if 'PELE_ENABLE_REACTORNN' not in content:
    # Insert after the last option() before the C++ Options section
    insert_pos = content.find('\n# C++ Options')
    content = content[:insert_pos] + cmake_option + content[insert_pos:]
    with open(sys.argv[1], "w") as f:
        f.write(content)
    print("Patched:", sys.argv[1])
else:
    print("Already patched:", sys.argv[1])

# Patch BuildPelePhysicsLib.cmake
with open(sys.argv[2]) as f:
    content = f.read()

if 'ReactorNN' not in content:
    # Insert the ReactorNN section after the ReactorCvodePreconditioner section
    marker = 'ReactorCvodePreconditioner.cpp'
    insert_pos = content.find(marker, content.find(marker) + len(marker))
    if insert_pos > 0:
        insert_pos = content.find('\n    )\n', insert_pos) + 6
        content = content[:insert_pos] + pele_physics_reactions_nn + content[insert_pos:]
        with open(sys.argv[2], "w") as f:
            f.write(content)
        print("Patched:", sys.argv[2])
    else:
        print("Marker not found in:", sys.argv[2])
else:
    print("Already patched:", sys.argv[2])
