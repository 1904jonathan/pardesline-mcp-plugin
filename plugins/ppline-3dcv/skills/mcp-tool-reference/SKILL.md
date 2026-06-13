---
name: mcp-tool-reference
description: >-
  Complete API reference for ALL 34 ppline-3dcv MCP tools + 2 resources: exact
  signatures, every parameter (type/default/meaning), the exact return-dict keys, error
  patterns, auth (X-API-Key), metering, file_id lifecycle, blocking/timeout behavior, and
  absolute output-URL format. Load this when you need the precise signature, return shape,
  or error behavior of any ppline-3dcv tool (run_job, run_pipeline, upload_file, project
  CRUD, process_image, generate_3d_from_image, DICOM/deformation tools, visualize_*).
---

# ppline-3dcv MCP Tool Reference

The `ppline-3dcv` MCP server (FastMCP name `productpardesline-3dcv`) exposes the
ProductPardesLine 3D computer-vision / medical-imaging platform over **Streamable
HTTP**, mounted into the FastAPI app at **`/mcp`**. It provides **34 tools** and
**2 resources**.

This file is the **scannable index + universal conventions**. For the exhaustive
per-tool detail (exact signature, every return key, every error string, side
effects, copy-paste example), see **[reference.md](reference.md)**.

The server config (from the code):
- `stateless_http=True`, `json_response=True` (plain JSON, no SSE), endpoint at `/mcp/`.
- DNS-rebinding Host/Origin validation is **disabled** (`enable_dns_rebinding_protection=False`) — required behind Cloud Run, auth is enforced by `X-API-Key` instead.

---

## Tool index (34 tools, grouped by category)

### Discovery (10)
| Tool | One-line | Detail |
|------|----------|--------|
| `list_modules()` | Full catalog of classical 3D-CV modules + methods + params | [reference.md](reference.md#list_modules) |
| `get_module_info(module_id)` | One module's methods, params, defaults, I/O formats | [reference.md](reference.md#get_module_info) |
| `list_models()` | Training-oriented deep-learning model-skills (PointNet, VoxelMorph, ...) | [reference.md](reference.md#list_models) |
| `get_model_info(model_id)` | One model-skill's metadata + data_format contract | [reference.md](reference.md#get_model_info) |
| `list_open3d_samples()` | Built-in Open3D point-cloud/mesh PLY samples | [reference.md](reference.md#list_open3d_samples) |
| `list_pyvista_samples()` | PyVista mesh/volume samples | [reference.md](reference.md#list_pyvista_samples) |
| `list_simpleitk_samples()` | SimpleITK medical samples (RIRE CT/MR, POPI, ...) | [reference.md](reference.md#list_simpleitk_samples) |
| `list_expert_topics()` | Curated `context://expert/{topic}` topics actually present | [reference.md](reference.md#list_expert_topics) |
| `list_image_processing_methods()` | 2D AI methods on the GCP image-processing service | [reference.md](reference.md#list_image_processing_methods) |
| `list_trellis_methods()` | Trellis image→3D methods (L4 GPU service) | [reference.md](reference.md#list_trellis_methods) |

### Data input (3)
| Tool | One-line | Detail |
|------|----------|--------|
| `upload_file(filename, content_base64)` | Upload your own local file → `file_id` | [reference.md](reference.md#upload_file) |
| `use_sample(sample_id)` | Materialize a built-in sample → `file_id` | [reference.md](reference.md#use_sample) |
| `upload_dicom_folder(files)` | Reassemble a multi-slice DICOM folder → volume `file_id` | [reference.md](reference.md#upload_dicom_folder) |

### Compute (4)
| Tool | One-line | Detail |
|------|----------|--------|
| `run_job(module_id, method_id, ...)` | Run ONE module, **block** until done, return result | [reference.md](reference.md#run_job) |
| `get_job_status(job_id)` | Poll a job (only when run_job returned `running`) | [reference.md](reference.md#get_job_status) |
| `run_pipeline(steps, ...)` | Run a LINEAR multi-step chain, block until done | [reference.md](reference.md#run_pipeline) |
| `run_project_workflow(project_id, ...)` | Run a project's SAVED node-editor DAG | [reference.md](reference.md#run_project_workflow) |

### Project management (8)
| Tool | One-line | Detail |
|------|----------|--------|
| `list_projects()` | All projects (id, name, has_api_key, has_workflow) | [reference.md](reference.md#list_projects) |
| `create_project(name)` | Create a project (+ on-disk dirs) | [reference.md](reference.md#create_project) |
| `get_project(project_id)` | One project's metadata | [reference.md](reference.md#get_project) |
| `delete_project(project_id)` | Delete project + on-disk data (irreversible) | [reference.md](reference.md#delete_project) |
| `get_project_workflow(project_id)` | Load the saved workflow JSON | [reference.md](reference.md#get_project_workflow) |
| `save_project_workflow(project_id, workflow)` | Save the node-editor workflow JSON | [reference.md](reference.md#save_project_workflow) |
| `generate_project_api_key(project_id)` | Generate/regenerate the `pl_...` key | [reference.md](reference.md#generate_project_api_key) |
| `revoke_project_api_key(project_id)` | Revoke the project key | [reference.md](reference.md#revoke_project_api_key) |

### AI compute on GCP (2)
| Tool | One-line | Detail |
|------|----------|--------|
| `process_image(image_base64, filename, method, ...)` | 2D AI on one/two images → PNG/ZIP URL | [reference.md](reference.md#process_image) |
| `generate_3d_from_image(image_base64, ...)` | Image → 3D `.glb` via Trellis (L4 GPU) | [reference.md](reference.md#generate_3d_from_image) |

### Medical: DICOM I/O + deformation (4)
| Tool | One-line | Detail |
|------|----------|--------|
| `get_volume_info(file_id)` | Volume geometry: dims, spacing, origin, intensity range | [reference.md](reference.md#get_volume_info) |
| `export_volume_dicom(file_id, series_description)` | Volume → zipped downloadable DICOM series | [reference.md](reference.md#export_volume_dicom) |
| `analyze_registration_deformation(transform_file_id, reference_file_id, grid_spacing)` | Displacement + Jacobian folding QC | [reference.md](reference.md#analyze_registration_deformation) |
| `warp_volume(fixed_file_id, moving_file_id, transform_file_id, t)` | Warp moving into fixed space at interp `t` | [reference.md](reference.md#warp_volume) |

### Visualize (3)
| Tool | One-line | Detail |
|------|----------|--------|
| `visualize_sample(sample_id)` | Open one Open3D sample in full-screen viewer (URL) | [reference.md](reference.md#visualize_sample) |
| `visualize_samples(sample_ids)` | Open several Open3D samples in one scene (URL) | [reference.md](reference.md#visualize_samples) |
| `visualize_registration(fixed, moving, method, ...)` | Open volumes in the 4-panel registration studio (URL) | [reference.md](reference.md#visualize_registration) |

**Count check:** Discovery 10 + Data input 3 + Compute 4 + Projects 8 + AI 2 + Medical 4 + Visualize 3 = **34**.

### Resources (2)
| Resource | One-line | Detail |
|----------|----------|--------|
| `context://expert/{topic}` | Curated 3D-CV expert markdown (allowlisted topics) | [reference.md](reference.md#resource-contextexperttopic) |
| `context://model/{model_id}` | A model-skill's knowledge layer (`models/<id>/SKILL.md`) | [reference.md](reference.md#resource-contextmodelmodel_id) |

---

## Universal conventions

These apply to **every** tool. The per-tool blocks in `reference.md` do not repeat them.

### Authentication (X-API-Key)
- Auth is enforced by `ApiKeyMiddleware` on the MCP ASGI app.
- Send the project key in **either**:
  - the `X-API-Key` header, **or**
  - the `Authorization: Bearer <key>` header (the middleware reads `bearer` and strips the prefix).
- Keys have the form `pl_<32 hex chars>` (`pl_` prefix; generated as `pl_` + first 32 chars of `sha256(token_bytes(32)).hexdigest()`).
- Validation order (`_validate_key`): **DB first** (`Project.api_key` column, written by `generate_project_api_key` / the UI), then **fallback** to the legacy `backend/data/projects.json` file (`validate_api_key`, which additionally requires the `pl_` prefix).
- **401 responses** (JSON body):
  - Missing key → `{"error": "Missing X-API-Key header. Generate one in your project settings."}`, status `401`.
  - Invalid key → `{"error": "Invalid API key. Check your key or generate a new one."}`, status `401`.
- **`MCP_REQUIRE_API_KEY`** env var (default `true`): when set to `false`/`0`/`no`, auth is bypassed entirely (every request passes, anonymous). Used for local testing.
- When auth is off (or no key), there is **no current project**, so metering is silently skipped (see below) and uploads go to the **global** dirs (no `project_id`).

### Metering (best-effort, no tier gating)
- After a key validates, the middleware stashes `{id, name}` in a `ContextVar` (`_current_project`).
- Compute/produce-style tools call `_meter()` → `increment_api_usage(project_id)`, which bumps `api_usage_count` and sets `api_last_used` in `projects.json`.
- It is **best-effort**: wrapped in try/except, never raises, and there is **NO tier/quota gating** — metering never blocks a call.
- If there is no current project (auth off / file missing), metering is a no-op.
- Which tools meter is documented per-tool in `reference.md` (broadly: `run_job`, `run_pipeline`, `run_project_workflow`, `visualize_registration`, `process_image`, `generate_3d_from_image`, `upload_dicom_folder`, `export_volume_dicom`, `analyze_registration_deformation`, `warp_volume`). Pure discovery/upload/project-CRUD tools do **not** meter.

### file_id lifecycle
- A **`file_id`** is a UUID (string) naming a file on disk **without** its extension; lookups are extension-agnostic (`get_upload_path` matches by `p.stem == file_id`).
- **Uploads** (`upload_file`, `use_sample`, `upload_dicom_folder`, the `.glb` from `generate_3d_from_image`, and materialized samples) live in `UPLOADS_DIR` (or `DATA_DIR/project_<id>/uploads` when a project is active) and are mirrored to the storage backend (local / S3 / GCS). `get_upload_path` searches global uploads, then every `project_*/uploads`, then restores from the storage backend.
- **Outputs** (`run_pipeline`, `run_project_workflow`, `process_image`, `generate_3d_from_image` ZIP, `export_volume_dicom`, `warp_volume`) are published into `OUTPUTS_DIR` under a fresh UUID and persisted to storage; their URL is `/api/files/outputs/<file_id><ext>` (made absolute — see below).
- **`run_job` outputs** are keyed by the **`job_id`** (the GLB/raw/volume artifact is `<job_id>.glb` or `<job_id><ext>`); sidecars (`.json` matrix, `.tfm`, `.hdf5`) are exposed in `extra_outputs`.
- **Jobs are in-memory** (`JobManager._jobs` dict). A server restart (Cloud Run scale-to-zero!) **loses all jobs** — `get_job_status` then returns `{"error": "Job '...' not found (in-memory store; lost on restart)."}`. Files persist; the Job object does not.
- A volume `file_id` can be resolved across uploads **and** outputs by `_find_artifact` (used by `get_volume_info`, `export_volume_dicom`, `analyze_registration_deformation`, `warp_volume`), searching `UPLOADS_DIR`, `OUTPUTS_DIR`, and `DATA_DIR/outputs` for a matching extension.

### Blocking model + `timeout_s` cap (~540 s) + the `running` fallback
- `run_job`, `run_pipeline`, `run_project_workflow` **block** (submit + poll) and return the final result in **one** call.
- `timeout_s` (default **540**) is **clamped to `[10, 540]`** (`max(10, min(int(timeout_s), 540))`). 540 s stays under the Cloud Run 600 s request budget. The `_COMPUTE_DEFAULT_TIMEOUT_S = 540` ceiling cannot be exceeded even if you pass a larger value.
- Poll interval is **0.5 s** (`_COMPUTE_POLL_S`).
- **Fallback shapes when the wall-clock cap is hit:**
  - `run_job` → `{"job_id", "status": "running", "message": "Job still running after <t>s. Call get_job_status('<job_id>') ..."}`. The job keeps running in the background; recover it via `get_job_status` (if the server hasn't restarted).
  - `run_pipeline` / `run_project_workflow` → `{"status": "running", "error": "Pipeline still running after <t>s (no result handle ... re-run with a larger timeout_s or fewer steps)."}`. There is **NO** recovery handle for standalone workflows — you must re-run.
- `generate_3d_from_image` uses its own `timeout_s` (default **480**), clamped to **`[60, 540]`** (`max(60, min(int(timeout_s), 540))`), and retries on `503` GPU cold-start (sleep 15 s) / transient errors (sleep 10 s); on exhaustion → `{"status": "timeout", "error": "...", }`.

### Absolute output-URL format
- Relative `/api/...` URLs are made absolute by `_abs_url`: `f"{FRONTEND_BASE}{url}"` when the URL starts with `/`.
- `FRONTEND_BASE` = env `MCP_FRONTEND_BASE` (default `http://localhost:8000`), trailing slash stripped. In production this is the Cloud Run URL.
- Downloadable artifacts: `<FRONTEND_BASE>/api/files/outputs/<id><ext>`.
- Viewer deep-links (from `visualize_*`, `warp_volume`, `generate_3d_from_image`): `<FRONTEND_BASE>/?<urlencoded query>`. Present these to the user as clickable links.

### The `/mcp` trailing-slash rule
- The Streamable-HTTP endpoint lives at **`/mcp/`** (trailing slash). A bare `/mcp` would 405.
- `McpSlashNormalizer` (pure-ASGI middleware on the parent app) rewrites a request whose path is exactly `/mcp` to `/mcp/`, so the URL works **with or without** the trailing slash.

### Error convention
- Tools do **not** raise to the client; on failure they return a dict with an **`"error"`** key (string). Many also include extra context keys (e.g. `available`, `missing`). Always check for `"error"` in the returned dict before using a result.
