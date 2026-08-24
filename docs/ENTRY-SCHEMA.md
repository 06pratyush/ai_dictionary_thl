# Lexical Entry Schema v2.0

Every entry in `data/ai-mathematics.json` and `data/software-engineering.json`
conforms to this shape. `build/validate.py` enforces it; the build fails on any
violation. Rule numbers refer to the Master Lexicographical Framework.

**v2.0 adds the `topic` block.** Every entry added from this point carries one,
and the rendered page follows `docs/TOPIC-PAGE-SPEC.md` section for section. The
lexical fields below are unchanged — the topic block sits alongside them and
supplies the prose sections the spec requires.

```jsonc
{
  "lid":      "AIM-00042",        // Rule 101. Unique. Prefix AIM- or SWE-.
  "term":     "Gradient Descent", // Display form. Capitalisation preserved (Rule 104).
  "slug":     "gradient-descent", // URL segment. Lowercase, hyphenated, unique site-wide.
  "ngram":    "bigram",           // Rule 102: unigram | bigram | polygram. Derived, not authored.
  "syllables":"gra·di·ent de·scent",   // Rule 203. Interpuncts.
  "ipa":      "/ˈɡreɪdiənt dɪˈsɛnt/",  // Rule 204.
  "pos":      "noun",             // Rule 206.
  "domain":   "Optimization",     // Sub-field label shown as the entry eyebrow.
  "tags":     ["Core"],           // Free labels: Core, Foundational, Archaic, Jargon, Slang…
  "abbr":     ["GD"],             // Abbreviations and acronyms that must also resolve to this LID.
  "inflections": ["gradient descents"],  // Rule 202/715. Redirect to this lemma.
  "variants":    ["gradient-descent"],   // Rule 106/303. Spelling and spacing variants.

  "definitions": [                // Rule 504: ordered by modern frequency of use.
    {
      "id": 1,
      "context": "in optimization",   // Rule 511. Optional bracketed frame. Omit if none.
      "text": "an iterative method that …",  // Rule 501/502/503: substitutable, non-circular,
                                             // lowercase start, ends with a period.
      "example": "The model converged after …"  // Rule 507. Required on every definition.
    }
  ],

  "formula": {                    // Optional. AI & Mathematics entries mainly.
    "latex": "\\theta_{t+1} = \\theta_t - \\eta \\nabla J(\\theta_t)",
    "plain": "theta(t+1) = theta(t) - eta * grad J(theta(t))",
    "note":  "eta is the learning rate."
  },

  "etymology": "From …",          // Rule 515-519. "[Origin obscure]" when unattested (Rule 517).
  "firstAttested": "1847",        // Year or empty string.

  "synonyms": [                   // Rule 521-527. senseId is mandatory — never map to the LID alone.
    { "term": "steepest descent", "senseId": 1, "proximity": "Near" }
  ],
  "antonyms": [
    { "term": "gradient ascent", "senseId": 1, "polarity": "Relational" }
  ],

  "related":   ["backpropagation", "learning-rate"],  // slugs. Rendered as cross-links (Rule 604).
  "citations": [                  // Rule: every entry carries at least one verifiable reference.
    { "label": "Cauchy, A. (1847). Méthode générale …",
      "source": "Comptes Rendus de l'Académie des Sciences",
      "url": "https://…" }
  ],

  "topic": {                      // Topic Page Spec v1.0. Required on every new entry.
    "category":    "Optimization",       // §0. Architecture | Training | Tokenization | Systems | …
    "difficulty":  "Intermediate",       // §0. Beginner | Intermediate | Advanced
    "readingTime": 9,                    // §0. Whole minutes.
    "status":      "Published",          // §0. Draft | Published | Needs Review
    "datePublished": "2026-08-24",       // §0. ISO date.
    "dateUpdated":   "2026-08-24",       // §0. ISO date.
    "author":   "Vidya",                 // §0/§17.
    "reviewer": "",                      // §0/§17. Empty when unreviewed.
    "metaDescription": "…",              // §0. 150-160 chars, standalone answer.

    "quickTake": "…",                    // §1. 2-3 plain-English sentences, no jargon.

    "formalDefinitions": [               // §2. Max 3. Chosen for contrast, not redundancy.
      { "quote": "…", "author": "Cauchy, A.", "year": "1847", "ref": 1 }
    ],                                   // ref -> 1-based index into citations[].

    "formalStatement": "…",              // §3. The site's own canonical sentence.

    "background": ["…", "…"],            // §5. Paragraphs. Why this exists, not how it works.

    "prerequisites": [                   // §6. slug links into the corpus where one exists.
      { "label": "Softmax", "slug": "softmax" }
    ],

    "deepDive": {                        // §7. The core content.
      "paragraphs": ["…"],
      "steps": ["…"],                    // Optional derivation steps, rendered as an ordered list.
      "videos": [ { "title": "…", "creator": "…", "url": "https://…", "why": "…" } ]
    },

    "workedExample": {                   // §8. Concrete numbers, traceable by hand.
      "intro": "…",
      "steps": ["…"]
    },

    "variantsTable": {                   // §9. Sibling comparison.
      "columns": ["Variant", "Key difference"],
      "rows": [["…", "…"]]
    },

    "misconceptions": [                  // §10. 2-4 pairs.
      { "claim": "…", "correction": "…" }
    ],

    "applications": [                    // §11. Named systems, not generic statements.
      { "name": "…", "detail": "…" }
    ],

    "moreResources": [                   // §12. Same-site links only. Omit if nothing exists.
      { "label": "…", "href": "/articles.html" }
    ],

    "furtherReading": [                  // §13. External recommendation, not citation trail.
      { "label": "…", "href": "https://…", "note": "…" }
    ],

    "faq": [                             // §14. 3-6 pairs, each answerable in 2-4 sentences.
      { "q": "…", "a": "…" }
    ],

    "revisions": [                       // §16. Append-only.
      { "version": "1.0", "date": "2026-08-24", "change": "Initial publish", "editor": "Vidya" }
    ]
  },

  "frequency": 95,                // 0-100 corpus-frequency proxy. Rule 718 tie-breaker.
  "opacity":   null,              // Rule 417. 1-3 for idiomatic jargon; null for literal terms.
  "flags":     []                 // Rule 107/108/422: NSFW, Archaic, Obsolete, Historical.
}
```

## Authoring rules that the validator enforces

| Check | Rule | Failure mode |
| :--- | :--- | :--- |
| `lid` unique across both corpora | 101 | duplicate LID |
| `slug` unique across both corpora | — | page collision in `terms/` |
| `slug` matches `^[a-z0-9]+(-[a-z0-9]+)*$` | — | broken URL |
| definition text starts lowercase, ends `.` | 503 | style violation |
| definition text does not contain the headword stem | 502 | circular definition |
| every definition has a non-empty `example` | 507 | missing context |
| every `synonyms[]` / `antonyms[]` entry has a valid `senseId` | 521 | sense-blind mapping |
| `related[]` slugs all resolve to a real entry | 604 | dead cross-reference |
| at least one citation | — | unsourced claim |
| `proximity` ∈ {Absolute, Near} | 523 | bad enum |
| `polarity` ∈ {Complementary, Gradable, Relational} | 525 | bad enum |
| `ngram` agrees with the whitespace-separated word count of `term` | 102/103 | mis-tagged |
| `topic` present on every entry outside the legacy allowlist | Spec §0 | entry does not follow the topic page interface |
| `topic.difficulty` ∈ {Beginner, Intermediate, Advanced} | Spec §0 | bad enum |
| `topic.status` ∈ {Draft, Published, Needs Review} | Spec §0 | bad enum |
| `topic.metaDescription` is 150–160 chars | Spec §0 | snippet truncated or padded in search results |
| `topic.readingTime` is a positive whole number | Spec §0 | bad metadata |
| ISO dates on `datePublished` / `dateUpdated` | Spec §0 | bad metadata |
| every Required spec section has authored content | Spec §1–§5, §7, §15–§17 | incomplete topic page |
| at most 3 `topic.formalDefinitions[]` | Spec §2 | redundant citation stack |
| every `formalDefinitions[].ref` resolves to a `citations[]` index | Spec §2/§15 | dangling reference marker |
| `topic.prerequisites[].slug` resolves to a real entry | Spec §6 | dead cross-reference |
| `topic.moreResources[].href` is same-site | Spec §12 | external link in an internal section |
| `topic.revisions[]` non-empty, ISO-dated | Spec §16 | no revision trail |

## LID allocation

`.orchestrator/termlist-aim.json` and `termlist-swe.json` are the canonical LID
registries for their sections. Take the next free number from there when adding
a term, and add the term to the registry in the same commit — authoring an entry
with a number the registry has already promised to another term produces a
duplicate LID, which the validator rejects but only after the fact.

## The topic page contract

`docs/TOPIC-PAGE-SPEC.md` is the authority on what each section means and in what
order it renders. Two consequences for authoring:

1. **New entries carry a complete `topic` block.** The validator fails the build
   otherwise. The only exemption is the legacy migration allowlist in
   `build/validate.py`, which holds the 39 entries that predate the spec and only
   ever shrinks.
2. **Optional sections are omitted, not padded.** An empty `misconceptions` or
   `faq` array renders nothing at all. Do not invent content to fill a section —
   a thin section is worse than an absent one, and the FAQ in particular emits
   `FAQPage` structured data, so a fabricated question is a search-manual-action
   risk.

## Fields the build derives — never author them by hand

- `ngram` is recomputed from `term`.
- `search-index.json` (headword, abbr, inflections, variants, synonyms, definition
  text, edge n-grams) is generated by `build/build.py` per Rules 710-712.
- `terms/<slug>.html` is generated from the entry plus the page template.
- `sitemap.xml` is generated from the union of both corpora.
- §1 Quick Take and §3 Final Formal Statement are derived from `definitions[0]`
  for legacy entries that have not been migrated yet. The derived markup carries
  `data-derived="true"`. Authoring `topic.quickTake` / `topic.formalStatement`
  replaces the derivation — never edit the generated page to do it.
