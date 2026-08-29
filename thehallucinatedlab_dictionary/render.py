from __future__ import annotations

import json
import os
import re
import textwrap
from dataclasses import dataclass
from typing import Any, Optional

from .corpus import Entry
from .search import Hit, Results

GOLD = "\033[38;5;178m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

def supports_colour(stream) -> bool:
    return not (os.getenv("NO_COLOR") or stream.isatty() and os.getenv("TERM") == "dumb")

def _wrap(text: str, width: int, indent: int) -> str:
    wrapper = textwrap.TextWrapper(width=width, initial_indent=" " * indent, subsequent_indent=" " * indent)
    return wrapper.fill(text)

def entry_brief(entry: Entry, *, colour: bool = True, width: int = 80) -> str:
    section_marker = entry.section[0].upper()
    gloss = entry.gloss[:width - len(entry.term) - len(section_marker) - 3]
    return f"{entry.term} {section_marker} {gloss}..."

def entry_full(entry: Entry, *, colour: bool = True, width: int = 80) -> str:
    parts = [f"{entry.term} [{entry.ipa}] {entry.syllables} {entry.pos}"]
    if entry.domain:
        parts.append(f"Domain: {entry.domain}")
    if entry.tags:
        parts.append(f"Tags: {', '.join(entry.tags)}")
    for i, defn in enumerate(entry.definitions, 1):
        parts.append(f"{i}. {defn.text}")
        if defn.example:
            parts.append(f"  Example: {defn.example}")
        if defn.context:
            parts.append(f"  Context: {defn.context}")
    if entry.formula:
        parts.append(f"Formula: {entry.formula['plain']}")
    if entry.etymology:
        parts.append(f"Etymology: {entry.etymology}")
    if entry.synonyms:
        parts.append(f"Synonyms: {', '.join(f'{syn['term']} ({syn['sense']})' for syn in entry.synonyms)}")
    if entry.antonyms:
        parts.append(f"Antonyms: {', '.join(f'{ant['term']} ({ant['sense']})' for ant in entry.antonyms)}")
    if entry.related:
        parts.append(f"Related: {', '.join(entry.related)}")
    if entry.citations:
        parts.append(f"Citations: {', '.join(entry.citations)}")
    parts.append(f"URL: {entry.url}")
    return "\n".join(parts)

def results_table(results: Results, *, colour: bool = True, width: int = 80) -> str:
    parts = [f"Results: {results.total} hits"]
    if results.suggestion:
        parts.append(f"Did you mean: {results.suggestion}")
    for hit in results.hits:
        parts.append(entry_brief(hit.entry, colour=colour, width=width))
    return "\n".join(parts)

def entry_json(entry: Entry) -> str:
    return json.dumps(entry, ensure_ascii=False, indent=2)

def results_json(results: Results) -> str:
    return json.dumps(results, ensure_ascii=False, indent=2)
