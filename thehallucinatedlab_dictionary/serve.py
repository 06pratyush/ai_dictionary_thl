"""The loopback bridge, and optionally the static site.

``thl-dict serve`` runs a small HTTP server on 127.0.0.1 so the dictionary is
reachable as JSON, and so the built site can be browsed without a separate
static server. Everything it exposes is read-only: there is no endpoint that
writes, uploads, or executes.

Deliberately stdlib only, for the same reason the toolkit's bridge is: this
exists so a local page can reach a local process, and a web framework in a
package whose dependency list is empty would cost more than it returns.

Retained rather than delegated. This is a network boundary, and §7.6 of the
protocol keeps those with me.

Security model, in the order that the work actually gets done:

1.  **The Host allowlist.** This is what survives DNS rebinding. An attacker
    who points evil.com at 127.0.0.1 makes their page *same-origin* with this
    server, and browsers omit Origin on same-origin GETs -- so an Origin check
    alone waves the request straight through. Host still tells the truth,
    because the browser sends the name it was asked to resolve.
2.  **The Origin allowlist.** Binding to loopback stops the *network* reaching
    this server; it does not stop another site the visitor has open, since
    their browser runs on this machine too.
3.  **Loopback binding.** 127.0.0.1 only, never 0.0.0.0.
4.  **A query cap.** The fuzzy matcher is O(query x vocabulary); an unbounded
    query string is a way to burn CPU on the machine you are trying to help.
5.  **Path containment on static files.** Every served path is resolved and
    confirmed to sit inside the site root, so no request can walk out of it.
"""

from __future__ import annotations

import json
import mimetypes
import re
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from . import __version__
from .corpus import Corpus, load
from .errors import DictionaryError
from .search import SearchEngine

DEFAULT_PORT = 8788
"""8787 belongs to the toolkit's own bridge. Colliding with it would make
whichever started second fail to bind, for no benefit."""

DEFAULT_ORIGINS = ("https://thehallucinatedlab.space",)
_LOCAL_ORIGIN = re.compile(r"^http://(?:localhost|127\.0\.0\.1)(?::\d+)?$")
_LOOPBACK_HOST = re.compile(r"^(?:127\.0\.0\.1|localhost|\[::1\])(?::\d+)?$", re.IGNORECASE)

MAX_QUERY_CHARS = 200
MAX_LIMIT = 100

_SLUG_PATH = re.compile(r"^/thl/v1/dict/term/([a-z0-9][a-z0-9-]*)/?$")


def host_allowed(host: str | None) -> bool:
    """Whether the Host header names this machine's loopback interface.

    A missing Host is allowed for the same reason a missing Origin is: HTTP/1.1
    requires one and every browser sends one, so the only clients affected are
    command-line tools, which are not the attack this defends against.
    """
    if host is None:
        return True
    return bool(_LOOPBACK_HOST.match(host.strip()))


def origin_allowed(origin: str | None, extra: tuple[str, ...] = ()) -> bool:
    """Whether a browser Origin may use this bridge.

    A missing Origin is allowed: curl and the test suite do not send one, and a
    request without one did not come from a page. What must never be allowed is
    an Origin that is present and unrecognised.
    """
    if origin is None:
        return True
    if origin in DEFAULT_ORIGINS or origin in extra:
        return True
    return bool(_LOCAL_ORIGIN.match(origin))


def _entry_payload(entry: Any) -> dict[str, Any]:
    """One entry as plain JSON-able data."""
    return {
        "lid": entry.lid,
        "term": entry.term,
        "slug": entry.slug,
        "section": entry.section,
        "domain": entry.domain,
        "pos": entry.pos,
        "ngram": entry.ngram,
        "syllables": entry.syllables,
        "ipa": entry.ipa,
        "tags": list(entry.tags),
        "flags": list(entry.flags),
        "abbr": list(entry.abbr),
        "inflections": list(entry.inflections),
        "variants": list(entry.variants),
        "definitions": [
            {"id": d.id, "context": d.context, "text": d.text, "example": d.example}
            for d in entry.definitions
        ],
        "formula": entry.formula,
        "etymology": entry.etymology,
        "firstAttested": entry.first_attested,
        "synonyms": [dict(s) for s in entry.synonyms],
        "antonyms": [dict(a) for a in entry.antonyms],
        "related": list(entry.related),
        "citations": [dict(c) for c in entry.citations],
        "frequency": entry.frequency,
        "opacity": entry.opacity,
        "url": entry.url,
    }


def capabilities(corpus: Corpus | None = None) -> dict[str, Any]:
    """What a caller needs to know before asking for anything."""
    corpus = corpus if corpus is not None else load()
    return {
        "name": "thehallucinatedlab-dictionary",
        "version": __version__,
        "entries": len(corpus.entries),
        "sections": {
            section_id: {
                "title": meta.get("title", section_id),
                "entries": len(corpus.in_section(section_id)),
            }
            for section_id, meta in corpus.sections.items()
        },
        "endpoints": [
            "/thl/v1/capabilities",
            "/thl/v1/dict/search",
            "/thl/v1/dict/term/<slug>",
            "/thl/v1/dict/sections",
        ],
        "origins": list(DEFAULT_ORIGINS),
    }


def _clamp_int(raw: str | None, default: int, low: int, high: int) -> int:
    """Read one integer query parameter.

    A query string can only carry text, so `limit=abc` is a well-formed
    parameter that int() then rejects. Falling back to the default rather than
    raising keeps a malformed URL from becoming a 500.
    """
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(low, min(high, value))


class BridgeHandler(BaseHTTPRequestHandler):
    """One request. Read-only: GET and OPTIONS, nothing else."""

    server_version = f"thl-dict/{__version__}"
    extra_origins: tuple[str, ...] = ()
    quiet = True
    corpus: Corpus | None = None
    engine: SearchEngine | None = None
    site_root: Path | None = None

    # Applied to the socket by StreamRequestHandler.setup(). Without it a client
    # that opens a connection and then stops sending holds its worker thread
    # forever, and enough of those starve the bridge.
    timeout = 30

    def log_message(self, fmt: str, *args: Any) -> None:
        if not self.quiet:
            super().log_message(fmt, *args)

    # -- gates ------------------------------------------------------

    def _origin(self) -> str | None:
        return self.headers.get("Origin")

    def _permitted(self) -> bool:
        """Host first: it is the one an attacker cannot forge."""
        if not host_allowed(self.headers.get("Host")):
            return False
        return origin_allowed(self._origin(), self.extra_origins)

    # -- writing ----------------------------------------------------

    def _cors(self, origin: str | None) -> None:
        if origin is None:
            return
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors(self._origin())
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self._cors(self._origin())
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _refuse(self) -> None:
        """No CORS headers on the way out.

        Sending them would let the calling page read the refusal, which tells an
        unrecognised origin that a bridge is here and what it is.
        """
        body = b'{"error":"origin not allowed"}'
        self.send_response(403)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # -- verbs ------------------------------------------------------

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's naming
        if not self._permitted():
            self._refuse()
            return
        self.send_response(204)
        self._cors(self._origin())
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        # Chromium will not let a public page reach a private address without
        # this on the preflight.
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if not self._permitted():
            self._refuse()
            return

        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        try:
            if path.rstrip("/") == "/thl/v1/capabilities":
                self._send_json(200, capabilities(self.corpus))
                return
            if path.rstrip("/") == "/thl/v1/dict/sections":
                self._send_json(200, {"sections": capabilities(self.corpus)["sections"]})
                return
            if path.rstrip("/") == "/thl/v1/dict/search":
                self._search(params)
                return
            match = _SLUG_PATH.match(path)
            if match:
                self._term(match.group(1))
                return
            self._static(path)
        except DictionaryError as err:
            self._send_json(400, {"error": str(err)})
        except Exception as err:  # noqa: BLE001 - one bad request must not kill the bridge
            self._send_json(500, {"error": f"{type(err).__name__}: {err}"})

    # -- endpoints --------------------------------------------------

    def _search(self, params: dict[str, list[str]]) -> None:
        query = (params.get("q") or [""])[0]
        if not query.strip():
            self._send_json(400, {"error": "q is required"})
            return
        if len(query) > MAX_QUERY_CHARS:
            # The fuzzy pass is O(query x vocabulary). An unbounded query is a
            # way to burn CPU on the machine this is meant to be helping.
            self._send_json(413, {"error": f"q longer than {MAX_QUERY_CHARS} characters"})
            return

        section = (params.get("section") or ["all"])[0]
        if self.corpus is not None and section != "all" and section not in self.corpus.sections:
            self._send_json(400, {"error": f"no section named {section!r}"})
            return

        limit = _clamp_int((params.get("limit") or [None])[0], 20, 1, MAX_LIMIT)
        offset = _clamp_int((params.get("offset") or [None])[0], 0, 0, 100_000)

        assert self.engine is not None  # set by create_server
        results = self.engine.search(query, scope=section, limit=limit, offset=offset)
        self._send_json(200, {
            "query": results.query.raw,
            "section": section,
            "total": results.total,
            "suggestion": results.suggestion,
            "results": [
                {**_entry_payload(hit.entry), "score": round(hit.score, 4),
                 "reasons": list(hit.reasons)}
                for hit in results.hits
            ],
        })

    def _term(self, slug: str) -> None:
        assert self.corpus is not None
        entry = self.corpus.by_slug(slug)
        if entry is None:
            self._send_json(404, {"error": f"no entry with slug {slug!r}"})
            return
        self._send_json(200, _entry_payload(entry))

    def _static(self, path: str) -> None:
        """Serve the built site, if this server was given one.

        Every path is resolved and then checked to be inside the root. Rejecting
        ".." by string match is not enough -- a symlink inside the root can point
        anywhere, and only resolution catches that.
        """
        if self.site_root is None:
            self._send_json(404, {"error": "no such endpoint"})
            return

        relative = urllib.parse.unquote(path).lstrip("/") or "index.html"
        candidate = (self.site_root / relative).resolve()

        try:
            candidate.relative_to(self.site_root)
        except ValueError:
            # Outside the root. Answer as though it simply is not there rather
            # than confirming that a traversal was attempted and detected.
            self._send_json(404, {"error": "not found"})
            return

        if candidate.is_dir():
            candidate = candidate / "index.html"
        if not candidate.is_file():
            self._send_json(404, {"error": "not found"})
            return

        content_type, _ = mimetypes.guess_type(str(candidate))
        self._send_bytes(200, candidate.read_bytes(),
                         content_type or "application/octet-stream")


def create_server(
    port: int = DEFAULT_PORT,
    extra_origins: tuple[str, ...] = (),
    quiet: bool = True,
    site_root: Path | None = None,
    corpus: Corpus | None = None,
) -> ThreadingHTTPServer:
    """Build the server without starting it. Bound to loopback only.

    The corpus is loaded and the engine built once here rather than per request:
    index construction is the expensive part, and doing it inside a handler
    would put it on every search.
    """
    corpus = corpus if corpus is not None else load()
    root = site_root.resolve() if site_root is not None else None

    handler = type(
        "ConfiguredBridgeHandler",
        (BridgeHandler,),
        {
            "extra_origins": tuple(extra_origins),
            "quiet": quiet,
            "corpus": corpus,
            "engine": SearchEngine(corpus),
            "site_root": root,
        },
    )
    # Threading so a slow search does not block the capabilities probe a page
    # makes on load.
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def serve(
    port: int = DEFAULT_PORT,
    extra_origins: tuple[str, ...] = (),
    quiet: bool = True,
    site_root: Path | None = None,
) -> int:
    """Run the bridge until interrupted."""
    try:
        server = create_server(port, extra_origins, quiet, site_root)
    except OSError as err:
        print(f"thl-dict: cannot listen on 127.0.0.1:{port} -- {err}")
        return 1

    info = capabilities(server.RequestHandlerClass.corpus)  # type: ignore[attr-defined]
    print(f"thl-dict serve {__version__} -- http://127.0.0.1:{port}")
    print(f"  {info['entries']} entries across {len(info['sections'])} sections")
    if site_root is not None:
        print(f"  serving the site from {site_root}")
    print(f"  answering: {', '.join(DEFAULT_ORIGINS + tuple(extra_origins))}")
    print("  loopback only, read-only, nothing leaves this machine. ctrl-c to stop.")

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        thread.join()
    except KeyboardInterrupt:
        print("\nstopping.")
        server.shutdown()
    finally:
        server.server_close()
    return 0
