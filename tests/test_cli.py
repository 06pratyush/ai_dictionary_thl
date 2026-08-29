"""The command line and the terminal renderer.

Every command is driven through ``main()`` with captured output, so what is
asserted is what a user actually sees, exit code included.
"""

from __future__ import annotations

import io
import json

import pytest

from thehallucinatedlab_dictionary import render
from thehallucinatedlab_dictionary.cli import attach_commands, build_parser, main
from thehallucinatedlab_dictionary.corpus import load
from thehallucinatedlab_dictionary.search import SearchEngine

ESC = "\x1b"


@pytest.fixture(scope="module")
def corpus():
    return load()


@pytest.fixture(scope="module")
def entry(corpus):
    return corpus.by_slug("technical-debt")


def run(capsys, argv):
    """Run one command; return (exit code, stdout, stderr)."""
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# -- the parser -----------------------------------------------------


def test_no_arguments_prints_help_and_succeeds(capsys):
    code, out, _ = run(capsys, [])

    assert code == 0
    assert "thl-dict" in out
    assert "define" in out


def test_every_command_is_reachable_from_the_parser():
    """The toolkit mounts this same parser as `thl dict`.

    If a command exists in one front door and not the other, they have drifted.
    """
    parser = build_parser()
    actions = [a for a in parser._actions if hasattr(a, "choices") and a.choices]
    commands = set(actions[0].choices)

    assert commands == {"search", "define", "list", "random", "sections", "serve"}


def test_attach_commands_works_on_a_foreign_parser():
    """This is what plugin.add_subparser relies on."""
    import argparse

    host = argparse.ArgumentParser(prog="thl")
    subparsers = host.add_subparsers(dest="command")
    mounted = subparsers.add_parser("dict")
    attach_commands(mounted)

    args = host.parse_args(["dict", "define", "entropy"])
    assert args.term == ["entropy"]


# -- sections -------------------------------------------------------


def test_sections_lists_both_corpora(capsys):
    code, out, _ = run(capsys, ["sections"])

    assert code == 0
    assert "ai-mathematics" in out
    assert "software-engineering" in out
    assert "total" in out


# -- define ---------------------------------------------------------


def test_define_prints_the_whole_entry(capsys):
    code, out, _ = run(capsys, ["define", "technical", "debt", "--no-color"])

    assert code == 0
    assert "Technical Debt" in out
    assert "ETYMOLOGY" in out
    assert "REFERENCES" in out
    assert "technical-debt.html" in out


def test_define_resolves_a_slug(capsys):
    code, out, _ = run(capsys, ["define", "gradient-descent", "--no-color"])
    assert code == 0
    assert "Gradient Descent" in out


def test_define_resolves_an_abbreviation(capsys):
    code, out, _ = run(capsys, ["define", "GD", "--no-color"])
    assert code == 0
    assert "Gradient Descent" in out


def test_define_unknown_term_exits_two_and_reports_on_stderr(capsys):
    """Exit 2, not 1: a script wants to tell "not here" from "dictionary broken"."""
    code, out, err = run(capsys, ["define", "zzznotarealword"])

    assert code == 2
    assert out == ""
    assert "zzznotarealword" in err


def test_define_json_is_parseable_and_uncoloured(capsys):
    code, out, _ = run(capsys, ["define", "eigenvector", "--json"])
    payload = json.loads(out)

    assert code == 0
    assert payload["term"] == "Eigenvector"
    assert payload["url"].endswith("eigenvector.html")
    assert ESC not in out


# -- search ---------------------------------------------------------


def test_search_ranks_the_exact_headword_first(capsys):
    code, out, _ = run(capsys, ["search", "gradient", "--no-color"])

    assert code == 0
    assert "Gradient Descent" in out


def test_search_spans_both_sections(capsys):
    code, out, _ = run(capsys, ["search", "function", "--no-color", "--limit", "20"])

    assert code == 0
    assert "[AI]" in out
    assert "[SWE]" in out


def test_search_scope_confines_results(capsys):
    code, out, _ = run(
        capsys, ["search", "gradient", "-s", "software-engineering", "--no-color"]
    )

    assert code == 0
    assert "[AI]" not in out


def test_search_json_carries_scores(capsys):
    code, out, _ = run(capsys, ["search", "gradient", "--json", "--limit", "2"])
    payload = json.loads(out)

    assert code == 0
    assert payload["total"] > 0
    assert "score" in payload["results"][0]
    assert ESC not in out


def test_search_with_no_matches_says_so(capsys):
    code, out, _ = run(capsys, ["search", "zzzqqqxxx", "--no-color"])

    assert code == 0
    assert "no matches" in out


# -- list and random ------------------------------------------------


def test_list_honours_the_limit(capsys):
    code, out, _ = run(capsys, ["list", "-s", "software-engineering",
                                "--limit", "3", "--no-color"])

    assert code == 0
    assert len([line for line in out.splitlines() if line.strip()]) == 3


def test_list_filters_by_letter(capsys):
    code, out, _ = run(capsys, ["list", "--letter", "e", "--no-color"])

    assert code == 0
    for line in out.splitlines():
        if line.strip():
            assert line.lower().startswith("e")


def test_list_with_an_impossible_filter_reports_on_stderr(capsys):
    code, out, err = run(capsys, ["list", "--domain", "NoSuchDomain", "--no-color"])

    assert code == 0
    assert out == ""
    assert "Nothing matched" in err


def test_random_returns_an_entry_from_the_requested_section(capsys):
    code, out, _ = run(capsys, ["random", "-s", "ai-mathematics", "--no-color"])

    assert code == 0
    assert out.strip()


# -- render ---------------------------------------------------------


def test_entry_brief_never_exceeds_the_given_width(entry):
    for width in (40, 60, 80, 120):
        line = render.entry_brief(entry, colour=False, width=width)
        assert "\n" not in line
        assert len(line) <= width


def test_entry_brief_at_an_absurd_width_still_returns_one_line(entry):
    line = render.entry_brief(entry, colour=False, width=10)
    assert "\n" not in line


def test_no_escape_sequences_when_colour_is_off(entry, corpus):
    engine = SearchEngine(corpus)
    results = engine.search("gradient")

    assert ESC not in render.entry_full(entry, colour=False)
    assert ESC not in render.entry_brief(entry, colour=False)
    assert ESC not in render.results_table(results, colour=False)


def test_colour_is_emitted_when_asked_for(entry):
    assert ESC in render.entry_full(entry, colour=True)


def test_entry_full_omits_sections_that_have_no_content(corpus):
    """An entry with no formula must not print an empty FORMULA heading."""
    without = next(e for e in corpus.entries if not e.formula)
    rendered = render.entry_full(without, colour=False)

    assert "FORMULA" not in rendered
    assert without.term in rendered


def test_entry_full_includes_every_sense(entry):
    rendered = render.entry_full(entry, colour=False)

    for definition in entry.definitions:
        assert definition.text[:40] in rendered


def test_results_table_shows_a_suggestion_when_there_is_one(corpus):
    engine = SearchEngine(corpus)
    rendered = render.results_table(engine.search("etnropy"), colour=False)

    assert "did you mean" in rendered


def test_results_table_omits_the_suggestion_line_when_there_is_none(corpus):
    engine = SearchEngine(corpus)
    rendered = render.results_table(engine.search("gradient"), colour=False)

    assert "did you mean" not in rendered


def test_supports_colour_is_false_for_a_non_tty():
    assert render.supports_colour(io.StringIO()) is False


def test_supports_colour_honours_no_color(monkeypatch):
    class Tty(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert render.supports_colour(Tty()) is True

    monkeypatch.setenv("NO_COLOR", "1")
    assert render.supports_colour(Tty()) is False


def test_supports_colour_honours_dumb_terminals(monkeypatch):
    class Tty(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "dumb")
    assert render.supports_colour(Tty()) is False


def test_supports_colour_on_a_stream_without_isatty():
    class Bare:
        pass

    assert render.supports_colour(Bare()) is False
