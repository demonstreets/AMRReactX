"""fix_make_pelelmex.py: 修复 Make.PeleLMeX 添加 AMReX-Hydro 源文件"""
import sys

with open(sys.argv[1]) as f:
    content = f.read()

old = "INCLUDE_LOCATIONS += $(foreach dir, $(HYDROdirs), $(AMREX_HYDRO_HOME)/$(dir))"
new = """INCLUDE_LOCATIONS += $(foreach dir, $(HYDROdirs), $(AMREX_HYDRO_HOME)/$(dir))
  Bpack += $(foreach dir, $(HYDROdirs), $(AMREX_HYDRO_HOME)/$(dir)/Make.package)
  Blocs += $(foreach dir, $(HYDROdirs), $(AMREX_HYDRO_HOME)/$(dir))"""

if old in content:
    content = content.replace(old, new)
    with open(sys.argv[1], "w") as f:
        f.write(content)
    print("Fixed:", sys.argv[1])
else:
    print("Pattern not found")
    print([l for l in content.splitlines() if 'HYDRO' in l][:5])
