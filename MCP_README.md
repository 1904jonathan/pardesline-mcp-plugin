# ProductPardesLine MCP Server

Exposes the platform as a **Model Context Protocol** server so developers using
Claude Code (or any MCP client) get extremely targeted **3D computer-vision
context** PLUS **full programmatic access** to every platform feature: the module
catalog, sample datasets, single-module and multi-node compute, project
management, AI microservices (2D image processing + image→3D), medical DICOM I/O,
non-rigid deformation analysis, and viewer deep-links.

- Hosted MCP server (you connect over HTTP — no platform code is shipped to you)
- Reachable at **`/mcp`** on the production Cloud Run endpoint
- Transport: Streamable HTTP (stateless, JSON responses) — works behind Cloud Run
- **Goal: full parity** — anything the web UI / REST API can do is reachable via MCP.

## Tool surface (34 tools)

**Discovery**
| Tool | Returns |
|------|---------|
| `list_modules()` / `get_module_info(id)` | 3D CV module catalog + methods + params |
| `list_models()` / `get_model_info(id)` | Deep-learning model-skills (PointNet, VoxelMorph…) |
| `list_open3d_samples()` | Open3D point-cloud / mesh samples |
| `list_pyvista_samples()` | PyVista mesh / volume samples |
| `list_simpleitk_samples()` | SimpleITK medical samples (RIRE, POPI…) |
| `list_expert_topics()` | Available expert context topics |

**Data in**
| Tool | Returns |
|------|---------|
| `upload_file(filename, content_base64)` | Upload one local file → `file_id` |
| `use_sample(sample_id)` | Materialize a built-in sample → `file_id` |
| `upload_dicom_folder(files=[{filename, content_base64}])` | Reassemble a multi-slice DICOM series → volume `file_id` |

**Compute**
| Tool | Returns |
|------|---------|
| `run_job(module_id, method_id, file_id/sample_id, …)` | Run ONE module, BLOCK for result (dual-input registration via `moving_*`) |
| `get_job_status(job_id)` | Poll a long-running job |
| `run_pipeline(steps=[{module_id, method_id, params}], file_id/sample_id)` | Chain modules (linear node-editor); BLOCK for final artifact |
| `run_project_workflow(project_id, file_id/sample_id)` | Run a project's saved node-editor DAG (mirrors `/api/execute`) |

**Projects** (full CRUD + workflow + API keys)
| Tool | Purpose |
|------|---------|
| `list_projects` / `create_project` / `get_project` / `delete_project` | Project lifecycle |
| `get_project_workflow` / `save_project_workflow` | Load / save the node-editor DAG |
| `generate_project_api_key` / `revoke_project_api_key` | Manage the `pl_…` key MCP clients authenticate with |

**AI microservices (GCP Cloud Run)**
| Tool | Service |
|------|---------|
| `list_image_processing_methods` / `process_image(...)` | 2D AI (europe-west1) |
| `list_trellis_methods` / `generate_3d_from_image(image_base64=…)` | Image→3D `.glb`, L4 GPU (europe-west4) |

**Medical / registration QC**
| Tool | Purpose |
|------|---------|
| `get_volume_info(file_id)` | Dimensions / spacing / origin / intensity range |
| `analyze_registration_deformation(transform_file_id, reference_file_id)` | Displacement magnitude + Jacobian folding fraction |
| `warp_volume(fixed, moving, transform, t)` | Warp moving→fixed; returns viewer deep-link |
| `export_volume_dicom(file_id)` | Export a volume back to a downloadable DICOM ZIP |

**Visualize**: `visualize_sample(s)`, `visualize_registration(...)` → clickable
full-screen viewer / registration-studio URLs.

**Resources** (context): `context://expert/{topic}` for 14 curated 3D CV experts
(`open3d, pyvista, vtk, simpleitk, mesh-processing, threejs, glsl-shader,
3d-file-format, node-pipeline, slicer-integration, medical-registration,
frontend-architecture, backend-architecture, devops-infrastructure`) and
`context://model/{model_id}` for model-skill knowledge.

> **Compute is metered** (`increment_api_usage`, best-effort) but **not tier-gated
> yet** — billing tiers / quotas are the next step before public launch.
> The two AI tools proxy external Cloud Run services; the backend service account
> needs `roles/run.invoker` on them (already granted — the web routers use the
> same path).

## Authentication — OAuth 2.1 (browser email+OTP, no API key)

Authenticate with a **browser sign-in** (email + 6-digit OTP), not a static key. On the
first call Claude Code gets a `401` + `WWW-Authenticate` pointing at the server's OAuth
metadata, registers itself (RFC 7591), opens your browser to the PardesLine sign-in page
(PKCE S256), and — after you enter your allowlisted email + the emailed code — receives a
Bearer token automatically. Access is gated by the email allowlist + API-access tier;
usage is metered per user.

## Connect from Claude Code (without the plugin)

```bash
claude mcp add --transport http ppline-3dcv \
  https://ppline-backend-565128781631.me-west1.run.app/mcp
# then: /mcp → ppline-3dcv → Authenticate (browser email+OTP sign-in)
```

Then, inside Claude Code, the model can read `context://expert/simpleitk`,
call `list_modules()`, etc. — grounded in the actually-deployed catalog.

## Install as a Claude Code plugin (one-liner)

The server is also packaged as a **Claude Code plugin** under
[`plugins/ppline-3dcv/`](plugins/ppline-3dcv/), listed by the repo-root
marketplace [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json):

```bash
/plugin marketplace add 1904jonathan/pardesline-mcp-plugin
/plugin install ppline-3dcv@ppline-3dcv-tools
# then: /mcp → ppline-3dcv → Authenticate (browser email+OTP sign-in)
```

The plugin declares the prod HTTP MCP server inline (no `headers` block — OAuth)
**and bundles 8 token-efficient skills** (`using-ppline` + 7 domain skills) that embed
the module catalog so a remote agent runs `run_job` / `run_pipeline` without exploratory
`list_modules` / `get_module_info` round-trips. Skills ship in the plugin (NOT in the
Docker image and NOT from `.claude/`). See
[`plugins/ppline-3dcv/README.md`](plugins/ppline-3dcv/README.md).

## Smoke test (after install)

In Claude Code, run `/mcp` and confirm `ppline-3dcv` is **connected**, then ask:

> *"list the modules via ppline-3dcv"*

You should get the live module catalog back from the hosted server.
