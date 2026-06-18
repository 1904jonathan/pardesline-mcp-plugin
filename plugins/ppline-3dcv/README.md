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

## Install (sign in with your email — no API key)

Authentication is **OAuth 2.1**: there is no key to copy and no env var to set. The
first time Claude Code talks to the server, your browser opens a PardesLine sign-in
page; enter your **authorized email + the 6-digit code** emailed to you, and Claude
Code is connected automatically.

1. **Add this repo as a marketplace and install:**

   ```bash
   /plugin marketplace add 1904jonathan/pardesline-mcp-plugin
   /plugin install ppline-3dcv@ppline-3dcv-tools
   ```

2. **Run `/mcp`**, pick `ppline-3dcv`, choose **Authenticate**. Your browser opens the
   PardesLine sign-in page → enter your email → enter the emailed code → you're returned
   to the terminal, connected. Try: *"list the modules via ppline-3dcv"*.

   > Your email must be on the platform allowlist with API access. Registration-only
   > accounts cannot connect via MCP. Contact your administrator to be added.

### Prefer a one-liner without the plugin?

```bash
claude mcp add --transport http ppline-3dcv https://ppline-backend-565128781631.me-west1.run.app/mcp
```

Then `/mcp` → Authenticate (same browser sign-in). No marketplace, no key, no env var.

## Configuration

No configuration required — OAuth handles credentials. Tokens are stored securely by
Claude Code and refreshed automatically.

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
