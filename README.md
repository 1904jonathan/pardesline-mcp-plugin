# pardesline-mcp-plugin

Public distribution repo for the **ProductPardesLine** Claude Code plugin — one-liner
access to the platform's **3D computer-vision & medical-imaging MCP server** (point
clouds, meshes, registration, volumes, DICOM, image→3D).

This repo ships **only** a Claude Code marketplace + plugin manifest + bundled skills.
It contains **no platform source code** — the plugin points Claude Code at the already
deployed, hosted MCP endpoint. All compute runs server-side and is authenticated with
your own API key.

> The exact same content is also downloadable as a `.zip` from the platform UI. This
> repo is the **git install** path: `/plugin marketplace add …`.

## Install (Claude Code)

1. **Get an API key.** Create a project in the platform and generate its `pl_…` key
   (web UI, or the MCP tool `generate_project_api_key`).

2. **Export it** so the plugin injects it as the `X-API-Key` header:

   ```bash
   export PPLINE_API_KEY=pl_your_key_here          # macOS / Linux
   ```
   ```powershell
   $env:PPLINE_API_KEY = "pl_your_key_here"        # Windows PowerShell
   ```

   Set it **before** launching Claude Code (or put it in your shell profile).

3. **Add this repo as a marketplace and install:**

   ```bash
   /plugin marketplace add 1904jonathan/pardesline-mcp-plugin
   /plugin install ppline-3dcv@ppline-3dcv-tools
   ```

4. **Approve** the MCP server when prompted, then run `/mcp` — `ppline-3dcv` should be
   **connected**. Try: *"list the modules via ppline-3dcv"*.

## What's inside

| Path | Purpose |
|------|---------|
| [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) | Marketplace entry consumed by `/plugin marketplace add` |
| [`plugins/ppline-3dcv/.claude-plugin/plugin.json`](plugins/ppline-3dcv/.claude-plugin/plugin.json) | Plugin manifest — declares the hosted HTTP MCP server inline (`X-API-Key: ${PPLINE_API_KEY}`) |
| [`plugins/ppline-3dcv/skills/`](plugins/ppline-3dcv/skills/) | Token-efficient bundled skills (catalog, registration, mesh, DICOM, pipelines…) |
| [`MCP_README.md`](MCP_README.md) | Full MCP server reference (34 tools + context resources) |

## What you get (34 MCP tools + context resources)

- **Discovery** — module catalog, deep-learning model-skills, Open3D / PyVista /
  SimpleITK sample datasets.
- **Compute (blocking)** — `run_job` (one module, dual-input registration), `run_pipeline`
  (linear multi-node chain), `run_project_workflow` (a saved node-editor DAG).
- **Data** — `upload_file`, `use_sample`, `upload_dicom_folder` (multi-slice DICOM).
- **Projects** — full CRUD + node-editor workflow load/save + API-key generate/revoke.
- **GCP AI** — `process_image` (2D AI), `generate_3d_from_image` (image→`.glb`, L4 GPU).
- **Medical QC** — `get_volume_info`, `analyze_registration_deformation`, `warp_volume`,
  `export_volume_dicom`.
- **Visualize** — `visualize_sample(s)` / `visualize_registration` → clickable viewer URLs.
- **Context** — `context://expert/{topic}` (14 curated 3D-CV experts) and
  `context://model/{model_id}` (DL model knowledge).

See [`MCP_README.md`](MCP_README.md) for the full tool reference and
[`plugins/ppline-3dcv/README.md`](plugins/ppline-3dcv/README.md) for plugin details.

## Notes

- Compute is **metered** and consumes backend CPU/GPU; `generate_3d_from_image` runs on
  an L4 GPU with cold starts (~60–120 s when scaled to zero).
- The endpoint URL is the production Cloud Run service, hard-wired in the plugin
  manifest. No secrets live in this repo — you bring your own `PPLINE_API_KEY`.

## License & access

**Proprietary** — see [LICENSE](LICENSE). The files in this repo are free to download and
use *only* to configure an MCP client. **The MCP Service itself is a paid product:** every
tool/compute call requires a valid **paid ProductPardesLine subscription** and an active
`pl_…` API key. Without a subscription, the hosted server rejects your requests. This repo
grants **no** access to the Service.

© 2026 ProductPardesLine. All rights reserved.
