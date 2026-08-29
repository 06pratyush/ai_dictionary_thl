"""The exception hierarchy.

One base class so a caller can catch everything this package raises on purpose
without also catching bugs. The CLI turns any DictionaryError into a single
line on stderr; anything else keeps its traceback, because a traceback is the
right output for a bug and the wrong output for "no entry called that".
"""

from __future__ import annotations


class DictionaryError(Exception):
    """Base for every error this package raises deliberately."""


class CorpusUnavailable(DictionaryError):
    """The shipped corpus files are missing or unreadable."""


class TermNotFound(DictionaryError):
    """A term was asked for by name and no entry matches.

    Carries the near-misses the search engine found so the caller can offer
    them. A bare "not found" makes the reader guess again; naming the three
    closest headwords usually ends the search on the next keystroke.
    """

    def __init__(self, term: str, suggestions: list[str] | None = None) -> None:
        self.term = term
        self.suggestions = suggestions or []
        message = f"No entry for {term!r}."
        if self.suggestions:
            message += " Did you mean: " + ", ".join(self.suggestions) + "?"
        super().__init__(message)
