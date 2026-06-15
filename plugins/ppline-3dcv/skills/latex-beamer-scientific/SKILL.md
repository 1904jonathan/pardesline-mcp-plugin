---
name: latex-beamer-scientific
description: "Use this skill to plan and build a scientific presentation in LaTeX with the Beamer class. Triggers: 'Beamer', 'LaTeX presentation', 'slides', 'talk', 'defense slides', 'conference talk', 'metropolis theme', 'frames/overlays', 'slide deck in LaTeX', or any request to turn research into academic slides. It establishes the talk plan and narrative arc (title → motivation/gap → contributions → method → results → conclusion), frame structure, theme selection (metropolis and others), overlays/incremental reveals, columns for figure+text layouts, blocks/theorems, section navigation, handout mode, and slide-design discipline (one idea per slide, minimal text, big readable figures). Consult latex-scientific-core alongside this skill for math, figures, and bibliography mechanics."
---

# Scientific Presentation in LaTeX (Beamer)

Read `latex-scientific-core` first for math/figures/bib mechanics. This skill adds the **talk structure, frame design, themes, and overlay system**.

## 1. Talk narrative (the plan that drives the slides)

A research talk is a *story*, not a paper read aloud. Plan slides around this arc before writing any LaTeX:

1. **Title slide** — title, authors, affiliation, venue, date.
2. **Motivation / problem** (1–2 slides) — why anyone should care; the big picture.
3. **Gap / question** (1 slide) — what's missing, stated as a crisp question.
4. **Contributions** (1 slide) — bulleted, what *this* work delivers. The audience should be able to leave after this slide and know the point.
5. **Method / approach** (2–4 slides) — the key idea, one concept per slide, built up with overlays.
6. **Results** (2–4 slides) — the evidence; big figures, headline numbers, minimal table clutter.
7. **Conclusion / takeaways** (1 slide) — restate contributions + main result + future work.
8. **Backup / appendix** (optional) — extra detail for Q&A, after the "thank you" slide, excluded from the progress count via `appendixnumberbeamer`.

Rule of thumb: ~1 slide per minute; a 15-minute talk ≈ 12–16 content slides.

## 2. Slide-design discipline (non-negotiable for scientific talks)

- **One idea per frame.** If a frame needs scrolling-length text, split it.
- **Minimal text.** Loose 6×6 guideline (≤ ~6 bullets, ≤ ~6 words each). Slides support speech; they are not the script.
- **Figures are first-class.** Make them large, vector, readable from the back row; label axes with big fonts.
- **Headline titles.** Use the frame title to state the takeaway ("Our model halves error", not "Results").
- **Restraint with color/animation.** Color carries meaning (alerts, highlights), not decoration. Avoid gratuitous transitions.
- **Consistent math notation** with the paper/thesis (reuse the same macros).

## 3. Theme selection

| Theme | Character | Notes |
|-------|-----------|-------|
| `metropolis` | Modern, flat, minimal, progress bar | Best default for technical talks. Needs **Fira Sans** + **XeLaTeX/LuaLaTeX**. |
| `default` | Plain, no navigation | Clean, distraction-free, works with pdflatex. |
| `CambridgeUS` / `Madrid` / `Berlin` | Classic Beamer with headline navigation | Heavier "chrome"; fine for teaching. |
| Minimalist custom (e.g. Michaillat / Blei-style) | One font size, grayscale text, 4:3 | Excellent for argument-focused research talks. |

Customize color independently: `\usecolortheme{seahorse}` (soft blue), etc.

## 4. Metropolis skeleton (recommended default)

Compile with **xelatex** or **lualatex** (`latexmk -xelatex slides.tex`).

```latex
\documentclass[10pt,aspectratio=169]{beamer}   % 16:9; use 43 for 4:3
\usetheme[progressbar=frametitle]{metropolis}
\usepackage{appendixnumberbeamer}              % backup slides excluded from numbering
\usepackage{booktabs}
\usepackage[scale=2]{ccicons}
\usepackage{pgfplots}\pgfplotsset{compat=1.18}
\usepackage{amsmath,amssymb,bm}
\usepackage{xspace}

\title{Headline-Style Title of the Talk}
\subtitle{Optional clarifying subtitle}
\author{Jonathan Tabet \and Co-author}
\institute{Affiliation}
\date{Venue, \today}
% \titlegraphic{\hfill\includegraphics[height=1.2cm]{logo.pdf}}

\begin{document}

\maketitle

\begin{frame}{Outline}
  \setbeamertemplate{section in toc}[sections numbered]
  \tableofcontents[hideallsubsections]
\end{frame}

% recap the structure at each new section
\AtBeginSection[]{%
  \begin{frame}{Outline}\tableofcontents[currentsection,hideallsubsections]\end{frame}}

\section{Motivation}
\begin{frame}{Why this problem matters}
  \begin{itemize}
    \item Context point one.
    \item The cost of the unsolved problem.
  \end{itemize}
\end{frame}

\section{Contributions}
\begin{frame}{What we contribute}
  \begin{enumerate}
    \item First contribution.
    \item Second contribution.
  \end{enumerate}
\end{frame}

% ... Method, Results, Conclusion sections ...

\begin{frame}[standout]   % metropolis "standout" big-text slide
  Thank you. \\ Questions?
\end{frame}

\appendix
\begin{frame}{Backup: extra detail}\end{frame}

\end{document}
```

For **pdflatex** users without Fira Sans: use `\documentclass{beamer}\usetheme{default}` (or `CambridgeUS`) instead of metropolis.

## 5. Frames — the atomic unit

```latex
\begin{frame}{Frame title states the takeaway}
  content...
\end{frame}
```
- Use `\begin{frame}[fragile]{...}` whenever the frame contains `verbatim`, `lstlisting`, or `minted`.
- `\begin{frame}[allowframebreaks]{...}` lets long content (e.g. references) auto-split across slides.
- `\begin{frame}[plain]` for a full-bleed image or title.

## 6. Overlays — reveal incrementally

Overlays control *when* content appears, keeping each slide focused as you talk.

```latex
\begin{frame}{Build up the argument}
  \begin{itemize}
    \item<1-> Always visible from step 1.
    \item<2-> Appears on the second click.
    \item<3-> Appears on the third.
  \end{itemize}

  \onslide<2->{Text that joins at step 2.}
  \only<3>{Shown only during step 3, takes no space otherwise.}
  \alert<2>{Highlighted only on step 2.}
\end{frame}
```
- `\pause` is the quick-and-dirty sequential reveal.
- `<+->` auto-increments overlay steps (`\item<+->`).
- Use overlays to **direct attention**, not to animate for its own sake.

## 7. Columns — figure beside text (the workhorse layout)

```latex
\begin{frame}{Results overview}
  \begin{columns}[T]                 % T = top-align
    \begin{column}{0.45\textwidth}
      \begin{itemize}
        \item Accuracy: 94.2\%
        \item F1: 0.91
        \item Inference: 12\,ms
      \end{itemize}
    \end{column}
    \begin{column}{0.55\textwidth}
      \includegraphics[width=\linewidth]{figures/results.pdf}
    \end{column}
  \end{columns}
\end{frame}
```

## 8. Blocks, theorems, alerts

```latex
\begin{block}{Key result}
  Nondimensional parameters collapse the curves.
\end{block}
\begin{alertblock}{Caution}
  Holds only under assumption A.
\end{alertblock}
\begin{exampleblock}{Example}
  ...
\end{exampleblock}

\begin{theorem}\label{thm:main}
  Statement.
\end{theorem}
\begin{proof} sketch... \end{proof}
```
Block appearance follows the theme. Theorem environments are predefined in Beamer (no `amsthm` needed for the basic ones).

## 9. Figures, tables, plots on slides

- Big, vector, axis labels readable from afar; one figure per point.
- `\includegraphics[width=\linewidth]{...}`; avoid shrinking text to fit — split instead.
- Native pgfplots plots match slide fonts and stay crisp (see `latex-scientific-core` §6).
- Tables: booktabs, few rows, bold the headline number; consider revealing rows with overlays.

## 10. Citations on slides

Keep references light. Options:
- Footnote-style inline: `\footnote{[1] Rogers et al., 2017}` (manual, simplest for a talk).
- `\usepackage[backend=biber,style=verbose-inote]{biblatex}` for footnote citations, or a final **References** frame with `\printbibliography` (use `[allowframebreaks]`).
- Shrink with `\tiny`/`\scriptsize`; the audience won't read full entries — a short author-year tag is enough.

## 11. Navigation & structure aids

- `\AtBeginSection` outline recap (shown above) reminds the audience where they are.
- `\tableofcontents[currentsection]` highlights the current section.
- Hyperlink buttons for non-linear jumps to backup slides:
```latex
\hyperlink{detail}{\beamerbutton{details}}     % link
\begin{frame}[label=detail]{Backup detail}...\end{frame}   % target
```

## 12. Handout mode (printable, no overlays)

Collapse all overlay steps into one static slide per frame for printing:
```latex
\documentclass[handout]{beamer}
% or, to print 2-up / 4-up via pgfpages:
\usepackage{pgfpages}
\pgfpagesuselayout{2 on 1}[a4paper,border shrink=5mm]
```
Beamer also supports `presentation`, `handout`, and `trans` modes.

## 13. Compilation notes

- `metropolis` + Fira Sans ⇒ **xelatex/lualatex** (`latexmk -xelatex`). Missing-font errors mean Fira Sans isn't installed.
- `[fragile]` on any frame with verbatim/listings, or compilation fails.
- Output is a PDF — portable across OSes and projectors; embed fonts (`pdffonts slides.pdf`).
- **No local LaTeX? Compile via the `ppline-3dcv` MCP** (Tectonic, XeTeX-based, auto-fetches CTAN
  incl. metropolis + Fira): pass the full deck source to `compile_latex(source)`, or build a quick
  deck from structured content with `create_presentation(title, slides=[{title, bullets, body}],
  theme="metropolis")`. Both return `{pdf_url, tex_url}`; on `{ok:false, log_tail}` fix and retry.
  For hand-authored overlays/columns/`[standout]` frames use `compile_latex` (full control);
  `create_presentation` is the fast structured path. Reference: `ppline-3dcv:research-and-presentations`.

## 14. Pre-talk checklist

- [ ] Narrative arc present: motivation → gap → contributions → method → results → conclusion.
- [ ] One idea per frame; titles state takeaways; text minimal.
- [ ] Contributions slide is self-sufficient.
- [ ] Figures large, vector, readable from the back; axes labeled with big fonts.
- [ ] Overlays direct attention, not decorate; `[fragile]` where needed.
- [ ] Math notation matches the paper/thesis.
- [ ] Section recaps via `\AtBeginSection`; progress bar/ToC consistent.
- [ ] Backup slides after the thank-you, excluded from numbering (`appendixnumberbeamer`).
- [ ] Compiles with the correct engine; fonts embedded; ~1 slide/minute budget respected.
- [ ] A `handout` build exists if printed copies are needed.
