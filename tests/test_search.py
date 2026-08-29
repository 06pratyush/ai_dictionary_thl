"""Search engine conformance.

Mirrors tests/search-engine.test.mjs case for case. The Python engine and the
JavaScript one must not disagree about what a query means, and the cheapest way
to keep that true is to write both suites from the same list.

Each test names the Series 700 rule it protects.
"""

from __future__ import annotations

import pytest

from thehallucinatedlab_dictionary.corpus import load
from thehallucinatedlab_dictionary.search import (
    SearchEngine,
    damerau_levenshtein,
    edit_budget,
    key_proximity,
    metaphone,
    normalize,
    parse_query,
    tokenize,
)


@pytest.fixture(scope="module")
def engine() -> SearchEngine:
    """One engine over the shipped corpora; index construction is the slow part."""
    return SearchEngine(load())


def slugs(results) -> list[str]:
    return [hit.entry.slug for hit in results.hits]


# -- Series 70.A — normalization ------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("GRADIENT", "gradient"),                    # Rule 701
        ("Bayes' Theorem", "bayes theorem"),         # Rule 703
        ("café", "cafe"),                            # Rule 702
        ("résumé", "resume"),                        # Rule 702
        ("mother-in-law", "mother in law"),          # Rule 703
        ("   gradient    descent  ", "gradient descent"),  # Rule 704
        ("", ""),
    ],
)
def test_normalize_folds_case_diacritics_and_space(raw, expected):
    assert normalize(raw) == expected


def test_normalize_case_fold_precedes_the_character_filter():
    """The filter is [^a-z0-9], so folding must happen first.

    Reversed, every capital letter is deleted rather than lowered and a
    capitalised query normalises to the empty string — which returns no results
    for anything typed at the start of a sentence.
    """
    assert normalize("Gradient Descent") == normalize("gradient descent")
    assert normalize("ENTROPY") != ""


def test_tokenize_empty_string_returns_no_tokens():
    assert tokenize("") == []
    assert tokenize("   ") == []


def test_stop_words_dropped_from_polygram_query_only():
    """Rule 705."""
    long_query = parse_query("the arrangement of the nodes")
    assert "the" not in long_query.terms
    assert "arrangement" in long_query.terms

    short_query = parse_query("the")
    assert short_query.terms == ("the",)


# -- Series 70.B — fuzzy matching -----------------------------------


@pytest.mark.parametrize("length,expected", [(4, 1), (7, 2), (12, 3)])
def test_edit_budget_scales_with_word_length(length, expected):
    """Rule 706."""
    assert edit_budget(length) == expected


def test_damerau_levenshtein_transposition_costs_one():
    """Rule 707: adjacent transposition is the commonest typing error."""
    assert damerau_levenshtein("etnropy", "entropy") == 1
    assert damerau_levenshtein("hte", "the") == 1


def test_damerau_levenshtein_identical_strings_cost_nothing():
    assert damerau_levenshtein("abc", "abc") == 0


def test_damerau_levenshtein_empty_operand_costs_the_other_length():
    assert damerau_levenshtein("", "abc") == 3
    assert damerau_levenshtein("abc", "") == 3


def test_damerau_levenshtein_ceiling_short_circuits():
    """A distance past the ceiling need not be computed exactly, only exceeded."""
    assert damerau_levenshtein("abcdefgh", "zzzzzzzz", 2) > 2


def test_key_proximity_adjacent_keys_cost_less_than_distant():
    """Rule 709."""
    assert key_proximity("a", "a") == 0
    assert key_proximity("a", "s") < key_proximity("a", "m")


def test_key_proximity_unknown_character_costs_full():
    assert key_proximity("a", "!") == 1


def test_metaphone_maps_sound_alikes_together():
    """Rule 708."""
    assert metaphone("phlegm") == metaphone("flegm")
    assert metaphone("") == ""


# -- Series 70.E — query modifiers ----------------------------------


def test_quoted_phrase_is_marked_exact():
    """Rule 721."""
    query = parse_query('"gradient descent"')
    assert query.exact is True
    assert query.phrases == ("gradient descent",)


def test_not_operator_collects_exclusions():
    """Rule 722."""
    assert parse_query("tensor NOT physics").excluded == ("physics",)


def test_and_operator_sets_the_mode():
    """Rule 722."""
    assert parse_query("gradient AND descent").mode == "AND"


def test_wildcard_token_compiles_to_a_pattern():
    """Rule 720."""
    query = parse_query("*ology")
    assert len(query.wildcards) == 1
    assert query.wildcards[0].match("topology")
    assert not query.wildcards[0].match("gradient")


def test_question_mark_matches_exactly_one_character():
    """Rule 720."""
    pattern = parse_query("entrop?").wildcards[0]
    assert pattern.match("entropy")
    assert not pattern.match("entropies")


def test_empty_query_parses_to_nothing():
    assert parse_query("").terms == ()
    assert parse_query("   ").raw == ""


# -- Series 70.C/D — indexing and ranking ---------------------------


def test_exact_headword_outranks_a_definition_mention(engine):
    """Rules 714 and 717."""
    results = engine.search("gradient")
    assert results.hits
    assert results.hits[0].entry.term == "Gradient Descent"


def test_search_is_case_insensitive(engine):
    """Rule 701, end to end."""
    assert engine.search("GRADIENT").hits[0].entry.slug == "gradient-descent"
    assert slugs(engine.search("Gradient")) == slugs(engine.search("gradient"))


def test_abbreviation_resolves_to_its_lemma(engine):
    """Rule 713."""
    assert engine.search("GD").hits[0].entry.slug == "gradient-descent"


def test_anchor_word_surfaces_its_multi_word_entry(engine):
    """Rule 716."""
    assert "gradient-descent" in slugs(engine.search("descent"))


def test_one_query_spans_both_sections(engine):
    """The whole point of a single search bar over two corpora."""
    sections = {hit.entry.section for hit in engine.search("function").hits}
    assert len(sections) == 2


def test_scope_confines_results_to_one_section(engine):
    results = engine.search("gradient", scope="software-engineering")
    assert all(hit.entry.section == "software-engineering" for hit in results.hits)


def test_no_entry_appears_twice_in_one_result_set(engine):
    """An entry reaches the same index key by several routes.

    Stored in a list rather than a set, it would appear once per route and its
    score would be multiplied by the same factor.
    """
    found = slugs(engine.search("gradient"))
    assert len(set(found)) == len(found)

    suggested = [entry.slug for entry in engine.suggest("gra")]
    assert len(set(suggested)) == len(suggested)


def test_misspelling_still_finds_its_entry(engine):
    """Rules 706-707."""
    assert "entropy" in slugs(engine.search("etnropy"))


def test_a_missed_query_offers_a_correction(engine):
    """Rule 601."""
    assert engine.search("etnropy").suggestion == "entropy"


def test_quoted_phrase_bypasses_fuzzy_matching(engine):
    """Rule 721: a typo inside quotes must not be corrected."""
    assert engine.search('"etnropy"').hits == ()


def test_not_excludes_matching_entries(engine):
    """Rule 722."""
    assert "gradient-descent" not in slugs(engine.search("gradient NOT descent"))


def test_and_requires_every_term(engine):
    """Rule 722."""
    assert "gradient-descent" in slugs(engine.search("gradient AND descent"))


def test_empty_query_returns_nothing_rather_than_everything(engine):
    assert engine.search("").total == 0
    assert engine.search("   ").total == 0


def test_results_are_capped_and_pageable(engine):
    """Rule 725."""
    first = engine.search("e", limit=2, offset=0)
    assert len(first.hits) <= 2
    if first.total > 2:
        second = engine.search("e", limit=2, offset=2)
        assert first.hits[0].entry.slug != second.hits[0].entry.slug


def test_hits_are_sorted_by_descending_score(engine):
    scores = [hit.score for hit in engine.search("gradient").hits]
    assert scores == sorted(scores, reverse=True)


def test_suggest_returns_prefix_matches(engine):
    """Rule 711."""
    assert "gradient-descent" in [entry.slug for entry in engine.suggest("gra")]


def test_suggest_on_empty_prefix_returns_nothing(engine):
    assert engine.suggest("") == []


def test_hits_carry_the_reason_they_matched(engine):
    """The reasons drive the badges the web UI renders on each result card."""
    top = engine.search("gradient").hits[0]
    assert top.reasons
    assert all(isinstance(reason, str) for reason in top.reasons)
