"""Tests for the simulators' maths and logic, and for the Llama connection (using a local stand-in server)."""
import sys
import threading
from http.server import ThreadingHTTPServer as HTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fake_llm_server import H  # noqa: E402
from p1 import ai_writer as AI  # noqa: E402
from p1 import llm  # noqa: E402
from p1.simulators import analyse, power_calc, rule_check  # noqa: E402


# ------------------------------------------------------------------ hypothesis testing
def test_power_matches_textbook_values():
    assert abs(power_calc(0.05, 64, 0.5, 2)["power"] - 0.807) < 0.005      # classic n=64 per group, d=0.5
    assert abs(power_calc(0.05, 50, 0.5, 2)["power"] - 0.705) < 0.005


def test_power_moves_the_right_way():
    base = power_calc(0.05, 50, 0.5, 2)["power"]
    assert power_calc(0.01, 50, 0.5, 2)["power"] < base        # smaller alpha → less power
    assert power_calc(0.05, 100, 0.5, 2)["power"] > base       # bigger sample → more power
    assert power_calc(0.05, 50, 0.8, 2)["power"] > base        # bigger effect → more power
    assert power_calc(0.05, 50, 0.5, 1)["power"] > base        # one-tailed → more power


# ------------------------------------------------------------------ syllogisms
@pytest.mark.parametrize("prem,concl,modern,trad", [
    ([("A", "M", "P"), ("A", "S", "M")], ("A", "S", "P"), True, True),     # Barbara
    ([("E", "M", "P"), ("A", "S", "M")], ("E", "S", "P"), True, True),     # Celarent
    ([("A", "M", "P"), ("A", "M", "S")], ("I", "S", "P"), False, True),    # Darapti: traditional only
    ([("A", "S", "M"), ("I", "M", "P")], ("I", "S", "P"), False, False),   # undistributed middle
    ([("E", "S", "M"), ("E", "M", "P")], ("E", "S", "P"), False, False),   # exclusive premises
])
def test_syllogism_verdicts(prem, concl, modern, trad):
    r = analyse(prem, concl)
    assert r["modern"] == modern and r["traditional"] == trad


def test_rule_check_names_the_fallacy():
    names = {"S": "Teachers", "M": "Researchers", "P": "Innovators"}
    out = " ".join(rule_check([("A", "S", "M"), ("I", "M", "P")], ("I", "S", "P"), names)).lower()
    assert "middle" in out


# ------------------------------------------------------------------ Llama (OpenAI-compatible) connection
@pytest.fixture(scope="module")
def server():
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}/v1"
    srv.shutdown()


class _Store(dict):
    def get(self, k, d=None):
        return super().get(k, d)


def test_config_builds_backup_chain():
    assert llm.config({}, _Store()) == {}
    cfg = llm.config({"groq_api_key": "g", "openrouter_api_key": "o", "gemini_api_key": "x"}, _Store())
    order = [(s["provider"], s["model"]) for s in cfg["chain"]]
    assert order[0] == ("groq", "openai/gpt-oss-120b")
    assert order[-1][0] == "gemini"                                   # paid service always last
    assert ("openrouter", "meta-llama/llama-3.3-70b-instruct:free") in order
    assert order.index(("groq", "openai/gpt-oss-20b")) > order.index(("openrouter", "openrouter/free"))
    # a provider switched off in Class settings is left out
    off = llm.config({"groq_api_key": "g", "gemini_api_key": "x"}, _Store({"class:llm_on_gemini": "0"}))
    assert all(s["provider"] != "gemini" for s in off["chain"])
    # key saved by the earlier version still works
    assert llm.config({"llm_api_key": "k"}, _Store())["chain"][0]["provider"] == "groq"


def test_backup_takes_over_when_busy(server):
    llm._COOL.clear()
    cfg = {"chain": [{"label": "Busy", "base_url": server, "model": "busy-model", "api_key": "good-key"},
                     {"label": "BadKey", "base_url": server, "model": "m", "api_key": "nope"},
                     {"label": "Good", "base_url": server, "model": "m", "api_key": "good-key"}]}
    assert "Tutor reply" in llm.chat(cfg, [{"role": "user", "content": "hi"}])
    assert cfg["used"].startswith("Good")
    assert llm._COOL                                                 # the busy one rests for a minute
    with pytest.raises(llm.LLMError, match="All the AI services are busy") as e:
        llm.chat({"chain": cfg["chain"][:2]}, [{"role": "user", "content": "hi"}])
    assert len(e.value.details) == 2


def test_chat_and_bad_key(server):
    good = {"base_url": server, "model": "m", "api_key": "good-key"}
    assert "Tutor reply" in llm.chat(good, [{"role": "user", "content": "hi"}])
    with pytest.raises(llm.LLMError, match="rejected the API key"):
        llm.chat({**good, "api_key": "bad"}, [{"role": "user", "content": "hi"}])


def test_unreachable_server_gives_friendly_error():
    with pytest.raises(llm.LLMError):
        llm.chat({"base_url": "http://127.0.0.1:9/v1", "model": "m", "api_key": "x"},
                 [{"role": "user", "content": "hi"}], timeout=3)


def test_llama_question_writer(server):
    rows, problems = AI.generate_llama({"base_url": server, "model": "m", "api_key": "good-key"},
                                       "U9", "U9.1", "direct_fact", 1, 2, [], [])
    assert len(rows) == 1 and rows[0]["status"] == "pending" and rows[0]["answer"] == 1 and not problems


def test_explain_prompt_keeps_official_answer():
    q = {"text": "2+2?", "options": ["3", "4", "5", "6"], "answer": 1, "display": "text"}
    p = llm.explain_question_prompt(q, 0)
    assert "Official answer: option 2" in p and "chose option 1" in p


def test_withdrawn_model_is_skipped_for_an_hour(server):
    llm._COOL.clear()
    gone = {"label": "Old", "base_url": server, "model": "gone-model", "api_key": "good-key"}
    good = {"label": "Good", "base_url": server, "model": "m", "api_key": "good-key"}
    cfg = {"chain": [gone, good]}
    assert "Tutor reply" in llm.chat(cfg, [{"role": "user", "content": "hi"}])
    assert llm._COOL[(server, "gone-model")] > __import__("time").time() + 3000
    n = len(__import__("fake_llm_server").LOG)
    llm.chat(cfg, [{"role": "user", "content": "hi"}])
    assert len(__import__("fake_llm_server").LOG) == n + 1          # the withdrawn model wasn't tried again


def test_nvidia_and_mistral_join_the_chain():
    cfg = llm.config({"groq_api_key": "g", "nvidia_api_key": "n", "mistral_api_key": "m"}, _Store())
    prov = [s["provider"] for s in cfg["chain"]]
    assert prov.index("nvidia") < prov.index("mistral") and prov[0] == "groq"


def test_hanging_service_fails_over_fast(server):
    import time as _t

    llm._COOL.clear()
    cfg = {"chain": [{"label": "Slow", "base_url": server, "model": "slow-model", "api_key": "good-key"},
                     {"label": "Good", "base_url": server, "model": "m", "api_key": "good-key"}]}
    t0 = _t.time()
    assert "Tutor reply" in llm.chat(cfg, [{"role": "user", "content": "hi"}], timeout=1)
    assert _t.time() - t0 < 2.5 and cfg["used"].startswith("Good")
    t0 = _t.time()
    llm.chat(cfg, [{"role": "user", "content": "hi"}], timeout=1)          # slow one now rests: instant
    assert _t.time() - t0 < 0.5
