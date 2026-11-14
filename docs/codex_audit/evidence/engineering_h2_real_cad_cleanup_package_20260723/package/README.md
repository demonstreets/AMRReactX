# Engineering H2 Real-CAD Cleanup Package

Fill `real_cad_cleanup_manifest.json` from the template after source CAD and cleaned geometry files are staged.

Production credit requires:
- `synthetic: false` and `cad_source_is_real: true`
- `source_type` in `['as_built_cad', 'owner_operator_cad', 'plant_cad', 'vendor_cad']`
- at least three geometries for a large-layout campaign
- source and cleaned geometry files with exact SHA-256 hashes
- cleanup checks proving declared units, closed/watertight surfaces, nondegenerate elements, positive volume/area, and meter bounding boxes
- all intake checklist rows in `real_cad_intake_checklist.csv` satisfied by controlled evidence

This package is a data-ingestion gate. It does not claim CFD accuracy by itself.
