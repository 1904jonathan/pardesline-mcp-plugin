---
name: pointcloud-ops
description: >-
  Point-cloud filtering/downsampling/outlier removal, RANSAC plane & DBSCAN
  segmentation, normals/curvature/FPFH features, depth colorization & filtering,
  LiDAR height/intensity colorization + ground removal + object clustering, and
  PyVista point-cloud threshold/clip/sample/extract — all via the ppline-3dcv MCP
  server. Load whenever the user wants to denoise/clean/downsample a point cloud,
  remove outliers or ground, segment a plane, cluster objects, estimate
  normals/FPFH/curvature, colorize depth/height/intensity, or clip/crop/threshold
  a cloud. Covers modules point_cloud_processing, point_cloud_segmentation,
  features_extraction, stereo_3d_reconstruction, lidar_scene_detection,
  lidar_camera_fusion, pyvista_pointcloud_processing.
---

# Point-Cloud Ops (ppline-3dcv)

7 modules, 19 methods, all returning a single `.ply` `output_url`. This file is the
**fast index + how-to-choose**. For the EXHAUSTIVE per-method spec (purpose from the real
script, every param with type/default/range/effect, recolor-vs-crop behavior, copy-paste
example, and the **script-vs-module.json discrepancies** that will silently no-op a job),
read the sibling **[reference.md](reference.md)**.

- Upload→`run_job`→`output_url` recipe: **ppline-3dcv:using-ppline** (do not repeat it).
- `run_job` return shape (`{output_url, output_type, extra_outputs, logs_tail}`): **ppline-3dcv:mcp-tool-reference**. None of these methods emit `extra_outputs`; always read `logs_tail` for counts/ranges.
- Sample ids: **ppline-3dcv:samples-catalog**, or `list_open3d_samples()` / `list_pyvista_samples()` at runtime. **Never invent sample ids or param names.**

All calls: `run_job(module_id, method_id, file_id=<id>, params={...})`. Omit `params` (or pass `{}`) to use each script's defaults (safe). Units are the **data's own** — Open3D/PyVista samples ~unit-scale (bbox ≈ 1), LiDAR/stereo data in **meters**.

## Catalog (module_id — method_id(real script defaults))
| module_id | methods → see [reference.md](reference.md) |
|---|---|
| point_cloud_processing | `voxel_downsample(voxel_size=0.02)` · `statistical_outlier_removal(nb_neighbors=20, std_ratio=2.0)` · `radius_outlier_removal(radius=0.05, min_neighbors=5)` · `mesh_to_pointcloud()` *(needs a MESH)* |
| point_cloud_segmentation | `ransac_plane(distance_threshold=0.01, num_iterations=1000)` · `dbscan_clustering(eps=0.02, min_points=10)` |
| features_extraction | `normal_estimation(radius=0.05, max_nn=30)` · `fpfh_features(voxel_size=0.005)` *(downsamples)* · `curvature_estimation(radius=0.05, max_nn=30)` |
| stereo_3d_reconstruction | `depth_colorization(colormap=0)` *(colors by Z)* · `depth_filter(min_depth=0.1, max_depth=0.9)` *(percentile FRACTIONS 0–1)* |
| lidar_scene_detection | `height_colorization(colormap=0)` · `ground_removal(distance_threshold=0.3)` · `object_clustering(ground_threshold=0.3, cluster_eps=0.5, min_cluster_points=10)` |
| lidar_camera_fusion | `intensity_colorization(colormap=0)` *(distance-from-origin)* · `roi_extraction(x_range=0.5, y_range=0.5, z_range=0.8)` *(FACTORS 0–1)* · `multi_resolution(levels=3, base_voxel_size=0.01)` |
| pyvista_pointcloud_processing | `pv_threshold(lower=0, upper=1, scalars="")` · `pv_clip_plane(origin_x/y/z=0, normal_x=1, normal_y=0, normal_z=0)` · `pv_clip_box(x_min=-0.5..z_max=0.5)` · `pv_random_sample(fraction=0.5)` · `pv_extract_points(scalars="", lower=0, upper=1)` |

> ⚠️ The defaults above are the **script's actual** defaults. For `depth_filter`, `roi_extraction`, and `multi_resolution` they DIFFER from `module.json` — see the discrepancy table at the end and in reference.md.

## Examples
```text
# A) Clean + downsample an Open3D sample (chain output_file_id forward)
use_sample(sample_id="<from list_open3d_samples()>")
run_job("point_cloud_processing","statistical_outlier_removal", file_id="<id>",
        params={"nb_neighbors":20,"std_ratio":2.0})
run_job("point_cloud_processing","voxel_downsample", file_id="<denoised_id>",
        params={"voxel_size":0.02})

# B) Mesh in → cloud → normals → features
run_job("point_cloud_processing","mesh_to_pointcloud", file_id="<mesh_id>", params={})
run_job("features_extraction","normal_estimation", file_id="<cloud_id>",
        params={"radius":0.05,"max_nn":30})
run_job("features_extraction","fpfh_features", file_id="<normals_id>", params={"voxel_size":0.005})

# C) LiDAR (meters): strip ground then cluster objects
run_job("lidar_scene_detection","ground_removal", file_id="<id>", params={"distance_threshold":0.3})
run_job("lidar_scene_detection","object_clustering", file_id="<no_ground_id>",
        params={"ground_threshold":0.3,"cluster_eps":0.5,"min_cluster_points":10})

# D) Segment the dominant plane, then DBSCAN the rest
run_job("point_cloud_segmentation","ransac_plane", file_id="<id>",
        params={"distance_threshold":0.01,"num_iterations":1000})
run_job("point_cloud_segmentation","dbscan_clustering", file_id="<id>",
        params={"eps":0.02,"min_points":10})

# E) PyVista crop + subsample (set bounds from REAL extents, not the ±0.5 default)
run_job("pyvista_pointcloud_processing","pv_clip_box", file_id="<id>",
        params={"x_min":-0.2,"x_max":0.2,"y_min":-0.2,"y_max":0.2,"z_min":-0.2,"z_max":0.2})
run_job("pyvista_pointcloud_processing","pv_random_sample", file_id="<clipped_id>", params={"fraction":0.3})
```

## Recommended ordering
1. `mesh_to_pointcloud` (only if input is a mesh) → 2. outlier removal (`statistical_` then optionally `radius_`) → 3. `voxel_downsample` → 4. `normal_estimation` → 5. segmentation (`ransac_plane` / `dbscan_clustering`) or features (`fpfh_features` / `curvature_estimation`).
**Always downsample BEFORE features/segmentation/clustering** — `curvature_estimation` (per-point Python loop) and DBSCAN on raw LiDAR are slow.

## Choosing params (non-obvious — full detail in reference.md)
- **voxel_size / radii / eps scale with the data.** ~1–5% of the bbox diagonal. Unit-scale defaults (0.02, 0.05) silently no-op on meter-scale LiDAR; scale up to 0.05–0.5 m.
- **statistical_outlier_removal:** **lower `std_ratio` removes MORE** (stricter). Tune `std_ratio` before `nb_neighbors`.
- **radius_outlier_removal:** `radius` MUST exceed point spacing or the cloud comes back empty.
- **dbscan_clustering:** `eps` ≈ a few × point spacing — too small → all noise (−1), too large → one blob. LiDAR `object_clustering` uses `cluster_eps=0.5` m (≫ the 0.02 unit-scale eps; don't copy across).
- **normal_estimation / curvature / fpfh:** feature radius > spacing but < feature size. `fpfh_features` downsamples internally at `voxel_size` (its only knob) and derives normal radius ×2 / feature radius ×5.
- **ransac_plane / ground_removal:** `distance_threshold` ≈ noise/flatness tolerance. Each call peels ONE plane — re-run to remove floor then walls.
- **colormap (depth/height/intensity):** 0 = default ramp. `depth_colorization` colors by **Z**; `intensity_colorization` colors by **distance-from-origin**. See reference.md for exact per-index palettes.

## Gotchas
- **`mesh_to_pointcloud` requires a real MESH** (faces) — it errors on a point-cloud input. Conversely, every other method reads only vertices if you hand it a mesh; convert first for an even sampling.
- **Output is the recolored/cropped cloud only — no `extra_outputs`.** Plane equations, cluster counts, scalar ranges, kept/removed counts are in `logs_tail`. Read it.
- **Recolor vs crop:** colorization/feature/segmentation methods keep all geometry and only change RGB; `*_outlier_removal`, `*_filter`, `ground_removal`, `roi_extraction`, `pv_clip_*`, `pv_*sample/extract`, `voxel_downsample`, `fpfh_features` change the point set.
- **`fpfh_features` and downstream ICP/global-registration need normals** — run `normal_estimation` first.
- **Empty result** after an outlier/radius/threshold/clip op almost always = wrong scale (radius/eps/voxel too small, or threshold/box outside the scalar's/coords' real range). For PyVista threshold/extract, the bounds are in **scalar units** (read the logged min/max); for `pv_clip_box` the ±0.5 default assumes unit-scale data.
- **`dbscan_clustering` labels noise as −1** (dark gray) — some unclustered points are normal.
- **`object_clustering` writes the ORIGINAL cloud and exits 0** if ground removal leaves nothing — check `logs_tail`.
- **`curvature_estimation` is a per-point Python loop** → slow on large clouds; downsample first. Output is curvature-as-color (hot ramp), geometry unchanged.
- **`multi_resolution` lays out copies side-by-side in +X** (a LOD strip), so the output bbox is much wider than the input — it is not a single adaptive cloud.

## ⚠️ Script-vs-module.json discrepancies (these silently break jobs — full table in reference.md)
| method | `module.json` default | **pass this instead** |
|---|---|---|
| `depth_filter` | `min_depth=0.0, max_depth=80.0` | **fractions** `{"min_depth":0.1,"max_depth":0.9}` (percentiles ×100) |
| `roi_extraction` | `x/y/z_range=50` | **factors 0–1** `{"x_range":0.5,"y_range":0.5,"z_range":0.8}` (50 ⇒ 25×extent ⇒ no crop) |
| `multi_resolution` | `near_voxel=0.01, far_voxel=0.05` | real args `{"levels":3,"base_voxel_size":0.01}` (the json names don't exist) |
| `intensity_colorization` | "2=inferno, 3=coolwarm" | 0=warm/cool · 1=viridis · 2=plasma · ≥3→viridis |

When unsure, pass `params={}` to use the **script's** defaults, then verify with `logs_tail`.
