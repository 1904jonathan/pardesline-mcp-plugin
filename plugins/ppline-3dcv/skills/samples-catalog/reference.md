# Samples reference — every built-in id

Exhaustive enumeration of all built-in samples, grounded in the platform code/registries:

- **Open3D** (11) — `backend/services/sample_generator.py` (`SAMPLE_INFO`), materialized in
  `backend/data/samples/*.ply`.
- **PyVista** (45) — `backend/services/pyvista_sample_generator.py`, registry
  `backend/data/pyvista_dataset_registry.json`, files in `backend/data/pyvista_samples/`.
- **SimpleITK** (21) — `backend/services/simpleitk_samples_service.py`, registry
  `backend/data/simpleitk_dataset_registry.json`.

Every id below is real. Pass it to `use_sample(id)`, `run_job(..., sample_id=id)`,
`visualize_sample(id)`, or (volumes) `visualize_registration(fixed=id, moving=id)`.

Geometry-type values: `mesh`, `pointcloud`, `volume`. These come from the registries — note a
few PyVista shapes are detected as `pointcloud` (no faces in the saved PLY), flagged below.

---

## 1. Open3D samples (11) — `list_open3d_samples()`

PLY files. `mesh` = triangle mesh, `pointcloud` = points only.

| id | name | geometry | category | notes |
|----|------|----------|----------|-------|
| `bunny` | Stanford Bunny | mesh | primitive | classic demo mesh ("try it on the bunny") |
| `sphere` | Sphere | mesh | primitive | radius 0.5 |
| `cube` | Cube | mesh | primitive | 1×1×1, centered |
| `cylinder` | Cylinder | mesh | primitive | r=0.3, h=1.0 |
| `cone` | Cone | mesh | primitive | r=0.4, h=1.0 |
| `random_cloud` | Random Cloud | pointcloud | primitive | 5000 random points in unit cube |
| `armadillo` | Armadillo | mesh | open3d | Stanford Armadillo |
| `knot` | Knot | mesh | open3d | trefoil knot |
| `eagle` | Eagle | pointcloud | open3d | colored scan, ~5000 pts |
| `icp_source` | ICP Source | pointcloud | open3d | DemoICP cloud_bin_0 — **moving** in ICP demo |
| `icp_target` | ICP Target | pointcloud | open3d | DemoICP cloud_bin_1 — **fixed** in ICP demo |

Registration pair: `fixed=icp_target`, `moving=icp_source` (the canonical Open3D ICP tutorial
pair; cloud_bin_0 + cloud_bin_1 are adjacent views aligned by the tutorial's trans_init).

---

## 2. PyVista samples (45) — `list_pyvista_samples()`

### 2a. Primitives (12) — `category: primitive`

| id | name | geometry | source |
|----|------|----------|--------|
| `pv_sphere` | Sphere | mesh | `pyvista.Sphere()` |
| `pv_cylinder` | Cylinder | mesh | `pyvista.Cylinder()` |
| `pv_box` | Box | mesh | `pyvista.Box()` |
| `pv_cone` | Cone | **pointcloud** | `pyvista.Cone()` (saved PLY has no faces) |
| `pv_arrow` | Arrow | mesh | `pyvista.Arrow()` |
| `pv_plane` | Plane | mesh | `pyvista.Plane()` |
| `pv_disc` | Disc | mesh | `pyvista.Disc()` |
| `pv_platonic_tetrahedron` | Platonic Tetrahedron | **pointcloud** | `pyvista.PlatonicSolid('tetrahedron')` |
| `pv_platonic_cube` | Platonic Cube | mesh | `pyvista.PlatonicSolid('cube')` |
| `pv_platonic_octahedron` | Platonic Octahedron | mesh | `pyvista.PlatonicSolid('octahedron')` |
| `pv_platonic_dodecahedron` | Platonic Dodecahedron | mesh | `pyvista.PlatonicSolid('dodecahedron')` |
| `pv_platonic_icosahedron` | Platonic Icosahedron | mesh | `pyvista.PlatonicSolid('icosahedron')` |

### 2b. Parametric surfaces (21) — `category: parametric`, all `mesh`

| id | name | source |
|----|------|--------|
| `pv_supertoroid` | Super Toroid | `pyvista.ParametricSuperToroid()` |
| `pv_ellipsoid` | Ellipsoid | `pyvista.ParametricEllipsoid()` |
| `pv_pseudosphere` | Pseudosphere | `pyvista.ParametricPseudosphere()` |
| `pv_bohemian_dome` | Bohemian Dome | `pyvista.ParametricBohemianDome()` |
| `pv_bour` | Bour Surface | `pyvista.ParametricBour()` |
| `pv_boy` | Boy Surface | `pyvista.ParametricBoy()` |
| `pv_catalan_minimal` | Catalan Minimal | `pyvista.ParametricCatalanMinimal()` |
| `pv_conic_spiral` | Conic Spiral | `pyvista.ParametricConicSpiral()` |
| `pv_cross_cap` | Cross Cap | `pyvista.ParametricCrossCap()` |
| `pv_dini` | Dini Surface | `pyvista.ParametricDini()` |
| `pv_enneper` | Enneper Surface | `pyvista.ParametricEnneper()` |
| `pv_figure8_klein` | Figure-8 Klein | `pyvista.ParametricFigure8Klein()` |
| `pv_henneberg` | Henneberg Surface | `pyvista.ParametricHenneberg()` |
| `pv_klein` | Klein Bottle | `pyvista.ParametricKlein()` |
| `pv_kuen` | Kuen Surface | `pyvista.ParametricKuen()` |
| `pv_mobius` | Mobius Strip | `pyvista.ParametricMobius()` |
| `pv_pluckerconoid` | Plucker Conoid | `pyvista.ParametricPluckerConoid()` |
| `pv_random_hills` | Random Hills | `pyvista.ParametricRandomHills()` |
| `pv_roman` | Roman Surface | `pyvista.ParametricRoman()` |
| `pv_super_ellipsoid` | Super Ellipsoid | `pyvista.ParametricSuperEllipsoid()` |
| `pv_torus` | Torus | `pyvista.ParametricTorus()` |

### 2c. Downloaded datasets (12) — `category: downloaded`

| id | name | geometry | format | source |
|----|------|----------|--------|--------|
| `pv_bunny_coarse` | Bunny (Coarse) | mesh | .ply | `examples.download_bunny_coarse()` |
| `pv_teapot` | Teapot | mesh | .ply | `examples.download_teapot()` |
| `pv_cad_model` | CAD Model | mesh | .ply | `examples.download_cad_model()` |
| `pv_pump_bracket` | Pump Bracket | mesh | .ply | `examples.download_pump_bracket()` |
| `pv_nefertiti` | Nefertiti | mesh | .ply | `examples.download_nefertiti()` |
| `pv_knee` | Knee (Full) | **volume** | .vti | `examples.download_knee_full()` |
| `pv_head` | Head | **volume** | .vti | `examples.download_head()` |
| `pv_bolt_nut` | Bolt & Nut | **volume** | .vti | `examples.download_bolt_nut()` |
| `pv_frog` | Frog | **volume** | .vti | `examples.download_frog()` |
| `pv_lidar` | LiDAR Point Cloud | **pointcloud** | .ply | `examples.download_lidar()` |
| `pv_crater_topo` | Crater Topography | **volume** | .vtk | `examples.download_crater_topo()` |
| `pv_antarctica_velocity` | Antarctica Velocity | mesh | .vtk | `examples.download_antarctica_velocity()` |

PyVista totals: 37 mesh, 5 volume (`pv_knee`, `pv_head`, `pv_bolt_nut`, `pv_frog`,
`pv_crater_topo`), 3 pointcloud (`pv_cone`, `pv_platonic_tetrahedron`, `pv_lidar`).
The 4 `.vti` volumes also appear in the SimpleITK list (see §3) for medical-compatible use.

---

## 3. SimpleITK medical samples (21) — `list_simpleitk_samples()`

All registered as `available: true` in `backend/data/simpleitk_dataset_registry.json`. The
first 4 are PyVista volumes re-exposed for SimpleITK/medical pipelines; the other 17 are
native SimpleITK downloads (with `size_mb`; large ones >200 MB are fetched on demand the first
time but are marked available here).

### 3a. PyVista volumes re-exposed (4) — `category: medical`

| id | name | modality | source |
|----|------|----------|--------|
| `pv_head` | Head CT/MR | Medical | PyVista examples |
| `pv_knee` | Knee MRI | Medical | PyVista examples |
| `pv_bolt_nut` | Bolt & Nut CT | Industrial | PyVista examples |
| `pv_frog` | Frog Volume | Biology | PyVista examples |

### 3b. Native SimpleITK volumes (17)

| id | name | modality | source | size (MB) | notes |
|----|------|----------|--------|----------:|-------|
| `sitk_training_001_ct` | RIRE CT Brain | CT | RIRE dataset | 25 | **fixed** for CT↔MR reg |
| `sitk_training_001_mr_T1` | RIRE MR Brain T1 | MR-T1 | RIRE dataset | 20 | **moving** for CT↔MR reg |
| `sitk_fib_sem_bacillus` | FIB-SEM Bacteria 3D | EM | Microscopy | 500 | electron microscopy volume |
| `sitk_cirs_phantom` | CIRS Abdominal Phantom | CT+MR | CIRS phantom | 800 | DICOM archive (multi-series) |
| `sitk_popi_00` | POPI Lung 4D-CT Phase 00 | 4D-CT | POPI dataset | 80 | lung respiratory phase 0% |
| `sitk_popi_10` | POPI Lung 4D-CT Phase 10 | 4D-CT | POPI dataset | 80 | phase 10% |
| `sitk_popi_20` | POPI Lung 4D-CT Phase 20 | 4D-CT | POPI dataset | 80 | phase 20% |
| `sitk_popi_30` | POPI Lung 4D-CT Phase 30 | 4D-CT | POPI dataset | 80 | phase 30% |
| `sitk_popi_40` | POPI Lung 4D-CT Phase 40 | 4D-CT | POPI dataset | 80 | phase 40% |
| `sitk_popi_50` | POPI Lung 4D-CT Phase 50 | 4D-CT | POPI dataset | 80 | phase 50% (max exhale/inhale) |
| `sitk_popi_mask_00` | POPI Lung Mask Phase 00 | Segmentation | POPI dataset | 20 | air/body/lungs mask for phase 00 |
| `sitk_liver_patient01` | Liver Tumor Patient 01 (Ground Truth) | CT | Segmentation dataset | 5 | reference segmentation |
| `sitk_liver_rad01` | Liver Tumor Radiologist 01 | CT | Segmentation dataset | 5 | observer 1 segmentation |
| `sitk_liver_rad02` | Liver Tumor Radiologist 02 | CT | Segmentation dataset | 5 | observer 2 segmentation |
| `sitk_liver_rad03` | Liver Tumor Radiologist 03 | CT | Segmentation dataset | 5 | observer 3 segmentation |
| `sitk_vm_head_mri` | Visible Human MRI Head | MRI | Visible Human | 40 | head MRI volume |
| `sitk_vm_head_rgb` | Visible Human RGB Head | RGB | Visible Human | 300 | cryosection RGB volume |

### SimpleITK registration / comparison pairs

| Use case | fixed | moving | method (module `simpleitk_registration`) |
|----------|-------|--------|------------------------------------------|
| Brain CT↔MR rigid/affine (RIRE) | `sitk_training_001_ct` | `sitk_training_001_mr_T1` | `rigid` / `advanced_rigid` / `affine` |
| Lung 4D-CT deformable (POPI) | `sitk_popi_00` | `sitk_popi_10` … `sitk_popi_50` | `bspline` / `demons` |
| Multimodal phantom CT↔MR | `sitk_cirs_phantom` (CT series) | `sitk_cirs_phantom` (MR series) | `affine` (single multi-series DICOM archive) |
| Liver inter-observer overlap | `sitk_liver_patient01` | `sitk_liver_rad01/02/03` | `difference_analysis` |

Lung mask `sitk_popi_mask_00` pairs with `sitk_popi_00` for masked metrics / segmentation QC.

---

## Quick recipes

```python
# 1. Run an algorithm directly on a sample (auto-materialized)
run_job("mesh_processing", "simplification", sample_id="bunny",
        params={"target_triangles": 2000})

# 2. Visualize an Open3D sample in the full-screen viewer
visualize_sample("armadillo")            # -> {view_url}
visualize_samples(["bunny", "armadillo"])# several in one scene

# 3. Medical CT->MR registration with the 4-panel slicer
visualize_registration(fixed="sitk_training_001_ct",
                       moving="sitk_training_001_mr_T1",
                       method="rigid")

# 4. Point-cloud ICP on the Open3D demo pair
run_job("registration", "icp_refinement",
        sample_id="icp_target", moving_sample_id="icp_source")
```

Totals: **Open3D 11 · PyVista 45 · SimpleITK 21 = 77 built-in samples.**
