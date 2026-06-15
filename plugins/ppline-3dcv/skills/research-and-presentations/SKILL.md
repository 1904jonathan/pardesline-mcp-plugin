---
name: research-and-presentations
description: >-
  Search the scientific literature and build LaTeX/Beamer presentations as PDFs, via the
  ppline-3dcv MCP server. search_papers queries OpenAlex (~250M works — title, authors,
  abstract, DOI, citations, open-access PDF) with NO extra login. compile_latex turns raw
  LaTeX into a PDF (sandboxed Tectonic engine, auto-fetches CTAN packages). create_presentation
  builds a Beamer deck from structured slides. Use for "find papers on X", "literature review",
  "make a presentation / slides / Beamer deck", "compile this LaTeX", "turn these papers into
  a slide deck". Pairs naturally: search_papers → create_presentation.
---

# Research & Presentations over MCP

Three tools on the **`ppline-3dcv`** MCP server. They need only your existing
`X-API-Key` (the `PPLINE_API_KEY` the plugin already injects) — **no Consensus /
academic-service / Overleaf login**. The platform calls OpenAlex and runs the LaTeX
compiler server-side.

## 1. `search_papers` — scientific literature search (OpenAlex)

```
search_papers(query, limit=10, year_min=None, open_access_only=False)
```
- `query` — free-text search.
- `limit` — 1–50 results.
- `year_min` — only papers published on/after this year.
- `open_access_only` — restrict to papers with a free full-text PDF.

**Returns** `{query, count, results:[...], source}` where each result has:
`title, authors[], year, venue, doi, citations, is_open_access, pdf_url, openalex_url,
abstract`.

- The `abstract` is the full reconstructed abstract (good enough to summarize / extract a
  method and write code from it).
- For papers with `is_open_access: true`, fetch `pdf_url` (e.g. with WebFetch) to read the
  **full text**. Paywalled papers expose metadata + abstract only — that is a limitation of
  every source, not just this one.

## 2. `compile_latex` — raw LaTeX → PDF

```
compile_latex(source, engine="tectonic", timeout_s=120)
```
Use when **you write the full LaTeX yourself** (TikZ, equations, custom packages, any
document class, not just slides).

- Default engine **Tectonic** is sandboxed (no `\write18` shell-escape) and **auto-downloads
  any missing CTAN package** — so you can use almost any package without server changes.
- **Returns on success** `{ok:true, pdf_url, pdf_file_id, tex_url, tex_file_id, engine}`.
  Both the PDF *and* the `.tex` are saved.
- **Returns on failure** `{ok:false, log_tail}` — the compiler errors. Read `log_tail`, fix
  the source, and call again. This is the normal correction loop.

## 3. `create_presentation` — structured slides → Beamer PDF

```
create_presentation(title, slides, subtitle=None, author=None, institute=None,
                    date=None, theme="Madrid", color_theme=None,
                    aspectratio="169", timeout_s=120)
```
The **easy path** when you don't want to hand-write LaTeX.

- `slides` — a list of `{title, bullets?: [str], body?: str}`. Plain text is auto-escaped.
- `theme` — any Beamer theme (`Madrid`, `Berlin`, `Copenhagen`, `metropolis`, …).
- **Returns** the same shape as `compile_latex` **plus** `generated_source` (the Beamer
  `.tex` it built) and `slides` (count).
- For figures / TikZ / equations, write the source yourself and use `compile_latex`.

## Editing a deck after generation

Backend is a **stateless compiler-as-a-service** — the source of truth is the user's local
`.tex` + the tool call. To let a user edit a deck **without LaTeX installed locally**:

1. After `create_presentation` / `compile_latex`, **save the returned `.tex` (or
   `generated_source`) to a local file** (e.g. `presentation.tex`).
2. The user edits that file in their editor.
3. On "recompile", **read the edited file** and call `compile_latex(source=<edited>)` again.

## Recipe: papers → literature-review deck

```
1. r = search_papers("3D point cloud deep learning segmentation", limit=8, year_min=2017)
2. Build slides from r.results (one slide per paper or grouped by theme; cite year + venue).
3. create_presentation(title="Point-Cloud DL: a short review",
                       author="…", theme="metropolis",
                       slides=[{title, bullets:[…]}, …])
4. Save the returned .tex locally; download the pdf_url.
```

## LaTeX writing craft (companion skills)

These tools are the **compile + search** layer. For *how to write* the document well, route to
the bundled LaTeX-craft skills (they all compile through `compile_latex` / `create_presentation`,
no local TeX needed — see each skill's "Build via the ppline-3dcv MCP" note):

| Need | Skill |
|------|-------|
| Math / figures / tables / bibliography / compilation backbone | `ppline-3dcv:latex-scientific-core` (read first) |
| Conference/journal paper (IEEEtran, ACM, LNCS, arXiv) | `ppline-3dcv:latex-paper-ieee` |
| MSc/PhD thesis (book/report, frontmatter, chapters) | `ppline-3dcv:latex-thesis-research` |
| Academic slides (themes, overlays, columns) | `ppline-3dcv:latex-beamer-scientific` |
| Neural-net architecture diagrams (PlotNeuralNet) | `ppline-3dcv:latex-plotneuralnet-architectures` (use `compile_latex(assets=["plotneuralnet"])`) |
| Venue compliance (NeurIPS/CVPR/MICCAI/Nature… page limits, anonymity) | `ppline-3dcv:latex-venue-standards` |

## Notes
- Both compile tools persist the PDF + `.tex` to the platform's output store and return
  absolute, downloadable URLs.
- Calls are metered (best-effort) like every other compute tool; no tier gating.
- See `ppline-3dcv:mcp-tool-reference` for exact return-dict keys and error strings.
