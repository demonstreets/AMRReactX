#!/bin/bash
export PATH=/home/cj/.npm-global/bin:$PATH
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY=***ome...cd /home/cj/my-pele

claude -p "编译 PelePhysics。AMReX在external/amrex，PelePhysics在external/PelePhysics且Submodules/amrex已软链。SUNDIALS如需要请用apt装libsundials-dev。完成后报告编译结果。"   --model claude-sonnet --max-turns 15 2>&1 | tee /tmp/cc_phase0.log
