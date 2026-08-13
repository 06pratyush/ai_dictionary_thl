#!/usr/bin/env python3
"""Generate the dictionary's static output.

Produces, from the two JSON corpora:
  terms/<slug>.html      one crawlable page per entry (RULE-03)
  data/search-index.json the client-side search index (Rules 710-712)
  sitemap.xml            every term page plus the hub

Nothing here ships to the browser; this runs at build time only. The corpora
are the single source of truth — never hand-edit anything this writes.

Usage:
    python build/build.py
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validate import CORPORA, main as validate_main  # noqa: E402

SITE = "https://thehallucinatedlab.space"
BASE = f"{SITE}/dictionary"
OG_IMAGE = f"{SITE}/assets/images/logo.jpeg"

NAV_ITEMS = [
    ("Home", "/", False),
    ("Tools", "/tools.html", False),
    ("Assistant", "/assistant.html", False),
    ("Solutions", "/solutions.html", False),
    ("Media", "/media.html", False),
    ("Dictionary", "/dictionary/", True),
    ("Certification", "/certification.html", False),
    ("Consultancy", "/consultancy.html", False),
]


def e(value):
    """Escape for HTML text and attribute contexts."""
    return html.escape(str(value if value is not None else ""), quote=True)


def nav_html(depth):
    """depth 0 = /dictionary/index.html, depth 1 = /dictionary/terms/x.html"""
    up = "../" * depth
    items = []
    for label, href, active in NAV_ITEMS:
        target = f"{up}index.html" if active else f"{SITE}{href}"
        current = ' aria-current="page"' if active else ""
        items.append(f'<li><a href="{e(target)}"{current}>{e(label)}</a></li>')
    return f"""<header>
  <nav class="navbar" aria-label="Primary">
    <div class="nav-inner">
      <a class="nav-logo" href="{SITE}/">
        <img src="{OG_IMAGE}" alt="The Hallucinated Lab logo" width="36" height="36">
        <span class="nav-wordmark">THE HALLUCINATED LAB</span>
      </a>
      <button class="nav-toggle" type="button" aria-expanded="false"
              aria-controls="nav-links" aria-label="Toggle navigation">
        <span></span><span></span><span></span>
      </button>
      <ul class="nav-links" id="nav-links">
        {"".join(items)}
      </ul>
    </div>
  </nav>
</header>"""


FOOTER = """<footer class="site-footer">
  <p>&copy; 2026 The Hallucinated Lab. Built with curiosity and caffeine.
  <a href="{site}/">Return to the lab</a>.</p>
</footer>"""


def head_html(*, title, description, canonical, depth, extra_ld=""):
    up = "../" * depth
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:site_name" content="The Hallucinated Lab">
<meta property="og:locale" content="en_US">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The Hallucinated Lab">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(description)}">
<meta name="twitter:image" content="{OG_IMAGE}">
<link rel="icon" href="{OG_IMAGE}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;600&display=swap">
<link rel="stylesheet" href="{up}assets/css/tokens.css">
<link rel="stylesheet" href="{up}assets/css/dictionary.css">
{extra_ld}"""


# ---------------------------------------------------------------- term page


def definitions_html(entry):
    parts = []
    for definition in entry["definitions"]:
        context = definition.get("context")
        context_html = (f'<span class="definition-context">[{e(context)}] </span>'
                        if context else "")
        parts.append(f"""<div class="definition">
  <p><span class="definition-number">{e(definition['id'])}.</span>{context_html}<span class="definition-text">{e(definition['text'])}</span></p>
  <p class="definition-example">{e(definition['example'])}</p>
</div>""")
    return "\n".join(parts)


def formula_html(entry):
    formula = entry.get("formula")
    if not formula:
        return ""
    note = (f'<p class="formula-note">{e(formula["note"])}</p>'
            if formula.get("note") else "")
    return f"""<section class="term-section">
  <h2>Formal statement</h2>
  <div class="formula-block"><code>{e(formula.get('plain') or formula.get('latex'))}</code></div>
  {note}
</section>"""


def relations_html(entry, index):
    """Synonyms, antonyms and cross-references. Rules 521-525, 604."""
    blocks = []

    if entry.get("synonyms"):
        items = "".join(
            f'<li><span class="relation-chip">{e(s["term"])}'
            f'<span class="relation-tag">sense {e(s["senseId"])} · {e(s["proximity"])}</span>'
            f"</span></li>"
            for s in entry["synonyms"])
        blocks.append(f'<section class="term-section"><h2>Synonyms</h2>'
                      f'<ul class="relation-list">{items}</ul></section>')

    if entry.get("antonyms"):
        items = "".join(
            f'<li><span class="relation-chip">{e(a["term"])}'
            f'<span class="relation-tag">sense {e(a["senseId"])} · {e(a["polarity"])}</span>'
            f"</span></li>"
            for a in entry["antonyms"])
        blocks.append(f'<section class="term-section"><h2>Antonyms</h2>'
                      f'<ul class="relation-list">{items}</ul></section>')

    # Only link cross-references that actually resolve, so no page ships a 404.
    live = [slug for slug in entry.get("related") or [] if slug in index]
    if live:
        items = "".join(
            f'<li><a href="{e(slug)}.html">{e(index[slug]["term"])}</a></li>'
            for slug in live)
        blocks.append(f'<section class="term-section"><h2>See also</h2>'
                      f'<ul class="relation-list">{items}</ul></section>')

    return "\n".join(blocks)


def citations_html(entry):
    items = []
    for citation in entry.get("citations") or []:
        label = e(citation["label"])
        if citation.get("url"):
            label = f'<a href="{e(citation["url"])}" rel="noopener">{label}</a>'
        source = (f'<span class="citation-source">{e(citation["source"])}</span>'
                  if citation.get("source") else "")
        items.append(f"<li>{label}{source}</li>")
    return f"""<section class="term-section">
  <h2>References</h2>
  <ul class="citation-list">{"".join(items)}</ul>
</section>"""


def aside_html(entry, section):
    rows = [
        ("Lexical ID", entry["lid"]),
        ("Section", section["title"]),
        ("Domain", entry["domain"]),
        ("Part of speech", entry["pos"]),
        ("Form", entry["ngram"]),
    ]
    if entry.get("firstAttested"):
        rows.append(("First attested", entry["firstAttested"]))
    if entry.get("abbr"):
        rows.append(("Also written", ", ".join(entry["abbr"])))
    if entry.get("variants"):
        rows.append(("Variants", ", ".join(entry["variants"])))
    if entry.get("inflections"):
        rows.append(("Inflections", ", ".join(entry["inflections"])))
    if entry.get("opacity"):
        rows.append(("Opacity", f"{entry['opacity']} of 3"))
    body = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in rows)
    return f'<aside class="term-aside"><h2>Entry data</h2><dl>{body}</dl></aside>'


def jsonld_term(entry, section, canonical):
    """DefinedTerm inside a DefinedTermSet, plus the breadcrumb trail."""
    graph = [
        {
            "@type": "DefinedTerm",
            "@id": f"{canonical}#term",
            "name": entry["term"],
            "description": entry["definitions"][0]["text"],
            "termCode": entry["lid"],
            "inDefinedTermSet": {
                "@type": "DefinedTermSet",
                "@id": f"{BASE}/#{section['id']}",
                "name": section["title"],
                "url": f"{BASE}/#{section['id']}",
            },
            "url": canonical,
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
                {"@type": "ListItem", "position": 2, "name": "Dictionary", "item": f"{BASE}/"},
                {"@type": "ListItem", "position": 3, "name": section["title"],
                 "item": f"{BASE}/#{section['id']}"},
                {"@type": "ListItem", "position": 4, "name": entry["term"], "item": canonical},
            ],
        },
    ]
    payload = json.dumps({"@context": "https://schema.org", "@graph": graph},
                         ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{payload}\n</script>'


def term_page(entry, section, index, prev_entry, next_entry):
    canonical = f"{BASE}/terms/{entry['slug']}.html"
    gloss = entry["definitions"][0]["text"]
    description = f"{entry['term']} ({entry['pos']}, {entry['domain']}) — {gloss}"[:300]

    phonetics = []
    if entry.get("ipa"):
        phonetics.append(f'<span class="term-ipa">{e(entry["ipa"])}</span>')
    if entry.get("syllables"):
        phonetics.append(f"<span>{e(entry['syllables'])}</span>")
    phonetics.append(f'<span class="term-pos">{e(entry["pos"])}</span>')

    badges = [f'<span class="badge">{e(tag)}</span>' for tag in entry.get("tags") or []]
    badges += [f'<span class="badge">{e(flag)}</span>' for flag in entry.get("flags") or []]

    etymology = f"""<section class="term-section">
  <h2>Etymology</h2>
  <p class="etymology-text">{e(entry['etymology'])}</p>
</section>"""

    nav_links = []
    if prev_entry:
        nav_links.append(f'<a href="{e(prev_entry["slug"])}.html">'
                         f'<span class="term-nav-label">Previous</span>'
                         f'{e(prev_entry["term"])}</a>')
    if next_entry:
        nav_links.append(f'<a href="{e(next_entry["slug"])}.html" style="text-align:right">'
                         f'<span class="term-nav-label">Next</span>'
                         f'{e(next_entry["term"])}</a>')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_html(title=f"{entry['term']} — The Hallucinated Lab Dictionary",
           description=description, canonical=canonical, depth=1,
           extra_ld=jsonld_term(entry, section, canonical))}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{nav_html(1)}
<main id="main">
  <article class="term-page">
    <div>
      <header class="term-hero">
        <p class="page-breadcrumb">
          <a href="../index.html">Dictionary</a> /
          <a href="../index.html#{e(section['id'])}">{e(section['title'])}</a>
        </p>
        <h1>{e(entry['term'])}</h1>
        <div class="term-phonetics">{"".join(phonetics)}</div>
        <div class="term-meta-row">
          <span class="badge">{e(entry['domain'])}</span>
          {"".join(badges)}
        </div>
      </header>

      <section class="term-section">
        <h2>Definition</h2>
        {definitions_html(entry)}
      </section>

      {formula_html(entry)}
      {etymology}
      {relations_html(entry, index)}
      {citations_html(entry)}

      <nav class="term-nav" aria-label="Adjacent entries">{"".join(nav_links)}</nav>
    </div>
    {aside_html(entry, section)}
  </article>
</main>
{FOOTER.format(site=SITE)}
<script src="../assets/js/nav.js" type="module"></script>
</body>
</html>
"""


# ---------------------------------------------------------------- hub page


def entry_card(entry, href_prefix="terms/"):
    tags = "".join(f'<span class="badge">{e(t)}</span>'
                   for t in (entry.get("tags") or [])[:2])
    return f"""<a class="entry-card" href="{href_prefix}{e(entry['slug'])}.html">
  <div class="entry-card-top">
    <span class="entry-card-domain">{e(entry['domain'])}</span>
    <span class="entry-card-lid">{e(entry['lid'])}</span>
  </div>
  <h3>{e(entry['term'])}</h3>
  <span class="entry-card-pos">{e(entry['pos'])}</span>
  <p class="entry-card-gloss">{e(entry['definitions'][0]['text'])}</p>
  <div class="entry-card-tags">{tags}</div>
</a>"""


def alpha_nav(entries):
    """Rule 604-adjacent: a jump strip so browsing does not depend on search."""
    present = {entry["term"][0].upper() for entry in entries}
    cells = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if letter in present:
            cells.append(f'<a href="#letter-{letter}">{letter}</a>')
        else:
            cells.append(f"<span>{letter}</span>")
    return f'<nav class="alpha-nav" aria-label="Jump to letter">{"".join(cells)}</nav>'


def section_html(corpus, alt):
    section = corpus["section"]
    entries = corpus["entries"]
    cards = []
    seen_letters = set()
    for entry in entries:
        letter = entry["term"][0].upper()
        anchor = ""
        if letter not in seen_letters:
            seen_letters.add(letter)
            anchor = f'<span id="letter-{letter}"></span>'
        cards.append(anchor + entry_card(entry))

    return f"""<section class="section{' section-alt' if alt else ''}" id="{e(section['id'])}">
  <div class="container">
    <div class="corpus-head">
      <div>
        <span class="section-label">{e(section['label'])}</span>
        <h2 class="section-title">{e(section['title'])}</h2>
        <div class="section-line"></div>
        <p class="section-intro">{e(section['description'])}</p>
      </div>
      <span class="results-count">{len(entries)} entries</span>
    </div>
    {alpha_nav(entries)}
    <div class="corpus-grid">
      {"".join(cards)}
    </div>
  </div>
</section>"""


def jsonld_hub(corpora, total):
    sets = [{
        "@type": "DefinedTermSet",
        "@id": f"{BASE}/#{c['section']['id']}",
        "name": c["section"]["title"],
        "description": c["section"]["description"],
        "url": f"{BASE}/#{c['section']['id']}",
        "hasDefinedTerm": [
            {"@type": "DefinedTerm", "name": entry["term"],
             "termCode": entry["lid"],
             "url": f"{BASE}/terms/{entry['slug']}.html"}
            for entry in c["entries"]
        ],
    } for c in corpora]

    graph = sets + [
        {
            "@type": "CollectionPage",
            "@id": f"{BASE}/#page",
            "name": "The Hallucinated Lab Dictionary",
            "description": (f"A {total}-entry reference covering AI, mathematics "
                            "and software engineering."),
            "url": f"{BASE}/",
            "isPartOf": {"@id": f"{SITE}/#website"},
            "hasPart": [{"@id": s["@id"]} for s in sets],
        },
        {
            "@type": "WebSite",
            "@id": f"{SITE}/#website",
            "url": f"{SITE}/",
            "name": "The Hallucinated Lab",
            "potentialAction": {
                "@type": "SearchAction",
                "target": {"@type": "EntryPoint",
                           "urlTemplate": f"{BASE}/?q={{search_term_string}}"},
                "query-input": "required name=search_term_string",
            },
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
                {"@type": "ListItem", "position": 2, "name": "Dictionary", "item": f"{BASE}/"},
            ],
        },
    ]
    payload = json.dumps({"@context": "https://schema.org", "@graph": graph},
                         ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{payload}\n</script>'


def hub_page(corpora):
    template_path = os.path.join(ROOT, "build", "templates", "index.html")
    with open(template_path, encoding="utf-8") as fh:
        template = fh.read()

    total = sum(len(c["entries"]) for c in corpora)
    stats = "".join(
        f'<span class="badge">{len(c["entries"])} {e(c["section"]["title"])}</span>'
        for c in corpora)
    stats += f'<span class="badge">{total} entries total</span>'

    sections = "\n".join(section_html(c, alt=i % 2 == 1)
                         for i, c in enumerate(corpora))

    return (template
            .replace("{{HEAD}}", head_html(
                title="Dictionary — The Hallucinated Lab",
                description=("A searchable reference for AI, mathematics and software "
                             "engineering. Two corpora, one search, one page per term."),
                canonical=f"{BASE}/", depth=0,
                extra_ld=jsonld_hub(corpora, total)))
            .replace("{{NAV}}", nav_html(0))
            .replace("{{STATS}}", stats)
            .replace("{{SECTIONS}}", sections)
            .replace("{{FOOTER}}", FOOTER.format(site=SITE)))


# ---------------------------------------------------------------- index


def build_search_index(corpora):
    """Rules 710-712. Flattened, render-ready, and small enough to ship whole."""
    entries = []
    for corpus in corpora:
        section_id = corpus["section"]["id"]
        for entry in corpus["entries"]:
            entries.append({
                "lid": entry["lid"],
                "term": entry["term"],
                "slug": entry["slug"],
                "section": section_id,
                "domain": entry["domain"],
                "pos": entry["pos"],
                "ngram": entry["ngram"],
                "tags": entry.get("tags") or [],
                "flags": entry.get("flags") or [],
                "abbr": entry.get("abbr") or [],
                "inflections": entry.get("inflections") or [],
                "variants": entry.get("variants") or [],
                "synonyms": [s["term"] for s in entry.get("synonyms") or []],
                "gloss": entry["definitions"][0]["text"],
                "defText": " ".join(d["text"] for d in entry["definitions"]),
                "frequency": entry.get("frequency", 0),
            })
    return {
        "version": 1,
        "sections": {c["section"]["id"]: c["section"] for c in corpora},
        "entries": entries,
    }


def sitemap(corpora):
    urls = [f"{BASE}/"]
    for corpus in corpora:
        for entry in corpus["entries"]:
            urls.append(f"{BASE}/terms/{entry['slug']}.html")
    body = "".join(
        f"  <url><loc>{e(url)}</loc><changefreq>monthly</changefreq></url>\n"
        for url in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{body}</urlset>\n")


def derive(entry):
    """Fields the build owns — authored values are overwritten, never trusted."""
    words = re.split(r"[\s‐-―-]+", entry["term"].strip())
    count = len([w for w in words if w])
    entry["ngram"] = "unigram" if count == 1 else "bigram" if count == 2 else "polygram"
    return entry


def main():
    if validate_main([]) != 0:
        print("\nbuild aborted: corpus validation failed", file=sys.stderr)
        return 1

    corpora = []
    for path in CORPORA:
        with open(path, encoding="utf-8") as fh:
            corpus = json.load(fh)
        corpus["entries"].sort(key=lambda x: x["term"].lower())
        for entry in corpus["entries"]:
            derive(entry)
        corpora.append(corpus)

    index = {entry["slug"]: entry
             for corpus in corpora for entry in corpus["entries"]}

    terms_dir = os.path.join(ROOT, "terms")
    os.makedirs(terms_dir, exist_ok=True)
    written = 0

    for corpus in corpora:
        entries = corpus["entries"]
        for i, entry in enumerate(entries):
            page = term_page(
                entry, corpus["section"], index,
                entries[i - 1] if i > 0 else None,
                entries[i + 1] if i + 1 < len(entries) else None,
            )
            with open(os.path.join(terms_dir, f"{entry['slug']}.html"),
                      "w", encoding="utf-8", newline="\n") as fh:
                fh.write(page)
            written += 1

    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(hub_page(corpora))

    with open(os.path.join(ROOT, "data", "search-index.json"),
              "w", encoding="utf-8", newline="\n") as fh:
        json.dump(build_search_index(corpora), fh, ensure_ascii=False, indent=1)

    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sitemap(corpora))

    print(f"built {written} term pages, hub page, search index, sitemap")
    return 0


if __name__ == "__main__":
    sys.exit(main())
