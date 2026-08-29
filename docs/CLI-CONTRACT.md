# Interface contract — `thehallucinatedlab-dictionary`

Authored, not delegated: the packet describing this would have been longer than
the contract itself (§7.6). Every downstream delegation packet carries this file
verbatim as CONTEXT, which is what keeps independently-generated modules
consistent with one another (§7.1).

## Package layout

```
thehallucinatedlab_dictionary/
  __init__.py    version + public re-exports
  errors.py      the exception hierarchy
  corpus.py      load the shipped JSON corpora
  search.py      the Series 700 engine, ported from assets/js/search-engine.js
  render.py      terminal rendering
  cli.py         argparse, the `thl-dict` entry point
  serve.py       loopback bridge and static server
  plugin.py      mount hook for the main toolkit's `thl` command
  data/          the two corpora, copied in at build time
```

## errors.py

```python
class DictionaryError(Exception):
    """Base for every error this package raises deliberately."""

class CorpusUnavailable(DictionaryError):
    """The shipped corpus files are missing or unreadable."""

class TermNotFound(DictionaryError):
    """A term was asked for by name and no entry matches."""
    def __init__(self, term: str, suggestions: list[str] | None = None) -> None: ...
    term: str
    suggestions: list[str]
```

## corpus.py

```python
SECTIONS: tuple[str, ...] = ("ai-mathematics", "software-engineering")

@dataclass(frozen=True)
class Definition:
    id: int
    text: str
    example: str
    context: str | None

@dataclass(frozen=True)
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
    formula: dict | None
    etymology: str
    first_attested: str
    synonyms: tuple[dict, ...]
    antonyms: tuple[dict, ...]
    related: tuple[str, ...]
    citations: tuple[dict, ...]
    frequency: int
    opacity: int | None

    @property
    def gloss(self) -> str:
        """The first definition's text."""

    @property
    def url(self) -> str:
        """Canonical page on thehallucinatedlab.space."""

@dataclass(frozen=True)
class Corpus:
    entries: tuple[Entry, ...]
    sections: dict[str, dict]

    def by_slug(self, slug: str) -> Entry | None: ...
    def by_lid(self, lid: str) -> Entry | None: ...
    def in_section(self, section: str) -> tuple[Entry, ...]: ...

def data_dir() -> Path:
    """Directory holding the shipped corpus JSON."""

def load(path: Path | None = None) -> Corpus:
    """Read both corpora. Raises CorpusUnavailable if they cannot be read."""
```

## search.py

A faithful port of `assets/js/search-engine.js`. Same rules, same weights, same
tier ordering — the CLI and the website must not disagree about what a query
means.

```python
STOP_WORDS: frozenset[str]
WEIGHT: dict[str, float]     # headword_exact 10, inflected_exact 8,
                             # abbreviation 8, headword_prefix 6.5,
                             # anchor_token 5, synonym 3, fuzzy 4,
                             # phonetic 2.5, definition 1
ARCHAIC_FLAGS: frozenset[str]

def normalize(text: str) -> str: ...            # Rules 701-704
def tokenize(text: str) -> list[str]: ...
def key_proximity(a: str, b: str) -> float: ... # Rule 709, returns 0, 0.5 or 1
def damerau_levenshtein(a: str, b: str, ceiling: float = inf) -> float: ...
def edit_budget(length: int) -> int: ...        # Rule 706: 1 / 2 / 3
def metaphone(word: str) -> str: ...            # Rule 708

@dataclass(frozen=True)
class Query:
    raw: str
    phrases: list[str]
    terms: list[str]
    excluded: list[str]
    wildcards: list[re.Pattern]
    mode: str        # "AND" or "OR"
    exact: bool

def parse_query(raw: str) -> Query: ...         # Rules 720-722

@dataclass(frozen=True)
class Hit:
    entry: Entry
    score: float
    reasons: tuple[str, ...]

@dataclass(frozen=True)
class Results:
    hits: tuple[Hit, ...]
    total: int
    suggestion: str | None
    query: Query

class SearchEngine:
    def __init__(self, corpus: Corpus) -> None: ...
    def suggest(self, raw: str, scope: str = "all", limit: int = 8) -> list[Entry]: ...
    def search(self, raw: str, scope: str = "all",
               limit: int = 20, offset: int = 0) -> Results: ...
```

## render.py

Rendering only. No I/O, no printing — every function returns a string, so the
CLI decides where it goes and the test suite can assert on it.

```python
GOLD: str; DIM: str; BOLD: str; RESET: str   # ANSI, empty when colour is off

def supports_colour(stream) -> bool:
    """False when not a tty, when NO_COLOR is set, or when TERM is dumb."""

def entry_full(entry: Entry, *, colour: bool = True, width: int = 80) -> str:
    """The whole entry: headword, phonetics, senses, formula, etymology,
    relations, citations."""

def entry_brief(entry: Entry, *, colour: bool = True, width: int = 80) -> str:
    """One line: term, section marker, gloss truncated to width."""

def results_table(results: Results, *, colour: bool = True, width: int = 80) -> str:
    """Ranked hits, one brief line each, with the count and any suggestion."""

def entry_json(entry: Entry) -> str: ...
def results_json(results: Results) -> str: ...
```

## cli.py

Mirrors the main toolkit's conventions exactly: namespaced subcommands, a bare
namespace lists what is available, `main(argv) -> int`, and a `_guard` that
turns a library error into one line on stderr rather than a traceback.

```python
def build_parser() -> argparse.ArgumentParser: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

Commands:

| Command | Effect |
| :-- | :-- |
| `thl-dict search <query...>` | ranked hits across both corpora |
| `thl-dict define <term...>` | one full entry, or a not-found with suggestions |
| `thl-dict list` | browse; `--section`, `--domain`, `--letter` |
| `thl-dict random` | one entry at random |
| `thl-dict serve` | loopback bridge + the static site |
| `thl-dict sections` | the two corpora and their sizes |

Global flags on every command: `--section {all,ai-mathematics,software-engineering}`
(alias `-s`), `--json`, `--no-color`, `--width N`, `--limit N`.

Exit codes: 0 success, 1 a library error, 2 a usage error or a term not found.

## serve.py

Retained rather than delegated: this is a network boundary (§7.6).

```python
DEFAULT_PORT: int = 8788        # 8787 is the toolkit's bridge; do not collide
DEFAULT_ORIGINS: tuple[str, ...]
MAX_QUERY_CHARS: int = 200

def host_allowed(host: str | None) -> bool: ...
def origin_allowed(origin: str | None, extra: tuple[str, ...] = ()) -> bool: ...
def capabilities() -> dict: ...
def create_server(port: int, extra_origins: tuple[str, ...], quiet: bool,
                  site_root: Path | None) -> ThreadingHTTPServer: ...
def serve(port: int = DEFAULT_PORT, extra_origins: tuple[str, ...] = (),
          quiet: bool = True, site_root: Path | None = None) -> int: ...
```

Endpoints, all read-only:

- `GET /thl/v1/capabilities` — name, version, sections, entry count
- `GET /thl/v1/dict/search?q=&section=&limit=&offset=` — ranked hits as JSON
- `GET /thl/v1/dict/term/<slug>` — one entry as JSON
- `GET /thl/v1/dict/sections` — the corpora
- Any other path — the static site, when `site_root` is given

## plugin.py

```python
def add_subparser(subparsers) -> None:
    """Mount this package as `thl dict` on the main toolkit's parser."""
def run_parsed(args: argparse.Namespace) -> int: ...
```

Registered under the `thehallucinatedlab.commands` entry-point group so the
main `thl` command can discover it without importing this package eagerly.
