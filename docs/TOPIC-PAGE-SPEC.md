# The Hallucinated Lab — Topic Page Specification (v1.0)

**Status:** Living document. Update the changelog at the bottom whenever this spec itself changes.
**Applies to:** Every topic/reference page on thehallucinatedlab.space (e.g. "Attention Mechanism", "RoPE", "SliceGPT").
**Goal:** One fixed structure, used every time, so pages are consistent for readers, easy to author, and structured enough to be citable by search/AI-answer engines.

---

## 0. How to use this spec

1. Copy the section skeleton below for every new topic.
2. Sections marked **Required** must be present. Sections marked **Optional** can be omitted if genuinely not applicable — don't force content into them.
3. Keep section order fixed. Consistent order is what makes the site feel like a reference work rather than a blog.
4. Each section maps to a semantic HTML id (table in §3) — use these exact ids when you build the `.html` template so styling/JS/anchors stay consistent across pages.

---

## 1. Section-by-section breakdown

### §0 — Metadata (front matter) — **Required**
Not rendered as visible prose; drives SEO/GEO, sorting, and internal tooling.

| Field | Notes |
|---|---|
| `title` | Canonical topic name |
| `slug` | URL-safe identifier |
| `category` | e.g. Architecture, Training, Tokenization, Systems |
| `tags` | 3–6 keywords |
| `difficulty` | Beginner / Intermediate / Advanced |
| `reading_time` | Estimated minutes |
| `status` | Draft / Published / Needs Review |
| `date_published` | ISO date |
| `date_updated` | ISO date |
| `author` | Name/handle |
| `reviewer` | If applicable |
| `canonical_url` | Full URL |
| `meta_description` | 150–160 chars, written as a standalone answer — this is what gets pulled into search/AI-overview snippets |
| `schema_type` | Suggested: `Article` + `DefinedTerm`, or `FAQPage` if the FAQ section is substantial |

### §1 — Quick Take (TL;DR) — **Required**
2–3 plain-English sentences. No jargon, no citations. This is the block most likely to get lifted verbatim by an AI answer engine, so write it as a self-contained answer, not a teaser.

### §2 — Formal Definitions (max 3) — **Required**
Up to three definitions pulled from reliable, reputable sources — see the **Definition Source Hierarchy** in §2 below. Each definition:
- Blockquoted, with inline attribution (author, source, year).
- Short enough to be fair use — a sentence or two, not a paragraph.
- Chosen for *disagreement or complementary angle*, not redundancy. If three sources say the same thing the same way, use one.

Use three only when the topic genuinely has competing framings (e.g. attention as "soft dictionary lookup" vs. "learned weighted average" vs. "differentiable content-based addressing"). Simple topics may need only one.

### §3 — Final Formal Statement — **Required**
Your own synthesized, canonical definition — written in the site's voice, reconciling §2. This is the sentence you'd want quoted elsewhere; treat it as the page's citation asset.

### §4 — Etymology — **Required**
Where the term came from: who coined it, in what paper/context, what it was called before (if renamed), and any notable naming disputes.

### §5 — Background & Motivation — **Required**
What problem existed before this concept, what limitations of prior approaches motivated it, and the historical moment it emerged in. This is "why does this exist" — not "how does it work" (that's §7).

### §6 — Prerequisites — **Optional, recommended**
Bulleted list of concepts the reader should already know, each linking to its own page on the site if one exists. This is what turns isolated pages into a knowledge graph.

### §7 — In-Depth Explanation — **Required**
The core content:
- Conceptual explanation, building from intuition to formalism.
- Full mathematical formulation and derivation where applicable (use KaTeX/MathJax; show intermediate steps, don't skip to the result).
- Diagrams where they clarify structure or flow.
- Pseudocode or a minimal code snippet if it aids understanding.
- 1–3 curated video links (embedded, with title + creator + why it's included).

### §8 — Worked Example — **Optional, recommended for math-heavy topics**
A concrete walkthrough with actual numbers — small enough to trace by hand. Distinct from the derivation in §7: the derivation proves it works, this shows how to compute it.

### §9 — Variants & Related Concepts — **Optional**
Short comparison of siblings or variants (e.g. self- vs. cross- vs. multi-head attention). A small comparison table is usually the clearest format.

### §10 — Common Misconceptions — **Optional, recommended**
2–4 things people commonly get wrong about the topic, stated plainly and corrected.

### §11 — Real-World Applications — **Optional, recommended**
Where this shows up in practice — specific systems, papers, or products, not generic statements.

### §12 — More Resources (internal) — **Required if applicable**
Same-site articles, blog posts, or artifacts related to this topic, each as a link button. Omit the section entirely if nothing yet exists rather than leaving it empty.

### §13 — Further Reading (external, curated) — **Optional**
A short, hand-picked list of external resources worth reading beyond what's cited in §14 — distinct from References: this is recommendation, not citation trail.

### §14 — FAQ — **Optional, recommended for AI-answer-engine visibility**
3–6 question/answer pairs, each answerable in 2–4 sentences. Q&A-formatted content is disproportionately surfaced by AI answer engines, so this section pulls weight beyond just reader convenience.

### §15 — References — **Required**
Full citation list for everything drawn on in §2 and §7. One consistent format across the whole site:

```
[n] Author(s). "Title." Publisher/Venue, Year. Accessed: YYYY-MM-DD. URL
```

Numbered inline `[n]` markers in the body should match this list. Every source in §2 must appear here.

### §16 — Revision History — **Required**
| Version | Date | Change | Editor |
|---|---|---|---|
| 1.0 | YYYY-MM-DD | Initial publish | |

Necessary in a fast-moving field — pages will need correction as understanding shifts.

### §17 — Author & Review — **Required**
Who wrote and (if applicable) reviewed the page, with a link to a bio/credentials page. This is an E-E-A-T signal — it's part of what makes original research on the site function as a citable authority rather than an anonymous blog post.

---

## 2. Definition Source Hierarchy (for §2 and §15)

Prefer sources in this order when choosing what to cite:

1. **Primary source** — the original paper that introduced the concept.
2. **Standard textbook** — e.g. Goodfellow/Bengio/Courville, Bishop, Jurafsky & Martin.
3. **Official technical documentation** — e.g. PyTorch, Hugging Face, framework docs.
4. **Established course materials** — e.g. Stanford CS224n/CS231n lecture notes.
5. **Reputable technical encyclopedia** — established computing/ML reference works.
6. **Expert-authored blog/explainer** — only when authored by a recognized practitioner or researcher, and only if nothing above covers the angle needed.

Avoid uncredited blogs, SEO-farm explainers, and secondary aggregators — even if convenient, they weaken the page's trust signal.

---

## 3. HTML section-ID mapping

For consistency when the `.html` template is built, use these ids:

| Section | HTML id |
|---|---|
| Metadata (not rendered) | — |
| Quick Take | `#quick-take` |
| Formal Definitions | `#definitions` |
| Final Formal Statement | `#formal-statement` |
| Etymology | `#etymology` |
| Background & Motivation | `#background` |
| Prerequisites | `#prerequisites` |
| In-Depth Explanation | `#deep-dive` |
| Worked Example | `#worked-example` |
| Variants & Related Concepts | `#variants` |
| Common Misconceptions | `#misconceptions` |
| Real-World Applications | `#applications` |
| More Resources | `#more-resources` |
| Further Reading | `#further-reading` |
| FAQ | `#faq` |
| References | `#references` |
| Revision History | `#revision-history` |
| Author & Review | `#about-author` |

---

## 4. Compact example skeleton — "Attention Mechanism"

```
---
title: Attention Mechanism
slug: attention-mechanism
category: Architecture
tags: [transformers, attention, deep-learning, NLP]
difficulty: Intermediate
reading_time: 12
status: Draft
date_published: 2026-08-24
date_updated: 2026-08-24
author: Vidya
canonical_url: https://thehallucinatedlab.space/topics/attention-mechanism
meta_description: "Attention is a mechanism that lets a model weigh and combine information from different parts of its input based on learned relevance scores."
schema_type: Article, DefinedTerm
---

## Quick Take
Attention lets a model decide, for each token, how much to "look at" every
other token when building its representation — instead of relying on a
fixed-size summary or strict left-to-right order.

## Formal Definitions
> [Source A definition] — [Author, Year] [1]
> [Source B definition] — [Author, Year] [2]

## Final Formal Statement
[Synthesized canonical definition.]

## Etymology
...

## Background & Motivation
...

## Prerequisites
- [Vector embeddings](/topics/embeddings)
- [Softmax function](/topics/softmax)

## In-Depth Explanation
[Conceptual build-up → Q/K/V formulation → scaled dot-product derivation → diagram → video links]

## Worked Example
[Small 3-token numeric walkthrough]

## Variants & Related Concepts
| Variant | Key difference |
|---|---|
| Self-attention | Q, K, V from same sequence |
| Cross-attention | Q from one sequence, K/V from another |
| Multi-head attention | Multiple attention subspaces in parallel |

## Common Misconceptions
...

## Real-World Applications
...

## More Resources
- [Link button: internal article on GQA]
- [Link button: internal artifact — transformer forward pass demo]

## Further Reading
...

## FAQ
...

## References
[1] ...
[2] ...

## Revision History
| Version | Date | Change | Editor |
|---|---|---|---|
| 1.0 | 2026-08-24 | Initial publish | Vidya |

## Author & Review
Written by Vidya. [Bio link]
```

---

## Changelog (for this spec itself)

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-08-24 | Initial specification, based on the 7-section draft, expanded to 18 sections/blocks. |

---

## 5. How this spec binds to the dictionary corpus

This repository is the implementation of the spec above. The mapping is fixed,
mechanical, and enforced by `build/validate.py`:

| Spec section | HTML id | Entry JSON source |
|---|---|---|
| §0 Metadata | — | `topic.category`, `topic.difficulty`, `topic.readingTime`, `topic.status`, `topic.datePublished`, `topic.dateUpdated`, `topic.author`, `topic.reviewer`, `topic.metaDescription` |
| §1 Quick Take | `#quick-take` | `topic.quickTake` |
| §2 Formal Definitions | `#definitions` | `topic.formalDefinitions[]` (max 3), falling back to `definitions[]` |
| §3 Final Formal Statement | `#formal-statement` | `topic.formalStatement` |
| §4 Etymology | `#etymology` | `etymology`, `firstAttested` |
| §5 Background & Motivation | `#background` | `topic.background[]` |
| §6 Prerequisites | `#prerequisites` | `topic.prerequisites[]` |
| §7 In-Depth Explanation | `#deep-dive` | `topic.deepDive` (+ `formula`) |
| §8 Worked Example | `#worked-example` | `topic.workedExample` |
| §9 Variants & Related Concepts | `#variants` | `topic.variantsTable`, `synonyms`, `antonyms`, `related` |
| §10 Common Misconceptions | `#misconceptions` | `topic.misconceptions[]` |
| §11 Real-World Applications | `#applications` | `topic.applications[]` |
| §12 More Resources | `#more-resources` | `topic.moreResources[]` |
| §13 Further Reading | `#further-reading` | `topic.furtherReading[]` |
| §14 FAQ | `#faq` | `topic.faq[]` |
| §15 References | `#references` | `citations[]` |
| §16 Revision History | `#revision-history` | `topic.revisions[]` |
| §17 Author & Review | `#about-author` | `topic.author`, `topic.reviewer` |

### The rule for new entries

**Every term added from now on carries a complete `topic` block.** The validator
rejects any entry that does not, unless its slug appears in the legacy migration
allowlist in `build/validate.py` — the 39 entries that predate this spec. That
list only ever shrinks: migrating an entry means authoring its `topic` block and
deleting its slug from the allowlist. It is never extended.

### What the build derives, and what it refuses to invent

Sections the spec marks **Required** are rendered for every entry. Where a
legacy entry has no authored content for one, the build derives it from data the
entry already carries — a Quick Take from the first sense, a Final Formal
Statement from the headword plus that sense — and marks the section
`data-derived="true"` so the gap is visible in the markup rather than hidden.

The build never invents a source. §2 renders attributed blockquotes only when
`topic.formalDefinitions[]` supplies them; otherwise it renders the entry's own
senses, unattributed and clearly the site's own. §14 emits `FAQPage` JSON-LD
only when FAQ pairs are actually rendered on the page — structured data
describing absent content is a manual-action risk, not a style opinion.
