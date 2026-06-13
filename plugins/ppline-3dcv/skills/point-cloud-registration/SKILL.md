---
name: point-cloud-registration
description: >-
  Align/register two point clouds into a common frame via the ppline-3dcv MCP server —
  RANSAC global registration (FPFH feature matching for unknown initial pose), ICP
  refinement (point-to-plane local fit for already-close clouds), the full RANSAC+ICP
  coarse->fine pipeline (large-rotation robust), and non-rigid CPD elastic deformation /
  single-cloud Gaussian pressure warp. Use for "align", "register", "match these scans",
  "fit moving cloud to fixed", "ICP", "RANSAC", "coherent point drift", "deform/warp a
  point cloud", or any two-cloud rigid/elastic alignment task.
---

# Point Cloud Registration (dual-input)

This skill is the exhaustive, script-grounded guide for the **`registration`** and
**`deformable_registration`** modules of the `ppline-3dcv` MCP server. Everything below is
read from the actual scripts in `modules/registration/scripts/` and
`modules/deformable_registration/scripts/` — the parameter semantics, outputs, and gotchas
are what the code *really does*, not the manifest defaults.

Universal call/output/upload mechanics (recipe, `file_id` lifecycle, blocking model,
absolute URLs) live in **`ppline-3dcv:using-ppline`** (read first) and the exact tool
signatures in **`ppline-3dcv:mcp-tool-reference`** (`run_job`/`run_pipeline` shape,
`visualize_*` deep-links). Built-in sample ids are in **`ppline-3dcv:samples-catalog`**.

---

## ⚠️ THE dual-input rule (the #1 thing people get wrong — read twice)

`registration` (and `deformable_registration:cpd_deformable`) is **DUAL-INPUT**. Every
script in this skill takes two clouds:

| Role | CLI flag | `run_job` arg (pass ONE of) |
|------|----------|-----------------------------|
| **Fixed** = target (stays put) | `--input` | `file_id="..."` **or** `sample_id="..."` |
| **Moving** = source (gets transformed onto fixed) | `--moving` | `moving_file_id="..."` **or** `moving_sample_id="..."` |

- **If you OMIT the moving input, the script SYNTHESIZES a moving cloud by rotating/translating
  a copy of the fixed cloud, then "registers" that copy back onto the fixed.** This is the
  scripts' *demo mode*. It produces a high fitness (~0.6–1.0) and looks perfectly aligned, but
  it is **input-vs-itself self-alignment** — completely meaningless for real data. This was the
  original #1 user complaint ("ICP/RANSAC modules register input 1 with itself"). The cause was
  scripts ignoring `--moving`; that is fixed, but **omitting `moving_*` silently re-enters the
  same demo trap.** ALWAYS pass a moving input.
- **`run_pipeline` CANNOT do dual-input** — a pipeline step has exactly one input
  (`file_id` chained step→step). There is no `moving_*` per step. **Always use `run_job` for
  any `registration` or `cpd_deformable` call.** (`gaussian_deformation` is single-input and
  *can* go in a pipeline — see below.)
- The frontend auto-hides `demo_only` params (`rotation_degrees`) once a moving cloud is
  connected. Over MCP you control this yourself: with a real moving cloud, `rotation_degrees`
  is simply ignored.

If your registration result shows suspiciously perfect fitness on data you expected to be
hard, **you almost certainly forgot `moving_*`.**

---

## Common mechanics shared by all three `registration` methods

All three scripts (`ransac_global`, `icp_refinement`, `ransac_icp_pipeline`) share this
exact behaviour — know it once:

### voxel_size auto-correction (important)
The manifest default is `voxel_size=0.5`, but **the script almost never uses 0.5 literally.**
Each script computes the **target's bbox diagonal** `t_diag` and applies:
```
auto_vs = t_diag * 0.013          # 1.3% of diagonal = the Open3D tutorial value
if user_vs <= 0  OR  user_vs < t_diag*0.005  OR  user_vs > t_diag*0.05:
    voxel_size = auto_vs           # override — user value was outside the [0.5%, 5%] sweet spot
```
- So `voxel_size=0.5` on the Open3D demo pair (bbox diag ~3.0) is **out of band → auto-corrected
  to ~0.0395**. That is *intended* and safe — leaving `voxel_size=0.5` works.
- `voxel_size=0` explicitly means "auto" (1.3% of diagonal).
- Only a value **inside** `[0.5%, 5%]` of the target diagonal is honoured verbatim. If your
  clouds are at an unusual scale and you want manual control, set `voxel_size` to ~1–5% of the
  fixed cloud's bbox diagonal.

### Why voxel_size matters (RANSAC feature scale)
voxel_size drives the entire FPFH feature pipeline (`ransac_global` and `ransac_icp_pipeline`,
plus the RANSAC pre-pass inside `icp_refinement`):
- downsample voxel = `voxel_size`
- normal estimation radius = `voxel_size * 2`, max_nn=30
- FPFH feature radius = `voxel_size * 5`, max_nn=100
- RANSAC `max_correspondence_distance` = `voxel_size * 1.5`, `ransac_n=3`, edge-length checker
  0.9, distance checker `voxel_size*1.5`, criteria `(100000, 0.999)`, `mutual_filter=True`,
  point-to-point estimation.

**Too small** → FPFH finds no repeatable features → `fitness=0`. **Too large** → downsampling
erases all geometric detail → no correspondences. The auto-correction exists precisely to keep
you in the band; trust it unless you have a reason not to.

### Output (identical shape for all three)
- **Primary output** (`output_url`, `output_type` = point cloud `.ply`): the **aligned moving
  cloud only**, transformed by the recovered matrix and **painted uniform yellow `[1.0, 0.85, 0.0]`**.
  Output normals are re-estimated (radius `voxel_size*2`) so the viewer shades points. The fixed
  cloud is NOT included in the output file — overlay it yourself in a viewer if you want both.
- **Transform sidecar JSON** (in `extra_outputs`, `<output>.json`):
  - `transformation_matrix` — 4×4 row-major list (the rigid `T = (R, t)` that maps moving→fixed)
  - `fitness` — inlier overlap ratio (higher = better; ~0.61 on the canonical Open3D pair)
  - `inlier_rmse` — RMS error of inlier correspondences (lower = better; ~0.0063 on the demo pair)
  - `correspondence_count` — number of inlier correspondences
  - `ransac_icp_pipeline` additionally adds `ransac_fitness`, `ransac_inlier_rmse`
  - `icp_refinement` additionally adds `method` ("point-to-plane (with point-to-point fallback)")
- **No transform is `.tfm`/`.hdf5`** — these are point-cloud rigid transforms saved as JSON only.
- **Reading results:** check `extra_outputs` for the `.json`, parse `fitness`/`inlier_rmse` to
  judge quality. Download the aligned cloud from `output_url`.

### Quality reference (canonical Open3D demo pair `icp_target` + `icp_source`)
- `ransac_global` → fitness ≈ 0.656, RMSE ≈ 0.023 (coarse; RANSAC is stochastic, varies a little)
- `icp_refinement` → fitness ≈ 0.612, RMSE ≈ 0.006263
- `ransac_icp_pipeline` → fitness ≈ 0.612, RMSE ≈ 0.006263 (matches the Open3D tutorial's
  reported 0.621 / 0.006581; small delta is RANSAC variance)
- On a perfectly-overlapping synthetic pair, `ransac_icp_pipeline` → fitness 1.000, RMSE 0.000.

---

## Method 1 — `registration` / `ransac_global`  (coarse, unknown pose)

**Purpose (what the script does):** Global registration from scratch with **no initial guess**.
Downsamples both clouds, estimates normals, computes FPFH features on both, then runs
`registration_ransac_based_on_feature_matching` (RANSAC over FPFH correspondences) to find a
rigid transform. This is the right tool when the two clouds are in **arbitrary relative pose**
(large unknown rotation/translation) and you have no prior alignment.

**Input requirement:** two clouds. The script estimates normals + FPFH **internally** — you do
NOT need to pre-run feature extraction. Fixed via `--input`, moving via `--moving`.

**Output:** aligned moving cloud (yellow) + transform JSON (`transformation_matrix`, `fitness`,
`inlier_rmse`, `correspondence_count`). No ICP polish — expect a coarse fit (RMSE ~0.02 on the
demo), good enough to seed ICP but not metrologically tight on its own.

**Parameters:**
| Param | Type | Default | Range | Effect |
|-------|------|---------|-------|--------|
| `voxel_size` | float | 0.5 | 0–0.9 | Feature/downsample scale; auto-corrected to 1.3% of target bbox diag unless inside [0.5%,5%] of diag. `0` = auto. See "Common mechanics". |

**Example:**
```text
run_job(module_id="registration", method_id="ransac_global",
        sample_id="icp_target", moving_sample_id="icp_source",
        params={"voxel_size": 0.5})
```

**Gotchas:** stochastic — re-running gives slightly different fitness. If `fitness=0`, voxel_size
is off (let it auto-correct) or the clouds genuinely don't overlap. Use this as a coarse stage;
follow with `icp_refinement`, or just use `ransac_icp_pipeline` to get both in one job.

---

## Method 2 — `registration` / `icp_refinement`  (already roughly aligned → fine fit)

**Purpose (what the script does):** Tutorial-faithful ICP, but robust to a bad start. Despite the
name, it does **not** assume an identity init — it runs a quick **FPFH-RANSAC pre-pass** to get a
`trans_init`; if that pre-pass `fitness > 0.3` it seeds ICP with it, otherwise it falls back to a
**center-of-mass translation-only** init. Then:
1. point-to-plane ICP on the **downsampled** clouds (threshold `voxel_size*1.5`), with a
   **point-to-point fallback** if point-to-plane returns `fitness==0` (the silent-NaN-normals case);
2. **re-estimates normals on the full-resolution clouds** (radius `voxel_size*2`) — critical
   because some demo files (e.g. `icp_target.ply`) ship with NaN normals that make point-to-plane
   silently return 0 correspondences;
3. a single **full-resolution** point-to-plane refinement at threshold `voxel_size*0.4` (the
   tutorial value), again with point-to-point fallback. It keeps the downsampled result if the
   full-res pass is unusable.

ICP is a **local** optimizer: it polishes an alignment that is already close. For large unknown
rotations (>~30°) prefer `ransac_icp_pipeline` (the pre-pass here helps, but the full pipeline is
purpose-built for it).

**Input requirement:** two clouds (fixed `--input`, moving `--moving`). Normals are handled
internally; no pre-processing needed.

**Output:** aligned moving cloud (yellow) + transform JSON including `method` and the final
`fitness`/`inlier_rmse`/`correspondence_count`.

**Parameters:**
| Param | Type | Default | Range | Effect |
|-------|------|---------|-------|--------|
| `voxel_size` | float | 0.5 | 0–0.9 | Downsample + ICP threshold scale (thresholds derive as `*1.5` coarse, `*0.4` fine). Auto-corrected as in "Common mechanics". |
| `max_iterations` | int | 2000 | 100–10000 | Max ICP iterations per stage; also `ICPConvergenceCriteria(relative_fitness=1e-6, relative_rmse=1e-6)`. ICP usually converges well before the cap; raising it rarely changes a good fit, but helps a slow-converging hard pair. |

**Example:**
```text
run_job(module_id="registration", method_id="icp_refinement",
        sample_id="icp_target", moving_sample_id="icp_source",
        params={"voxel_size": 0.5, "max_iterations": 2000})
```

**Gotchas:** if `fitness=0` even after the fallbacks, the clouds likely don't overlap or the
voxel_size landed wrong. Do **not** chase ultra-fine thresholds — a further pass at
`voxel_size*0.1` *drops* fitness (~0.68→0.20 on the demo) because it over-fits below the ~5 mm
data noise floor. The single tutorial-strict full-res pass is correct by design.

---

## Method 3 — `registration` / `ransac_icp_pipeline`  (full coarse→fine; large rotation)

**Purpose (what the script does):** The complete, recommended default. **Phase 1:** RANSAC global
registration via FPFH (same as `ransac_global`) to recover the gross pose. **Phase 2:** ICP
refinement on the **full-resolution** clouds, point-to-plane at threshold `voxel_size*0.4`, seeded
by the RANSAC transform, with a point-to-point fallback on silent failure; if both ICP variants
fail it keeps the RANSAC result. Re-estimates normals on full-res first (NaN-normals guard). This
reproduces the canonical Open3D tutorial result (fitness ≈ 0.612, RMSE ≈ 0.006263). **Use this
when you don't know the relative pose and want a tight final fit in one job** — it is robust to
large rotations because RANSAC does not need an initial guess.

**Input requirement:** two clouds (fixed `--input`, moving `--moving`). All features/normals
internal.

**Output:** aligned moving cloud (yellow) + transform JSON with both the ICP result
(`transformation_matrix`/`fitness`/`inlier_rmse`/`correspondence_count`) and the RANSAC stage
metrics (`ransac_fitness`, `ransac_inlier_rmse`).

**Parameters:**
| Param | Type | Default | Range | Effect |
|-------|------|---------|-------|--------|
| `voxel_size` | float | 0.5 | 0–0.9 | Feature + ICP scale; auto-corrected as in "Common mechanics". |
| `rotation_degrees` | float | 45.0 | 5–90 | **DEMO MODE ONLY** (`demo_only`). Only used when **no** `--moving` is provided, to synthesize the fake moving cloud's rotation (`(angle*0.6, angle, angle*1.3)` rad + translation). **Completely ignored when you pass a real moving cloud.** It does NOT widen ICP's capture range on real data — RANSAC already handles arbitrary rotation. Leave it at 45.0; it is harmless. |

**Example:**
```text
run_job(module_id="registration", method_id="ransac_icp_pipeline",
        sample_id="icp_target", moving_sample_id="icp_source",
        params={"voxel_size": 0.5, "rotation_degrees": 45.0})
```

**Gotchas:** `rotation_degrees` is a frequent misunderstanding — it is *not* a real-data knob, it
only shapes the synthetic demo cloud. With a real `moving_*`, ignore it. RANSAC variance means
fitness wobbles slightly run-to-run; that's expected.

---

## Method 4 — `deformable_registration` / `cpd_deformable`  (DUAL-INPUT; elastic / non-rigid)

**Purpose (what the script does):** Non-rigid alignment via **Coherent Point Drift** (`pycpd`
`DeformableRegistration`). Models the moving (source) points as GMM centroids and deforms them
elastically (EM optimization) to fit the fixed (target) shape — for soft deformations between
two shapes (organs, cloth, growth/deformation studies) that a rigid transform can't capture.
Steps: load both clouds → **joint normalization** (subtract combined center, divide by combined
scale, so source and target share a frame — essential for CPD to converge) → run
`DeformableRegistration(X=target_norm, Y=source_norm, beta, alpha, max_iterations, tol)` →
un-normalize the registered points.

**Input requirement:** two clouds. **This is dual-input** (per-method `dual_input: true`) — pass
`moving_*`. Omitting it triggers the demo path: a synthetic Gaussian-deformed copy of the fixed
cloud is used as the source (self-deformation; not real). No normals/features needed beforehand.

**Output:** a **COMBINED** cloud (different from the rigid methods!): the **fixed target painted
red `[1,0,0]`** + the **registered (deformed) moving painted green `[0,1,0]`**, concatenated into
one `.ply`, with output normals estimated for shading. **There is NO transform-matrix JSON** —
CPD is a free-form deformation field, not a 4×4 matrix. The convergence indicator is the final
CPD `sigma^2` (logged; lower = tighter fit), reported in the job logs (`logs_tail`), not a sidecar.

**Parameters (note: only two are exposed in the manifest; the script accepts more with these
defaults):**
| Param | Type | Default | Range | Effect |
|-------|------|---------|-------|--------|
| `max_iterations` | int | 100 (manifest) / 150 (script) | 10–500 | Max EM iterations. More = tighter fit but slower; CPD is O(N²) so this is the main runtime lever. |
| `tolerance` | float | 0.001 | 0.0001–0.01 | EM convergence tolerance (`tol`). Smaller = stricter convergence, more iterations. |
| `beta` | float | 100.0 (script default; not in manifest) | — | Width of the Gaussian smoothing kernel on the deformation. Larger = stiffer/more rigid, more coherent (neighbors move together); smaller = more local flexibility. |
| `lambda_val` | float | 2.0 (script default → `alpha`; not in manifest) | — | Regularization weight (trades data fit vs. deformation smoothness). Larger = smoother/less deformation. |

**Example:**
```text
run_job(module_id="deformable_registration", method_id="cpd_deformable",
        sample_id="<fixed_shape>", moving_sample_id="<moving_shape>",
        params={"max_iterations": 100, "tolerance": 0.001})
```

**Gotchas:** CPD is **O(N²)** in point count — **downsample large clouds first** (run
`point_cloud_processing:voxel_downsample` via run_job on each cloud, then feed the resulting
file_ids). Output is a combined red+green cloud, NOT a transform — don't look for a matrix JSON.
Requires `pycpd` on the server (already installed). The two clouds do **not** need equal point
counts (CPD handles unequal). It is dual-input, so **`run_job` only**, never `run_pipeline`.

---

## Method 5 — `deformable_registration` / `gaussian_deformation`  (SINGLE-INPUT; synthetic warp)

**Purpose (what the script does):** This is **NOT an alignment** — it **warps one point cloud**.
It applies a localized Gaussian "pressure" push to a single cloud: finds the cloud center, places
a pressure point at the **left side** (min-X, center Y/Z), pushes points in the +X direction with
a Gaussian falloff (`sigma = radius/2`) over a `radius`-ball neighborhood (KD-tree query), up to
`displacement` at the center. Use it to **generate synthetic deformed test data** (e.g. to then
register back with CPD), demonstrate elastic deformation, or create a "dented" variant of a cloud.

**Input requirement:** **ONE** cloud (`--input` only). No `--moving`. It is the only method in
this skill that is **single-input** and therefore the only one usable inside `run_pipeline`.

**Output:** the deformed cloud, **colored by deformation magnitude** (red = high, blue = none;
per-vertex colors). No transform JSON, no metrics sidecar (magnitudes logged to `logs_tail`).

**Parameters:**
| Param | Type | Default | Range | Effect |
|-------|------|---------|-------|--------|
| `displacement` | float | 0.02 (manifest) / 0.003 (script) | 0.001–0.1 | Max push at the pressure center, in **world units** (NOT bbox-relative). On a cloud with bbox > ~1 unit the default looks tiny — scale it up to see real bending. |
| `radius` | float | 0.1 | 0.01–0.5 | Radius of influence of the pressure (world units). Larger = broader, smoother bulge; `sigma` is `radius/2`. |

**Example (single input — pipeline-safe):**
```text
run_job(module_id="deformable_registration", method_id="gaussian_deformation",
        file_id="<one_cloud_file_id>",
        params={"displacement": 0.02, "radius": 0.1})
```

**Gotchas:** displacement/radius are **absolute world units, not bbox-relative**, so the visible
effect depends entirely on your cloud's scale — bump `displacement` for large clouds (this is a
known UI-cap limitation; over MCP just pass a bigger value). It is single-input: do not pass
`moving_*` (ignored). Don't confuse it with `cpd_deformable` — this one neither needs nor uses a
second cloud and does not align anything.

---

## Method selection (cheat sheet)

| Situation | module_id / method_id | key params |
|-----------|------------------------|-----------|
| Coarse, **unknown** initial pose, just need a rough match | `registration` / `ransac_global` | `voxel_size=0.5` |
| Clouds **already roughly aligned**, want a tight fit | `registration` / `icp_refinement` | `voxel_size=0.5, max_iterations=2000` |
| **Don't know the pose / large rotation; want tight fit in one job** (default) | `registration` / `ransac_icp_pipeline` | `voxel_size=0.5, rotation_degrees=45.0` |
| **Elastic / non-rigid** alignment of two shapes (dual) | `deformable_registration` / `cpd_deformable` | `max_iterations=100, tolerance=0.001` |
| **Warp ONE cloud** (make synthetic deformed data; NOT alignment) | `deformable_registration` / `gaussian_deformation` | `displacement=0.02, radius=0.1` |

**When unsure for rigid alignment → `ransac_icp_pipeline`** (global coarse + ICP fine in one call,
robust to arbitrary rotation).

---

## Worked examples

**1) Canonical built-in pair, full coarse→fine pipeline** (the recommended default; pair is
documented in `ppline-3dcv:samples-catalog` — `fixed=icp_target`, `moving=icp_source`, the Open3D
`cloud_bin_1` + `cloud_bin_0` demo):
```text
run_job(module_id="registration", method_id="ransac_icp_pipeline",
        sample_id="icp_target", moving_sample_id="icp_source",
        params={"voxel_size": 0.5, "rotation_degrees": 45.0})
# → output_url: aligned moving cloud (yellow .ply)
# → extra_outputs[*].json: { transformation_matrix, fitness≈0.612, inlier_rmse≈0.0063,
#                            correspondence_count, ransac_fitness, ransac_inlier_rmse }
```

**2) Two uploaded files, already close → ICP refine only:**
```text
fixed  = upload_file("scan_fixed.ply",  <base64>)   # → file_id
moving = upload_file("scan_moving.ply", <base64>)   # → file_id
run_job(module_id="registration", method_id="icp_refinement",
        file_id=fixed["file_id"], moving_file_id=moving["file_id"],
        params={"voxel_size": 0.5, "max_iterations": 2000})
```

**3) Non-rigid CPD on two shapes (dual-input; downsample big clouds first):**
```text
run_job(module_id="deformable_registration", method_id="cpd_deformable",
        sample_id="<fixed_shape>", moving_sample_id="<moving_shape>",
        params={"max_iterations": 100, "tolerance": 0.001})
# → output_url: COMBINED cloud (fixed=red + deformed moving=green). No matrix JSON;
#   final CPD sigma^2 is in logs_tail (lower = tighter).
```

---

## Previewing / inspecting results

- **Preview the input clouds** before/after with the viewer tools (see `ppline-3dcv:mcp-tool-reference`,
  Visualize section): `visualize_sample("icp_target")`, or several at once
  `visualize_samples(["icp_target", "icp_source"])` (one MeshLab-style scene, returns a clickable
  absolute URL). These take **sample ids**, not output urls.
- **The aligned output cloud** is fetched/downloaded via the `output_url` from `run_job` (an
  absolute `/api/files/outputs/<id>.ply`) — it is not a sample, so it does not go through
  `visualize_samples`. To see fixed+moving overlaid, load the fixed sample plus the output file in
  your own viewer, or rely on the rigid methods' yellow-painted output over the red/green
  convention CPD already bakes in.
- **Judge quality from the sidecar JSON** (`extra_outputs`): higher `fitness`, lower `inlier_rmse`.
  For volumetric/medical (CT/MR) registration with deformation/Jacobian QC and the 4-panel slicer,
  use `ppline-3dcv:medical-imaging` (`simpleitk_registration`, `analyze_registration_deformation`,
  `visualize_registration`) — a different module from this point-cloud skill.

---

## Gotchas (lead: the self-alignment trap)

1. **MISSING `--moving` = self-alignment.** The single biggest mistake. Omitting `moving_*`
   makes the script invent a moving cloud from the fixed one and "register" it back → high fitness,
   zero meaning. Always pass `moving_sample_id`/`moving_file_id` for `registration` and
   `cpd_deformable`. Suspiciously perfect fitness on hard data ⇒ you forgot it.
2. **`run_pipeline` can't carry two inputs.** Use `run_job` for every `registration` method and
   for `cpd_deformable`. Only `gaussian_deformation` (single-input) is pipeline-safe.
3. **`voxel_size=0.5` is auto-corrected, not literal.** Scripts override it to ~1.3% of the target
   bbox diagonal unless it's already within [0.5%, 5%] of the diagonal. `0` = auto. Too small →
   no FPFH features → `fitness=0`; too large → detail erased. Leave the default; trust the
   auto-correction.
4. **`rotation_degrees` is demo-only.** It only shapes the synthetic moving cloud when no
   `--moving` is given. With a real moving cloud it is ignored — it does NOT extend ICP's capture
   range (RANSAC handles arbitrary rotation already).
5. **Point-to-plane ICP fails *silently* on NaN normals** (returns `fitness=0, RMSE=0, corr=0`,
   no exception — e.g. `icp_target.ply` ships with NaN normals). The scripts already re-estimate
   normals on full-res and fall back to point-to-point on `fitness==0`. If you still see
   `fitness=0` on real data, the clouds don't overlap or voxel_size is wrong, not a normals bug.
6. **Don't over-refine.** A single full-res ICP pass at `threshold = voxel_size*0.4` is correct.
   An extra ultra-fine pass (`voxel_size*0.1`) *drops* fitness (~0.68→0.20 on the demo) by
   over-fitting below the ~5 mm noise floor. The scripts deliberately do one pass.
7. **Rigid outputs are the aligned MOVING cloud only**, painted yellow — the fixed cloud is not in
   the file. CPD output is a COMBINED red(fixed)+green(deformed-moving) cloud. Know which you got.
8. **CPD has no transform matrix** (free-form field) — convergence is the logged `sigma^2`. The
   rigid methods give a 4×4 `transformation_matrix` JSON; CPD does not.
9. **CPD is O(N²)** — downsample large clouds first (e.g. `point_cloud_processing:voxel_downsample`)
   or it will be slow / hit the ~540 s compute cap.
10. **`gaussian_deformation` is a single-cloud WARP, not an alignment**, and its
    `displacement`/`radius` are **absolute world units** (not bbox-relative) — scale `displacement`
    up for clouds with bbox > 1 unit to see visible bending.
11. **`paint_uniform_color`/per-vertex colors in outputs are expected**, not a bug. (In the web UI
    the material color-picker must disable `vertexColors` to override them; over MCP you just read
    the file as-is.)
12. **Wrong canonical pair note:** the Open3D ICP tutorial pair is `cloud_bin_0`+`cloud_bin_1`
    (= `icp_source`+`icp_target`). An earlier bug shipped `cloud_bin_2` as the target, widening the
    rotation gap; the current samples are correct. Trust `fixed=icp_target, moving=icp_source`.
