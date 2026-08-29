"""The loopback bridge.

Driven against a real server on a real ephemeral port rather than a mocked
handler, because most of what could go wrong here — CORS headers, preflight,
status codes, path containment — lives in the parts a mock would replace.

The origin and host tests are the important ones. Loopback binding stops the
network reaching this server; it does not stop another website the visitor
happens to have open, since their browser runs on this machine too.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from thehallucinatedlab_dictionary.serve import (
    MAX_QUERY_CHARS,
    capabilities,
    create_server,
    host_allowed,
    origin_allowed,
)

SITE = "https://thehallucinatedlab.space"


@pytest.fixture(scope="module")
def site_root(tmp_path_factory):
    """A tiny static site, with a file outside it that must stay unreachable."""
    root = tmp_path_factory.mktemp("site")
    (root / "index.html").write_text("<h1>hi</h1>", encoding="utf-8")
    (root.parent / "SECRET.txt").write_text("do not serve me", encoding="utf-8")
    return root


@pytest.fixture(scope="module")
def bridge(site_root):
    """A running bridge on an OS-assigned port."""
    server = create_server(port=0, site_root=site_root)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def request(url, *, method="GET", origin=SITE, headers=None):
    """Returns (status, headers, body), never raising on 4xx/5xx."""
    req = urllib.request.Request(url, method=method)
    if origin is not None:
        req.add_header("Origin", origin)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, dict(response.headers), response.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        return err.code, dict(err.headers), err.read().decode("utf-8")


# -- the origin boundary --------------------------------------------


@pytest.mark.parametrize(
    "origin",
    [SITE, "http://localhost:4173", "http://127.0.0.1:8080", "http://localhost", None],
)
def test_origins_that_may_use_the_bridge(origin):
    assert origin_allowed(origin) is True


@pytest.mark.parametrize(
    "origin",
    [
        "https://evil.example",
        "http://thehallucinatedlab.space",           # http, not https
        "https://thehallucinatedlab.space.evil.co",  # suffix attack
        "https://notthehallucinatedlab.space",
        "http://localhost.evil.co",
        "null",
    ],
)
def test_origins_that_may_not(origin):
    assert origin_allowed(origin) is False


def test_an_extra_origin_can_be_allowed_explicitly():
    assert origin_allowed("https://staging.example", ("https://staging.example",)) is True
    assert origin_allowed("https://staging.example") is False


def test_a_disallowed_origin_is_refused_without_cors_headers(bridge):
    status, headers, _ = request(f"{bridge}/thl/v1/capabilities", origin="https://evil.example")

    assert status == 403
    # Echoing CORS back would let the calling page read the refusal, and so
    # confirm a bridge is here and what it is.
    assert "Access-Control-Allow-Origin" not in headers


# -- the host boundary ----------------------------------------------


@pytest.mark.parametrize(
    "host",
    ["127.0.0.1", "127.0.0.1:8788", "localhost", "localhost:8788", "[::1]:8788", None],
)
def test_hosts_that_may_use_the_bridge(host):
    assert host_allowed(host) is True


@pytest.mark.parametrize(
    "host",
    ["evil.example", "evil.example:8788", "127.0.0.1.evil.co", "localhost.evil.co"],
)
def test_hosts_that_may_not(host):
    assert host_allowed(host) is False


def test_a_rebound_host_is_refused_even_with_no_origin(bridge):
    """The DNS-rebinding shape, end to end: truthful Host, absent Origin.

    Checking Origin alone answers this request with a document describing what
    this machine has installed.
    """
    status, headers, _ = request(
        f"{bridge}/thl/v1/capabilities", origin=None, headers={"Host": "evil.example"}
    )

    assert status == 403
    assert "Access-Control-Allow-Origin" not in headers


# -- capabilities ---------------------------------------------------


def test_capabilities_reports_both_sections(bridge):
    status, headers, body = request(f"{bridge}/thl/v1/capabilities")
    payload = json.loads(body)

    assert status == 200
    assert headers["Access-Control-Allow-Origin"] == SITE
    assert headers["Vary"] == "Origin"
    assert payload["name"] == "thehallucinatedlab-dictionary"
    assert set(payload["sections"]) == {"ai-mathematics", "software-engineering"}
    assert payload["entries"] == sum(s["entries"] for s in payload["sections"].values())


def test_capabilities_counts_match_the_loaded_corpus():
    payload = capabilities()
    assert payload["entries"] > 0
    assert payload["endpoints"]


# -- search ---------------------------------------------------------


def test_search_returns_ranked_results(bridge):
    status, _, body = request(f"{bridge}/thl/v1/dict/search?q=gradient")
    payload = json.loads(body)

    assert status == 200
    assert payload["total"] > 0
    assert payload["results"][0]["term"] == "Gradient Descent"
    assert "score" in payload["results"][0]


def test_search_without_a_query_is_a_400(bridge):
    status, _, _ = request(f"{bridge}/thl/v1/dict/search")
    assert status == 400


def test_an_overlong_query_is_refused(bridge):
    """Fuzzy matching is O(query x vocabulary); an unbounded query burns CPU."""
    status, _, _ = request(f"{bridge}/thl/v1/dict/search?q={'a' * (MAX_QUERY_CHARS + 50)}")
    assert status == 413


def test_an_unknown_section_is_a_400(bridge):
    status, _, _ = request(f"{bridge}/thl/v1/dict/search?q=gradient&section=nope")
    assert status == 400


def test_a_non_numeric_limit_falls_back_rather_than_crashing(bridge):
    """A query string carries only text, so limit=abc is well-formed input."""
    status, _, body = request(f"{bridge}/thl/v1/dict/search?q=gradient&limit=abc")
    assert status == 200
    assert json.loads(body)["total"] > 0


# -- terms ----------------------------------------------------------


def test_a_term_can_be_fetched_by_slug(bridge):
    status, _, body = request(f"{bridge}/thl/v1/dict/term/technical-debt")

    assert status == 200
    assert json.loads(body)["term"] == "Technical Debt"


def test_an_unknown_slug_is_a_404(bridge):
    status, _, _ = request(f"{bridge}/thl/v1/dict/term/no-such-entry")
    assert status == 404


# -- static files ---------------------------------------------------


def test_the_site_is_served_when_a_root_is_given(bridge):
    status, _, body = request(f"{bridge}/index.html")
    assert status == 200
    assert "<h1>hi</h1>" in body


@pytest.mark.parametrize("path", ["/../SECRET.txt", "/%2e%2e/SECRET.txt", "/..%2fSECRET.txt"])
def test_a_path_cannot_walk_out_of_the_site_root(bridge, path):
    """Rejecting ".." by string match is not enough.

    A symlink inside the root can point anywhere, so containment is checked by
    resolving the path and confirming it is still under the root.
    """
    status, _, body = request(f"{bridge}{path}")

    assert status == 404
    assert "do not serve me" not in body


# -- preflight ------------------------------------------------------


def test_the_preflight_grants_private_network_access(bridge):
    status, headers, _ = request(f"{bridge}/thl/v1/dict/search", method="OPTIONS")

    assert status == 204
    assert headers["Access-Control-Allow-Origin"] == SITE
    # Chromium refuses public -> private without this.
    assert headers["Access-Control-Allow-Private-Network"] == "true"


def test_a_disallowed_origin_gets_no_preflight_either(bridge):
    status, headers, _ = request(
        f"{bridge}/thl/v1/dict/search", method="OPTIONS", origin="https://evil.example"
    )

    assert status == 403
    assert "Access-Control-Allow-Private-Network" not in headers


def test_an_unknown_endpoint_is_a_404_not_a_crash(bridge):
    status, _, _ = request(f"{bridge}/thl/v1/nope")
    assert status == 404
