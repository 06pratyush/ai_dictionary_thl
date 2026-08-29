from __future__ import annotations

import json

import pytest

from thehallucinatedlab_dictionary.corpus import load, ngram_class
from thehallucinatedlab_dictionary.errors import CorpusUnavailable


@pytest.fixture(scope="module")
def corpus():
    """The real corpora, as shipped inside the package.

    Loaded once for the whole module: index construction is the expensive part
    and none of these tests mutate it. The error-path tests below build their
    own broken files under tmp_path instead.
    """
    return load()


def test_load_both_sections_and_counts_reconcile(corpus):
    """Both corpora load, and the section counts account for every entry.

    Asserted as a relationship rather than a total: the corpus grows, and a
    test that hard-codes today's size fails on the next entry added.
    """
    assert set(corpus.sections) == {"ai-mathematics", "software-engineering"}

    per_section = [len(corpus.in_section(name)) for name in corpus.sections]
    assert all(count > 0 for count in per_section)
    assert sum(per_section) == len(corpus.entries)

def test_load_single_section(tmp_path):
    (tmp_path / "corpus.json").write_text(
        json.dumps(
            {
                "section": {"id": "ai-mathematics"},
                "entries": [
                    {
                        "lid": "AIM-00001",
                        "term": "gradient-descent",
                        "slug": "gradient-descent",
                        "definitions": [
                            {"id": 1, "text": "Finds the minimum of a function."}
                        ],
                    }
                ],
            }
        )
    )
    loaded_corpus = load(tmp_path / "corpus.json")
    assert len(loaded_corpus.entries) == 1
    assert len(loaded_corpus.sections) == 1

def test_load_missing_directory(tmp_path):
    with pytest.raises(CorpusUnavailable) as excinfo:
        load(tmp_path / "nonexistent")
    assert "Missing corpus file" in str(excinfo.value)

def test_load_malformed_json(tmp_path):
    (tmp_path / "corpus.json").write_text("malformed json")
    with pytest.raises(CorpusUnavailable) as excinfo:
        load(tmp_path / "corpus.json")
    assert "Malformed JSON" in str(excinfo.value)

def test_load_missing_entry(tmp_path):
    (tmp_path / "corpus.json").write_text(
        json.dumps(
            {
                "section": {"id": "ai-mathematics"},
                "entries": [
                    {"lid": "AIM-00001", "term": "gd", "slug": "gd"}
                ],
            }
        )
    )
    with pytest.raises(CorpusUnavailable) as excinfo:
        load(tmp_path / "corpus.json")
    assert "is missing" in str(excinfo.value)
    assert "definitions" in str(excinfo.value)

def test_by_slug_hit(corpus):
    entry = corpus.by_slug("gradient-descent")
    assert entry.lid == "AIM-00001"

def test_by_slug_miss(corpus):
    assert corpus.by_slug("nonexistent") is None

def test_by_lid_hit(corpus):
    entry = corpus.by_lid("AIM-00001")
    assert entry.slug == "gradient-descent"

def test_by_lid_miss(corpus):
    assert corpus.by_lid("nonexistent") is None

def test_in_section_hit_returns_only_that_section(corpus):
    entries = corpus.in_section("ai-mathematics")

    assert entries
    assert all(entry.section == "ai-mathematics" for entry in entries)
    assert {entry.slug for entry in entries} >= {"gradient-descent"}
    assert not any(entry.slug == "technical-debt" for entry in entries)

def test_in_section_miss(corpus):
    assert len(corpus.in_section("nonexistent")) == 0

def test_ngram_class_one_word():
    assert ngram_class("word") == "unigram"

def test_ngram_class_two_word():
    assert ngram_class("word1 word2") == "bigram"

def test_ngram_class_three_word():
    assert ngram_class("word1 word2 word3") == "polygram"

def test_ngram_class_hyphenated():
    assert ngram_class("word1-word2") == "bigram"

def test_entry_gloss_is_the_first_definition(corpus):
    entry = corpus.by_slug("gradient-descent")

    assert entry.gloss == entry.definitions[0].text
    assert entry.gloss.endswith(".")
    assert entry.gloss[0].islower()

def test_entry_url(corpus):
    entry = corpus.by_slug("gradient-descent")
    assert entry.url == "https://thehallucinatedlab.space/dictionary/terms/gradient-descent.html"

def test_entry_hashable_usable_in_a_set(corpus):
    """Entry hashes by identity, which is what lets the search engine index it.

    The engine puts entries in sets constantly; a value-based hash would raise
    TypeError on the dict-valued fields (formula, synonyms, citations).
    """
    first = corpus.by_slug("gradient-descent")
    second = corpus.by_slug("technical-debt")

    assert isinstance(hash(first), int)
    assert len({first, second, first}) == 2
    assert corpus.by_slug("gradient-descent") is first



def test_entry_frozen(corpus):
    entry = corpus.by_slug("gradient-descent")
    with pytest.raises(AttributeError):
        entry.lid = "new-lid"

def test_definition_frozen(corpus):
    entry = corpus.by_slug("gradient-descent")
    definition = entry.definitions[0]
    with pytest.raises(AttributeError):
        definition.text = "new-text"
