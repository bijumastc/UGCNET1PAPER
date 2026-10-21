"""Write new practice questions with Google Gemini, in the style of the real papers.

Every AI-written question is saved as 'pending'. The teacher reviews it (approve, edit or
reject) before any student sees it, because AI models sometimes get facts wrong.
"""
from __future__ import annotations

import json
import re
import uuid

from .classify import _tokens
from .patterns import PATTERN_BY_ID, pattern_name
from .store import now_iso
from .syllabus import UNITS, subtopic_name, unit_name

DEFAULT_MODEL = "gemini-3.8-flash"     # change in Settings to any model your Google AI Studio account lists

AR_OPTIONS = ["Both (A) and (R) are true and (R) is the correct explanation of (A)",
              "Both (A) and (R) are true but (R) is NOT the correct explanation of (A)",
              "(A) is true but (R) is false", "(A) is false but (R) is true"]
STMT_OPTIONS = ["Both Statement I and Statement II are true", "Both Statement I and Statement II are false",
                "Statement I is true but Statement II is false", "Statement I is false but Statement II is true"]

FORMAT_RULES = {
    "assertion_reason": "Write 'Assertion (A): …' and 'Reason (R): …' on separate lines. Use exactly these four options "
                        "in this order: " + json.dumps(AR_OPTIONS),
    "statement_i_ii": "Write 'Statement I: …' and 'Statement II: …'. Use exactly these four options in this order: "
                      + json.dumps(STMT_OPTIONS),
    "match_list": "Put List I (A, B, C, D) and List II (I, II, III, IV) in the question text, one item per line. "
                  "Options are codes like 'A-II, B-I, C-IV, D-III'.",
    "sequence": "List 4–5 items labelled A, B, C, D, E in the question; options are orders like 'B, A, D, C'.",
    "multi_statement": "List 3–5 statements labelled A, B, C… then 'Choose the correct answer from the options given "
                       "below:'; options are combinations like 'A and B only'.",
    "negative": "Ask which option is NOT correct / does NOT belong.",
}


def build_prompt(unit: str, subtopic: str, pattern: str, n: int, level: int, examples: list[dict],
                 facts: str = "") -> str:
    ex = "\n\n".join(f"Example {i + 1}:\n{e['text'][:700]}" + (
        "\nOptions: " + " | ".join(e["options"]) if len(e.get("options") or []) == 4 else "")
        for i, e in enumerate(examples[:6])) or "(no examples available)"
    diff = {1: "easy (direct recall of one fact)", 2: "medium (needs understanding of a concept)",
            3: "hard (exam-level, needs careful reasoning; strong distractors)"}[level]
    return f"""You write original multiple-choice questions for the UGC NET Paper 1 exam (India), in English.

Unit: {unit_name(unit)}
Topic: {subtopic_name(subtopic)}
Question format: {pattern_name(pattern)}
Difficulty: {diff}

Here are real past exam questions on this topic. Match their style and level, but do NOT copy them
or reuse their exact facts in the same form:

{ex}
{("Reference facts from trusted websites (use only facts supported here or that you are certain of):" + chr(10) + facts + chr(10)) if facts else ""}
Rules:
- Write {n} NEW questions. Every fact must be correct and well established. If you are not sure of a fact,
  date, name or number, choose a different fact. Never invent people, books, laws, reports or dates.
- Exactly 4 options; exactly one is correct. Distractors must be plausible but clearly wrong.
- {FORMAT_RULES.get(pattern, "Keep the question short and unambiguous.")}
- explanation: 2–4 sentences a beginner can follow: why the answer is right and why the others are wrong.
- hint: one short nudge that does not give the answer away.

Return ONLY a JSON array. Each element:
{{"question": str, "options": [str, str, str, str], "answer": 1-4 (number of the correct option),
  "explanation": str, "hint": str}}"""


def _parse(text: str) -> list:
    """Accept a JSON array, or an object holding one (e.g. {"questions": [...]})."""
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    raw = (m.group(1) if m else text).strip()
    try:
        data = json.loads(raw)
    except Exception:
        start = raw.find("[")
        data = json.loads(raw[start:raw.rfind("]") + 1])
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])
    return data


def validate(item: dict, real_questions: list[dict]) -> str | None:
    """Return a problem description, or None if the question looks usable."""
    opts = item.get("options") or []
    if not str(item.get("question", "")).strip():
        return "empty question"
    if len(opts) != 4 or len({str(o).strip().lower() for o in opts}) != 4:
        return "needs 4 different options"
    try:
        a = int(item.get("answer"))
    except Exception:
        return "answer is not a number"
    if not 1 <= a <= 4:
        return "answer must be 1–4"
    if not str(item.get("explanation", "")).strip():
        return "no explanation"
    new = set(_tokens(item["question"]))
    for q in real_questions:
        old = set(_tokens(q["text"]))
        if new and old and len(new & old) / len(new | old) > 0.75:
            return "too close to a real past question"
    return None


def generate(api_key: str, model: str, unit: str, subtopic: str, pattern: str, n: int, level: int,
             examples: list[dict], real_questions: list[dict], facts: str = "") -> tuple[list[dict], list[str]]:
    """Ask Gemini for questions. Returns (rows ready to save as 'pending', problems)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=model, contents=build_prompt(unit, subtopic, pattern, n, level, examples, facts),
        config=types.GenerateContentConfig(temperature=0.7, response_mime_type="application/json"))
    return _rows_from(_parse(resp.text or "[]"), unit, subtopic, pattern, level, model, real_questions)


def generate_llama(cfg: dict, unit, subtopic, pattern, n, level, examples, real_questions, facts: str = ""):
    """Same as generate(), using the free AI services (Groq, Cerebras, OpenRouter) through llm.chat."""
    from . import llm

    prompt = build_prompt(unit, subtopic, pattern, n, level, examples, facts).replace(
        "Return ONLY a JSON array. Each element:", 'Return ONLY a JSON object {"questions": [...]}. Each element:')
    text = llm.chat(cfg, [{"role": "user", "content": prompt}], temperature=0.7, max_tokens=4000, json_mode=True,
                    timeout=60)
    return _rows_from(_parse(text), unit, subtopic, pattern, level, cfg.get("used", cfg["model"]), real_questions)


def _rows_from(items, unit, subtopic, pattern, level, model, real_questions):
    rows, problems = [], []
    for it in items:
        why = validate(it, real_questions)
        if why:
            problems.append(f"Dropped one question: {why}.")
            continue
        o = [str(x).strip() for x in it["options"]]
        rows.append({"id": uuid.uuid4().hex[:10], "created": now_iso(), "status": "pending", "unit": unit,
                     "subtopic": subtopic, "pattern": pattern, "level": level, "question": str(it["question"]).strip(),
                     "option1": o[0], "option2": o[1], "option3": o[2], "option4": o[3], "answer": int(it["answer"]),
                     "explanation": str(it.get("explanation", "")).strip(), "hint": str(it.get("hint", "")).strip(),
                     "model": model, "note": ""})
    return rows, problems


def as_question(row: dict) -> dict:
    """An approved AI question in the same shape as the paper questions."""
    lvl = int(row.get("level") or 2)
    return {"key": f"ai:{row['id']}", "text": row["question"],
            "options": [row["option1"], row["option2"], row["option3"], row["option4"]],
            "answer": int(row["answer"]) - 1, "unit": row["unit"], "subtopic": row["subtopic"],
            "pattern": row["pattern"], "level": lvl, "origin": "ai", "session": "AI-written, teacher-approved",
            "qno": 0, "display": "text", "status": "ok", "explanation": row.get("explanation"),
            "hint": row.get("hint"), "answer_source": "Written by AI, checked and approved by your teacher"}


def formats_for(unit: str) -> list[str]:
    """Formats NTA uses for recall units."""
    base = ["direct_fact", "definition", "multi_statement", "assertion_reason", "statement_i_ii", "match_list",
            "sequence", "negative", "concept_origin"]
    return [p for p in base if p in PATTERN_BY_ID]
