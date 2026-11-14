"""patch_build_cmake.py: 在 BuildPelePhysicsLib.cmake 中添加 ReactorNN"""
import sys

with open(sys.argv[1]) as f:
    content = f.read()

nn_block = '''
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

marker = "ReactorUtils.cpp\n    )"
insert_pos = content.find(marker)
if insert_pos > 0:
    insert_pos += len(marker)
    content = content[:insert_pos] + nn_block + content[insert_pos:]
    with open(sys.argv[1], "w") as f:
        f.write(content)
    print("Patched:", sys.argv[1])
else:
    print("Marker not found in:", sys.argv[1])
