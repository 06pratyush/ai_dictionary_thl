## Session 2026-08-13
Models available: orch-reader (gemma4:e4b @ 64K ctx, resident), gemma4:e4b,
gemma4:latest (same blob as e4b), llama3:latest, kimi-k2.5/2.6 (cloud)
Goal: build the two-corpus dictionary for thehallucinatedlab.space — one search
bar across both sections, one static page per term.

### Units
| # | Task | Route | Model | Attempts | Status | Notes |
|---|------|-------|-------|----------|--------|-------|
| 1 | Orchestrator harness | RETAIN | — | 1 | merged | delegate/extract/ask/warm/gate/htmlcheck |
| 2 | Entry schema + CONTEXT.md | RETAIN | — | 1 | merged | architecture; sets every downstream contract |
| 3 | Design tokens + dictionary CSS | RETAIN | — | 1 | merged | creative work per §11.4 |
| 4 | Search engine (Series 700) | RETAIN | — | 1 | merged | algorithmic core; 26 conformance tests |
| 5 | Corpus validator | RETAIN | — | 1 | merged | the firewall for delegated content |
| 6 | Static generator + hub template | RETAIN | — | 1 | merged | owns terms/, index.html, sitemap |
| 7 | Seed corpus entries (7) | RETAIN | — | 1 | merged | exemplars that define house style |
| 8 | Corpus expansion (~89 entries) | DELEGATE | orch-reader | 3 | in progress | one term per packet; see below |
| 9 | Search conformance tests | RETAIN | — | 1 | merged | wrote alongside the engine; packet would have exceeded the code |

### Failure patterns (fold into future packets)
- **`ollama run` corrupts output.** It emits cursor-movement and erase-line
  codes even when stdout is redirected, and hard-wraps at terminal width.
  Stripping the codes afterwards leaves duplicated fragments
  ("generaliz generalize") because erase-line is semantic, not decorative.
  Fixed structurally: all dispatch now goes through the HTTP API.
- **Loading `gemma4:e4b` alongside `orch-reader` OOMs.** They are the same 9.6GB
  blob under two tags. Route code work to the resident model.
- **Batching entries fails.** Eight per packet drifts off-schema and truncates
  around entry two. One deliverable per packet holds every time (§5).
- **LaTeX backslashes are emitted unescaped** into JSON. Deterministic, so
  repaired in extract.py rather than spent on a correction cycle.
- **The headword is echoed into `variants`.** Repaired in merge_generated.py.
- **Definitions restate the headword** despite an explicit prohibition
  (convolutional-neural-network). Caught by the anti-circularity check; rejected.
- **Etymologies are the one unsalvageable field.** In 4 of the first 6 entries
  the model produced banned filler ("a descriptive compound term combining…"),
  and where it produced a real derivation it was wrong — "loss" was given an Old
  French root when the word is Old English *los*. Re-prompting will not fix a
  knowledge gap. Any etymology matching the filler shapes is now replaced with
  `[Origin obscure]` per Rule 517 and queued for authoring.

### Decisions
- **Definitions and examples ARE delegable; etymologies are not.** The
  generated definitions are substitutable, accurate and genuinely usable, and
  the citations point at real works. Word origins are the one field where the
  model is confidently wrong, so that field is quarantined by default.
- Corpora are data, never code (RULE-01). Every definition lives in
  `data/*.json`; nothing is inlined into HTML or JS.
- The hub page is generated, not hand-written, so both section indexes ship as
  static HTML and the site survives JavaScript being off (RULE-08).
- `--text-muted` is lifted to #827b74 here (4.60:1, AA pass). The parent site
  still ships the failing #5a5550; logged as GAP-01 rather than silently
  diverging.
- One term per delegation packet, dispatched by a resumable batch script that
  skips work already on disk.
