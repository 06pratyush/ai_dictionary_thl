# The Unified SEO + AI Search Playbook (2026)
### For thehallucinatedlab.space — Google Search, Google AI Overviews/AI Mode, ChatGPT, Perplexity

A note on scope: this is an expansion of your original 100-item checklist, not a padded-to-a-number version of it. It's organized into 9 pillars plus **per-page-type playbooks** (which your original file didn't have), because "optimize the site" and "optimize this specific comparison page" require different actions. Total distinct, non-redundant instructions: ~360.

---

## 0. What actually changed since your last version (read this first)

- AI Overviews now appear on roughly **48% of Google queries** (up from 34.5% three months earlier), and about **68% of US Google searches result in zero clicks** to any external site. Ranking #1 no longer guarantees traffic — it guarantees eligibility to be *cited*, which is a different game.
- Pages **cited inside** an AI Overview see ~35% more clicks than a standard #1 organic result would. The new objective is citation rate, not rank position, for informational queries specifically. Transactional/navigational queries still behave like classic SEO.
- Google shipped a dedicated **Search Generative AI performance report inside Search Console (June 3, 2026)**, with impressions-by-page for AI Overviews, AI Mode, and generative Discover — plus a toggle to opt content out of AI features without a ranking penalty. This is now your primary AI-visibility measurement tool; stop guessing from anecdote.
- **Preferred Sources** now follows users into AI Overviews and AI Mode, not just classic Top Stories. A user who marks you as preferred is more likely to see you surfaced inside an AI answer.
- Google's own public stance: for Google specifically, there is **no separate GEO/AEO discipline** — the same fundamentals that earn rankings earn AI citations. This does *not* extend to ChatGPT, Perplexity, or Claude, which crawl and rank sources independently — so a two-track strategy (Google-native + LLM-crawler-native) is still correct for those surfaces.
- E-commerce queries trigger AI Overviews far less often now (~4%, down from ~29% at launch) — Google is deliberately preserving click-through commercial SERPs. Don't over-invest GEO effort on pure product pages; invest it in informational/comparison content instead.
- AI Mode queries average roughly 3x longer than typical search queries, and are closer to full questions or multi-step research asks than keyword strings. Content structured around question-answer pairs benefits disproportionately.

---

## 🧠 Pillar 1 — Generative Engine Optimization (GEO) & LLM Ingestion

**Foundational file hygiene**
1. Host a `/llms.txt` file at the root summarizing the site's purpose, core sections, and highest-value URLs in plain Markdown.
2. Host `/llms-full.txt` as a deeper index so crawlers with limited context windows don't miss inner pages.
3. Keep both files under version control and regenerate them automatically on publish, not by hand — they go stale fast on a growing site.
4. Add a changelog line at the top of `llms-full.txt` (`Last updated: YYYY-MM-DD`) so an LLM can judge freshness without re-crawling everything.
5. Cross-link `/llms.txt` from your `robots.txt` and footer, since not all crawlers discover root files automatically.

**Writing for extraction, not persuasion**
6. Pass the "Island Test": every paragraph should stand alone semantically — an LLM lifting one paragraph out of context shouldn't lose meaning.
7. Open every H2/H3 with a direct, one-sentence definition or answer before any elaboration — this is the sentence most likely to get lifted verbatim into a synthesized answer.
8. Eliminate vague pronouns ("it," "this," "that") in favor of the actual noun, especially across paragraph and sentence boundaries.
9. Write in Subject–Predicate–Object order wherever possible; avoid inverted or heavily subordinate-clause sentence structures that confuse dependency parsing.
10. Use one consistent name per concept/feature across the entire site — don't let marketing rename the same thing three ways across different pages.
11. Keep each landing page atomic: one core intent, one core answer, one core CTA. Split multi-intent pages rather than trying to rank one page for everything.
12. Place code snippets, examples, or worked cases directly next to the concept they illustrate — not in a separate "examples" section three scrolls down.
13. Ditch figurative/abstract marketing language in favor of literal, specific claims — "reduces inference latency by ~40% at 7B parameters on consumer GPUs" beats "blazing fast."
14. Answer the implicit question in the URL slug or title within the first 150 words of body copy — don't make the reader (or model) infer intent from structure alone.
15. Write numbers as digits, not spelled out, in any content meant for statistical extraction — models parse "23%" more reliably than "twenty-three percent" in tabular/data contexts.

**Query coverage**
16. Target conversational long-tail phrasing that matches how people type into AI Mode or ask ChatGPT — full questions, not fragment keywords.
17. Build "fan-out" coverage: break one comprehensive pillar topic into the 6–10 granular sub-questions an AI would decompose it into, and make sure each has an answerable section or dedicated page.
18. Maintain a living list of the exact questions your target audience asks (from support tickets, forum threads, your own DMs) and map each to a URL that answers it directly — treat this as your actual GEO keyword list, not a keyword-volume tool export.
19. For technical/dev-audience content specifically, mirror the phrasing developers use in GitHub issues and Stack Overflow, not marketing phrasing — that's the training distribution LLMs weight most heavily for technical citation.
20. Prioritize comparison and "X vs Y" framing for any concept where multiple approaches exist (this matters enormously for you given the MoE/MLA/GQA-type content you write) — AI answers to "should I use X or Y" queries pull disproportionately from pages that already frame the tradeoff explicitly.

**Citation bait & distribution**
21. Put your single strongest stat, rule, or claim per section into a blockquote — visually distinct blocks are disproportionately likely to be lifted as the citable "quote" in a synthesized answer.
22. Syndicate substantial pieces to high-authority hubs (Reddit, dev.to, Hashnode, relevant subreddits, Medium) where AI crawlers index frequently and community engagement acts as a trust signal.
23. Track Share of Voice — how often your brand/domain is named across AI answers for your core topics — as a KPI, not just clicks. Use manual query sampling across ChatGPT/Perplexity/AI Overviews weekly if you don't have paid tooling.
24. Build one canonical "alternative to X" page per meaningful competitor/tool in your space, targeting the exact buying-intent phrasing people use.
25. Build explicit, factual 1v1 comparison tables (not narrative prose) for major head-to-head decisions in your niche — tables are what both classic snippets and LLM extraction favor.
26. Inject verifiable statistics and named sources into technical claims; AI answer-generation systems actively seek data points to ground otherwise-vague claims.
27. Audit server/bot logs monthly for crawl frequency from GPTBot, ClaudeBot, PerplexityBot, Applebot-Extended, Google-Extended, and CCBot — a page never crawled by these agents cannot be cited by their respective products, regardless of content quality.
28. Where budget allows, add interactive elements (a small calculator, a config generator, a code sandbox) — dwell-time and engagement signals still matter for classic ranking even though LLMs can't "interact" with them directly.
29. Explicitly allow (don't accidentally block) the LLM crawlers you *want* indexing you in `robots.txt`, and explicitly disallow ones whose training use you object to — these are two separate decisions, not one toggle.
30. Republish/update your single best-performing piece of original research or benchmark data at least twice a year with a visible "updated" date — freshness plus originality is currently the single strongest AI-citation combination available to a small site.

---

## 🛠️ Pillar 2 — Technical SEO & Crawlability

31. Maintain strict, non-skipping heading hierarchy (H1 → H2 → H3) sitewide — a skipped level breaks both accessibility tooling and LLM section-parsing.
32. Keep an auto-updating XML sitemap registered in Search Console and (separately) Bing Webmaster Tools.
33. Configure `robots.txt` deliberately per user-agent, not with a single blanket allow/deny — separate rules for Googlebot, Bingbot, GPTBot, ClaudeBot, CCBot, and generic crawlers.
34. Score >90 on Core Web Vitals; specifically watch **INP** (Interaction to Next Paint), which fully replaced FID as the responsiveness metric and is stricter under real-world conditions.
35. Use flat, human-readable URL slugs; strip tracking parameters from canonical/indexable URLs.
36. Serve WebP or AVIF for all raster images; keep total image payload per page under a defined budget (e.g., 500KB).
37. Server-render or statically pre-render core copy — anything gated behind client-side JS execution risks being missed by crawlers that don't fully execute JS (this includes some AI crawlers, which are more script-averse than Googlebot).
38. Run a 404 audit at least monthly and fix or redirect every broken internal link — a dead end mid-crawl truncates that page's context in a crawler's index.
39. Use `rel="canonical"` consistently to consolidate near-duplicate pages (print versions, tracked-parameter variants, staging leftovers) into one authoritative URL.
40. Enforce HTTPS sitewide with a valid, non-expiring-soon SSL cert; redirect all HTTP traffic with a single 301, not a chain.
41. Test responsive layout at real breakpoints (not just browser devtools presets) and ensure tap targets meet the 44×44px minimum.
42. Get Time to First Byte under ~200ms via a CDN/edge-first hosting setup — TTFB is now a meaningful ranking input, not just a UX nicety.
43. Set long-lived cache headers for static assets and use edge caching for HTML where content doesn't change per-request.
44. Minify and bundle CSS/JS; audit for unused JS shipped on pages that don't need it (a common self-inflicted wound in React-heavy sites).
45. Hardcode `width`/`height` (or `aspect-ratio`) on all images and embeds to eliminate layout shift.
46. If you localize content, use clean subfolder structure (`/es/`, `/fr/`) with proper `hreflang` tags rather than subdomains or query params.
47. Prune or `noindex` thin, outdated, or cannibalizing pages on a quarterly cadence — crawl budget on a small domain is a real constraint, not a myth reserved for enterprise sites.
48. Flatten unnecessarily deep DOM nesting; excessive `<div>` wrapping measurably slows both parser extraction and render.
49. Eliminate multi-hop redirect chains — collapse any A→B→C into a single A→C 301.
50. Keep the underlying framework/stack current (security patches, performance improvements ship faster on modern stacks) rather than freezing on an old version for stability alone.
51. Verify your site renders correctly with JavaScript disabled for at least the primary content — a fast manual gut-check for AI-crawler compatibility.
52. Confirm log-file crawl stats show Googlebot successfully rendering (not just fetching) your JS-dependent pages, via the URL Inspection tool's rendered-HTML view.
53. Set a `Last-Modified` HTTP header accurately, and don't fake it on unchanged content — some crawlers use it to decide whether re-fetching is worth the cost.
54. Paginate long listing pages properly (`rel="next"`/`rel="prev"` conventions are deprecated by Google but still useful for other bots and for UX) rather than infinite-scrolling content that never gets a stable URL.
55. Keep a staging environment fully `noindex`ed and password-gated so it never gets crawled and creates duplicate-content confusion.

---

## 🏷️ Pillar 3 — Rich Schema Markup & Semantic Data

56. Deploy `Organization` schema with legal name, logo, `sameAs` social/profile links, and contact points.
57. Deploy `SoftwareApplication` schema for any tool/product you ship, including version, OS support, and pricing.
58. Use `Product` schema (ratings, price, availability) on anything purchasable to remain eligible for rich results.
59. Use `FAQPage` schema for genuine FAQ content — matched precisely to on-page visible Q&A pairs, never invented purely for schema.
60. Add `VideoObject` schema (title, description, duration, upload date, thumbnail) to every embedded video.
61. Use `HowTo` schema for genuinely sequential technical setup instructions.
62. Use `Article`/`TechArticle` schema with accurate `datePublished`, `dateModified`, and `author` fields — and keep `dateModified` honest; don't bump it without a real content change.
63. Add `BreadcrumbList` schema matching your actual navigation hierarchy.
64. Connect `sameAs` entities to authoritative external profiles (GitHub, Crunchbase, Wikipedia/Wikidata where applicable, ORCID for research authorship).
65. Write literal, descriptive alt text for every chart/diagram/screenshot — this is now genuinely load-bearing for multimodal AI models parsing your visuals, not just an accessibility checkbox.
66. Add explicit `<caption>` or structured captions to statistical tables explaining what the table shows.
67. Build internal "anchor rings" — tight contextual linking between related child pages and their topical parent/pillar page.
68. Interlink schema types on a single page (e.g., `Person` author linked to `Organization` linked to `Article`) so relationships are machine-explicit, not just implied by proximity.
69. Keep JSON-LD syntactically valid — run it through a linter in CI, not just manually once at launch.
70. Validate all structured data with Google's Rich Results Test on every deploy that touches templates, not just at initial implementation.
71. Publish clean `<table>` markup for genuinely tabular data (benchmarks, comparisons, specs) — never fake a table with `<div>` grids, which both crawlers and screen readers parse worse.
72. Never let schema claim something the visible page doesn't show — mismatched hidden schema is treated as spam by Google and erodes AI-model trust in your entity over time.
73. Add internal `sitelinks searchbox` schema if you run a functional on-site search.
74. Link statistical/data claims directly to their primary source dataset rather than to a secondary article citing it.
75. Use predictable, stable heading `id` attributes (`#configuring-lora-rank`, not `#section-4`) so AI answers and external links can deep-link precisely and durably.
76. For research-adjacent content (your cybersecurity paper, SLM work), add `ScholarlyArticle` or `Dataset` schema where genuinely applicable — this is underused by small technical sites and is a real differentiator.
77. Mark up any benchmark results you publish with explicit units and methodology notes in both visible copy and structured data — ambiguous units (tokens/sec on what hardware?) get silently dropped or misquoted by summarizing models.
78. Keep a single machine-readable `CHANGELOG` or `Article` "dateModified" trail for any page describing a fast-moving technical area (model architectures, security landscape) — recency is a trust signal AI systems weight heavily on volatile topics.
79. Where you cite academic papers (arXiv, etc.), use consistent, resolvable citation formatting (arXiv ID, DOI) rather than just a link — this makes your citations themselves more extractable and verifiable.
80. Audit schema coverage sitewide quarterly — new page templates are the most common source of "we forgot schema on this type" gaps.

---

## ✍️ Pillar 4 — E-E-A-T & High-Value Content Strategy

81. Lead with firsthand experience: your own screenshots, your own benchmark runs, your own failure modes — not restated third-party findings.
82. Build topic clusters — a pillar page plus 5–10 genuinely deep supporting articles — rather than isolated one-off posts competing with each other for the same intent.
83. Maintain a visible, dated changelog of substantive site/content updates to signal active maintenance (a real freshness signal, distinct from a fake "last updated" timestamp bump).
84. Publish a real author bio with credentials, specialization, and a link to a canonical profile (GitHub, LinkedIn, ORCID) — anonymous or generic "admin" bylines are a measurable trust deduction for both classic E-E-A-T and AI-citation trust scoring.
85. Refresh pillar/cornerstone pages at minimum quarterly; on fast-moving technical topics (model architectures, security threats) monthly is more appropriate.
86. Avoid commoditized restatement — if a paragraph could have been written by summarizing three other articles without hands-on work, it's the first thing AI systems learn to deduplicate against, and the first thing a technical reader (like your own audience) discounts.
87. Go deep rather than broad on flagship pieces — long-form technical deep-dives with real methodology sections currently earn disproportionate citation volume relative to shorter surface-level posts.
88. Where relevant, include real practitioner or reviewer input (even informal — a peer review comment, a Discord discussion) rather than manufactured testimonials, which read as inauthentic in technical spaces.
89. Keep factual claims (benchmarks, capabilities, pricing) consistent across your site, your socials, and any press mentions — inconsistency across surfaces is a specific, checkable trust signal LLMs use when deciding whether to cite an entity.
90. Solve real, specific problems your actual audience has (informed by what people ask you directly) over chasing keyword-volume topics with no genuine expertise behind them.
91. Write in plain, direct language even for advanced technical topics — this helps both international readers and LLM parsing, and doesn't require dumbing down the substance.
92. Offer a downloadable, citable artifact (a whitepaper, a dataset, a benchmark methodology doc) for your deepest research pieces — these become the "primary source" other sites and AI systems link back to.
93. Publish your editorial/fact-checking process explicitly (even briefly) — a stated methodology is itself a trust signal, especially for security and ML research content where reproducibility matters.
94. Pair long-form text with a genuinely useful diagram or flowchart, not a decorative one — for architecture/security content this is often the single highest-leverage addition per hour spent.
95. Handle any client/employer work you reference by anonymizing specifics while keeping the technical substance detailed and verifiable — vague "a company" case studies without real detail read as fabricated.
96. Link out to primary sources generously (papers, official docs, upstream repos) — outbound linking to authoritative sources is a positive trust signal, not "leaking" authority, contrary to old SEO folklore.
97. Keep visual design clean and distraction-free — ad density and layout clutter are directly correlated with lower dwell time and lower perceived trustworthiness in both human and automated evaluation.
98. Write for semantic relevance and natural entity coverage, not keyword density — density-based optimization is actively counterproductive against modern ranking and citation systems.
99. Put the direct answer to the page's core question in the first ~150 words, above the fold, before any scene-setting — this is the single highest-value habit for AI Overview eligibility on informational queries.
100. When you cover a genuinely contested or unsettled technical question (e.g., whether MoE is worth it below 1B params), state your position *and* the counter-position explicitly — pages that acknowledge tradeoffs get cited more often for nuanced AI answers than ones that assert a single confident take.
101. For any claim sourced from a paper, correctly attribute the paper (authors, year) inline, not just in a bibliography — this is both good practice and improves how confidently an LLM will attribute the claim back to you rather than to the underlying paper.
102. Disclose your own uncertainty or the limits of your testing explicitly ("tested on a single 4090, not validated at scale") — over-claiming is increasingly penalized as models get better at detecting unsupported generalization.
103. Avoid AI-generated filler content entirely on pages meant to demonstrate expertise — detectable low-effort AI text is now actively down-weighted, and undermines exactly the trust signal E-E-A-T exists to measure.
104. Build a genuine internal "about the author's methodology" page once you have enough research output (SLM work, security paper) to justify it — this becomes a durable trust anchor other pages can link to.

---

## 📈 Pillar 5 — Off-Page Authority, PR & Brand Equity

105. Pursue placement on legitimate "best of" / roundup lists in your specific technical niche (AI security tooling roundups, local-LLM tooling lists).
106. Claim and complete profiles on relevant directories (GitHub org profile, Crunchbase if applicable, relevant dev-tool directories) — completeness itself is a trust/entity signal.
107. Distribute genuine milestone announcements (paper published, tool released) through channels your actual audience already reads, not generic PR-wire spam.
108. Earn backlinks contextually from domains with real topical relevance (security research blogs, ML engineering blogs) over high-DA but irrelevant sites.
109. Participate authentically in relevant subreddits and dev forums (r/LocalLLaMA, r/MachineLearning, relevant Discords) — genuine participation, not drive-by self-promotion, which communities and algorithms both penalize.
110. If pursuing international reach, create genuinely localized (not machine-translated) content for specific underserved-language technical audiences — this remains comparatively low-competition.
111. Open-source a starter kit, reference implementation, or tool related to your work (very natural for you given the from-scratch RAG pipeline and SLM work) and host it on GitHub with a clear README linking back to your site.
112. Track brand-mention growth over time (even manually via periodic search) as a leading indicator before it shows up in citation-rate metrics.
113. Run or contribute to an active community channel (Discord/Slack) around your specific niche if you want compounding organic word-of-mouth.
114. Pursue podcast or talk appearances in your specific technical niche — these produce durable backlinks and citable transcripts that AI crawlers index.
115. Co-author or contribute technical review to work by other credible voices in AI security/local-LLM space where genuinely warranted — collaboration signals are increasingly used as authority proxies.
116. Audit your backlink profile periodically and disavow clearly toxic/spam links, without over-reacting to every low-quality link (most have negligible impact).
117. Build reviews/social proof on relevant platforms only where genuinely applicable to your work (less relevant for a personal research blog than for a SaaS product — don't force this one).
118. Publish original research or survey data on a topic your audience cares about (you're already positioned to do this via your security paper and SLM experiments) — this is the single highest-leverage backlink-earning content type available to a small technical site.
119. Contribute genuine guest commentary or technical takes to outlets that already have audience trust in your niche, rather than mass-pitching irrelevant publications.
120. Design at least one genuinely shareable technical diagram per major piece (architecture diagrams, threat-model diagrams) that others would want to embed with attribution.
121. Build a direct email list from your most engaged readers — this is your only fully-owned channel as AI answers absorb more top-of-funnel search traffic.
122. Prioritize long-term recognizable brand/entity building over any single tactic — Google and AI systems increasingly favor entities with a consistent, verifiable track record over anonymous or inconsistent ones.

---

## 🤖 Pillar 6 (NEW) — AI Citation Tracking, Preferred Sources & the New Measurement Layer

123. Enable and monitor Google's Search Generative AI performance report in Search Console as soon as it reaches your account — it's currently the only first-party data source for AI Overview/AI Mode impressions.
124. Understand its current limits: it shows impressions only, broken down by page/country/device/date — no click data yet. Don't over-interpret impression spikes as traffic wins.
125. Establish a baseline the day you get access: record total AI impressions and what share they represent of total Search impressions — this ratio is the most useful single number the report currently gives you.
126. Sort the by-page view to identify your "AI workhorse" pages — the ones AI features lean on most — and treat them as protected assets: keep them fresher and more rigorously fact-checked than average content.
127. Deliberately decide whether to enable the AI-features opt-out toggle per property — understand it removes you from AI Overviews/AI Mode/AI Discover without affecting classic organic rank, which is a genuinely new lever, not previously available.
128. Distinguish the three separate controls that are commonly conflated: `Google-Extended` (blocks AI model training, not AI Overviews), `nosnippet` (blocks AI features but also strips your classic snippet), and the new GSC toggle (blocks AI features only, no snippet tradeoff). Pick the right one deliberately per page.
129. Prompt your actual returning audience (newsletter, socials) to add you as a Preferred Source using Google's provided instructions/button — this doesn't change ranking directly but raises your odds of being surfaced in AI answers for people who've already chosen you.
130. In Search Console's standard performance report, filter by query type and watch for the specific signature of AI-Overview cannibalization: informational-query clicks falling while branded/transactional queries hold steady. Don't confuse this with a core-update penalty — the fixes differ.
131. Track citation rate manually where you lack paid tooling: periodically run your top 10–20 target questions through Google AI Mode, ChatGPT (with browsing), and Perplexity, and log whether/where you're cited.
132. Recognize that AI Overview and AI Mode citations overlap only partially (roughly 1 in 7 URLs cited in one also appear in the other) — optimizing for one doesn't automatically win the other; treat them as related but distinct surfaces.
133. Separately track visibility across the non-Google surfaces that matter for your audience (ChatGPT, Perplexity, and Claude, given your own technical readership likely uses these) using their respective citation/source-attribution behavior, since Google's tools obviously won't cover them.
134. Set a recurring calendar reminder (monthly is reasonable at your scale) to re-run the citation-rate spot-check — this space is moving fast enough that quarterly is too slow.
135. When AI-attributed impressions rise but clicks stay flat or fall, treat that as brand-awareness value, not failure — but don't let it replace tracking of the metrics that actually pay the bills (email signups, direct traffic, backlinks).

---

## 🧩 Pillar 7 (NEW) — Page-Type & Subpage Playbooks

Different page types need different treatment. Apply the pillar-level rules above everywhere, plus these specifics.

### Homepage
136. State what the site/entity is in one literal sentence in the first 100 words — no metaphor, no "welcome to."
137. Link prominently to your 3–5 highest-authority pillar pages, not just recent posts.
138. Include `Organization`/`Person` schema here specifically, since it's the canonical entity-anchor page crawlers use to resolve "who is this."
139. Keep load time exceptionally fast here — it's disproportionately crawled and disproportionately abandoned if slow.
140. Avoid burying the actual navigation under decorative hero content.

### Blog / Article Pages
141. Answer the headline's implied question in the first paragraph before any narrative setup.
142. Use `Article` schema with accurate `datePublished`/`dateModified` — never silently backdate or fake freshness.
143. Add a 2–3 sentence TL;DR/summary block near the top — this is disproportionately what gets lifted into AI answers.
144. Include a real author byline linked to a bio page, every time, no exceptions.
145. End with genuinely related internal links (2–4), not auto-generated unrelated "related posts."
146. For technical deep-dives specifically (your natural format), include a table of contents with anchored headings for both UX and AI deep-linking.
147. Where you present a tradeoff or contested take (MoE vs. dense, GQA vs. MLA at small scale), format it as an explicit comparison block, not buried in prose — this is your single best-fit content type for GEO given your existing writing.

### Product / Tool / Service Pages
148. Lead with the concrete problem solved and for whom, not a feature list.
149. Use `Product`/`SoftwareApplication` schema with accurate, current version/pricing data.
150. Keep these pages excluded from heavy GEO-only optimization effort — Google is deliberately keeping AI Overviews rare on commercial/product queries (~4% trigger rate) to preserve click-through; invest GEO effort in adjacent informational content that funnels here instead.
151. Include genuine screenshots or output examples, not stock imagery.
152. Add a clear, singular CTA — atomic-page principle applies doubly here.

### Comparison / "Alternative to X" Pages
153. Build an explicit, factual comparison table as the centerpiece, not prose-only.
154. State clearly which use cases favor each option — a page that's honest about tradeoffs earns more AI citations for nuanced queries than a one-sided pitch.
155. Keep the comparison criteria consistent and labeled the same way across all your comparison pages sitewide, so they read as a coherent internal dataset, not one-offs.
156. Date-stamp comparisons explicitly and commit to revisiting them — comparative claims about fast-moving tools/models go stale faster than almost any other content type on a technical site.

### Documentation / API Reference / Technical How-To Pages
157. Use `HowTo` schema for genuinely sequential setup content.
158. Number steps explicitly and keep one action per step — don't bundle multiple actions into one numbered item.
159. Place a working code example immediately after each conceptual explanation, never in a separate appendix.
160. Version-label instructions clearly ("as of vX.Y") since AI systems have no reliable way to know your docs have since changed unless you say so on-page.
161. Keep a single canonical docs URL per topic — duplicate docs across a blog post and a docs page split your authority and confuse crawlers about which is current.

### FAQ Pages
162. Use real questions actually asked by your audience — never invent FAQ entries purely to farm `FAQPage` schema, which Google now actively discounts when detected as synthetic.
163. Keep each answer genuinely self-contained (Island Test again) since FAQ answers are the content type most frequently lifted verbatim into AI answers.
164. Match visible on-page text exactly to the schema markup — no hidden or reworded answers in the JSON-LD.

### Category / Listing / Index Pages
165. Write a genuine, non-boilerplate intro paragraph per category — thin "browse our X" text with no unique content is a recurring source of index bloat and crawl-budget waste.
166. Use `BreadcrumbList` schema and consistent pagination handling.
167. `noindex` any listing variant produced purely by filter/sort parameters, keeping only the canonical unfiltered view indexable.

### Local / Location-Specific Pages (if ever applicable)
168. One page per genuinely distinct location — never a templated page swapping only a city name with no unique local content.
169. Include accurate, consistent NAP (name, address, phone) data matching your Google Business Profile exactly.
170. Use `LocalBusiness` schema with correct geo-coordinates.

---

## 🛠️ Pillar 8 (NEW) — Governance, Cadence & Team Process

171. Maintain a single content calendar that tracks not just publish dates but next-review dates per pillar page.
172. Run a technical SEO audit (crawl errors, Core Web Vitals, schema validity) monthly at minimum; weekly if you're actively shipping new page templates.
173. Run the citation-rate spot-check (Pillar 6) monthly.
174. Keep a living style guide enforcing consistent terminology (Pillar 1, #10) so it survives beyond your own memory of past decisions.
175. Review `robots.txt` and crawler-access rules quarterly — new AI crawlers appear often enough that a "set once" policy silently goes stale.
176. Log every algorithm-update-adjacent traffic anomaly (date, magnitude, affected query types) so you can distinguish a core update effect from an AI-Overview cannibalization effect from a genuine content problem, months later, using your own historical log rather than memory.
177. Treat schema, sitemap, and canonical-tag correctness as CI-checked invariants on any site rebuild, not manual one-time tasks.
178. Revisit the opt-out-of-AI-features decision (Pillar 6, #127) at least twice a year as Google's AI-feature click data becomes available and the tradeoff becomes measurable rather than theoretical.

---

## Honest closing note

This list is deliberately not padded to a round number. A handful of items here matter far more than the rest for a site like yours specifically:

- **#20, #25, #147, #153–156** (comparison-format content) — your natural writing mode already fits the format that currently earns the most AI citations for nuanced technical questions.
- **#118** (original research/benchmark data) — you're already sitting on genuinely original work (the SLM architecture research, the security paper) that's rarer and more citable than 95% of "SEO content."
- **#123–135** (the new measurement layer) — worth setting up now so you have a real baseline instead of guessing later.

If you want, I can turn this into a 90-day implementation calendar sequenced specifically around your current priorities (SLM research publishing cadence + the security paper), rather than a generic rollout order.
