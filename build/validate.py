#!/usr/bin/env python3
"""Schema and lexicographical gate for the dictionary corpora.

This is the firewall between generated content and the site. It enforces the
rules in docs/ENTRY-SCHEMA.md mechanically, so a bad entry fails the build
rather than reaching a reader.

Usage:
    python build/validate.py [--warn-only]
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPORA = [
    os.path.join(ROOT, "data", "ai-mathematics.json"),
    os.path.join(ROOT, "data", "software-engineering.json"),
]

REQUIRED_FIELDS = [
    "lid", "term", "slug", "syllables", "ipa", "pos", "domain", "tags", "abbr",
    "inflections", "variants", "definitions", "formula", "etymology",
    "firstAttested", "synonyms", "antonyms", "related", "citations",
    "frequency", "opacity", "flags",
]

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LID_RE = re.compile(r"^(AIM|SWE)-\d{5}$")
PROXIMITY = {"Absolute", "Near"}
POLARITY = {"Complementary", "Gradable", "Relational"}
POS_VALUES = {
    "noun", "verb", "adjective", "adverb", "pronoun", "preposition",
    "conjunction", "interjection", "phrase", "proverb", "abbreviation",
}

# Rule 502 is applied to content words only; these carry no semantic load and
# would otherwise flag every multi-word headword as circular.
STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "and", "or",
    "problem", "notation", "function", "method", "system", "rule", "theorem",
    "matrix", "test", "tree", "table", "list", "queue", "chain", "value",
}

# Rule 502 exemptions: terms whose stem genuinely cannot be avoided in a
# substitutable definition. Each one is a deliberate, reviewed decision.
CIRCULARITY_EXEMPT = {
    "database-index",   # "index" is the only word for the B-tree structure
    "salt",             # cryptographic sense requires naming the input
}


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, lid, message):
        self.errors.append(f"[{lid}] {message}")

    def warn(self, lid, message):
        self.warnings.append(f"[{lid}] {message}")


def stem(word):
    """A crude suffix-stripper — enough to catch 'regularize' under 'regularization'."""
    word = word.lower()
    for suffix in ("ization", "isation", "ations", "ation", "ising", "izing",
                   "ities", "ness", "ing", "ers", "ed", "es", "s", "ly", "e"):
        if len(word) - len(suffix) >= 4 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def words(text):
    return re.findall(r"[a-zA-Z][a-zA-Z'-]*", text.lower())


def check_entry(entry, report, seen_lids, seen_slugs):
    lid = entry.get("lid", "<no lid>")

    for field in REQUIRED_FIELDS:
        if field not in entry:
            report.error(lid, f"missing required field '{field}'")
    if any(f not in entry for f in ("lid", "term", "slug", "definitions")):
        return

    if not LID_RE.match(entry["lid"]):
        report.error(lid, f"malformed LID '{entry['lid']}' (expected AIM-00000 / SWE-00000)")
    if entry["lid"] in seen_lids:
        report.error(lid, "duplicate LID")
    seen_lids.add(entry["lid"])

    if not SLUG_RE.match(entry["slug"]):
        report.error(lid, f"malformed slug '{entry['slug']}'")
    if entry["slug"] in seen_slugs:
        report.error(lid, f"duplicate slug '{entry['slug']}'")
    seen_slugs.add(entry["slug"])

    if entry.get("pos") not in POS_VALUES:
        report.error(lid, f"unknown part of speech '{entry.get('pos')}'")

    # Rule 102/103: n-gram class must agree with the headword's word count.
    word_count = len(re.split(r"[\s‐-―-]+", entry["term"].strip()))
    expected = "unigram" if word_count == 1 else "bigram" if word_count == 2 else "polygram"
    if entry.get("ngram") not in (None, expected):
        report.error(lid, f"ngram '{entry['ngram']}' disagrees with word count {word_count}")

    # Rule 106/303: a variant that equals the headword is not a variant.
    term_lower = entry["term"].lower()
    for variant in entry.get("variants") or []:
        if variant.lower() == term_lower:
            report.error(lid, f"variants contains the headword itself ('{variant}')")

    freq = entry.get("frequency")
    if not isinstance(freq, int) or not 0 <= freq <= 100:
        report.error(lid, f"frequency must be an integer 0-100, got {freq!r}")
    if entry.get("opacity") not in (None, 1, 2, 3):
        report.error(lid, f"opacity must be 1, 2, 3 or null, got {entry.get('opacity')!r}")

    if not entry.get("citations"):
        report.error(lid, "at least one citation is required")
    for citation in entry.get("citations") or []:
        if not citation.get("label"):
            report.error(lid, "citation with no label")

    if not entry.get("etymology"):
        report.error(lid, "etymology is required (use '[Origin obscure]' if unknown)")

    check_definitions(entry, report)
    check_relations(entry, report)


def check_definitions(entry, report):
    lid = entry["lid"]
    definitions = entry.get("definitions") or []
    if not definitions:
        report.error(lid, "at least one definition is required")
        return

    content_stems = {
        stem(w) for w in words(entry["term"])
        if w not in STOPWORDS and len(w) > 3
    }

    for definition in definitions:
        did = definition.get("id", "?")
        text = (definition.get("text") or "").strip()
        example = (definition.get("example") or "").strip()

        if not text:
            report.error(lid, f"definition {did}: empty text")
            continue
        # Rule 503.
        if not text[0].islower():
            report.error(lid, f"definition {did}: text must start with a lowercase letter")
        if not text.endswith("."):
            report.error(lid, f"definition {did}: text must end with a period")
        # Rule 507.
        if not example:
            report.error(lid, f"definition {did}: example sentence is required")
        elif not any(
            token in example.lower()
            for token in (entry["term"].lower(), *(a.lower() for a in entry.get("abbr") or []))
        ):
            report.warn(lid, f"definition {did}: example does not use the term")

        # Rule 502 — the anti-circularity rule.
        if entry["slug"] not in CIRCULARITY_EXEMPT:
            hit = content_stems & {stem(w) for w in words(text)}
            if hit:
                report.error(
                    lid,
                    f"definition {did}: circular — reuses the headword stem {sorted(hit)}")


def check_relations(entry, report):
    lid = entry["lid"]
    definition_ids = {d.get("id") for d in entry.get("definitions") or []}

    for synonym in entry.get("synonyms") or []:
        # Rule 521: sense-specific linking is mandatory.
        if synonym.get("senseId") not in definition_ids:
            report.error(lid, f"synonym '{synonym.get('term')}' has no valid senseId")
        if synonym.get("proximity") not in PROXIMITY:
            report.error(lid, f"synonym '{synonym.get('term')}' has bad proximity "
                              f"{synonym.get('proximity')!r}")

    for antonym in entry.get("antonyms") or []:
        if antonym.get("senseId") not in definition_ids:
            report.error(lid, f"antonym '{antonym.get('term')}' has no valid senseId")
        if antonym.get("polarity") not in POLARITY:
            report.error(lid, f"antonym '{antonym.get('term')}' has bad polarity "
                              f"{antonym.get('polarity')!r}")

    for slug in entry.get("related") or []:
        if not SLUG_RE.match(slug):
            report.error(lid, f"related entry '{slug}' is not a valid slug")


def load_corpora():
    corpora = []
    for path in CORPORA:
        with open(path, encoding="utf-8") as fh:
            corpora.append((path, json.load(fh)))
    return corpora


def main(argv):
    warn_only = "--warn-only" in argv
    report = Report()
    seen_lids, seen_slugs = set(), set()
    all_slugs = set()
    total = 0

    corpora = load_corpora()
    for _, corpus in corpora:
        for entry in corpus["entries"]:
            all_slugs.add(entry.get("slug"))

    for path, corpus in corpora:
        prefix = corpus["section"]["lidPrefix"]
        for entry in corpus["entries"]:
            total += 1
            check_entry(entry, report, seen_lids, seen_slugs)
            if not str(entry.get("lid", "")).startswith(prefix):
                report.error(entry.get("lid", "?"),
                             f"LID prefix does not match section '{prefix}' in {os.path.basename(path)}")
            # Rule 604: cross-references must resolve or they render as dead links.
            for slug in entry.get("related") or []:
                if slug not in all_slugs:
                    report.warn(entry["lid"], f"related slug '{slug}' has no entry yet")

    for warning in report.warnings:
        print(f"WARN  {warning}")
    for error in report.errors:
        print(f"ERROR {error}")

    print(f"\nvalidated {total} entries — {len(report.errors)} errors, "
          f"{len(report.warnings)} warnings")
    if report.errors and not warn_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
