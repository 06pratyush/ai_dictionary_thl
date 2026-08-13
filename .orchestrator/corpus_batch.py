#!/usr/bin/env python3
"""Dispatch one delegation packet per term to the local model.

Batching eight entries into a single packet fails: the model drifts off the
schema partway through and truncates. One term per packet holds the schema and
finishes every time, and wall-clock on a local model is free.

Usage:
    python .orchestrator/corpus_batch.py <termlist.json> <output-dir>

The term list is a JSON array of {lid, term, slug, domain} objects. Output is
one <slug>.json per term, skipped if it already exists so the run is resumable.
"""
import json
import os
import re
import sys
import urllib.request

MODEL = os.environ.get("ORCH_CODER", "orch-reader")
ENDPOINT = "http://localhost:11434/api/generate"

EXEMPLAR = json.dumps({
    "lid": "AIM-00004",
    "term": "Eigenvector",
    "slug": "eigenvector",
    "syllables": "ei·gen·vec·tor",
    "ipa": "/ˈaɪɡənˌvɛktər/",
    "pos": "noun",
    "domain": "Linear Algebra",
    "tags": ["Core", "Foundational"],
    "abbr": [],
    "inflections": ["eigenvectors"],
    "variants": ["eigen vector"],
    "definitions": [{
        "id": 1,
        "context": "in linear algebra",
        "text": "a non-zero vector whose direction is unchanged by a given "
                "linear map, so the map merely rescales it by a constant factor.",
        "example": "The covariance matrix's leading eigenvector points along "
                   "the axis of greatest spread in the data."
    }],
    "formula": {
        "latex": "A\\\\mathbf{v} = \\\\lambda \\\\mathbf{v}",
        "plain": "A v = lambda v",
        "note": "lambda is the eigenvalue: the factor by which the map "
                "stretches that direction."
    },
    "etymology": "A partial calque of German Eigenvektor, from eigen 'own, "
                 "characteristic'. Hilbert used Eigenwert in 1904.",
    "firstAttested": "1904",
    "synonyms": [{"term": "characteristic vector", "senseId": 1, "proximity": "Absolute"}],
    "antonyms": [],
    "related": ["eigenvalue", "principal-component-analysis"],
    "citations": [{
        "label": "Strang, G. (2016). Introduction to Linear Algebra, 5th ed., ch. 6.",
        "source": "Wellesley-Cambridge Press.",
        "url": ""
    }],
    "frequency": 84,
    "opacity": None,
    "flags": []
}, indent=2, ensure_ascii=False)

PACKET = """ROLE
You are a local lexicographer executing one narrowly scoped task.
You have no access to the repository. Everything you need is below.

TASK
Write exactly ONE JSON dictionary entry for the term "{term}".

CONTEXT (authoritative - do not invent anything outside this)
This is a complete, correct entry. Copy its field names, field order, and
writing style exactly. Yours must have the same 22 fields in the same order.

{exemplar}

The entry you write must use exactly these values, unchanged:
  "lid":    "{lid}"
  "term":   "{term}"
  "slug":   "{slug}"
  "domain": "{domain}"

STEPS
1. Write the "definitions" array first. One or two senses, no more.
2. Write "text" so it could replace the term in a sentence.
3. Write one "example" sentence per sense that uses the term naturally.
4. Fill "formula" with the standard equation, or set it to null if there is none.
5. Fill the remaining fields.

CONSTRAINTS - violating any of these fails the task
- Output ONE JSON object. Not an array. Not multiple objects.
- BANNED WORDS. The "text" of a definition must not contain any of these words,
  in any form, singular or plural: {banned}
  These are the words of the headword itself. A definition that reuses them is
  circular and fails. Define the idea from scratch using different vocabulary.
  Bad:  "Loss Function" -> "a function that measures the loss of a model"
  Good: "Loss Function" -> "a rule assigning a single number to how far a
        prediction sits from the target, which training seeks to make small"
- "text" must start with a lowercase letter and end with a period.
- Every definition must have a non-empty "example" that contains the term.
- "variants" must NOT contain "{term}" itself - only genuine alternate
  spellings or spacings. Use [] if there are none.
- "proximity" is exactly "Absolute" or "Near".
- "polarity" is exactly "Complementary", "Gradable" or "Relational".
- Every string in "related" is lowercase-hyphenated, like "loss-function".
- "frequency" is an integer 0-100. "opacity" is 1, 2, 3 or null.
- In LaTeX, write every backslash as a doubled backslash.
- "etymology" must trace the actual word origin - the language, root, and who
  coined it. Do NOT write "a blend of X and Y" or "a descriptive compound".
  If you do not know the origin, write exactly: [Origin obscure]
- Cite only sources you are confident exist. Set "url" to "" unless you are
  certain of the DOI or arXiv link.
- Do not add fields. Do not remove fields. Do not reorder fields.
- Do not write explanations, apologies, or preamble.

ACCEPTANCE CRITERIA
- Output parses as a single JSON object with all 22 fields.
- The definition text does not contain the headword.
- Every definition has an example sentence containing the term.

OUTPUT FORMAT
Return only the JSON object. Nothing before it. Nothing after it.
"""


def banned_words(term):
    """Spell out the words a definition may not reuse (Rule 502).

    Naming the constraint abstractly is not enough — the model restated the
    headword in roughly two entries in five. Enumerating the actual words, with
    a worked bad/good pair, gives it something checkable.
    """
    skip = {"of", "the", "a", "an", "in", "on", "to", "and", "or"}
    words = [w for w in re.findall(r"[A-Za-z]+", term) if w.lower() not in skip]
    return ", ".join(f'"{w.lower()}"' for w in words)


def dispatch(entry):
    prompt = PACKET.format(
        term=entry["term"], lid=entry["lid"], slug=entry["slug"],
        domain=entry["domain"], exemplar=EXEMPLAR,
        banned=banned_words(entry["term"]),
    )
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "8h",
        "format": "json",
        "options": {"temperature": 0.2},
    }).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as resp:
        envelope = json.load(resp)
    if "error" in envelope:
        raise RuntimeError(envelope["error"])
    return envelope.get("response", "")


def main(termlist_path, out_dir):
    terms = json.load(open(termlist_path, encoding="utf-8"))
    os.makedirs(out_dir, exist_ok=True)
    ok = fail = skip = 0

    for entry in terms:
        dest = os.path.join(out_dir, f"{entry['slug']}.json")
        if os.path.exists(dest):
            skip += 1
            continue
        try:
            raw = dispatch(entry)
            parsed = json.loads(raw)
        except Exception as exc:  # noqa: BLE001 - log and continue the batch
            print(f"FAIL {entry['slug']}: {type(exc).__name__}: {exc}", flush=True)
            fail += 1
            continue
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(parsed, fh, indent=2, ensure_ascii=False)
        ok += 1
        print(f"OK   {entry['slug']}", flush=True)

    print(f"DONE ok={ok} fail={fail} skip={skip}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
