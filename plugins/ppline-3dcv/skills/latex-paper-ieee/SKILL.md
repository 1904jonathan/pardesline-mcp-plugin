---
name: latex-paper-ieee
description: "Use this skill to plan and write a scientific paper in LaTeX — IEEE conference/journal (IEEEtran), but also generic two-column or journal article styles (ACM acmart, Elsevier elsarticle, Springer LNCS/svjour, arXiv preprint). Triggers: 'IEEE paper', 'conference paper', 'journal paper', 'IEEEtran', 'two-column', 'CVPR/ICASSP/NeurIPS style', 'submit to a journal', 'camera-ready', or any request to produce/structure a research paper or manuscript in LaTeX. It establishes the section plan (IMRaD), the document-class options, author/affiliation blocks, abstract+keywords, figure/table placement under two columns, the numbered IEEE citation style, and a submission/camera-ready checklist. Consult latex-scientific-core alongside this skill for math, figures, and bibliography mechanics."
---

# Scientific Paper in LaTeX (IEEE & journal styles)

Read `latex-scientific-core` first for math/figures/bib mechanics. This skill adds the **paper-specific structure, class options, and submission rules**.

## 1. Choose the class

| Venue | Class line | Bib |
|-------|-----------|-----|
| IEEE conference | `\documentclass[conference]{IEEEtran}` | `IEEEtran.bst` (bibtex) or biblatex `style=ieee` |
| IEEE journal / Transactions | `\documentclass[journal]{IEEEtran}` | same |
| IEEE Computer Society | `\documentclass[10pt,journal,compsoc]{IEEEtran}` | same |
| IEEE Access | `\documentclass{ieeeaccess}` (journal's own) | provided `.bst` |
| ACM | `\documentclass[sigconf]{acmart}` | `ACM-Reference-Format` |
| Elsevier | `\documentclass[preprint,review]{elsarticle}` | `elsarticle-num` |
| Springer LNCS | `\documentclass{llncs}` | `splncs04.bst` |
| arXiv / generic | `\documentclass[11pt]{article}` + `geometry` | biblatex `numeric` or `authoryear` |

For venue-specific compliance (page limits, anonymity, mandatory sections, checklists, reporting standards) across NeurIPS/CVPR/ACL/MICCAI/Nature/etc., use the dedicated `latex-venue-standards` skill.

**Always tell the user to download the venue's official template** (IEEE Template Selector / Overleaf gallery / ACM / journal author kit) — class files encode exact margins, fonts, and front-matter order, and conferences sometimes ship customized IEEEtran variants (CVPR, ICASSP). Current `IEEEtran.cls` is **v1.8b**; ignore the unofficial `compsocconf` option seen in the wild.

## 2. Section plan (IMRaD → IEEE sections)

A standard 4–8 page paper:

1. **Title** — specific, searchable, no filler.
2. **Authors & affiliations** — `\IEEEauthorblockN` / `\IEEEauthorblockA` (see §4).
3. **Abstract** (`\begin{abstract}`) — 150–250 words: purpose+importance, methods, key quantitative findings, implication. No citations, no undefined acronyms.
4. **Index Terms / Keywords** (`\begin{IEEEkeywords}`) — 4–6, alphabetical.
5. **Introduction** (`\section{Introduction}`) — the three CARS moves: context → gap → contributions. End with an explicit bulleted **contributions** list and a paper-organization sentence.
6. **Related Work** — group thematically, not paper-by-paper; end by positioning *this* work against the gap.
7. **Method / Approach** — problem formulation, notation, model/algorithm, design justifications. Replication-grade detail.
8. **Experiments / Results** — datasets, metrics, implementation details (hyperparameters, hardware), then results tables/figures. **Report only**, no over-interpretation.
9. **Discussion / Analysis** — ablations, error analysis, why it works, limitations.
10. **Conclusion** — restate contribution + main result, future work. No new results.
11. **Acknowledgments** (`\section*{Acknowledgment}`) — unnumbered; remove for double-blind.
12. **References** — IEEE numbered, in order of citation.

Keep the **hourglass**: broad intro → narrow method/results → broad conclusion.

## 3. Minimal IEEE conference skeleton

```latex
\documentclass[conference]{IEEEtran}
\IEEEoverridecommandlockouts        % needed if using \thanks / grant footnotes
\usepackage{cite}                   % IEEE numbered citation handling (bibtex route)
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage[hidelinks]{hyperref}    % load last; cleveref after it if used

\begin{document}
\title{A Specific, Searchable Title Without Filler}

\author{
  \IEEEauthorblockN{Jonathan Tabet}
  \IEEEauthorblockA{\textit{Dept. of Computer Vision} \\
                    \textit{Affiliation} \\
                    City, Country \\
                    email@domain}
  \and
  \IEEEauthorblockN{Second Author}
  \IEEEauthorblockA{\textit{Dept.} \\ \textit{Affiliation} \\ City, Country \\ email}
}
\maketitle

\begin{abstract}
Purpose and importance in one or two sentences. What was done (methods).
Key quantitative findings. What it implies.
\end{abstract}

\begin{IEEEkeywords}
computer vision, deep learning, medical imaging, registration
\end{IEEEkeywords}

\section{Introduction}
% Move 1: territory. Move 2: gap. Move 3: contributions.
Our contributions are:
\begin{itemize}
  \item ...
  \item ...
\end{itemize}

\section{Related Work}
\section{Method}
\section{Experiments}
\section{Discussion}
\section{Conclusion}

\section*{Acknowledgment}   % remove for double-blind

\bibliographystyle{IEEEtran}
\bibliography{references}
\end{document}
```

**biblatex variant** (if you prefer biber): drop `\usepackage{cite}`, the `\bibliographystyle`/`\bibliography` lines, and use:
```latex
\usepackage[backend=biber,style=ieee]{biblatex}
\addbibresource{references.bib}
...
\printbibliography
```
Check the venue accepts biblatex; if it ships only a `.bst`, stay with bibtex.

## 4. Authors, affiliations, special footnotes

- Multiple authors, shared affiliation, superscripts:
```latex
\author{First Author\,$^{1}$ \quad Second Author\,$^{2}$ \\
  $^{1}$Institute A \quad $^{2}$Institute B}
```
- Grant/funding footnote: `\thanks{This work was supported by ...}` inside `\author{...}` (requires `\IEEEoverridecommandlockouts`).
- **Double-blind submission:** anonymize authors (`Anonymous`, remove affiliations), strip Acknowledgments, and neutralize self-citations ("we previously [12]" → "prior work [12]").

## 5. Two-column figure/table mechanics

- Single-column float: `figure`/`table` with `[t]` (top) preferred; bottoms (`[b]`) and `[h]` sparingly.
- **Full-width** (span both columns): starred floats `figure*` / `table*`, which can only be placed `[t]` or `[!t]` at the top of a page.
```latex
\begin{figure*}[t]\centering
  \includegraphics[width=\textwidth]{figures/architecture.pdf}
  \caption{Full-width system architecture.}\label{fig:arch}
\end{figure*}
```
- Captions: figures **below**, tables **above** (`booktabs` only). Keep wide result tables to `\columnwidth`; use `\resizebox{\columnwidth}{!}{...}` if needed.
- Reference everything with `\cref{}` (cleveref) for consistent "Fig.~"/"Table~".
- IEEE convention: "Fig." in body text, "Figure" only at sentence start.

## 6. Math & algorithms in papers

- Number only equations you reference (`\nonumber` / `\notag` otherwise).
- Inline a derivation only if short; long derivations → appendix.
- Algorithms: IEEE papers usually use `algorithmic` (with `algorithm` float) or `algorithm2e`. Keep to one.

## 7. Page-limit survival

- Vector figures, tight `\caption`s, `\vspace{-Xpt}` around floats only as a last resort (many venues forbid margin/spacing hacks — check).
- `\IEEEnoindent`, balance columns on the last page with `\balance` (from `balance` pkg) or `multicol` tricks.
- Move proofs, extra ablations, dataset details to a `\appendix` or supplementary.

## 8. Common IEEE pitfalls

- Forgetting to **remove guidance text** from the template before submission.
- Using `eqnarray` (banned — use `align`).
- Vertical rules in tables (`|`) — IEEE/booktabs style is horizontal rules only.
- Bibliography showing `[?]` → bib pass not run, or `IEEEtran.bst` missing.
- Mixing `cite` package with `natbib` (incompatible) — pick the route that matches your bib backend.
- Hardcoding reference numbers instead of `\cref`/`\eqref`.

## 9. Submission / camera-ready checklist

- [ ] Correct class option (`conference` vs `journal`) and **official** template version.
- [ ] All guidance/boilerplate text removed.
- [ ] Within page limit; columns balanced on last page.
- [ ] Abstract self-contained (no citations, no undefined acronyms), keywords present.
- [ ] Contributions explicitly listed in the introduction.
- [ ] Every figure/table referenced and captioned; figures vector; tables booktabs.
- [ ] References complete with DOIs; numbered IEEE style; no `[?]`.
- [ ] Double-blind handled if required (anonymized, no Acknowledgment, neutral self-cites).
- [ ] PDF fonts embedded (`pdffonts main.pdf` shows all "emb"), correct paper size (US Letter for IEEE).
- [ ] Compiles with `latexmk -pdf main.tex` from clean.

## 10. Other venue notes
- **ACM (`acmart`)**: needs CCS concepts (`\ccsdesc`), `\keywords`, copyright/`\setcopyright`, uses `ACM-Reference-Format` with `\citestyle{acmauthoryear}` or numeric per track.
- **Springer LNCS (`llncs`)**: authors via `\author{}\institute{}`, abstract+keywords, `splncs04` bib, no `\IEEEkeywords`.
- **arXiv preprint**: any class; ensure all `.bbl`/figures are included, no `\write18`/minted-shell-escape (arXiv blocks it unless requested), upload sources not just PDF.
