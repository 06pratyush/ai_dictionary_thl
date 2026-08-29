"""Mount point for the main toolkit's ``thl`` command.

Installing this wheel is the only step needed to make ``thl dict`` work. The
toolkit reads the ``thehallucinatedlab.commands`` entry-point group when it
builds its parser and mounts whatever it finds, so neither package has to know
the other exists at build time and ``pip install thehallucinatedlab`` stays as
small as it is.

The toolkit calls::

    add_subparser(pipelines)   # while building its parser
    run_parsed(args)           # when `thl dict ...` is invoked

Both are thin: the real parser lives in cli.py, so ``thl dict search`` and
``thl-dict search`` cannot drift apart. Everything heavy is imported inside the
functions rather than at module scope, because the toolkit imports this module
merely to build ``thl --help``.
"""

from __future__ import annotations

import argparse


def add_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Attach the dictionary's commands as `thl dict`.

    Args:
        subparsers: The toolkit's top-level subparser action.

    Returns:
        The parser that was added, so the caller can inspect it.
    """
    from .cli import attach_commands

    parser = subparsers.add_parser(
        "dict",
        help="look words up in the lab dictionary; bare `thl dict` lists the sections",
        description="The Hallucinated Lab dictionary — AI, mathematics and "
                    "software engineering.",
    )
    attach_commands(parser)
    return parser


def run_parsed(args: argparse.Namespace) -> int:
    """Run an already-parsed `thl dict ...` invocation.

    Returns:
        The process exit code: 0 success, 1 a library error, 2 usage or
        term-not-found.
    """
    from .cli import dispatch

    return dispatch(args)
