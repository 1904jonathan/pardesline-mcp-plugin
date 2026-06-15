---
name: latex-scientific-core
description: "Foundational reference for writing rigorous scientific documents in LaTeX, independent of output format (paper, thesis, or Beamer slides). Use this skill whenever a LaTeX task involves scientific rigor: mathematical typesetting (amsmath, equations, theorems), bibliography and citation management (biblatex/biber vs bibtex, .bib hygiene, citation commands), figures and tables (graphicx, booktabs, subcaption, TikZ, pgfplots), cross-referencing (cleveref, labels), algorithms (algorithm2e/algorithmic), units (siunitx), code listings (minted/listings), reproducible compilation (latexmk), and the IMRaD logic that governs scientific argument structure. This is the shared backbone consulted alongside latex-paper-ieee, latex-thesis-research, and latex-beamer-scientific. Trigger it for any scientific LaTeX work even when the specific document type is not yet decided."
---

# LaTeX Scientific Writing — Core Reference

This skill is the **shared backbone** for all scientific LaTeX work. The three format-specific skills (`latex-paper-ieee`, `latex-thesis-research`, `latex-beamer-scientific`) inherit everything here and only add their format constraints. Read this first, then the format skill.

## 0. Operating principles

1. **Rigor over decoration.** Every claim is supported (citation, equation, figure, or derivation). Never invent a citation or a numerical result. If a value is a placeholder, mark it explicitly with `% TODO` and a visible token like `\todo{...}`.
2. **Compile reproducibly.** Always provide a `latexmk` workflow so the user can build in one command. Specify the engine (pdflatex / xelatex / lualatex) and the bib backend (biber / bibtex) explicitly.
3. **Modular files.** Split anything longer than ~2 pages into `\input`/`\include` files. A failed compile then points to a single chapter/section.
4. **Targeted diffs.** When editing an existing project, change the minimal set of lines. Do not rewrite a working preamble.
5. **Separate content from style.** Macros and formatting live in the preamble or a `.sty`; prose lives in chapter/section files.

## 1. Engine and compilation

| Engine | When to use | Bib backend |
|--------|-------------|-------------|
| `pdflatex` | Default, fastest, widest package support. IEEE papers. | `bibtex` or `biber` |
| `xelatex` / `lualatex` | System fonts (`fontspec`), Unicode, `metropolis` Beamer theme (Fira Sans), CJK/Hebrew/Arabic. | `biber` |

**Canonical build:** always prefer `latexmk`. Provide a `.latexmkrc` when the engine is non-default:

```latexmk
# .latexmkrc
$pdf_mode = 1;            # 1 = pdflatex, 4 = lualatex, 5 = xelatex
$bibtex_use = 2;          # run biber/bibtex as needed
$out_dir = 'build';
```

Build commands:
```bash
latexmk -pdf main.tex            # pdflatex
latexmk -lualatex main.tex       # lualatex
latexmk -xelatex main.tex        # xelatex
latexmk -c                       # clean aux files (keep pdf)
```

Manual sequence (when explaining the "??" / missing-citation problem): `pdflatex → biber/bibtex → pdflatex → pdflatex`. The first pass writes `.aux`, the bib pass resolves references, the last two passes settle cross-references and page numbers.

### 1b. Compiling on the platform (ppline-3dcv MCP) — no local LaTeX needed

If the user has **no LaTeX toolchain installed**, compile server-side via the
`ppline-3dcv` MCP server instead of `latexmk`. Two tools, both sandboxed
(no shell-escape) on a **Tectonic** engine that auto-fetches missing CTAN packages:

- `compile_latex(source, engine="tectonic", timeout_s=120, assets=None)` — full LaTeX
  string → PDF. Returns `{ok, pdf_url, pdf_file_id, tex_url, tex_file_id}` (PDF **and**
  the `.tex` are saved as downloadable URLs). On failure: `{ok:false, log_tail}` — read
  the compiler errors, fix the source, call again.
- `create_presentation(title, slides=[...], theme=...)` — structured Beamer deck → PDF
  (see `latex-beamer-scientific`).
- `assets=["plotneuralnet"]` stages the PlotNeuralNet TikZ styles into the compile dir
  (see `latex-plotneuralnet-architectures`).

Caveats vs a local build: Tectonic uses XeTeX semantics (don't add `\usepackage[utf8]{inputenc}`;
UTF-8 is native), runs multi-pass automatically (no manual `biber→pdflatex×2`), and
`minted`/`-shell-escape` is **not** available (use `listings`). The **edit loop**: save the
returned `.tex` locally; the user edits it; re-read the file and call `compile_latex` again.
The MCP-tool usage reference is `ppline-3dcv:research-and-presentations`.

## 2. The scientific argument: IMRaD logic

LaTeX is only the typesetting layer. The *content* of any empirical scientific document follows **IMRaD** — Introduction, Methods, Results, and Discussion — mirroring the scientific method. Keep the **hourglass shape**: broad context → narrow methods/results → broad implications.

**Introduction (three moves / CARS):**
1. *Establish the territory* — present the problem in a wide context ("big picture"), state why it matters.
2. *Establish the niche* — review the current state of the field, then expose the **gap** or unsolved problem.
3. *Occupy the niche* — state how this work fills the gap; end with explicit contributions / hypotheses / research questions.

**Methods:** enough detail for **replication**. Materials, data, procedure (chronological), software/stats, and *justification* of each design choice. Past tense, often passive.

**Results:** **report only**, no interpretation. State facts without judgment words ("surprisingly", "unfortunately"). Lean on figures/tables; the text points to them, it does not duplicate them.

**Discussion:** **interpret**. Relate results back to the gap and to prior work (compare/contrast with citations), state limitations honestly, give implications and future work. Mirror the introduction's structure in reverse (narrow → broad).

**Abstract:** one paragraph condensing all four: purpose+importance (1–2 sentences), methods (1–2), main findings (a few), implications (1–2). Write it last.

For a thesis, this expands into a chapter-level structure (see `latex-thesis-research`). For a paper, it maps onto sections (see `latex-paper-ieee`).

## 3. Preamble starter (format-agnostic scientific block)

```latex
% --- Math ---
\usepackage{amsmath,amssymb,amsthm,mathtools}   % mathtools supersedes/extends amsmath
\usepackage{bm}                                  % bold math symbols (vectors/tensors)
\usepackage{siunitx}                             % \SI{9.81}{m/s^2}, aligned units & numbers

% --- Figures & tables ---
\usepackage{graphicx}
\usepackage{booktabs}                            % \toprule \midrule \bottomrule — NEVER vertical rules
\usepackage{subcaption}                          % subfigures with subref
\usepackage{float}                               % [H] placement when truly needed
\usepackage{adjustbox}                           % scale wide tables/figures

% --- Code & algorithms ---
\usepackage[ruled,vlined,linesnumbered]{algorithm2e}  % OR algorithmicx/algpseudocode
\usepackage{listings}                            % or minted (needs -shell-escape + Pygments)

% --- Cross-refs (load order matters: hyperref then cleveref, last) ---
\usepackage[hidelinks]{hyperref}
\usepackage{cleveref}                            % \cref{...} -> "Figure 3", "Eq. (2)"
```

**Load order rule:** `hyperref` near-last, `cleveref` *after* `hyperref`. `siunitx`, `booktabs` order-insensitive.

## 4. Mathematics

- Numbered display equations: `equation`. Multi-line/aligned: `align`, `gather`, `split` (all from amsmath). **Never** use `eqnarray` (obsolete, bad spacing).
- Reference equations with `\cref{eq:...}` / `\eqref{eq:...}`, never hardcode numbers.
- Theorem-like environments via `amsthm`:
```latex
\theoremstyle{plain}   \newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\theoremstyle{definition} \newtheorem{definition}{Definition}[section]
\newtheorem{assumption}{Assumption}
\theoremstyle{remark}  \newtheorem{remark}{Remark}
```
- Define reusable operators/notation in the preamble for consistency:
```latex
\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator*{\argmax}{arg\,max}
\newcommand{\R}{\mathbb{R}}
\newcommand{\E}{\mathbb{E}}
\newcommand{\norm}[1]{\left\lVert #1 \right\rVert}
\newcommand{\given}{\,\vert\,}
```
- Vectors/matrices: pick one convention (`\mathbf` or `\bm`) and apply it everywhere.

## 5. Figures and tables

**Figures** — always `\centering`, a `\caption` *below*, and a `\label` *after* the caption:
```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=0.8\linewidth]{figures/pipeline.pdf}
  \caption{One-sentence claim the figure supports, not just a noun phrase.}
  \label{fig:pipeline}
\end{figure}
```
- Prefer **vector** formats (`.pdf`, `.eps`) for plots/diagrams; raster (`.png`) only for photos/screenshots.
- `\graphicspath{{figures/}}` so paths stay short.
- Subfigures:
```latex
\begin{figure}[t]\centering
  \begin{subfigure}[b]{0.48\linewidth}\centering
    \includegraphics[width=\linewidth]{a.pdf}\caption{}\label{fig:a}\end{subfigure}\hfill
  \begin{subfigure}[b]{0.48\linewidth}\centering
    \includegraphics[width=\linewidth]{b.pdf}\caption{}\label{fig:b}\end{subfigure}
  \caption{Overall caption; refer to \subref{fig:a} and \subref{fig:b}.}
\end{figure}
```

**Tables** — caption *above*, `booktabs` rules only (no `|`, no `\hline`):
```latex
\begin{table}[t]\centering
  \caption{Results on the test set. Best in \textbf{bold}.}
  \label{tab:results}
  \begin{tabular}{lccc}
    \toprule
    Method & Accuracy & F1 & Inference (ms) \\
    \midrule
    Baseline      & 89.1 & 0.86 & 8 \\
    \textbf{Ours} & \textbf{94.2} & \textbf{0.91} & 12 \\
    \bottomrule
  \end{tabular}
\end{table}
```
- Align numbers on the decimal with `siunitx`'s `S` column type: `\begin{tabular}{l S[table-format=2.1]}`.
- Wide tables: `\resizebox{\linewidth}{!}{...}` or `adjustbox`, or rotate with `\begin{sidewaystable}` (rotating/`rotfloat`).

## 6. Plotting natively (TikZ / pgfplots)

For reproducible, vector, font-matched plots, prefer pgfplots over importing external images:
```latex
\usepackage{pgfplots}\pgfplotsset{compat=1.18}
...
\begin{figure}[t]\centering
\begin{tikzpicture}
  \begin{axis}[xlabel={Epoch}, ylabel={Loss}, legend pos=north east, grid=both]
    \addplot table[x=epoch,y=train,col sep=comma]{data/loss.csv};
    \addplot table[x=epoch,y=val,col sep=comma]{data/loss.csv};
    \legend{train, val}
  \end{axis}
\end{tikzpicture}
\caption{Training and validation loss.}
\end{figure}
```
Diagrams (architectures, flowcharts): TikZ with libraries `positioning`, `arrows.meta`, `fit`, `calc`.

**Neural-network architecture diagrams** (3D box-and-arrow CNN/U-Net/ResNet figures): use the dedicated `latex-plotneuralnet-architectures` skill (PlotNeuralNet), which generates a standalone cropped PDF to `\includegraphics`.

## 7. Algorithms

```latex
\usepackage[ruled,vlined,linesnumbered]{algorithm2e}
\begin{algorithm}[t]
\caption{Training loop}\label{alg:train}
\KwIn{dataset $\mathcal{D}$, learning rate $\eta$}
\KwOut{parameters $\theta$}
Initialize $\theta$\;
\For{$t \leftarrow 1$ \KwTo $T$}{
  Sample minibatch $B \subset \mathcal{D}$\;
  $\theta \leftarrow \theta - \eta\,\nabla_\theta \mathcal{L}(\theta; B)$\;
}
\Return $\theta$\;
\end{algorithm}
```
Alternative stack: `algorithm` + `algpseudocode` (algorithmicx). Pick one per project.

## 8. Code listings

`listings` (no external dependency):
```latex
\lstset{basicstyle=\ttfamily\small, keywordstyle=\color{blue},
        commentstyle=\color{gray}, frame=single, breaklines=true,
        numbers=left, numberstyle=\tiny}
\begin{lstlisting}[language=Python, caption={Forward pass}, label=lst:fwd]
def forward(x):
    return model(x)
\end{lstlisting}
```
`minted` (prettier, needs Python `Pygments` and compiling with `-shell-escape`): use only if the user can enable shell-escape.

## 9. Bibliography and citations

**Decision:** use **biblatex + biber** for new work (full Unicode, flexible styles, better sorting, localization). Use **bibtex** (or `natbib`) only when the venue's template demands it (many IEEE/ACM/Elsevier templates ship a `.bst`).

### biblatex + biber (recommended default)
```latex
\usepackage[backend=biber, style=numeric, sorting=nyt, doi=true, url=false, isbn=false]{biblatex}
\addbibresource{references.bib}
...
\textcite{key}     % "Smith (2024) showed..."
\parencite{key}    % "(Smith, 2024)" / "[3]"
\cite{key}
...
\printbibliography
```
Common styles: `numeric`, `numeric-comp` (ranges [1–3]), `authoryear`, `authoryear-comp`, `alphabetic`, `ieee`, `apa`. Build: `pdflatex → biber → pdflatex → pdflatex`.

### bibtex (legacy / template-mandated)
```latex
\bibliographystyle{IEEEtran}   % or plain, abbrv, unsrt, plainnat, acm...
\bibliography{references}
```
With `natbib` for author-year: `\usepackage[authoryear,round]{natbib}` → `\citet`, `\citep`. Build: `pdflatex → bibtex → pdflatex → pdflatex`.

### .bib hygiene (non-negotiable)
- One **stable, lowercase** citation key convention: `authorYEARkeyword` (e.g. `rogers2017xray`).
- Protect capitals in titles with braces: `title = {A {CNN}-{BiLSTM} for {ECG}}`.
- Always fill `doi` when available; prefer DOI over URL.
- Prefer published venue over arXiv when both exist; otherwise cite arXiv with `eprint`/`archivePrefix`.
- Never leave `??` in the PDF — that means the bib pass did not run or the key is wrong.
- Do **not** fabricate entries. If the user has not supplied a reference, insert `\todo{cite}` and leave a `% NEEDS CITATION` marker rather than inventing authors/years/DOIs.

Entry template:
```bibtex
@article{rogers2017xray,
  author  = {Rogers, Thomas W. and Jaccard, Nicolas and Morton, Edward J. and Griffin, Lewis D.},
  title   = {Automated X-ray Image Analysis for Cargo Security},
  journal = {IEEE Transactions on ...},
  year    = {2017},
  volume  = {},
  number  = {},
  pages   = {},
  doi     = {},
}
```

## 10. Cross-referencing discipline

- Label immediately after the captioned object; prefix by type: `fig:`, `tab:`, `eq:`, `sec:`, `alg:`, `lst:`, `thm:`, `ch:`.
- Reference with `cleveref`: `\cref{fig:pipeline}` → "Figure 3"; `\Cref{...}` at sentence start; ranges `\crefrange{}{}`.
- Never type "Figure~\ref{...}" by hand once `cleveref` is loaded — it produces inconsistent capitalization/abbreviation.

## 11. Microtypography & language

```latex
\usepackage{microtype}                 % better justification, always on
\usepackage[english]{babel}            % or polyglossia for xelatex/lualatex (multilingual, Hebrew/Arabic)
\usepackage{csquotes}                  % REQUIRED with biblatex+babel for correct quotes
```
- Non-breaking spaces before refs/units/citations: `Fig.~\ref{...}`, `\SI{5}{\milli\second}`, `model~\cite{...}`.
- Use `\,` thin space in numbers/units; `--` for ranges (pp. 10--14), `---` for em-dash.

## 12. Pre-delivery checklist (apply to every scientific LaTeX deliverable)

- [ ] Compiles clean with the stated `latexmk` command, no undefined references, no `??`.
- [ ] No fabricated citations or numbers; placeholders clearly flagged.
- [ ] Every figure/table is referenced in the text and has a meaningful caption.
- [ ] booktabs tables (no vertical rules), vector figures where possible.
- [ ] Equations numbered only if referenced; referenced via `\cref`/`\eqref`.
- [ ] Consistent notation (one vector/matrix convention, operators predefined).
- [ ] Bibliography style matches venue; `.bib` keys consistent; DOIs present.
- [ ] `microtype` on; `csquotes` loaded if biblatex+babel.
- [ ] Modular files; preamble separated from content.
