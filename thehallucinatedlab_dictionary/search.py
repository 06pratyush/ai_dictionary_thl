"""The dictionary search engine.

A faithful port of ``assets/js/search-engine.js``: same rules, same weights,
same tier ordering, same tie-breaks. The command line and the website must
never disagree about what a query means, so any change here needs the same
change there, and the conformance suites on both sides are written from one
list of cases.

Rule map, from Series 700 of the Master Lexicographical Framework:

===========  ===============================  ==========================================
Rules        Function                         What it covers
===========  ===============================  ==========================================
701-704      :func:`normalize`                case-folding, diacritics, punctuation
705          :func:`parse_query`              stop words
706-707      :func:`damerau_levenshtein`      edit distance with transposition
708          :func:`metaphone`                phonetic fallback
709          :func:`key_proximity`            QWERTY-weighted substitution cost
710-712      :meth:`SearchEngine._build`      inverted index over several fields
711          edge n-grams                     prefix retrieval for auto-complete
713          alias routing                    inflected forms reach their lemma
714-719      :data:`WEIGHT`                    the relevance tiers and penalties
720-722      :func:`parse_query`              wildcards, phrases, boolean operators
725          :meth:`SearchEngine.search`      pagination
===========  ===============================  ==========================================

Written directly rather than delegated. The generated port was ~440 lines
against a delegation ceiling of ~150, and shipped defects that compile and lint
cleanly while being silently wrong: a ``normalize`` with no case fold, so
``[^a-z0-9]`` deleted every capital letter and "GRADIENT" normalised to the
empty string; a QWERTY table keyed by row rather than by character, so no
lookup could hit; and a transposition distance of zero. Verifying a translation
that shape costs more than writing it.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field

from .corpus import Corpus, Entry

# --------------------------------------------------------------------------
# Series 70.A — query pre-processing and normalization
# --------------------------------------------------------------------------

#: Rule 705. Literal in a short query, dropped from a long one.
STOP_WORDS = frozenset({
    'a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'is', 'are', 'was',
    'were', 'be', 'by', 'with', 'and', 'or', 'as', 'that', 'this', 'it', 'its',
})

BOOLEAN_OPERATORS = frozenset({'AND', 'OR', 'NOT'})

_DASHES = re.compile(r'[‐-―]')
_NON_SEARCHABLE = re.compile(r'[^a-z0-9*?\s]')
_WHITESPACE = re.compile(r'\s+')


def normalize(text: str) -> str:
    """Rules 701-704: case-fold, strip diacritics, flatten punctuation, collapse space.

    Applied identically to queries and to indexed text, so both sides of a
    comparison live in the same space. ``Bayes' Theorem``, ``bayes theorem``
    and ``BAYES-THEOREM`` all reduce to ``bayes theorem``.
    """
    if not text:
        return ''
    decomposed = unicodedata.normalize('NFD', str(text).lower())
    without_marks = ''.join(ch for ch in decomposed if not unicodedata.combining(ch))
    flattened = _NON_SEARCHABLE.sub(' ', _DASHES.sub(' ', without_marks))
    return _WHITESPACE.sub(' ', flattened).strip()


def tokenize(text: str) -> list[str]:
    """Normalized whitespace-separated tokens."""
    normalized = normalize(text)
    return normalized.split(' ') if normalized else []


# --------------------------------------------------------------------------
# Series 70.B — fuzzy matching and typo tolerance
# --------------------------------------------------------------------------

QWERTY_ROWS = ('qwertyuiop', 'asdfghjkl', 'zxcvbnm')

#: Built once at import. Rows sit half a key apart, which is the 0.5 term.
KEY_POSITIONS: dict[str, tuple[float, float]] = {
    char: (x + y * 0.5, float(y))
    for y, row in enumerate(QWERTY_ROWS)
    for x, char in enumerate(row)
}


def key_proximity(a: str, b: str) -> float:
    """Rule 709: an adjacent-key substitution is the likelier typo.

    Returns 0 for an identical character, 0.5 for neighbours, 1 otherwise.
    """
    if a == b:
        return 0.0
    first = KEY_POSITIONS.get(a)
    second = KEY_POSITIONS.get(b)
    if first is None or second is None:
        return 1.0
    distance = math.hypot(first[0] - second[0], first[1] - second[1])
    return 0.5 if distance <= 1.2 else 1.0


def edit_budget(length: int) -> int:
    """Rule 706: how many edits to tolerate for a word of this length."""
    if length < 5:
        return 1
    if length < 10:
        return 2
    return 3


def damerau_levenshtein(a: str, b: str, ceiling: float = math.inf) -> float:
    """Rules 706-707: edit distance with transposition and QWERTY-weighted swaps.

    ``ceiling`` short-circuits once the best possible remaining distance already
    exceeds what the caller would accept, which is what keeps the fuzzy pass
    affordable over the whole vocabulary.
    """
    if a == b:
        return 0.0
    if not a:
        return float(len(b))
    if not b:
        return float(len(a))
    if abs(len(a) - len(b)) > ceiling:
        return ceiling + 1

    previous_previous: list[float] = []
    previous: list[float] = [float(j) for j in range(len(b) + 1)]

    for i in range(1, len(a) + 1):
        current: list[float] = [0.0] * (len(b) + 1)
        current[0] = float(i)
        row_minimum = current[0]

        for j in range(1, len(b) + 1):
            substitution = 0.0 if a[i - 1] == b[j - 1] else key_proximity(a[i - 1], b[j - 1])
            best = min(
                current[j - 1] + 1,
                previous[j] + 1,
                previous[j - 1] + substitution,
            )
            # Transposition of adjacent characters — the commonest typing error.
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                best = min(best, previous_previous[j - 2] + 1)

            current[j] = best
            row_minimum = min(row_minimum, best)

        if row_minimum > ceiling:
            return ceiling + 1
        previous_previous = previous
        previous = current

    return previous[len(b)]


_VOWELS = frozenset('aeiou')


def metaphone(word: str) -> str:
    """Rule 708: a compact Metaphone, enough to route "flem" to "phlegm".

    Not a full phonetic library — just the transformations that matter for
    technical vocabulary, so a sound-alike query still lands when exact and
    fuzzy matching have both missed.
    """
    text = re.sub(r'[^a-z]', '', normalize(word))
    if not text:
        return ''

    # Silent leading clusters.
    for cluster in ('kn', 'gn', 'pn', 'ae', 'wr'):
        if text.startswith(cluster):
            text = text[1:]
            break
    if text.startswith('x'):
        text = 's' + text[1:]
    elif text.startswith('wh'):
        text = 'w' + text[2:]

    out: list[str] = []
    i = 0
    while i < len(text):
        char = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''
        after = text[i + 2] if i + 2 < len(text) else ''
        prev = text[i - 1] if i else ''

        if char == prev and char != 'c':
            i += 1
            continue

        if char in _VOWELS:
            if i == 0:
                out.append(char)
        elif char == 'b':
            if not (i == len(text) - 1 and prev == 'm'):
                out.append('b')
        elif char == 'c':
            if nxt == 'i' and after == 'a':
                out.append('x')
            elif nxt == 'h':
                out.append('x')
                i += 1
            elif nxt in 'iey':
                out.append('s')
            else:
                out.append('k')
        elif char == 'd':
            if nxt == 'g' and after in 'iey':
                out.append('j')
                i += 1
            else:
                out.append('t')
        elif char == 'g':
            if nxt == 'h':
                if after and after in _VOWELS:
                    out.append('k')
                i += 1
            elif nxt == 'n':
                pass  # silent
            elif nxt in 'iey':
                out.append('j')
            else:
                out.append('k')
        elif char == 'h':
            if not (prev in _VOWELS and nxt not in _VOWELS):
                out.append('h')
        elif char == 'k':
            if prev != 'c':
                out.append('k')
        elif char == 'p':
            if nxt == 'h':
                out.append('f')
                i += 1
            else:
                out.append('p')
        elif char == 'q':
            out.append('k')
        elif char == 's':
            if nxt == 'h':
                out.append('x')
                i += 1
            elif nxt == 'i' and after in 'oa':
                out.append('x')
            else:
                out.append('s')
        elif char == 't':
            if nxt == 'h':
                out.append('0')
                i += 1
            elif nxt == 'i' and after in 'oa':
                out.append('x')
            else:
                out.append('t')
        elif char == 'v':
            out.append('f')
        elif char in 'wy':
            if nxt and nxt in _VOWELS:
                out.append(char)
        elif char == 'x':
            out.append('ks')
        elif char == 'z':
            out.append('s')
        else:
            out.append(char)
        i += 1

    return ''.join(out)


# --------------------------------------------------------------------------
# Series 70.E — advanced query modifiers
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Query:
    """A parsed query. See :func:`parse_query`."""

    raw: str
    phrases: tuple[str, ...] = ()
    terms: tuple[str, ...] = ()
    excluded: tuple[str, ...] = ()
    wildcards: tuple[re.Pattern[str], ...] = ()
    mode: str = 'OR'
    exact: bool = False


def _wildcard_pattern(token: str) -> re.Pattern[str]:
    """Rule 720: ``*`` is any run of characters, ``?`` exactly one."""
    escaped = re.escape(token).replace(r'\*', '.*').replace(r'\?', '.')
    return re.compile(f'^{escaped}$')


def parse_query(raw: str) -> Query:
    """Rules 720-722: split raw input into phrases, terms, exclusions, wildcards.

    ``"kick the bucket"`` is an exact phrase and disables fuzzy matching.
    ``*ology`` is a wildcard. ``a NOT b`` excludes. ``a AND b`` requires both.
    """
    text = (raw or '').strip()
    if not text:
        return Query(raw='')

    phrases: list[str] = []

    def _capture(match: re.Match[str]) -> str:
        phrases.append(normalize(match.group(1)))
        return ' '

    # Quoted phrases first: everything inside them bypasses later processing.
    remainder = re.sub(r'"([^"]+)"', _capture, text)

    terms: list[str] = []
    excluded: list[str] = []
    wildcards: list[re.Pattern[str]] = []
    mode = 'OR'
    negate_next = False

    for token in remainder.split():
        if token in BOOLEAN_OPERATORS:
            if token == 'NOT':
                negate_next = True
            else:
                mode = token
            continue

        cleaned = normalize(token)
        if not cleaned:
            continue
        if negate_next:
            excluded.append(cleaned)
            negate_next = False
        elif '*' in cleaned or '?' in cleaned:
            wildcards.append(_wildcard_pattern(cleaned))
        else:
            terms.append(cleaned)

    # Rule 705: stop words stay literal in a short query, and are dropped from a
    # long one where they carry no discriminating power.
    if len(terms) > 2:
        kept = [t for t in terms if t not in STOP_WORDS]
        if kept:
            terms = kept

    return Query(
        raw=text,
        phrases=tuple(phrases),
        terms=tuple(terms),
        excluded=tuple(excluded),
        wildcards=tuple(wildcards),
        mode=mode,
        exact=bool(phrases),
    )


# --------------------------------------------------------------------------
# Series 70.D — scoring weights
# --------------------------------------------------------------------------

WEIGHT: dict[str, float] = {
    'headword_exact': 10.0,    # Rule 714
    'inflected_exact': 8.0,    # Rule 715
    'abbreviation': 8.0,
    'headword_prefix': 6.5,
    'anchor_token': 5.0,       # Rule 716
    'synonym': 3.0,
    'fuzzy': 4.0,
    'phonetic': 2.5,
    'definition': 1.0,         # Rule 717
}

#: Rule 719. These must not outrank a live equivalent on a fuzzy hit.
ARCHAIC_FLAGS = frozenset({'Archaic', 'Obsolete', 'Rare'})

MAX_NGRAM = 24


@dataclass(frozen=True)
class Hit:
    """One ranked result."""

    entry: Entry
    score: float
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class Results:
    """A page of results, plus the total and any spelling suggestion."""

    hits: tuple[Hit, ...] = ()
    total: int = 0
    suggestion: str | None = None
    query: Query = field(default_factory=lambda: Query(raw=''))


# --------------------------------------------------------------------------
# The engine — Series 70.C
# --------------------------------------------------------------------------


class SearchEngine:
    """Corpus-agnostic search over a loaded :class:`~.corpus.Corpus`.

    Knows nothing about which sections exist or what the LID prefixes are; it
    is handed a corpus and builds its indexes from whatever is in it.
    """

    def __init__(self, corpus: Corpus) -> None:
        self.corpus = corpus
        self.sections = corpus.sections

        self.by_headword: dict[str, list[Entry]] = {}
        self.by_alias: dict[str, list[Entry]] = {}
        # Sets, not lists: one entry reaches the same key by several routes --
        # "gra" prefixes the headword, its first token, and an inflection -- and
        # duplicates would multiply that entry's score.
        self.by_token: dict[str, set[Entry]] = {}
        self.by_phonetic: dict[str, set[Entry]] = {}
        self.by_edge_ngram: dict[str, set[Entry]] = {}

        self.headwords: dict[Entry, str] = {}
        self.tokens: dict[Entry, tuple[str, ...]] = {}
        self.definition_text: dict[Entry, str] = {}
        self.vocabulary: set[str] = set()

        self._build()

    # -- indexing ---------------------------------------------------

    def _build(self) -> None:
        for entry in self.corpus.entries:
            headword = normalize(entry.term)
            tokens = tuple(headword.split(' ')) if headword else ()
            self.headwords[entry] = headword
            self.tokens[entry] = tokens

            self.by_headword.setdefault(headword, []).append(entry)
            self.vocabulary.add(headword)

            for form in {headword, *tokens}:
                self.by_phonetic.setdefault(metaphone(form), set()).add(entry)
                self._index_prefixes(form, entry)

            # Rule 713: inflections, variants and abbreviations route to the lemma.
            aliases = [normalize(a) for a in (*entry.inflections, *entry.variants, *entry.abbr)]
            for alias in aliases:
                if not alias:
                    continue
                self.by_alias.setdefault(alias, []).append(entry)
                self.vocabulary.add(alias)
                self.by_phonetic.setdefault(metaphone(alias), set()).add(entry)
                self._index_prefixes(alias, entry)

            definition_text = normalize(' '.join(d.text for d in entry.definitions))
            self.definition_text[entry] = definition_text

            # Rule 712: the inverted index spans headword, synonyms and definitions.
            synonyms = [normalize(s.get('term', '')) for s in entry.synonyms]
            searchable = ' '.join([headword, *aliases, *synonyms, definition_text])
            for token in set(searchable.split(' ')):
                if not token:
                    continue
                self.by_token.setdefault(token, set()).add(entry)
                if len(token) > 2:
                    self.vocabulary.add(token)

    def _index_prefixes(self, text: str, entry: Entry) -> None:
        """Rule 711: edge n-grams, so a prefix retrieves without a corpus scan."""
        for n in range(1, min(len(text), MAX_NGRAM) + 1):
            self.by_edge_ngram.setdefault(text[:n], set()).add(entry)

    # -- helpers ----------------------------------------------------

    def _in_scope(self, entry: Entry, scope: str) -> bool:
        return scope == 'all' or entry.section == scope

    def _synonym_terms(self, entry: Entry) -> Iterable[str]:
        return (normalize(s.get('term', '')) for s in entry.synonyms)

    # -- auto-complete ----------------------------------------------

    def suggest(self, raw: str, scope: str = 'all', limit: int = 8) -> list[Entry]:
        """Rule 602/711: prefix retrieval for an auto-complete list.

        The caller owns the 3-keystroke threshold and any debounce.
        """
        prefix = normalize(raw)
        if not prefix:
            return []

        scored: list[tuple[float, Entry]] = []
        for entry in self.by_edge_ngram.get(prefix, set()):
            if not self._in_scope(entry, scope):
                continue
            headword = self.headwords[entry]
            if headword == prefix:
                base = WEIGHT['headword_exact']
            elif headword.startswith(prefix):
                base = WEIGHT['headword_prefix']
            else:
                base = WEIGHT['anchor_token']
            scored.append((base + entry.frequency / 1000, entry))

        if not scored:
            return [hit.entry for hit in self.search(raw, scope=scope, limit=limit).hits]

        scored.sort(key=lambda pair: (-pair[0], pair[1].term))
        return [entry for _, entry in scored[:limit]]

    # -- search -----------------------------------------------------

    def search(
        self,
        raw: str,
        scope: str = 'all',
        limit: int = 20,
        offset: int = 0,
    ) -> Results:
        """Run a query and return one page of ranked results."""
        query = parse_query(raw)
        if not query.raw:
            return Results(query=query)

        points: dict[Entry, float] = {}
        reasons: dict[Entry, list[str]] = {}

        def add(entry: Entry, amount: float, reason: str) -> None:
            if not self._in_scope(entry, scope):
                return
            points[entry] = points.get(entry, 0.0) + amount
            bucket = reasons.setdefault(entry, [])
            if reason not in bucket:
                bucket.append(reason)

        self._score_phrases(query, add)
        self._score_wildcards(query, add)
        self._score_terms(query, add)
        suggestion = self._score_fuzzy(query, points, add)

        ranked = self._rank(query, points, reasons)
        page = ranked[offset:offset + limit]
        return Results(
            hits=tuple(page),
            total=len(ranked),
            suggestion=suggestion,
            query=query,
        )

    def _score_phrases(self, query: Query, add) -> None:
        """Rule 721: an exact phrase bypasses fuzzy matching and phonetics."""
        for phrase in query.phrases:
            for entry in self.by_headword.get(phrase, []):
                add(entry, WEIGHT['headword_exact'], 'exact phrase')
            for entry in self.by_alias.get(phrase, []):
                add(entry, WEIGHT['inflected_exact'], 'exact phrase')
            for entry, text in self.definition_text.items():
                if phrase in text:
                    add(entry, WEIGHT['definition'], 'phrase in definition')

    def _score_wildcards(self, query: Query, add) -> None:
        """Rule 720: wildcards run against headwords and aliases only."""
        for pattern in query.wildcards:
            for headword, entries in self.by_headword.items():
                if pattern.match(headword):
                    for entry in entries:
                        add(entry, WEIGHT['headword_exact'], 'wildcard')
            for alias, entries in self.by_alias.items():
                if pattern.match(alias):
                    for entry in entries:
                        add(entry, WEIGHT['inflected_exact'], 'wildcard')

    def _score_terms(self, query: Query, add) -> None:
        whole = ' '.join(query.terms)
        if whole:
            for entry in self.by_headword.get(whole, []):
                add(entry, WEIGHT['headword_exact'], 'exact match')
            for entry in self.by_alias.get(whole, []):
                add(entry, WEIGHT['inflected_exact'], 'inflected form')

        for term in query.terms:
            for entry in self.by_headword.get(term, []):
                add(entry, WEIGHT['headword_exact'], 'exact match')
            for entry in self.by_alias.get(term, []):
                add(entry, WEIGHT['inflected_exact'], 'inflected form')

            for entry in self.by_edge_ngram.get(term, set()):
                headword = self.headwords[entry]
                if headword.startswith(term) and headword != term:
                    add(entry, WEIGHT['headword_prefix'], 'prefix')

            for entry in self.by_token.get(term, set()):
                tokens = self.tokens[entry]
                if term in tokens and len(tokens) > 1:
                    # Rule 716: an anchor word inside a multi-word headword.
                    add(entry, WEIGHT['anchor_token'], 'anchor term')
                elif term in self._synonym_terms(entry):
                    add(entry, WEIGHT['synonym'], 'synonym')
                else:
                    # Rule 717: a mention buried in a definition.
                    add(entry, WEIGHT['definition'], 'in definition')

    def _score_fuzzy(self, query: Query, points: dict[Entry, float], add) -> str | None:
        """Rules 601/706-708: correct a typo, then fall back to how it sounds."""
        if query.exact or len(points) >= 5:
            return None

        suggestion: str | None = None
        for term in query.terms:
            budget = edit_budget(len(term))
            best_word: str | None = None
            best_distance = math.inf

            for word in self.vocabulary:
                if abs(len(word) - len(term)) > budget:
                    continue
                distance = damerau_levenshtein(term, word, budget)
                if distance > budget:
                    continue
                amount = WEIGHT['fuzzy'] * (1 - distance / (budget + 1))
                for entry in self.by_headword.get(word, []):
                    add(entry, amount, 'fuzzy match')
                for entry in self.by_alias.get(word, []):
                    add(entry, amount * 0.8, 'fuzzy match')
                if distance < best_distance:
                    best_distance = distance
                    best_word = word

            # Rule 708: phonetics only when nothing at all has landed.
            if not points:
                for entry in self.by_phonetic.get(metaphone(term), set()):
                    add(entry, WEIGHT['phonetic'], 'sounds like')
                    if best_word is None:
                        best_word = self.headwords[entry]

            # Rule 601: offer a correction only when the query itself missed.
            if best_word and best_word != term and term not in self.by_headword:
                suggestion = best_word

        return suggestion

    def _rank(
        self,
        query: Query,
        points: dict[Entry, float],
        reasons: dict[Entry, list[str]],
    ) -> list[Hit]:
        hits: list[Hit] = []
        for entry, score in points.items():
            haystack = f'{self.headwords[entry]} {self.definition_text[entry]}'

            # Rule 722.
            if any(term in haystack for term in query.excluded):
                continue
            if (query.mode == 'AND' and len(query.terms) > 1
                    and not all(term in haystack for term in query.terms)):
                continue

            # Rule 719: an obsolete term must not outrank a live one on a fuzzy hit.
            penalty = 0.5 if ARCHAIC_FLAGS & set(entry.flags) else 1.0
            # Rule 718: corpus frequency breaks ties without overturning tiers.
            final = score * penalty + entry.frequency / 1000

            hits.append(Hit(entry=entry, score=final, reasons=tuple(reasons.get(entry, ()))))

        hits.sort(key=lambda hit: (-hit.score, hit.entry.term))
        return hits
