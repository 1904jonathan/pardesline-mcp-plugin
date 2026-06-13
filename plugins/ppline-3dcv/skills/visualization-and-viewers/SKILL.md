---
name: visualization-and-viewers
description: >-
  Open results in the platform's browser viewers via the ppline-3dcv MCP server:
  visualize_sample / visualize_samples (full-screen MeshLab-style 3D viewer for point
  clouds & meshes) and visualize_registration (4-panel MPR slicer / registration studio
  for CT/MR volumes), plus the exact deep-link URL grammar these tools return and how to
  present them. Load when the user wants to SEE a sample, mesh, point cloud, volume, or a
  registration overlay.
---

# Visualization & viewers (ppline-3dcv)

The platform has a browser frontend. The MCP server cannot "show" anything itself — instead,
each visualization tool **prepares the data server-side and returns a deep-link URL**. Your
job is to call the right tool and **hand the returned URL to the user as a clickable link**.
Opening that URL boots the frontend straight into the correct viewer with the data preloaded.

> All URLs are absolute and built from `FRONTEND_BASE` (env `MCP_FRONTEND_BASE`). In the
> deployed plugin this is the production Cloud Run URL; in local dev it defaults to
> `http://localhost:8000`. The tool already returns the full absolute URL — do not rewrite it.

---

## The two viewer modes

| Mode | What it shows | Driven by | Deep-link marker | Frontend entry point |
|------|---------------|-----------|------------------|----------------------|
| **Object viewer** (full-screen MeshLab-style) | Point clouds & meshes (PLY/GLB/OBJ/STL) | `visualize_sample`, `visualize_samples` (also `generate_3d_from_image` → `view_url`) | `?view=<file_id>...` | `openViewer()` |
| **Registration studio / slicer** (4-panel MPR) | Medical CT/MR/DICOM volumes (.vti), fixed + optional moving overlay | `visualize_registration` (also `warp_volume` → `view_url`) | `?reg=1&fixed=...` | `openRegistrationStudio()` + `RegistrationStudio.loadVolumes()` |

In the frontend's `init()` (app.js) the `?reg=` deep-link is checked **first and takes
precedence**; only if `reg` is absent does it fall back to the `?view=` object viewer. So a
single URL drives exactly one mode.

---

## Deep-link URL grammar (exact, from mcp_server.py)

### Object viewer — single object
Built by `visualize_sample`:

```
{FRONTEND_BASE}/?view=<file_id>&ext=.ply&type=<mesh|pointcloud>&name=<display name>&sample=<sample_id>
```

Query params (`urlencode`d):

| Param | Meaning | Example |
|-------|---------|---------|
| `view` | the uploads `file_id` to load (the sample is copied into uploads first) | `view=3f2a...` |
| `ext` | file extension to load it as | `ext=.ply` |
| `type` | geometry type — `mesh` or `pointcloud` | `type=mesh` |
| `name` | display name shown in the object list | `name=Stanford+Bunny` |
| `sample` | originating sample id (metadata only) | `sample=bunny` |

### Object viewer — multiple objects (one scene)
Built by `visualize_samples`: the **same five params, each a comma-joined list** zipped per
index by the frontend, so one link loads several objects into the SAME scene:

```
{FRONTEND_BASE}/?view=<id1>,<id2>&ext=.ply,.ply&type=mesh,pointcloud&name=Bunny,Sphere&sample=bunny,sphere
```

How `app.js init()` consumes it: it reads `view`, splits on `,` to get the id list, then
splits `ext`/`type`/`name`/`sample` and uses a `pick(arr, i, dflt)` helper — per-item value
falls back to `arr[0]`, then to a default (`.ply` / `undefined` / `'Model'`). So lists may be
shorter than the id list; missing entries inherit the first value. The frontend loads each
spec sequentially into the existing scene (no clear between items) and frames all objects, then
rewrites history to `/?view=<id1>,<id2>`.

> The `generate_3d_from_image` tool (Trellis image→3D) returns the same single-object form with
> `type=mesh&name=Trellis+3D` as `view_url`. See `ppline-3dcv:ai-3d-generation`.

### Registration studio / slicer
Built by `visualize_registration`:

```
{FRONTEND_BASE}/?reg=1&fixed=<file_id>&fixedName=<name>&method=<method>[&moving=<file_id>&movingName=<name>]
```

| Param | Meaning |
|-------|---------|
| `reg` | always `1` — selects registration mode (takes precedence over `view`) |
| `fixed` | file_id of the fixed (background, gray) volume — must be slicer-loadable (.vti) |
| `fixedName` | display name for the fixed volume |
| `method` | pre-selects the method dropdown (see method list below) |
| `moving` | (optional) file_id of the moving (overlay) volume |
| `movingName` | (optional) display name for the moving volume |

How `app.js init()` consumes it: if `params.get('reg')` is truthy it calls
`openRegistrationStudio()` then `registrationStudio.loadVolumes({ fixedFileId, fixedName,
movingFileId, movingName, method })`, reading exactly `fixed` / `fixedName` / `moving` /
`movingName` / `method`. `loadVolumes()` sets the method dropdown, loads the fixed volume as the
gray slicer background, then adds the moving volume as a cyan overlay. The file_ids **must
already exist server-side as slicer-loadable .vti volumes** — the tool guarantees this by
materializing samples or validating uploaded file_ids before building the URL.

> `warp_volume` returns the same `?reg=1...` form as `view_url`, overlaying the warped result
> (`movingName=warped (t=...)`) on the fixed volume. See `ppline-3dcv:medical-imaging`.

---

## Tools

### `visualize_sample(sample_id)` — one object, full-screen
- **Input**: `sample_id` — an **Open3D PLY** sample id from `list_open3d_samples()` (see
  `ppline-3dcv:samples-catalog`), e.g. `bunny`, `armadillo`.
- **Side effect**: copies the sample PLY into uploads under a fresh `file_id`
  (`_copy_sample_to_uploads`) and best-effort persists it to storage. Cheap I/O, no compute.
- **Returns**: `{ sample_id, file_id, geometry_type, url, message }`. `geometry_type` is
  `mesh` if the sample is a mesh, else `pointcloud`.
- **On bad id**: returns `{ error, available: [...] }` listing valid sample ids.

### `visualize_samples(sample_ids)` — several objects, one scene
- **Input**: `sample_ids` — a **list** of Open3D PLY sample ids. Use this instead of calling
  `visualize_sample` repeatedly so all objects land in the SAME viewer scene.
- **Side effect**: copies each found sample into uploads (one file_id each).
- **Returns**: `{ objects: [{sample_id, file_id, geometry_type, name}], missing: [...], url,
  message }`. A single comma-list URL. Each object keeps its own geometry type.
- **On all-missing**: returns `{ error, missing, available }`.

> Both object-viewer tools only accept **Open3D PLY** sample ids (they look for
> `SAMPLES_DIR/<id>.ply`). They do not visualize PyVista/SimpleITK samples — for medical
> volumes use `visualize_registration`.

### `visualize_registration(fixed, moving=None, method="rigid", fixed_is_file_id=False, moving_is_file_id=False)`
Opens one or two volumes in the 4-panel MPR registration studio (fixed = gray background,
moving = overlay).

- **`fixed` / `moving`** are by **default treated as SAMPLE ids** (`list_simpleitk_samples()` /
  PyVista volumes), e.g. `sitk_training_001_ct`, `sitk_training_001_mr_T1`. Each is
  materialized into a slicer-loadable `.vti` file_id (`_resolve_volume` → `_materialize_sample`).
- **To visualize the developer's OWN uploaded volume**, pass its `file_id` and set
  `fixed_is_file_id=True` / `moving_is_file_id=True`. The file must already exist in uploads and
  be slicer-loadable (`.vti`, e.g. produced by `upload_dicom_folder` — see
  `ppline-3dcv:medical-imaging`). The tool validates existence with `get_upload_path`.
- **`method`** pre-selects the registration method in the UI dropdown. Valid values:
  `rigid` | `advanced_rigid` | `affine` | `bspline` | `demons` | `difference_analysis`.
  (It only sets the dropdown; it does not run registration. Run it from the studio's "Run
  Registration" button, or programmatically via `run_job` on `simpleitk_registration` — see
  `ppline-3dcv:medical-imaging`.)
- **`moving` is optional**: omit it to open a single volume in the slicer.
- **Returns**: `{ fixed, moving, method, url, message }` (`moving` is `null` if not given).
- **On error**: `{ error: "Fixed volume: ..." }` / `{ error: "Moving volume: ..." }`.

> Usage is metered best-effort (no tier gating). The other viz tools are pure I/O and not
> metered.

---

## Object viewer capabilities (MeshLab-style)

The full-screen object viewer is a multi-object scene with an object list, gizmo, and toolbar.

**Keyboard shortcuts** (active when not typing in an input/textarea/select — from
`KeyboardManager.js`):

| Key | Action |
|-----|--------|
| `A` | Frame all objects |
| `F` | Frame selected object |
| `R` | Reset view |
| `W` | Translate gizmo mode |
| `E` | Rotate gizmo mode |
| `H` | Toggle visibility of selected object(s) |

**Toolbar buttons** (`ViewerToolbar.js`, top-left): Frame All (A), Frame Selected (F), Reset
View (R), Translate (W, toggle), Rotate (E, toggle), Export PLY, Export OBJ.

**Other capabilities** (per the platform): per-object list panel with select / frame /
estimate-normals; multi-select (Ctrl-click) with a shared gizmo; point clouds auto-estimate
normals for nicer shading; a "← Home" exit button. The chat widget can also drive scene
actions (opacity, color, render mode, point size, normals, bbox, frame, export).

---

## Registration studio / slicer capabilities

A full-page 4-panel **MPR** (multi-planar reconstruction) layout (`SlicerLayout.js`,
`ViewerModeManager.js`):

```
┌───────────────┬───────────────┐
│   SAGITTAL    │    CORONAL    │   axis 0 (X, red) │ axis 1 (Y, green)
├───────────────┼───────────────┤
│     AXIAL     │   3D VOLUME   │   axis 2 (Z, blue)│ raycast volume render
└───────────────┴───────────────┘
```

| Capability | Detail (from code) |
|------------|--------------------|
| Crosshair sync | Left-click / drag on any slice panel moves the crosshair; all 3 views stay in sync (`CrosshairSync`). |
| Scroll navigation | Mouse wheel on a slice panel steps that slice by one voxel. |
| Slice sliders | Per-panel range slider; label shows `X/Y/Z: idx/max (mm)` using volume dimensions + spacing. |
| Fixed vs overlay | `volumes[0]` = FIXE (background, **gray**); overlays are radio-selected; one alpha slider blends FIXE↔overlay. |
| Colormaps (auto) | `AUTO_COLORMAPS = ['gray', 'cyan', 'orange']` — index 0 FIXE gray, index 1 moving cyan, index 2+ (registered) orange. Full colormap dropdown also available (continuous + categorical). |
| Blend modes | Overlay, Checkerboard, Difference. |
| Swap A/B | Swap FIXE and the active overlay roles (e.g. show MRI as background, CT as overlay). |
| W/L presets | Full Range; **CT** Soft Tissue / Bone / Lung / Brain; **MRI** T1 / T2 / FLAIR / DWI / ADC; PET. (CT = linear HU windowing; MRI = percentile-stretched non-linear contrast modes.) |
| Measurement | Ruler tool with a per-volume source picker + measurements table. |
| Header (studio) | Fixed / Moving pickers, Method dropdown, Run Registration, Logs, DICOM export, Theory, Save, Reset, Exit. |
| DICOM export | Exports a completed registration result as a DICOM ZIP. |

> Note: the moving overlay colormap is **cyan** in current code (`AUTO_COLORMAPS[1]` and
> `RegistrationStudio._acceptInput('moving', ..., 'cyan')`), not green. The panel border
> accent colors (red/green/blue) are separate from the volume colormaps.

---

## Examples

**1 — Show a single sample full-screen**
```
visualize_sample("bunny")
→ { url: "<FRONTEND_BASE>/?view=<id>&ext=.ply&type=mesh&name=Stanford%20Bunny&sample=bunny", ... }
```
Present: "Here's the Stanford Bunny in the 3D viewer: <url>". Tell the user they can press
`A` to frame all, `F` to frame the selection, `W`/`E` for the move/rotate gizmo.

**2 — Compare two samples in one scene**
```
visualize_samples(["bunny", "armadillo"])
→ one comma-list URL loading both objects into the same scene
```

**3 — Open a CT + MR overlay in the slicer with bspline pre-selected**
```
visualize_registration(
    fixed="sitk_training_001_ct",
    moving="sitk_training_001_mr_T1",
    method="bspline",
)
→ { url: "<FRONTEND_BASE>/?reg=1&fixed=<ct_id>&fixedName=...&method=bspline&moving=<mr_id>&movingName=...", ... }
```
Present the URL and note the CT is the gray background, the MR is the cyan overlay, and the
method dropdown is set to B-spline; the user clicks "Run Registration" in the studio (or you
run it via `run_job` on `simpleitk_registration`).

**4 — Visualize the user's own uploaded volume**
```
# after upload_dicom_folder(...) returned file_id=ABC (a .vti)
visualize_registration(fixed="ABC", fixed_is_file_id=True)
```

---

## Gotchas

- **Always return the URL to the user as a clickable link.** The MCP server cannot render the
  view; the user must open the link. The tool's `message` field already contains a ready phrasing.
- **Do not hand-craft these URLs** — call the tool so the data is copied/materialized
  server-side first. A `?view=` or `?reg=` link pointing at a file_id that was never prepared
  will fail to load.
- **Object viewer ⇄ slicer are mutually exclusive per link** — `?reg=` wins over `?view=`.
- **`visualize_sample(s)` is Open3D-PLY-only.** For PyVista/SimpleITK volumes use
  `visualize_registration` (single-volume form). For PyVista meshes there is no direct viz tool
  — run them through compute and view the output, or use the web UI.
- **`fixed_is_file_id` defaults to False** — if you pass an uploaded file_id without setting it
  True, the tool will try to treat it as a sample id and fail with "not found".
- **The moving volume must be slicer-loadable (.vti).** Raw `.dcm`/`.mha`-only uploads should go
  through `upload_dicom_folder` (which writes a `.vti`) before being passed as a file_id.
- **`method` only sets the dropdown** — it does not execute registration.
- **In-memory / scale-to-zero**: deep-links reference files persisted to storage; they survive,
  but registration jobs you start are in-memory (lost on server restart) — see
  `ppline-3dcv:medical-imaging`.

## See also
- `ppline-3dcv:samples-catalog` — valid sample ids for every viz tool.
- `ppline-3dcv:medical-imaging` — DICOM upload, registration, `warp_volume`, deformation QC.
- `ppline-3dcv:ai-3d-generation` — `generate_3d_from_image` and its `view_url`.
- `ppline-3dcv:mcp-tool-reference` — the full tool catalog.
