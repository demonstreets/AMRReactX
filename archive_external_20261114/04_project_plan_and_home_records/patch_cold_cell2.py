"""patch_cold_cell2.py: 修复低温跳过逻辑 - 用 if(skip_cold) 包裹化学更新"""
import sys

with open(sys.argv[1]) as f:
    content = f.read()

# Find the section from the `float rho = batch_rho[idx];` to the end of cell processing
old_start = "        // NN outputs: [dY_0..dY_9, dT] in [1/s] and [K/s]"
old_end = "        // Track function calls (set to 1 since we do one NN pass)"

new_code = """        // For cold cells (T < MIN_REACT_TEMP): skip chemistry update
        if (skip_cold) {
          // No chemical reactions for this cell - leave state unchanged
        } else {
          // NN outputs: [dY_0..dY_9, dT] in [1/s] and [K/s]
          // Euler update: Y_new = Y_old + dY * dt, T_new = T_old + dT * dt
          amrex::Real mass_frac_new[NUM_SPECIES];
          amrex::Real sum_Y = 0.0;

          for (int sp = 0; sp < NUM_SPECIES; sp++) {
            amrex::Real dY_dt = static_cast<amrex::Real>(out_row[sp]);
            amrex::Real rhoY_old = rY_in(i, j, k, sp);
            amrex::Real Y_old = rhoY_old / static_cast<amrex::Real>(rho);
            amrex::Real Y_new = Y_old + dY_dt * dt_react;
            Y_new = amrex::max<amrex::Real>(0.0, amrex::min<amrex::Real>(1.0, Y_new));
            mass_frac_new[sp] = Y_new;
            sum_Y += Y_new;
          }

          // Renormalize mass fractions
          if (sum_Y > 0.0) {
            amrex::Real inv_sum = 1.0 / sum_Y;
            for (int sp = 0; sp < NUM_SPECIES; sp++) {
              mass_frac_new[sp] *= inv_sum;
            }
          }

          // Write back rY = rho * Y_new
          for (int sp = 0; sp < NUM_SPECIES; sp++) {
            rY_in(i, j, k, sp) = static_cast<amrex::Real>(rho) * mass_frac_new[sp];
          }

          // Update temperature
          amrex::Real dT_dt = static_cast<amrex::Real>(out_row[NN_OUTPUT_DIM - 1]);
          amrex::Real T_new = T_in(i, j, k, 0) + dT_dt * dt_react;
          T_new = amrex::max<amrex::Real>(200.0, T_new);
          T_in(i, j, k, 0) = T_new;
        }

        // Update energy: rhoH += src * dt (same as RK64)
        rEner_in(i, j, k, 0) = rEner_in(i, j, k, 0) + dt_react * batch_rhoH[idx];

        // Track function calls
        FC_in(i, j, k, 0) = 1.0;"""

if old_start in content and old_end in content:
    start_pos = content.find(old_start)
    end_pos = content.find(old_end, start_pos)
    # Find the end of the "Track function calls" line
    end_of_block = content.find('\n', content.find('\n', end_pos) + 1) + 1
    
    # Replace from old_start to end_of_block with new_code
    old_block = content[start_pos:end_of_block]
    # But we need to be more precise - let's find where the old chemistry block ends
    content = content[:start_pos] + new_code + content[end_of_block:]
    with open(sys.argv[1], "w") as f:
        f.write(content)
    print("Patched successfully")
else:
    print("Markers not found")
    # Debug
    print(f"old_start found: {old_start in content}")
    print(f"old_end found: {old_end in content}")
