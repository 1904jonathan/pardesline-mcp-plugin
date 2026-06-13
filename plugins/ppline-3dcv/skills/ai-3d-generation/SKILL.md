---
name: ai-3d-generation
description: >-
  Run AI on images via the ppline-3dcv MCP server — 2D image processing
  (segmentation, depth, super-resolution, etc. on a GCP GPU service) and turning a
  single 2D image into a 3D .glb model with Trellis (NVIDIA L4 GPU). Use for
  "generate a 3D model from this image/photo", "make a 3D mesh from a picture",
  "run segmentation/depth/super-resolution on this image", "image to 3D",
  "image-to-glb". These are dedicated MCP tools backed by two GPU Cloud Run
  microservices, not registry modules.
---

# AI 2D Image Processing & Image→3D Generation

This skill covers four dedicated MCP tools on the `ppline-3dcv` server that run AI
on images using GPU-backed Google Cloud Run microservices:

| Tool | Purpose | Backend service / region |
|------|---------|--------------------------|
| `list_image_processing_methods()` | List 2D AI methods + their params | `ppline-image-processing`, **europe-west1** |
| `process_image(...)` | Run a 2D AI method on 1 or 2 images | `ppline-image-processing`, **europe-west1** |
| `list_trellis_methods()` | List image→3D generation methods | `ppline-trellis` (L4 GPU), **europe-west4** |
| `generate_3d_from_image(...)` | Turn one 2D image into a 3D `.glb` | `ppline-trellis` (L4 GPU), **europe-west4** |

Default service URLs (from `backend/config.py`, overridable via env):
- `IMAGE_PROCESSING_URL = https://ppline-image-processing-565128781631.europe-west1.run.app`
- `TRELLIS_URL = https://ppline-trellis-565128781631.europe-west4.run.app`

## CRITICAL: these are NOT registry modules

Unlike `run_job` / `run_pipeline` (which operate on uploaded `file_id`s via
`upload_file`), these four tools are **direct image tools**. They take **raw image
bytes, base64-encoded, passed DIRECTLY as a string argument** (`image_base64`).

- Do **NOT** call `upload_file` first. Do **NOT** pass a `file_id`.
- Read the local image, base64-encode the bytes, and pass that string.
- The platform decodes the base64 (`base64.b64decode(..., validate=True)` — invalid
  base64 returns `{"error": "...not valid base64..."}`, empty content returns
  `{"error": "Empty image content."}`), runs the AI service, then **persists the
  result** and returns you **downloadable URLs** (and for Trellis, a viewer
  deep-link).

```python
import base64
image_base64 = base64.b64encode(open("photo.png", "rb").read()).decode()
```

Auth to the GPU microservices is **service-to-service**: the platform mints a GCP
identity token from the Cloud Run metadata server (audience = the target service
URL), falling back to `gcloud auth print-identity-token` in local dev. This is
handled entirely **server-side** — you never supply a token. Your only credential is
the normal `ppline-3dcv` MCP `X-API-Key`, configured in the MCP client.

---

## 1. 2D Image Processing

### `list_image_processing_methods() -> dict`

Call this **first**. It proxies `GET /methods` on the image-processing service and
returns that service's live method catalog (with per-method parameters). **Always
call it before `process_image`** to get the exact valid `method` ids and their
`params` schema — the catalog is owned by the remote service and can change, so do
not hardcode method names.

- Returns the remote JSON, shaped like (per the frontend that consumes it):
  ```json
  { "methods": [ { "id": "...", "name": "...", "description": "...",
                   "params": [ { "name": "...", "type": "number"|"text", "default": ... } ] } ] }
  ```
  The frontend `ImageProcessingTab.js` reads exactly `res.methods[].id`, `.name`,
  `.description`, and `.params[].{name,type,default}` (param inputs are rendered as
  `number` or `text`).
- On failure returns `{ "error": "Image-processing service unavailable: ..." }` —
  always check for an `"error"` key.
- **Method ids are NOT hardcoded anywhere in this repo** — not in the router
  (`backend/routers/image_processing.py` is a pure proxy), not in `mcp_server.py`,
  and not in the frontend (it renders whatever the catalog returns). They live on the
  remote service. The service is documented to provide methods such as
  **segmentation, depth estimation, and super-resolution**, but you must read the
  live catalog for the authoritative list and each method's exact `id` + `params`.

### `process_image(image_base64, filename, method, params=None, image2_base64=None, filename2=None) -> dict`

Runs one 2D AI method on **one or two** images.

**Arguments**
- `image_base64` (str, required) — base64 of the first/primary image's bytes.
- `filename` (str, required) — original filename, e.g. `"photo.png"` (used as the
  multipart part name/extension on the remote side).
- `method` (str, required) — a method `id` from `list_image_processing_methods()`.
- `params` (dict | None) — the method's JSON parameter dict (keys/types per the
  catalog's `params`). Serialized to JSON server-side; defaults to `{}` if omitted.
- `image2_base64` (str | None) — base64 of a **second** image, only for methods that
  take two inputs (e.g. image-pair / difference operations).
- `filename2` (str | None) — filename for the second image (defaults to
  `"image2.png"`).

**Return keys** (success)
- `method` — echoes the method id you ran.
- `output_url` — downloadable URL of the result, persisted on the platform. **Give
  this to the user.**
- `output_file_id` — platform file id of the result (reusable as input to other
  tools / re-download).
- `content_type` — MIME type of the result.
- `result_info` — parsed JSON of the service's `X-Result-Info` response header (or
  the raw string if it wasn't JSON); present only when the service set it. Useful
  metadata (e.g. detected classes, scale factor).
- `message` — human-readable "Result saved. Download: <url>".

**Output shape rule (important)**
- **1 input image → PNG.** `content_type` is `image/png`; the result file extension
  is `.png`.
- **2 input images → ZIP.** `content_type` is `application/zip`; extension `.zip`; the
  archive contains the two result images + a `result.json`.

The MCP layer picks the extension from `content_type` (`zip`→`.zip`, `image`→`.png`,
else `.bin`).

**Errors** — returns `{ "error": "..." }`. HTTP failures include the upstream status,
e.g. `"Image processing failed (400): <body>"`; transport errors give
`"Image-processing service error: ..."`.

**Timeout** — the MCP tool uses a 300s HTTP timeout to the service. The
image-processing service has a much shorter cold start than Trellis, so timeouts are
rare here.

---

## 2. Image → 3D Generation (Trellis)

### `list_trellis_methods() -> dict`

Lists the image→3D methods on the Trellis L4 GPU service (proxies `GET /methods`,
300s timeout to absorb cold start). Optional but recommended if you're unsure of the
method id. Returns the same `{ "methods": [...] }` shape. On failure:
`{ "error": "Trellis service unavailable: ..." }`.

- The default/primary method id is **`trellis_generate`** (the documented default for
  `generate_3d_from_image` and the router's `/generate` default). The frontend
  auto-selects the method when the catalog has exactly one entry.
- This call itself can trigger a GPU cold start.

### `generate_3d_from_image(image_base64, filename="input.png", method="trellis_generate", params=None, timeout_s=480) -> dict`

Generates a textured 3D model (`.glb`) from a **single** 2D image using Trellis on an
NVIDIA L4 GPU.

**Arguments**
- `image_base64` (str, required) — base64 of the source image's bytes.
- `filename` (str) — default `"input.png"`.
- `method` (str) — default `"trellis_generate"`; use a value from
  `list_trellis_methods()` if different.
- `params` (dict | None) — method parameter dict; serialized to JSON, defaults to
  `{}`.
- `timeout_s` (int) — total time budget the tool spends (including cold start).
  Default **480**. **Clamped server-side to [60, 540]** (`max(60, min(timeout_s, 540))`).

**Return keys** (success)
- `view_url` — a **frontend deep-link** that opens the generated `.glb` directly in
  the platform's 3D viewer
  (`<FRONTEND_BASE>/?view=<id>&ext=.glb&type=mesh&name=Trellis+3D`). **Give this to
  the user to inspect the model.**
- `zip_url` — downloadable URL of the **full result ZIP** (the `.glb` + a preview
  `.mp4` + `result.json`). **Give this to the user to download.**
- `model_file_id` — platform file id of the extracted `.glb` (reusable as input to
  mesh tools, `run_job`, etc.).
- `attempts` — number of POST attempts it took (≥1; higher means it sat through cold
  start).
- `message` — "3D model ready — open in viewer: <view_url>".
- `warning` — present only if the `.glb` couldn't be extracted from the ZIP (you
  still get `zip_url`).

**Cold-start / timeout behavior (exact, from the code)**
- The L4 GPU service **scales to zero**. A cold start is **~60–120s** (and full
  pipeline + model loading can push the first-call latency higher — the frontend's
  activation UI budgets up to ~2–3 min for warm-up).
- `generate_3d_from_image` **BLOCKS and retries internally** — you do **not** loop.
  It computes a deadline = clamped `timeout_s`, then POSTs to `/process` in a loop:
  - On **HTTP 503** (GPU still warming up): records the error, `await asyncio.sleep(15)`,
    adds 15 to the accumulated wait, retries.
  - On any other transient exception: `await asyncio.sleep(10)`, adds 10 to the wait,
    retries.
  - It keeps going while accumulated wait `< deadline`.
- A non-503 **HTTP error** (e.g. 400/500) is **not** retried — it returns immediately
  as `{ "error": "Trellis generation failed (<code>): <body>" }`.
- If the deadline elapses without success, it returns
  `{ "status": "timeout", "error": "Trellis did not return within <N>s (last: <last error>). Retry with a larger timeout_s." }`.

**GOTCHA — do not self-retry on timeout.** If you get `status: "timeout"`, simply
**call again with a larger `timeout_s`** (up to the 540s cap). Do not wrap the tool
in your own retry loop and do not fire concurrent calls — the tool already handles
the cold-start wait, and parallel calls just thrash the single GPU instance. The
first call after the service has been idle is the one most likely to need the bigger
budget; subsequent calls while the instance is warm return in well under a minute.

> Note: the underlying browser route (`POST /api/trellis/generate`) streams the ZIP
> and retries 503 up to 12× / 15s (≈3 min) and 500 up to 2× / 5s. The **MCP tool**
> uses its own `timeout_s`-bounded loop described above — that is the behavior you
> get from `generate_3d_from_image`.

---

## Typical workflows

### A. Run a 2D AI method on an image
1. `list_image_processing_methods()` → pick a `method` id and read its `params`.
2. base64-encode the image.
3. `process_image(image_base64=..., filename="photo.png", method="<id>", params={...})`.
4. Hand the user `output_url` (PNG). Surface anything useful from `result_info`.

### B. Run a 2-input method (image pair)
1. `list_image_processing_methods()` → confirm the method accepts two inputs.
2. base64-encode both images.
3. `process_image(image_base64=a, filename="a.png", image2_base64=b, filename2="b.png", method="<id>", params={...})`.
4. Result is a **ZIP** (`content_type: application/zip`) — give the user `output_url`
   and note it contains both result images + `result.json`.

### C. Image → 3D model
1. (Optional) `list_trellis_methods()` to confirm the method id (default
   `trellis_generate`).
2. base64-encode the source image.
3. `generate_3d_from_image(image_base64=..., filename="input.png")` — this blocks
   through cold start; be patient.
4. Give the user **both**: `view_url` (opens the `.glb` in the 3D viewer) and
   `zip_url` (downloads glb + preview mp4 + json). Mention `model_file_id` if they
   want to feed the mesh into further processing.
5. If you got `status: "timeout"`, retry **once** with a larger `timeout_s` (e.g.
   540).

---

## Examples

**Example 1 — depth/segmentation on one image**
```text
User: "Run depth estimation on diningroom.jpg"
1. list_image_processing_methods() → find the depth method's id + params.
2. process_image(
       image_base64=<b64 of diningroom.jpg>,
       filename="diningroom.jpg",
       method="<depth_method_id>",
       params={}          # or whatever the catalog lists
   )
3. → { output_url: "...result.png", content_type: "image/png", result_info: {...} }
   Reply with the output_url.
```

**Example 2 — generate a 3D model from a photo**
```text
User: "Make a 3D model from this product photo (sneaker.png)"
1. generate_3d_from_image(
       image_base64=<b64 of sneaker.png>,
       filename="sneaker.png"          # method defaults to "trellis_generate"
   )
   (blocks ~60-120s on cold start; do not retry yourself)
2. → { view_url: "...?view=...&ext=.glb...", zip_url: "...trellis_result.zip",
       model_file_id: "<uuid>", attempts: 3 }
3. Reply: "Your 3D model is ready. View it here: <view_url>. Download (glb + preview
   mp4): <zip_url>."
```

**Example 3 — first call timed out**
```text
generate_3d_from_image(...) → { status: "timeout", error: "...Retry with a larger timeout_s." }
→ generate_3d_from_image(..., timeout_s=540)   # single retry, larger budget
→ success.
```

---

## Gotchas & limits

- **Base64 size.** The whole image is base64-encoded into a single string argument
  and travels in the MCP request body. base64 inflates bytes ~33%. Keep source images
  reasonable (downscale very large photos before encoding) to avoid oversized
  requests / memory pressure. Trellis works fine from typical single-object photos.
- **Cold starts.** Both services can scale to zero. The 2D service warms quickly;
  **Trellis (L4 GPU) is the slow one** — the first call after idle is the one that
  needs the wait. Tell the user the first 3D generation may take a couple of minutes.
- **1 image = PNG, 2 images = ZIP** for `process_image`. Don't assume a viewable PNG
  came back when you sent two inputs.
- **Always present the returned URLs verbatim.** Results are persisted on the
  platform; `output_url` / `zip_url` are the user's way to retrieve them, and
  `view_url` opens the 3D model in-browser. Don't paraphrase or truncate them.
- **Check for `"error"` / `"status": "timeout"` keys** in every return before
  declaring success.
- **Don't `upload_file` for these tools** — that's only for registry modules. These
  take base64 directly.

## Related skills
- **`ppline-3dcv:mcp-tool-reference`** — full catalog of all MCP tools, auth, and the
  `view_url` viewer deep-link convention.
- **`ppline-3dcv:data-io-and-files`** — how persisted outputs, `file_id`s, and
  download URLs work (e.g. reusing `model_file_id` / `output_file_id` downstream).
- **`ppline-3dcv:mesh-and-surfaces`** — process the generated `.glb` mesh further
  (the Trellis `model_file_id` is a normal mesh file id you can feed into mesh tools).
