"""Connect the AI tutor to free AI services, with automatic backup.

Each request tries the services in order. If one is busy (rate limit), down, or its key is missing or wrong,
the next one answers, so students are not held up:

  1. Groq        free key  https://console.groq.com/keys        openai/gpt-oss-120b (very fast)
  2. NVIDIA      free key  https://build.nvidia.com             meta/llama-3.3-70b-instruct, then Llama 4 Maverick
  3. Cerebras    free key  https://cloud.cerebras.ai            gpt-oss-120b
  4. OpenRouter  free key  https://openrouter.ai/keys           meta-llama/llama-3.3-70b-instruct:free,
                                                                then openrouter/free (any free model)
  5. Mistral     free key  https://console.mistral.ai           mistral-small-latest (Experiment plan)
  6. Groq        (same key)                                     openai/gpt-oss-20b (separate limit)
  7. Gemini      your paid key (optional last backup)           gemini-3.8-flash

A model that a service has withdrawn is skipped for an hour automatically, so it never slows students down.

Note (Oct 2026): Groq and Cerebras stopped offering Llama on their free plans (Groq on 16 Aug 2026), so
they use OpenAI's open-weight gpt-oss models instead. OpenRouter still lists a free Llama 3.3 70B.
Model names can change: edit them in ⚙️ Class settings, or in Secrets (e.g. groq_models = "a, b").
"""
from __future__ import annotations

import time

PROVIDERS = {
    "groq": {"label": "Groq", "base_url": "https://api.groq.com/openai/v1", "secret": "groq_api_key",
             "models": ["openai/gpt-oss-120b"], "late_models": ["openai/gpt-oss-20b"],
             "key_url": "https://console.groq.com/keys"},
    "nvidia": {"label": "NVIDIA", "base_url": "https://integrate.api.nvidia.com/v1", "secret": "nvidia_api_key",
               "models": ["meta/llama-3.3-70b-instruct", "meta/llama-4-maverick-17b-128e-instruct"],
               "key_url": "https://build.nvidia.com",
               "note": "Free for prototyping/learning. NVIDIA has been withdrawing free models; if 🔌 Test shows "
                       "'no longer offered', pick a model marked 'Free Endpoint' on build.nvidia.com and paste its name."},
    "cerebras": {"label": "Cerebras", "base_url": "https://api.cerebras.ai/v1", "secret": "cerebras_api_key",
                 "models": ["gpt-oss-120b"], "key_url": "https://cloud.cerebras.ai"},
    "openrouter": {"label": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "secret": "openrouter_api_key",
                   "models": ["meta-llama/llama-3.3-70b-instruct:free", "openrouter/free"],
                   "key_url": "https://openrouter.ai/keys"},
    "mistral": {"label": "Mistral", "base_url": "https://api.mistral.ai/v1", "secret": "mistral_api_key",
                "models": ["mistral-small-latest"], "key_url": "https://console.mistral.ai/api-keys",
                "note": "Free 'Experiment' plan: needs phone verification, and Mistral may use these requests to "
                        "train its models. Students' questions contain no names, but switch it off if you prefer."},
    "gemini": {"label": "Gemini (paid)", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
               "secret": "gemini_api_key", "models": [], "key_url": "https://aistudio.google.com/apikey"},
}
_COOL: dict = {}            # (base_url, model) -> time until which we skip it after a rate limit
COOL_SECONDS = 60           # after "busy" (rate limit)
GONE_SECONDS = 3600         # after "model not found / withdrawn" or a rejected key
DOWN_SECONDS = 120          # after a timeout, no connection or a server error
CONNECT_TIMEOUT = 5         # seconds to reach a service before trying the next one
READ_TIMEOUT = 25           # seconds to wait for an answer before trying the next one


def _rest(step, seconds):
    """Skip this service+model for a while (shared by all students on the same app server)."""
    _COOL[(step["base_url"], step["model"])] = time.time() + seconds


class LLMError(Exception):
    def __init__(self, msg, details=None, retry=True):
        super().__init__(msg)
        self.details = details or []
        self.retry = retry


def _models(pid, secrets, store, gemini_model):
    p = PROVIDERS[pid]
    if pid == "gemini":
        return [gemini_model]
    raw = secrets.get(f"{pid}_models") or store.get(f"class:llm_models_{pid}", "")
    if raw:
        return [m.strip() for m in str(raw).split(",") if m.strip()]
    return p["models"] + p.get("late_models", [])


def provider_key(pid, secrets, store):
    p = PROVIDERS[pid]
    key = secrets.get(p["secret"]) or store.get(f"class:{p['secret']}", "")
    if not key and pid != "gemini":           # keys saved by the earlier version (llm_api_key + preset)
        old = secrets.get("llm_api_key") or store.get("class:llm_api_key", "")
        preset = (secrets.get("llm_preset") or store.get("class:llm_preset", "") or "Groq").lower()
        if old and pid in preset:
            key = old
    return str(key or "").strip()


def provider_on(pid, store, secrets=None) -> bool:
    default = "0" if pid == "gemini" and (secrets or {}).get("gemini_backup") is False else "1"
    return store.get(f"class:llm_on_{pid}", default) == "1"


def config(secrets: dict, store, gemini_model: str = "gemini-3.8-flash") -> dict:
    """The backup chain from Secrets (online) or ⚙️ Class settings (this computer). {} when nothing is set up."""
    steps, late = [], []
    custom_base = secrets.get("llm_base_url") or store.get("class:llm_base_url", "")
    custom_model = secrets.get("llm_model") or store.get("class:llm_model", "")
    if custom_base and custom_model and "groq.com" not in custom_base and "openrouter.ai" not in custom_base:
        steps.append({"provider": "custom", "label": "Custom", "base_url": custom_base.rstrip("/"),
                      "model": custom_model, "api_key": secrets.get("llm_api_key") or store.get("class:llm_api_key", "")})
    for pid, p in PROVIDERS.items():
        key = provider_key(pid, secrets, store)
        if not key or not provider_on(pid, store, secrets):
            continue
        ms = _models(pid, secrets, store, gemini_model)
        n_main = len(p["models"]) if not (secrets.get(f"{pid}_models") or store.get(f"class:llm_models_{pid}", "")) else len(ms)
        for i, m in enumerate(ms):
            step = {"provider": pid, "label": p["label"], "base_url": p["base_url"], "model": m, "api_key": key}
            (steps if i < n_main or pid == "gemini" else late).append(step)
    gem = [s for s in steps if s["provider"] == "gemini"]
    chain = [s for s in steps if s["provider"] != "gemini"] + late + gem      # paid Gemini always last
    if not chain:
        return {}
    return {"chain": chain, "model": " → ".join(dict.fromkeys(s["label"] for s in chain))}


def _call(step, messages, temperature, max_tokens, json_mode, timeout) -> str:
    import requests

    body = {"model": step["model"], "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    if "gpt-oss" in step["model"] and step.get("provider") in ("groq", "cerebras"):
        body["reasoning_effort"] = "low"             # keep the thinking short so the answer fits
    if step.get("provider") == "gemini":
        body["reasoning_effort"] = "low"
    headers = {"Content-Type": "application/json"}
    if step.get("api_key"):
        headers["Authorization"] = f"Bearer {step['api_key']}"
    if "openrouter.ai" in step["base_url"]:
        headers["X-Title"] = "UGC NET Paper 1 Trainer"
    try:
        r = requests.post(f"{step['base_url']}/chat/completions", json=body, headers=headers,
                          timeout=(CONNECT_TIMEOUT, timeout))
    except requests.exceptions.Timeout:
        _rest(step, DOWN_SECONDS)
        raise LLMError("The AI took too long to answer. Please try again.")
    except requests.exceptions.RequestException:
        _rest(step, DOWN_SECONDS)
        raise LLMError("Couldn't reach the AI service. Check the internet connection.")
    if r.status_code in (401, 402, 403):
        _rest(step, GONE_SECONDS)
        raise LLMError("The AI service rejected the API key (or this model isn't open to your account)."
                       if r.status_code != 402 else "This service needs credits on the account.")
    if r.status_code == 429:
        try:                                  # e.g. a daily limit used up: the service says how long to wait
            wait = float(r.headers.get("retry-after", COOL_SECONDS))
        except ValueError:
            wait = COOL_SECONDS
        _rest(step, min(max(wait, 20), 3 * 3600))
        raise LLMError("The free AI limit is busy right now 🙂 Please wait a minute and try again.")
    if r.status_code >= 500:
        _rest(step, DOWN_SECONDS)
        raise LLMError(f"The AI service is having trouble (error {r.status_code}).")
    low = r.text.lower()
    if r.status_code in (404, 410) or (r.status_code == 400 and "model" in low and any(
            w in low for w in ("not found", "decommission", "deprecat", "does not exist", "no longer", "invalid model"))):
        _rest(step, GONE_SECONDS)
        raise LLMError("This model is no longer offered by the service. Change it in ⚙️ Class settings.")
    if r.status_code >= 400:
        if json_mode and r.status_code == 400:          # some models don't support JSON mode: retry without it
            return _call(step, messages, temperature, max_tokens, False, timeout)
        raise LLMError(f"AI service error {r.status_code}: {r.text[:200]}")
    try:
        text = r.json()["choices"][0]["message"]["content"] or ""
    except Exception:
        raise LLMError("The AI service sent an unexpected reply.")
    if not text.strip():
        raise LLMError("The AI sent an empty answer.")
    return text


def chat(cfg: dict, messages: list[dict], temperature: float = 0.4, max_tokens: int = 1500,
         json_mode: bool = False, timeout: int = READ_TIMEOUT) -> str:
    """One answer. With a backup chain, tries each service in turn; cfg['used'] tells which one answered."""
    steps = cfg.get("chain") or [cfg]
    fresh = [s for s in steps if _COOL.get((s["base_url"], s["model"]), 0) < time.time()]
    order = fresh or steps                       # resting ones are skipped (unless nothing else is left)
    details = []
    for s in order:
        try:
            text = _call(s, messages, temperature, max_tokens, json_mode, timeout)
            cfg["used"] = f"{s.get('label', 'AI')} · {s['model']}"
            return text
        except LLMError as e:
            details.append(f"{s.get('label', 'AI')} · {s['model']}: {e}")
    if len(order) == 1:
        raise LLMError(details[0].split(": ", 1)[1], details)
    raise LLMError("All the AI services are busy right now 🙂 Please wait a minute and try again. "
                   "Practice and the Learn cards always work.", details)


def resting() -> list[str]:
    """Services/models being skipped right now, with minutes left (for the teacher)."""
    now = time.time()
    names = {v["base_url"]: v["label"] for v in PROVIDERS.values()}
    return [f"{names.get(b, b)} · {m} ({(u - now) / 60:.0f} min)" for (b, m), u in _COOL.items() if u > now]


def test_each(cfg: dict) -> list[dict]:
    """For the teacher's 🔌 Test button: try every step once."""
    out = []
    for s in cfg.get("chain", []):
        t0 = time.time()
        try:
            reply = _call(s, [{"role": "user", "content": "In one short sentence: what is Paper 1 of UGC NET?"}],
                          0.2, 400, False, 30)
            _COOL.pop((s["base_url"], s["model"]), None)          # working again: stop skipping it
            out.append({"service": s["label"], "model": s["model"], "result": "✅ " + reply[:120],
                        "seconds": round(time.time() - t0, 1)})
        except LLMError as e:
            out.append({"service": s["label"], "model": s["model"], "result": "❌ " + str(e),
                        "seconds": round(time.time() - t0, 1)})
    return out


# ------------------------------------------------------------------ tutor prompts
TUTOR_SYSTEM = """You are a friendly, patient tutor for the UGC NET Paper 1 exam (General Paper on Teaching and
Research Aptitude, India). Your student may be a beginner.

How to teach:
- Start simple (as if to a first-year student), then build up to exam level.
- Short paragraphs, simple English, everyday Indian examples. Use a small table or numbered steps when it helps.
- For maths and logic, show every step.
- End with one quick check question or a memory tip when it fits.
- Warm and encouraging; an occasional emoji is fine. Never make the student feel bad about a mistake.

Rules:
- Only teach topics from the UGC NET Paper 1 syllabus. If asked about something else, gently bring the
  conversation back to Paper 1.
- Be accurate. If you are not sure of a fact (a date, name, number, report or law), say so plainly instead of
  guessing, and suggest checking the textbook or the teacher.
- When an official answer is given to you, treat it as correct and explain its reasoning. If you think it
  might be wrong, say the student should ask their teacher; do not tell them the key is wrong.
- Keep answers under about 250 words unless the student asks for more."""


def tutor_context(unit_name: str, topic_name: str, primer: dict | None, examples: list[dict]) -> str:
    parts = [f"Current unit: {unit_name}. Current topic: {topic_name}."]
    if primer:
        parts.append("Teacher's notes for this topic (use them; they are correct):\n"
                     f"- Basic idea: {primer['zero']}\n- Method: " + " | ".join(primer["method"]) +
                     "\n- Common traps: " + " | ".join(primer["traps"]))
    if examples:
        ex = []
        for q in examples[:3]:
            opts = q.get("options") or []
            line = f"Q: {q['text'][:500]}"
            if len(opts) == 4:
                line += "\nOptions: " + " | ".join(f"({i + 1}) {o}" for i, o in enumerate(opts))
            if q.get("answer") is not None:
                line += f"\nOfficial answer: option {q['answer'] + 1}"
            ex.append(line)
        parts.append("Real past exam questions on this topic (for style and level):\n\n" + "\n\n".join(ex))
    return "\n\n".join(parts)


def explain_question_prompt(q: dict, chosen: int | None) -> str:
    opts = q.get("options") or []
    txt = q["text"][:1500]
    note = "" if q.get("display") == "text" else \
        "\n(The text was read from a scanned paper by OCR and may contain small reading errors.)"
    o = "\n".join(f"({i + 1}) {x}" for i, x in enumerate(opts)) if len(opts) == 4 else "(options shown to the student as an image)"
    return (f"Explain this exam question to the student.{note}\n\nQuestion:\n{txt}\n\nOptions:\n{o}\n\n"
            f"Official answer: option {q['answer'] + 1}." +
            (f" The student chose option {chosen + 1}." if chosen is not None and chosen >= 0 else "") +
            "\n\nExplain why the official answer is right" +
            (" and why the student's choice is not" if chosen is not None and chosen >= 0 and chosen != q["answer"] else "") +
            ", then give one tip for similar questions.")
