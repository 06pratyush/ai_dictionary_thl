#!/usr/bin/env python3
"""Catch the number-one local-model defect: an import that does not exist.

Usage: python .orchestrator/imports.py <file.py> [--package <dir>]

Relative imports are resolved against the package directory rather than
importlib, because a module inside a package being written right now is not
importable from here yet.
"""
from __future__ import annotations

import ast
import importlib
import importlib.util
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path.cwd()))

STDLIB = set(sys.stdlib_module_names)



def check_names(tree: ast.AST, package: str) -> list[str]:
    """Confirm each `from <first-party module> import name` actually resolves.

    The module-level check above only proves the module exists. A model that
    writes `from x.errors import FrozenInstanceError` -- a real module, a name
    that lives in `dataclasses` -- passes it and then fails at collection time.
    Importing the module and checking the attribute closes that.

    Only first-party modules are imported: pulling in an arbitrary third-party
    package to introspect it would run its import side effects.
    """
    missing: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.level:
            continue
        if not node.module or not node.module.split(".")[0] == package:
            continue
        try:
            module = importlib.import_module(node.module)
        except Exception as exc:  # noqa: BLE001 - report, do not crash the gate
            missing.append(f"{node.module} (import failed: {exc})")
            continue
        for alias in node.names:
            if alias.name != "*" and not hasattr(module, alias.name):
                missing.append(f"{node.module}.{alias.name}")
    return missing


def main(path: str, package_root: str | None) -> int:
    source = pathlib.Path(path).read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        print(f"SYNTAX_ERROR line {exc.lineno}: {exc.msg}")
        return 1

    absolute: set[str] = set()
    relative: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            absolute |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.module:
                relative.add(node.module.split(".")[0])
            elif node.module:
                absolute.add(node.module.split(".")[0])

    bad = [
        name for name in absolute
        if name not in STDLIB and importlib.util.find_spec(name) is None
    ]

    if package_root:
        root = pathlib.Path(package_root)
        for name in relative:
            if not (root / f"{name}.py").exists() and not (root / name).is_dir():
                bad.append(f".{name}")

    if package_root:
        bad += check_names(tree, pathlib.Path(package_root).name)

    if bad:
        print("HALLUCINATED_OR_MISSING_IMPORTS: " + ", ".join(sorted(bad)))
        return 1
    return 0


if __name__ == "__main__":
    pkg = None
    if "--package" in sys.argv:
        pkg = sys.argv[sys.argv.index("--package") + 1]
    sys.exit(main(sys.argv[1], pkg))
