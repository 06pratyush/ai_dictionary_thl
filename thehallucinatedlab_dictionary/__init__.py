"""The Hallucinated Lab dictionary, as an importable package and a CLI.

Two corpora -- AI & Mathematics and Software Engineering Core -- behind one
search engine, the same one the website runs. The corpora ship inside the
wheel, so every command works with no network at all::

    thl-dict search gradient
    thl-dict define "technical debt"
    thl-dict serve

The heavy import (the search engine builds its indexes at construction) is
deferred to first use, so `thl-dict --help` stays fast.
"""

from __future__ import annotations

__version__ = "1.0.0"

from .errors import CorpusUnavailable, DictionaryError, TermNotFound

__all__ = [
    "CorpusUnavailable",
    "DictionaryError",
    "TermNotFound",
    "__version__",
]
