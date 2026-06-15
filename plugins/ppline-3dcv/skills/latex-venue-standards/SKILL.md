---
name: latex-venue-standards
description: "Use this skill to adapt a research paper to the exact standards of a target journal or conference across disciplines — ML/AI (NeurIPS, ICML, ICLR, AAAI), computer vision (CVPR, ICCV, ECCV, WACV, 3DV), NLP (ACL/EMNLP/NAACL via ACL Rolling Review), medical imaging (MICCAI, IPMI, SPIE, IEEE TMI, Springer LNCS), IEEE Transactions/conferences, ACM (acmart/SIGCONF), and the big science publishers (Nature/Nature portfolio, Science, Cell, Elsevier elsarticle, PLOS). Triggers: 'format for <venue>', 'is my paper ready for <conference>', 'page limit / template / style file for X', 'double-blind', 'camera-ready', 'rebuttal', 'reproducibility checklist', 'reporting standard (PRISMA/CONSORT/STROBE/STARD/CLAIM/TRIPOD)', 'CRediT / ORCID / author contributions', or any request to make a manuscript comply with a venue's submission rules. It gives the document class, page-limit and anonymity rules, required sections (limitations/ethics/broader-impact/checklists), bibliography style, and a desk-reject-avoidance checklist per venue. Always confirm the CURRENT year's official author kit by web search before finalizing — rules change yearly. Use with latex-paper-ieee for paper mechanics and latex-scientific-core for figures/bib."
---

# Adapting a Paper to Venue Standards

This skill encodes what differs **between venues** so a manuscript clears desk-screening. The mechanics of writing the LaTeX (math, figures, bib) live in `latex-scientific-core` and `latex-paper-ieee`; this skill is the **compliance layer**.

## 0. The one rule that overrides everything

**Always fetch the CURRENT year's official author kit / call-for-papers before finalizing.** Page limits, anonymity policy, required checklists, submission-per-author caps, and AI-use disclosure change *every year*. Tweaking margins, line spacing, or font size to fit is itself grounds for desk rejection at almost every top venue. When a user names a venue, web-search "<venue> <year> author guidelines / call for papers" and confirm against the table below before committing. Treat the table as a fast-start default, not the source of truth.

## 1. Cross-venue decision flow

1. Identify **field** → narrows the class file family (single-column ML style vs IEEE two-column vs LNCS vs Nature Word).
2. Identify **review model**: double-blind (anonymize) vs single-blind/open (full author block). Most CS conferences are double-blind; many journals are single-blind or open.
3. Identify **page/word limit** and **what's excluded** (references, appendix, limitations, ethics, checklist).
4. Identify **mandatory sections** (limitations, broader impact, ethics, reproducibility checklist, data/code availability).
5. Identify **bibliography style** required by the class.
6. Apply the **desk-reject checklist** (§9).

## 2. Quick reference — top venues (verify yearly)

| Venue | Class / style | Layout | Page limit (main text) | Excluded from limit | Review | Bib |
|-------|---------------|--------|------------------------|---------------------|--------|-----|
| **NeurIPS** | `neurips_<year>.sty` (`article`) | single-col, 10pt | 9 (+1 camera-ready) | refs, checklist, appendix | double-blind, OpenReview | any consistent; `.bst` provided |
| **ICML** | `icml<year>.sty` | single-col | 8 (+1 camera-ready) | refs, appendix | double-blind | provided |
| **ICLR** | `iclr<year>_conference.sty` | single-col (NeurIPS variant) | ~9 | refs, appendix | double-blind, OpenReview | `.bst` provided |
| **AAAI** | `aaai<year>.sty` | **two-col** | 7 + refs (varies) | refs (within rules) | double-blind | `aaai.bst` |
| **CVPR / ICCV / WACV / 3DV** | `cvpr.sty` / `ieee` review style | **two-col** | **8** (refs unlimited, not counted) | references only | double-blind, OpenReview | IEEE numeric |
| **ECCV** | `eccv.sty` (LNCS-derived) | LNCS single-col | ~14 incl. refs (varies) | varies | double-blind | `splncs04` |
| **ACL / EMNLP / NAACL (ARR)** | `acl.sty` (`[review]`) | **two-col** | **8 long / 4 short** | refs, **Limitations**, **Ethics**, ack | double-blind, ARR/OpenReview | natbib via `acl_natbib` |
| **MICCAI / workshops** | Springer **LNCS** (`llncs`) | single-col | **8 + 2 refs** (no mods!) | references (2 pp) | double-blind, CMT/OpenReview | `splncs04` |
| **IPMI** | LNCS | single-col | **12** excl. refs | refs, ack | double-blind, **no rebuttal** | `splncs04` |
| **SPIE (Medical Imaging)** | `spie.cls` | two-col | varies (often ~6–12) | varies | usually single-blind | SPIE/IEEE style |
| **IEEE Transactions (TMI, TPAMI, TIP…)** | `IEEEtran` `[journal]` | two-col | journal-specific (often ~12–14 typeset) | varies | single-blind | `IEEEtran.bst` |
| **IEEE conferences** | `IEEEtran` `[conference]` | two-col | typically 4–8 | varies | single/double-blind | `IEEEtran.bst` |
| **ACM (SIG venues)** | `acmart` `[sigconf]` | two-col | venue-specific | varies | varies | `ACM-Reference-Format` |
| **Nature / Nature portfolio** | Word or LaTeX (own template) | journal-set | **~3,000–5,000 words**, abstract ≤150–200 w | Methods after refs; Extended Data | single-blind (double-blind optional) | superscript numeric |
| **Science** | Word/LaTeX (own) | journal-set | ~2,500 words (Reports) | Methods/Supp separate | single-blind | Science numeric |
| **Cell Press** | own template | journal-set | ~6,000–8,000 words | extensive supplement | single-blind | numbered |
| **Elsevier (most)** | `elsarticle.cls` | "Your Paper Your Way" — loose at submission | journal-specific | refs etc. | single/double-blind | `elsarticle-num` / `-harv` |
| **PLOS ONE** | own / LaTeX | journal-set | no strict limit | — | single-blind, criteria-based | Vancouver numeric |

## 3. Field-specific class skeletons

**ML single-column (NeurIPS-style; ICML/ICLR analogous):**
```latex
\documentclass{article}
\usepackage{neurips_2025}            % submission: anonymous + line numbers
% \usepackage[final]{neurips_2025}  % camera-ready: shows authors
% \usepackage[preprint]{neurips_2025} % arXiv non-anonymous preprint
\title{...}
\author{ ... }                      % ignored unless [final]/[preprint]
\begin{document}\maketitle
\begin{abstract}...\end{abstract}
\section{Introduction}...
% Mandatory: NeurIPS paper checklist (do NOT delete) after references
\end{document}
```

**CV two-column (CVPR/ICCV/WACV/3DV):**
```latex
\documentclass[10pt,twocolumn,letterpaper]{article}
\usepackage[review]{cvpr}            % review = anonymized + line numbers
% \usepackage{cvpr}                  % camera-ready
\usepackage{graphicx,amsmath,amssymb}
\begin{document}
\title{...}\author{Anonymous CVPR submission\\ Paper ID ****}  % review mode
\maketitle
\begin{abstract}...\end{abstract}
% 8 pages excl. references; references unlimited
\end{document}
```

**NLP (ACL Rolling Review):**
```latex
\documentclass[11pt]{article}
\usepackage[review]{acl}             % review setting MUST be on for submission
\usepackage{times,latexsym}
\begin{document}
\title{...}
% body ≤ 8 (long) / 4 (short) pages
\section*{Limitations}              % MANDATORY, after Conclusion, before refs; not counted
\section*{Ethical Considerations}   % optional but recommended; not counted
\bibliography{anthology,custom}     % uses acl_natbib
\end{document}
```

**Medical imaging (MICCAI/ECCV/IPMI — Springer LNCS):**
```latex
\documentclass[runningheads]{llncs}
\usepackage{graphicx,amsmath}
\begin{document}
\title{...}
\author{Anonymous}                  % template ships anonymized block — DO NOT delete to gain space
\institute{}
\maketitle
\begin{abstract}...\end{abstract}   % keep abstract + keywords; 150–250 words
\keywords{...}
% 8 pages + up to 2 pages refs (MICCAI); NO template modification whatsoever
\bibliographystyle{splncs04}
\bibliography{refs}
\end{document}
```

**Elsevier journal:**
```latex
\documentclass[preprint,review,12pt]{elsarticle}
\begin{document}
\begin{frontmatter}
  \title{...}
  \author{...}\affiliation{...}
  \begin{abstract}...\end{abstract}
  \begin{keyword} ... \end{keyword}
\end{frontmatter}
% IMRaD body
\bibliographystyle{elsarticle-num}   % or elsarticle-harv
\bibliography{refs}
\end{document}
```

**IEEE / ACM:** see `latex-paper-ieee` §1 (IEEEtran options; acmart `sigconf`).

## 4. Anonymity (double-blind) — what to strip

For CVPR/ICCV/NeurIPS/ICML/ICLR/ACL/MICCAI/IPMI/AAAI submission versions:
- Remove author names, affiliations, emails; use the template's anonymized block (don't delete it to reclaim space — MICCAI/CVPR explicitly forbid this).
- **Neutralize self-citations**: write "prior work [12] showed…", never "our previous work [12]" or "[Anonymous, 2023]".
- Remove Acknowledgments/funding/grant IDs (re-add at camera-ready). NeurIPS provides an `ack` environment that auto-hides in anonymous mode.
- Anonymize **supplementary**: no author names in videos, code repos, PDFs. Anonymize GitHub/project links (use anonymous.4open.science or similar); avoid Dropbox-type links that reveal identity/track viewers.
- Anonymize the **running header** and abstract (a common MICCAI desk-reject cause).
- Respect **social-media / media embargo**: many CV venues forbid naming the conference in posts about a paper under review.

## 5. Mandatory non-IMRaD sections by venue (the desk-reject traps)

- **NeurIPS**: paper **checklist** (reproducibility, broader impact, ethics) — shipped in the `.sty`, must be included, does not count toward 9 pages. **Funding/competing-interests disclosure** at camera-ready. Optional Broader Impact.
- **ICML**: appendix in the **same PDF** (reviewers won't fetch a separate file).
- **ACL/EMNLP/NAACL**: **"Limitations"** section is **mandatory** (desk reject if missing), after Conclusion, before References, not counted; discussion only — no new experiments/figures. **"Ethical Considerations"** optional, recommended, not counted. **Responsible NLP checklist** required.
- **CVPR/ICCV**: no mandatory limitations section, but ethics guidelines apply; supplementary and rebuttal (≤1 page) have strict rules; color-blind-safe figures expected (don't rely on red/green alone).
- **MICCAI**: data **origin/license disclosure**, **ethics approval number** where applicable; acknowledgments/disclosure-of-interest optional at submission (count toward 8 pp if included).
- **Nature/Science/Cell**: **Methods** often after references; **Data/Code Availability** statement mandatory; **Author Contributions** (CRediT); **Competing Interests**; Extended Data / Supplementary; abstract length strictly capped.
- **Elsevier/PLOS**: **CRediT author contributions**, **data availability statement**, declaration of competing interest, **highlights** (Elsevier, 3–5 bullets ≤85 chars), graphical abstract (some journals).

## 6. Reporting standards (clinical / medical-AI work — critical for medical imaging)

When the paper makes clinical or diagnostic claims, comply with the relevant **EQUATOR** reporting guideline and include its checklist (often as supplementary). Match guideline to study type:

| Study type | Guideline |
|------------|-----------|
| Randomized controlled trial | **CONSORT** (+ **CONSORT-AI** for AI interventions) |
| Trial protocol | **SPIRIT** (+ **SPIRIT-AI**) |
| Observational (cohort/case-control) | **STROBE** |
| Diagnostic accuracy | **STARD** (+ **STARD-AI**) |
| Prediction model (dev/validation) | **TRIPOD** (+ **TRIPOD-AI**), risk of bias via **PROBAST(-AI)** |
| Systematic review / meta-analysis | **PRISMA** (+ **PRISMA-AI**, search via **PRISMA-S**) |
| **AI in medical imaging** | **CLAIM** (Checklist for AI in Medical Imaging) — the key one for radiology/imaging AI |
| Animal in-vivo | **ARRIVE** |

Practical: cite the guideline in Methods ("reported in accordance with CLAIM/PRISMA"), register systematic reviews on **PROSPERO**, and attach the completed checklist. These materially affect acceptance at IEEE TMI, MICCAI, Radiology, Nature Medicine.

## 7. Authorship & metadata standards (journals)

- **ORCID** for each author (mandatory at many publishers).
- **CRediT taxonomy** for the Author Contributions statement (Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Writing – original/review & editing, Visualization, Supervision, Funding acquisition…).
- **Data/Code Availability** statement with repository + DOI (Zenodo/Figshare/OSF) or access conditions.
- **Competing Interests** and **Funding** declarations.
- **Ethics/IRB** approval statement and consent where human/animal data are involved.

## 8. Bibliography per venue (set the right backend/style)

- IEEE (TMI/CVPR/conf): `IEEEtran.bst` (bibtex) or biblatex `style=ieee`.
- LNCS (MICCAI/ECCV/IPMI): `splncs04` (alphabetical default; order-of-appearance also accepted).
- ACL: `acl_natbib` (natbib commands `\citet`/`\citep`), Anthology `.bib`.
- ML (NeurIPS/ICML/ICLR): provided `.bst`; any consistent style; 9pt allowed for the list.
- ACM: `ACM-Reference-Format` (numeric or author-year per track).
- Elsevier: `elsarticle-num` (numbered) or `elsarticle-harv` (author-year).
- Nature/Science: superscript numeric, journal's own style; let the publisher restyle at proof.
See `latex-scientific-core` §9 for biblatex-vs-bibtex mechanics and `.bib` hygiene.

## 9. Universal desk-reject-avoidance checklist

- [ ] **Current** official template/class for the target **year** (re-downloaded, not last year's).
- [ ] No margin/spacing/font-size tampering; no `\vspace` hacks to fit.
- [ ] Within page/word limit; confirmed **what's excluded** (refs/appendix/limitations/ethics/checklist).
- [ ] Anonymized correctly (names, affils, emails, self-cites, ack, supplementary, running header, links) **if** double-blind.
- [ ] All **mandatory sections** present (e.g., ACL Limitations; NeurIPS checklist; Nature Data Availability).
- [ ] Required **reporting-standard checklist** attached if clinical/medical-AI (CLAIM/PRISMA/STROBE…).
- [ ] **CRediT / ORCID / competing interests / funding / data & code availability** for journals.
- [ ] Correct **bibliography style** for the class; no `[?]`; DOIs present.
- [ ] PDF only; under file-size cap; **Type-1 fonts embedded** (no Type-3 — check `pdffonts`); correct paper size.
- [ ] Appendix in the **same PDF** if the venue requires (ICML/NeurIPS).
- [ ] Figures color-blind-safe (don't encode meaning by red/green alone) where venue notes it (CVPR).
- [ ] Compiles clean via `latexmk`; zero LaTeX warnings; abstract within its word cap.
- [ ] Media/social-media embargo respected for venues that require it.

## 10. Camera-ready transitions (after acceptance)

- Switch class option from review/anonymous to **final** (`[final]`, remove `[review]`, uncomment `\iclrfinalcopy`, etc.).
- Re-insert authors, affiliations, **Acknowledgments**, funding, **competing-interests/ORCID**.
- Add the allowed **extra page** (NeurIPS/ICML/ACL grant +1).
- Sign and include **copyright / license-to-publish** forms (IEEE copyright release; Springer Consent-to-Publish — wet-ink for MICCAI; ACM e-rights).
- Update DOIs, finalize data/code links, embed final figures (vector, fonts embedded).
- Re-run the desk-reject checklist against **camera-ready** rules (often differ slightly from submission).

## 11. When the user hasn't named a venue
Ask only the minimum needed: field (CV / ML / NLP / medical imaging / general science / engineering), and target type (conference vs journal). Then pick the closest class from §2–3 and state the assumption inline. Do not over-question if the field is already clear from context.
