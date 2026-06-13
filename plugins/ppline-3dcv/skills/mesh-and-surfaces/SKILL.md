---
name: mesh-and-surfaces
description: >-
  Mesh decimation/subdivision/smoothing/cleaning/hole-filling/normals/triangulate,
  surface reconstruction from point clouds (Poisson, alpha shape, ball pivoting,
  convex hull), voxelization & binary erosion, signed distance fields + marching
  cubes, collision/penetration measurement, PyVista volume contour/slice/threshold/
  extract and geometric analysis (curvature/distance/glyph/edges), via the
  ppline-3dcv MCP server. Use when the user asks to repair/simplify/smooth/subdivide
  a mesh, sample a mesh to points, build a surface from a point cloud, voxelize,
  compute an SDF/occupancy/TSDF, detect collisions or measure penetration, contour/
  slice/threshold a volume, or analyze curvature/distance/feature-edges/glyphs.
---

# Mesh & Surfaces (ppline-3dcv)

The universal recipe (`upload_file`/`use_sample` -> `run_job` -> `output_url`; `visualize_sample` for views) lives in **ppline-3dcv:using-ppline** — do not repeat it. `run_job` shape + return keys: **ppline-3dcv:mcp-tool-reference**. Sample ids (fetch at runtime, never invent): **ppline-3dcv:samples-catalog** via `list_open3d_samples()` / `list_pyvista_samples()`. Point-cloud prep (normals, downsample, outlier removal): **ppline-3dcv:pointcloud-ops**.

This file is the **scannable index + the load-bearing gotchas**. For the EXHAUSTIVE per-method detail (purpose from the script, exact input/output type, every parameter with default/range/effect, internal behavior, extra outputs, copy-paste `run_job`, per-method gotchas) see **[reference.md](reference.md)**. Everything below is grounded in the actual Python scripts under `modules/<id>/scripts/`.

---

## Input/Output requirements (CRITICAL — read first)

| Module | Backend | Input it REALLY needs | Output |
|---|---|---|---|
| `mesh_processing` | Open3D | a **triangle mesh** (`subdivision` needs triangles; if you feed a points-only file the mesh-to-pcd methods build a convex hull first) | mesh `.ply`, or point cloud `.ply` for the two `mesh_to_pcd_*` methods |
| `pyvista_mesh_processing` | PyVista/VTK | a **mesh** (non-PolyData is auto `extract_surface()`'d); `pv_extract_surface` is meant for a **volume/grid** | mesh `.ply` |
| `point_cloud_reconstruction` | Open3D | a **point cloud**. `poisson`/`ball_pivoting` need **normals** — but the scripts **estimate + orient normals internally if absent** (radius=0.1, max_nn=30, orient k=15). `alpha_shape`/`convex_hull` do NOT use normals | mesh `.ply` |
| `voxel_to_mesh` | Open3D (+scipy/skimage) | a **mesh** (points-only -> convex hull) | `voxelization` -> **colored point cloud** of voxel centers; `binary_erosion` -> mesh `.ply` |
| `sdf` | Open3D RaycastingScene | a **mesh** (points-only -> convex hull). Watertight + manifold for correct signs | `compute_sdf`/`occupancy_reconstruction` -> mesh `.ply`; `sdf_voxel_visualization` -> **colored point cloud** |
| `collision_detection` | Open3D RaycastingScene | a **mesh** (points-only -> convex hull). Tests against a **synthetic sphere**, NOT a second mesh | colored point cloud `.ply` (metrics go to logs only) |
| `pyvista_volume_processing` | PyVista/VTK | a **volume/grid** with scalar data (`.vti`/`.vtu`/`.vtk`); surfaces work for slice/extract but contour/threshold need scalars | `.ply` (surfaces/slices) or `.vtu` (threshold, extract_cells) |
| `pyvista_analysis` | PyVista/VTK | a **mesh** (non-PolyData auto `extract_surface()`'d). `pv_glyph`/`pv_vector_magnitude` need a **vector array** (auto-computes `Normals` if you ask for `Normals`) | mesh `.ply` with a new scalar/vector field |

---

## Catalog (module_id — method_id(param=default))

- **mesh_processing** — `subdivision(iterations=1)` · `simplification(target_triangles=5000)` · `mesh_to_pcd_uniform(num_points=5000)` · `mesh_to_pcd_poisson_disk(num_points=5000)`
- **pyvista_mesh_processing** — `pv_decimate(target_reduction=0.5)` · `pv_subdivide(n_subdivisions=1, algorithm=linear)` · `pv_smooth_laplacian(n_iterations=20, relaxation_factor=0.01)` · `pv_smooth_taubin(n_iterations=20, pass_band=0.1)` · `pv_clean(tolerance=0.0)` · `pv_fill_holes(hole_size=100.0)` · `pv_compute_normals(flip_normals=0, consistency=1)` · `pv_triangulate()` · `pv_extract_surface()`
- **point_cloud_reconstruction** — `poisson(depth=9, scale=1.1)` · `convex_hull()` · `alpha_shape(alpha=0.03)` · `ball_pivoting(radius_factor=2.0)`
- **voxel_to_mesh** — `voxelization(voxel_size=0.01)` · `binary_erosion(voxel_size=0.01, erosion_iterations=1)`
- **sdf** — `compute_sdf(voxel_size=0.01, padding=5)` · `occupancy_reconstruction(voxel_size=0.01, padding=5)` · `sdf_voxel_visualization(resolution=32, min_clamp=-0.1, max_clamp=0.1)`
- **collision_detection** — `sdf_collision(obstacle_radius=0.5, penetration_ratio=0.3, num_samples=50000)` · `penetration_depth(obstacle_radius=0.5, overlap_distance=0.15)`
- **pyvista_volume_processing** — `pv_contour(n_contours=5, scalars="")` · `pv_slice(normal_x=1, normal_y=0, normal_z=0, origin_x=0, origin_y=0, origin_z=0)` · `pv_slice_orthogonal(x=0, y=0, z=0)` · `pv_threshold_volume(lower=0, upper=1)` · `pv_extract_geometry()` · `pv_extract_cells(cell_type=tetrahedral)`
- **pyvista_analysis** — `pv_curvature(curvature_type=mean)` · `pv_distance()` · `pv_glyph(scale_factor=0.01, vector_name=Normals)` · `pv_vector_magnitude(vector_name=Normals)` · `pv_scalar_stats(scalars="")` · `pv_extract_feature_edges(feature_angle=30, boundary_edges=true, non_manifold_edges=true, manifold_edges=false)`

Full per-method tables (every param, range, effect, extra outputs, examples) -> **[reference.md](reference.md)**.

---

## Copy-paste recipes

Reconstruct a watertight surface from a point cloud (Poisson — normals auto-estimated, but estimate yourself for control):
```text
use_sample(sample_id="<pcd_id>")                         # id from list_open3d_samples()
run_job(module_id="features_extraction", method_id="normal_estimation",
        file_id="<pcd_id>", params={"radius": 0.05, "max_nn": 30})   # optional but recommended
run_job(module_id="point_cloud_reconstruction", method_id="poisson",
        file_id="<normals_or_raw_pcd_id>", params={"depth": 9, "scale": 1.1})
```

Decimate a dense mesh by 50%, then Taubin-smooth (shrinkage-free):
```text
run_job(module_id="pyvista_mesh_processing", method_id="pv_decimate",
        file_id="<mesh_id>", params={"target_reduction": 0.5})
run_job(module_id="pyvista_mesh_processing", method_id="pv_smooth_taubin",
        file_id="<decimated_id>", params={"n_iterations": 30, "pass_band": 0.1})
```

Mesh -> SDF -> reconstructed surface (marching cubes at the zero level set):
```text
run_job(module_id="sdf", method_id="compute_sdf",
        file_id="<mesh_id>", params={"voxel_size": 0.01, "padding": 5})
```

Volume -> isosurface (needs point-data scalars; the script converts cell->point data automatically):
```text
run_job(module_id="pyvista_volume_processing", method_id="pv_contour",
        file_id="<volume_id>", params={"n_contours": 5, "scalars": ""})
```

---

## Gotchas (load-bearing)

- **`target_reduction` is the FRACTION REMOVED** (`pv_decimate`): `0.5` keeps ~50% of triangles, `0.9` keeps only ~10%. By contrast `simplification.target_triangles` is the absolute **keep** count.
- **`mesh_processing.subdivision` uses Open3D `subdivide_loop` (Loop, smoothing) — not midpoint.** Triangle-only and it smooths/rounds the surface. Face count ~×4 per iteration; `iterations=4` on a dense mesh explodes memory.
- **Poisson auto-estimates normals** (radius **0.1** — wrong if your cloud isn't ~unit scale) and **trims the lowest 1% density** vertices, but can still balloon past the cloud. For control, run `features_extraction.normal_estimation` first; `depth` ↑ = detail + compute/memory, `scale` controls the reconstruction-cube padding.
- **`ball_pivoting`** auto-estimates normals too and derives ball radii from **average NN spacing × radius_factor × {1,2,4}**. Needs roughly uniform density; too small `radius_factor` misses triangles, too large bridges gaps. Leaves holes (not watertight).
- **`alpha_shape`** needs NO normals; `alpha` too small = fragmented/holey, too large = convex blob. If it yields an empty mesh the script **auto-retries with alpha = bbox-diagonal × {0.1,0.25,0.5,1.0}**.
- **`convex_hull`** ignores all concavities (outer envelope only) — fallback/bounding use, not detail.
- **SDF/occupancy/collision input should be watertight & manifold** or inside/outside signs are wrong. **`voxel_size` ↓ = cubic blow-up** in memory/time (grid = bbox/voxel_size per axis); keep ≥0.005 for anything non-tiny. `padding` is in **voxels**.
- **`voxelization` outputs a POINT CLOUD** (voxel centers, height-colored), not a mesh/voxel file. **`binary_erosion`** erodes with a 6-connected structuring element (scipy) then marching-cubes back to a mesh; shrinks the solid by `erosion_iterations` voxels.
- **`sdf_voxel_visualization` is a TSDF viewer**: keeps only voxels with SDF in `[min_clamp, max_clamp]` (a near-surface band), coolwarm-colored (blue interior / white surface / red exterior). `resolution` is clamped to **[8,128]**; cost is `resolution^3`.
- **`collision_detection` does NOT test two meshes** — it places a synthetic **sphere** (`obstacle_radius`) overlapping the input along +X and measures penetration of sampled surface points. `penetration_depth` **hardcodes 50000 samples** (ignores any `num_samples`) and writes max/mean depth + collision bbox **to the logs only** (output is the colored point cloud). `sdf_collision`'s `num_samples` IS honored.
- **`pv_distance` does NOT take a second mesh** — it computes each vertex's distance to the mesh's **own center of mass** and stores `distance_from_center`. (The old skill claimed dual-input; that is WRONG.)
- **`pv_smooth_laplacian` shrinks volume**; prefer **`pv_smooth_taubin`** for organic/closed shapes.
- **`pv_fill_holes(hole_size=...)`** is a size threshold in **mesh units** (not a hole count); large boundary loops stay open. VTK's filler can also bridge unintended openings.
- **`pv_extract_surface` is a no-op on a plain surface mesh** — it's for volumes/UnstructuredGrid. For a volume's outer boundary use **`pv_extract_geometry`** (volume module).
- **`pv_contour`/`pv_threshold_volume` need scalar data.** `pv_contour` auto-converts cell→point data and auto-picks the first array if no active scalars; it computes `n_contours` **evenly-spaced isovalues strictly between** the scalar min/max. `pv_threshold_volume` outputs **`.vtu`** (keeps volumetric cells); feed that to `pv_extract_geometry` to get a surface.
- **`pv_glyph`/`pv_vector_magnitude`** need the named vector array; if `vector_name="Normals"` is missing they **auto-compute point normals**, otherwise they error with the available array list. `pv_glyph` uses `scale=False` so output size = `scale_factor` only (set it relative to your bounding box — default 0.01 assumes unit scale).
- **`pv_curvature`/`pv_scalar_stats`/`pv_vector_magnitude`/`pv_distance`** only ADD a scalar/vector field — geometry is unchanged. Colorize via `visualize_sample` to see results. `pv_scalar_stats` prints stats to logs, adds `<name>_normalized`, and falls back to a `Z`/`elevation` scalar if none exist.
- **`pv_extract_cells`** only matters for UnstructuredGrid with mixed cell types; if no cells match it **writes an empty grid and exits 0** (silent). Valid `cell_type`: tetrahedral, hexahedral, wedge, pyramid, triangle, quad.
- **Jobs are in-memory**: on Cloud Run scale-to-zero a long job's handle can vanish (`get_job_status` -> not found). Files persist; prefer `run_pipeline` for chains. See mcp-tool-reference.
