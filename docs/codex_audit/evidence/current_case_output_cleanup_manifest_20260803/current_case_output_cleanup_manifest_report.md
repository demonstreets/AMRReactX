# Current Case-Output Cleanup Manifest

- Status: `AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST`
- Generated/case-output git entries: `309`
- Cleanup candidate roots: `32`
- Existing candidate roots: `2`
- Already-missing candidate roots: `30`
- Existing candidate size KiB: `8`
- Cleanup performed: `False`

## Candidate Sample

- `examples/academic/rayleigh_taylor/AMReX_buildInfo.cpp` kind=`generated_build_metadata_file` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.0498042` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.0529036` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.0556617` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.0682824` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.0817258` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.1029174` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.1050419` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.1143438` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.1349918` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.1356355` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.1490527` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.7699801` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.7959640` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.9281908` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00000.old.9518449` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00002.old.0167888` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00002.old.3280654` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk00020.old.1950868` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk01000.old.4328205` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk01000.old.7982188` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/academic/shock_droplet/chk01000.old.9622512` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/engineering/backward_facing_step/chk00000.old.2715963` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/engineering/backward_facing_step/chk00000.old.3920124` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/engineering/backward_facing_step/chk00100.old.1787719` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/engineering/backward_facing_step/chk00100.old.3153737` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/engineering/backward_facing_step/chk00200.old.8313595` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/engineering/backward_facing_step/chk00200.old.9972798` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/engineering/bfs_kepsilon/chk00000.old.4853439` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/engineering/bfs_kepsilon/chk00100.old.2395318` kind=`case_output_directory` exists=`False` size_kib=`None`
- `examples/engineering/c3h8_flacs/AMReX_buildInfo.cpp` kind=`generated_build_metadata_file` exists=`True` size_kib=`4`
- `external/PeleLMeX/Exec/RegTests/EB_EnclosedFlame/AMReX_buildInfo.cpp` kind=`generated_build_metadata_file` exists=`True` size_kib=`4`

## Recommendations

- Review this manifest before any disk cleanup; it is not itself a cleanup command.
- Already-missing roots usually represent previous removal of generated outputs and should be reconciled separately from source changes.
- Existing roots may be cleanup candidates only after required evidence reports, logs, and plotfiles have been preserved.
