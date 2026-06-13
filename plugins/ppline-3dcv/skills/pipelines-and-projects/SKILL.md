---
name: pipelines-and-projects
description: >-
  Chain platform modules into pipelines and manage projects via the ppline-3dcv MCP
  server — run a linear multi-step chain (run_pipeline), build & run a saved node-editor
  DAG workflow (save/get/run_project_workflow), full project CRUD (list/create/get/delete),
  and generate/revoke the project API key. Use for "run a multi-step pipeline", "save this
  as a workflow", "create a project", "rotate my API key", "run my saved workflow".
---

# Pipelines & Projects (ppline-3dcv)

This skill covers running **multi-step** work and managing **projects** over the
`ppline-3dcv` MCP server. For the universal one-tool recipe, the module/method catalog
(where every `module_id` / `method_id` comes from), and getting data in
(`upload_file` / `use_sample`), see **`ppline-3dcv:using-ppline`**. For the flat list of
every MCP tool, see **`ppline-3dcv:mcp-tool-reference`**.

**Full workflow-dict schema, the topological execution model, the dual-input port
caveat, and runnable DAG snippets are in [`reference.md`](reference.md) — read it before
hand-building any non-linear or dual-input workflow.**

---

## Two ways to run multiple steps

| | `run_pipeline` | `save_project_workflow` + `run_project_workflow` |
|---|---|---|
| Graph shape | ordered **LINEAR** chain only (`input → s1 → s2 → …`) | any **DAG** (branches, fan-in/out) |
| Input | ONE primary (`file_id` **or** `sample_id`) | ONE primary (`file_id` **or** `sample_id`) |
| Persisted? | no (one-shot, ad-hoc) | yes (saved on the project) |
| Blocks built by | the tool, for you | you (the dict you save) |
| Use when | quick A→B→C | reusable / non-linear graph |

Both run through the **same** standalone `WorkflowExecutor` the web `/api/execute`
endpoint uses, so behavior is identical (`backend/services/workflow_executor.py`).
`run_pipeline` simply constructs the linear `{blocks, edges}` dict and hands it to that
executor; `run_project_workflow` loads the project's saved dict and hands it over.

---

## Tool signatures & exact return keys

### Multi-step execution

`run_pipeline(steps, file_id=None, sample_id=None, timeout_s=540)`
- `steps`: ordered `list[dict]`, each `{module_id, method_id, params?}` (params optional;
  method defaults used when omitted). Module/method must exist (validated per step against
  the registry — an unknown one returns `{"error": …}`).
- Provide exactly one primary input: `file_id` (from `upload_file`) **or** `sample_id`
  (materialized automatically).
- BLOCKS until the whole chain finishes.
- Returns on success:
  ```python
  {"status": "completed",
   "steps": "modA.methA -> modB.methB",   # human-readable chain label
   "output_url": "https://…/api/files/outputs/<id>.<ext>",  # absolute, downloadable
   "output_file_id": "<uuid>",            # feed into get_volume_info / further run_job
   "output_type": "ply",                  # final file extension, no dot
   "message": "Pipeline finished. Download: …"}
  ```
- On timeout: `{"status": "running", "error": "Pipeline still running after <t>s …"}`
  (no resumable handle — there is NO job_id for standalone workflows; re-run with a larger
  `timeout_s` or fewer/cheaper steps).
- On failure: `{"error": "Pipeline execution failed: …"}`.
- **Single input per step** → cannot express dual-input registration. See the caveat below.

`run_project_workflow(project_id, file_id=None, sample_id=None, timeout_s=540)`
- Runs the project's SAVED node-editor DAG on a new input. Mirrors `POST /api/execute`.
- `project_id` from `list_projects()`; the workflow comes from `save_project_workflow` or
  the web editor. One primary input (`file_id` or `sample_id`).
- Same return shape as `run_pipeline` (the `steps` label is `project:<name>`).
- Errors if the project has no saved workflow (`…has no saved workflow…`) or no `blocks`.

`timeout_s` is clamped to **`max(10, min(timeout_s, 540))`** in both tools — 540s is the
hard cap (stays under the Cloud Run 600s request budget).

### Project CRUD

- `list_projects()` → `list[{id, name, created_at, has_api_key, has_workflow}]`
  (newest first). `has_workflow` is true only when the saved workflow has a non-empty
  `blocks` list.
- `create_project(name)` → `{id, name, created_at, has_api_key, has_workflow}`. Also
  creates the on-disk `data/project_<id>/{uploads,outputs}` dirs. Empty name → `{"error"}`.
- `get_project(project_id)` → same dict as a `list_projects` entry, or `{"error"}`.
- `delete_project(project_id)` → `{"status": "deleted", "id": …}`. **IRREVERSIBLE** —
  also `rmtree`s the project's on-disk `data/project_<id>` directory.
- `get_project_workflow(project_id)` → `{"project_id": …, "workflow": {…}|null}`.
- `save_project_workflow(project_id, workflow)` → `{"status": "saved", "id": …,
  "blocks": <count>}`. `workflow` MUST be a dict with at least a `"blocks"` list, else
  `{"error": "workflow must be a dict with at least a 'blocks' list."}`.

### Project API key (the credential MCP clients auth with)

- `generate_project_api_key(project_id)` → `{api_key: "pl_…", project_id, project_name}`.
  Generates OR **regenerates**; regenerating **invalidates the previous key**.
- `revoke_project_api_key(project_id)` → `{status: "revoked", project_id}`. Sets the key to
  none; subsequent MCP / `/api/execute` calls with the old key are rejected (401).

The key format is `pl_` + 32 hex chars (`pl_<sha256(token)[:32]>`). This is the **same**
`X-API-Key` the MCP transport and `/api/execute` authenticate with — see the lockout
gotcha below.

---

## The workflow dict (what you save / what runs)

Minimal linear shape — `run_pipeline` builds exactly this for you:

```jsonc
{
  "blocks": [
    {"id": "input", "type": "file-input"},
    {"id": "step1", "type": "process", "moduleId": "<module_id>", "methodId": "<method_id>", "params": {}},
    {"id": "step2", "type": "process", "moduleId": "<module_id>", "methodId": "<method_id>", "params": {}}
  ],
  "edges": [
    {"from": {"nodeId": "input"}, "to": {"nodeId": "step1"}},
    {"from": {"nodeId": "step1"}, "to": {"nodeId": "step2"}}
  ]
}
```

- **Input node**: `type` is `"file-input"` (web editor also emits `"upload"`; the executor
  accepts both). The single API/primary input file replaces this node's output.
- **Process node**: `{id, type:"process", moduleId, methodId, params}`. `params` defaults to
  `{}` if omitted. The web editor adds layout/UI fields (`x`, `y`, `operatorName`, `fileId`,
  `sampleId`, …) — the executor ignores everything except `id/type/moduleId/methodId/params`.
- **Edge**: `{from:{nodeId}, to:{nodeId}}`. The web editor also stores a `port` on each
  endpoint (`from.port`, `to.port`); **the standalone executor ignores ports** (see below).

Execution = Kahn topological sort over `blocks`/`edges`; each process block takes the
**first** edge whose `to.nodeId` matches it, reads that upstream node's output file, runs
`python <script> --input <upstream_out> --output <block_id><ext> [params]`, and stores the
result. The **last process block in topo order** is published as the downloadable output.
Cycles raise `"Workflow contains cycles - cannot execute"`. Full details + a worked DAG in
**[`reference.md`](reference.md)**.

---

## CRITICAL: dual-input registration does NOT run through pipelines/DAGs

The web node editor *draws* dual-input registration: a process node has two input ports,
`input` (label **fixed**, left) and `input_t` (label **moving**, top), and the editor saves
edges with `to.port: "input"` vs `to.port: "input_t"`
(`frontend/js/workflow/Operator.js`, `NodeEditor.js`). **But the standalone
`WorkflowExecutor` that MCP and `/api/execute` use ignores `to.port` entirely** — it picks
the first matching edge by `to.nodeId` and passes a single file via `--input` only. There is
**no `--moving` wiring** in `WorkflowExecutor.execute`. Without `--moving`, registration
scripts synthesize a moving cloud from the fixed input → meaningless self-alignment.

→ For any dual-input registration (CT+MRI, fixed+moving), use **`run_job(module_id,
method_id, file_id=fixed, moving_file_id=moving, …)`** — only `run_job` passes the moving
path. See **`ppline-3dcv:point-cloud-registration`** and **`ppline-3dcv:medical-imaging`**.

You may still wire single-input steps freely; just keep registration out of the chain.

---

## Example 1 — linear pipeline (one-shot, no project)

```python
run_pipeline(
  steps=[
    {"module_id": "point_cloud_processing", "method_id": "voxel_downsample",
     "params": {"voxel_size": 0.05}},
    {"module_id": "point_cloud_reconstruction", "method_id": "poisson"},
  ],
  sample_id="<sample_id>",   # or file_id="<from upload_file>"
)
# -> {"status":"completed", "output_url":..., "output_file_id":..., "output_type":"ply"}
```

## Example 2 — create project → save DAG → run it (reusable)

```python
p = create_project("scan-cleanup")          # -> {"id": PID, ...}

save_project_workflow(p["id"], {
  "blocks": [
    {"id": "input", "type": "file-input"},
    {"id": "down",  "type": "process", "moduleId": "point_cloud_processing",
     "methodId": "voxel_downsample", "params": {"voxel_size": 0.05}},
    {"id": "mesh",  "type": "process", "moduleId": "point_cloud_reconstruction",
     "methodId": "poisson"},
  ],
  "edges": [
    {"from": {"nodeId": "input"}, "to": {"nodeId": "down"}},
    {"from": {"nodeId": "down"},  "to": {"nodeId": "mesh"}},
  ],
})

run_project_workflow(p["id"], sample_id="<sample_id>")   # reuse on any new input
```

## Example 3 — rotate the API key safely

```python
list_projects()                              # find the project id
# WARNING: if this project's key is the one THIS session authenticates with,
# regenerating it can lock you out mid-session. Confirm with the user first.
generate_project_api_key("<project_id>")     # -> {"api_key": "pl_..."}  (store it)
```

(For a non-linear / dual-input snippet see **[`reference.md`](reference.md)**.)

---

## Gotchas

- **Linear vs DAG**: `run_pipeline` builds a strictly linear chain. Branches, fan-in, or
  fan-out → hand-build the dict + `save_project_workflow` + `run_project_workflow`.
- **Dual-input is editor-only**: registration's `input`/`input_t` ports are saved by the web
  UI but the executor ignores `to.port` and never passes `--moving`. Use `run_job` for
  fixed+moving. Do not put a registration node in a pipeline/DAG expecting two inputs.
- **Match edges by `nodeId`, not array order**: the executor keys everything off `to.nodeId`
  /`from.nodeId`. Don't rely on edge list ordering (it's unreliable — see
  `/node-pipeline-expert`).
- **One input edge per process block wins**: the executor uses the *first* edge into a block;
  a process node with two upstream edges still only consumes one (the other is dropped).
- **Validate the DAG**: no cycles (raises), and every process block must be reachable so its
  input file exists at run time — otherwise `"Missing input for block <id>"`.
- **Final output = last process block in topo order**, then published to
  `/api/files/outputs/<id>` as `output_url` + `output_file_id`. Branch tips that aren't last
  in topo order are NOT returned.
- **`timeout_s` cap ~540s**: clamped to `[10, 540]`. Long chains can exceed it → returns
  `status:"running"` with NO resumable handle. Shrink params (e.g. larger `voxel_size`),
  split the chain, or raise `timeout_s` toward 540.
- **API-key rotation lockout**: `generate_project_api_key` invalidates the current key;
  `revoke_project_api_key` kills it. If it's the key this session uses, you lose access.
  Confirm before rotating.
- **In-memory / ephemeral**: `run_job` jobs live in memory (lost on restart); standalone
  workflows have no job handle at all. Persist results via `output_file_id` / `output_url`.
- **Persist only config**: a saved workflow stores `moduleId/methodId/params`, never job ids
  or transient results.
- **`delete_project` is irreversible** — it removes the on-disk `data/project_<id>` tree.

## See also
- `ppline-3dcv:using-ppline` — universal recipe + module/method catalog + `upload_file`/`use_sample`
- `ppline-3dcv:mcp-tool-reference` — every MCP tool, flat
- `ppline-3dcv:point-cloud-registration`, `ppline-3dcv:medical-imaging` — dual-input via `run_job`
- [`reference.md`](reference.md) — full schema, topo execution, dual-input port detail, DAG example
