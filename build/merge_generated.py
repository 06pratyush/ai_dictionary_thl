#!/usr/bin/env python3
"""Merge locally-generated entries into a corpus, after normalising them.

Generated entries are structurally close but not clean: models omit fields,
echo the headword into "variants", and drift on enum spelling. Everything this
script repairs is deterministic. Anything it cannot repair mechanically is
reported and left out, so a defective entry never reaches the corpus silently.

Usage:
    python build/merge_generated.py <generated-dir> <corpus.json> [--apply]
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validate import (  # noqa: E402
    REQUIRED_FIELDS, POS_VALUES, PROXIMITY, POLARITY, Report,
    check_entry, check_definitions,
)

DEFAULTS = {
    "syllables": "", "ipa": "", "pos": "noun", "tags": [], "abbr": [],
    "inflections": [], "variants": [], "formula": None,
    "etymology": "[Origin obscure]", "firstAttested": "", "synonyms": [],
    "antonyms": [], "related": [], "citations": [], "frequency": 50,
    "opacity": None, "flags": [],
}

SLUGIFY = re.compile(r"[^a-z0-9]+")

# Rule 517 forbids publishing a speculative origin as fact. The local model
# reliably produces one of two failure modes here: contentless filler ("a
# descriptive compound term combining X and Y"), or a confidently wrong
# derivation — it gave "loss" an Old French root when the word is Old English.
# Neither is detectable per-entry, so any etymology matching these shapes is
# replaced with the honest marker and queued for a human to write.
ETYMOLOGY_FILLER = re.compile(
    r"descriptive compound|a blend of|combining\s+'|combining\s+\"|"
    r"coined in the (context|field) of|derived from the (words|terms)\s|"
    r"portmanteau of|self-explanatory|straightforward combination",
    re.I,
)


def slugify(value):
    return SLUGIFY.sub("-", str(value).lower()).strip("-")


def repair(entry):
    """Deterministic normalisation only. Never invents meaning."""
    notes = []

    for field, default in DEFAULTS.items():
        if entry.get(field) is None and field != "formula" and field != "opacity":
            entry[field] = default
            notes.append(f"filled missing '{field}'")
        elif field not in entry:
            entry[field] = default
            notes.append(f"filled missing '{field}'")

    # Rule 106: the headword is not one of its own variants.
    term_lower = entry["term"].lower()
    variants = [v for v in entry["variants"] if v.lower() != term_lower]
    if len(variants) != len(entry["variants"]):
        notes.append("dropped headword from variants")
    entry["variants"] = variants

    if entry.get("pos") not in POS_VALUES:
        entry["pos"] = str(entry.get("pos", "noun")).lower().strip()
        if entry["pos"] not in POS_VALUES:
            entry["pos"] = "noun"
            notes.append("normalised part of speech to 'noun'")

    # Enum casing drifts; the value itself is almost always right.
    for synonym in entry.get("synonyms") or []:
        value = str(synonym.get("proximity", "")).capitalize()
        if value not in PROXIMITY:
            value = "Near"
            notes.append("defaulted synonym proximity to 'Near'")
        synonym["proximity"] = value
    for antonym in entry.get("antonyms") or []:
        value = str(antonym.get("polarity", "")).capitalize()
        if value not in POLARITY:
            value = "Relational"
            notes.append("defaulted antonym polarity to 'Relational'")
        antonym["polarity"] = value

    # Rule 604: cross-references must be slugs, not prose.
    related = []
    for item in entry.get("related") or []:
        slug = slugify(item)
        if slug and slug not in related:
            related.append(slug)
    if related != entry.get("related"):
        notes.append("slugified related entries")
    entry["related"] = related

    frequency = entry.get("frequency")
    if not isinstance(frequency, int):
        try:
            entry["frequency"] = int(float(frequency))
            notes.append("coerced frequency to int")
        except (TypeError, ValueError):
            entry["frequency"] = 50
            notes.append("defaulted frequency to 50")
    entry["frequency"] = max(0, min(100, entry["frequency"]))

    if entry.get("opacity") not in (None, 1, 2, 3):
        entry["opacity"] = None
        notes.append("cleared invalid opacity")

    # Rule 517.
    etymology = (entry.get("etymology") or "").strip()
    if not etymology or ETYMOLOGY_FILLER.search(etymology):
        entry["etymology"] = "[Origin obscure]"
        notes.append("QUARANTINED etymology — needs an authored origin")

    # Rule 503: casing and terminal punctuation of the definition.
    for definition in entry.get("definitions") or []:
        text = (definition.get("text") or "").strip()
        if text:
            if text[0].isupper() and not text.split()[0].isupper():
                text = text[0].lower() + text[1:]
                notes.append("lowercased definition opening")
            if not text.endswith("."):
                text += "."
                notes.append("added terminal period")
        definition["text"] = text
        definition["example"] = (definition.get("example") or "").strip()

    # Reorder to the canonical field order so diffs stay readable.
    return {field: entry[field] for field in REQUIRED_FIELDS if field in entry}, notes


def main(gen_dir, corpus_path, apply_changes):
    with open(corpus_path, encoding="utf-8") as fh:
        corpus = json.load(fh)
    existing = {entry["slug"] for entry in corpus["entries"]}

    accepted, rejected = [], []
    for name in sorted(os.listdir(gen_dir)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(gen_dir, name), encoding="utf-8") as fh:
            entry = json.load(fh)
        if entry.get("slug") in existing:
            continue

        entry, notes = repair(entry)
        report = Report()
        check_entry(entry, report, set(), set())

        if report.errors:
            rejected.append((entry.get("slug", name), report.errors))
            continue
        accepted.append((entry, notes, report.warnings))

    print(f"accepted {len(accepted)}, rejected {len(rejected)}\n")
    for slug, errors in rejected:
        print(f"REJECT {slug}")
        for error in errors:
            print(f"       {error}")
    quarantined = []
    for entry, notes, warnings in accepted:
        for warning in warnings:
            print(f"WARN   {warning}")
        if any("QUARANTINED" in note for note in notes):
            quarantined.append(entry["slug"])

    if quarantined:
        print(f"\n{len(quarantined)} etymologies quarantined as [Origin obscure]:")
        print("  " + ", ".join(quarantined))

    if apply_changes and accepted:
        corpus["entries"].extend(entry for entry, _, _ in accepted)
        corpus["entries"].sort(key=lambda x: x["lid"])
        with open(corpus_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(corpus, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"\nmerged {len(accepted)} entries into {os.path.basename(corpus_path)}")
    elif not apply_changes:
        print("\ndry run — pass --apply to write")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], "--apply" in sys.argv))
