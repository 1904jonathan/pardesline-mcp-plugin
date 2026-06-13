---
name: deep-learning-models
description: >-
  Discover and use the platform's deep-learning model-skills via the ppline-3dcv MCP
  server — reference architectures (e.g. PointNet) with exact training recipes,
  hyper-parameters, a bring-your-own-data format contract, a runnable reference
  implementation and bundled sample data. Use when the user wants to train, fine-tune,
  or pick a neural model for point clouds / meshes / volumes (classification,
  segmentation, registration).
---

# Deep-Learning Model-Skills (ppline-3dcv)

Help a developer **train / fine-tune a neural 3D model on their OWN data**, grounded in the
platform's model-skills knowledge layer. Every claim below is taken from real files in the
repo — do not invent fields, hyper-parameters, or models that the registry does not list.

> **This is DISTINCT from classical `run_job` modules** (`ppline-3dcv:using-ppline`,
> `ppline-3dcv:pointcloud-ops`, etc.). Those `run_modules()` / `run_job()` entries are
> one-shot Open3D / PyVista / SimpleITK *algorithms* that execute on the server and return an
> output file. Model-skills are about **TRAINING / FINE-TUNING neural networks** — the platform
> hands you the architecture, the exact converging hyper-parameters, a bring-your-own-data
> contract, a runnable reference trainer and synthetic sample data, so you write correct
> training code the first time. The knowledge layer does **not** run training for you (see
> "Knowledge is free, compute is separate").

---

## 1. The two MCP tools + one resource (exact)

These are the only model-skill surfaces. All come from `backend/mcp_server.py`; the data comes
from `backend/processing/model_registry.py` scanning `models/<id>/model.json`.

| Call | Kind | Returns / purpose |
|------|------|-------------------|
| `list_models()` | tool | `list[dict]` — the whole catalog, one dict per model (full field table below). Discover model `id`s. Distinct from `list_modules()`. |
| `get_model_info(model_id)` | tool | one model's dict (same fields), including the **`data_format` contract**. On a bad id returns `{"error": "Model '<id>' not found. Call list_models() for valid ids."}`. |
| `context://model/{model_id}` | resource | **THE full knowledge layer**: architecture, exact hyper-parameters, train / fine-tune / inference recipe, validation gate, gotchas. This is the raw text of `models/<id>/SKILL.md`. |

**Resource fallbacks (real behavior in `model_skill()`):**
- Unknown id → `"No model-skill '<id>'. Available: <comma-list>"`.
- Known id but no `SKILL.md` on disk → `"Model '<id>' has no knowledge-layer SKILL.md (compute-only card)."`
- Otherwise → the full file text (UTF-8). The file ships **inside the Docker image** (unlike
  `.claude/` expert context which does not), so it is available in production.

> **ALWAYS read `context://model/<id>` before advising on or writing training code.** The tool
> dicts give you metadata and the data contract; only the resource has the architecture, the
> regularizer, the optimizer schedule and the gotchas. Skipping it produces silently-wrong code.

---

## 2. The full model dict — every field (`to_api_response`)

`list_models()` and `get_model_info()` return exactly these keys (source:
`ModelRegistry.to_api_response()`):

| Field | Type | Meaning |
|-------|------|---------|
| `id` | str | Unique id (kebab/snake), e.g. `"pointnet"`. Use it for `get_model_info` and `context://model/<id>`. |
| `name` | str | Human name, e.g. `"PointNet"`. |
| `description` | str | What the skill teaches. |
| `use_case` | str | The precise thing a dev would TRAIN this model for, on their own data. |
| `pillar` | str | Landscape pillar (enum, see §5). |
| `task` | str | e.g. `classification`, `semantic_segmentation`, `deformable_registration`. |
| `framework` | str | `pytorch` \| `tensorflow` \| `jax` \| `other`. |
| `license` | str | SPDX id / short label. Flags non-commercial pretrained weights. |
| `papers` | list[dict] | `[{title, year?, url?}]` — grounding literature. |
| `category` | str | Default `"neural"`. |
| `icon` | str | Default `"brain"` (UI). |
| `hardware` | str | Rough training cost / budget, e.g. GPU size + time + accuracy. |
| `data_format` | dict | **The bring-your-own-data contract**: `{task, input, labels?, layout?}`. |
| `has_skill` | bool | **Computed live**: `skill_path(id) is not None` — i.e. `models/<id>/SKILL.md` exists on disk. |
| `has_reference_impl` | bool | **Computed live**: `reference_path(id) is not None` — i.e. the `reference_impl` file (e.g. `reference/train.py`) exists on disk. |
| `has_sample_data` | bool | **Computed live**: `sample_data_path(id) is not None` — i.e. the `sample_data/` dir exists on disk. |

**What the three `has_*` booleans really mean.** They are not free-text flags; the registry
calls `skill_path()` / `reference_path()` / `sample_data_path()`, each of which resolves the path
declared in `model.json` (`skill`, `reference_impl`, `sample_data`) **inside the model's own
folder** and returns it only if it actually exists on disk:
- `has_reference_impl: true` → there is a runnable reference trainer you can execute.
- `has_sample_data: true` → there is correctly-formatted synthetic data to prove the loop before
  using real data.
- `has_skill: true` → `context://model/<id>` will return real knowledge (not the fallback string).

**Path-traversal guard (`_safe_path`).** All three resolvers route through `_safe_path(model_id,
rel)`: empty `rel` → `None`; the target is resolved under `MODELS_DIR/<id>` and rejected (`None`)
if it escapes that folder (traversal attempt); finally returned only if it exists. So these paths
are server-side helpers — you don't fetch the reference file over MCP, you read it from the repo /
Docker image at `models/<id>/...`.

**Auto-discovery (no code to add a model).** `ModelRegistry.refresh()` scans `MODELS_DIR`, and for
each subdirectory that (a) is a directory, (b) does **not** start with `_` (so `models/_schema` is
ignored), and (c) contains a `model.json`, it loads a `ModelDescriptor`. Models are returned sorted
by the `order` field. Dropping a new `models/<name>/` folder with `model.json` + `SKILL.md` adds a
model with zero code changes.

---

## 3. `model.json` schema — required vs optional (`models/_schema/model.schema.json`)

Every model card is validated against this draft-07 schema.

**Required:** `id`, `name`, `pillar`, `task`, `skill`.

**Optional (with defaults from `ModelDescriptor`):** `description` (`""`), `use_case` (`""`),
`framework` (`"other"`), `license` (`""`), `papers` (`[]`), `reference_impl` (`""`),
`sample_data` (`""`), `pretrained_weights` (`""`), `hardware` (`""`), `data_format` (`{}`),
`category` (`"neural"`), `icon` (`"brain"`), `order` (`99`).

**Enums:**
- `pillar` ∈ `pointcloud_lidar, medical, mesh, implicit_sdf, radiance_gsplat, generative,
  foundation_2d, multiview_geometry, registration_3d, foundation_3d_llm, scene_understanding,
  slam_4d, infra`.
- `framework` ∈ `pytorch, tensorflow, jax, other`.
- `data_format` requires `task` + `input`; optional `labels`, `layout`.

Note `pretrained_weights` is parsed by the registry but is **not** included in `to_api_response()`
— so over MCP you learn about pretrained weights from the `SKILL.md` text, not the tool dict.

---

## 4. The discovery + knowledge flow (teach this every time)

```
1. list_models()                     → catalog; pick the right id for the task
2. get_model_info(id)                → metadata + data_format contract (how to lay out data)
3. read context://model/<id>         → FULL architecture + train/fine-tune/inference recipe + gotchas   ← MANDATORY before advising
4. prepare the user's data per data_format (exact layout)
5. run the reference trainer (e.g. reference/train.py) — first on sample_data to prove the loop, then on the user's data
```

Concrete sequence for the currently-available model:
```
list_models()
get_model_info(model_id="pointnet")
read resource context://model/pointnet
# → prepare clouds/ + labels.csv per the contract
python models/pointnet/reference/train.py --data sample_data --epochs 30 --batch 16   # validation gate
python models/pointnet/reference/train.py --data /path/to/my_dataset --num_points 1024 --epochs 200 --batch 32 --lr 1e-3 --out pointnet.pt
```

---

## 5. The catalog WILL grow — never hard-code it

The registry is the source of truth. The MCP docstrings explicitly name **VoxelMorph, 3D U-Net,
MeshCNN** as planned reference models, and the `pillar` enum covers medical, mesh, implicit/SDF,
radiance/gsplat, generative, registration, SLAM/4D, etc. **Always call `list_models()`** rather
than assuming only `pointnet` exists. The section below documents the one model that exists today;
treat it as an example of the level of detail every model card carries — but re-fetch live.

---

## 6. PointNet — the currently available model (FULL)

*Sourced from `models/pointnet/model.json`, `models/pointnet/SKILL.md`,
`models/pointnet/reference/train.py`, `models/pointnet/sample_data/`.*

### Metadata (from `model.json`)
- **id** `pointnet` · **name** `PointNet` · **order** `10` · **category** `neural` · **icon** `brain`
- **pillar** `pointcloud_lidar` · **task** `classification` (the card's primary task; the skill
  also covers part- and semantic-segmentation heads)
- **framework** `pytorch` · **license** `MIT` (commercial-friendly)
- **use_case**: *"Train a classifier or per-point segmenter on YOUR own point-cloud dataset
  (proprietary objects, scans), with few classes and limited labels."*
- **hardware**: *"1 GPU 8GB, ~1-2h to ~89% on ModelNet40 (1024 pts, 200 epochs)"*
- **papers**: PointNet (Qi et al., 2017, arxiv 1612.00593); PointNet++ (Qi et al., 2017,
  arxiv 1706.02413, the hierarchical successor).
- **has_skill / has_reference_impl / has_sample_data**: all **true** — `SKILL.md`,
  `reference/train.py`, and `sample_data/` all exist on disk (validation-gate passed).

### data_format contract (EXACT — from `model.json`)
| Key | Value |
|-----|-------|
| `task` | `classification | part_segmentation | semantic_segmentation` |
| `input` | point cloud `N × 3` (xyz); **optionally** `N × 6` with normals |
| `labels` | classification → **one integer class id per cloud**; segmentation → **one integer label per point** |
| `layout` | a folder of `.ply` / `.npy` clouds + `labels.csv` (classification) **or** matching `.npy` label arrays (segmentation) |

`labels.csv` columns are `file,label` (a relative cloud path + an integer class id). An optional
`classes.txt` (one class name per line) gives nicer logging. The trainer derives
`num_classes = max(label) + 1`.

### Architecture (from `SKILL.md` + verified against `reference/train.py`)
PointNet consumes a **raw unordered set** `N × 3` directly — no voxelization, no meshing. Three
ideas make it work:
1. **Permutation invariance via a symmetric function**: a shared per-point MLP lifts each point to
   a high-dim feature, then a **max-pool over all N points** yields an order-independent global
   descriptor — `f({x₁..xₙ}) ≈ γ( maxᵢ h(xᵢ) )`.
2. **Input/feature alignment via T-Nets**: mini-PointNets regress a **3×3** input transform and a
   **64×64** feature transform (applied by `bmm`), making the net robust to rigid transforms. The
   T-Net predicts a **residual on the identity** (`m + I`). The 64×64 transform is regularized
   toward orthogonal: **`L_reg = ‖I − A Aᵀ‖²`**.
3. **Local ⊕ global concatenation (segmentation)**: per-point (64-d) features are concatenated with
   the (1024-d) global descriptor so each point "sees" the whole shape.

Classification flow: `input (N×3) → T-Net(3) → matmul → shared MLP(64,64) → T-Net(64) → matmul
(+L_reg) → shared MLP(64,128,1024) → max-pool → global(1024) → MLP(512,256,k) → logits`.
Segmentation head: `per-point feat(64) ⊕ global(1024) → shared MLP(512,256,128,m) → per-point
logits`. The reference `PointNetCls` uses `Conv1d` shared MLPs with **BatchNorm1d + ReLU**, a
**Dropout(0.3)** in the head, and returns `(logits, a)` where `a` is the 64×64 transform fed to the
regularizer.

### Training recipe / exact hyper-parameters (from `SKILL.md` + `train.py` defaults)
- **Loss**: `CrossEntropy(logits, y) + reg_weight · ‖I − A Aᵀ‖²`, default **`reg_weight = 1e-3`**.
- **Optimizer**: **Adam**, **lr 1e-3**, **weight_decay 1e-4**.
- **LR schedule**: **StepLR, ×0.5 every 20 epochs**.
- **Points**: classification **1024** (default `--num_points`), segmentation **2048**.
- **Defaults**: `--epochs 200`, `--batch 32`, `--val_split 0.2`, `--seed 0`, device auto
  (`cuda` if available else `cpu`).
- **Result**: **~89% on ModelNet40** (1024 pts, 200 epochs, 1×8GB GPU).
- **Preprocessing (MUST match at inference)**: resample/pad to a fixed `num_points`; **normalize
  into the unit sphere** (subtract centroid, divide by max point norm); train-only augmentation =
  random rotation about the up-axis (z) + small Gaussian jitter (σ≈0.01). The reference helpers are
  `load_cloud` (.npy / .ply via Open3D→trimesh fallback), `normalize_unit_sphere`, `resample`,
  `augment`. The platform's `point_cloud_processing` module (downsample, normal estimation) is the
  natural upstream preprocessor.
- **Fine-tune**: load pretrained weights, replace the final `Linear(256, k)` head with your `k`,
  freeze the backbone for a few epochs, then unfreeze. Best when your dataset is small.
- **Inference**: sample to `num_points`, normalize identically, forward → `argmax` (cls) or
  per-point `argmax` (seg).

### Reference implementation — `models/pointnet/reference/train.py` (exists, runnable)
A complete ~275-line PyTorch classification trainer implementing the contract above: dataset
loader from `labels.csv`, `PointCloudDataset` ((3, N) tensors), `TNet`, `PointNetCls`,
`feature_transform_regularizer`, train/val split, StepLR, and best-val checkpointing
(`torch.save({"model", "num_classes", "num_points", "class_names"})` → default `pointnet.pt`).
Its CLI: `--data` (required), `--task classification`, `--num_points`, `--epochs`, `--batch`,
`--lr`, `--reg_weight`, `--val_split`, `--seed`, `--device`, `--workers`, `--out`. (Segmentation
heads are described in `SKILL.md`; the reference CLI is classification-only.)

### Sample data — `models/pointnet/sample_data/` (exists, in-contract)
A tiny, deterministic, geometrically-separable synthetic set in the **exact classification
contract format**, so you can prove the loop converges before plugging in real data:
- `clouds/` — **96** `.npy` clouds: 4 classes × 24 each = `sphere_000..023`, `cube_*`, `plane_*`,
  `cylinder_*`, each a `float32 (1024, 3)` array.
- `labels.csv` — columns `file,label` (e.g. `clouds/sphere_000.npy,0`), one row per cloud.
- `classes.txt` — `sphere`, `cube`, `plane`, `cylinder` (label ids 0–3).
- `generate.py` — regenerates the set deterministically (seed 1234): `python
  models/pointnet/sample_data/generate.py`.

**Validation gate (prove the loop, then swap in your data):**
```bash
python models/pointnet/reference/train.py --data sample_data --epochs 30 --batch 16 --device cpu
# expected: train loss → ~0.03, train & val acc → 1.000 (it overfits the toy set)
```
If that converges, the loop is correct — point `--data` at your own dataset (same layout).

### PointNet gotchas (from `SKILL.md`)
- **Fixed point count**: PointNet needs a constant `N` per batch — always sample/pad.
- **Normalize consistently**: train and inference must use the *same* normalization, or accuracy
  collapses silently.
- **Feature-transform reg matters**: dropping `L_reg` on the 64×64 T-Net destabilizes training.
- **No local structure**: the global max-pool ignores neighborhoods → weaker on fine detail and
  large scenes. Use PointNet++ / Point Transformer when that matters (separate, future skills).

---

## 7. Knowledge is free, compute is separate

The model-skill **knowledge layer** (`list_models`, `get_model_info`, `context://model/<id>`) is
**free** — it is metering-only, like the other context tools. It returns architecture, recipes and
gotchas so you can write correct training code. It does **not** run training. **Managed GPU
training runs are a separate, future capability** — today you run the reference trainer yourself
(locally or on your own GPU). Do not promise hosted/managed training from these tools.

**Cross-link:** `ppline-3dcv:expert-context-and-models` covers the broader context/knowledge
surface (expert context resources + this model catalog) and where these model-skills sit relative
to the classical `run_job` modules.

---

## 8. Gotchas (skill-level)

- **Read `context://model/<id>` before advising or writing training code** — the tool dicts give
  metadata + the data contract; only the resource holds the architecture, regularizer, optimizer
  schedule, and gotchas. Skipping it yields plausible-but-wrong code.
- **Respect the `data_format` `layout` exactly** — wrong folder layout / column names = training
  fails or the loader can't find labels.
- **Classification vs segmentation label shapes differ** — classification: one integer id *per
  cloud* (in `labels.csv`); segmentation: one integer label *per point* (matching `.npy` arrays).
  Don't mix them.
- **Prove the loop on `sample_data/` first** when the model ships it (`has_sample_data: true`),
  then swap `--data` for the user's dataset.
- **`list_models()` is the source of truth** — the registry auto-discovers and is sorted by
  `order`; it will expand beyond `pointnet` (VoxelMorph / 3D U-Net / MeshCNN planned). Never
  hard-code the catalog.
- **Knowledge is free; managed GPU training is a separate (future) capability** — don't conflate
  reading a skill with running a job.
- **These are NOT `run_job` modules** — don't try to "run" a model-skill via the module API.
