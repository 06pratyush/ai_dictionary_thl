"""Terminal rendering.

Every function here returns a string. Nothing prints, nothing writes to a
stream: the CLI decides where output goes, and the test suite can assert on the
exact text rather than capturing stdout.

The site's palette is gold on near-black. In a terminal the closest honest
equivalent is 256-colour 178 for the gold and the terminal's own dim attribute
for muted text, so the output reads as the same product without trying to
repaint the user's terminal background.
"""

from __future__ import annotations

import json
import os
import textwrap

from .corpus import Entry
from .search import Results

GOLD = "\x1b[38;5;178m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RESET = "\x1b[0m"

#: Short markers so a mixed result list shows which corpus each hit came from
#: without spending a column on the full section title.
SECTION_MARKS = {
    "ai-mathematics": "AI",
    "software-engineering": "SWE",
}


def supports_colour(stream) -> bool:
    """Whether to emit ANSI at all.

    Honours NO_COLOR (https://no-color.org) and TERM=dumb, and refuses when the
    stream is not a terminal — so piping to a file or another program gives
    plain text without the user having to ask. A stream with no isatty() is
    treated as not a terminal rather than raising.
    """
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        return False


def _paint(text: str, code: str, colour: bool) -> str:
    """Wrap text in an escape code, or return it untouched."""
    return f"{code}{text}{RESET}" if colour and text else text


def _wrap(text: str, width: int, indent: str = "") -> str:
    """Wrap to width, indenting every line after the first."""
    if not text:
        return ""
    return textwrap.fill(
        text,
        width=max(width, 20),
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )


def _truncate(text: str, width: int) -> str:
    """Cut to width, with an ellipsis when something was removed."""
    if len(text) <= width:
        return text
    if width <= 1:
        return text[:width]
    return text[: width - 1] + "…"


# ---------------------------------------------------------------- entries


def entry_brief(entry: Entry, *, colour: bool = True, width: int = 80) -> str:
    """One line: term, section marker, and as much gloss as fits.

    Measured on the plain text and coloured afterwards — colouring first would
    count the escape sequences toward the width and truncate the visible text
    early.
    """
    mark = SECTION_MARKS.get(entry.section, entry.section[:3].upper())
    prefix = f"{entry.term}  [{mark}]  "
    room = width - len(prefix)

    if room < 12:
        return _paint(_truncate(entry.term, width), GOLD, colour)

    gloss = _truncate(entry.gloss, room)
    if not colour:
        return f"{prefix}{gloss}"
    return f"{GOLD}{entry.term}{RESET}  {DIM}[{mark}]{RESET}  {gloss}"


def entry_full(entry: Entry, *, colour: bool = True, width: int = 80) -> str:
    """The whole entry, as it would read on its page.

    Sections with nothing in them are omitted entirely rather than printed as an
    empty heading — an entry with no formula should not show the reader a
    "FORMULA" label with nothing under it.
    """
    lines: list[str] = []

    lines.append(_paint(entry.term, GOLD + BOLD, colour))

    phonetics = [part for part in (entry.ipa, entry.syllables, entry.pos) if part]
    if phonetics:
        lines.append(_paint("  ".join(phonetics), DIM, colour))

    badge_parts = [entry.domain, *entry.tags, *entry.flags]
    badges = "  ·  ".join(part for part in badge_parts if part)
    if badges:
        lines.append(_paint(badges, DIM, colour))
    lines.append("")

    for definition in entry.definitions:
        body = definition.text
        if definition.context:
            body = f"[{definition.context}] {body}"
        lines.append(_wrap(f"{definition.id}. {body}", width).rstrip())
        if definition.example:
            lines.append(_paint(_wrap(f'"{definition.example}"', width, "   "), DIM, colour))
        lines.append("")

    if entry.formula:
        plain = entry.formula.get("plain") or entry.formula.get("latex")
        if plain:
            lines.append(_paint("FORMULA", GOLD, colour))
            lines.append(f"  {plain}")
            note = entry.formula.get("note")
            if note:
                lines.append(_paint(_wrap(note, width, "  "), DIM, colour))
            lines.append("")

    if entry.etymology:
        lines.append(_paint("ETYMOLOGY", GOLD, colour))
        lines.append(_wrap(entry.etymology, width, "  "))
        if entry.first_attested:
            lines.append(_paint(f"  first attested {entry.first_attested}", DIM, colour))
        lines.append("")

    lines.extend(_relations(entry, colour))

    if entry.citations:
        lines.append(_paint("REFERENCES", GOLD, colour))
        for citation in entry.citations:
            label = citation.get("label", "")
            if label:
                lines.append(_wrap(f"- {label}", width, "  "))
            source = citation.get("source")
            if source:
                lines.append(_paint(_wrap(source, width, "    "), DIM, colour))
        lines.append("")

    lines.append(_paint(entry.url, DIM, colour))
    lines.append(_paint(entry.lid, DIM, colour))

    return "\n".join(lines).rstrip() + "\n"


def _relations(entry: Entry, colour: bool) -> list[str]:
    """Synonyms, antonyms and cross-references, each tagged with its sense.

    Rule 521: a synonym is mapped to a specific sense, never to the entry as a
    whole, so the sense number travels with it into the output.
    """
    lines: list[str] = []

    if entry.synonyms:
        lines.append(_paint("SYNONYMS", GOLD, colour))
        for synonym in entry.synonyms:
            tag = f"sense {synonym.get('senseId', '?')} · {synonym.get('proximity', '')}".strip()
            lines.append(f"  {synonym.get('term', '')}  " + _paint(f"({tag})", DIM, colour))
        lines.append("")

    if entry.antonyms:
        lines.append(_paint("ANTONYMS", GOLD, colour))
        for antonym in entry.antonyms:
            tag = f"sense {antonym.get('senseId', '?')} · {antonym.get('polarity', '')}".strip()
            lines.append(f"  {antonym.get('term', '')}  " + _paint(f"({tag})", DIM, colour))
        lines.append("")

    if entry.related:
        lines.append(_paint("SEE ALSO", GOLD, colour))
        lines.append(f"  {', '.join(entry.related)}")
        lines.append("")

    return lines


# ---------------------------------------------------------------- results


def results_table(results: Results, *, colour: bool = True, width: int = 80) -> str:
    """The count, any spelling correction, then one brief line per hit."""
    lines: list[str] = []

    if not results.total:
        lines.append(_paint("no matches", DIM, colour))
        if results.suggestion:
            lines.append(f"did you mean: {_paint(results.suggestion, GOLD, colour)}?")
        return "\n".join(lines) + "\n"

    plural = "" if results.total == 1 else "es"
    shown = len(results.hits)
    count = f"{results.total} match{plural}"
    if shown < results.total:
        count += f", showing {shown}"
    lines.append(_paint(count, DIM, colour))

    if results.suggestion:
        lines.append(f"did you mean: {_paint(results.suggestion, GOLD, colour)}?")
    lines.append("")

    for hit in results.hits:
        lines.append(entry_brief(hit.entry, colour=colour, width=width))

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- json


def _entry_dict(entry: Entry) -> dict:
    """One entry as plain JSON-able data, in the shape the web API returns.

    Written out field by field rather than via dataclasses.asdict so the JSON
    keeps the corpus's own key spelling — firstAttested, not first_attested —
    and so a new internal field cannot silently change the public payload.
    """
    return {
        "lid": entry.lid,
        "term": entry.term,
        "slug": entry.slug,
        "section": entry.section,
        "domain": entry.domain,
        "pos": entry.pos,
        "ngram": entry.ngram,
        "syllables": entry.syllables,
        "ipa": entry.ipa,
        "tags": list(entry.tags),
        "flags": list(entry.flags),
        "abbr": list(entry.abbr),
        "inflections": list(entry.inflections),
        "variants": list(entry.variants),
        "definitions": [
            {
                "id": definition.id,
                "context": definition.context,
                "text": definition.text,
                "example": definition.example,
            }
            for definition in entry.definitions
        ],
        "formula": entry.formula,
        "etymology": entry.etymology,
        "firstAttested": entry.first_attested,
        "synonyms": [dict(s) for s in entry.synonyms],
        "antonyms": [dict(a) for a in entry.antonyms],
        "related": list(entry.related),
        "citations": [dict(c) for c in entry.citations],
        "frequency": entry.frequency,
        "opacity": entry.opacity,
        "url": entry.url,
    }


def _dump(payload) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def entry_json(entry: Entry) -> str:
    """One entry as JSON."""
    return _dump(_entry_dict(entry))


def entries_json(entries) -> str:
    """A list of entries as JSON."""
    return _dump([_entry_dict(entry) for entry in entries])


def results_json(results: Results) -> str:
    """A result page as JSON, scores and match reasons included."""
    return _dump({
        "query": results.query.raw,
        "total": results.total,
        "suggestion": results.suggestion,
        "results": [
            {
                **_entry_dict(hit.entry),
                "score": round(hit.score, 4),
                "reasons": list(hit.reasons),
            }
            for hit in results.hits
        ],
    })
