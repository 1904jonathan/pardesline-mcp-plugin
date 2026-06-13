---
name: samples-catalog
description: >-
  The built-in datasets you can run algorithms on without uploading: Open3D point
  clouds/meshes, PyVista meshes/volumes, and SimpleITK medical CT/MR volumes. Lists the
  sample ids to pass to use_sample / visualize_sample / run_job(sample_id=...). Load when
  the user says "use a sample", "try it on the bunny", "demo this", or asks what data is
  available.
---

# Built-in samples catalog (ppline-3dcv)

The platform ships **three families** of ready-to-use datasets. You never have to upload
anything to demo an algorithm — pass a sample **id** straight into a compute or viz tool.
All ids below are real (taken from the platform's generators + materialized registries);
do not invent new ones.

## The three families

| Family | Count | List tool | Geometry types | Example ids |
|--------|------:|-----------|----------------|-------------|
| **Open3D** (PLY) | 11 | `list_open3d_samples()` | mesh, pointcloud | `bunny`, `armadillo`, `eagle`, `icp_source`, `icp_target` |
| **PyVista** (PLY / VTI / VTK / VTU) | 45 | `list_pyvista_samples()` | mesh, volume, pointcloud | `pv_sphere`, `pv_teapot`, `pv_nefertiti`, `pv_knee`, `pv_lidar` |
| **SimpleITK** (medical MHA/MHD/VTI) | 21 | `list_simpleitk_samples()` | volume (CT/MR/EM/seg) | `sitk_training_001_ct`, `sitk_training_001_mr_T1`, `sitk_popi_00`, `sitk_liver_patient01` |

- **Open3D** — Stanford reference geometry + simple primitives + an ICP demo pair. Best for
  point-cloud / mesh / registration demos.
- **PyVista** — geometric primitives, parametric surfaces, downloaded CAD/scan meshes, and
  volumetric CT/MR/industrial datasets. Best for mesh processing, volume contouring/slicing,
  LiDAR.
- **SimpleITK** — real medical CT/MR/4D-CT/segmentation volumes. Best for medical
  registration, segmentation, and DICOM/QC work. (4 of these are PyVista volumes re-exposed
  as medical-compatible VTI; 17 are native SimpleITK downloads.)

The **full id list with names, geometry types and notes is in [reference.md](reference.md)** —
read it when the user wants the complete menu or a specific category.

## How ids flow into tools

An id from any of the three `list_*` tools is accepted by:

- `use_sample(sample_id)` → materializes the sample into a fresh `file_id` you can feed to
  `run_job` / `run_pipeline`. Returns `{file_id, geometry_type, name, extension}`.
- `run_job(module_id, method_id, sample_id=<id>, params={...})` → runs an algorithm directly
  on a sample (auto-materialized; no separate `use_sample` call needed). Blocks and returns
  the result.
- `visualize_sample(sample_id)` / `visualize_samples([id, ...])` → opens the sample(s) in the
  full-screen MeshLab viewer; returns a clickable `view_url`. (Open3D ids work best here.)
- `visualize_registration(fixed, moving, method)` → 4-panel slicer view; `fixed` and `moving`
  accept SimpleITK / PyVista-volume sample ids.

You usually do **not** need to call the `list_*` tools first — pick an id from reference.md.
Only call a `list_*` tool to confirm live availability or if an id is rejected.

## Registration needs a PAIR (fixed + moving)

Registration / dual-input modules align a **moving** dataset onto a **fixed** one, so you
must supply BOTH:

```
run_job("simpleitk_registration", "rigid",
        sample_id="sitk_training_001_ct",          # fixed  → --input
        moving_sample_id="sitk_training_001_mr_T1") # moving → --moving
```

Never omit the moving input on a dual-input module — the script then "registers" the fixed
volume to itself (self-alignment, meaningless result).

Recommended built-in pairs:

| Use case | fixed | moving |
|----------|-------|--------|
| Brain CT↔MR (RIRE) | `sitk_training_001_ct` | `sitk_training_001_mr_T1` |
| Lung 4D-CT deformable (POPI) | `sitk_popi_00` | any of `sitk_popi_10/20/30/40/50` |
| Point-cloud ICP (Open3D demo) | `icp_target` | `icp_source` |
| Liver segmentation inter-observer | `sitk_liver_patient01` | `sitk_liver_rad01/02/03` |

See `ppline-3dcv:medical-imaging` and `ppline-3dcv:point-cloud-registration` for method
parameters; see `reference.md` here for every sample id.
