---
name: medical-imaging
description: >-
  Medical volume work over the ppline-3dcv MCP server — load a DICOM folder,
  rigid/affine/B-spline/demons registration of CT/MR volumes, organ/tissue
  segmentation, deformation QC (Jacobian folding), warp a moving volume, export
  DICOM, and open the 4-panel slicer / registration studio. Use for DICOM, CT,
  MR, "register these scans", "segment this volume", "align CT and MRI",
  "check the deformation", "export as DICOM".
---

# Medical Imaging (ppline-3dcv)

Everything for CT/MR/DICOM volume work over the `ppline-3dcv` MCP server, grounded
in the real platform scripts and services. Two flavors of tooling:

1. **Registry modules** — run via the generic `run_job` (and `run_pipeline`).
   `simpleitk_registration` (dual-input) and `simpleitk_segmentation` (single-input).
2. **Dedicated MCP medical tools** — call directly: `upload_dicom_folder`,
   `get_volume_info`, `analyze_registration_deformation`, `warp_volume`,
   `export_volume_dicom`, `visualize_registration`.

Universal call/auth recipe (X-API-Key header, `list_modules`/`get_module_info`,
`run_job` shape): see **`ppline-3dcv:using-ppline`** and **`ppline-3dcv:mcp-tool-reference`**.
File-id lifecycle (uploads → outputs, download URLs): **`ppline-3dcv:data-io-and-files`**.
Sample ids: **`ppline-3dcv:samples-catalog`**. Viewers/URLs: **`ppline-3dcv:visualization-and-viewers`**.

If this file feels long, the same content with deeper internals is in the sibling
**`reference.md`** in this folder.

---

## Core mental model — coordinates, init, transform space

These four facts govern everything below (from `backend/services/simpleitk_service.py`):

- **Array order is (z, y, x).** SimpleITK numpy arrays are `[depth, row, col]`.
  `GetSize()` returns `(x, y, z)`; `GetArrayFromImage()` returns `(z, y, x)`. The
  VTI conversion explicitly transposes ZYX→XYZ. Never index a slice as `[x,y,z]`.
- **Registration runs in physical mm space, not voxel space.** Spacing, origin and
  direction (LPS) are honored; transforms map physical points → physical points.
  Two volumes with different spacing/origin still register correctly.
- **Initialization is GEOMETRY, not MOMENTS.** `get_initial_transform()` uses
  `CenteredTransformInitializerFilter.GEOMETRY` (aligns the geometric centers of
  the two images). MOMENTS (center-of-mass + principal axes) is *not* the default
  because it can flip/fail on partial-FOV or multi-modal data. (The one exception:
  `advanced_rigid`'s exhaustive pre-search seeds from MOMENTS internally, then
  refines.)
- **The metric is Mattes Mutual Information** (50 histogram bins) for rigid/
  advanced_rigid/affine — correct for multi-modal CT↔MR. B-spline uses MeanSquares;
  demons uses optical-flow. Multi-resolution pyramid is `[4, 2, 1]` shrink with
  `[2, 1, 0]` smoothing sigmas (physical units) for the optimizer-based methods.

---

## `simpleitk_registration` — DUAL-INPUT (module `order=18`, category `registration`)

Input formats: `.vti .mha .nrrd .nii .dcm`. Output extension: `.vti` for every method.
Each script also writes a **`.json` sidecar** next to the output (transform summary +
geometry). `dual_input=true`, `dual_input_label="Moving Volume"`.

### THE DUAL-INPUT RULE (read first)
In `run_job` you MUST pass BOTH volumes:
- **fixed** (reference) → `file_id=` OR `sample_id=` → script `--input`
- **moving** (to be aligned) → `moving_file_id=` OR `moving_sample_id=` → script `--moving`

**Omitting the moving input is the #1 trap.** Every registration script, when
`--moving` is absent, calls `create_synthetic_moving(fixed)`: it applies a *known*
fabricated rotation/translation to the fixed volume and registers that. The result
looks plausible but is self-alignment garbage — it tells you nothing about your real
moving scan. Always supply `moving_file_id`/`moving_sample_id`.

### Output of every registration method
- **`output_url`**: the registered moving volume resampled into the fixed grid (`.vti`,
  loadable in the slicer; gray=fixed, overlay=moving conventionally).
- **`.json` sidecar** (same basename, `.json`): `{transform_type, transform, spacing,
  origin, direction}`. `transform` is produced by `transform_to_dict()`:
  - Euler3D (rigid): `rotation_rad`, `rotation_deg` (3), `translation_mm` (3),
    `center_mm`, plus raw `parameters`/`fixed_parameters`.
  - Affine: `matrix_3x3` (9), `translation_mm` (3).
  - Composite (advanced_rigid, bspline): `num_transforms` + `sub_transforms[]`.
  - DisplacementField (demons): a **summary only** (`field_size`, `field_spacing`,
    `mean/max/std_displacement_mm`) — NOT the full field (millions of vectors would OOM).

> ⚠️ The sidecar is a **human-readable JSON summary**, not a SimpleITK-loadable
> `.tfm/.hdf5/.txt`. The deformation-QC and warp tools (`analyze_registration_deformation`,
> `warp_volume`) require a transform file in `.tfm/.hdf5/.txt`. See the **Transform-file
> gotcha** below — you generally inspect deformation from the registered volume + the
> sidecar, and use `warp_volume` only when you have a real saved `.tfm`.

### Methods

| method_id | params (defaults) | model | what it does |
|---|---|---|---|
| `rigid` | `learning_rate=1.0`, `num_iterations=100`, `sampling_percentage=0.01` | Euler3D, 6 DOF | GEOMETRY init → Mattes MI → GradientDescent, pyramid [4,2,1]. Pose only (3 rot + 3 trans). Fast baseline. |
| `advanced_rigid` | `learning_rate=0.2`, `num_iterations=200`, `sampling_percentage=0.15` | Composite(Euler3D∘Euler3D) | Two-stage: **exhaustive rotation search** (12 steps/axis ≈ 15° over all 3 axes, MOMENTS-seeded, coarse 8× shrink) THEN refined GradientDescent. Recovers LARGE rotational offsets gradient descent alone can't. Slower (~2-4×). |
| `affine` | `learning_rate=1.0`, `num_iterations=100`, `sampling_percentage=0.01` | Affine, 12 DOF | GEOMETRY init → Mattes MI → GradientDescent. Adds scale + shear on top of rigid. Use when scanners differ / anisotropic scaling / inter-scan growth. |
| `bspline` | `grid_spacing=50.0`, `num_iterations=100` | Composite(Affine + BSpline FFD) | **Non-rigid.** Runs `register_affine` first (pose), then cubic B-spline free-form deformation on a control-point grid (`grid_spacing` mm → mesh size), MeanSquares metric, LBFGSB optimizer, scaleFactors [1,2,4]. |
| `demons` | `num_iterations=20`, `standard_deviations=2.0` | DisplacementFieldTransform | **Non-rigid.** FastSymmetricForcesDemons optical-flow; dense per-voxel displacement field, Gaussian-smoothed each iteration (σ = `standard_deviations`). Best for mono-modal/same-modality local deformation. |
| `difference_analysis` | `lower_threshold=50.0`, `upper_threshold=400.0` | (QC, not a transform) | Computes `|fixed − moving|` absolute-difference volume + stats. Output sidecar `statistics`: `mean/max/std_difference`, `total_voxels`, `high_diff_voxels`, `high_diff_percentage`. Use as a quick residual-error check; pass a *registered* volume as the moving input. |

#### Parameter meanings / ranges (from `module.json`)
- `learning_rate` (0.1–5.0 rigid/affine; 0.05–2.0 advanced): GradientDescent step.
  Lower = more stable, slower. advanced_rigid's 0.2 is deliberately conservative.
- `num_iterations` (rigid/affine 10–500; advanced 50–500; bspline 20–300; demons 5–100):
  max optimizer iterations. For bspline this is LBFGSB iters; for demons, demons iters.
- `sampling_percentage` (0.005–0.5): fraction of voxels sampled for the metric.
  advanced_rigid's 15% gives a smoother metric landscape (vs 1% default) at higher cost.
- `grid_spacing` (10.0–100.0 mm, bspline): control-point spacing. **Smaller = finer/
  more flexible deformation = more parameters = more folding risk.** Larger = stiffer.
- `standard_deviations` (0.5–5.0, demons): Gaussian smoothing σ of the displacement
  field. **Higher = smoother, more diffeomorphic (less folding); lower = more local
  but riskier.**
- `lower_threshold`/`upper_threshold` (difference_analysis): HU/intensity band that
  counts as "high misalignment" in the residual stats.

---

## `simpleitk_segmentation` — SINGLE-INPUT (module `order=19`, category `segmentation`)

Input formats: `.vti .mha .nrrd .nii`. Output `.vti` (label map, cast to Float32 for the
web viewer). Single input only — pass `file_id`/`sample_id`, no moving.

| method_id | params (defaults, ranges) | what it does / output |
|---|---|---|
| `otsu_threshold` | (none) | Otsu between-class-variance auto threshold → binary mask (inside=1). Best for bimodal histograms (bone vs background). Logs the chosen threshold value. |
| `manual_threshold` | `lower=100` (−1000…3000), `upper=1000` (−1000…3000) | `BinaryThreshold(lower≤I≤upper)` → binary mask. CT is HU-calibrated: air −1000, water 0, soft tissue +40…+80, bone +300…+3000 — pick the band you want. |
| `connected_components` | `threshold=100` (−1000…3000), `min_size=15` voxels (1…1000) | Binary-threshold at `threshold`, label connected regions (`ConnectedComponent`), drop regions smaller than `min_size` (`RelabelComponent`). Output = labeled volume; logs object count. |
| `watershed` | `threshold=100`, `seed_radius=10.0` mm (1…50), `min_object_size=15` (1…1000) | Full pipeline: binary threshold → morphological opening+closing-by-reconstruction → signed Maurer distance map → seeds from distance peaks beyond `seed_radius` → `MorphologicalWatershedFromMarkers` → boundary-object removal. Splits *touching* objects that plain CC merges. Output = labeled volume. |

Use Otsu/manual to get a mask, then CC or watershed to separate instances; watershed
when objects touch (e.g. adjacent vertebrae/cells), CC when they're spatially separated.

---

## Dedicated MCP medical tools (call DIRECTLY, not via `run_job`)

### `upload_dicom_folder(files: list[dict]) -> dict`
- `files` = list of `{filename, content_base64}`, **one entry per `.dcm` slice** (the MCP
  client reads the folder and base64-encodes each slice).
- Reassembles the series with SimpleITK GDCM (`load_dicom`: picks the series with the most
  slices; on broken metadata, groups files by shared 2D image size and stacks the largest
  group). Stores it as a `.vti` **plus a `.mha` sibling**.
- **Why the `.mha` sibling:** `load_volume()` prefers a sibling `.mha` for `.vti` inputs —
  `sitk.ReadImage(.mha)` is ~3× faster and ~3× less memory than the PyVista→numpy→SimpleITK
  path needed for `.vti`. Registration scripts get the fast path for free.
- **Returns:** volume metadata + `{file_id, extension:".vti", geometry_type:"volume",
  slices_received, dimensions, spacing, origin, scalar_range, message}`.
- For a *single* file use the generic `upload_file` instead.

### `get_volume_info(file_id: str) -> dict`
- Returns `{dimensions [x,y,z], spacing [mm], origin, scalar_name, scalar_range
  [min,max], file_id}`. Looks in `.vti .vtu .vtk .mha .nrrd .nii`.
- **Run BEFORE registration** on fixed and moving to sanity-check geometry (units,
  orientation, intensity range — e.g. CT in HU vs MR arbitrary units).

### `analyze_registration_deformation(transform_file_id, reference_file_id, grid_spacing=4) -> dict`
- `transform_file_id` = a **loadable transform file** (`.tfm/.hdf5/.txt`); `reference_file_id`
  = the fixed volume defining the physical space.
- Samples the displacement field every `grid_spacing` voxels and computes the **Jacobian
  determinant** on the central axial slice (finite differences).
- **Returns:** `displacement_magnitude_mm {min,max}`, `sampled_points`,
  `jacobian_range {min,max}`, **`folded_fraction`** (fraction of sampled voxels with
  Jacobian ≤ 0), `folding_detected` (bool), `slice:"central axial"`, `message`.
- **KEY QC.** Jacobian det > 0 everywhere = locally invertible (diffeomorphic, valid).
  **Jacobian ≤ 0 = the deformation folds/tears** (tissue collapses onto itself) — an
  invalid warp. Always run this after `bspline`/`demons`; reject results with
  `folding_detected=true` / `folded_fraction>0` and increase regularization
  (bigger `grid_spacing`, higher demons `standard_deviations`).

### `warp_volume(fixed_file_id, moving_file_id, transform_file_id, t=1.0) -> dict`
- Applies the transform to warp moving into fixed space at interpolation `t∈[0,1]`
  (t=0 → original moving, t=1 → fully registered; intermediate = parameter/field-scaled
  morph for visualizing the deformation animation).
- `transform_file_id` again must be `.tfm/.hdf5/.txt`.
- **Returns:** `{warped_file_id, t, output_url (downloadable .vti), view_url, message}`.
  `view_url` is a registration-studio deep-link overlaying the warped volume on the fixed.

### `export_volume_dicom(file_id, series_description="Registered") -> dict`
- Casts the volume to Int16, writes per-slice DICOM with a fresh series UID and slice
  geometry, zips it. Accepts the volume set `.vti/.vtu/.vtk/.mha/.nrrd/.nii` (same as
  `get_volume_info`; non-image grids fail gracefully).
- **Returns:** `{file_id, series_description, slices, zip_url, message}`. Use for a DICOM
  deliverable from a registration/warp output.

### `visualize_registration(fixed, moving=None, method="rigid", fixed_is_file_id=False, moving_is_file_id=False) -> dict`
- Opens the FULL-PAGE 4-panel MPR slicer / registration studio (sagittal, coronal, axial
  + 3D), fixed as gray background, moving overlaid.
- **DEFAULTS to SAMPLE ids** (`fixed`/`moving` are sample ids unless you flip the flags).
  To visualize YOUR uploaded volume, pass its `file_id` and set
  `fixed_is_file_id=True` / `moving_is_file_id=True` (file must be a slicer-loadable `.vti`,
  e.g. from `upload_dicom_folder`).
- `method` pre-selects the UI method (`rigid|advanced_rigid|affine|bspline|demons|
  difference_analysis`).
- **Returns:** `{fixed, moving, method, url, message}` — present the `url` to the user.

---

## Recommended pipeline ordering

1. **Ingest.** `upload_dicom_folder(...)` for a DICOM folder, or grab `sample_id`/
   `moving_sample_id` from `ppline-3dcv:samples-catalog` (e.g. RIRE CT + MR, POPI lung CT pairs).
2. **Inspect.** `get_volume_info(fixed)` and `get_volume_info(moving)` — confirm
   spacing/dims/intensity are sane and the modalities are what you think.
3. **Pose first (linear).** Run `rigid` (or `advanced_rigid` if there's a large rotation
   offset) — or `affine` if scale/shear differs. This fixes gross alignment.
4. **Then non-rigid.** Run `bspline` or `demons` on the rigid-aligned result for local
   deformation. (B-spline already does an affine pre-step internally, but feeding it a
   pose-aligned volume still helps convergence.)
5. **ALWAYS QC the deformation.** `analyze_registration_deformation(...)` — verify
   `folded_fraction ≈ 0` and no negative Jacobian. If folding is detected, loosen the
   deformation (larger `grid_spacing` / higher demons `standard_deviations`) and re-run.
6. **Materialize + inspect.** `warp_volume(...)` to produce the registered volume;
   `visualize_registration(...)` to eyeball the overlay in the slicer.
7. **Deliver.** `export_volume_dicom(...)` if a DICOM ZIP is needed.

---

## Examples

### 1. Rigid CT(fixed) ← MR(moving) from samples, with extra iterations
```text
# sample ids from ppline-3dcv:samples-catalog (list_simpleitk_samples)
run_job(
  module_id="simpleitk_registration", method_id="rigid",
  sample_id="<ct_sample_id>",            # fixed  -> --input
  moving_sample_id="<mr_sample_id>",     # moving -> --moving   (DO NOT omit)
  params={"num_iterations": 200},
)
# -> output_url = MR registered into CT grid (.vti); .json sidecar has rotation_deg/translation_mm
```

### 2. Non-rigid on uploaded volumes, then deformation QC
```text
ct  = upload_dicom_folder(files=[...ct slices...])     # -> file_id
mr  = upload_dicom_folder(files=[...mr slices...])     # -> file_id

# pose first
run_job(module_id="simpleitk_registration", method_id="rigid",
        file_id=ct["file_id"], moving_file_id=mr["file_id"])

# then B-spline (non-rigid)
run_job(module_id="simpleitk_registration", method_id="bspline",
        file_id=ct["file_id"], moving_file_id=mr["file_id"],
        params={"grid_spacing": 50.0, "num_iterations": 100})

# QC — needs a loadable .tfm transform (see Transform-file gotcha)
analyze_registration_deformation(transform_file_id="<tfm_file_id>",
                                 reference_file_id=ct["file_id"])
# reject if folding_detected == true / folded_fraction > 0
```

### 3. Open the 4-panel slicer / registration studio
```text
# default = SAMPLE ids
visualize_registration(fixed="<ct_sample_id>", moving="<mr_sample_id>", method="rigid")

# OWN uploaded volumes -> flip the flags
visualize_registration(fixed=ct["file_id"], moving=mr["file_id"], method="bspline",
                       fixed_is_file_id=True, moving_is_file_id=True)
```

---

## Gotchas (read before running)

1. **MISSING `moving` ⇒ self-alignment garbage.** `simpleitk_registration` is dual-input;
   without `moving_file_id`/`moving_sample_id` every script fabricates a synthetic moving
   from the fixed volume (a known rot+trans) and "registers" that. Always pass moving.
2. **Initialization is GEOMETRY, not MOMENTS.** Aligns image geometric centers — robust
   for partial-FOV and multi-modal. MOMENTS (center-of-mass) can flip/fail; it's only used
   inside `advanced_rigid`'s coarse exhaustive search, then refined.
3. **Jacobian QC is mandatory for non-rigid.** After `bspline`/`demons` run
   `analyze_registration_deformation`; a negative Jacobian (`folded_fraction>0`,
   `folding_detected=true`) means the warp folds/tears — invalid. Increase regularization
   and re-run.
4. **The `.mha` sibling matters.** Volumes are stored as `.vti` + `.mha`. `load_volume()`
   uses the `.mha` for speed/memory. If a `.vti` has no `.mha` sibling it falls back to the
   slow 3-copy PyVista path (a real source of Cloud Run OOM). `upload_dicom_folder` writes
   both; keep them together.
5. **Transform-file gotcha (.json sidecar ≠ loadable .tfm).** Registration scripts write a
   human-readable **`.json` summary** sidecar, NOT a `.tfm`. But
   `analyze_registration_deformation` and `warp_volume` require a transform in
   `.tfm/.hdf5/.txt`. Two consequences: (a) **CompositeTransform / DisplacementField cannot
   be written as `.tfm/.hdf5`** at all (advanced_rigid, bspline, demons produce composites/
   fields) — for those you read deformation from the `.json` summary + the registered volume;
   (b) only when you have a genuinely saved single-transform `.tfm` (e.g. a plain rigid/affine
   Euler3D/Affine) will the QC/warp tools accept it. Don't pass the `.json` sidecar's URL as a
   `transform_file_id`.
6. **Order: linear pose FIRST, then non-rigid.** rigid/advanced_rigid (or affine) for gross
   pose, then bspline/demons for local deformation. Skipping pose makes non-rigid fold or
   diverge.
7. **Cloud Run nonrigid caveat (timeout, not just memory).** `bspline` and `demons` are slow
   on Cloud Run's shared/throttled vCPUs and can approach the **600 s request timeout**
   (B-spline runs an affine pre-step + single-threaded LBFGSB; demons builds a large
   displacement field). On big volumes (e.g. POPI lung 482×360×141 ≈ 24 M voxels) they may
   time out or run hot on memory. Mitigations: prefer rigid/affine when adequate; downsample
   large volumes before non-rigid; raise `run_job` `timeout_s` (capped server-side at ~540 s);
   keep the `.mha` sibling for fast loading. See skill
   `nonrigid-registration-cloudrun-diagnosis` for the full analysis.
8. **Multi-modal metric.** rigid/advanced_rigid/affine use Mattes Mutual Information (CT↔MR
   safe); bspline uses MeanSquares (intended for mono-modal / pose-aligned same-intensity
   data). For cross-modality non-rigid, get a good MI-based pose first.
9. **Coordinate order (z, y, x).** Any time you index a slice or interpret array shape,
   remember `GetArrayFromImage` is ZYX while `GetSize`/spacing/origin are XYZ.
10. **`difference_analysis` expects a registered moving.** It computes `|fixed − moving|`;
    feed it the *registered* volume (not the raw moving) or the residual is meaningless.

---

## Cross-links
- `ppline-3dcv:using-ppline` — auth, `run_job` shape, job polling.
- `ppline-3dcv:mcp-tool-reference` — full tool catalog and signatures.
- `ppline-3dcv:data-io-and-files` — file_id lifecycle, upload/download URLs.
- `ppline-3dcv:samples-catalog` — RIRE CT/MR, POPI lung CT sample ids.
- `ppline-3dcv:visualization-and-viewers` — slicer / registration studio URLs.
