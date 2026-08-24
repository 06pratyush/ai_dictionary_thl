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
- **[GAP-05]** The corpus predates the Topic Page Specification. Entries on the legacy allowlist in `build/validate.py` render §1 and §3 from derived fallbacks and omit the sections they cannot honestly supply (Background, In-Depth prose, Revision History, Author). Every build prints the coverage count; the allowlist only ever shrinks. New entries are held to the full spec.

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

---

- **Timestamp:** 2026-08-13T03:00:00Z
- **Trigger Event:** AI Edit
- **Author/Agent:** Claude Opus 5 (Master Orchestrator)
- **Target Subsystem:** `data/`, `.orchestrator/corpus_batch.py`
- **Intent:** Third merge wave; tighten the delegation packet against circular definitions.
- **Bugs/Gaps Addressed:** The packet stated the anti-circularity rule abstractly and the model restated the headword in roughly two entries in five. It now enumerates the specific forbidden words per term with a worked example.
- **Context Modifications:** Corpus at 39 entries (21 AI & Mathematics, 18 Software Engineering Core); regenerated `terms/`, `index.html`, `data/search-index.json`, `sitemap.xml`.

---

- **Timestamp:** 2026-08-15T16:30:00Z
- **Trigger Event:** Site Integration
- **Author/Agent:** @06pratyush (Contributor) / Antigravity AI
- **Target Subsystem:** Site Integration & Navbar Wiring
- **Intent:** Integrate full aiDictionary_thl corpus into thehallucinatedlab.space under /dictionary/, wire up main site navigation, sitemaps, and test suites.
- **Bugs/Gaps Addressed:** Integrated 39 term pages, static search engine, and dictionary assets seamlessly into the live website structure.
- **Context Modifications:** Updated navigation bar to feature Dictionary tab right after Solutions across all pages, synced sitemap.xml, llms.txt, llms-full.txt, and passed all 377 site invariant tests.


---

- **Timestamp:** 2026-08-24T09:00:00Z
- **Trigger Event:** AI Edit
- **Author/Agent:** Claude Code (Master Orchestrator)
- **Target Subsystem:** `docs/TOPIC-PAGE-SPEC.md`, `docs/ENTRY-SCHEMA.md`
- **Intent:** Adopt the Topic Page Specification v1.0 as the entry contract, so every term page renders the same eighteen sections in the same order and every future term is authored against that shape rather than the ad-hoc lexical layout.
- **Bugs/Gaps Addressed:** The term page had five sections (Definition, Formula, Etymology, Relations, References) with no fixed contract, so page shape drifted with whatever fields an entry happened to carry. The spec fixes the order and the HTML ids; the schema doc now carries the `topic` block that supplies the prose sections.
- **Context Modifications:** Added `docs/TOPIC-PAGE-SPEC.md` (the spec verbatim plus a §5 binding it to the corpus field-by-field). `docs/ENTRY-SCHEMA.md` bumped to v2.0 with the `topic` block, the new validator rules, and the derived-fallback note. No code or data changed in this commit — contract first, implementation next.

---

- **Timestamp:** 2026-08-24T10:00:00Z
- **Trigger Event:** AI Edit
- **Author/Agent:** Claude Code (Master Orchestrator)
- **Target Subsystem:** `build/build.py` (term page renderer)
- **Intent:** Render every term page as a Topic Page — the spec's eighteen sections, in the spec's order, under the spec's HTML ids.
- **Bugs/Gaps Addressed:** `topic_sections()` is now the single source of truth for section order; the page body and the new on-page contents list are both built from its return value, so they cannot drift apart. Two integration defects were caught and fixed while wiring it up: `citations_html()` and `relations_html()` each emitted their own `<section><h2>`, which nested an h2 inside an h2 once the new renderer supplied the section wrapper — they now return bare bodies and h3 subsections respectively. `formula_html()` became dead code when `deep_dive_html()` absorbed the formula block, and was deleted rather than left orphaned.
- **Context Modifications:** `build/build.py` gains the §1–§17 section renderers, `topic_sections()`, `contents_html()`, `topic_meta_html()`, and a `topic_coverage()` line printed on every build. `jsonld_term()` now also emits `Article` (with author/reviewer/dates where recorded) and emits `FAQPage` **only** when the FAQ section actually rendered — structured data never describes an absent question. `aside_html()` carries the contents list plus the §0 metadata rows. All 39 term pages regenerated; each renders 7 spec sections with derived Quick Take and Final Formal Statement marked `data-derived="true"`. Coverage today: 0/39 migrated — tracked as GAP-05.

---

- **Timestamp:** 2026-08-24T10:45:00Z
- **Trigger Event:** AI Edit
- **Author/Agent:** Claude Code (Master Orchestrator)
- **Target Subsystem:** `build/build.py` (`entry_card`), `assets/css/dictionary.css`
- **Intent:** Bring the hub cards onto the topic-page interface and style the fourteen sections the renderer can now emit.
- **Bugs/Gaps Addressed:** The card showed the lexical domain and the raw first sense. It now prefers the topic category as its eyebrow and the authored Quick Take as its gloss, and carries a difficulty/reading-time strip — the three things a reader uses to choose a page. All three are rendered only where the entry records them, so an un-migrated card is byte-identical to what it was apart from the gloss source.
- **Context Modifications:** `entry_card()` rewritten with `card_meta_html()`. `assets/css/dictionary.css` gains ~330 lines covering §0–§17: the metadata chips, the contents list, the Quick Take and Final Formal Statement blocks, attributed blockquotes, prerequisite chips, derivation steps, video links, worked-example steps, the variants and revision tables, misconception pairs, application list, §12/§13 link buttons, FAQ items and the author block. `.entry-card { display: block }` is untouched — the parent site's `dictionary-browse.test.js` asserts against that rule and its specificity.
