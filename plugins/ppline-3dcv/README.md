# ppline-3dcv — Claude Code plugin

One-liner install for the **ProductPardesLine** 3D computer-vision & medical-imaging
MCP server. The plugin ships *only* a config that points Claude Code at the already
deployed production MCP endpoint — no platform code travels with it.

Server reference: [`../../MCP_README.md`](../../MCP_README.md).

## What you get (34 MCP tools + context resources)

- **Discovery** — module catalog, deep-learning model-skills, and Open3D / PyVista /
  SimpleITK sample datasets.
- **Compute (blocking)** — `run_job` (one module, dual-input registration), `run_pipeline`
  (linear multi-node chain), `run_project_workflow` (a saved node-editor DAG).
- **Data** — `upload_file`, `use_sample`, `upload_dicom_folder` (multi-slice DICOM).
- **Projects** — full CRUD + node-editor workflow load/save + API-key generate/revoke.
- **GCP AI** — `process_image` (2D AI) and `generate_3d_from_image` (image→`.glb`, L4 GPU).
- **Medical QC** — `get_volume_info`, `analyze_registration_deformation` (Jacobian
  folding), `warp_volume`, `export_volume_dicom`.
- **Visualize** — `visualize_sample(s)` / `visualize_registration` return clickable
  full-screen viewer / registration-studio URLs.
- **Context resources** — `context://expert/{topic}` (14 curated 3D-CV experts) and
  `context://model/{model_id}` (DL training knowledge).

## Install

1. **Get an API key.** Create a project in the platform and generate its `pl_…` key
   (web UI project settings, or via the MCP tool `generate_project_api_key` from an
   already-authenticated session).

2. **Export it** so the plugin can inject it as the `X-API-Key` header:

   ```bash
   # macOS / Linux
   export PPLINE_API_KEY=pl_your_key_here
   ```
   ```powershell
   # Windows PowerShell
   $env:PPLINE_API_KEY = "pl_your_key_here"
   ```

   The env var is read at MCP-server startup, so set it **before** launching Claude Code
   (or set it permanently in your shell profile).

3. **Add this repo as a marketplace and install:**

   ```bash
   /plugin marketplace add 1904jonathan/pardesline-mcp-plugin
   /plugin install ppline-3dcv@ppline-3dcv-tools
   ```

4. **Approve** the MCP server when prompted, then `/mcp` should list `ppline-3dcv` as
   connected. Try: *"list the modules via ppline-3dcv"*.

## Configuration

| Env var | Required | Purpose |
|---------|----------|---------|
| `PPLINE_API_KEY` | yes | Your `pl_…` project key, expanded into the `X-API-Key` header. |

The endpoint URL is hard-wired to the production Cloud Run service in
[`.claude-plugin/plugin.json`](.claude-plugin/plugin.json). For **local development**
against your own `uvicorn` instance, don't use the plugin — register the server directly:

```bash
MCP_REQUIRE_API_KEY=false uvicorn backend.main:app --port 8000
claude mcp add --transport http ppline-3dcv http://localhost:8000/mcp/
```

## Notes

- Compute is **metered** but not tier-gated yet; heavy tools (`run_job`, `run_pipeline`,
  `process_image`, `generate_3d_from_image`) consume backend CPU/GPU.
- `generate_3d_from_image` runs on an L4 GPU with **cold starts** (~60–120 s when scaled
  to zero); the tool blocks and retries through the cold start.
- Jobs are in-memory on the server (scale-to-zero): prefer the blocking `run_job`, which
  returns the result in a single call, over polling `get_job_status`.
