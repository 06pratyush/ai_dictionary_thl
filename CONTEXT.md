# SYSTEM CONTEXT MANIFEST & EXECUTION TIMELINE

## 1. PROJECT IDENTIFICATION & OPERATIONAL STATE
- **Project Identifier:** The Hallucinated Lab — Dictionary
- **Operational Status:** ACTIVE DEVELOPMENT
- **System Purpose:** A static, zero-build reference dictionary with two corpora — AI & Mathematics and Software Engineering Core — unified behind one client-side search engine. Ships as a new navbar section of thehallucinatedlab.space.

## 2. TECHNICAL STACK MATRIX
| Layer | Technology | Version | Enforcement Rules |
| :--- | :--- | :--- | :--- |
| **Markup** | Static HTML5 | — | One `<h1>` per page; semantic landmarks; skip link on every page |
| **Styling** | Vanilla CSS custom properties | — | Tokens only; never hard-code a colour, radius, or easing curve |
| **Client logic** | Vanilla ES2020 modules | — | No frameworks, no bundler, no runtime dependencies |
| **Data** | JSON corpora | — | Schema-validated; every entry carries a unique LID |
| **Generator** | Python (stdlib only) | 3.14 | Build-time only; never shipped to the browser |
| **Hosting** | GitHub Pages | — | 100% static output; no server, no cookies, no trackers |

## 3. ARCHITECTURAL BOUNDARIES & RULES
1. **[RULE-01]** Corpora are data, never code. No definition text may live in a `.js` or `.html` source file — it lives in `data/*.json` and is rendered.
2. **[RULE-02]** The search engine is corpus-agnostic. It receives an index and a config; it never hard-codes a section name, term, or LID prefix.
3. **[RULE-03]** Every term gets a real, crawlable static page at `terms/<slug>.html`. No client-side-only routing for term content.
4. **[RULE-04]** `build/build.py` is the only writer of `terms/`, `data/search-index.json`, and `sitemap.xml`. Those are generated artefacts; never hand-edit them.
5. **[RULE-05]** All visual values come from the tokens in `assets/css/tokens.css`, which mirrors the site design language exactly.
6. **[RULE-06]** No external runtime dependency may be added. Google Fonts is the only permitted external request.
7. **[RULE-07]** Every definition must satisfy the anti-circularity rule (Rule 502) — enforced mechanically by `build/validate.py`.
8. **[RULE-08]** Search must degrade gracefully: with JavaScript disabled the section indexes and every term page still render and remain navigable.

## 4. CURRENT SYSTEM GAPS & KNOWN SHORTCOMINGS
- **[GAP-01]** `--text-muted` (#5a5550) fails WCAG AA at 2.60:1. This project ships the corrected `#827b74` (4.60:1) locally; the parent site has not adopted it, so the two will differ until it does.
- **[GAP-02]** Corpus coverage is a seeded baseline, not exhaustive. Expansion is incremental and additive.
- **[GAP-03]** Search index is shipped whole to the client. Fine at the current corpus size; past roughly 5,000 entries it needs sharding or a server-side endpoint.
- **[GAP-04]** IPA transcriptions are supplied for headwords only, not for every inflected form.

## 5. IMMUTABLE EXECUTION TIMELINE & BUG LOG
*(Append-only log. Never erase previous entries.)*

<!-- TIMELINE LOGS BEGIN BELOW THIS LINE -->

- **Timestamp:** 2026-08-13T00:00:00Z
- **Trigger Event:** Project Initialization
- **Author/Agent:** Claude Opus 5 (Master Orchestrator)
- **Target Subsystem:** Core System
- **Intent:** Bootstrap the orchestrator delegation harness and establish the context manifest.
- **Bugs/Gaps Addressed:** None — greenfield.
- **Context Modifications:** Added `.orchestrator/` (delegate, extract, ask, warm, gate, htmlcheck), `.gitignore`, `CONTEXT.md`.

---

- **Timestamp:** 2026-08-13T01:00:00Z
- **Trigger Event:** AI Edit
- **Author/Agent:** Claude Opus 5 (Master Orchestrator)
- **Target Subsystem:** `assets/`, `build/`, `tests/`
- **Intent:** Build the dictionary end to end — design tokens, the Series 700 search engine, the corpus validator, and the static generator that owns `terms/`, `index.html`, the search index and the sitemap.
- **Bugs/Gaps Addressed:**
  - `ollama run` corrupted delegated output with terminal erase-line codes, leaving duplicated word fragments. Dispatch moved to the HTTP API.
  - Loading `gemma4:e4b` alongside the resident `orch-reader` exhausted memory — they are the same blob under two tags.
  - Derived index buckets stored one entry several times when the headword, a token and an inflection all reached the same key, triplicating suggestions and inflating that entry's rank by up to 3x.
- **Context Modifications:** `assets/css/{tokens,dictionary}.css`, `assets/js/{search-engine,app,nav}.js`, `build/{validate,build,merge_generated}.py`, `build/templates/index.html`, `tests/search-engine.test.mjs`, `package.json`, CI workflows.

---

- **Timestamp:** 2026-08-13T02:00:00Z
- **Trigger Event:** AI Edit
- **Author/Agent:** Claude Opus 5 (Master Orchestrator)
- **Target Subsystem:** `data/`
- **Intent:** Land the corpus baseline — 37 entries across both sections, part generated locally under gate, part authored.
- **Bugs/Gaps Addressed:**
  - Authored Software Engineering entries reused LIDs already assigned by `.orchestrator/termlist-swe.json`, producing 12 duplicate identifiers. Caught by the validator and reconciled against the termlist, which is the canonical LID registry for that section.
  - Four generated entries defined a term using its own headword; rejected by the anti-circularity check and rewritten by hand.
  - Six generated etymologies were filler or factually wrong; quarantined under Rule 517 and authored.
- **Context Modifications:** `data/ai-mathematics.json` (20 entries), `data/software-engineering.json` (17 entries), regenerated `terms/`, `index.html`, `data/search-index.json`, `sitemap.xml`.
