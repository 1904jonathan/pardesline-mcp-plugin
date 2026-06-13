# Pipelines & Projects — Reference

Full workflow-dict schema, the exact topological execution model, the dual-input port
caveat, and runnable DAG examples. Grounded in:
- `backend/services/workflow_executor.py` (the executor MCP + `/api/execute` both use)
- `backend/mcp_server.py` (`run_pipeline`, `run_project_workflow`, project tools)
- `backend/routers/api_execute.py`, `backend/routers/projects.py` (REST parity)
- `frontend/js/workflow/{NodeEditor,Operator,Pipeline}.js` (what the web editor saves)

---

## 1. Workflow dict — full schema

```jsonc
{
  "blocks": [
    // --- input node (exactly one is consumed) ---
    {
      "id": "input",            // unique node id
      "type": "file-input"      // "file-input" OR "upload" (executor accepts both)
      // web editor also writes: x, y, fileId, sampleId, sampleSource, geometryType,
      // extension, fileName — ALL IGNORED by the standalone executor
    },

    // --- process node ---
    {
      "id": "step1",            // unique node id (becomes the intermediate filename)
      "type": "process",
      "moduleId": "<module_id>",// from list_modules() / get_module_info()
      "methodId": "<method_id>",
      "params": { /* method params; defaults used when omitted; {} is fine */ }
      // web editor extras (ignored by executor): x, y, operatorName, fileId,
      // sampleId, sampleSource, geometryType, extension, fileName
    }
    // ... more process nodes
  ],

  "edges": [
    {
      "from": { "nodeId": "input" },  // executor reads from.nodeId only
      "to":   { "nodeId": "step1" }   // executor reads to.nodeId only
      // web editor ALSO writes from.port / to.port (e.g. "file", "input",
      // "input_t", "result") — the standalone executor IGNORES ports
    }
  ],

  "zoom": 1.0   // web-editor UI state only; ignored by executor
}
```

### Field reference

| Path | Type | Required | Consumed by executor? | Notes |
|------|------|----------|-----------------------|-------|
| `blocks[].id` | str | yes | yes | unique; intermediate output file is `<id><ext>` |
| `blocks[].type` | str | yes | yes | `"file-input"`/`"upload"` = input; `"process"` = step |
| `blocks[].moduleId` | str | for process | yes | validated against the registry |
| `blocks[].methodId` | str | for process | yes | validated against the registry |
| `blocks[].params` | dict | no | yes | passed as `--<key> <value>` to the script |
| `edges[].from.nodeId` | str | yes | yes | source block id |
| `edges[].to.nodeId` | str | yes | yes | target block id |
| `edges[].from.port` / `to.port` | str | no | **NO** | saved by web UI; executor ignores |
| `zoom`, block `x`/`y`, etc. | — | no | no | UI-only |

`save_project_workflow` requires only that `workflow` is a dict containing a `"blocks"`
list. `run_project_workflow` / `/api/execute` additionally require `blocks` to be non-empty.

---

## 2. Exact execution model (`WorkflowExecutor.execute`)

1. **Topological sort** (`_topological_sort`, Kahn's algorithm) over `blocks` using `edges`
   (`from.nodeId → to.nodeId`). If `len(sorted) != len(blocks)` → raises
   `"Workflow contains cycles - cannot execute"`.
2. **Seed the input**: the first block whose `type` is `"upload"` or `"file-input"` (in topo
   order) is mapped to the single API/primary input file. `node_outputs[input.id] = input_file`.
3. **For each block in topo order**, skipping input nodes:
   - Find the input edge: **`next(e for e in edges if e['to']['nodeId'] == block['id'])`** —
     the **first** edge targeting this block, **by `nodeId` only (port is never read)**.
   - `input_path = node_outputs[input_edge.from.nodeId]`. If there is *no* input edge, it
     falls back to the original API input file.
   - If `input_path` is missing/nonexistent → raises `"Missing input for block <id>"`.
   - Look up the `MethodDescriptor` (`registry.get_method(moduleId, methodId)`); missing →
     `"Method not found: <module>.<method>"`.
   - Output path = `output_dir / f"{block.id}{method.output_extension}"`.
   - Run `execute_script(script_path, input_path, output_path, params)` → effectively
     `python <script> --input <input_path> --output <output_path> [--<param> <val> …]`.
     Non-zero exit → raises `"Block <id> failed: <stderr>"`.
   - `node_outputs[block.id] = output_path`.
4. **Final output**: the **last `process` block in topo order** (`reversed(sorted_blocks)`)
   whose output exists; else the last value in `node_outputs`. MCP then copies it into
   `OUTPUTS_DIR`, persists it, and returns `output_url` + `output_file_id` + `output_type`.

### Key consequences
- **Only ONE upstream feeds a process block** — the first edge by `to.nodeId`. A node wired
  with two incoming edges silently uses one and drops the other.
- **`--moving` is never passed** by the executor → dual-input registration cannot work here.
- **Only ONE primary input** enters the whole graph (the seeded input node). There is no way
  to inject a second independent file via the workflow.
- **The published result is the topo-last process block**, not necessarily a branch you care
  about. Put the block you want returned last.

---

## 3. How `run_pipeline` builds the dict (from `mcp_server.py`)

```python
blocks = [{"id": "input", "type": "file-input"}]
edges  = []
prev   = "input"
for i, step in enumerate(steps):
    bid = f"step{i+1}"
    blocks.append({"id": bid, "type": "process",
                   "moduleId": step["module_id"], "methodId": step["method_id"],
                   "params": step.get("params") or {}})
    edges.append({"from": {"nodeId": prev}, "to": {"nodeId": bid}})
    prev = bid
# -> {"blocks": blocks, "edges": edges}  handed to WorkflowExecutor
```

So `run_pipeline` is purely the linear case of the general dict. For branches / fan-out,
build the dict yourself and `save_project_workflow` → `run_project_workflow`.

---

## 4. DAG example — fan-out then continue on one branch

A single input feeds two independent process steps; only the branch ending in the
topo-last block (`refine`) is returned as the downloadable output.

```python
save_project_workflow(project_id, {
  "blocks": [
    {"id": "input",  "type": "file-input"},
    {"id": "clean",  "type": "process", "moduleId": "point_cloud_processing",
     "methodId": "statistical_outlier_removal", "params": {}},
    {"id": "stats",  "type": "process", "moduleId": "point_cloud_analysis",
     "methodId": "compute_normals", "params": {}},     # side branch off input
    {"id": "refine", "type": "process", "moduleId": "point_cloud_processing",
     "methodId": "voxel_downsample", "params": {"voxel_size": 0.02}},
  ],
  "edges": [
    {"from": {"nodeId": "input"}, "to": {"nodeId": "clean"}},
    {"from": {"nodeId": "input"}, "to": {"nodeId": "stats"}},   # fan-out
    {"from": {"nodeId": "clean"}, "to": {"nodeId": "refine"}},  # main branch
  ],
})
run_project_workflow(project_id, sample_id="<id>")
# returned output = topo-last process block (here: refine). 'stats' runs but is not published.
```

(Module/method ids above are illustrative — confirm real ones via `list_modules()` /
`get_module_info()` per `ppline-3dcv:using-ppline`.)

---

## 5. Dual-input registration — why it belongs in `run_job`, not here

What the **web editor** produces for a registration node (single process block, two ports):

```jsonc
{
  "blocks": [
    {"id": "ct",  "type": "file-input"},
    {"id": "mri", "type": "file-input"},
    {"id": "reg", "type": "process", "moduleId": "simpleitk_registration", "methodId": "rigid"}
  ],
  "edges": [
    {"from": {"nodeId": "ct"},  "port": "file"}, "to": {"nodeId": "reg", "port": "input"}},   // fixed
    {"from": {"nodeId": "mri"}, "port": "file"}, "to": {"nodeId": "reg", "port": "input_t"}}  // moving
  ]
}
```

Port names (`frontend/js/workflow/Operator.js`): process inputs are
`{name:"input", label:"fixed", side:"left"}` and `{name:"input_t", label:"moving",
side:"top"}`. The editor's *in-browser* runner (`NodeEditor.js`) reads `to.port` to split
fixed (`input`) from moving (`input_t`).

**But the standalone executor ignores `to.port`** and never emits `--moving`. So this graph,
when run via `run_project_workflow` / `/api/execute`, would feed only one volume (whichever
edge is found first by `to.nodeId`) on `--input`, and the registration script would
synthesize a moving cloud from the fixed input → self-alignment garbage. There is also no
way to seed a *second* primary input into the executor.

**Correct path for fixed+moving:**

```python
run_job(
  module_id="simpleitk_registration", method_id="rigid",
  file_id="<fixed CT file_id>",            # -> --input
  moving_file_id="<moving MRI file_id>",   # -> --moving
  params={...},
)
```

`run_job` is the only MCP compute tool that resolves and passes a moving path. See
`ppline-3dcv:point-cloud-registration` and `ppline-3dcv:medical-imaging`.

---

## 6. REST parity (for reference)

| MCP tool | REST endpoint | Notes |
|----------|---------------|-------|
| `run_project_workflow` | `POST /api/execute` (multipart `file`, `X-API-Key`) | REST loads `project_<id>/workflow.json` from disk; MCP loads `Project.workflow` from the DB. Same executor, same dict shape. |
| `list_projects` | `GET /api/projects` | REST returns full `api_key`/`workflow`; MCP returns the safe `has_api_key`/`has_workflow` booleans. |
| `create_project` | `POST /api/projects` | both create `data/project_<id>/{uploads,outputs}` |
| `get_project` | `GET /api/projects/{id}` | |
| `delete_project` | `DELETE /api/projects/{id}` | both `rmtree` the project dir (path-guarded under `DATA_DIR`) |
| `get_project_workflow` | `GET /api/projects/{id}/workflow` | both return `{... "workflow": {...}}` |
| `save_project_workflow` | `PUT /api/projects/{id}/workflow` | |
| `generate_project_api_key` | `POST /api/projects/{id}/generate-api-key` | key = `pl_<sha256(token)[:32]>`; REST route requires the `api_access` capability |
| `revoke_project_api_key` | `DELETE /api/projects/{id}/api-key` | |

Note the storage difference: `/api/execute` reads the workflow from a disk file
(`project_<id>/workflow.json`), while the MCP project tools read/write `Project.workflow` in
the database. When driving everything through MCP, this is consistent end-to-end
(`save_project_workflow` → DB → `run_project_workflow` reads DB).
