# pardesline-mcp-plugin

Public distribution repo for the **ProductPardesLine** Claude Code plugin — one-liner
access to the platform's **3D computer-vision & medical-imaging MCP server** (point
clouds, meshes, registration, volumes, DICOM, image→3D).

This repo ships **only** a Claude Code marketplace + plugin manifest + bundled skills.
It contains **no platform source code** — the plugin points Claude Code at the already
deployed, hosted MCP endpoint. All compute runs server-side and is authenticated with
**OAuth** (browser email sign-in) — no API key to copy, no env var to set.

> The exact same content is also downloadable as a `.zip` from the platform UI. This
> repo is the **git install** path: `/plugin marketplace add …`.

## Install (Claude Code) — sign in with your email

1. **Add this repo as a marketplace and install:**

   ```bash
   /plugin marketplace add 1904jonathan/pardesline-mcp-plugin
   /plugin install ppline-3dcv@ppline-3dcv-tools
   ```

2. **Authenticate.** Run `/mcp`, pick `ppline-3dcv`, choose **Authenticate**. Your
   browser opens a PardesLine sign-in page → enter your **authorized email** → enter the
   **6-digit code** emailed to you → you're returned to the terminal, **connected**.
   Try: *"list the modules via ppline-3dcv"*.

   > Your email must be on the platform allowlist with API access (registration-only
   > accounts cannot connect via MCP). Contact your administrator to be added.

Prefer no plugin? One command does the same (OAuth still applies):

```bash
claude mcp add --transport http ppline-3dcv https://ppline-backend-565128781631.me-west1.run.app/mcp
```

## What's inside

| Path | Purpose |
|------|---------|
| [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) | Marketplace entry consumed by `/plugin marketplace add` |
| [`plugins/ppline-3dcv/.claude-plugin/plugin.json`](plugins/ppline-3dcv/.claude-plugin/plugin.json) | Plugin manifest — declares the hosted HTTP MCP server inline (no headers — OAuth sign-in) |
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
  manifest. No secrets live in this repo — you sign in via OAuth (email + OTP); tokens
  are stored securely by Claude Code and refreshed automatically.

## License & access

**Proprietary** — see [LICENSE](LICENSE). The files in this repo are free to download and
use *only* to configure an MCP client. **The MCP Service itself is a paid product:** every
tool/compute call requires a valid **paid ProductPardesLine subscription** and an
authorized account (allowlisted email with API access). Without a subscription, the hosted
server rejects your sign-in. This repo grants **no** access to the Service.

© 2026 ProductPardesLine. All rights reserved.
