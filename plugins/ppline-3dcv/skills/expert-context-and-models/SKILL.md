---
name: expert-context-and-models
description: >-
  The FREE knowledge layer of the ppline-3dcv MCP server: 14 curated 3D-CV expert
  context resources (context://expert/{topic}) and the deep-learning model-skills
  (context://model/{model_id}). Read the relevant expert resource BEFORE writing
  library/platform code (Open3D, PyVista, VTK, SimpleITK, Three.js, GLSL, registration,
  node-pipeline, architecture, devops), and the model resource before training a model.
---

# Expert Context & Model-Skills (the free knowledge layer)

The `ppline-3dcv` MCP server (`productpardesline-3dcv`) exposes two kinds of **MCP
resources** that cost nothing to read and exist to make you write correct code on the
first try instead of guessing library APIs:

1. **`context://expert/{topic}`** — 14 curated, hand-written 3D computer-vision
   domain-expert documents (the platform's own `*-expert.md` skill files).
2. **`context://model/{model_id}`** — deep-learning model-skills: the full
   architecture + training recipe + "bring your own data" contract for each reference
   model (currently PointNet).

These are **read-only resources** (MCP `resources/read`), distinct from the **tools**
(`run_job`, `run_pipeline`, `process_image`, ...) which actually execute compute. The
knowledge layer is **FREE**; compute tools are **metered** (best-effort
`increment_api_usage`, no tier-gating yet). Read the knowledge first, then compute.

## WHY read these before coding

The MCP server's own `INSTRUCTIONS` (returned at session init) say it directly:

> "Before writing code, read the relevant expert context resource ... Use
> `list_expert_topics()` to see what is actually available."

Each `*-expert.md` is a dense cheat-sheet of the **exact** API calls, parameter
defaults, coordinate-system gotchas and ordering rules for one library or subsystem —
grounded in how this platform actually uses it. Reading
`context://expert/simpleitk` before writing registration code, or
`context://expert/glsl-shader` before touching a volume-rendering shader, replaces
guessing with authoritative reference and avoids the classic mistakes (wrong axis
order, MOMENTS vs GEOMETRY init, missing `--moving`, etc.).

Rule of thumb: **if you are about to write code in one of the 14 domains below, read
that expert resource first.** If you are about to TRAIN/FINE-TUNE a model, read its
`context://model/<id>` first.

## The 14 expert topics (`context://expert/{topic}`)

`CURATED_TOPICS` in `backend/mcp_server.py` is an explicit **allowlist** (not a glob),
so project-internal notes (deploy status, auth, secrets, session logs) can never leak —
only these 14 reusable, domain-knowledge files are served.

| topic (resource id) | What it covers / when to read it |
|---|---|
| `open3d` | Open3D point-cloud & mesh API: load/downsample/outlier-removal, normal & FPFH estimation, ICP (point-to-point/plane), mesh simplify/smooth/watertight checks. Read before any Open3D point-cloud or mesh code. |
| `pyvista` | PyVista (Pythonic VTK): read/save many formats (.vtk/.vti/.vtu/.stl/.ply/.mha/.nrrd), decimate/subdivide/smooth/clean/fill-holes/boolean, volume contour/slice/threshold. Read before mesh analysis or volumetric visualization in PyVista. |
| `vtk` | Raw VTK data model & pipeline: dataset hierarchy (vtkImageData volumes, vtkPolyData surfaces/point clouds, unstructured grids), PointData/CellData, filters, readers/writers, PyVista interop. Read when working below PyVista or debugging VTK objects. |
| `simpleitk` | SimpleITK medical imaging: read/write MHA/NRRD/NII/DICOM-series, pixel types & casting, the **(z,y,x)** numpy axis order, and **physical (mm) coordinate systems** (origin+spacing+direction). Read before any CT/MR/registration/resampling code. |
| `mesh-processing` | MeshLab-style repair & reconstruction: manifold/watertight/Euler fundamentals, the standard repair pipeline ordering (dedup → degenerate → non-manifold → fill holes → orient normals), remeshing, format conversion. Read before mesh cleaning/repair. |
| `threejs` | Three.js WebGL viewers: renderer/scene/camera setup, color space & tone mapping, rendering meshes vs point clouds, camera controls, volume rendering UIs. Read before frontend 3D-viewer code. |
| `glsl-shader` | GLSL ES 3.00 for WebGL/Three.js: shader structure, uniforms/attributes, ray marching, colormaps, custom materials — focused on volume rendering & medical imaging (W/L). Read before writing/editing shaders. |
| `3d-file-format` | File-format & dataset engineering: per-format capability tables (PLY/PCD/XYZ/PTS/LAS/E57 for clouds; mesh formats), binary protocols, conversion pipelines, dataset registries & sample generation. Read before format conversion or dataset wiring. |
| `node-pipeline` | Node-based / Simulink-style DAG systems: node/edge/port model, topological sort, dataflow execution engines. Read before touching the node editor or workflow executor (the `run_pipeline` / `run_project_workflow` substrate). |
| `slicer-integration` | 3D Slicer Python API integration: load volumes/segmentations/models, volume exchange with SimpleITK/VTK, spatial transforms, segmentation workflows. Read before Slicer interop. |
| `medical-registration` | THIS platform's CT/MRI registration pipeline end-to-end: NodeEditor dual-input wiring (fixed `input` port / moving `input_t` port), `/api/process` payload, slicer visualization, the 6 methods. Read before debugging/extending registration. |
| `frontend-architecture` | Frontend architecture for visualization-heavy apps: no-framework class-based components, state management, interaction patterns, responsive layouts. Read before frontend structure/refactor work. |
| `backend-architecture` | Python/FastAPI backend architecture: app factory & middleware, routers (upload/processing/modules/projects), async job pipelines, module registry, file management. Read before backend structure/endpoint work. |
| `devops-infrastructure` | DevOps for scientific 3D apps: multi-stage Dockerfiles (libGL/cmake deps), CI/CD, env reproducibility, deployment & GPU compute. Read before Docker/Cloud Run/deploy work. |

**`list_expert_topics()` is the source of truth at runtime.** It returns only the
topics whose `*-expert.md` file is actually present on the running server
(`_expert_topics()` filters `CURATED_TOPICS` by file existence). Always call it instead
of assuming all 14 are live.

### Production bundling caveat (important)

The expert files live in the repo at `.claude/commands/<topic>-expert.md`. In
`backend/mcp_server.py`, `CONTEXT_DIR` defaults to `PROJECT_ROOT/.claude/commands`, but
that directory is **excluded from the Docker build** (`.dockerignore` / `.gcloudignore`).
So on the deployed Cloud Run instance, `context://expert/...` and `list_expert_topics()`
may return **empty / "not deployed"** unless `MCP_CONTEXT_DIR` is set to a bundled copy.

- If `list_expert_topics()` returns `[]` in prod, the expert layer is not bundled — fall
  back to the corresponding local plugin skill (the same knowledge is mirrored as
  `*-expert` skills available locally) or set `MCP_CONTEXT_DIR`.
- Model-skills (`context://model/<id>`) do **not** have this problem: `models/` ships in
  the Docker image, so model resources work in prod.

## How to read a resource

Use the MCP client's resource-read capability (`resources/read`) against the URI:

- Expert: `context://expert/simpleitk`, `context://expert/glsl-shader`, etc.
- Model: `context://model/pointnet`.

In Claude Code, read MCP resources via the `ReadMcpResourceTool` (server
`productpardesline-3dcv`/`ppline-3dcv`, URI = the `context://...` string);
`ListMcpResourcesTool` enumerates what the server advertises. You can also discover the
live topic list with the `list_expert_topics()` **tool** and the model list with
`list_models()` before reading the corresponding resource.

Server behavior (from `expert_context()` / `model_skill()` in `backend/mcp_server.py`):

- A non-curated `topic` returns a helpful message listing the available topics (no
  traversal possible — only the allowlist is served).
- A missing-but-curated topic returns `"Context file for '<topic>' is not deployed
  (check MCP_CONTEXT_DIR)."`.
- An unknown `model_id` returns the list of valid model ids; a model with no SKILL.md
  returns a "compute-only card" message.

## The model-skills layer (`context://model/{model_id}`)

Distinct from the classical algorithm modules (`list_modules`, the Open3D/PyVista/
SimpleITK operations run by `run_job`), model-skills are **training-oriented reference
models**. Each gives you the exact architecture, hyper-parameters, data-format contract
and non-obvious gotchas to TRAIN/FINE-TUNE the model on your own data.

The registry (`backend/processing/model_registry.py`) **auto-discovers** any folder
under `models/` that contains a `model.json` card (folders starting with `_`, e.g.
`_schema`, are ignored). Adding a skill = dropping a folder with `model.json` +
`SKILL.md`; no code change required.

### Discovery → metadata → knowledge (the 3-step flow)

1. **`list_models()`** — catalog of all model-skills.
2. **`get_model_info(model_id)`** — metadata for one model.
3. **Read `context://model/<id>`** — the full SKILL.md: architecture, training recipe,
   data contract, gotchas. **Read this before helping a developer train/fine-tune.**

### Model-registry fields (`to_api_response()`)

Each entry returned by `list_models()` / `get_model_info()` carries:

| field | meaning |
|---|---|
| `id` | model id (e.g. `pointnet`); use it for `get_model_info` and `context://model/<id>`. |
| `name` | human name (e.g. "PointNet"). |
| `description` | one-line summary of the skill. |
| `use_case` | what you'd train it for on YOUR data. |
| `pillar` | which 3D-DL pillar it belongs to (e.g. `pointcloud_lidar`). |
| `task` | primary task (e.g. `classification`). |
| `framework` | DL framework (e.g. `pytorch`). |
| `license` | model/code license (e.g. `MIT`). |
| `papers` | key reference papers (title/year/url). |
| `category` / `icon` | UI grouping (`neural` / `brain`). |
| `hardware` | training hardware + rough time/accuracy expectation. |
| `data_format` | the **bring-your-own-data contract**: task variants, input shape, label format, folder layout. |
| `has_skill` | whether a knowledge-layer `SKILL.md` exists (→ `context://model/<id>` is readable). |
| `has_reference_impl` | whether a runnable `reference/train.py` ships in the folder. |
| `has_sample_data` | whether correctly-formatted synthetic `sample_data/` ships (prove training runs before plugging in your own data). |

(`ModelDescriptor` also tracks `skill`, `reference_impl`, `sample_data`,
`pretrained_weights`, `order`; `skill_path` / `reference_path` / `sample_data_path`
resolve these safely inside the model's own folder with path-traversal guards.)

### Currently available model: `pointnet`

From `models/pointnet/model.json` (and its `SKILL.md`):

- **name / task / framework**: PointNet — `classification` — `pytorch` (`license` MIT,
  `pillar` `pointcloud_lidar`).
- **use_case**: train a classifier or per-point segmenter on **your own** point-cloud
  dataset (proprietary objects/scans, few classes, limited labels).
- **hardware**: 1 GPU 8 GB, ~1–2 h to ~89% on ModelNet40 (1024 pts, 200 epochs).
- **data_format contract**: task ∈ `classification | part_segmentation |
  semantic_segmentation`; input = point cloud `N×3` xyz (optional `N×6` with normals);
  labels = one int class id per cloud (cls) or one int label per point (seg); layout =
  folder of `.ply`/`.npy` clouds + `labels.csv` (cls) or matching `.npy` label arrays
  (seg).
- **ships**: `reference/train.py` (`has_reference_impl`) and synthetic `sample_data/`
  (`has_sample_data`) so you can prove the trainer runs before using real data.
- **SKILL.md** teaches the architecture (T-Nets for input/feature alignment, shared
  MLP + symmetric max-pool for permutation invariance, local⊕global concat for
  segmentation, the `‖I − AAᵀ‖²` orthogonality regularizer) plus exact hyper-parameters
  and convergence gotchas. Read `context://model/pointnet` before writing any training
  code.

### Cross-link: training workflow

For the end-to-end **training/fine-tuning workflow** (how to combine `list_models` →
`get_model_info` → read SKILL → bring your data → run the reference trainer), use the
sibling skill **`ppline-3dcv:deep-learning-models`**. This skill is the reference for
the knowledge layer; that one drives the workflow.

## Gotchas & rules

- **Read before advising.** Don't answer library/API questions from memory when a
  matching `context://expert/<topic>` exists — read it first; it encodes this platform's
  exact conventions and defaults.
- **Knowledge is free, compute is metered.** Reading `context://expert/*` and
  `context://model/*` costs nothing; tools like `run_job`/`run_pipeline`/`process_image`/
  `generate_3d_from_image` call `increment_api_usage` (best-effort metering). Read first,
  then compute.
- **Check what's live.** `list_expert_topics()` (not the static list of 14) tells you
  which expert resources the running server actually serves.
- **Prod bundling.** Expert context may be unavailable on the deployed server unless
  `MCP_CONTEXT_DIR` points at a bundled copy (`.claude/` is excluded from the image).
  Model-skills are unaffected (`models/` ships in the image).
- **Allowlist only.** Only the 14 curated topics are served; requesting any other topic
  (or attempting path traversal) returns a guidance message, never file contents.
