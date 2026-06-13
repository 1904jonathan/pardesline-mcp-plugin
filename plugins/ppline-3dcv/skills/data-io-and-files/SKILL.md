---
name: data-io-and-files
description: >-
  How data enters and leaves the ppline-3dcv platform: upload your own files
  (upload_file, base64), reassemble a multi-slice DICOM folder (upload_dicom_folder),
  materialize built-in samples (use_sample), inspect volume geometry (get_volume_info),
  export volumes back to DICOM (export_volume_dicom), and the file_id lifecycle / output
  URLs / transform formats. Load when uploading data, handling DICOM/volumes, or
  resolving file_id / output_url questions.
---

# Data I/O and Files (ppline-3dcv)

Everything about getting data **into** the platform, knowing what `file_id` is, and getting
results **out** as downloadable URLs. For running algorithms see `ppline-3dcv:using-ppline`
(run_job/run_pipeline). For DICOM-specific QC/registration see `ppline-3dcv:medical-imaging`.
For the built-in sample catalog see `ppline-3dcv:samples-catalog`.

Grounded in: `backend/mcp_server.py`, `backend/services/file_manager.py`,
`backend/services/simpleitk_service.py`, `backend/config.py`.

---

## 1. The `file_id` model

A `file_id` is a bare UUID (string, e.g. `"3fa85f64-5717-4562-b3fc-2c963f66afa6"`). It is the
**only** handle compute tools accept for data. It carries no extension — the platform finds the
matching file on disk by stem (`get_upload_path` scans for a file whose `stem == file_id`,
extension-agnostic).

Three tools return a `file_id`, all interchangeable as `run_job(file_id=...)`:

| Tool | Source of data | Lands in | Return keys |
|---|---|---|---|
| `upload_file(filename, content_base64)` | your OWN local file | uploads dir | `file_id, filename, extension, size_bytes, message` |
| `use_sample(sample_id)` | built-in platform sample | uploads dir | `file_id, geometry_type, name, extension` |
| `upload_dicom_folder(files=[...])` | multi-slice .dcm folder | uploads dir (`.vti` + `.mha`) | `file_id, dimensions, spacing, origin, scalar_name, scalar_range, extension, geometry_type, slices_received, message` |

### Two storage areas
- **uploads** (`UPLOADS_DIR`) — inputs. `upload_file`, `use_sample`, `upload_dicom_folder`,
  and viewer-extracted `.glb` (from `generate_3d_from_image`) all write here. Found by
  `get_upload_path(file_id)`.
- **outputs** (`OUTPUTS_DIR`, served at `/api/files/outputs/<id><ext>`) — results published by
  `_publish_output()` (run_pipeline, run_project_workflow, process_image, export_volume_dicom,
  warp_volume, trellis ZIP). Each gets its own fresh `file_id`.

### Persistence + restore
Every write is mirrored to the storage backend (S3/local) via `_persist_to_storage` /
`persist_output` (best-effort: failures are swallowed in local dev). If a local file is missing,
`get_upload_path` falls back to `_restore_from_storage` (downloads it back from the backend). This
is what keeps `file_id`s alive across Cloud Run scale-to-zero restarts for files on disk/storage.

### In-memory job outputs are NOT persisted the same way
`run_job` results live in the **in-memory** `job_manager` store. A server restart loses
`job_id`s — `get_job_status('...')` then returns `{"error": "Job '...' not found (in-memory
store; lost on restart)."}`. The job's **output_url** (an `/api/files/outputs/...` link) and any
output `file_id` survive (they are real files), but the job *record* does not. Retrieve results
promptly; don't rely on polling a job hours later.

---

## 2. `upload_file` — bring your own file

```
upload_file(filename: str, content_base64: str) -> dict
```

The MCP client reads the local file, base64-encodes the **raw bytes**, and passes the original
`filename` (used only to derive the extension — the stored name is `<uuid><ext>`).

### Allowed extensions (exact list from `backend/config.py` `ALLOWED_EXTENSIONS`)
```
.ply  .pcd  .txt  .xyz  .pts  .las  .vtk  .vti  .vtu  .stl  .obj  .mha  .nrrd  .nii  .dcm
.tfm  .hdf5  .h5
```
The extension check (`validate_extension`) is **case-insensitive** (suffix is lowercased). Anything
not in this set raises `FileValidationError`.

> Geometry/volume formats plus registration transforms: `.tfm/.hdf5/.h5` were added so you
> can upload your OWN transform for `analyze_registration_deformation` / `warp_volume` (see §7);
> transforms also commonly come from a registration *run*. `.glb` is NOT accepted by
> `upload_file` (it is only produced as an output by `generate_3d_from_image`).

### Size guidance
base64 over MCP is fine up to a **few tens of MB**. For very large medical volumes prefer
`use_sample()` (no transfer) or the web UI. A single `.dcm` slice goes through `upload_file`; a
whole **folder** of slices goes through `upload_dicom_folder` (§5).

### Error / return cases
| Condition | Result |
|---|---|
| `content_base64` not valid base64 | `{"error": "content_base64 is not valid base64: ..."}` |
| decoded content empty | `{"error": "Empty file content."}` |
| extension not allowed | `{"error": "Extension '<ext>' not allowed. Accepted: ..."}` (FileValidationError) |
| any other failure | `{"error": "Upload failed: ..."}` |
| success | `{file_id, filename, extension, size_bytes, message}` |

If a `project_id` is in context (X-API-Key resolved to a project), the file is saved under that
project's `project_<id>/uploads` dir; otherwise the global uploads dir.

---

## 3. `use_sample` / `_materialize_sample` — built-in data

```
use_sample(sample_id: str) -> dict
```
Copies a built-in sample into uploads under a **fresh** `file_id` (cheap I/O, no compute).
`_materialize_sample` tries **three resolution paths in order**:

| # | Path | Matches | Source | `geometry_type` | `extension` |
|---|---|---|---|---|---|
| 1 | Open3D PLY | `SAMPLES_DIR/<id>.ply` exists | copy `.ply` | `mesh` if SAMPLE_INFO type=="mesh" else `pointcloud` | `.ply` |
| 2 | SimpleITK / PyVista **volume** | `materialize_simpleitk_sample(id)` succeeds (`sitk_*`, `pv_*` volumes) | writes `.vti` (+ `.mha` sibling) | `volume` | `.vti` |
| 3 | PyVista mesh / pcd | id found in PyVista registry, `file_path` under `DATA_DIR` exists | copy native file | `mesh` / `volume` / `pointcloud` by registry `type` | source suffix (e.g. `.vtp`, `.stl`) |

Return on success: `{file_id, geometry_type, name, extension}`.
Not found: `{"error": "Sample '<id>' not found. Use list_open3d_samples / list_pyvista_samples /
list_simpleitk_samples for valid ids."}`.

Sample ids come from the discovery tools — `list_open3d_samples`, `list_pyvista_samples`,
`list_simpleitk_samples` (see `ppline-3dcv:samples-catalog`). Do **not** guess ids.

---

## 4. Volume vs transform extension sets (used by §6–§7 tools)

Defined in `mcp_server.py`:
```
_VOLUME_EXTS    = [".vti", ".vtu", ".vtk", ".mha", ".nrrd", ".nii"]
_TRANSFORM_EXTS = [".tfm", ".hdf5", ".h5", ".txt"]
```
`_find_artifact(file_id, exts)` resolves a `file_id` to a Path by searching, in order:
`get_upload_path(file_id)` (if its suffix is in `exts`), then `UPLOADS_DIR`, `OUTPUTS_DIR`, and
`DATA_DIR/outputs` for `<file_id><ext>` for each ext. So volume/transform tools see both uploaded
inputs and published outputs.

---

## 5. `upload_dicom_folder` — reassemble a multi-slice series

```
upload_dicom_folder(files: list[dict]) -> dict
```
Use for a **whole folder** of `.dcm` slices (one 3D series). For a single file use `upload_file`.

### Payload shape
```json
[
  {"filename": "slice_0000.dcm", "content_base64": "<b64>"},
  {"filename": "slice_0001.dcm", "content_base64": "<b64>"},
  ...
]
```
Each entry = one slice. The MCP client reads the folder and base64-encodes every slice. Missing
`filename` defaults to `slice_<i>.dcm`; entries without `content_base64` are skipped. A slice with
invalid base64 aborts the whole call with `{"error": "Slice <i> ('<name>') has invalid base64: ..."}`.

### How it reassembles (SimpleITK GDCM)
Slices are written to a temp dir, then `load_dicom(folder)` runs:
1. **GDCM series detection** (`GetGDCMSeriesIDs`) — if ≥1 series with ≥2 slices, picks the series
   with the **most slices** (the main diagnostic volume, skipping localizers); retries the next
   series if a read fails.
2. **Size-grouping fallback** — if GDCM detection is insufficient (broken metadata, extensionless
   filenames), reads each file's 2D size and stacks the **largest same-size group**.
This is why mixed folders (localizer + axial stack) reconstruct cleanly.

### The `.vti` + `.mha` sibling (and WHY)
The reconstructed volume is written **twice** to uploads under the same `file_id`:
- `<file_id>.vti` (via `volume_to_vti`) — for the **web viewer** (slicer / registration studio).
- `<file_id>.mha` (via `sitk.WriteImage`) — a SimpleITK-native sibling.

**Why the `.mha` sibling:** registration / SimpleITK scripts call `load_volume()`, which for a
`.vti`/`.vtu` path **prefers a sibling `.mha` if present** — `sitk.ReadImage(.mha)` is ~3× faster
and uses ~3× less memory than the PyVista→numpy→SimpleITK conversion needed to load `.vti`. Without
the sibling it falls back to the slow PyVista loader. The returned `file_id` is the `.vti` one; the
`.mha` is found automatically by the loader. (`.mha` write is best-effort — if it fails the `.vti`
still works, just slower.)

### Return metadata (from `volume_metadata` + extras)
| key | meaning |
|---|---|
| `dimensions` | `[x, y, z]` voxel counts |
| `spacing` | `[sx, sy, sz]` voxel spacing in mm |
| `origin` | `[ox, oy, oz]` physical origin (mm) |
| `scalar_name` | `"intensity"` |
| `scalar_range` | `[min, max]` voxel intensity |
| `file_id` | the `.vti` file_id (use for run_job / visualize_registration) |
| `extension` | `".vti"` |
| `geometry_type` | `"volume"` |
| `slices_received` | count of decodable slices written to the temp dir |
| `message` | how to use it next |

Failure cases: empty `files`; `"No decodable slices in the payload."`; `"Failed to reconstruct
DICOM series: ..."`; `"Failed to convert DICOM to VTI: ..."`.

---

## 6. `get_volume_info` — inspect geometry

```
get_volume_info(file_id: str) -> dict
```
Searches `_VOLUME_EXTS` (`.vti .vtu .vtk .mha .nrrd .nii`) via `_find_artifact`, loads with
`load_volume`, and returns `volume_metadata` plus the `file_id`:

| field | meaning |
|---|---|
| `dimensions` | `[x, y, z]` voxel counts |
| `spacing` | voxel spacing in **mm** `[sx, sy, sz]` |
| `origin` | physical origin `[ox, oy, oz]` (mm) |
| `scalar_name` | `"intensity"` |
| `scalar_range` | intensity `[min, max]` |
| `file_id` | echoed back |

Not found: `{"error": "Volume not found for file_id '<id>' (looked for .vti, .vtu, .vtk, .mha,
.nrrd, .nii)."}`. Read failure: `{"error": "Failed to read volume: ..."}`.

Run this **before** registration to sanity-check that fixed/moving volumes share a sensible
geometry. Works on uploads, materialized samples, and registration **outputs** alike.

---

## 7. Transform files

Saved registration transforms (NOT volumes). Extensions `_TRANSFORM_EXTS`: `.tfm .hdf5 .h5 .txt`.

- **Where they come from:** a registration **run** produces them (`save_transform` writes `.tfm`;
  `load_transform` reads any of these via `sitk.ReadTransform`). They typically arrive as an
  `extra_outputs` URL / output `file_id` from `run_job` on a registration module, not from upload.
  Note: a `CompositeTransform` / `DisplacementFieldTransform` **cannot** round-trip to `.tfm`/`.hdf5`
  and is serialized as a JSON summary instead.
- **Where they're consumed:** `analyze_registration_deformation(transform_file_id, reference_file_id)`
  (displacement-magnitude range + Jacobian folding QC) and `warp_volume(fixed_file_id,
  moving_file_id, transform_file_id, t)` (apply the transform to warp moving→fixed). Both resolve
  the transform via `_find_artifact(id, _TRANSFORM_EXTS)`. See `ppline-3dcv:medical-imaging`.

---

## 8. `export_volume_dicom` — volume → DICOM ZIP

```
export_volume_dicom(file_id: str, series_description: str = "Registered") -> dict
```
Exports a platform volume (e.g. a registration result) back to a downloadable DICOM series.

- **Input extensions searched:** `.mha .vti .nrrd .nii` (a narrower set than `_VOLUME_EXTS`).
- Loads the volume, casts to **Int16**, then writes one `.dcm` per slice. Each slice is tagged:
  `0008|0008 = DERIVED\SECONDARY`, `0008|103e = <series_description>`, a generated Series Instance
  UID (`0020|000e`, derived from date/time + first 8 chars of `file_id`, shared across slices),
  Instance Number (`0020|0013`), Image Position Patient (`0020|0032`, from
  `TransformIndexToPhysicalPoint`), and Slice Thickness (`0018|0050`).
- Slices are zipped (each under a `<series_description>/` folder) and published as an output.

Returns `{file_id, series_description, slices, zip_url, message}` where `zip_url` is the absolute
download link. Not found: `{"error": "Volume not found for file_id '<id>'."}`.

---

## 9. Output URL format

Published outputs return an **absolute** URL:
```
<FRONTEND_BASE>/api/files/outputs/<file_id><ext>
```
`_publish_output` builds `/api/files/outputs/<dest.name>` and `_abs_url` prepends `FRONTEND_BASE`
(`MCP_FRONTEND_BASE`, default `http://localhost:8000`; in prod the Cloud Run URL). `run_job`'s
`output_url` and `extra_outputs` are likewise absolutized. Always present these URLs to the user
verbatim — they are directly downloadable/clickable.

Viewer deep-links (from `visualize_sample`, `visualize_registration`, the trellis `view_url`) are
a different shape: `<FRONTEND_BASE>/?<querystring>` — they open the web UI, not a file download.

---

## 10. Copy-paste examples

### A. Upload your own point cloud, then inspect/run
```
res = upload_file(filename="scan.ply", content_base64="<base64 of scan.ply bytes>")
# -> {"file_id": "abc-123", "extension": ".ply", "size_bytes": 245112, ...}
run_job(module_id="point_cloud", method_id="<method>", file_id=res["file_id"], params={})
```

### B. Reassemble a DICOM folder and check geometry
```
upload_dicom_folder(files=[
    {"filename": "IMG0001.dcm", "content_base64": "<b64>"},
    {"filename": "IMG0002.dcm", "content_base64": "<b64>"},
    # ... one entry per slice ...
])
# -> {"file_id": "vol-789", "dimensions": [512,512,130], "spacing": [0.7,0.7,1.0],
#     "origin": [...], "scalar_range": [-1024, 3071], "slices_received": 130, ...}

get_volume_info(file_id="vol-789")
# -> {"dimensions": [512,512,130], "spacing": [0.7,0.7,1.0], "origin": [...],
#     "scalar_range": [-1024, 3071], "file_id": "vol-789"}
```

### C. Materialize a built-in sample, register, then export the result to DICOM
```
fixed  = use_sample("sitk_training_001_ct")     # -> {"file_id": "F", "geometry_type": "volume", ...}
moving = use_sample("sitk_training_001_mr_T1")  # -> {"file_id": "M", ...}
job = run_job("simpleitk_registration", "rigid",
              file_id=fixed["file_id"], moving_file_id=moving["file_id"])
# job["output_url"] -> absolute /api/files/outputs/<id>.vti ; output file_id usable downstream
export_volume_dicom(file_id="<registered output file_id>", series_description="CT_MR_rigid")
# -> {"zip_url": "http://.../api/files/outputs/<id>.zip", "slices": 130, ...}
```

---

## 11. Gotchas

- **`file_id` has no extension.** Never append one; pass the bare UUID. The platform finds the
  file by stem (extension-agnostic for uploads; ext-specific for `_find_artifact`).
- **Allowed extensions.** `upload_file` rejects anything outside `ALLOWED_EXTENSIONS` (18 exts:
  the geometry/volume formats + `.tfm/.hdf5/.h5` transforms). `.glb` is NOT accepted (it is only
  an *output* of `generate_3d_from_image`). You CAN now upload your own `.tfm/.hdf5/.h5` transform
  for the deformation tools; they also commonly come from a registration run.
- **`use_sample` ≠ `visualize_sample`.** `use_sample` returns a `file_id` for **compute**;
  `visualize_sample`/`visualize_samples` return a viewer **URL** (and a file_id) and only handle
  Open3D PLY samples.
- **DICOM: folder vs single file.** A folder of slices → `upload_dicom_folder`; one file →
  `upload_file`. Sending a single `.dcm` as a 1-element folder works but `load_dicom` will return
  a single-slice volume.
- **The `.mha` sibling matters for speed.** If `.mha` write failed, registration on the `.vti`
  falls back to the slow PyVista loader (3× slower, 3× memory) — still correct, just slower.
- **`get_volume_info` only sees `_VOLUME_EXTS`.** A point cloud / mesh `file_id` (`.ply`, `.stl`)
  returns "Volume not found" — that's expected; it's a volume-only inspector.
- **`export_volume_dicom` searches a narrower set** (`.mha .vti .nrrd .nii`) than `get_volume_info`
  (`.vtu`/`.vtk` not exported).
- **Job records are in-memory.** Save `output_url` / output `file_id` immediately; a restart loses
  `job_id` (so `get_job_status` fails) even though the output file persists.
- **Storage persistence is best-effort.** In local dev without a configured backend, persist calls
  silently no-op; files still work locally but won't survive a fresh container with empty disk.
- **Empty / invalid base64** is the most common upload error — decode locally to confirm before
  sending; one bad slice aborts an entire `upload_dicom_folder`.
- **Output URLs are absolute & honor `MCP_FRONTEND_BASE`.** Locally they point at
  `http://localhost:8000`; in prod at the Cloud Run URL — pass them to the user as-is.
