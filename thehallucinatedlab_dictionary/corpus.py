from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import CorpusUnavailable

_WORD_SPLIT = re.compile(r"[\s‐-―-]+")


def ngram_class(term: str) -> str:
    """Rules 102/103: the n-gram class of a headword, from its word count.

    Derived here rather than read from the JSON because it is a build-time
    field -- build/build.py recomputes it on every build and never writes it
    back to data/*.json. Reading it would KeyError on every entry. The rule is
    duplicated from build.py deliberately: the alternative is importing the
    build script into the shipped wheel.
    """
    words = [w for w in _WORD_SPLIT.split(term.strip()) if w]
    if len(words) == 1:
        return "unigram"
    return "bigram" if len(words) == 2 else "polygram"


SECTIONS: tuple[str, ...] = ("ai-mathematics", "software-engineering")

@dataclass(frozen=True)
class Definition:
    id: int
    text: str
    example: str
    context: str | None

@dataclass(frozen=True, eq=False)
class Entry:
    lid: str
    term: str
    slug: str
    section: str
    domain: str
    pos: str
    ngram: str
    syllables: str
    ipa: str
    tags: tuple[str, ...]
    flags: tuple[str, ...]
    abbr: tuple[str, ...]
    inflections: tuple[str, ...]
    variants: tuple[str, ...]
    definitions: tuple[Definition, ...]
    formula: dict[str, Any] | None
    etymology: str
    first_attested: str
    synonyms: tuple[dict[str, Any], ...]
    antonyms: tuple[dict[str, Any], ...]
    related: tuple[str, ...]
    citations: tuple[dict[str, Any], ...]
    frequency: int
    opacity: int | None

    @property
    def gloss(self) -> str:
        return self.definitions[0].text

    @property
    def url(self) -> str:
        return f"https://thehallucinatedlab.space/dictionary/terms/{self.slug}.html"

@dataclass(frozen=True)
class Corpus:
    entries: tuple[Entry, ...]
    sections: dict[str, dict[str, Any]]

    def __post_init__(self) -> None:
        slug_lookup = {entry.slug: entry for entry in self.entries}
        lid_lookup = {entry.lid: entry for entry in self.entries}
        object.__setattr__(self, "_slug_lookup", slug_lookup)
        object.__setattr__(self, "_lid_lookup", lid_lookup)

    def by_slug(self, slug: str) -> Entry | None:
        return self._slug_lookup.get(slug)

    def by_lid(self, lid: str) -> Entry | None:
        return self._lid_lookup.get(lid)

    def in_section(self, section: str) -> tuple[Entry, ...]:
        return tuple(entry for entry in self.entries if entry.section == section)

def data_dir() -> Path:
    return Path(__file__).parent / "data"

def _read(path: Path) -> dict[str, Any]:
    """Read and parse one corpus file, or fail with a message naming it."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise CorpusUnavailable(f"Missing corpus file: {path}") from None
    except OSError as err:
        raise CorpusUnavailable(f"Cannot read corpus file {path}: {err}") from None
    except json.JSONDecodeError as err:
        raise CorpusUnavailable(f"Malformed JSON in {path}: {err}") from None


def _entries_from(data: dict[str, Any], section_id: str) -> list[Entry]:
    """Convert one parsed corpus file into Entry objects."""
    entries: list[Entry] = []
    for entry_data in data.get("entries", []):
        for required in ("lid", "term", "slug", "definitions"):
            if required not in entry_data:
                raise CorpusUnavailable(
                    f"Entry in section {section_id!r} is missing {required!r}."
                )
        definitions = tuple(
            Definition(
                id=def_data["id"],
                text=def_data["text"],
                example=def_data.get("example", ""),
                context=def_data.get("context"),
            )
            for def_data in entry_data["definitions"]
        )
        entries.append(
            Entry(
                lid=entry_data["lid"],
                term=entry_data["term"],
                slug=entry_data["slug"],
                section=section_id,
                domain=entry_data.get("domain", ""),
                pos=entry_data.get("pos", "noun"),
                ngram=ngram_class(entry_data["term"]),
                syllables=entry_data.get("syllables", ""),
                ipa=entry_data.get("ipa", ""),
                tags=tuple(entry_data.get("tags", [])),
                flags=tuple(entry_data.get("flags", [])),
                abbr=tuple(entry_data.get("abbr", [])),
                inflections=tuple(entry_data.get("inflections", [])),
                variants=tuple(entry_data.get("variants", [])),
                definitions=definitions,
                formula=entry_data.get("formula"),
                etymology=entry_data.get("etymology", ""),
                first_attested=entry_data.get("firstAttested", ""),
                synonyms=tuple(entry_data.get("synonyms", [])),
                antonyms=tuple(entry_data.get("antonyms", [])),
                related=tuple(entry_data.get("related", [])),
                citations=tuple(entry_data.get("citations", [])),
                frequency=entry_data.get("frequency", 0),
                opacity=entry_data.get("opacity"),
            )
        )
    return entries


def load(path: Path | None = None) -> Corpus:
    """Read both corpora and return them as one searchable Corpus.

    A single search bar spans both sections, so the default is to load both --
    loading one would silently make half the dictionary unreachable.

    Args:
        path: A directory holding the corpus files, or a single corpus file.
            Defaults to the data directory shipped inside the package.

    Raises:
        CorpusUnavailable: A file is missing, unreadable, malformed, or an
            entry lacks a required key.
    """
    target = path if path is not None else data_dir()

    files = (
        [target] if target.is_file()
        else [target / f"{name}.json" for name in SECTIONS]
    )

    entries: list[Entry] = []
    sections: dict[str, dict[str, Any]] = {}

    for file_path in files:
        data = _read(file_path)
        section = data.get("section") or {}
        section_id = section.get("id") or file_path.stem
        sections[section_id] = section
        entries.extend(_entries_from(data, section_id))

    if not entries:
        raise CorpusUnavailable(f"No entries found under {target}.")

    entries.sort(key=lambda entry: entry.term.casefold())
    return Corpus(entries=tuple(entries), sections=sections)
