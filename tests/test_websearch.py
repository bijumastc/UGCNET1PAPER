"""Tavily fact-checking: trusted sites first, open web as fallback, daily limit, cache, prompt with sources."""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from p1 import websearch as WS  # noqa: E402

CALLS = []


class T(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        CALLS.append(body)
        if body.get("api_key") != "tvly-good":
            self.send_response(401); self.end_headers(); return
        if "nothing trusted" in body["query"] and body.get("include_domains"):
            res = []
        else:
            res = [{"title": "SWAYAM", "url": "https://swayam.gov.in/about", "content": "SWAYAM was launched in 2017."},
                   {"title": "MOOC", "url": "https://en.wikipedia.org/wiki/SWAYAM", "content": "Indian MOOC platform."}]
        out = json.dumps({"results": res}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(out)


class Store(dict):
    def get(self, k, d=None):
        return super().get(k, d)

    def set(self, k, v):
        self[k] = str(v)


@pytest.fixture()
def tav(monkeypatch):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), T)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setattr(WS, "TAVILY_URL", f"http://127.0.0.1:{srv.server_port}/search")
    WS._CACHE.clear()
    WS._DOWN["until"] = 0
    CALLS.clear()
    yield
    srv.shutdown()


def test_trusted_sites_first_then_cache(tav):
    st = Store()
    r = WS.search(st, "tvly-good", "When was SWAYAM launched?")
    assert r[0]["url"].startswith("https://swayam.gov.in") and CALLS[0]["include_domains"]
    assert WS.used_today(st) == 1
    WS.search(st, "tvly-good", "When was  SWAYAM launched?")             # same question: no new search
    assert len(CALLS) == 1 and WS.used_today(st) == 1


def test_open_web_when_trusted_sites_have_little(tav):
    st = Store()
    r = WS.search(st, "tvly-good", "nothing trusted about this")
    assert len(r) == 2 and len(CALLS) == 2 and "include_domains" not in CALLS[1] and WS.used_today(st) == 2


def test_daily_limit_and_bad_key(tav):
    st = Store({"class:web_daily_limit": "1"})
    WS.search(st, "tvly-good", "q one")
    with pytest.raises(WS.SearchError, match="used up"):
        WS.search(st, "tvly-good", "q two")
    with pytest.raises(WS.SearchError, match="rejected"):
        WS.search(Store(), "tvly-bad", "q three")


def test_only_fact_topics_are_searched_and_prompt_cites():
    assert WS.needs_facts("U10") and WS.needs_facts("U6", "Indian logic: pramanas")
    assert not WS.needs_facts("U5") and not WS.needs_facts("U6", "Syllogisms & Venn diagrams")
    msg = WS.context_message([{"title": "A", "url": "https://x.org", "content": "fact"}])
    assert "[1] A (https://x.org)" in msg and "not sure" in msg
    assert WS.sources_md([{"title": "A", "url": "https://x.org"}]) == "1. [A](https://x.org)"
