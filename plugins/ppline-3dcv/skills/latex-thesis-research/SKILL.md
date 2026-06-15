---
name: latex-thesis-research
description: "Use this skill to plan and write a long-form research dissertation in LaTeX — Master's research thesis, MSc/MRes report, or PhD thesis. Triggers: 'thesis', 'dissertation', 'PhD thesis', 'master thesis', 'memoire', 'these', 'book/report class', 'frontmatter/mainmatter/backmatter', 'chapters', 'list of figures', 'glossary/acronyms', 'declaration', 'abstract chapter', or any multi-chapter scientific document with front matter, numbered chapters, an appendix, and a full bibliography. It establishes the overall plan (title page, declaration, abstract, acknowledgements, ToC/LoF/LoT, chapter-level IMRaD across Introduction → Literature Review → Methodology → Results → Discussion → Conclusion, appendices, references), the modular file layout, glossary/acronym handling, and a defense-ready checklist. Consult latex-scientific-core alongside this skill for math, figures, and bibliography mechanics."
---

# Research Thesis / Dissertation in LaTeX

Read `latex-scientific-core` first. This skill adds the **multi-chapter document architecture, front/back matter, and thesis-specific tooling**.

## 0. Rule #1 — check the university template first

Almost every graduate school provides an **official `.cls` or template** encoding required margins, font size, line spacing, title-page wording, and front-matter order. Always start there. Only fall back to a generic `book`/`report` build when none exists. Never override a university class's margins/spacing — examiners reject on formatting.

## 1. Document class & top-level structure

Use `book` (two-sided, `\frontmatter/\mainmatter/\backmatter` available) or `report` (one-sided default, chapters but no automatic matter switches). Theses are usually `12pt`, `a4paper`.

```latex
\documentclass[12pt,a4paper,oneside]{book}   % oneside for PDF submission; twoside for print
\input{preamble}                              % all packages + macros live here

\begin{document}

\frontmatter            % roman page numbers, chapters unnumbered
\input{frontmatter/titlepage}
\input{frontmatter/declaration}
\input{frontmatter/abstract}
\input{frontmatter/acknowledgements}
\tableofcontents
\listoffigures
\listoftables
\input{frontmatter/acronyms}      % printed glossary/acronym list (optional here)

\mainmatter             % arabic page numbers, numbered chapters
\include{chapters/01-introduction}
\include{chapters/02-literature}
\include{chapters/03-methodology}
\include{chapters/04-results}
\include{chapters/05-discussion}
\include{chapters/06-conclusion}

\appendix
\include{appendices/A-derivations}
\include{appendices/B-extra-results}

\backmatter             % chapter numbering off
\printbibliography[heading=bibintoc, title={References}]
% \printglossaries  % if using glossaries package for terms

\end{document}
```

Key mechanics:
- `\frontmatter` → roman numerals (i, ii, …), unnumbered chapters in ToC.
- `\mainmatter` → resets to arabic (1, 2, …), numbered chapters.
- `\backmatter` → keeps arabic but turns *off* chapter numbering (for bibliography/index).
- `\include{}` (not `\input`) for chapters: forces a page break and enables `\includeonly{}` to compile a single chapter while drafting — huge time saver, and isolates compile errors to one chapter.

## 2. Chapter plan (thesis-level IMRaD)

The thesis is IMRaD expanded to chapter scale, keeping the global hourglass (broad → narrow → broad):

1. **Introduction** — motivation, problem statement, **gap**, research questions/objectives, contributions, thesis outline (one paragraph mapping each chapter).
2. **Background / Literature Review** — systematic, thematically organized synthesis; ends by articulating exactly what is missing and how the thesis addresses it. Not a list of summaries.
3. **Methodology / Approach** — formal problem definition, notation, datasets, models/algorithms, experimental design, with full justification. Replication-grade.
4. **Results** — report findings objectively (figures/tables), per research question. No interpretation.
5. **Discussion** — interpret against the gap and prior work; ablations, error analysis, limitations, threats to validity.
6. **Conclusion** — restate contributions and main findings, broader implications, future work. No new results.

For a thesis bundling published papers ("stapler"/article-based thesis), each results chapter wraps a paper with a linking introduction; a unifying intro+conclusion bookend them.

## 3. Front matter components

- **Title page**: exact wording is dictated by the university (degree, department, year, supervisor). If using a generic class, build it manually with `\begin{titlepage}`.
- **Declaration / statement of originality**: signed statement that the work is the author's own; usually mandatory.
- **Abstract**: one page condensing the whole thesis (problem, methods, key results, contribution). Sometimes a second abstract in another language (e.g. Hebrew/French) — use `polyglossia` (xelatex/lualatex) for RTL/accented scripts.
- **Acknowledgements**: informal, optional.
- **ToC / List of Figures / List of Tables**: automatic (`\tableofcontents`, `\listoffigures`, `\listoftables`).
- **List of Acronyms / Glossary / Nomenclature**: see §5.

## 4. Modular file layout (recommended)

```
thesis/
├── main.tex
├── preamble.tex
├── references.bib
├── frontmatter/
│   ├── titlepage.tex  declaration.tex  abstract.tex  acknowledgements.tex  acronyms.tex
├── chapters/
│   ├── 01-introduction.tex ... 06-conclusion.tex
├── appendices/
│   ├── A-derivations.tex  B-extra-results.tex
└── figures/
```
Number-prefix files so the filesystem order matches reading order. Each chapter file starts with `\chapter{...}\label{ch:...}` and nothing else from the preamble.

## 5. Glossary, acronyms, nomenclature

For documents > ~100 pages, manage abbreviations automatically with the **`glossaries`** (or `glossaries-extra`) package — define once, expand on first use, abbreviate thereafter, and auto-print the list.

```latex
% preamble
\usepackage[acronym,toc,nonumberlist]{glossaries}
\makeglossaries
\newacronym{cnn}{CNN}{Convolutional Neural Network}
\newacronym{mri}{MRI}{Magnetic Resonance Imaging}
\newglossaryentry{tensor}{name=tensor, description={a multilinear map ...}}
```
```latex
% in text
First use: \gls{cnn}  -> "Convolutional Neural Network (CNN)"
Later:     \gls{cnn}  -> "CNN"        Plural: \glspl{cnn}
% print the list (frontmatter or backmatter)
\printglossary[type=\acronymtype, title={List of Acronyms}]
```
**Compilation:** `glossaries` needs an extra pass — `makeglossaries main` between LaTeX runs (latexmk can be configured to do it). If `makeglossaries`/`makeindex` is unavailable, use `\usepackage[...]{glossaries}` with `\printnoidxglossaries` and `\makenoidxglossaries` (pure-TeX, slower, no external tool).

`nomencl` package is an alternative for symbol nomenclature.

## 6. Bibliography for a thesis

Use **biblatex + biber** (best for large, multilingual, evolving reference lists):
```latex
% preamble
\usepackage[backend=biber, style=numeric-comp, sorting=nyt, doi=true, url=false,
            maxbibnames=99, giveninits=true]{biblatex}
\addbibresource{references.bib}
\usepackage{csquotes}   % required with babel/polyglossia + biblatex
```
- `numeric-comp` for engineering/CS (compresses [3–5]); `authoryear` for many sciences/humanities. Match your department's norm.
- `maxbibnames=99` so the bibliography lists *all* authors (theses must not "et al." in the reference list).
- One `references.bib`; keep keys stable and unique across years of writing.
- Optional **per-chapter bibliographies** via `refsection` / `\printbibliography[section=...]` if required.

## 7. Layout & typographic requirements typical of theses

```latex
\usepackage[a4paper,margin=2.5cm,bindingoffset=1cm]{geometry}  % binding offset for printed copies
\usepackage{setspace}\onehalfspacing      % or \doublespacing if required
\usepackage{microtype}
\usepackage{fancyhdr}                      % running headers with chapter/section
\usepackage[english]{babel}                % or polyglossia for multilingual
\usepackage{emptypage}                     % no headers on blank pages (twoside)
```
- Honor the university's required line spacing (often 1.5 or double) and binding margin.
- Page numbering: roman in front matter, arabic from chapter 1 — handled by `\frontmatter`/`\mainmatter`, or manually with `\pagenumbering{roman}` / `\pagenumbering{arabic}` if not using `book`.
- Chapter-opening style via `titlesec` if the default is undesired.

## 8. Cross-document referencing at scale

- Prefix labels by chapter to avoid collisions: `\label{ch:methodology}`, `\label{sec:methodology:loss}`, `\label{fig:methodology:pipeline}`.
- Use `cleveref`: "as shown in \cref{fig:methodology:pipeline} of \cref{ch:methodology}".
- `\autoref`/`\nameref` for "see the *Loss* section" style references.

## 9. Drafting workflow

- `\includeonly{chapters/03-methodology}` while writing chapter 3 → compiles in seconds, page numbers from earlier chapters preserved via `.aux`.
- `\usepackage{todonotes}` → `\todo{...}`, `\missingfigure{...}`, and `\listoftodos` to track open items.
- Track word/page targets; compile the *whole* thesis periodically to catch cross-ref and float-placement issues early.
- Version-control the source; never keep a 300-page single `.tex`.

## 10. Defense / submission checklist

- [ ] Built from the **official university class** (or matches its margins/spacing/title page exactly).
- [ ] `\frontmatter`/`\mainmatter`/`\backmatter` page numbering correct (roman → arabic).
- [ ] Title page, declaration, abstract, acknowledgements, ToC, LoF, LoT all present and correct.
- [ ] List of acronyms/glossary builds (`makeglossaries` pass run); acronyms expand on first use only.
- [ ] Every chapter compiles standalone via `\includeonly`; whole thesis compiles clean.
- [ ] All figures/tables referenced and captioned; vector figures; booktabs tables.
- [ ] Bibliography lists **all** authors (no et al. in list), DOIs present, style matches department.
- [ ] Binding offset/margins set if a printed copy is required.
- [ ] No `\todo`/`\missingfigure`/`??`/placeholder values remain.
- [ ] Fonts embedded; correct paper size; PDF/A if the repository demands it.
- [ ] `latexmk` builds end-to-end (configure it to run biber + makeglossaries).
