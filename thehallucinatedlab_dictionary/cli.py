"""The ``thl-dict`` command.

Two front doors onto one parser::

    thl-dict search gradient          # installed on its own
    thl dict search gradient          # mounted on the main toolkit

:func:`attach_commands` is what makes that possible: it adds every subcommand to
whatever parser it is handed, so the toolkit's ``thl dict`` and the standalone
``thl-dict`` cannot drift apart. There is one definition of every flag.

Retained rather than delegated: the command surface is API design, and §7.6 of
the protocol keeps that here.
"""

from __future__ import annotations

import argparse
import random
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__, render
from .errors import DictionaryError, TermNotFound

SECTION_CHOICES = ("all", "ai-mathematics", "software-engineering")

DEFAULT_WIDTH = 80
DEFAULT_LIMIT = 20


# ---------------------------------------------------------------- parser


def _add_output_flags(parser: argparse.ArgumentParser, *, limit: bool = True) -> None:
    """Flags that shape output, shared by every command that produces any."""
    parser.add_argument(
        "-s", "--section", choices=SECTION_CHOICES, default="all",
        help="which corpus to look in (default: both)",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--no-color", action="store_true", help="plain text even on a tty")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH,
                        help=f"wrap column (default {DEFAULT_WIDTH})")
    if limit:
        parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                            help=f"maximum results (default {DEFAULT_LIMIT})")


def attach_commands(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Add every dictionary subcommand to ``parser``.

    Called by :func:`build_parser` for the standalone command, and by
    ``plugin.add_subparser`` when the main toolkit mounts this as ``thl dict``.
    """
    commands = parser.add_subparsers(dest="command")

    search = commands.add_parser("search", help="ranked hits across both corpora")
    search.add_argument("query", nargs="+", help='a term, or "an exact phrase"')
    search.add_argument("--offset", type=int, default=0, help="skip this many results")
    _add_output_flags(search)

    define = commands.add_parser("define", help="one full entry")
    define.add_argument("term", nargs="+", help="the headword, slug or abbreviation")
    _add_output_flags(define, limit=False)

    browse = commands.add_parser("list", help="browse the corpora")
    browse.add_argument("--domain", default=None, help="filter by domain, e.g. Concurrency")
    browse.add_argument("--letter", default=None, help="filter by first letter")
    _add_output_flags(browse)

    chance = commands.add_parser("random", help="one entry, at random")
    _add_output_flags(chance, limit=False)

    commands.add_parser("sections", help="what the corpora hold")

    bridge = commands.add_parser("serve", help="run the local read-only bridge")
    bridge.add_argument("-p", "--port", type=int, default=None, help="default 8788")
    bridge.add_argument("--allow-origin", action="append", default=[],
                        help="an extra origin to answer, repeatable")
    bridge.add_argument("--site", default=None,
                        help="directory of the built site to serve alongside the API")
    bridge.add_argument("--verbose", action="store_true", help="log every request")

    return parser


def build_parser() -> argparse.ArgumentParser:
    """The standalone ``thl-dict`` parser."""
    parser = argparse.ArgumentParser(
        prog="thl-dict",
        description="The Hallucinated Lab dictionary — AI, mathematics and "
                    "software engineering.",
        epilog='Try: thl-dict define "technical debt"',
    )
    parser.add_argument("--version", action="version", version=f"thl-dict {__version__}")
    return attach_commands(parser)


# ---------------------------------------------------------------- helpers


def _configure_stdio() -> None:
    """Make stdout able to carry the corpus.

    Every entry holds IPA, and many hold en dashes and typographic quotes. On
    Windows stdout defaults to the ANSI code page -- cp1252 here -- and the
    first `thl-dict define` dies with UnicodeEncodeError on the stress mark in
    the pronunciation. Reconfiguring to UTF-8 fixes it where the terminal can
    show those glyphs; errors="replace" keeps the command useful where it
    cannot, because a substituted character is a far better outcome than a
    traceback instead of the definition.

    Wrapped because a stream that has been replaced -- by a test harness, or by
    a caller capturing output -- may not offer reconfigure() at all.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            continue


def _corpus():
    """Load the corpora. Imported here so `--help` does not pay for it."""
    from .corpus import load

    return load()


def _engine(corpus):
    from .search import SearchEngine

    return SearchEngine(corpus)


def _colour(args: argparse.Namespace) -> bool:
    """Colour only when asked for, supported, and not emitting JSON."""
    if getattr(args, "json", False) or getattr(args, "no_color", False):
        return False
    return render.supports_colour(sys.stdout)


def _scoped(corpus, section: str):
    return corpus.entries if section == "all" else corpus.in_section(section)


# ---------------------------------------------------------------- commands


def _run_search(args: argparse.Namespace) -> int:
    corpus = _corpus()
    results = _engine(corpus).search(
        " ".join(args.query),
        scope=args.section,
        limit=args.limit,
        offset=args.offset,
    )
    if args.json:
        print(render.results_json(results))
        return 0

    print(render.results_table(results, colour=_colour(args), width=args.width))
    return 0


def _run_define(args: argparse.Namespace) -> int:
    """Resolve slug, then exact headword, then fall back to search.

    A miss names the closest headwords rather than leaving the reader to guess
    again — a bare "not found" usually costs another three attempts.
    """
    corpus = _corpus()
    wanted = " ".join(args.term)

    entry = corpus.by_slug(wanted.lower().replace(" ", "-"))
    if entry is None:
        folded = wanted.casefold()
        entry = next(
            (
                candidate for candidate in corpus.entries
                if candidate.term.casefold() == folded
                or folded in {a.casefold() for a in candidate.abbr}
            ),
            None,
        )

    engine = _engine(corpus)
    if entry is None:
        results = engine.search(wanted, scope=args.section, limit=1)
        if results.hits:
            entry = results.hits[0].entry

    if entry is None:
        suggestions = [e.term for e in engine.suggest(wanted, scope=args.section, limit=3)]
        raise TermNotFound(wanted, suggestions)

    if args.json:
        print(render.entry_json(entry))
        return 0

    print(render.entry_full(entry, colour=_colour(args), width=args.width))
    return 0


def _run_list(args: argparse.Namespace) -> int:
    corpus = _corpus()
    entries = _scoped(corpus, args.section)

    if args.domain:
        wanted = args.domain.casefold()
        entries = tuple(e for e in entries if e.domain.casefold() == wanted)
    if args.letter:
        initial = args.letter[:1].casefold()
        entries = tuple(e for e in entries if e.term[:1].casefold() == initial)

    entries = entries[: args.limit]
    if args.json:
        print(render.entries_json(entries))
        return 0

    if not entries:
        print("Nothing matched that filter.", file=sys.stderr)
        return 0

    colour = _colour(args)
    for entry in entries:
        print(render.entry_brief(entry, colour=colour, width=args.width))
    return 0


def _run_random(args: argparse.Namespace) -> int:
    corpus = _corpus()
    entries = _scoped(corpus, args.section)
    if not entries:
        raise DictionaryError(f"No entries in section {args.section!r}.")

    entry = random.choice(entries)
    if args.json:
        print(render.entry_json(entry))
        return 0

    print(render.entry_full(entry, colour=_colour(args), width=args.width))
    return 0


def _run_sections(args: argparse.Namespace) -> int:
    corpus = _corpus()
    for section_id, meta in corpus.sections.items():
        count = len(corpus.in_section(section_id))
        title = meta.get("title", section_id)
        print(f"{section_id:24} {title:32} {count:>4} entries")
    print(f"{'':24} {'total':32} {len(corpus.entries):>4} entries")
    return 0


def _run_serve(args: argparse.Namespace) -> int:
    # Imported here, not at module scope: `thl-dict --help` should not pay for
    # loading the corpus and building the search indexes.
    from .serve import DEFAULT_PORT, serve

    return serve(
        args.port or DEFAULT_PORT,
        tuple(args.allow_origin),
        quiet=not args.verbose,
        site_root=Path(args.site) if args.site else None,
    )


_RUNNERS = {
    "search": _run_search,
    "define": _run_define,
    "list": _run_list,
    "random": _run_random,
    "sections": _run_sections,
    "serve": _run_serve,
}


# ---------------------------------------------------------------- entry point


def dispatch(args: argparse.Namespace) -> int:
    """Run an already-parsed namespace. Used by both front doors."""
    runner = _RUNNERS.get(getattr(args, "command", None))
    if runner is None:
        return _run_sections(args)
    return _guard(lambda: runner(args))


def _guard(fn) -> int:
    """Turn a library error into one line and an exit code.

    A traceback is the right output for a bug and the wrong output for "no entry
    called that". TermNotFound exits 2 rather than 1: it is a usage outcome, and
    scripts want to tell "you asked for something that isn't here" apart from
    "the dictionary itself is broken".
    """
    try:
        return fn()
    except TermNotFound as err:
        print(f"thl-dict: {err}", file=sys.stderr)
        return 2
    except DictionaryError as err:
        print(f"thl-dict: {err}", file=sys.stderr)
        return 1
    except BrokenPipeError:  # pragma: no cover - `thl-dict list | head`
        return 0
    except KeyboardInterrupt:  # pragma: no cover
        return 130


def main(argv: Sequence[str] | None = None) -> int:
    """The console-script entry point."""
    _configure_stdio()
    args = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()

    if not args:
        parser.print_help()
        return 0

    return dispatch(parser.parse_args(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
