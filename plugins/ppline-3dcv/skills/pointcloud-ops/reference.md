# Point-Cloud Ops — Exhaustive Method Reference (ppline-3dcv)

Per-method ground truth for the 7 point-cloud modules, read directly from the real
`modules/<id>/scripts/*.py` (not just `module.json`). Where the script disagrees with
`module.json`, the **script wins** and the discrepancy is called out — those are the
sharp edges.

Companion to **[SKILL.md](SKILL.md)**. For the upload→run_job recipe see
**ppline-3dcv:using-ppline**; for the `run_job` return shape see
**ppline-3dcv:mcp-tool-reference**; for sample ids see **ppline-3dcv:samples-catalog**
(or call `list_open3d_samples()` / `list_pyvista_samples()` at runtime — never invent ids).

## Conventions used below
- **Input geom** = geometry the script actually reads: `pointcloud` (via `o3d.io.read_point_cloud`, which on a mesh file reads vertices only), `mesh` (via `read_triangle_mesh`), or `any` (PyVista `pv.read`, mesh or cloud).
- **Output** = always `.ply` for every method here (`output_extension` in every `module.json`). Most Open3D methods **recolor** the cloud (write per-point RGB); note which change geometry vs only color.
- Every call: `run_job(module_id="...", method_id="...", file_id="<id>", params={...})`. Returns `{output_url, output_type, extra_outputs, logs_tail}`. **None of these methods emit `extra_outputs`** — the colored/filtered cloud is the single `output_url`. Read `logs_tail` for the loguru counts (inliers, clusters, ranges).
- Geometry units are the **data's own**. Open3D/PyVista samples are ~unit-scale (bbox ≈ 1); LiDAR/stereo data is in **meters**. Defaults below are tuned for unit-scale unless stated.

---

# 1. point_cloud_processing  (order 1, category "processing")

Fundamental preprocessing. Input formats `.ply .pcd .txt .xyz`.

## voxel_downsample
- **Purpose:** `pcd.voxel_down_sample(voxel_size)` — partitions space into a regular grid of cubes of side `voxel_size`; each non-empty voxel is replaced by the **centroid** of its points. Reduces count + gives uniform spatial density. Changes geometry; preserves nothing per-point but the centroid (colors/normals averaged if present).
- **Input geom:** pointcloud · **Output:** downsampled `.ply`.

| param | meaning | type | default | range | effect |
|---|---|---|---|---|---|
| `voxel_size` | cube side length (data units) | float | 0.02 | 0.001–0.5 | larger = fewer points / coarser; smaller = more detail |

- **Log:** input pts, output pts, `reduction: X%`.
- **Example:** `run_job("point_cloud_processing","voxel_downsample", file_id, {"voxel_size":0.02})`
- **Gotcha:** 0.02 assumes unit-scale (Open3D bunny). For LiDAR in meters this removes nearly nothing — use 0.05–0.2. Pick ~1–5% of the bbox diagonal. Too-large voxel can collapse the whole cloud to a handful of points.

## statistical_outlier_removal
- **Purpose:** `pcd.remove_statistical_outlier(nb_neighbors, std_ratio)`. For each point computes mean distance to its `nb_neighbors` nearest neighbors; removes points whose mean distance exceeds `global_mean + std_ratio * global_std`. Returns inlier indices; script keeps `pcd.select_by_index(ind)`. Removes scattered noise; **geometry-only** (no recolor).
- **Input geom:** pointcloud · **Output:** denoised `.ply`.

| param | meaning | type | default | range | effect |
|---|---|---|---|---|---|
| `nb_neighbors` | k neighbors for the per-point mean distance | int | 20 | 5–100 | fewer = more local/aggressive |
| `std_ratio` | std-dev multiplier threshold | float | 2.0 | 0.5–5.0 | **lower = removes more** (stricter); higher = gentler |

- **Log:** `Inliers: N, removed: M`.
- **Example:** `run_job("point_cloud_processing","statistical_outlier_removal", file_id, {"nb_neighbors":20,"std_ratio":2.0})`
- **Gotcha:** Tune `std_ratio` first. Very low `std_ratio` (≈0.5) on a clean cloud can strip real surface detail.

## radius_outlier_removal
- **Purpose:** `pcd.remove_radius_outlier(nb_points=min_neighbors, radius)`. Removes any point with fewer than `min_neighbors` neighbors inside a sphere of `radius`. Good for isolated specks; **geometry-only**.
- **Input geom:** pointcloud · **Output:** denoised `.ply`.

| param | meaning | type | default | range | effect |
|---|---|---|---|---|---|
| `radius` | neighbor-search sphere radius (data units) | float | 0.05 | 0.001–1.0 | too small → deletes almost everything |
| `min_neighbors` | min neighbors to keep a point | int | 5 | 1–50 | higher = more aggressive |

- **Note:** `min_neighbors` maps to Open3D's `nb_points` argument.
- **Example:** `run_job("point_cloud_processing","radius_outlier_removal", file_id, {"radius":0.05,"min_neighbors":5})`
- **Gotcha:** `radius` **must exceed typical point spacing** or the result is empty. If the cloud comes back near-empty, raise `radius` or lower `min_neighbors`. Scale `radius` up to meters for LiDAR.

## mesh_to_pointcloud
- **Purpose:** `read_triangle_mesh` → extract **vertices** into a `PointCloud` (discards faces/triangles). Preserves vertex **normals** and **colors** if the mesh has them. Use to feed mesh data into cloud-only algorithms. Note: this samples ONLY the vertices, not the faces — for an even surface sampling use the `mesh_processing` module's `mesh_to_pcd_uniform` / `mesh_to_pcd_poisson_disk` instead (see ppline-3dcv:mesh-and-surfaces).
- **Input geom:** **mesh** (must have triangles) · **Output:** vertex `.ply`.
- **Params:** none.
- **Log:** `Input: V vertices, T triangles` → `Output: V points`; "Normals preserved" / "Colors preserved" when present.
- **Example:** `run_job("point_cloud_processing","mesh_to_pointcloud", file_id, {})`
- **Gotcha:** Errors (`Mesh is empty`, exit 1) if the input has no triangles — i.e. you fed it a point cloud. A low-poly mesh gives a sparse, irregular cloud (vertices cluster at detail). Only method in this skill that **requires a mesh**.

---

# 2. point_cloud_segmentation  (order 8, category "segmentation")

Geometric segmentation. Input `.ply .pcd .txt .xyz`. Both methods **recolor** (geometry unchanged).

## ransac_plane
- **Purpose:** `pcd.segment_plane(distance_threshold, ransac_n=3, num_iterations)` — RANSAC fits the dominant plane `ax+by+cz+d=0`. Script paints **inliers RED [1,0,0]**, **outliers BLUE [0,0.4,1]**, and writes `inlier + outlier` combined. The plane equation is logged, not returned as a sidecar.
- **Input geom:** pointcloud · **Output:** recolored `.ply` (red plane + blue rest).

| param | meaning | type | default | range | effect |
|---|---|---|---|---|---|
| `distance_threshold` | max point→plane distance for an inlier (data units) | float | 0.01 | 0.001–0.1 | ≈ noise level / flatness tolerance; larger captures a thicker slab |
| `num_iterations` | RANSAC trials | int | 1000 | 100–10000 | more = more robust on noisy/cluttered scenes, slower |

- **Note:** `ransac_n=3` (minimal plane sample) is hardcoded.
- **Log:** plane equation, normal, `Inliers/Outliers`, `Inlier ratio %`.
- **Example:** `run_job("point_cloud_segmentation","ransac_plane", file_id, {"distance_threshold":0.01,"num_iterations":1000})`
- **Gotcha:** Returns only **one** plane per call. To peel floor then walls, re-run on the blue-outlier output repeatedly. `distance_threshold` too large merges multiple surfaces into "the plane".

## dbscan_clustering
- **Purpose:** `pcd.cluster_dbscan(eps, min_points)` — density clustering. A point is core if it has ≥ `min_points` neighbors within `eps`. Script assigns each of the N clusters a **random color (seed=42)**; **noise (label −1) → dark gray [0.3,0.3,0.3]**.
- **Input geom:** pointcloud · **Output:** recolored-by-cluster `.ply`.

| param | meaning | type | default | range | effect |
|---|---|---|---|---|---|
| `eps` | max neighbor distance within a cluster (data units) | float | 0.02 | 0.001–0.5 | too small → everything is noise; too large → one mega-cluster |
| `min_points` | min points to seed a cluster | int | 10 | 3–100 | higher = stricter, more points become noise |

- **Log:** `Found C clusters, K noise points`, `Noise ratio %`, per-cluster point counts.
- **Example:** `run_job("point_cloud_segmentation","dbscan_clustering", file_id, {"eps":0.02,"min_points":10})`
- **Gotcha:** `eps` ≈ a few × point spacing. **Downsample first** (voxel) for speed and stable clusters — DBSCAN is O(n) KD-tree queries and slow on raw LiDAR. Some unclustered (gray, −1) points are normal.

---

# 3. features_extraction  (order 12, category "features")

Geometric descriptors. Input `.ply .pcd .txt .xyz`. All three **recolor** the cloud so the feature is visible; `fpfh_features` also **downsamples** (changes geometry).

## normal_estimation
- **Purpose:** `estimate_normals(KDTreeSearchParamHybrid(radius, max_nn))` then `orient_normals_consistent_tangent_plane(k=min(max_nn,15))`. Writes per-point **normals**, and colors the cloud by **|normal| mapped to RGB** (`colors = abs(normals)`).
- **Input geom:** pointcloud · **Output:** `.ply` with normals + direction-coloring.

| param | meaning | type | default | range | effect |
|---|---|---|---|---|---|
| `radius` | hybrid-search radius (data units) | float | 0.05 | 0.005–0.5 | larger = smoother normals, less detail |
| `max_nn` | max neighbors per estimate | int | 30 | 10–100 | caps cost; also caps orientation k at 15 |

- **Example:** `run_job("features_extraction","normal_estimation", file_id, {"radius":0.05,"max_nn":30})`
- **Gotcha:** `radius` must exceed point spacing but stay below feature size. Output **has normals** — run this before anything needing normals (FPFH, point-to-plane ICP, Poisson). Consistent-tangent-plane orientation can flip on thin/double-sided surfaces.

## fpfh_features
- **Purpose:** Downsample at `voxel_size` → estimate normals (`radius = voxel_size*2`, max_nn 30) → `compute_fpfh_feature` (`radius = voxel_size*5`, max_nn 100) → 33-D histograms. Script then **PCA-projects the 33-D FPFH to 3-D**, normalizes each axis to [0,1], and uses that as RGB so feature-similar regions share color.
- **Input geom:** pointcloud · **Output:** **downsampled** `.ply` colored by FPFH-PCA.

| param | meaning | type | default | range | effect |
|---|---|---|---|---|---|
| `voxel_size` | downsample size; also drives normal/feature radii (×2, ×5) | float | 0.005 | 0.001–0.05 | the single knob — set to your data scale |

- **Log:** down count, feature shape `(N,33)`, `PCA variance explained by top 3 %`.
- **Example:** `run_job("features_extraction","fpfh_features", file_id, {"voxel_size":0.005})`
- **Gotcha:** Output point count ≠ input (it downsamples). `voxel_size` is the only scale control — too small on big data = slow/huge; too large = washed-out features. The PCA coloring is **for visualization**, not the raw 33-D descriptor (no descriptor sidecar is emitted).

## curvature_estimation
- **Purpose:** For each point, hybrid KNN (`radius`, `max_nn`), local covariance, eigenvalues sorted; curvature `κ = λ0 / (λ0+λ1+λ2)` (0 = flat, →1/3 = sharp). Normalized to the **99th percentile** and colored with the matplotlib **`hot`** colormap. Pure-Python per-point loop.
- **Input geom:** pointcloud · **Output:** `.ply` colored by curvature (geometry unchanged).

| param | meaning | type | default | range | effect |
|---|---|---|---|---|---|
| `radius` | neighbor-search radius (data units) | float | 0.05 | 0.005–0.5 | larger = smoother/global curvature |
| `max_nn` | max neighbors per point | int | 30 | 10–100 | caps cost per point |

- **Log:** curvature min/max, mean, 99th percentile.
- **Example:** `run_job("features_extraction","curvature_estimation", file_id, {"radius":0.05,"max_nn":30})`
- **Gotcha:** Python loop over every point → **slow on large clouds; downsample first.** Points with <3 neighbors get curvature 0. Output encodes curvature as **color only** (hot ramp), geometry is identical to input.

---

# 4. stereo_3d_reconstruction  (order 9, category "stereo")

Depth/Z analysis. Input `.ply .pcd .txt .xyz`. Both **recolor**; `depth_filter` also crops.

## depth_colorization
- **Purpose:** Reads the **Z coordinate** of each point (NOT Euclidean distance — `module.json` theory says distance-from-origin, the script uses `points[:,2]`), normalizes Z to [0,1], applies a matplotlib colormap.
- **Input geom:** pointcloud · **Output:** Z-colored `.ply` (geometry unchanged).

| param | meaning | type | default | range | colormap |
|---|---|---|---|---|---|
| `colormap` | palette index | int | 0 | 0–3 | 0=jet, 1=viridis, 2=plasma, 3=turbo |

- **Example:** `run_job("stereo_3d_reconstruction","depth_colorization", file_id, {"colormap":0})`
- **Gotcha:** Colors by **Z**, so it only reads as "depth" if the camera/sensor axis is Z. Out-of-range `colormap` is clamped to the last entry (turbo).

## depth_filter
- **Purpose:** Keeps points whose **Z** lies between two **percentiles** of the Z distribution, then recolors survivors with `viridis`. Robust to scale because it's percentile-based.
- **Input geom:** pointcloud · **Output:** cropped + viridis-colored `.ply`.

| param | meaning | type | script default | module.json default | effect |
|---|---|---|---|---|---|
| `min_depth` | **lower Z percentile, as a fraction 0–1** (×100 internally) | float | 0.1 | 0.0 | raise to drop the nearest slab |
| `max_depth` | **upper Z percentile, as a fraction 0–1** | float | 0.9 | 80.0 | lower to drop the far background |

- **CRITICAL discrepancy:** the **script** treats these as fractions in `[0,1]` (`np.percentile(z, value*100)`). The **`module.json` defaults are `0.0` and `80.0`** with range 0–100. Passing `max_depth=80.0` → `percentile(z, 8000)`, which NumPy clamps to the max → no far clipping. **Pass fractions** (e.g. `min_depth=0.1, max_depth=0.9`) to match the script's intent. Always read `logs_tail` (`Depth range: [..]`, `Kept N/M`) to confirm.
- **Example (correct, script semantics):** `run_job("stereo_3d_reconstruction","depth_filter", file_id, {"min_depth":0.1,"max_depth":0.9})`
- **Gotcha:** `min_depth ≥ max_depth` → empty output. These are **percentiles, not metric depths**, despite the meter-flavored `module.json` description.

---

# 5. lidar_scene_detection  (order 10, category "lidar")

Automotive/robotics LiDAR. Input `.ply .pcd .txt .xyz .las`. All recolor; ground/cluster also crop.

## height_colorization
- **Purpose:** Normalizes **Z (height)** to [0,1]. `colormap=0` is a **custom blue→cyan→green→yellow→red gradient** (built by hand, not matplotlib); `colormap` 1/2/3 = viridis/plasma/turbo.
- **Input geom:** pointcloud · **Output:** height-colored `.ply` (geometry unchanged).

| param | meaning | type | default | range | colormap |
|---|---|---|---|---|---|
| `colormap` | palette | int | 0 | 0–3 | 0=custom height gradient, 1=viridis, 2=plasma, 3=turbo |

- **Example:** `run_job("lidar_scene_detection","height_colorization", file_id, {"colormap":0})`
- **Gotcha:** Unknown index ≥4 falls back to viridis. Assumes **Z is up**.

## ground_removal
- **Purpose:** RANSAC plane (`distance_threshold`, `ransac_n=3`, **`num_iterations=1000` hardcoded**), then **keeps the outliers** (`select_by_index(inliers, invert=True)`) = non-ground. Recolors survivors by height (R=z_norm, G=0.5, B=1−z_norm).
- **Input geom:** pointcloud · **Output:** ground-stripped `.ply`.

| param | meaning | type | default | range | effect |
|---|---|---|---|---|---|
| `distance_threshold` | ground-plane inlier band (meters) | float | 0.3 | 0.01–2.0 | larger eats more of the ground (and low objects); smaller leaves ground texture |

- **Log:** fitted plane eq, ground inlier count, remaining points.
- **Example:** `run_job("lidar_scene_detection","ground_removal", file_id, {"distance_threshold":0.3})`
- **Gotcha:** Removes only the **single dominant plane**. On sloped/multi-level ground it may keep some ground. Defaults are **meters** — wrong scale silently removes nothing or everything. Cannot change iteration count via params.

## object_clustering
- **Purpose:** Two-step: (1) RANSAC ground removal at `ground_threshold` (`num_iterations=1000` hardcoded), (2) `cluster_dbscan(cluster_eps, min_cluster_points)` on the non-ground points. Each object cluster gets a **random bright color (seed=42, brightened ×0.7+0.3)**; **noise → gray [0.3,0.3,0.3]**.
- **Input geom:** pointcloud · **Output:** non-ground, cluster-colored `.ply`.

| param | meaning | type | default | range | effect |
|---|---|---|---|---|---|
| `ground_threshold` | ground-plane inlier band before clustering (m) | float | 0.3 | 0.01–2.0 | same role as ground_removal's threshold |
| `cluster_eps` | DBSCAN neighbor distance (m) | float | 0.5 | 0.1–5.0 | larger merges nearby objects |
| `min_cluster_points` | min points per object | int | 10 | 3–100 | higher drops small/distant objects to noise |

- **Edge case:** if no non-ground points remain, it writes the **original cloud** and exits 0 (not an error) — check `logs_tail`.
- **Example:** `run_job("lidar_scene_detection","object_clustering", file_id, {"ground_threshold":0.3,"cluster_eps":0.5,"min_cluster_points":10})`
- **Gotcha:** `cluster_eps` (0.5 m) is automotive-scale, **much larger** than the segmentation module's `dbscan_clustering` eps (0.02). Don't copy unit-scale eps here. Slow on raw scans — downsample first.

---

# 6. lidar_camera_fusion  (order 11, category "lidar")

Sensor-fusion-flavored ops. Input `.ply .pcd .txt .xyz .las`. All recolor; ROI crops; multi-res stacks copies.

## intensity_colorization
- **Purpose:** Despite the name, colors by **Euclidean distance from origin** `‖p‖` (no intensity channel is read). `colormap=0` = custom **close=warm / far=cool** (R=1−d, G=0.3, B=d); 1=viridis, 2=plasma.
- **Input geom:** pointcloud · **Output:** distance-colored `.ply` (geometry unchanged).

| param | meaning | type | default | script colormap | module.json claim |
|---|---|---|---|---|---|
| `colormap` | palette | int | 0 | 0=custom warm/cool, 1=viridis, **2=plasma** | json says "2=inferno, 3=coolwarm" — **wrong; script handles only 0/1/2, ≥3 → viridis** |

- **Example:** `run_job("lidar_camera_fusion","intensity_colorization", file_id, {"colormap":0})`
- **Gotcha:** It's **distance-from-sensor**, not reflectance intensity. Trust the script table, not the `module.json` colormap legend.

## roi_extraction
- **Purpose:** Crops an axis-aligned box centered on the **median** point. Half-extent per axis = `extent * range_factor / 2`, where `extent = max−min` of the cloud. Crops via `AxisAlignedBoundingBox`, then recolors survivors with `coolwarm` by distance from center.
- **Input geom:** pointcloud · **Output:** cropped + coolwarm `.ply`.

| param | meaning | type | script default | module.json default | effect |
|---|---|---|---|---|---|
| `x_range` | **fraction 0–1** of X extent to keep (centered on median) | float | 0.5 | 50.0 | 0.5 keeps the middle 50% of X |
| `y_range` | fraction 0–1 of Y extent | float | 0.5 | 50.0 | |
| `z_range` | fraction 0–1 of Z extent | float | 0.8 | 50.0 | |

- **CRITICAL discrepancy:** the **script** expects **factors in [0,1]** (`half_extent = extent * range / 2`). The **`module.json` declares defaults of 50** with range 1–100 and "% of range" wording. If the MCP passes `50`, the half-extent becomes `extent*50/2 = 25×extent` → the box covers everything and **nothing is cropped**. **Pass fractions** like `{"x_range":0.5,"y_range":0.5,"z_range":0.8}` to actually crop. Confirm via `logs_tail` (`Extracted N/M points`).
- **Example (correct):** `run_job("lidar_camera_fusion","roi_extraction", file_id, {"x_range":0.5,"y_range":0.5,"z_range":0.8})`
- **Gotcha:** Box is centered on the **median**, not the centroid or origin — asymmetric clouds crop off-center. Factor ≥ ~2 keeps everything.

## multi_resolution
- **Purpose:** Builds a side-by-side **level-of-detail strip**: for `level` in `0..levels-1`, downsample at `base_voxel_size * 2**level`, paint a fixed level color (blue→green→red→yellow→magenta), **translate each level along +X** by `bbox_x*1.2*level`, and concatenate. Output is one cloud containing all levels laid out in a row.
- **Input geom:** pointcloud · **Output:** combined multi-level `.ply` (larger spatial footprint than input).

| param | meaning | type | script default | range | effect |
|---|---|---|---|---|---|
| `levels` | number of resolution copies | int | 3 | (1–5 colors defined) | more = longer X-strip |
| `base_voxel_size` | finest voxel; level k uses `×2**k` | float | 0.01 | — | scale to your data |

- **CRITICAL discrepancy:** the **script's real args are `--levels` and `--base_voxel_size`.** The **`module.json` declares `near_voxel` (0.01) and `far_voxel` (0.05)** — **those names do not exist in the script** and would be ignored (argparse uses defaults; unknown `--near_voxel` would in fact error). **Pass `{"levels":3,"base_voxel_size":0.01}`** (or `{}` for defaults), NOT `near_voxel`/`far_voxel`.
- **Example (correct):** `run_job("lidar_camera_fusion","multi_resolution", file_id, {"levels":3,"base_voxel_size":0.01})`
- **Gotcha:** This is a **visualization layout** (copies offset in X), not a single adaptive-resolution cloud. The output bbox is much wider than the input. Beyond 5 levels the color list repeats its last entry.

---

# 7. pyvista_pointcloud_processing  (order 15, category "processing")

PyVista/VTK filters via `pv.read`. Input `.ply .pcd .vtk .vtu .obj .stl`. Every script
forces the result to `PolyData` (via `extract_surface` when needed) before saving `.ply`.
These operate on **scalar arrays** and **coordinates**, not RGB.

## pv_threshold
- **Purpose:** `ds.threshold(value=[lower,upper], scalars=...)` — keeps cells whose scalar is in `[lower,upper]`. If `scalars=""` uses the active scalar. If the dataset has **no** point/cell scalars at all, the script first computes `compute_implicit_distance(pv.Plane())` and thresholds **`implicit_distance`**. Result is surface-extracted to PolyData.
- **Input geom:** any (mesh/cloud/grid) · **Output:** thresholded `.ply`.

| param | meaning | type | default | notes |
|---|---|---|---|---|
| `lower` | lower scalar bound | float | 0.0 | data-dependent — check the scalar's real min/max |
| `upper` | upper scalar bound | float | 1.0 | |
| `scalars` | scalar array name (`""` = active) | string | "" | named field must exist or exit 1 (logs available arrays) |

- **Example:** `run_job("pyvista_pointcloud_processing","pv_threshold", file_id, {"lower":0.0,"upper":1.0,"scalars":"elevation"})`
- **Gotcha:** Bounds are in the **scalar's** units, not coordinates. Defaults [0,1] rarely match real data → empty/full result; inspect the field first. Wrong `scalars` name → error (exit 1) with the available names in the log.

## pv_clip_plane
- **Purpose:** `ds.clip(normal, origin)` — removes everything on the **negative** side of the plane through `origin` with `normal`; keeps the +normal half-space.
- **Input geom:** any · **Output:** clipped `.ply`.

| param | meaning | type | default |
|---|---|---|---|
| `origin_x / origin_y / origin_z` | plane point | float | 0,0,0 |
| `normal_x / normal_y / normal_z` | plane normal | float | 1,0,0 |

- **Example:** `run_job("pyvista_pointcloud_processing","pv_clip_plane", file_id, {"origin_x":0,"origin_y":0,"origin_z":0,"normal_x":0,"normal_y":0,"normal_z":1})`
- **Gotcha:** Default origin (0,0,0) may sit outside the data → clips everything or nothing. Set `origin` to a real interior coordinate (e.g. the bbox center). Keeps the half-space the normal **points into**.

## pv_clip_box
- **Purpose:** `ds.clip_box(bounds, invert=False)` — keeps geometry **inside** the AABB `[x_min,x_max]×[y_min,y_max]×[z_min,z_max]` (invert=False = keep interior).
- **Input geom:** any · **Output:** cropped `.ply`.

| param | meaning | type | default |
|---|---|---|---|
| `x_min / x_max` | X bounds | float | −0.5 / 0.5 |
| `y_min / y_max` | Y bounds | float | −0.5 / 0.5 |
| `z_min / z_max` | Z bounds | float | −0.5 / 0.5 |

- **Example:** `run_job("pyvista_pointcloud_processing","pv_clip_box", file_id, {"x_min":-0.2,"x_max":0.2,"y_min":-0.2,"y_max":0.2,"z_min":-0.2,"z_max":0.2})`
- **Gotcha:** Default ±0.5 box assumes unit-scale, centered data → real-coordinate data comes back empty. Set bounds from the actual extents (use `get_volume_info` / inspect the model first). Keeps **inside** (opposite of a plane clip's half-space).

## pv_random_sample
- **Purpose:** Uniform random subsample **without replacement**: keep `max(1, int(n*fraction))` points via `np.random.choice`, indices sorted, `extract_points`. Output count is deterministic in size, random in selection (no fixed seed).
- **Input geom:** any (auto `extract_surface` to PolyData first) · **Output:** sampled `.ply`.

| param | meaning | type | default | range |
|---|---|---|---|---|
| `fraction` | fraction of points to keep | float | 0.5 | 0.01–1.0 |

- **Example:** `run_job("pyvista_pointcloud_processing","pv_random_sample", file_id, {"fraction":0.5})`
- **Gotcha:** No seed → not reproducible run-to-run. Unlike `voxel_downsample` it does **not** give uniform spatial density (pure random), and it keeps original points (no centroid averaging). `fraction=1.0` keeps all.

## pv_extract_points
- **Purpose:** Selects points whose scalar is in `[lower,upper]` (`mask`, `extract_points`). `scalars=""` → active scalars. If no name given **and** the dataset has no point_data, the script adds **`elevation` = Z coordinate** and filters on that.
- **Input geom:** any (auto PolyData) · **Output:** point subset `.ply`.

| param | meaning | type | default | notes |
|---|---|---|---|---|
| `scalars` | scalar array name (`""` = active, or auto `elevation`=Z) | string | "" | named field must exist in point_data or exit 1 |
| `lower` | lower bound | float | 0.0 | scalar units |
| `upper` | upper bound | float | 1.0 | scalar units |

- **Log:** `Scalar range in data: min=.. max=..` (use it to pick bounds), then matched/total count.
- **Example:** `run_job("pyvista_pointcloud_processing","pv_extract_points", file_id, {"scalars":"","lower":0.0,"upper":1.0})`
- **Gotcha:** With no scalars it filters on **Z (`elevation`)** — defaults [0,1] then mean "keep points with 0 ≤ Z ≤ 1", which may be empty for real-coordinate data. Read the logged scalar range first. Difference vs `pv_threshold`: extract_points works on **point** data and returns a point cloud; threshold works on cells.

---

## Cross-cutting discrepancy summary (script vs module.json)
| method | module.json says | script actually does | what to pass |
|---|---|---|---|
| `depth_filter` | `min_depth=0.0, max_depth=80.0` (0–100) | percentile **fractions 0–1** (×100) | `{"min_depth":0.1,"max_depth":0.9}` |
| `roi_extraction` | `x/y/z_range=50` (% 1–100) | **factors 0–1** (`extent*range/2`) | `{"x_range":0.5,"y_range":0.5,"z_range":0.8}` |
| `multi_resolution` | `near_voxel=0.01, far_voxel=0.05` | args are **`levels`, `base_voxel_size`** | `{"levels":3,"base_voxel_size":0.01}` |
| `intensity_colorization` | "2=inferno, 3=coolwarm" | 0=warm/cool, 1=viridis, **2=plasma**, ≥3→viridis | `{"colormap":0\|1\|2}` |
| `depth_colorization` | "distance from origin" | colors by **Z** | n/a |
| `intensity_colorization` | "intensity/reflectance" | distance from **origin** | n/a |

When in doubt, pass `params={}` to use the **script's** defaults (safe), then read `logs_tail`.
