#!/usr/bin/env python3
"""Strip prose, markdown fences and terminal control codes so only the payload
lands on disk.

`ollama run` emits ANSI cursor-movement and erase-line sequences even when its
stdout is redirected, and it hard-wraps at the terminal width. Inside a JSON
string literal that wrap becomes a raw newline, which is an invalid control
character. Both are repaired here rather than in every caller.
"""
import re
import sys

ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b[()][A-B]|[\r\x07\x08]")


def unwrap_strings(text):
    """Join lines that the terminal broke in the middle of a quoted string."""
    out = []
    in_string = False
    escaped = False
    for ch in text:
        if escaped:
            escaped = False
            out.append(ch)
            continue
        if ch == "\\":
            escaped = True
            out.append(ch)
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if ch == "\n" and in_string:
            # Collapse the wrap into a single space; the model did not intend
            # a line break here.
            if out and out[-1] != " ":
                out.append(" ")
            continue
        out.append(ch)
    return "".join(out)


VALID_ESCAPE = set('"\\/bfnrtu')


def escape_lone_backslashes(text):
    """Repair LaTeX written into JSON with single backslashes.

    Models reliably emit "\\theta" as \theta, which is an invalid JSON escape.
    A backslash not followed by one of the eight legal escape characters can
    only have been meant literally, so it is doubled.
    """
    out = []
    in_string = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '"' and (not out or out[-1] != "\\" or _escaped_quote(out)):
            in_string = not in_string
            out.append(ch)
            i += 1
            continue
        if ch == "\\" and in_string:
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if nxt in VALID_ESCAPE:
                out.append(ch)
                out.append(nxt)
                i += 2
                continue
            out.append("\\\\")
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _escaped_quote(out):
    """True when the trailing backslash run in `out` is itself escaped."""
    n = 0
    for ch in reversed(out):
        if ch != "\\":
            break
        n += 1
    return n % 2 == 0


def main(src, dest):
    raw = open(src, encoding="utf-8", errors="replace").read()
    raw = ANSI.sub("", raw)
    blocks = re.findall(r"```(?:[a-zA-Z0-9+#-]*)\n(.*?)```", raw, re.S)
    out = blocks[0] if blocks else raw
    if dest.endswith(".json"):
        out = unwrap_strings(out)
        out = re.sub(r"[ \t]+", " ", out)
        out = escape_lone_backslashes(out)
    open(dest, "w", encoding="utf-8").write(out.rstrip() + "\n")
    print(f"EXTRACTED_LINES={len(out.splitlines())} BLOCKS_FOUND={len(blocks)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
