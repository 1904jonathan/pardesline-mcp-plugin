# ppline-3dcv MCP Tool Reference — Exhaustive Detail

Authoritative per-tool reference for all **34 tools** + **2 resources** of the
`ppline-3dcv` MCP server. Every return key and error string below is copied from
the actual server code (`backend/mcp_server.py`) and the services it calls. Read
[SKILL.md](SKILL.md) first for the universal conventions (auth, metering, file_id
lifecycle, blocking/timeout, absolute URLs) — they are **not** repeated in each
block.

Notation: each block lists the **exact signature** (Python types + defaults), each
**parameter**, the **success return keys**, the **error shapes**, **side effects**
(metering / file creation), and an example. Where a tool delegates to a service
(e.g. `volume_metadata`, the GCP microservices), the exact extra keys depend on
that service's response and are noted as such.

---

## Discovery

### list_modules
```python
list_modules() -> list[dict]
```
- **Params:** none.
- **Returns:** `registry.to_api_response()` — a list, one dict per processing module (point cloud, mesh, registration, lidar, `simpleitk_registration`, ...). Each module dict includes its `id`, `methods` (each with `method_id`/`id`, parameters + defaults, input/output formats) and the `dual_input` flag. Use the `id`/`method_id` values as `module_id`/`method_id` elsewhere.
- **Errors:** none (always returns the catalog list).
- **Side effects:** none. No metering.
- **Example:** `list_modules()`

### get_module_info
```python
get_module_info(module_id: str) -> dict
```
- **Params:** `module_id` — id from `list_modules()`.
- **Returns (success):** the single module dict from `registry.to_api_response()` whose `id == module_id` (same shape as one entry of `list_modules`).
- **Errors:** `{"error": "Module '<module_id>' not found. Call list_modules() for valid ids."}`
- **Side effects:** none. No metering.
- **Example:** `get_module_info(module_id="simpleitk_registration")`

### list_models
```python
list_models() -> list[dict]
```
- **Params:** none.
- **Returns:** `model_registry.to_api_response()` — one dict per deep-learning model-skill, each with keys: `id`, `name`, `description`, `use_case`, `pillar`, `task`, `framework`, `license`, `papers` (list), `category`, `icon`, `hardware`, `data_format` (dict), `has_skill` (bool), `has_reference_impl` (bool), `has_sample_data` (bool). Sorted by the model's `order`.
- **Errors:** none.
- **Side effects:** none. No metering.
- **Example:** `list_models()`

### get_model_info
```python
get_model_info(model_id: str) -> dict
```
- **Params:** `model_id` — id from `list_models()`.
- **Returns (success):** the single model dict (same keys as a `list_models()` entry) whose `id == model_id`.
- **Errors:** `{"error": "Model '<model_id>' not found. Call list_models() for valid ids."}`
- **Side effects:** none. No metering. For the full training knowledge read `context://model/<model_id>`.
- **Example:** `get_model_info(model_id="pointnet")`

### list_open3d_samples
```python
list_open3d_samples() -> list[dict]
```
- **Params:** none.
- **Returns:** list of dicts, one per Open3D sample whose `<id>.ply` exists in `SAMPLES_DIR`. Keys: `id`, `name`, `type`, `category` (defaults to `"primitive"`).
- **Errors:** none (empty list if none present).
- **Side effects:** none. No metering.
- **Example:** `list_open3d_samples()`

### list_pyvista_samples
```python
list_pyvista_samples() -> list[dict]
```
- **Params:** none.
- **Returns:** list of PyVista registry entries whose `file_path` exists under `DATA_DIR`. Each entry is the raw registry dict (includes at least `id`, `name`, `type`, `file_path`; exact keys come from the PyVista sample registry).
- **Errors:** none.
- **Side effects:** none. No metering.
- **Example:** `list_pyvista_samples()`

### list_simpleitk_samples
```python
list_simpleitk_samples() -> list[dict]
```
- **Params:** none.
- **Returns:** `load_sitk_registry(DATA_DIR)` — the SimpleITK sample registry list (RIRE CT/MR, POPI lung CT, liver segmentations, ...). Each entry carries the sample `id` (e.g. `sitk_training_001_ct`, `sitk_training_001_mr_T1`) and metadata from the registry.
- **Errors:** none.
- **Side effects:** none. No metering.
- **Example:** `list_simpleitk_samples()`

### list_expert_topics
```python
list_expert_topics() -> list[str]
```
- **Params:** none.
- **Returns:** list of curated topic strings whose `<topic>-expert.md` file exists in `CONTEXT_DIR`. The full allowlist (`CURATED_TOPICS`): `open3d`, `pyvista`, `vtk`, `simpleitk`, `mesh-processing`, `threejs`, `glsl-shader`, `3d-file-format`, `node-pipeline`, `slicer-integration`, `medical-registration`, `frontend-architecture`, `backend-architecture`, `devops-infrastructure`. Only those actually present on disk are returned (may be empty if `CONTEXT_DIR`/`MCP_CONTEXT_DIR` is not deployed).
- **Errors:** none.
- **Side effects:** none. No metering.
- **Example:** `list_expert_topics()`

### list_image_processing_methods
```python
async list_image_processing_methods() -> dict
```
- **Params:** none.
- **Behavior:** `GET {IMAGE_PROCESSING_URL}/methods` with a Cloud Run identity-token `Authorization` header (httpx, timeout 120 s). `IMAGE_PROCESSING_URL` default `https://ppline-image-processing-565128781631.europe-west1.run.app`.
- **Returns (success):** the remote service's JSON (`r.json()`) — the method catalog + parameters (shape defined by that microservice).
- **Errors:** `{"error": "Image-processing service unavailable: <exception>"}` (any failure, incl. non-2xx via `raise_for_status`).
- **Side effects:** none. No metering.
- **Example:** `list_image_processing_methods()`

### list_trellis_methods
```python
async list_trellis_methods() -> dict
```
- **Params:** none.
- **Behavior:** `GET {TRELLIS_URL}/methods` with identity-token auth (httpx, timeout 300 s). `TRELLIS_URL` default `https://ppline-trellis-565128781631.europe-west4.run.app`. GPU service has cold starts (~60–120 s when scaled to zero).
- **Returns (success):** the remote service's JSON (`r.json()`).
- **Errors:** `{"error": "Trellis service unavailable: <exception>"}`
- **Side effects:** none. No metering.
- **Example:** `list_trellis_methods()`

---

## Data input

### upload_file
```python
async upload_file(filename: str, content_base64: str) -> dict
```
- **Params:**
  - `filename` — original filename; its extension determines validation + storage suffix.
  - `content_base64` — the file bytes, base64-encoded (validated with `validate=True`).
- **Allowed extensions** (`ALLOWED_EXTENSIONS`): `.ply .pcd .txt .xyz .pts .las .vtk .vti .vtu .stl .obj .mha .nrrd .nii .dcm`. (Base64 over MCP is fine up to a few tens of MB; for large medical volumes prefer `use_sample` or the web UI.)
- **Returns (success):** `{"file_id", "filename", "extension", "size_bytes", "message"}` where `message` = `"Uploaded '<filename>' as file_id=<id>. Pass it to run_job(file_id=...)."`. (`file_id`/`filename`/`extension`/`size_bytes` come from `save_upload`'s metadata.)
- **Errors:**
  - `{"error": "content_base64 is not valid base64: <e>"}`
  - `{"error": "Empty file content."}`
  - `{"error": "<FileValidationError message>"}` — e.g. `"Extension '<ext>' not allowed. Accepted: <sorted list>"`.
  - `{"error": "Upload failed: <e>"}` (any other exception).
- **Side effects:** writes `<file_id><ext>` into the uploads dir (project dir if a project is active, else global `UPLOADS_DIR`) **and** mirrors it to the storage backend. **No metering.**
- **Example:** `upload_file(filename="scan.ply", content_base64="<base64>")`

### use_sample
```python
use_sample(sample_id: str) -> dict
```
- **Params:** `sample_id` — id from `list_open3d_samples`, `list_pyvista_samples`, or `list_simpleitk_samples`.
- **Behavior:** `_materialize_sample` resolves the sample in this order: (1) Open3D `<id>.ply`, (2) SimpleITK/PyVista volume via `materialize_simpleitk_sample` (→ `.vti`), (3) PyVista registry entry (mesh/pointcloud/volume). Copies it into uploads under a fresh `file_id` and mirrors to storage.
- **Returns (success):** `{"file_id", "geometry_type", "name", "extension"}`. `geometry_type` ∈ `{"mesh", "pointcloud", "volume"}`; `extension` e.g. `.ply` / `.vti` / source suffix.
- **Errors:**
  - `{"error": "Sample '<id>' not found. Use list_open3d_samples / list_pyvista_samples / list_simpleitk_samples for valid ids."}`
  - `{"error": "Failed to materialize sample '<id>': <e>"}` (SimpleITK path failure).
- **Side effects:** creates an upload `file_id`. **No metering.**
- **Example:** `use_sample(sample_id="bunny")`

### upload_dicom_folder
```python
async upload_dicom_folder(files: list[dict]) -> dict
```
- **Params:** `files` — list of `{"filename": str, "content_base64": str}`, **one entry per `.dcm` slice**. Each `content_base64` is base64-validated; entries without `content_base64` are skipped; `filename` defaults to `slice_<i>.dcm`.
- **Behavior:** writes slices to a temp dir, reconstructs with SimpleITK GDCM (`load_dicom`), converts to `.vti` (`volume_to_vti`), and **also** writes a `.mha` sibling (same `file_id`) for fast registration. Both are mirrored to storage. (For a SINGLE file use `upload_file`.)
- **Returns (success):** the `volume_metadata(volume)` dict (dimensions, spacing, origin, intensity range — exact keys from `volume_metadata`) **merged with**: `{"file_id", "extension": ".vti", "geometry_type": "volume", "slices_received": <int>, "message": "DICOM series loaded as file_id=<id>. Use it with run_job / visualize_registration."}`.
- **Errors:**
  - `{"error": "Provide a non-empty list of {filename, content_base64} slices."}`
  - `{"error": "Slice <i> ('<name>') has invalid base64: <e>"}`
  - `{"error": "No decodable slices in the payload."}`
  - `{"error": "Failed to reconstruct DICOM series: <e>"}`
  - `{"error": "Failed to convert DICOM to VTI: <e>"}`
- **Side effects:** creates `<file_id>.vti` + `<file_id>.mha` uploads. **Meters** (`_meter()` on success).
- **Example:** `upload_dicom_folder(files=[{"filename":"s0.dcm","content_base64":"..."}, ...])`

---

## Compute

### run_job
```python
async run_job(
    module_id: str,
    method_id: str,
    file_id: str | None = None,
    sample_id: str | None = None,
    moving_file_id: str | None = None,
    moving_sample_id: str | None = None,
    params: dict | None = None,
    timeout_s: int = 540,
) -> dict
```
- **Params:**
  - `module_id`, `method_id` — from `list_modules` / `get_module_info`.
  - **Primary input (provide exactly one):** `file_id` (an upload) **or** `sample_id` (a built-in sample, materialized automatically).
  - **Moving input (dual-input modules only):** `moving_file_id` **or** `moving_sample_id`. Dual-input modules include registration (`simpleitk_registration`, `registration`, `deformable_registration`). Fixed → `--input`, moving → `--moving`.
  - `params` — the method's parameter dict; defaults used when omitted.
  - `timeout_s` — wall-clock blocking cap, clamped to `[10, 540]`.
- **Behavior:** validates the method exists (`registry.get_method`) and its `script_path` exists; resolves inputs to local paths; `job_manager.submit(...)`; **meters**; then polls every 0.5 s up to `timeout_s` for `COMPLETED`/`FAILED`.
- **Returns (success, via `_job_result`):** `{"job_id", "module_id", "method_id", "status", "output_type"}` plus conditionally: `"output_url"` (absolute, downloadable — present when set), `"extra_outputs"` (dict of sidecar name → absolute URL: keys `matrix_json` / `transform_tfm` / `transform_hdf5`), `"error"` (only on a FAILED job), `"logs_tail"` (last ≤15 cleaned log lines). `status` is `"completed"` or `"failed"`; `output_type` ∈ `{"glb", "ply", "volume"}`.
- **Returns (timeout fallback):** `{"job_id", "status": "running", "message": "Job still running after <t>s. Call get_job_status('<job_id>') to retrieve the result."}` — the job keeps running; recover via `get_job_status`.
- **Errors:**
  - `{"error": "Method '<method_id>' not found in module '<module_id>'. Call get_module_info('<module_id>') for valid methods."}`
  - `{"error": "Processing script missing for <module_id>/<method_id>."}`
  - `{"error": "Provide a primary input: file_id (upload) or sample_id."}`
  - `{"error": "Uploaded file not found: <file_id>. Re-upload via upload_file()."}` (input/moving resolution).
  - `{"error": "Sample '<id>' not found. ..."}` / `{"error": "Failed to materialize sample '<id>'."}` (sample resolution).
- **Side effects:** creates a job (in-memory) + output artifacts keyed by `job_id` in `OUTPUTS_DIR` (persisted to storage). **Meters** once at submit.
- **Example:** `run_job(module_id="simpleitk_registration", method_id="rigid", sample_id="sitk_training_001_ct", moving_sample_id="sitk_training_001_mr_T1", params={})`

### get_job_status
```python
get_job_status(job_id: str) -> dict
```
- **Params:** `job_id` — from a `run_job` that returned `status: "running"`.
- **Returns (success):** the **same shape as `run_job`** (`_job_result`): `job_id`, `module_id`, `method_id`, `status`, `output_type`, optional `output_url` / `extra_outputs` / `error` / `logs_tail`.
- **Errors:** `{"error": "Job '<job_id>' not found (in-memory store; lost on restart)."}` — jobs are in-memory; a server restart (Cloud Run scale-to-zero) loses them.
- **Side effects:** none. No metering.
- **Example:** `get_job_status(job_id="<uuid>")`

### run_pipeline
```python
async run_pipeline(
    steps: list[dict],
    file_id: str | None = None,
    sample_id: str | None = None,
    timeout_s: int = 540,
) -> dict
```
- **Params:**
  - `steps` — **ordered** list of `{"module_id": str, "method_id": str, "params"?: dict}`. Wires a LINEAR chain `input → step1 → step2 → ...`. `params` optional (defaults used).
  - **Primary input (one of):** `file_id` or `sample_id`.
  - `timeout_s` — clamped to `[10, 540]` (applied inside `_execute_workflow_dict` via `asyncio.wait_for`).
- **Behavior:** builds a workflow `{blocks, edges}` (a `file-input` block + one `process` block per step, chained by edges) and runs it through the standalone `WorkflowExecutor`. **Single input per step** — for dual-input registration use `run_job` instead. Publishes the final artifact.
- **Returns (success):** `{"status": "completed", "steps": "<mod.meth -> mod.meth ...>", "output_url": "<absolute>", "output_file_id": "<uuid>", "output_type": "<final suffix without dot>", "message": "Pipeline finished. Download: <url>"}`.
- **Returns (timeout fallback):** `{"status": "running", "error": "Pipeline still running after <t>s (no result handle for standalone workflows — re-run with a larger timeout_s or fewer steps)."}` — **no recovery handle; re-run.**
- **Errors:**
  - `{"error": "Provide at least one step: [{module_id, method_id, params?}]."}`
  - `{"error": "Provide a primary input: file_id (upload) or sample_id."}`
  - `{"error": "Step <i> is missing module_id / method_id."}`
  - `{"error": "Step <i>: method '<meth>' not found in module '<mid>'. Call get_module_info('<mid>') for valid methods."}`
  - `{"error": "Uploaded file not found: <file_id>. ..."}` / sample resolution errors.
  - `{"error": "Pipeline execution failed: <e>"}` (executor raised).
- **Side effects:** creates a `wf_<hex>` working dir under `OUTPUTS_DIR` and publishes the final output (new `output_file_id`, persisted to storage). **Meters** on completion / timeout / failure (`_meter()` is called in all three `_execute_workflow_dict` paths).
- **Example:** `run_pipeline(steps=[{"module_id":"point_cloud","method_id":"voxel_downsample","params":{"voxel_size":0.05}},{"module_id":"mesh","method_id":"poisson"}], sample_id="bunny")`

### run_project_workflow
```python
async run_project_workflow(
    project_id: str,
    file_id: str | None = None,
    sample_id: str | None = None,
    timeout_s: int = 540,
) -> dict
```
- **Params:**
  - `project_id` — from `list_projects()`; the project must have a saved workflow (from the web editor or `save_project_workflow`).
  - **Primary input (one of):** `file_id` or `sample_id`.
  - `timeout_s` — clamped to `[10, 540]`.
- **Behavior:** loads `project.workflow` from the DB and runs it via the same `WorkflowExecutor` (mirrors `/api/execute`).
- **Returns (success):** identical to `run_pipeline` success: `{"status": "completed", "steps": "project:<name or id>", "output_url", "output_file_id", "output_type", "message"}`.
- **Returns (timeout fallback):** identical to `run_pipeline` (`{"status": "running", "error": "Pipeline still running after <t>s ..."}`).
- **Errors:**
  - `{"error": "Project '<project_id>' not found. Call list_projects()."}`
  - `{"error": "Project '<project_id>' has no saved workflow. Build one in the web editor or via save_project_workflow()."}`
  - primary-input errors (same as `run_pipeline`).
  - `{"error": "Pipeline execution failed: <e>"}`.
- **Side effects:** publishes a new output `file_id`. **Meters** (via `_execute_workflow_dict`).
- **Example:** `run_project_workflow(project_id="<uuid>", file_id="<upload uuid>")`

---

## Project management

> All project tools open a fresh DB session (`SessionLocal`). The serializer `_project_dict(p)` returns `{"id", "name", "created_at" (ISO or null), "has_api_key" (bool), "has_workflow" (bool — true when the workflow has a non-empty `blocks` list)}`. None of these meter.

### list_projects
```python
list_projects() -> list[dict]
```
- **Params:** none.
- **Returns:** list of `_project_dict` (see above), ordered by `created_at` descending.
- **Errors:** none.
- **Example:** `list_projects()`

### create_project
```python
create_project(name: str) -> dict
```
- **Params:** `name` — non-empty (stripped) project name.
- **Returns (success):** `_project_dict` of the new project (`id`, `name`, `created_at`, `has_api_key`=false, `has_workflow`=false).
- **Errors:** `{"error": "Project name cannot be empty."}`
- **Side effects:** inserts a `Project` row (`user_id="anonymous"`) and creates `DATA_DIR/project_<id>/uploads` and `.../outputs` on disk.
- **Example:** `create_project(name="Lung registration study")`

### get_project
```python
get_project(project_id: str) -> dict
```
- **Params:** `project_id`.
- **Returns (success):** `_project_dict`.
- **Errors:** `{"error": "Project '<project_id>' not found."}`
- **Example:** `get_project(project_id="<uuid>")`

### delete_project
```python
delete_project(project_id: str) -> dict
```
- **Params:** `project_id`.
- **Returns (success):** `{"status": "deleted", "id": "<project_id>"}`.
- **Errors:** `{"error": "Project '<project_id>' not found."}`
- **Side effects:** **irreversible** — deletes the DB row and `rmtree`s `DATA_DIR/project_<id>` (guarded to stay inside `DATA_DIR`).
- **Example:** `delete_project(project_id="<uuid>")`

### get_project_workflow
```python
get_project_workflow(project_id: str) -> dict
```
- **Params:** `project_id`.
- **Returns (success):** `{"project_id": "<id>", "workflow": <the stored workflow JSON or null>}` (workflow shape: `{blocks: [...], edges: [...]}`).
- **Errors:** `{"error": "Project '<project_id>' not found."}`
- **Example:** `get_project_workflow(project_id="<uuid>")`

### save_project_workflow
```python
save_project_workflow(project_id: str, workflow: dict) -> dict
```
- **Params:**
  - `project_id`.
  - `workflow` — `{blocks: [...], edges: [...]}` (must be a dict containing a `"blocks"` key; same shape `get_project_workflow` returns / the web editor produces). This is what `run_project_workflow` executes.
- **Returns (success):** `{"status": "saved", "id": "<project_id>", "blocks": <len of blocks list>}`.
- **Errors:**
  - `{"error": "workflow must be a dict with at least a 'blocks' list."}`
  - `{"error": "Project '<project_id>' not found."}`
- **Side effects:** updates `project.workflow` in the DB.
- **Example:** `save_project_workflow(project_id="<uuid>", workflow={"blocks":[{"id":"input","type":"file-input"},{"id":"step1","type":"process","moduleId":"mesh","methodId":"poisson","params":{}}],"edges":[{"from":{"nodeId":"input"},"to":{"nodeId":"step1"}}]})`

### generate_project_api_key
```python
generate_project_api_key(project_id: str) -> dict
```
- **Params:** `project_id`.
- **Behavior:** sets `project.api_key = "pl_" + sha256(token_bytes(32)).hexdigest()[:32]`. Regenerating **invalidates the old key**.
- **Returns (success):** `{"api_key": "pl_...", "project_id": "<id>", "project_name": "<name>"}` — the key is returned **in full**; store it.
- **Errors:** `{"error": "Project '<project_id>' not found."}`
- **Side effects:** writes the new key to the DB.
- **Example:** `generate_project_api_key(project_id="<uuid>")`

### revoke_project_api_key
```python
revoke_project_api_key(project_id: str) -> dict
```
- **Params:** `project_id`.
- **Behavior:** sets `project.api_key = None`. Calls authenticating with the old key are then rejected (401).
- **Returns (success):** `{"status": "revoked", "project_id": "<id>"}`.
- **Errors:** `{"error": "Project '<project_id>' not found."}`
- **Side effects:** clears the key in the DB.
- **Example:** `revoke_project_api_key(project_id="<uuid>")`

---

## AI compute on GCP

> Both proxy external Cloud Run services with service-to-service identity-token auth (`_gcp_headers` chooses `image_processing._auth_headers` vs `trellis._auth_headers` by URL). Results are saved on the platform and returned as downloadable URLs.

### process_image
```python
async process_image(
    image_base64: str,
    filename: str,
    method: str,
    params: dict | None = None,
    image2_base64: str | None = None,
    filename2: str | None = None,
) -> dict
```
- **Params:**
  - `image_base64` — first image bytes, base64 (validated).
  - `filename` — first image filename.
  - `method` — a method id from `list_image_processing_methods()`.
  - `params` — the method's JSON parameter dict (default `{}`; sent as JSON string).
  - `image2_base64`, `filename2` — optional second image (some methods take two; `filename2` defaults to `"image2.png"`).
- **Behavior:** `POST {IMAGE_PROCESSING_URL}/process` (multipart `file`/`file2` + `method`+`params`; httpx timeout 300 s). Result content type decides extension: ZIP if `zip` in content-type (two-input methods), PNG if `image`, else `.bin`. The result is published to outputs.
- **Returns (success):** `{"method", "output_url" (absolute), "output_file_id", "content_type", "message": "Result saved. Download: <url>"}`. If the service set the `X-Result-Info` header, `"result_info"` is added (parsed JSON if possible, else the raw string).
- **Errors:**
  - `{"error": "image_base64 is not valid base64: <e>"}`
  - `{"error": "Empty image content."}`
  - `{"error": "image2_base64 is not valid base64: <e>"}`
  - `{"error": "Image processing failed (<status>): <response text>"}` (HTTP non-2xx).
  - `{"error": "Image-processing service error: <e>"}` (other failure).
- **Side effects:** publishes an output `file_id` (persisted). **Meters** on success.
- **Example:** `process_image(image_base64="<b64>", filename="cell.png", method="segment", params={})`

### generate_3d_from_image
```python
async generate_3d_from_image(
    image_base64: str,
    filename: str = "input.png",
    method: str = "trellis_generate",
    params: dict | None = None,
    timeout_s: int = 480,
) -> dict
```
- **Params:**
  - `image_base64` — image bytes, base64 (validated).
  - `filename` — default `"input.png"`.
  - `method` — default `"trellis_generate"`.
  - `params` — JSON parameter dict (default `{}`).
  - `timeout_s` — overall deadline, **clamped to `[60, 540]`**. Retries on `503` (GPU cold start, sleep 15 s) and transient errors (sleep 10 s) until the deadline.
- **Behavior:** `POST {TRELLIS_URL}/process` (multipart). On success the response is a ZIP (glb + preview mp4); the ZIP is published, and the `.glb` is extracted into uploads as a viewable file with a viewer deep-link.
- **Returns (success):** `{"zip_url" (absolute), "attempts": <int>}` plus, when a `.glb` is found in the ZIP: `"model_file_id"`, `"view_url"` (`<FRONTEND_BASE>/?view=<glb_id>&ext=.glb&type=mesh&name=Trellis 3D`), `"message": "3D model ready — open in viewer: <view_url>"`. If extraction fails: `"warning": "Could not extract .glb from ZIP: <e>"` (zip_url still present).
- **Errors:**
  - `{"error": "image_base64 is not valid base64: <e>"}`
  - `{"error": "Empty image content."}`
  - `{"error": "Trellis generation failed (<status>): <response text>"}` (non-503 HTTP error).
  - `{"status": "timeout", "error": "Trellis did not return within <deadline>s (last: <last_err>). Retry with a larger timeout_s."}`
- **Side effects:** publishes the ZIP output `file_id`; creates an uploads `<glb_id>.glb`. **Meters** on success (after the ZIP is received).
- **Example:** `generate_3d_from_image(image_base64="<b64>", filename="chair.png")`

---

## Medical: DICOM I/O + deformation

> Volume/transform file_ids are resolved across uploads + outputs by `_find_artifact`. Volume extensions (`_VOLUME_EXTS`): `.vti .vtu .vtk .mha .nrrd .nii`. Transform extensions (`_TRANSFORM_EXTS`): `.tfm .hdf5 .h5 .txt`.

### get_volume_info
```python
get_volume_info(file_id: str) -> dict
```
- **Params:** `file_id` — a volume from `upload_file` / `upload_dicom_folder` / `use_sample` / a registration output.
- **Returns (success):** the `volume_metadata(...)` dict (dimensions, voxel spacing mm, origin, intensity range — exact keys from `simpleitk_service.volume_metadata`) **plus** `"file_id": <file_id>`.
- **Errors:**
  - `{"error": "Volume not found for file_id '<id>' (looked for .vti, .vtu, .vtk, .mha, .nrrd, .nii)."}`
  - `{"error": "Failed to read volume: <e>"}`
- **Side effects:** none. No metering.
- **Example:** `get_volume_info(file_id="<volume uuid>")`

### export_volume_dicom
```python
export_volume_dicom(file_id: str, series_description: str = "Registered") -> dict
```
- **Params:**
  - `file_id` — a volume (resolved among `_VOLUME_EXTS`: `.vti .vtu .vtk .mha .nrrd .nii`, same set as `get_volume_info`; non-image grids fail gracefully in the load/cast step).
  - `series_description` — DICOM Series Description (default `"Registered"`); also used in the ZIP folder name.
- **Behavior:** casts to `Int16`, writes one `.dcm` per slice (with derived metadata + computed slice origins/UIDs), zips them, publishes the ZIP.
- **Returns (success):** `{"file_id", "series_description", "slices": <volume depth>, "zip_url" (absolute), "message": "DICOM series exported. Download: <zip_url>"}`.
- **Errors:**
  - `{"error": "Volume not found for file_id '<id>'."}`
  - `{"error": "Failed to load volume: <e>"}`
  - `{"error": "DICOM export failed: <e>"}`
- **Side effects:** publishes a ZIP output `file_id`. **Meters** on success.
- **Example:** `export_volume_dicom(file_id="<volume uuid>", series_description="Registered MR")`

### analyze_registration_deformation
```python
analyze_registration_deformation(
    transform_file_id: str,
    reference_file_id: str,
    grid_spacing: int = 4,
) -> dict
```
- **Params:**
  - `transform_file_id` — a saved transform (`.tfm`/`.hdf5`/`.h5`/`.txt`).
  - `reference_file_id` — the fixed volume defining the space (volume exts).
  - `grid_spacing` — sampling grid spacing for the displacement field (default `4`).
- **Behavior:** loads volume + transform, extracts the displacement field, computes the Jacobian determinant on the **central axial slice** (`axis=2, slice_pos=0.5, sample_spacing=2`), counts folded voxels (`Jacobian ≤ 0`).
- **Returns (success):** `{"displacement_magnitude_mm": {"min", "max"}, "sampled_points": <int>, "jacobian_range": {"min", "max"}, "folded_fraction": <round 4dp>, "folding_detected": <bool, jacobian min ≤ 0>, "slice": "central axial", "message": <"Negative Jacobian detected — the deformation folds/tears in places (check regularization)." | "Deformation is diffeomorphic on the sampled slice (no folding)."> }`.
- **Errors:**
  - `{"error": "Reference volume not found for '<id>'."}`
  - `{"error": "Transform not found for '<id>' (looked for .tfm, .hdf5, .h5, .txt)."}`
  - `{"error": "Failed to load data: <e>"}`
  - `{"error": "Failed to analyze deformation: <e>"}`
- **Side effects:** none on disk. **Meters** on success.
- **Example:** `analyze_registration_deformation(transform_file_id="<job uuid>", reference_file_id="<fixed uuid>", grid_spacing=4)`

### warp_volume
```python
warp_volume(
    fixed_file_id: str,
    moving_file_id: str,
    transform_file_id: str,
    t: float = 1.0,
) -> dict
```
- **Params:**
  - `fixed_file_id`, `moving_file_id` — volumes (volume exts).
  - `transform_file_id` — the transform (`.tfm`/`.hdf5`/`.h5`/`.txt`).
  - `t` — interpolation in `[0, 1]`; `t=1` = fully registered (default `1.0`).
- **Behavior:** `compute_warped_volume(...)`, saves the warped volume as a `.vti` output, returns a registration-studio deep-link overlaying it on the fixed volume.
- **Returns (success):** `{"warped_file_id", "t", "output_url" (absolute `.vti`), "view_url" (`<FRONTEND_BASE>/?reg=1&fixed=<fixed_file_id>&fixedName=fixed&moving=<warped_file_id>&movingName=warped (t=<t>)`), "message": "Warped volume saved (file_id=<id>). View overlay: <view_url>"}`.
- **Errors:**
  - `{"error": "Fixed volume not found for '<id>'."}`
  - `{"error": "Moving volume not found for '<id>'."}`
  - `{"error": "Transform not found for '<id>'."}`
  - `{"error": "Failed to warp volume: <e>"}`
  - `{"error": "Failed to save warped volume: <e>"}`
- **Side effects:** creates `<warped_file_id>.vti` in `OUTPUTS_DIR` (persisted). **Meters** on success.
- **Example:** `warp_volume(fixed_file_id="<ct>", moving_file_id="<mr>", transform_file_id="<tfm>", t=1.0)`

---

## Visualize

> These return clickable URLs (present them to the user). Sample-based ones copy data into uploads.

### visualize_sample
```python
visualize_sample(sample_id: str) -> dict
```
- **Params:** `sample_id` — an Open3D sample (from `list_open3d_samples`); a `<sample_id>.ply` must exist in `SAMPLES_DIR`.
- **Behavior:** copies the sample into uploads under a fresh `file_id`, builds a full-screen MeshLab-viewer deep-link.
- **Returns (success):** `{"sample_id", "file_id", "geometry_type" ("mesh"/"pointcloud"), "url" (`<FRONTEND_BASE>/?view=<file_id>&ext=.ply&type=<geo>&name=<name>&sample=<sample_id>`), "message": "Open this link to view '<name>' full-screen in the platform: <url>"}`.
- **Errors:** `{"error": "Sample '<sample_id>' not found.", "available": [<existing open3d sample ids>]}`
- **Side effects:** creates an upload `file_id`. **No metering.**
- **Example:** `visualize_sample(sample_id="bunny")`

### visualize_samples
```python
visualize_samples(sample_ids: list[str]) -> dict
```
- **Params:** `sample_ids` — list of Open3D sample ids to show together in one scene.
- **Behavior:** copies each found sample into uploads; builds one deep-link with comma-separated `view`/`ext`/`type`/`name`/`sample` lists (the frontend zips them per index).
- **Returns (success):** `{"objects": [{"sample_id","file_id","geometry_type","name"}, ...], "missing": [<not found ids>], "url", "message": "Open this link to view <names> together full-screen: <url>"}`.
- **Errors:**
  - `{"error": "Provide at least one sample id.", "sample_ids": []}`
  - `{"error": "None of the requested samples were found.", "missing": [...], "available": [<existing ids>]}`
- **Side effects:** creates one upload `file_id` per found sample. **No metering.**
- **Example:** `visualize_samples(sample_ids=["bunny", "sphere"])`

### visualize_registration
```python
visualize_registration(
    fixed: str,
    moving: str | None = None,
    method: str = "rigid",
    fixed_is_file_id: bool = False,
    moving_is_file_id: bool = False,
) -> dict
```
- **Params:**
  - `fixed` — by default a SimpleITK/PyVista **sample id** (e.g. `sitk_training_001_ct`). Set `fixed_is_file_id=True` to pass an existing uploaded **file_id** instead (must be slicer-loadable, e.g. a `.vti` from DICOM upload).
  - `moving` — optional second volume; same sample-vs-file_id rule via `moving_is_file_id`.
  - `method` — pre-selects the UI registration method: `rigid` | `advanced_rigid` | `affine` | `bspline` | `demons` | `difference_analysis` (default `rigid`).
- **Behavior:** `_resolve_volume` resolves each ref (sample → materialized `.vti` file_id; file_id → verified via `get_upload_path`), builds a 4-panel registration-studio deep-link.
- **Returns (success):** `{"fixed": {"file_id","name"}, "moving": {"file_id","name"} | null, "method", "url" (`<FRONTEND_BASE>/?reg=1&fixed=<id>&fixedName=<name>&method=<method>[&moving=<id>&movingName=<name>]`), "message": "Open this link to view <label> in the registration studio: <url>"}`.
- **Errors:**
  - `{"error": "Fixed volume: <reason>"}` — reason is `"Uploaded file not found: <ref>"` (file_id mode) or the materialize error.
  - `{"error": "Moving volume: <reason>"}` (same).
- **Side effects:** materializes sample volumes into uploads (when not file_id mode). **Meters** (`_meter()` before building the URL).
- **Example:** `visualize_registration(fixed="sitk_training_001_ct", moving="sitk_training_001_mr_T1", method="rigid")`

---

## Resources

### Resource `context://expert/{topic}`
```python
@mcp.resource("context://expert/{topic}")
def expert_context(topic: str) -> str
```
- **Param:** `topic` — must be in the `CURATED_TOPICS` allowlist: `open3d`, `pyvista`, `vtk`, `simpleitk`, `mesh-processing`, `threejs`, `glsl-shader`, `3d-file-format`, `node-pipeline`, `slicer-integration`, `medical-registration`, `frontend-architecture`, `backend-architecture`, `devops-infrastructure`. (Use `list_expert_topics()` for those actually deployed.)
- **Returns:** the text of `CONTEXT_DIR/<topic>-expert.md` (`MCP_CONTEXT_DIR`, default `<repo>/.claude/commands`).
- **"Error" returns (still a string, not raised):**
  - Topic not in allowlist → `"No expert context for '<topic>'. Available: <list or '(none — check MCP_CONTEXT_DIR)'>"`.
  - File missing → `"Context file for '<topic>' is not deployed (check MCP_CONTEXT_DIR)."`.
- **Note:** the allowlist also blocks path traversal; project-internal notes (gcp-deploy-status, auth-system-summary, ai-chatbot, session-*, cloudrun diagnosis) are deliberately excluded. `.claude/` is excluded from the Docker build, so in deployment `MCP_CONTEXT_DIR` must point at a bundled copy or these return the "not deployed" string.
- **Example URI:** `context://expert/simpleitk`

### Resource `context://model/{model_id}`
```python
@mcp.resource("context://model/{model_id}")
def model_skill(model_id: str) -> str
```
- **Param:** `model_id` — from `list_models()`.
- **Returns:** the text of the model's knowledge-layer `SKILL.md` (resolved by `model_registry.skill_path` → `models/<id>/<skill>`, traversal-guarded). This ships in the Docker image (unlike the `.claude` expert context).
- **"Error" returns (string):**
  - Unknown model → `"No model-skill '<model_id>'. Available: <comma-joined ids or '(none)'>"`.
  - No SKILL.md (compute-only card) → `"Model '<model_id>' has no knowledge-layer SKILL.md (compute-only card)."`.
- **Example URI:** `context://model/pointnet`
