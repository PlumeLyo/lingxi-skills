# International Paper Writing Reference

> Paper structure, literature sources, citation styles, and DOCX configuration for English academic writing.

---

## 1. Paper Types & Word Counts

| Paper Type | Min Body Words | Min Refs | Section Breakdown |
|-----------|------|------|------|
| Undergraduate Thesis | ≥15,000 | ≥20 | Intro≥1500 + LitRev≥3500 + Method≥3000 + Results≥3500 + Discuss≥2500 + Conclusion≥1000 |
| Master's Thesis | ≥15,000 | ≥50 | Intro≥1500 + LitRev≥4000 + Method≥3000 + Results≥3500 + Discuss≥3000 |
| PhD Dissertation | ≥60,000 | ≥100 | Multi-chapter, each ≥8000 |
| Course Essay | ≥5,000 | ≥8 | Intro≥800 + Body≥3400 + Conclusion≥800 |
| Research Paper | ≥5,000 | ≥15 | Intro≥600 + LitRev≥1200 + Method≥1000 + Findings≥1200 + Discuss≥1000 |
| Lab Report | ≥5,000 | ≥10 | Intro≥700 + Methods≥1000 + Results≥1500 + Discussion≥1800 |
| Case Study | ≥5,000 | ≥10 | Background≥900 + Analysis≥2500 + Recommend≥1000 + Implement≥600 |
| Journal Article (IMRaD) | ≥6,000 | ≥30 | Each section ≥800–1500 |
| Literature Review | ≥10,000 | ≥50 | Intro≥800 + Method≥800 + Themes≥2000×4 + Gaps≥1400 |
| Conference Paper | ≥5,000 (6–10 pages) | ≥20 | IMRaD, concise |
| Research Proposal | ≥5,000 | ≥20 | Background≥1000 + LitRev≥1200 + Method≥1500 + Timeline≥600 |
| Book Review | ≥5,000 | ≥5 | Summary≥800 + Analysis≥2500 + Comparison≥1000 + Conclusion≥700 |

Word count covers body only (Introduction through Conclusion), excluding abstract, keywords, references.

### Citation Allocation by Chapter

After search, allocate references to chapters using these proportions to ensure full citation coverage:

| Paper Type | Intro | Lit Review | Method | Results | Discussion/Conclusion |
|-----------|-------|-----------|--------|---------|----------------------|
| Undergraduate Thesis | 15% | 40% | 10% | 15% | 20% |
| Master's Thesis | 15% | 35% | 10% | 25% | 15% |
| PhD Dissertation | 10% | 30% | 10% | 35% | 15% |
| Journal Article | 20% | 25% | 15% | 20% | 20% |
| Conference Paper | 20% | 25% | 15% | 20% | 20% |
| Course Essay | 20% | — | 30% (across body sections) | — | 20% |
| Literature Review | 10% | 75% (across themes) | — | — | 15% |
| Research Proposal | 15% | 40% | 25% | — | 20% |

Percentages indicate each chapter's share of total citations. A single reference may appear in multiple chapters (e.g., cited in both Introduction and Discussion). The Literature Review chapter is the most citation-dense and should receive the largest allocation.

## 2. Cover Page & Abstract

**Cover Page** (theses only): separate section, no header/footer, centered. Includes title, author, supervisor, department, program, date. Use `XXXXX` for fields not provided. Layout in docx-api.md. Journal/conference papers do not need a cover page.

**Abstract Page** (theses): between cover and TOC, separate section.
- Title: `Abstract` (h.h1, centered). Body in Times New Roman: purpose, methodology, key findings, conclusions.
- End with `Keywords:` (bold) + 4–6 keywords (comma-separated).
- Word count: Undergraduate 150–300, Master's 250–500, PhD 300–600.
- Tense: past for methods/findings, present for conclusions/implications.
- Journal/conference papers: abstract on first page (not separate).

## 3. Thesis / Dissertation Structures

All theses share: Cover → Abstract + Keywords → Table of Contents → Body Chapters → References → Appendices (optional).

### Undergrad / Master's differences

| | Undergraduate (6 ch, ≥15,000) | Master's (6 ch, ≥15,000) |
|---|---|---|
| Ch 1: Introduction | Background (Context→Problem) / Aims (Aims→Objectives) / Significance (Theoretical→Practical) / Structure | Background (Context→Problem→Motivation) / Aims & Objectives / Research Questions or Hypotheses / Significance / Structure |
| Ch 2: Literature Review | Theoretical Framework (Theory A→B) / Thematic Review (3 themes) / Research Gap (Limitations→Questions) | Theoretical Framework (Theory A→B→Conceptual Model) / Thematic Review (3-4 themes, Evolution→Key Studies→Debates) / Critical Synthesis & Gap |
| Ch 3: Methodology | Design (Philosophy→Overall) / Collection (Sources→Instruments) / Analysis (Methods→Metrics) / Ethics | Design (Philosophy→Strategy) / Collection (Population→Procedures→Validity) / Analysis (Framework→Methods→Metrics) / Ethics & Limitations |
| Ch 4: Results | Setup (Environment→Parameters) / Main Results / Additional Analysis (Comparative→Sensitivity) | Overview / Findings per RQ/Hypothesis (Quantitative→Qualitative) / Ablation/Robustness Check |
| Ch 5: Discussion | Interpretation of Findings / Comparison with Prior Studies / Implications (Theoretical→Practical) | Interpretation per RQ/H / Comparison with Prior Lit / Theoretical Implications / Practical Implications |
| Ch 6: Conclusion | Summary / Limitations / Future Research | Key Contributions / Limitations / Future Directions |

### PhD Dissertation (7+ chapters, ≥60,000 words)

Front matter adds optional List of Figures / List of Tables. Back matter adds optional List of Publications.

| Chapter | Structure |
|---------|-----------|
| Ch 1: Introduction | Background (Domain→Challenges) / Literature Review (4-5 themes→Critical Assessment) / Research Gaps & Questions / Aims, Objectives, Scope / Thesis Organization |
| Ch 2: Theoretical Framework | Foundational Theories / Analytical Framework (Rationale→Relationships) / Assumptions & Constraints |
| Ch 3–5(6): Contributions | Each uses the **Contribution Chapter Template** below |
| Ch 6 (optional): Integrated Validation | Validation scheme / Cross-dataset verification / Integration testing / Discussion |
| Final Ch: Conclusion | Summary of Contributions / Limitations / Future Directions |

**Contribution Chapter Template** (used for each contribution chapter in PhD, also adaptable for multi-study Master's):
```
X.1 Problem Formulation
  X.1.1 Limitations of Existing Approaches
  X.1.2 Formal Problem Definition
X.2 Proposed Approach
  X.2.1 Overall Architecture
  X.2.2 Core Algorithm / Model
  X.2.3 Theoretical Analysis (complexity, convergence, etc.)
X.3 Experimental Design
  X.3.1 Datasets and Environment
  X.3.2 Baselines and Metrics
  X.3.3 Implementation Details
X.4 Results and Analysis
  X.4.1 Main Results
  X.4.2 Ablation Study
  X.4.3 Parameter Sensitivity
  X.4.4 Case Study and Visualization
  X.4.5 Chapter Summary
```

**Sub-section rule**: every X.N section must have ≥2 sub-sections (X.N.1, X.N.2). Adapt sub-section titles to the specific research topic.

## 4. Non-Thesis Structures

### Journal Article — IMRaD (≥6,000 words)

Abstract (150–250) + Keywords on first page → Introduction (Background→Related Work→Gap & Contribution→Organization) → Methodology (Problem Formulation→Proposed Method with sub-components→Implementation) → Experiments (Setup with Datasets & Baselines→Main Results→Ablation→Analysis) → Conclusion → References

Review articles: 8,000–12,000 words, 50–200+ refs (Systematic/Scoping/Narrative/Meta-analysis; PRISMA for systematic).

### Conference Paper (5,000–8,000 words, 6–10 pages)

Abstract (150–200) + Keywords → I. Introduction → II. Related Work (sub-topics) → III. Proposed Method (Overview→Modules) → IV. Experiments (Setup→Results→Analysis) → V. Conclusion → References

IEEE: 6–8 double-column pages; `*Abstract*—` prefix; Roman-numeral section titles centered.

### Research Proposal (≥5,000 words)

Introduction & Background (Context→Problem→Significance) → Literature Review (Theory→Current Research by theme→Gap) → Research Questions / Hypotheses → Methodology (Design→Sampling→Collection→Analysis) → Expected Contributions → Timeline → Ethics → References

### Course Essay (≥5,000 words)

Title Page → Introduction (Hook→Context→Thesis) → Body 3–5 sections (each with sub-arguments) → Conclusion (Restatement→Summary→Implications) → References. Types: Argumentative / Analytical / Expository / Compare-Contrast / Cause-Effect.

### Other Types

- **Lab Report**: Abstract → Intro (Background→Hypothesis) → Materials & Methods (Materials→Procedure→Analysis Methods) → Results (Observations→Statistics) → Discussion (Interpretation→Comparison→Error Sources→Implications) → Conclusion → References
- **Case Study**: Executive Summary → Background → Problem → Analysis (SWOT/PESTEL/Porter→Data→Stakeholders) → Alternatives → Recommendations (Strategy→Justification) → Implementation (Steps→Timeline) → References
- **Literature Review** (≥10,000): Intro (Scope→Search Strategy) → Thematic Sections 3–6 (Sub-themes→Synthesis per theme, each ≥2000 words, synthesize ≥5 sources) → Gaps & Future Directions → References
- **Book Review**: Summary → Strengths → Weaknesses → Field Contribution → Conclusion

### Writing Tips

- Thesis/Review: organize by **theme**, never paper-by-paper; synthesize ≥5 sources per thematic paragraph.
- Lab Report: methods/results past tense; established facts present tense.
- Case Study: use SWOT / PESTEL / Porter's frameworks.
- Journal Article: third person (STEM may use "we").
- Research Proposal: clearly articulate the research gap.

---

## 5. Literature Search

After path injection (`sys.path.insert(0, os.path.join(os.environ['SKILL_PATH'], 'paper-writer', 'scripts'))`), `import academic_search` to call all functions.

### Data Sources

| Function | Source | Notes |
|----------|--------|-------|
| `search_openalex(q, per_page=5)` | OpenAlex | 250M+ works |
| `search_semantic_scholar(q, limit=5)` | Semantic Scholar | 200M+ |
| `search_crossref(q, rows=5)` | CrossRef | 150M+ DOIs |
| `search_pubmed(q, retmax=5)` | PubMed | 36M+ biomedical |
| `search_arxiv(q, max_results=5)` | arXiv | 2.4M+ preprints |
| `search_doaj(q, page_size=5)` | DOAJ | 9M+ OA journals |
| `search_europe_pmc(q, page_size=5)` | Europe PMC | 42M+ life sciences |
| `search_core(q, limit=5, key)` | CORE | 200M+ OA (registration) |
| `search_google_scholar` | Google Scholar | Scraper, use sparingly |
| `check_unpaywall(doi)` | Unpaywall | DOI → OA URL |

### Source Selection

| Discipline | Primary | Secondary |
|-----------|---------|-----------|
| Computer Science | Semantic Scholar, arXiv, OpenAlex | CORE |
| Medicine / Health | PubMed, Europe PMC | CrossRef, OpenAlex |
| Social Sciences | OpenAlex, CrossRef | Semantic Scholar, DOAJ |
| Humanities | CrossRef, OpenAlex | DOAJ |
| Engineering | Semantic Scholar, CrossRef | arXiv, OpenAlex |

### Search Budget

| Target Refs | Per-round Scale | Rounds | Use Case |
|------------|----------------|--------|----------|
| ≤20 | 2-3 sources x 2 keywords | 2 | Course essay, proposal |
| 20-50 | 2-3 sources x 2-3 keywords | 3 | Thesis, research paper |
| ≥50 | 2-3 sources x 2-3 keywords | 3-5 | PhD thesis, lit review |

### Search Code Template

```python
import sys, os
sys.path.insert(0, os.path.join(os.environ['SKILL_PATH'], 'paper-writer', 'scripts'))
import academic_search as ac

await ac.multi_round_search(
    rounds=[
        {"keywords": ["core topic keyword 1", "core topic keyword 2"],
         "sources": ["openalex", "semantic_scholar", "crossref"]},
        {"keywords": ["subtopic A methodology", "subtopic B analysis"],
         "sources": ["openalex", "semantic_scholar", "crossref"]},
        {"keywords": ["supplementary direction A", "supplementary direction B"],
         "sources": ["openalex", "semantic_scholar"]},
    ],
    topic="Paper topic",
    target=50,
    per_page=5,
    refs_json=r'<OUTPUT_ROOT>/references.json',
)
```

### Mid-writing Supplementary Search

```python
await ac.search_and_save(
    keywords=["chapter-specific keyword"],
    sources=["openalex"],
    per_page=5,
    refs_json=r'<OUTPUT_ROOT>/references.json',
)
```

### Key Constraints

- **2-3 sources x 2-3 keywords per round**, `per_page=5`
- Set `target` to auto-skip remaining rounds once threshold is reached
- Results print to stdout; cite with `[@key]` during writing
- `refs_json` saves citation data; use `refs.autoBibliography()` in DOCX to auto-generate references

---

## 6. Citation Styles

Use `[@key]` in text. The DOCX engine auto-assigns numeric labels as **superscript** (e.g., `[@key]` → ^[1]^). Choose one style per paper. Do not manually write `h.text('[1]')` — always use the `[@key]` syntax to ensure correct superscript formatting.

| Style | In-text Format | Disciplines | Reference Format |
|-------|---------------|-------------|-----------------|
| APA 7th | (Author, Year) | Psychology, Education, Social Sci | `Author, A. A., & Author, B. B. (Year). Title. Journal, Vol(Iss), Pages. doi` — ≤20 all, 21+ first 19…last |
| IEEE | [1] numeric | Engineering, CS | `[N] A. A. Author, "Title," Journal, vol. X, no. Y, pp. Z–W, Year, doi` — >6 use et al. |
| Chicago | (Author Year) | History, Humanities | `Author, First. Year. "Title." Journal Vol (Iss): Pages. doi` — full first name |
| Harvard | (Author Year, p.X) | Business, Social Sci | `Author, A.A. (Year) 'Title', Journal, Vol(Iss), pp. Pages. doi` — ≥4 use et al. |
| Vancouver | [1] numeric | Medicine, Biomedical | `Author AA. Title. Journal Abbrev. Year;Vol(Iss):Pages. doi` — ≥7 use et al. |

### Consistency Rules (Highest Priority)

- Every `[@key]` must have a matching reference entry; every entry must be cited ≥1 time
- Same source always uses the same `[@key]`; max citation number = total reference count

---

## 7. DOCX Formatting

See [docx-api.md](docx-api.md) for initialization config, API reference, document assembly, and formatting notes (use "English single-column" or "English two-column" config).
