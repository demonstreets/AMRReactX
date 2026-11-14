"""fix_make.py: 修复 Make.PelePhysics 中的 USE_REACTORNN 块"""
import sys

with open(sys.argv[1]) as f:
    content = f.read()

# Find and replace the broken block
import re
# Match the existing (broken) USE_REACTORNN block
pattern = r'# Enable with USE_REACTORNN=TRUE.*?(?=^# for debugging|\Z)'
replacement = r"""# Enable with USE_REACTORNN=TRUE in the case GNUmakefile
ifdef USE_REACTORNN
  DEFINES += -DPELE_USE_REACTORNN
  RNNLIB_HOME ?= $(HOME)/NN_Project/ml_chem/h2o2/rnn_torch
  TORCH_DIR  ?= $(HOME)/.local/lib/python3.12/site-packages/torch
  INCLUDE_LOCATIONS += $(RNNLIB_HOME)
  INCLUDE_LOCATIONS += $(TORCH_DIR)/include
  INCLUDE_LOCATIONS += $(TORCH_DIR)/include/torch/csrc/api/include
  LIBRARIES += -L$(RNNLIB_HOME) -lrnn
  LIBRARIES += -L$(TORCH_DIR)/lib -ltorch -ltorch_cpu -lc10
  LDFLAGS += -Wl,-rpath,$(TORCH_DIR)/lib
endif

"""

if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)
    with open(sys.argv[1], "w") as f:
        f.write(content)
    print("Fixed:", sys.argv[1])
else:
    print("Pattern not found in:", sys.argv[1])
    # Print the current content to debug
    for line in content.splitlines():
        if 'REACTORNN' in line or 'RNNLIB' in line or 'TORCH_DIR' in line:
            print("  ", line)
