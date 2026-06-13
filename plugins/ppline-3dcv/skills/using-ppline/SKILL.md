---
name: using-ppline
description: >-
  START HERE for the ProductPardesLine 3D-CV / medical-imaging platform via the
  ppline-3dcv MCP server. Token-efficient catalog + recipe so you call run_job /
  run_pipeline directly WITHOUT exploratory list_modules / get_module_info calls.
  Use whenever the user wants to run point-cloud / mesh / registration / SDF /
  segmentation / LiDAR / DICOM / image->3D operations on the platform. Routes to all 12
  other ppline-3dcv skills (domain skills + the mcp-tool-reference, data-io-and-files,
  visualization-and-viewers, samples-catalog and expert-context-and-models references).
---

# Using ProductPardesLine over MCP

All tools are on the **`ppline-3dcv`** MCP server. This skill embeds the full module
catalog so you DON'T need `list_modules()` / `get_module_info()` — call compute tools
straight away with the ids below. Only call the `list_*` tools if a result says an id is
unknown (catalog drift) or to fetch live sample ids.

## The universal recipe (memorize this)

1. **Get data in** → returns a `file_id`:
   - Built-in sample: `use_sample(sample_id)` (ids from `list_open3d_samples` /
     `list_pyvista_samples` / `list_simpleitk_samples`).
   - User's own file: `upload_file(filename, content_base64)` (read the local file,
     base64 it). Allowed: `.ply .pcd .txt .xyz .pts .las .vtk .vti .vtu .stl .obj .mha
     .nrrd .nii .dcm`.
   - DICOM folder: `upload_dicom_folder(files=[{filename, content_base64}, ...])` →
     volume `file_id` (`.vti` + `.mha`).
2. **Run ONE module (blocking, result in one call)**:
   `run_job(module_id, method_id, file_id=<id>, params={...})` → `{output_url, output_type,
   extra_outputs, logs_tail}`. Omit `params` to use defaults below.
   - Dual-input (registration): add `moving_file_id=<id>` or `moving_sample_id=<id>`
     (fixed → `--input`, moving → `--moving`). NEVER omit moving on a dual module — the
     script then self-aligns the fixed to itself.
3. **Chain modules** (linear): `run_pipeline(steps=[{module_id, method_id, params}], file_id=<id>)`
   → final `output_url`. (For dual-input registration use `run_job`, not pipeline.)
4. **Show 3D** → returns a clickable URL: `visualize_sample(id)` / `visualize_samples([..])`
   (MeshLab viewer) · `visualize_registration(fixed, moving, method)` (4-panel slicer).
5. **Long jobs**: if `run_job` returns `status:"running"`, poll `get_job_status(job_id)`
   (jobs are in-memory — lost on server restart; prefer letting `run_job` block).

Give the user the returned `output_url` / `view_url` directly — they are absolute and
downloadable.

## Full module catalog (id · methods `method_id(param=default)`)

Geometry units are the data's own (Open3D/PyVista samples ~unit-scale; medical volumes in mm).

**Point clouds & filtering**
- `point_cloud_processing` — `voxel_downsample(voxel_size=0.02)` · `statistical_outlier_removal(nb_neighbors=20, std_ratio=2.0)` · `radius_outlier_removal(radius=0.05, min_neighbors=5)` · `mesh_to_pointcloud()`
- `point_cloud_segmentation` — `ransac_plane(distance_threshold=0.01, num_iterations=1000)` · `dbscan_clustering(eps=0.02, min_points=10)`
- `features_extraction` — `normal_estimation(radius=0.05, max_nn=30)` · `fpfh_features(voxel_size=0.005)` · `curvature_estimation(radius=0.05, max_nn=30)`
- `stereo_3d_reconstruction` — `depth_colorization(colormap=0)` · `depth_filter(min_depth=0.0, max_depth=80.0)`
- `lidar_scene_detection` — `height_colorization(colormap=0)` · `ground_removal(distance_threshold=0.3)` · `object_clustering(ground_threshold=0.3, cluster_eps=0.5, min_cluster_points=10)`
- `lidar_camera_fusion` — `intensity_colorization(colormap=0)` · `roi_extraction(x_range=50, y_range=50, z_range=50)` · `multi_resolution(near_voxel=0.01, far_voxel=0.05)`
- `pyvista_pointcloud_processing` — `pv_threshold(lower=0, upper=1, scalars="")` · `pv_clip_plane(origin_x/y/z=0, normal_x=1,...)` · `pv_clip_box(x_min=-.5..z_max=.5)` · `pv_random_sample(fraction=0.5)` · `pv_extract_points(scalars="", lower=0, upper=1)`

**Meshes, surfaces & volumes**
- `mesh_processing` — `subdivision(iterations=1)` · `simplification(target_triangles=5000)` · `mesh_to_pcd_uniform(num_points=5000)` · `mesh_to_pcd_poisson_disk(num_points=5000)`
- `pyvista_mesh_processing` — `pv_decimate(target_reduction=0.5)` · `pv_subdivide(n_subdivisions=1, algorithm=linear)` · `pv_smooth_laplacian(n_iterations=20, relaxation_factor=0.01)` · `pv_smooth_taubin(n_iterations=20, pass_band=0.1)` · `pv_clean(tolerance=0.0)` · `pv_fill_holes(hole_size=100.0)` · `pv_compute_normals(flip_normals=0, consistency=1)` · `pv_triangulate()` · `pv_extract_surface()`
- `point_cloud_reconstruction` — `poisson(depth=9, scale=1.1)` · `convex_hull()` · `alpha_shape(alpha=0.03)` · `ball_pivoting(radius_factor=2.0)`
- `voxel_to_mesh` — `voxelization(voxel_size=0.01)` · `binary_erosion(voxel_size=0.01, erosion_iterations=1)`
- `sdf` — `compute_sdf(voxel_size=0.01, padding=5)` · `occupancy_reconstruction(voxel_size=0.01, padding=5)` · `sdf_voxel_visualization(resolution=32, min_clamp=-0.1, max_clamp=0.1)`
- `collision_detection` — `sdf_collision(obstacle_radius=0.5, penetration_ratio=0.3, num_samples=50000)` · `penetration_depth(obstacle_radius=0.5, overlap_distance=0.15)`
- `pyvista_volume_processing` — `pv_contour(n_contours=5, scalars="")` · `pv_slice(normal_x=1,..., origin_x=0,...)` · `pv_slice_orthogonal(x=0, y=0, z=0)` · `pv_threshold_volume(lower=0, upper=1)` · `pv_extract_geometry()` · `pv_extract_cells(cell_type=tetrahedral)`
- `pyvista_analysis` — `pv_curvature(curvature_type=mean)` · `pv_distance()` · `pv_glyph(scale_factor=0.01, vector_name=Normals)` · `pv_vector_magnitude(vector_name=Normals)` · `pv_scalar_stats(scalars="")` · `pv_extract_feature_edges(feature_angle=30, ...)`

**Registration (★ = dual-input → pass `moving_*`)**
- `registration` ★ — `ransac_global(voxel_size=0.5)` · `icp_refinement(voxel_size=0.5, max_iterations=2000)` · `ransac_icp_pipeline(voxel_size=0.5, rotation_degrees=45.0)`
- `deformable_registration` — `cpd_deformable(max_iterations=100, tolerance=0.001)` · `gaussian_deformation(displacement=0.02, radius=0.1)`
- `simpleitk_registration` ★ — `rigid(learning_rate=1.0, num_iterations=100, sampling_percentage=0.01)` · `advanced_rigid(learning_rate=0.2, num_iterations=200, sampling_percentage=0.15)` · `affine(...)` · `bspline(grid_spacing=50.0, num_iterations=100)` · `demons(num_iterations=20, standard_deviations=2.0)` · `difference_analysis(lower_threshold=50.0, upper_threshold=400.0)`
- `simpleitk_segmentation` — `otsu_threshold()` · `manual_threshold(lower=100, upper=1000)` · `connected_components(threshold=100, min_size=15)` · `watershed(threshold=100, seed_radius=10, min_object_size=15)`

## Auth, metering & file lifecycle (essentials)

- **Auth**: every call needs the project `X-API-Key` (`pl_…`) — the plugin injects it from
  `$PPLINE_API_KEY`. Missing/invalid → 401.
- **Metering**: compute tools meter usage (best-effort); no tier gating yet. Discovery,
  `use_sample`, `upload_file` and project-CRUD don't meter.
- **file_id**: a bare UUID. Inputs live in *uploads*, results in *outputs* (downloadable at
  an absolute `/api/files/outputs/<id>` URL). `run_job` jobs are **in-memory** — lost on
  server restart, so prefer letting `run_job` block over polling.
- Full per-tool signatures / return shapes / errors: `ppline-3dcv:mcp-tool-reference`.

## Context resources (read BEFORE writing platform/library code)

- `context://expert/{topic}` — 14 curated experts (`open3d, pyvista, vtk, simpleitk,
  mesh-processing, threejs, glsl-shader, 3d-file-format, node-pipeline,
  slicer-integration, medical-registration, frontend-architecture, backend-architecture,
  devops-infrastructure`).
- `context://model/{model_id}` — deep-learning model-skill (architecture + training recipe).
- What each topic covers + how to read these: `ppline-3dcv:expert-context-and-models`.

## Where to go next — all 12 sibling skills

**Domain (run algorithms)**
| Task | Skill |
|------|-------|
| Point-cloud filtering, segmentation, features, LiDAR, depth | `ppline-3dcv:pointcloud-ops` |
| Mesh edits, reconstruction, SDF, voxels, collision, PyVista volume/analysis | `ppline-3dcv:mesh-and-surfaces` |
| Align two point clouds (RANSAC/ICP/CPD) | `ppline-3dcv:point-cloud-registration` |
| CT/MR/DICOM registration + segmentation + QC + slicer view | `ppline-3dcv:medical-imaging` |
| 2D AI on images + image→3D (.glb) | `ppline-3dcv:ai-3d-generation` |
| Multi-step pipelines + projects (save/run DAG, API keys) | `ppline-3dcv:pipelines-and-projects` |
| Train/fine-tune a DL model on your own data | `ppline-3dcv:deep-learning-models` |

**Reference / cross-cutting**
| Need | Skill |
|------|-------|
| Exact signature / return shape / error of ANY of the 34 tools | `ppline-3dcv:mcp-tool-reference` |
| Upload, DICOM, file_id lifecycle, volume I/O, transforms | `ppline-3dcv:data-io-and-files` |
| Open results in a viewer/slicer + deep-link URL grammar | `ppline-3dcv:visualization-and-viewers` |
| Which built-in sample ids exist (Open3D / PyVista / SimpleITK) | `ppline-3dcv:samples-catalog` |
| The free expert context + model-skill resources | `ppline-3dcv:expert-context-and-models` |
