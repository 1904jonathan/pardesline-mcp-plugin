# pardesline-mcp-plugin

Public distribution repo for the **ProductPardesLine** Claude Code plugin — one-liner
access to the platform's **3D computer-vision & medical-imaging MCP server** (point
clouds, meshes, registration, volumes, DICOM, image→3D).

This repo ships **only** a Claude Code marketplace + plugin manifest + bundled skills.
It contains **no platform source code** — the plugin points Claude Code at the already
deployed, hosted MCP endpoint. All compute runs server-side.

**Any MCP client works**, not only Claude Code — see
[Other MCP clients](#other-mcp-clients-codex-cursor-vs-code-scripts). Two credentials
are accepted:

| Credential | Where it comes from | Use it when |
|---|---|---|
| **OAuth** (browser email sign-in) | the client negotiates it — nothing to copy | the client runs where your browser can reach it (your own machine) |
| **API key** (`pl_…`) | app → avatar menu → **API keys**, or `POST /api/keys` | headless: SSH, a container, CI — where the OAuth callback to `127.0.0.1` never arrives |

## Install (Claude Code) — sign in with your email

1. **Add this repo as a marketplace and install:**

   ```bash
   /plugin marketplace add 1904jonathan/pardesline-mcp-plugin
   /plugin install ppline-3dcv@ppline-3dcv-tools
   ```

2. **Authenticate.** Run `/mcp`, pick `ppline-3dcv`, choose **Authenticate**. Your
   browser opens a PardesLine sign-in page → enter your **email** → enter the
   **6-digit code** emailed to you → you're returned to the terminal, **connected**.
   Try: *"list the modules via ppline-3dcv"*.

   > **Self-serve**: any email can sign up. New accounts get a **3-day trial with full
   > access**, then drop to the **Free plan — which still includes MCP**: 1,000 API/MCP
   > calls, 30 CPU jobs and 10 registration jobs per month, 1 GB storage, no card. A
   > paid plan buys GPU tools and higher quotas — see
   > [pricing](https://dev.pardesline.com/#pricing) or subscribe in the app at
   > [appbeta.pardesline.com](https://appbeta.pardesline.com/?checkout=1).

Prefer no plugin? One command does the same (OAuth still applies):

```bash
claude mcp add --transport http ppline-3dcv https://ppline-backend-565128781631.me-west1.run.app/mcp
```

## Other MCP clients (Codex, Cursor, VS Code, scripts)

The server is a standard **Streamable HTTP** MCP endpoint with OAuth 2.1 discovery, so
any compliant client connects to the same URL:

```
https://ppline-backend-565128781631.me-west1.run.app/mcp
```

### Codex CLI

```bash
codex mcp add pardesline --url https://ppline-backend-565128781631.me-west1.run.app/mcp
```

That command **starts the browser sign-in itself** (email + 6-digit code). If you add
the server by hand in `~/.codex/config.toml` instead, nothing will authenticate you —
Codex just reports `Not logged in` and every call fails. Run `codex mcp login pardesline`
to finish, and raise the two default timeouts, which are far too short for a platform
that scales to zero and runs real 3D jobs:

```toml
[mcp_servers.pardesline]
url = "https://ppline-backend-565128781631.me-west1.run.app/mcp"
startup_timeout_sec = 180   # default 10 — a cold instance needs ~30 s
tool_timeout_sec = 900      # default 60 — run_job blocks until the job is done
```

Headless (SSH, container, CI), where no browser can reach `127.0.0.1`, use a key:

```bash
export PARDESLINE_API_KEY=pl_...
codex mcp add pardesline --url https://ppline-backend-565128781631.me-west1.run.app/mcp \
  --bearer-token-env-var PARDESLINE_API_KEY
```

### Cursor / VS Code / any `mcp.json`

```json
{
  "mcpServers": {
    "ppline-3dcv": {
      "type": "http",
      "url": "https://ppline-backend-565128781631.me-west1.run.app/mcp"
    }
  }
}
```

Sign-in happens in the browser on first use. For a headless setup, add the key instead:
`"headers": { "X-API-Key": "pl_..." }`.

### Scripts (Python SDK)

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = "https://ppline-backend-565128781631.me-west1.run.app/mcp"
async with streamablehttp_client(URL, headers={"X-API-Key": "pl_..."}) as (r, w, _):
    async with ClientSession(r, w) as session:
        await session.initialize()
        print([t.name for t in (await session.list_tools()).tools])
```

### Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Client says **needs authentication / not logged in**, every call 401 | Nothing signed you in yet. Claude Code: `/mcp` → **Authenticate**. Codex: `codex mcp login pardesline`. Or use an API key. |
| **Timeout** on connect | The service scales to zero; a cold instance takes ~30 s. Raise the client's startup timeout (Codex: `startup_timeout_sec`). |
| **Timeout** on `run_job` / `generate_3d_from_image` | These block until the job finishes (a GPU job can take minutes). Raise the per-tool timeout (Codex: `tool_timeout_sec`). |
| `Protected resource … does not match expected …` | Your client and the server disagree on the origin. Use the exact URL above, without a redirect in front of it. |
| **402** with a quota message | Monthly Free-plan quota reached; it resets next month, or upgrade. |

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
  are stored securely by your client and refreshed automatically.

## License & access

**Proprietary** — see [LICENSE](LICENSE). The files in this repo are free to download and
use *only* to configure an MCP client. Using the hosted Service requires a PardesLine
account: the **Free plan includes MCP** within its monthly quotas, and GPU tools plus
higher quotas require a paid plan ([pricing](https://dev.pardesline.com/#pricing)).
An account whose access is paused is refused at sign-in and on every tool call. This
repo grants **no** access to the Service.

© 2026 ProductPardesLine. All rights reserved.
