"""patch_cold_cell.py: 给 ReactorNN.cpp 加低温跳过逻辑"""
import sys

with open(sys.argv[1]) as f:
    content = f.read()

# Find the output loop section and add cold-cell skip
old = """  idx = 0;
  for (int k = lo.z; k < lo.z + len.z; ++k) {
    for (int j = lo.y; j < lo.y + len.y; ++j) {
      for (int i = lo.x; i < lo.x + len.x; ++i) {
        const float* out_row = &batch_output[idx * NN_OUTPUT_DIM];"""

new = """  idx = 0;
  for (int k = lo.z; k < lo.z + len.z; ++k) {
    for (int j = lo.y; j < lo.y + len.y; ++j) {
      for (int i = lo.x; i < lo.x + len.x; ++i) {
        // Skip cold cells (outside training data range 800-2800K)
        bool skip_cold = (cell_temp[idx] < MIN_REACT_TEMP);
        const float* out_row = skip_cold ? nullptr : &batch_output[idx * NN_OUTPUT_DIM];"""

if old in content:
    content = content.replace(old, new)
else:
    print("Pattern 1 not found")
    # Debug: show what's around idx = 0
    for i, line in enumerate(content.splitlines()):
        if 'idx = 0' in line and 'for' in line:
            print(f"  Line {i+1}: {line}")

with open(sys.argv[1], "w") as f:
    f.write(content)
print("Done")
