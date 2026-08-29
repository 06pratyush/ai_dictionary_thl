# The dictionary on the command line

The whole dictionary — both corpora, the same search engine the website runs —
installed as a Python package and queried from a terminal. No network, no
account, no browser.

```bash
pip install thehallucinatedlab-dictionary
thl-dict define "technical debt"
```

## Install

```bash
pip install thehallucinatedlab-dictionary
```

That gives you `thl-dict`. If you also have the lab's main toolkit installed,
the same commands appear under it:

```bash
pip install thehallucinatedlab thehallucinatedlab-dictionary
thl dict define "technical debt"
```

Nothing needs configuring to make that happen. The toolkit reads the
`thehallucinatedlab.commands` entry-point group when it builds its parser and
mounts whatever it finds, so installing the wheel is the whole step. Both names
run the same code — `thl dict search` and `thl-dict search` cannot drift apart,
because there is one parser and two front doors onto it.

There are no runtime dependencies. The corpora ship inside the wheel, and the
local server is built on `http.server`, so a fresh interpreter with nothing else
installed runs every command offline. A dictionary that needs the network to
define a word is a website with extra steps.

## Commands

### `search` — ranked hits across both corpora

```bash
thl-dict search gradient
thl-dict search "loss function" --section ai-mathematics
thl-dict search entropi          # misspellings are corrected
```

Results are ranked by the same tiers the website uses: an exact headword scores
10×, an inflected form or abbreviation 8×, an anchor word inside a multi-word
term 5×, and a mention buried in a definition 1×.

Query syntax:

| Syntax | Effect |
| :-- | :-- |
| `"kick the bucket"` | exact phrase; fuzzy matching and phonetics are bypassed |
| `*ology` | wildcard — `*` is any run of characters, `?` is exactly one |
| `gradient AND descent` | both terms must be present |
| `tensor NOT physics` | excludes entries mentioning the second term |

### `define` — one full entry

```bash
thl-dict define eigenvector
thl-dict define "big o notation"
thl-dict define GD               # abbreviations resolve
```

Resolution goes slug, then exact headword, then the search engine. A miss exits
2 and names the closest headwords rather than leaving you to guess again.

### `list` — browse

```bash
thl-dict list --section software-engineering
thl-dict list --domain Concurrency
thl-dict list --letter e --limit 5
```

### `random` — one entry, at random

```bash
thl-dict random
thl-dict random --section ai-mathematics
```

### `sections` — what the corpora hold

```bash
thl-dict sections
```

### `serve` — the local bridge

```bash
thl-dict serve
thl-dict serve --site .          # also serve the built static site
```

Binds `127.0.0.1:8788` and answers read-only JSON:

| Endpoint | Returns |
| :-- | :-- |
| `GET /thl/v1/capabilities` | version, section names, entry counts |
| `GET /thl/v1/dict/search?q=&section=&limit=&offset=` | ranked hits |
| `GET /thl/v1/dict/term/<slug>` | one entry |
| `GET /thl/v1/dict/sections` | the corpora |

Port 8788, not 8787: the main toolkit's own bridge holds 8787, and colliding
would make whichever started second fail to bind for no benefit.

## Flags

Available on the commands they make sense for:

| Flag | Effect |
| :-- | :-- |
| `-s, --section` | `all` (default), `ai-mathematics`, `software-engineering` |
| `--json` | machine-readable output; never coloured |
| `--no-color` | plain text even on a tty |
| `--width N` | wrap column, default 80 |
| `--limit N` | maximum results, default 20 |

Colour is on only when stdout is a terminal, `NO_COLOR` is unset, and `TERM` is
not `dumb`. Piping to a file or another program gives you plain text without
being asked.

## Exit codes

| Code | Meaning |
| :-- | :-- |
| 0 | success |
| 1 | a library error — an unreadable corpus, a port already bound |
| 2 | a usage error, or a term that does not exist |

Errors go to stderr, results to stdout, so `thl-dict define x > out.txt` gives a
clean file either way.

## Using it as a library

```python
from thehallucinatedlab_dictionary.corpus import load
from thehallucinatedlab_dictionary.search import SearchEngine

corpus = load()
engine = SearchEngine(corpus)

for hit in engine.search("gradient", limit=5).hits:
    print(hit.entry.term, hit.score)

entry = corpus.by_slug("technical-debt")
print(entry.gloss)
print(entry.url)
```

`Entry` and `Definition` are frozen dataclasses. `Entry` hashes by identity, so
it is safe as a dict key or set member — which is what the engine's indexes rely
on.

## Security posture of `serve`

Everything it exposes is read-only; there is no endpoint that writes, uploads or
executes. Beyond that, in the order the work actually gets done:

1. **The Host allowlist.** This is what survives DNS rebinding. An attacker who
   points a domain at 127.0.0.1 makes their page same-origin with the server,
   and browsers omit `Origin` on same-origin GETs — so an Origin check alone
   waves the request through. `Host` still carries the name the browser was
   asked to resolve.
2. **The Origin allowlist.** Loopback binding stops the *network* reaching the
   server; it does not stop another site the visitor has open, since their
   browser runs on this machine too.
3. **Loopback binding.** `127.0.0.1` only, never `0.0.0.0`.
4. **A query cap.** Fuzzy matching is O(query × vocabulary), so an unbounded
   query string is a way to burn CPU on the machine you are trying to help.
5. **Path containment.** When serving the static site, every path is resolved
   and confirmed to sit inside the root. Rejecting `..` by string match is not
   enough — a symlink inside the root can point anywhere, and only resolution
   catches that.
