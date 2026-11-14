# DataverseNO Long-Window Reconciliation

- Status: `TRIAGED-DATAVERSE-OPEN-CHANNEL-LONG-WINDOW-REFINED-SOURCE-GAP`
- Existing 120 s window reaches peak interval: `True`
- Existing 120 s all sensors passed: `False`
- Existing 120 s failed sensors: `29`
- Current refined source ready: `True`
- Current refined source time end: `0.005` s
- AMR finest-owner projection ready: `True`
- Steps to 113 s at current refined dt: `22600000`
- Strict blocker cleared: `False`

## Interpretation

- The repository already contains a 120 s MPI+CUDA agreement attempt that reaches the 113-117 s reference peak interval.
- That 120 s attempt used an inflated 0.08 m numerical source radius and did not pass the production agreement thresholds.
- The current refined 2.3 mm source plus AMR finest-owner projection is implemented and build-verified, but its full-channel run evidence currently reaches only 0.005 s.
- At dt=5e-6 s, a direct refined-source run to 113 s would require about 22.6 million steps, so a production long-window campaign needs either a calibrated stable larger timestep strategy, more resources, or additional modeling changes.
