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



def relations_html(entry, index):
    """Synonyms, antonyms and cross-references. Rules 521-525, 604.

    Rendered as h3 subsections: topic_sections() already owns the h2 for
    'Variants & Related Concepts', and the site forbids skipped heading levels.
    """
    blocks = []

    if entry.get("synonyms"):
        items = "".join(
            f'<li><span class="relation-chip">{e(s["term"])}'
            f'<span class="relation-tag">sense {e(s["senseId"])} · {e(s["proximity"])}</span>'
            f"</span></li>"
            for s in entry["synonyms"])
        blocks.append(f'<div class="relation-block"><h3>Synonyms</h3>'
                      f'<ul class="relation-list">{items}</ul></div>')

    if entry.get("antonyms"):
        items = "".join(
            f'<li><span class="relation-chip">{e(a["term"])}'
            f'<span class="relation-tag">sense {e(a["senseId"])} · {e(a["polarity"])}</span>'
            f"</span></li>"
            for a in entry["antonyms"])
        blocks.append(f'<div class="relation-block"><h3>Antonyms</h3>'
                      f'<ul class="relation-list">{items}</ul></div>')

    # Only link cross-references that actually resolve, so no page ships a 404.
    live = [slug for slug in entry.get("related") or [] if slug in index]
    if live:
        items = "".join(
            f'<li><a href="{e(slug)}.html">{e(index[slug]["term"])}</a></li>'
            for slug in live)
        blocks.append(f'<div class="relation-block"><h3>See also</h3>'
                      f'<ul class="relation-list">{items}</ul></div>')

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
    return f'<ul class="citation-list">{"".join(items)}</ul>' if items else ""


#
# Every term page renders the sections of docs/TOPIC-PAGE-SPEC.md, in the
# spec's order, under the spec's HTML ids. `topic_sections()` is the single
# source of truth for that order: the body and the on-page contents list are
# both built from what it returns, so the two can never disagree.
#
# Sections the spec marks Required but that a legacy entry cannot honestly
# supply are omitted rather than filled with filler. Two of them — Quick Take
# and Final Formal Statement — are derivable from the entry's own first sense
# without inventing anything, so those are derived and marked
# data-derived="true". The rest are the author's job, and validate.py demands
# them from every entry that is not on the legacy migration allowlist.


def topic(entry):
    """The topic block, or an empty dict for an entry that predates the spec."""
    return entry.get("topic") or {}


def paragraphs_html(values):
    return "".join(f"<p>{e(value)}</p>" for value in values if value)


def derived_quick_take(entry):
    """Rule 501 makes definition 1 substitutable, so 'Term is <sense>.' is a
    faithful plain-English restatement — not a new claim about the term."""
    gloss = entry["definitions"][0]["text"].rstrip(".")
    return f"{entry['term']} is {gloss}."


def derived_formal_statement(entry):
    gloss = entry["definitions"][0]["text"].rstrip(".")
    return f"{entry['term']} ({entry['pos']}, {entry['domain']}): {gloss}."


def quick_take_html(entry):
    """Spec §1."""
    authored = topic(entry).get("quickTake")
    text = authored or derived_quick_take(entry)
    flag = "" if authored else ' data-derived="true"'
    return f'<p class="quick-take"{flag}>{e(text)}</p>'


def formal_definitions_html(entry):
    """Spec §2. Attributed blockquotes where sources back them, the entry's own
    senses otherwise — never a quote the corpus cannot stand behind."""
    sourced = topic(entry).get("formalDefinitions") or []
    if not sourced:
        return definitions_html(entry)
    blocks = []
    for definition in sourced[:3]:
        bits = [b for b in (definition.get("author"), definition.get("year")) if b]
        marker = (f' <a class="ref-marker" href="#references">[{e(definition["ref"])}]</a>'
                  if definition.get("ref") else "")
        cite = (f'<cite class="definition-attribution">{e(" , ".join(bits).replace(" , ", ", "))}'
                f"</cite>{marker}" if bits else marker)
        blocks.append(f'<blockquote class="formal-definition">'
                      f'<p>{e(definition["quote"])}</p>{cite}</blockquote>')
    return "".join(blocks)


def formal_statement_html(entry):
    """Spec §3."""
    authored = topic(entry).get("formalStatement")
    text = authored or derived_formal_statement(entry)
    flag = "" if authored else ' data-derived="true"'
    return f'<p class="formal-statement"{flag}>{e(text)}</p>'


def etymology_html(entry):
    """Spec §4."""
    parts = [f'<p class="etymology-text">{e(entry["etymology"])}</p>']
    if entry.get("firstAttested"):
        parts.append(f'<p class="etymology-attested">First attested '
                     f'{e(entry["firstAttested"])}.</p>')
    return "".join(parts)


def prerequisites_html(entry, index):
    """Spec §6. A prerequisite links only where the target page exists, so the
    knowledge graph never points at a 404."""
    items = []
    for prerequisite in topic(entry).get("prerequisites") or []:
        label = e(prerequisite.get("label") or prerequisite.get("slug", ""))
        slug = prerequisite.get("slug")
        items.append(f'<li><a href="{e(slug)}.html">{label}</a></li>'
                     if slug in index else f"<li>{label}</li>")
    return f'<ul class="prerequisite-list">{"".join(items)}</ul>' if items else ""


def videos_html(videos):
    """Spec §7. Linked, never embedded — an iframe would need a third-party
    frame-src and the CSP does not carry one."""
    items = []
    for video in videos:
        why = f'<span class="video-why">{e(video["why"])}</span>' if video.get("why") else ""
        creator = (f'<span class="video-creator">{e(video["creator"])}</span>'
                   if video.get("creator") else "")
        items.append(f'<li><a href="{e(video["url"])}" rel="noopener">'
                     f'{e(video["title"])}</a>{creator}{why}</li>')
    return (f'<div class="video-list"><h3>Watch</h3><ul>{"".join(items)}</ul></div>'
            if items else "")


def deep_dive_html(entry):
    """Spec §7. Folds the lexical `formula` block in as the formalism, so an
    entry that carries one never has to restate it in prose."""
    dive = topic(entry).get("deepDive") or {}
    parts = [paragraphs_html(dive.get("paragraphs") or [])]

    formula = entry.get("formula")
    if formula:
        note = (f'<p class="formula-note">{e(formula["note"])}</p>'
                if formula.get("note") else "")
        parts.append(f'<div class="formula-block">'
                     f'<code>{e(formula.get("plain") or formula.get("latex"))}</code></div>{note}')

    steps = dive.get("steps") or []
    if steps:
        items = "".join(f"<li>{e(step)}</li>" for step in steps)
        parts.append(f'<ol class="derivation-steps">{items}</ol>')

    parts.append(videos_html(dive.get("videos") or []))
    return "".join(part for part in parts if part)


def worked_example_html(entry):
    """Spec §8."""
    example = topic(entry).get("workedExample") or {}
    steps = example.get("steps") or []
    if not (example.get("intro") or steps):
        return ""
    intro = f'<p>{e(example["intro"])}</p>' if example.get("intro") else ""
    items = "".join(f"<li>{e(step)}</li>" for step in steps)
    body = f'<ol class="worked-steps">{items}</ol>' if items else ""
    return f'{intro}{body}'


def variants_html(entry, index):
    """Spec §9. The authored comparison table first, then the lexical relations
    the entry already carries — synonyms, antonyms and live cross-references."""
    parts = []
    table = topic(entry).get("variantsTable") or {}
    rows = table.get("rows") or []
    if rows:
        columns = table.get("columns") or []
        head = "".join(f"<th scope=\"col\">{e(c)}</th>" for c in columns)
        body = "".join("<tr>" + "".join(f"<td>{e(cell)}</td>" for cell in row) + "</tr>"
                       for row in rows)
        parts.append(f'<div class="table-scroll"><table class="variants-table">'
                     f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>")
    parts.append(relations_html(entry, index))
    return "".join(part for part in parts if part)


def misconceptions_html(entry):
    """Spec §10."""
    items = []
    for item in topic(entry).get("misconceptions") or []:
        items.append(f'<div class="misconception">'
                     f'<p class="misconception-claim">{e(item["claim"])}</p>'
                     f'<p class="misconception-correction">{e(item["correction"])}</p></div>')
    return "".join(items)


def applications_html(entry):
    """Spec §11."""
    items = []
    for item in topic(entry).get("applications") or []:
        detail = (f'<span class="application-detail">{e(item["detail"])}</span>'
                  if item.get("detail") else "")
        items.append(f'<li><span class="application-name">{e(item["name"])}</span>{detail}</li>')
    return f'<ul class="application-list">{"".join(items)}</ul>' if items else ""


def link_buttons_html(items, css_class):
    """Spec §12/§13. Rendered as link buttons, per the spec."""
    buttons = []
    for item in items:
        note = f'<span class="link-note">{e(item["note"])}</span>' if item.get("note") else ""
        external = ' rel="noopener"' if item["href"].startswith("http") else ""
        buttons.append(f'<a class="link-button" href="{e(item["href"])}"{external}>'
                       f'<span>{e(item["label"])}</span>{note}</a>')
    return f'<div class="{css_class}">{"".join(buttons)}</div>' if buttons else ""


def faq_html(entry):
    """Spec §14. Rendered as real text — the FAQPage JSON-LD is emitted from the
    same list, so structured data can never describe an absent question."""
    items = []
    for pair in topic(entry).get("faq") or []:
        items.append(f'<div class="faq-item"><h3>{e(pair["q"])}</h3>'
                     f'<p>{e(pair["a"])}</p></div>')
    return "".join(items)


def revisions_html(entry):
    """Spec §16."""
    rows = topic(entry).get("revisions") or []
    if not rows:
        return ""
    body = "".join(
        f'<tr><td>{e(row.get("version", ""))}</td><td>{e(row.get("date", ""))}</td>'
        f'<td>{e(row.get("change", ""))}</td><td>{e(row.get("editor", ""))}</td></tr>'
        for row in rows)
    return ('<div class="table-scroll"><table class="revision-table">'
            '<thead><tr><th scope="col">Version</th><th scope="col">Date</th>'
            '<th scope="col">Change</th><th scope="col">Editor</th></tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def about_author_html(entry):
    """Spec §17. An E-E-A-T signal, so it states only what the entry records."""
    data = topic(entry)
    if not data.get("author"):
        return ""
    parts = [f'<p class="author-line">Written by <span class="author-name">'
             f'{e(data["author"])}</span>.</p>']
    if data.get("reviewer"):
        parts.append(f'<p class="reviewer-line">Reviewed by {e(data["reviewer"])}.</p>')
    if data.get("dateUpdated"):
        parts.append(f'<p class="updated-line">Last updated '
                     f'<time datetime="{e(data["dateUpdated"])}">'
                     f'{e(data["dateUpdated"])}</time>.</p>')
    parts.append(f'<p class="author-bio-link"><a href="{SITE}/consultancy.html">'
                 "About The Hallucinated Lab</a></p>")
    return "".join(parts)


# The spec's fixed order. Nothing reorders this list at runtime; a section is
# either rendered here or not rendered at all.
def topic_sections(entry, index):
    candidates = [
        ("quick-take", "Quick Take", quick_take_html(entry)),
        ("definitions", "Formal Definitions", formal_definitions_html(entry)),
        ("formal-statement", "Final Formal Statement", formal_statement_html(entry)),
        ("etymology", "Etymology", etymology_html(entry)),
        ("background", "Background & Motivation",
         paragraphs_html(topic(entry).get("background") or [])),
        ("prerequisites", "Prerequisites", prerequisites_html(entry, index)),
        ("deep-dive", "In-Depth Explanation", deep_dive_html(entry)),
        ("worked-example", "Worked Example", worked_example_html(entry)),
        ("variants", "Variants & Related Concepts", variants_html(entry, index)),
        ("misconceptions", "Common Misconceptions", misconceptions_html(entry)),
        ("applications", "Real-World Applications", applications_html(entry)),
        ("more-resources", "More Resources",
         link_buttons_html(topic(entry).get("moreResources") or [], "resource-buttons")),
        ("further-reading", "Further Reading",
         link_buttons_html(topic(entry).get("furtherReading") or [], "reading-buttons")),
        ("faq", "FAQ", faq_html(entry)),
        ("references", "References", citations_html(entry)),
        ("revision-history", "Revision History", revisions_html(entry)),
        ("about-author", "Author & Review", about_author_html(entry)),
    ]
    return [(sid, title, body) for sid, title, body in candidates if body.strip()]


def sections_body_html(sections):
    return "\n".join(
        f'<section class="term-section" id="{sid}" aria-labelledby="{sid}-heading">\n'
        f'  <h2 id="{sid}-heading">{e(title)}</h2>\n  {body}\n</section>'
        for sid, title, body in sections)


def contents_html(sections):
    """The eighteen-section page is long; without a contents list the reader has
    to scroll to find out what it holds."""
    items = "".join(f'<li><a href="#{sid}">{e(title)}</a></li>' for sid, title, _ in sections)
    return (f'<nav class="topic-contents" aria-labelledby="contents-heading">'
            f'<h2 id="contents-heading">On this page</h2>'
            f"<ol>{items}</ol></nav>")


def topic_meta_html(entry):
    """Spec §0 rendered as the page's metadata strip — category, difficulty and
    reading time are the three the reader acts on before committing to a page."""
    data = topic(entry)
    chips = []
    if data.get("category"):
        chips.append(f'<span class="meta-chip meta-category">{e(data["category"])}</span>')
    if data.get("difficulty"):
        chips.append(f'<span class="meta-chip meta-difficulty" '
                     f'data-level="{e(data["difficulty"].lower())}">{e(data["difficulty"])}</span>')
    if data.get("readingTime"):
        chips.append(f'<span class="meta-chip meta-reading">{e(data["readingTime"])} min read</span>')
    if data.get("status") and data["status"] != "Published":
        chips.append(f'<span class="meta-chip meta-status">{e(data["status"])}</span>')
    return f'<div class="topic-meta">{"".join(chips)}</div>' if chips else ""


def aside_html(entry, section, sections):
    rows = [
        ("Lexical ID", entry["lid"]),
        ("Section", section["title"]),
        ("Domain", entry["domain"]),
        ("Part of speech", entry["pos"]),
        ("Form", entry["ngram"]),
    ]
    data = topic(entry)
    if data.get("category"):
        rows.append(("Category", data["category"]))
    if data.get("difficulty"):
        rows.append(("Difficulty", data["difficulty"]))
    if data.get("readingTime"):
        rows.append(("Reading time", f"{data['readingTime']} min"))
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
    return (f'<aside class="term-aside">{contents_html(sections)}'
            f"<h2>Entry data</h2><dl>{body}</dl></aside>")


def jsonld_term(entry, section, canonical, sections):
    """DefinedTerm inside a DefinedTermSet, the breadcrumb trail, and — only when
    the FAQ section actually rendered — the FAQPage block. RULE-05 on the parent
    site: structured data may describe nothing the page does not show."""
    data = topic(entry)
    rendered = {sid for sid, _, _ in sections}

    defined_term = {
        "@type": "DefinedTerm",
        "@id": f"{canonical}#term",
        "name": entry["term"],
        "description": data.get("quickTake") or entry["definitions"][0]["text"],
        "termCode": entry["lid"],
        "inDefinedTermSet": {
            "@type": "DefinedTermSet",
            "@id": f"{BASE}/#{section['id']}",
            "name": section["title"],
            "url": f"{BASE}/#{section['id']}",
        },
        "url": canonical,
    }

    article = {
        "@type": "Article",
        "@id": f"{canonical}#article",
        "headline": entry["term"],
        "description": data.get("metaDescription") or entry["definitions"][0]["text"],
        "mainEntityOfPage": canonical,
        "about": {"@id": f"{canonical}#term"},
        "isPartOf": {"@type": "WebSite", "@id": f"{SITE}/#website", "name": "The Hallucinated Lab"},
    }
    if data.get("author"):
        article["author"] = {"@type": "Person", "name": data["author"]}
    if data.get("reviewer"):
        article["reviewedBy"] = {"@type": "Person", "name": data["reviewer"]}
    if data.get("datePublished"):
        article["datePublished"] = data["datePublished"]
    if data.get("dateUpdated"):
        article["dateModified"] = data["dateUpdated"]
    if data.get("category"):
        article["articleSection"] = data["category"]

    graph = [defined_term, article, {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Dictionary", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 3, "name": section["title"],
             "item": f"{BASE}/#{section['id']}"},
            {"@type": "ListItem", "position": 4, "name": entry["term"], "item": canonical},
        ],
    }]

    if "faq" in rendered:
        graph.append({
            "@type": "FAQPage",
            "@id": f"{canonical}#faq",
            "mainEntity": [
                {"@type": "Question", "name": pair["q"],
                 "acceptedAnswer": {"@type": "Answer", "text": pair["a"]}}
                for pair in data["faq"]
            ],
        })

    payload = json.dumps({"@context": "https://schema.org", "@graph": graph},
                         ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{payload}\n</script>'


def term_page(entry, section, index, prev_entry, next_entry):
    canonical = f"{BASE}/terms/{entry['slug']}.html"
    data = topic(entry)
    gloss = entry["definitions"][0]["text"]
    description = (data.get("metaDescription")
                   or f"{entry['term']} ({entry['pos']}, {entry['domain']}) — {gloss}")[:300]

    sections = topic_sections(entry, index)

    phonetics = []
    if entry.get("ipa"):
        phonetics.append(f'<span class="term-ipa">{e(entry["ipa"])}</span>')
    if entry.get("syllables"):
        phonetics.append(f"<span>{e(entry['syllables'])}</span>")
    phonetics.append(f'<span class="term-pos">{e(entry["pos"])}</span>')

    badges = [f'<span class="badge">{e(tag)}</span>' for tag in entry.get("tags") or []]
    badges += [f'<span class="badge">{e(flag)}</span>' for flag in entry.get("flags") or []]

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
           extra_ld=jsonld_term(entry, section, canonical, sections))}
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
        {topic_meta_html(entry)}
      </header>

{sections_body_html(sections)}

      <nav class="term-nav" aria-label="Adjacent entries">{"".join(nav_links)}</nav>
    </div>
    {aside_html(entry, section, sections)}
  </article>
</main>
{FOOTER.format(site=SITE)}
<script src="../assets/js/nav.js" type="module"></script>
</body>
</html>
"""


# ---------------------------------------------------------------- hub page


def card_meta_html(entry):
    """The topic-page metadata a reader uses to decide whether to open a page:
    what field it belongs to, how hard it is, how long it takes. Rendered only
    where the entry records it, so a legacy card simply stays as it was."""
    data = topic(entry)
    bits = []
    if data.get("difficulty"):
        bits.append(f'<span class="card-difficulty" '
                    f'data-level="{e(data["difficulty"].lower())}">{e(data["difficulty"])}</span>')
    if data.get("readingTime"):
        bits.append(f'<span class="card-reading">{e(data["readingTime"])} min</span>')
    if not bits:
        return ""
    return f'<div class="entry-card-meta">{"".join(bits)}</div>'


def entry_card(entry, href_prefix="terms/"):
    data = topic(entry)
    # The eyebrow prefers the topic category, falling back to the lexical
    # domain, so a migrated and an un-migrated card read the same shape.
    eyebrow = data.get("category") or entry["domain"]
    gloss = data.get("quickTake") or entry["definitions"][0]["text"]
    tags = "".join(f'<span class="badge">{e(t)}</span>'
                   for t in (entry.get("tags") or [])[:2])
    return f"""<a class="entry-card" href="{href_prefix}{e(entry['slug'])}.html">
  <div class="entry-card-top">
    <span class="entry-card-domain">{e(eyebrow)}</span>
    <span class="entry-card-lid">{e(entry['lid'])}</span>
  </div>
  <h3>{e(entry['term'])}</h3>
  <span class="entry-card-pos">{e(entry['pos'])}</span>
  <p class="entry-card-gloss">{e(gloss)}</p>
  {card_meta_html(entry)}
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


def topic_coverage(index):
    """How much of the corpus has been migrated to the topic page interface.

    Printed on every build so the legacy backlog stays visible instead of
    quietly persisting behind pages that look complete.
    """
    total = len(index)
    migrated = sorted(slug for slug, entry in index.items() if entry.get("topic"))
    pending = total - len(migrated)
    line = (f"topic page coverage: {len(migrated)}/{total} entries carry a topic "
            f"block, {pending} still rendering derived fallbacks")
    if migrated:
        line += "\n  migrated: " + ", ".join(migrated)
    return line


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
    print(topic_coverage(index))
    return 0


if __name__ == "__main__":
    sys.exit(main())
