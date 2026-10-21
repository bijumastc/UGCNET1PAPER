"""Fact-checking with Tavily web search, so the AI tutor answers factual questions from real sources.

Free plan: 1,000 searches a month, no card (https://app.tavily.com). One basic search = 1 credit.
The app only searches for fact-based topics (teaching, research, communication, ICT, environment,
higher education, Indian logic), never for maths or logic puzzles, prefers official and reference sites,
remembers recent results, and keeps a class-wide daily limit so the free plan lasts the month.
"""
from __future__ import annotations

import time
from datetime import datetime

from .store import IST

FACT_UNITS = {"U1", "U2", "U4", "U8", "U9", "U10"}
TRUSTED = ["ugc.gov.in", "nta.ac.in", "ugcnet.nta.ac.in", "education.gov.in", "ncert.nic.in", "naac.gov.in",
           "aicte-india.org", "swayam.gov.in", "pib.gov.in", "india.gov.in", "meity.gov.in", "moef.gov.in",
           "unesco.org", "un.org", "unep.org", "ipcc.ch", "who.int", "worldbank.org", "britannica.com",
           "wikipedia.org"]
DEFAULT_DAILY = 30           # class-wide searches per day (~900 a month, inside the free 1,000)
_CACHE: dict = {}            # query -> (time, results)
CACHE_SECONDS = 7 * 86400
TAVILY_URL = "https://api.tavily.com/search"
_DOWN = {"until": 0.0}


class SearchError(Exception):
    pass


def needs_facts(unit: str | None, subtopic_label: str = "") -> bool:
    return unit in FACT_UNITS or "indian logic" in (subtopic_label or "").lower()


def api_key(secrets: dict, store) -> str:
    return str(secrets.get("tavily_api_key") or store.get("class:tavily_api_key", "") or "").strip()


def enabled(secrets: dict, store) -> bool:
    return bool(api_key(secrets, store)) and store.get("class:web_on", "1") == "1"


def _today_key() -> str:
    return "class:web_used:" + datetime.now(IST).strftime("%Y-%m-%d")


def used_today(store) -> int:
    try:
        return int(float(store.get(_today_key(), 0) or 0))
    except ValueError:
        return 0


def daily_limit(store) -> int:
    return int(float(store.get("class:web_daily_limit", DEFAULT_DAILY)))


def _call(key: str, query: str, max_results: int, domains: list[str] | None, timeout: float) -> list[dict]:
    import requests

    body = {"api_key": key, "query": query[:380], "search_depth": "basic", "max_results": max_results,
            "include_answer": False}
    if domains:
        body["include_domains"] = domains
    try:
        r = requests.post(TAVILY_URL, json=body, timeout=(5, timeout),
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    except requests.exceptions.RequestException:
        _DOWN["until"] = time.time() + 120
        raise SearchError("Couldn't reach the web search service.")
    if r.status_code in (401, 403):
        raise SearchError("Web search rejected the Tavily key.")
    if r.status_code in (429, 432, 433):
        _DOWN["until"] = time.time() + 600
        raise SearchError("The free web search limit is used up for now.")
    if r.status_code >= 400:
        _DOWN["until"] = time.time() + 120
        raise SearchError(f"Web search error {r.status_code}.")
    out = []
    for it in (r.json().get("results") or []):
        if it.get("url") and it.get("content"):
            out.append({"title": (it.get("title") or it["url"])[:120], "url": it["url"],
                        "content": " ".join(str(it["content"]).split())[:900]})
    return out


def search(store, key: str, query: str, max_results: int = 4, timeout: float = 12) -> list[dict]:
    """Trusted sites first; the open web only if they have too little. Counts against the daily limit."""
    q = " ".join(query.split())
    hit = _CACHE.get(q.lower())
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    if time.time() < _DOWN["until"]:
        raise SearchError("Web search is resting for a few minutes.")
    if used_today(store) >= daily_limit(store):
        raise SearchError("Today's web searches for the class are used up.")
    res = _call(key, q, max_results, TRUSTED, timeout)
    calls = 1
    if len(res) < 2:
        res = _call(key, q, max_results, None, timeout)
        calls = 2
    try:
        store.set(_today_key(), used_today(store) + calls)
    except Exception:
        pass
    _CACHE[q.lower()] = (time.time(), res)
    return res


def context_message(results: list[dict]) -> str:
    """System message giving the model the search results to answer from."""
    lines = ["Web search results for the student's question (from the internet, fetched just now). Use them for "
             "facts such as names, dates, numbers, reports, laws and definitions. Cite them like [1], [2]. If they "
             "do not cover the question, say plainly that you are not sure rather than guessing. If a result "
             "conflicts with the official answer key, trust the key and say the student should check with "
             "the teacher."]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']} ({r['url']})\n{r['content']}")
    return "\n\n".join(lines)


def sources_md(results: list[dict]) -> str:
    return "\n".join(f"{i}. [{r['title']}]({r['url']})" for i, r in enumerate(results, 1))


def facts_for_writer(results: list[dict]) -> str:
    """Reference facts for the AI question writer."""
    return "\n".join(f"- ({r['url']}) {r['content'][:600]}" for r in results)
