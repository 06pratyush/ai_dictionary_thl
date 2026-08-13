#!/usr/bin/env python3
"""Minimal structural gate for the static pages: well-formedness of tags we care
about, exactly one <h1>, and no unresolved template placeholders."""
import re, sys
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


class Check(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors, self.h1 = [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag == "h1":
            self.h1 += 1
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"line {self.getpos()[0]}: stray </{tag}>")
            return
        open_tag, line = self.stack.pop()
        if open_tag != tag:
            self.errors.append(
                f"line {self.getpos()[0]}: </{tag}> closes <{open_tag}> opened at line {line}")


def main(path):
    src = open(path, encoding="utf-8").read()
    c = Check()
    c.feed(src)
    c.close()
    for tag, line in c.stack:
        c.errors.append(f"line {line}: <{tag}> never closed")
    if c.h1 != 1:
        c.errors.append(f"expected exactly one <h1>, found {c.h1}")
    for placeholder in re.findall(r"\{\{[A-Z_]+\}\}", src):
        c.errors.append(f"unresolved placeholder {placeholder}")
    if c.errors:
        for e in c.errors[:20]:
            print(f"{path}: {e}")
        return 1
    print(f"{path}: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
