# Mesh & Surfaces — Exhaustive Method Reference (ppline-3dcv)

Every method of the 8 mesh/surface modules, documented from the **actual scripts** in `modules/<id>/scripts/`. For the `run_job` call shape and return keys see **ppline-3dcv:mcp-tool-reference**; for the upload->run->view recipe see **ppline-3dcv:using-ppline**; for sample ids use `list_open3d_samples()`/`list_pyvista_samples()` (do not invent ids); for point-cloud prep (normal_estimation, downsampling) see **ppline-3dcv:pointcloud-ops**.

**`run_job` shape used throughout:** `run_job(module_id="...", method_id="...", file_id="<id>", params={...})`. Omitted params take the defaults below. Output is downloadable at the absolute `/api/files/...` URL in the result; `extra_outputs` is empty for these modules (none emit sidecars).

Conventions in the tables: **type** is the CLI/argparse type; **default/min/max** are from `module.json`; **effect** + **internal behavior** are read from the script source.

---

## 1. `mesh_processing` (Open3D) — order 2, category processing

Input formats `.ply .obj .stl .off`. All read via `o3d.io.read_triangle_mesh`. Mesh-empty -> exit 1.

### `subdivision` — Loop subdivision
- **Purpose:** increase mesh resolution + smooth, via Open3D `mesh.subdivide_loop(number_of_iterations)`. (Loop, NOT midpoint — it interpolates/rounds.)
- **Input:** triangle mesh (must have triangles). **Output:** mesh `.ply` (vertex normals recomputed).
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| iterations | int | 1 | 1 | 4 | Loop iterations. Face count ≈ ×4 per iteration. |

- **Gotchas:** Loop smooths sharp features. `iterations=3-4` on a large mesh = memory blow-up (×64–×256 faces). No-op contract on point clouds — a points-only file has 0 triangles and `subdivide_loop` returns empty.
- **Example:** `run_job("mesh_processing","subdivision","<mesh_id>",{"iterations":2})`

### `simplification` — Quadric decimation (QEM)
- **Purpose:** reduce triangle count via `mesh.simplify_quadric_decimation(target_number_of_triangles)`. Logs achieved reduction %.
- **Input:** triangle mesh. **Output:** mesh `.ply` (vertex normals recomputed).
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| target_triangles | int | 5000 | 100 | 100000 | **Absolute KEEP count** of triangles (not a fraction). |

- **Gotchas:** This is the absolute target count — contrast with `pv_decimate` whose param is the fraction removed. If `target_triangles` ≥ current count it's a near no-op. QEM can produce non-manifold/degenerate triangles on bad input.
- **Example:** `run_job("mesh_processing","simplification","<mesh_id>",{"target_triangles":2000})`

### `mesh_to_pcd_uniform` — Uniform surface sampling
- **Purpose:** sample points uniformly over the mesh surface (area-weighted), `mesh.sample_points_uniformly(number_of_points)`.
- **Input:** mesh. **If the file has 0 triangles, the script builds a convex hull first** and samples that. **Output:** **point cloud** `.ply` (no normals).
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| num_points | int | 5000 | 100 | 100000 | Exact number of points sampled. |

- **Gotchas:** Output is a point cloud, not a mesh. Random sampling -> not blue-noise (clusters/gaps). Convex-hull fallback means feeding a point cloud gives points only on the hull surface — for clean resampling use `point_cloud_processing.mesh_to_pointcloud` (see pointcloud-ops) on an actual mesh.
- **Example:** `run_job("mesh_processing","mesh_to_pcd_uniform","<mesh_id>",{"num_points":20000})`

### `mesh_to_pcd_poisson_disk` — Poisson-disk (blue-noise) sampling
- **Purpose:** evenly spaced samples (no two closer than a min distance), `mesh.sample_points_poisson_disk(number_of_points)`.
- **Input:** mesh (0-triangle file -> convex hull fallback, same as above). **Output:** **point cloud** `.ply`.
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| num_points | int | 5000 | 100 | 100000 | **Approximate** target (Poisson-disk yields near, not exact). |

- **Gotchas:** Much slower than uniform (internally oversamples then prunes). Best when you need even coverage for downstream reconstruction (ball pivoting likes uniform density).
- **Example:** `run_job("mesh_processing","mesh_to_pcd_poisson_disk","<mesh_id>",{"num_points":8000})`

---

## 2. `pyvista_mesh_processing` (PyVista/VTK) — order 14, category processing

Input `.ply .obj .stl .vtk .vtu`. Every script: `pv.read`, and if not `PolyData` it calls `extract_surface()` first. `n_cells==0` -> exit 1 (except triangulate/extract_surface).

### `pv_decimate` — Quadric decimation
- **Purpose:** `mesh.decimate(target_reduction)` (VTK quadric error metrics).
- **Input:** mesh. **Output:** mesh `.ply`.
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| target_reduction | float | 0.5 | 0.01 | 0.99 | **Fraction REMOVED.** 0.5 removes ~50% (keeps 50%); 0.9 keeps only ~10%. |

- **Gotchas:** Opposite meaning from `simplification.target_triangles`. Can create non-manifold edges (VTK default does not preserve topology). High reduction destroys thin features.
- **Example:** `run_job("pyvista_mesh_processing","pv_decimate","<mesh_id>",{"target_reduction":0.7})`

### `pv_subdivide` — Subdivision (linear/butterfly/loop)
- **Purpose:** `mesh.subdivide(n_subdivisions, subfilter=algorithm)`.
- **Input:** mesh (must be all-triangles for VTK subdivision; run `pv_triangulate` first if it has quads/n-gons). **Output:** mesh `.ply`.
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| n_subdivisions | int | 1 | 1 | 4 | Iterations; faces ≈ ×4 each. |
| algorithm | string | linear | — | — | `linear` (midpoint, no smoothing), `butterfly` (interpolating/smooth, passes through originals), `loop` (approximating/smooth). |

- **Gotchas:** Non-triangle input fails — triangulate first. `loop`/`butterfly` smooth; `linear` only densifies. `n_subdivisions=4` = ×256 faces.
- **Example:** `run_job("pyvista_mesh_processing","pv_subdivide","<mesh_id>",{"n_subdivisions":2,"algorithm":"butterfly"})`

### `pv_smooth_laplacian` — Laplacian smoothing
- **Purpose:** `mesh.smooth(n_iter, relaxation_factor)` — move each vertex toward neighbor centroid.
- **Input:** mesh. **Output:** mesh `.ply`.
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| n_iterations | int | 20 | 1 | 500 | More iterations = smoother. |
| relaxation_factor | float | 0.01 | 0.001 | 1.0 | Step size; higher = stronger per-iteration smoothing. |

- **Gotchas:** **Shrinks volume** (objects pull inward). For closed/organic shapes prefer Taubin. High `relaxation_factor` + many iterations can collapse thin parts.
- **Example:** `run_job("pyvista_mesh_processing","pv_smooth_laplacian","<mesh_id>",{"n_iterations":50,"relaxation_factor":0.05})`

### `pv_smooth_taubin` — Taubin smoothing (volume-preserving)
- **Purpose:** `mesh.smooth_taubin(n_iter, pass_band)` — alternating λ/μ steps; no net shrinkage.
- **Input:** mesh. **Output:** mesh `.ply`.
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| n_iterations | int | 20 | 1 | 500 | More = smoother. |
| pass_band | float | 0.1 | 0.001 | 2.0 | Cutoff frequency. **Lower = smoother** (passes fewer high frequencies). |

- **Gotchas:** Preferred over Laplacian for shape preservation. `pass_band` semantics are inverse-intuitive (smaller smooths more).
- **Example:** `run_job("pyvista_mesh_processing","pv_smooth_taubin","<mesh_id>",{"n_iterations":40,"pass_band":0.05})`

### `pv_clean` — Merge duplicates / remove degenerates
- **Purpose:** `mesh.clean(tolerance=...)` (or `mesh.clean()` when tolerance==0) — merge coincident points, drop degenerate cells, strip unused points.
- **Input:** mesh. **Output:** mesh `.ply`.
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| tolerance | float | 0.0 | 0.0 | 1.0 | Merge tolerance. 0 = exact duplicates only. >0 merges within distance. |

- **Gotchas:** `tolerance` is in **mesh units** (often a fraction of bbox in VTK) — a large value collapses distinct vertices and wrecks geometry. Run `pv_clean` before boolean ops / reconstruction. STL especially benefits (3 dup vertices per face).
- **Example:** `run_job("pyvista_mesh_processing","pv_clean","<mesh_id>",{"tolerance":0.0})`

### `pv_fill_holes` — Fill boundary holes
- **Purpose:** `mesh.fill_holes(hole_size)` — triangulate boundary loops up to a size.
- **Input:** mesh with boundary holes. **Output:** mesh `.ply`.
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| hole_size | float | 100.0 | 1.0 | 10000.0 | Max hole "size" (VTK radius-like, mesh units) to fill. |

- **Gotchas:** `hole_size` is a **size threshold in mesh units, not a hole count**; loops larger than it stay open. VTK's filler may bridge unintended gaps or produce non-planar fills. Default 100 assumes large-coordinate meshes — scale down for unit-scale data.
- **Example:** `run_job("pyvista_mesh_processing","pv_fill_holes","<mesh_id>",{"hole_size":10.0})`

### `pv_compute_normals` — Point + cell normals
- **Purpose:** `mesh.compute_normals(cell_normals=True, point_normals=True, flip_normals, consistent_normals)`. Stores a `Normals` array in point_data and cell_data.
- **Input:** mesh. **Output:** mesh `.ply` with `Normals`.
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| flip_normals | int(0/1) | 0 | 0 | 1 | 1 = flip all normals. |
| consistency | int(0/1) | 1 | 0 | 1 | 1 = enforce consistent outward orientation. |

- **Gotchas:** Prereq for `pv_glyph`/`pv_vector_magnitude` with `vector_name="Normals"`. Consistency can still fail on non-manifold/open meshes. Flipping is global, not selective.
- **Example:** `run_job("pyvista_mesh_processing","pv_compute_normals","<mesh_id>",{"flip_normals":0,"consistency":1})`

### `pv_triangulate` — Polygons -> triangles
- **Purpose:** `mesh.triangulate()` — convert quads/n-gons to triangles. **No params.**
- **Input:** mesh (any poly). **Output:** all-triangle mesh `.ply`.
- **Gotchas:** Run before subdivision/decimation/boolean ops that assume triangles.
- **Example:** `run_job("pyvista_mesh_processing","pv_triangulate","<mesh_id>",{})`

### `pv_extract_surface` — Outer surface of a grid
- **Purpose:** `ds.extract_surface()` — boundary polygonal surface of a volumetric/unstructured dataset. **No params.**
- **Input:** a **volume/UnstructuredGrid** (`.vtu`/`.vtk`/`.vti`). **Output:** surface mesh `.ply`.
- **Gotchas:** **No-op on a plain PolyData surface.** For a volume's outer boundary `pv_extract_geometry` (volume module) is the natural sibling.
- **Example:** `run_job("pyvista_mesh_processing","pv_extract_surface","<grid_id>",{})`

---

## 3. `point_cloud_reconstruction` (Open3D) — order 5, category reconstruction

Input `.ply .pcd .txt .xyz` read via `o3d.io.read_point_cloud`. Empty -> exit 1. **Output is always a triangle mesh `.ply`.**

### `poisson` — Poisson surface reconstruction
- **Purpose:** `o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth, scale)` -> watertight mesh.
- **Input:** point cloud. **Normals:** if absent the script **estimates them** (`KDTreeSearchParamHybrid(radius=0.1, max_nn=30)`) and **orients** them (`orient_normals_consistent_tangent_plane(k=15)`). If present, kept as-is.
- **Post-process:** removes vertices below the **1st-percentile density** (noise/balloon trim).
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| depth | int | 9 | 4 | 13 | Octree depth. Higher = finer detail, slower, more memory. |
| scale | float | 1.1 | 0.5 | 2.0 | Reconstruction cube size vs samples bbox (padding factor). |

- **Gotchas:** The internal **radius=0.1 normal estimate assumes ~unit-scale data** — wrong scale -> bad normals -> blobs/inverted surface. For real control run `features_extraction.normal_estimation` first with a scale-appropriate radius. Poisson can still extend a smooth surface beyond the cloud (the 1% trim only removes the lowest-density tail). `depth=13` is very heavy.
- **Example:** `run_job("point_cloud_reconstruction","poisson","<pcd_id>",{"depth":9,"scale":1.1})`

### `convex_hull` — Convex hull
- **Purpose:** `pcd.compute_convex_hull()` — smallest convex polytope. **No params, no normals.**
- **Input:** point cloud. **Output:** convex mesh `.ply`.
- **Gotchas:** Discards all concavities. Use as a bounding/visualization fallback, never for detail.
- **Example:** `run_job("point_cloud_reconstruction","convex_hull","<pcd_id>",{})`

### `alpha_shape` — Alpha shape
- **Purpose:** `create_from_point_cloud_alpha_shape(pcd, alpha, tetra_mesh, pt_map)` (pre-builds a TetraMesh for efficiency). **No normals needed.**
- **Auto-retry:** if the result is empty, retries with `alpha = bbox_diagonal × {0.1, 0.25, 0.5, 1.0}` until non-empty; if all fail -> exit 1.
- **Input:** point cloud. **Output:** mesh `.ply` (vertex normals computed).
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| alpha | float | 0.03 | 0.005 | 0.5 | Scale. Smaller = tighter/more detail (risk: holes/fragments). Larger = smoother toward convex hull. |

- **Gotchas:** Highly scale-sensitive — `alpha` is an absolute distance in cloud units; the 0.03 default suits ~unit-scale clouds. Can yield non-manifold edges, holes, disconnected pieces. Build the tetra mesh once is expensive for huge clouds (downsample first).
- **Example:** `run_job("point_cloud_reconstruction","alpha_shape","<pcd_id>",{"alpha":0.02})`

### `ball_pivoting` — Ball pivoting (BPA)
- **Purpose:** `create_from_point_cloud_ball_pivoting(pcd, radii)` rolling a ball over the points.
- **Input:** point cloud. **Normals:** estimated+oriented internally if absent (same radius=0.1/max_nn=30/k=15 as Poisson).
- **Radii:** computed as `avg_nn_distance × radius_factor × {1, 2, 4}` (multi-scale).
- **Output:** mesh `.ply` (often NOT watertight).
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| radius_factor | float | 2.0 | 0.5 | 10.0 | Ball radius as a multiple of average point spacing. |

- **Gotchas:** Needs roughly **uniform density** (poisson-disk-sample a mesh first if needed). `radius_factor` too small -> missed triangles/holes; too large -> bridges across gaps. Leaves boundary holes — follow with `pv_fill_holes` or use Poisson if you need watertight.
- **Example:** `run_job("point_cloud_reconstruction","ball_pivoting","<pcd_id>",{"radius_factor":2.0})`

**Reconstruction chooser:** Poisson = dense clean scans, watertight. Ball pivoting = uniform clouds, preserves detail, not closed. Alpha shape = convex-ish/sparse, no normals. Convex hull = bounding box only.

---

## 4. `voxel_to_mesh` (Open3D + scipy + skimage) — order 3, category conversion

Input `.ply .obj .stl .off`.

### `voxelization` — Mesh -> voxel-center point cloud
- **Purpose:** build an Open3D `VoxelGrid` from the mesh (`create_from_triangle_mesh`; from point cloud via `create_from_point_cloud` if no triangles), then emit each **voxel center as a point**, height-colored (blue low -> red high on Z).
- **Input:** mesh (or point cloud). **Output:** **colored point cloud** `.ply` (NOT a voxel file, NOT a mesh).
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| voxel_size | float | 0.01 | 0.002 | 0.05 | Cube edge length. Smaller = finer grid, far more points. |

- **Gotchas:** Output is a point cloud of centers — to get a surface from voxels use `binary_erosion` or `sdf`. `voxel_size` below feature thickness drops thin parts. Cost grows ~cubically as `voxel_size` shrinks.
- **Example:** `run_job("voxel_to_mesh","voxelization","<mesh_id>",{"voxel_size":0.01})`

### `binary_erosion` — Occupancy erosion + marching cubes
- **Purpose:** build an **occupancy grid** via Open3D `RaycastingScene.compute_occupancy` over a padded bbox grid (padding fixed at **5×voxel_size**), apply scipy `binary_erosion` (6-connected `generate_binary_structure(3,1)`), then `skimage.measure.marching_cubes(level=0.5)` back to a mesh.
- **Input:** mesh (points-only -> convex hull). **Output:** eroded mesh `.ply`.
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| voxel_size | float | 0.01 | 0.002 | 0.05 | Grid resolution; cubic cost. |
| erosion_iterations | int | 1 | 1 | 5 | Voxel-layers removed from the boundary. |

- **Gotchas:** Occupancy needs a **watertight** mesh (ray-based inside test). `erosion_iterations` × `voxel_size` = physical shrink; too many erosions on a thin object erases it (empty marching cubes -> failure). Memory/time scale cubically with 1/`voxel_size`.
- **Example:** `run_job("voxel_to_mesh","binary_erosion","<mesh_id>",{"voxel_size":0.01,"erosion_iterations":2})`

---

## 5. `sdf` (Open3D RaycastingScene + skimage) — order 4, category implicit

Input `.ply .obj .stl .off`. All build a `RaycastingScene` from the mesh (points-only -> convex hull).

### `compute_sdf` — SDF grid + marching cubes
- **Purpose:** sample a signed distance field on a padded regular grid (`scene.compute_signed_distance`), then `marching_cubes(level=0.0)` -> reconstructed surface at the zero level set.
- **Input:** mesh (watertight for correct signs). **Output:** mesh `.ply`.
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| voxel_size | float | 0.01 | 0.002 | 0.05 | Grid step; **cubic** cost & memory. |
| padding | int | 5 | 1 | 20 | Padding voxels around bbox (room for the field). |

- **Gotchas:** Non-watertight/non-manifold -> wrong signs -> garbage surface. Grid size per axis = `(bbox_extent + 2·padding·voxel_size)/voxel_size`; halving `voxel_size` ~8× the work. This is the canonical SDF->mesh round-trip (smooths slightly).
- **Example:** `run_job("sdf","compute_sdf","<mesh_id>",{"voxel_size":0.01,"padding":5})`

### `occupancy_reconstruction` — Occupancy -> marching cubes
- **Purpose:** same padded grid but `scene.compute_occupancy` (inside=1/outside=0), then `marching_cubes(level=0.5)`.
- **Input:** mesh (watertight). **Output:** mesh `.ply`.
- **Params:** identical to `compute_sdf` (`voxel_size`=0.01 [0.002–0.05], `padding`=5 [1–20]).
- **Gotchas:** Occupancy is binary -> blockier/aliased surface than the SDF version; use `compute_sdf` for smoother results. Same watertight + cubic-cost caveats.
- **Example:** `run_job("sdf","occupancy_reconstruction","<mesh_id>",{"voxel_size":0.01,"padding":5})`

### `sdf_voxel_visualization` — TSDF near-surface point cloud
- **Purpose:** sample SDF on a `resolution^3` grid (padding = 15% of max extent), **keep only voxels with SDF in `[min_clamp, max_clamp]`** (a near-surface shell), color with **coolwarm** (blue interior / white surface / red exterior). This is a Truncated-SDF (TSDF) visualization.
- **Input:** mesh (points-only -> convex hull). **Output:** **colored point cloud** `.ply`.
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| resolution | int | 32 | 8 | 128 | Grid points per axis; **clamped to [8,128]** in code. Cost = resolution³. |
| min_clamp | float | -0.1 | -1.0 | 0.0 | Interior threshold; voxels with SDF below are dropped. |
| max_clamp | float | 0.1 | 0.0 | 1.0 | Exterior threshold; voxels with SDF above are dropped. |

- **Gotchas:** Output is a point cloud, not a mesh — purely for inspection. Clamp band too narrow -> nearly empty; too wide -> solid blob hiding the surface. `resolution=128` = 2M+ queries. Clamp values are absolute distances in mesh units (default ±0.1 suits unit-scale meshes).
- **Example:** `run_job("sdf","sdf_voxel_visualization","<mesh_id>",{"resolution":48,"min_clamp":-0.05,"max_clamp":0.05})`

---

## 6. `collision_detection` (Open3D RaycastingScene) — order 13, category collision

Input `.ply .obj .stl .off`. Both methods test the input against a **synthetic sphere obstacle**, NOT a second mesh. Points-only input -> convex hull. **Metrics are logged, not returned in the file.**

### `sdf_collision` — SDF-based collision (colored cloud)
- **Purpose:** sample `num_samples` points uniformly on the input surface; place a sphere of `obstacle_radius` overlapping the input along +X (overlap = `penetration_ratio × obstacle_radius`); compute each sample's SDF vs the sphere; color ALL samples by SDF (coolwarm: red=penetrating, blue=safe); append a yellow 5000-point sample of the obstacle.
- **Input:** mesh. **Output:** combined colored point cloud `.ply` (input samples + obstacle).
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| obstacle_radius | float | 0.5 | 0.1 | 5.0 | Radius of the synthetic sphere (sphere mesh resolution=50). |
| penetration_ratio | float | 0.3 | 0.05 | 0.8 | Fraction of `obstacle_radius` the sphere overlaps the input. |
| num_samples | int | 50000 | 5000 | 200000 | Surface samples for SDF eval. **Honored here.** |

- **Gotchas:** Not a two-mesh test — it's a controlled synthetic overlap demo/measurement. Sphere is placed at `center + [mesh_radius + R_obs − penetration, 0, 0]`, so it always grazes the +X side. Raise `num_samples` for thin parts. `obstacle_radius` should be comparable to your mesh scale to actually overlap.
- **Example:** `run_job("collision_detection","sdf_collision","<mesh_id>",{"obstacle_radius":0.5,"penetration_ratio":0.3,"num_samples":80000})`

### `penetration_depth` — Penetration depth measurement
- **Purpose:** same setup but overlap is an absolute `overlap_distance`; computes **max & mean penetration depth** and the **collision-region bounding box** (logged). Output cloud: penetrating points in a `hot` colormap by depth, non-penetrating points gray. If nothing penetrates, paints all green and notes "no collision".
- **Input:** mesh. **Output:** colored point cloud `.ply`. **Metrics go to the logs only** (no JSON sidecar).
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| obstacle_radius | float | 0.5 | 0.1 | 5.0 | Synthetic sphere radius. |
| overlap_distance | float | 0.15 | 0.01 | 2.0 | Absolute overlap distance (mesh units). |

- **Gotchas:** **`num_samples` is HARDCODED to 50000** here — there is no sample-count param. The numeric metrics (max_depth `|min(SDF)|`, mean_depth, collision bbox size) are only in the run logs; the artifact is the colored cloud. `overlap_distance` larger than `mesh_radius+R_obs` would place the sphere on the far side.
- **Example:** `run_job("collision_detection","penetration_depth","<mesh_id>",{"obstacle_radius":0.5,"overlap_distance":0.2})`

---

## 7. `pyvista_volume_processing` (PyVista/VTK) — order 16, category conversion

Input `.vti .vtk .vtu .ply .obj .stl`. `pv.read` auto-detects type.

### `pv_contour` — Isosurface contour (marching cubes)
- **Purpose:** extract `n_contours` evenly-spaced isosurfaces. The script: errors if no point/cell data; **converts cell data to point data** when needed; picks `scalars` (or active, or first array); computes `linspace(min, max, n_contours+2)[1:-1]` isovalues (strictly inside the range); `ds.contour(isosurfaces=..., scalars=...)`; result cast to `PolyData`.
- **Input:** dataset **with scalar data**. **Output:** surface `.ply`.
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| n_contours | int | 5 | 1 | 50 | Number of isosurface levels (interior of scalar range). |
| scalars | string | "" | — | — | Array name; empty = active/first available. |

- **Gotchas:** Needs scalars — a bare surface mesh with none -> exit 1. Cell-data scalars are auto-converted to point data. Endpoints (exact min/max) are excluded by design.
- **Example:** `run_job("pyvista_volume_processing","pv_contour","<volume_id>",{"n_contours":8,"scalars":""})`

### `pv_slice` — Single-plane slice
- **Purpose:** `ds.slice(normal, origin)`. If origin is exactly (0,0,0) it **defaults to the dataset center**. Result cast to PolyData.
- **Input:** any dataset. **Output:** slice `.ply`.
- **Params:**

| name | type | default | range | effect |
|---|---|---|---|---|
| normal_x | float | 1.0 | [-1,1] | Plane normal X. |
| normal_y | float | 0.0 | [-1,1] | Plane normal Y. |
| normal_z | float | 0.0 | [-1,1] | Plane normal Z. |
| origin_x | float | 0.0 | [-1e10,1e10] | X of plane origin (0,0,0 => center). |
| origin_y | float | 0.0 | [-1e10,1e10] | Y of plane origin. |
| origin_z | float | 0.0 | [-1e10,1e10] | Z of plane origin. |

- **Gotchas:** Default normal (1,0,0) cuts a YZ plane through the center. To slice off-center set a non-zero origin (all-zero is special-cased to center).
- **Example:** `run_job("pyvista_volume_processing","pv_slice","<volume_id>",{"normal_x":0,"normal_y":0,"normal_z":1})`

### `pv_slice_orthogonal` — Three orthogonal slices
- **Purpose:** `ds.slice_orthogonal(x,y,z)`; each position that is exactly 0 defaults to the dataset center on that axis. The resulting MultiBlock is merged into one PolyData.
- **Input:** any dataset. **Output:** merged slices `.ply`.
- **Params:**

| name | type | default | range | effect |
|---|---|---|---|---|
| x | float | 0.0 | [-1e10,1e10] | YZ-slice X position (0 => center). |
| y | float | 0.0 | [-1e10,1e10] | XZ-slice Y position (0 => center). |
| z | float | 0.0 | [-1e10,1e10] | XY-slice Z position (0 => center). |

- **Gotchas:** A value of exactly 0 is treated as "use center" — you cannot request a slice at true world-zero on an axis whose center isn't 0.
- **Example:** `run_job("pyvista_volume_processing","pv_slice_orthogonal","<volume_id>",{})`

### `pv_threshold_volume` — Threshold by scalar range
- **Purpose:** `ds.threshold(value=[lower, upper])` — keep cells with scalar in range, **preserving volumetric cells**. Output saved as **`.vtu`** (cast to UnstructuredGrid if needed).
- **Input:** dataset with scalar data. **Output:** `.vtu`.
- **Params:**

| name | type | default | range | effect |
|---|---|---|---|---|
| lower | float | 0.0 | [-1e10,1e10] | Lower scalar bound. |
| upper | float | 1.0 | [-1e10,1e10] | Upper scalar bound. |

- **Gotchas:** Defaults [0,1] only make sense for normalized data — **check your scalar's real min/max first** (e.g. via `pv_scalar_stats`) or you get an empty result. Output is `.vtu` (volumetric); feed to `pv_extract_geometry` for a surface.
- **Example:** `run_job("pyvista_volume_processing","pv_threshold_volume","<volume_id>",{"lower":100,"upper":300})`

### `pv_extract_geometry` — Boundary surface of a volume
- **Purpose:** `ds.extract_geometry()` -> outer polygonal boundary; cast to PolyData. **No params.**
- **Input:** volume/grid. **Output:** surface `.ply`.
- **Gotchas:** This is the right tool for "give me the surface of this volume" (vs `pv_extract_surface` in the mesh module, which is the analogous op but lives there).
- **Example:** `run_job("pyvista_volume_processing","pv_extract_geometry","<volume_id>",{})`

### `pv_extract_cells` — Select cells by type
- **Purpose:** keep only cells of one VTK type via `ds.extract_cells(indices)`. Output `.vtu`.
- **Input:** UnstructuredGrid with mixed cell types. **Output:** `.vtu`.
- **Params:**

| name | type | default | allowed | effect |
|---|---|---|---|---|
| cell_type | string | tetrahedral | tetrahedral, hexahedral, wedge, pyramid, triangle, quad | Which VTK cell type to keep. |

- **Gotchas:** Unknown `cell_type` -> exit 1 (lists valid options). **If no cells match it writes an EMPTY grid and exits 0** (silent empty result) — verify the dataset actually contains that cell type. The script logs the unique cell types present.
- **Example:** `run_job("pyvista_volume_processing","pv_extract_cells","<grid_id>",{"cell_type":"tetrahedral"})`

---

## 8. `pyvista_analysis` (PyVista/VTK) — order 17, category features

Input `.ply .obj .stl .vtk .vtu`. Non-PolyData auto `extract_surface()`'d. These ADD scalar/vector fields; geometry is unchanged (except `pv_glyph`, which builds arrow geometry).

### `pv_curvature` — Surface curvature
- **Purpose:** `mesh.curvature(curv_type)` -> per-vertex scalar stored as `curvature_<type>`. Logs min/max/mean.
- **Input:** mesh. **Output:** mesh `.ply` + `curvature_<type>` field.
- **Params:**

| name | type | default | allowed | effect |
|---|---|---|---|---|
| curvature_type | string | mean | mean, gaussian, maximum, minimum | mean H=(κ1+κ2)/2; gaussian K=κ1·κ2; maximum=κ1; minimum=κ2. |

- **Gotchas:** Invalid type -> exit 1. Result is a scalar field — colorize via `visualize_sample` to see it. Noisy/non-clean meshes give noisy curvature (clean first).
- **Example:** `run_job("pyvista_analysis","pv_curvature","<mesh_id>",{"curvature_type":"gaussian"})`

### `pv_distance` — Distance from center of mass
- **Purpose:** computes each vertex's Euclidean distance to the **mesh's own center of mass** (`np.linalg.norm(points - mesh.center)`), stores `distance_from_center`. **No params.**
- **Input:** a SINGLE mesh. **Output:** mesh `.ply` + `distance_from_center` field.
- **Gotchas:** **This is NOT a mesh-to-mesh distance / signed distance between two surfaces.** Despite the generic name it is a radial-distance-from-centroid scalar on one mesh. (Earlier docs incorrectly described it as dual-input — there is no second input.) For mesh-vs-mesh distance use the SDF tools or pointcloud ops.
- **Example:** `run_job("pyvista_analysis","pv_distance","<mesh_id>",{})`

### `pv_glyph` — Arrow glyphs from a vector field
- **Purpose:** `mesh.glyph(orient=vector_name, scale=False, factor=scale_factor)` -> arrow geometry oriented by the vectors (uniform size since `scale=False`). If `vector_name` is missing and equals `Normals`, computes point normals first; otherwise errors with available arrays.
- **Input:** mesh with a point-data vector array. **Output:** arrow-glyph mesh `.ply`.
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| scale_factor | float | 0.01 | 0.0001 | 1.0 | Glyph (arrow) size — absolute, since magnitude scaling is off. |
| vector_name | string | Normals | — | — | Point-data vector array to orient by. |

- **Gotchas:** Output is NEW arrow geometry, not the original surface. `scale_factor` is absolute — default 0.01 assumes ~unit-scale; arrows vanish or dominate at wrong scale. Auto-computes `Normals` only when you ask for `Normals`; any other missing array -> exit 1.
- **Example:** `run_job("pyvista_analysis","pv_glyph","<mesh_id>",{"scale_factor":0.02,"vector_name":"Normals"})`

### `pv_vector_magnitude` — L2 norm of a vector field
- **Purpose:** `np.linalg.norm(vectors, axis=1)` -> scalar `<vector_name>_magnitude`. Auto-computes `Normals` if requested-and-missing (same rule as glyph). Logs min/max/mean.
- **Input:** mesh with the named vector array. **Output:** mesh `.ply` + magnitude scalar.
- **Params:**

| name | type | default | effect |
|---|---|---|---|
| vector_name | string | Normals | Point-data vector array to take the magnitude of. |

- **Gotchas:** For unit normals every magnitude ≈ 1 (boring) — useful mostly on displacement/velocity fields. Missing non-`Normals` array -> exit 1.
- **Example:** `run_job("pyvista_analysis","pv_vector_magnitude","<mesh_id>",{"vector_name":"Normals"})`

### `pv_scalar_stats` — Scalar statistics + normalization
- **Purpose:** pick a scalar (named, else first point-data array, else falls back to **Z-coordinate as `elevation`**); log min/max/mean/median/std; add `<name>_normalized` ([0,1], or zeros if range ~0).
- **Input:** mesh (any). **Output:** mesh `.ply` + `<name>_normalized` field. Stats in logs.
- **Params:**

| name | type | default | effect |
|---|---|---|---|
| scalars | string | "" | Array name; empty = first available (or synthesized `elevation`=Z). |

- **Gotchas:** Named array not present -> exit 1. Stats are logged, not returned in the file. The auto-`elevation` fallback means it never fails for lack of scalars on a mesh with points.
- **Example:** `run_job("pyvista_analysis","pv_scalar_stats","<mesh_id>",{"scalars":""})`

### `pv_extract_feature_edges` — Feature/boundary/non-manifold edges
- **Purpose:** `mesh.extract_feature_edges(feature_angle, boundary_edges, feature_edges=True, non_manifold_edges, manifold_edges)` -> a line/edge PolyData. Detects sharp (dihedral > angle), boundary (1-face), non-manifold (3+-face), optionally manifold (2-face) edges.
- **Input:** mesh. **Output:** edges `.ply` (lines, not a surface).
- **Params:**

| name | type | default | min | max | effect |
|---|---|---|---|---|---|
| feature_angle | float | 30.0 | 0.0 | 180.0 | Dihedral threshold (deg); higher = fewer sharp edges flagged. |
| boundary_edges | string(bool) | "true" | — | — | Include open-boundary edges. |
| non_manifold_edges | string(bool) | "true" | — | — | Include edges shared by 3+ faces. |
| manifold_edges | string(bool) | "false" | — | — | Include ordinary 2-face edges. |

- **Booleans:** parsed via `s.lower() in ("true","1","yes")` — pass the strings `"true"`/`"false"`. `feature_edges` is always on.
- **Gotchas:** Output is edge geometry (visualize as lines). Great for QC: boundary edges reveal holes; non-manifold edges reveal topology errors. `manifold_edges=true` returns essentially the whole wireframe.
- **Example:** `run_job("pyvista_analysis","pv_extract_feature_edges","<mesh_id>",{"feature_angle":45,"boundary_edges":"true","non_manifold_edges":"true","manifold_edges":"false"})`

---

## Cross-cutting gotchas

- **Output types vary:** `mesh_to_pcd_*`, `voxelization`, `sdf_voxel_visualization`, and both `collision_detection` methods emit **point clouds**; `pv_threshold_volume`/`pv_extract_cells` emit **`.vtu`**; everything else emits `.ply` meshes/edges.
- **`target_reduction` (pv_decimate) = fraction removed** vs **`target_triangles` (simplification) = absolute keep count** — opposite semantics.
- **Open3D normal-estimation defaults (radius=0.1) are scale-bound** — Poisson/ball-pivoting on non-unit-scale clouds need explicit upstream normals (pointcloud-ops `normal_estimation`).
- **SDF/occupancy/voxel cost is cubic** in 1/`voxel_size` (or `resolution³`) — start coarse.
- **PyVista volume ops need scalars**; cell-data is auto-converted to point-data only inside `pv_contour`. Check ranges with `pv_scalar_stats` before thresholding (defaults [0,1] assume normalized data).
- **`pv_extract_surface` (mesh module) is a no-op on surfaces**; use `pv_extract_geometry` (volume module) for a volume's outer surface.
- **Analysis methods add fields, not geometry** (except `pv_glyph`); use `visualize_sample` to render the scalar/vector result.
- **Jobs are in-memory** (Cloud Run scale-to-zero can drop a long job's handle) — chain with `run_pipeline`; files persist. See **ppline-3dcv:mcp-tool-reference**.
