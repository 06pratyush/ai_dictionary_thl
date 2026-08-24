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


# ---------------------------------------------------------------- topic page
#
# docs/TOPIC-PAGE-SPEC.md is the contract for every term page. Every entry
# added from this point carries a complete `topic` block, and the checks below
# are what make that true rather than aspirational.
#
# TOPIC_LEGACY is the migration allowlist: the entries that predate the spec.
# It only ever shrinks. Migrating an entry means authoring its topic block and
# deleting its slug from this list — never adding a slug to it.

TOPIC_LEGACY = {
    "acid", "activation-function", "attention-mechanism", "backpropagation",
    "bayes-theorem", "bias-variance-tradeoff", "big-o-notation",
    "cap-theorem", "cohesion", "convolutional-neural-network", "coupling",
    "cross-validation", "deadlock", "dependency-injection", "eigenvector",
    "embedding", "entropy", "eventual-consistency", "gradient-descent",
    "hash-table", "idempotence", "learning-rate", "loss-function",
    "markov-chain", "maximum-likelihood-estimation", "memoization", "mutex",
    "overfitting", "principal-component-analysis", "pure-function",
    "race-condition", "refactoring", "regularization",
    "reinforcement-learning", "softmax", "sql-injection", "technical-debt",
    "transformer", "yak-shaving",
}

DIFFICULTY = {"Beginner", "Intermediate", "Advanced"}
TOPIC_STATUS = {"Draft", "Published", "Needs Review"}
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Spec §0 plus the Required prose sections. A topic block that omits any of
# these is an incomplete topic page, not a partial one.
TOPIC_REQUIRED = [
    "category", "difficulty", "readingTime", "status", "datePublished",
    "dateUpdated", "author", "metaDescription", "quickTake", "formalStatement",
    "background", "deepDive", "revisions",
]

MAX_FORMAL_DEFINITIONS = 3
META_DESCRIPTION_RANGE = (150, 160)


def check_topic(entry, report, all_slugs):
    """Spec §0-§17. Enforced in full on every entry outside TOPIC_LEGACY."""
    lid = entry.get("lid", "<no lid>")
    data = entry.get("topic")
    legacy = entry.get("slug") in TOPIC_LEGACY

    if not data:
        if legacy:
            report.warn(lid, "no topic block yet — page renders derived fallbacks "
                             "(see GAP-05); migrate it and drop the slug from TOPIC_LEGACY")
        else:
            report.error(lid, "missing 'topic' block — every entry added after the "
                              "Topic Page Specification must carry one "
                              "(docs/TOPIC-PAGE-SPEC.md)")
        return

    if legacy:
        report.warn(lid, "has a topic block but is still listed in TOPIC_LEGACY — "
                         "remove the slug so the full spec is enforced on it")

    for field in TOPIC_REQUIRED:
        value = data.get(field)
        if value is None or (isinstance(value, (str, list, dict)) and not value):
            report.error(lid, f"topic.{field} is required by the spec and is empty")

    if data.get("difficulty") and data["difficulty"] not in DIFFICULTY:
        report.error(lid, f"topic.difficulty '{data['difficulty']}' not in {sorted(DIFFICULTY)}")
    if data.get("status") and data["status"] not in TOPIC_STATUS:
        report.error(lid, f"topic.status '{data['status']}' not in {sorted(TOPIC_STATUS)}")

    reading = data.get("readingTime")
    if reading is not None and (not isinstance(reading, int) or reading <= 0):
        report.error(lid, "topic.readingTime must be a positive whole number of minutes")

    for field in ("datePublished", "dateUpdated"):
        value = data.get(field)
        if value and not ISO_DATE_RE.match(str(value)):
            report.error(lid, f"topic.{field} '{value}' is not an ISO date")

    # Rule 04 on the parent site: descriptions are 50-155 there, but the spec
    # asks for a standalone answer at 150-160, which is the tighter constraint.
    description = data.get("metaDescription") or ""
    low, high = META_DESCRIPTION_RANGE
    if description and not low <= len(description) <= high:
        report.error(lid, f"topic.metaDescription is {len(description)} chars, "
                          f"expected {low}-{high}")

    # §2: at most three, and every reference marker must land on a real citation.
    sourced = data.get("formalDefinitions") or []
    if len(sourced) > MAX_FORMAL_DEFINITIONS:
        report.error(lid, f"topic.formalDefinitions has {len(sourced)} entries, "
                          f"the spec allows at most {MAX_FORMAL_DEFINITIONS}")
    citation_count = len(entry.get("citations") or [])
    for definition in sourced:
        if not definition.get("quote"):
            report.error(lid, "topic.formalDefinitions[] entry has no quote")
        ref = definition.get("ref")
        if ref is not None and not (isinstance(ref, int) and 1 <= ref <= citation_count):
            report.error(lid, f"topic.formalDefinitions[] ref {ref} does not point at "
                              f"a citation (entry has {citation_count})")

    # §6: a prerequisite that does not resolve is a dead link in the graph.
    for prerequisite in data.get("prerequisites") or []:
        slug = prerequisite.get("slug")
        if slug and slug not in all_slugs:
            report.warn(lid, f"topic.prerequisites slug '{slug}' has no entry yet")
        if not prerequisite.get("label") and not slug:
            report.error(lid, "topic.prerequisites[] entry has neither label nor slug")

    # §12 is the internal section. An external link there belongs in §13.
    for resource in data.get("moreResources") or []:
        href = resource.get("href", "")
        if href.startswith("http") and "thehallucinatedlab.space" not in href:
            report.error(lid, f"topic.moreResources href '{href}' is external — "
                              "external recommendations belong in furtherReading (§13)")

    # §14: these pairs become FAQPage structured data, so a blank half would
    # ship markup describing a question the page does not answer.
    for pair in data.get("faq") or []:
        if not pair.get("q") or not pair.get("a"):
            report.error(lid, "topic.faq[] pair is missing a question or an answer")

    # §16: the revision trail is what makes a correction visible.
    for revision in data.get("revisions") or []:
        if not revision.get("version") or not revision.get("change"):
            report.error(lid, "topic.revisions[] entry needs a version and a change")
        if revision.get("date") and not ISO_DATE_RE.match(str(revision["date"])):
            report.error(lid, f"topic.revisions[] date '{revision['date']}' is not an ISO date")


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
            check_topic(entry, report, all_slugs)
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

    migrated = sum(1 for _, corpus in corpora for entry in corpus["entries"]
                   if entry.get("topic"))
    print(f"\nvalidated {total} entries — {len(report.errors)} errors, "
          f"{len(report.warnings)} warnings")
    print(f"topic page spec: {migrated}/{total} migrated, "
          f"{len(TOPIC_LEGACY)} slugs still on the legacy allowlist")
    if report.errors and not warn_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
