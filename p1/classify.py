"""Sort questions into syllabus units and sub-topics, detect their format, and group look-alikes."""
from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache

from .patterns import detect_pattern, pattern_level
from .syllabus import UNITS

SYLLOGISM = re.compile(r"\b(all|no|some)\s+\w+(\s+\w+)?\s+are\b.*\b(all|no|some)\s+\w+(\s+\w+)?\s+are\b", re.I | re.S)
TABLEISH = re.compile(r"\b(table|chart|graph|data|diagram|percentage|distribution)\b", re.I)


def _norm(text: str) -> str:
    """Lower-case and replace stray symbols (OCR often adds '!' '|' etc.) with spaces."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9%&\-./\s]", " ", text.lower()))


@lru_cache(maxsize=1)
def _compiled():
    out = {}
    for uid, u in UNITS.items():
        for sid, (_, kws) in u["subtopics"].items():
            regs = []
            for kw in kws:
                word, w = (kw, None) if isinstance(kw, str) else kw
                if w is None:
                    w = 1 + word.count(" ")
                if w <= 0:
                    continue
                wl = _norm(word).strip()
                left = r"(?<![a-z0-9])" if wl[:1].isalnum() else ""
                right = r"(?![a-z0-9])" if wl[-1:].isalnum() else ""
                regs.append((re.compile(left + re.escape(wl) + right), w, word))
            out[sid] = regs
    return out


def score_subtopics(text: str) -> tuple[dict, dict]:
    low = _norm(text)
    scores, hits = {}, {}
    for sid, regs in _compiled().items():
        s, h = 0.0, []
        for rx, w, word in regs:
            n = len(rx.findall(low))
            if n:
                s += w * min(n, 2)
                h.append(word)
        if s:
            scores[sid], hits[sid] = s, h
    if SYLLOGISM.search(text):
        scores["U6.3"] = scores.get("U6.3", 0) + 8
    return scores, hits


def group_unit(group_text: str | None) -> str | None:
    """NTA question groups are either a reading passage (Unit 3) or a data set (Unit 7)."""
    if not group_text:
        return None
    digits = len(re.findall(r"\d", group_text))
    if TABLEISH.search(group_text) or digits > 0.08 * max(len(group_text), 1):
        return "U7"
    return "U3"


def classify(text: str, options: list | None = None, group_text: str | None = None) -> dict:
    """Return unit, subtopic, pattern, level, confidence, keywords and whether it needs a human look."""
    body = text + "\n" + "\n".join(options or [])
    pattern = detect_pattern(text)
    g_unit = group_unit(group_text)
    if g_unit:
        sid = "U7.3" if g_unit == "U7" else "U3.1"
        if g_unit == "U3":
            pattern = "passage" if pattern in ("direct_fact", "definition") else pattern
        else:
            pattern = "data_interpretation" if pattern in ("direct_fact", "numerical", "definition") else pattern
        return {"unit": g_unit, "subtopic": sid, "pattern": pattern, "level": max(2, pattern_level(pattern)),
                "confidence": 0.95, "keywords": [], "needs_review": False, "guess": g_unit}

    rows = [l for l in text.splitlines() if len(re.findall(r"\d+(?:\.\d+)?%?", l)) >= 2]
    if len(rows) >= 3 and re.search(r"\btable\b|\bchart\b|\bgraph\b|\bdata\b", text, re.I):
        p2 = "data_interpretation" if pattern in ("direct_fact", "numerical", "definition") else pattern
        return {"unit": "U7", "subtopic": "U7.3", "pattern": p2, "level": 3, "confidence": 0.9,
                "keywords": ["table in question"], "needs_review": False, "guess": "U7"}
    scores, hits = score_subtopics(body)
    unit_scores = Counter()
    for sid, s in scores.items():
        unit_scores[sid.split(".")[0]] += s
    if not unit_scores:
        return {"unit": None, "subtopic": None, "pattern": pattern, "level": pattern_level(pattern),
                "confidence": 0.0, "keywords": [], "needs_review": True, "guess": None}
    ranked = unit_scores.most_common()
    top_u, top_s = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    margin = (top_s - second) / top_s
    conf = round(min(1.0, 0.55 * margin + 0.45 * min(1.0, top_s / 10)), 2)
    sid = max((s for s in scores if s.startswith(top_u + ".")), key=scores.get)
    needs_review = top_s < 2 or margin < 0.2
    return {"unit": None if needs_review else top_u, "subtopic": None if needs_review else sid,
            "pattern": pattern, "level": pattern_level(pattern), "confidence": conf,
            "keywords": hits.get(sid, [])[:6], "needs_review": needs_review, "guess": top_u,
            "guess_subtopic": sid}


# ------------------------------------------------------------------ look-alike grouping
STOP = set("""the of and to in is are was were be by for on as at or if that this these those which what who
with from into than then there their they them it its not no all any some each both following given
below above correct statement statements choose answer options option between among about after
before during under over only also can could would should will may might must has have had been
does did do most more less least true false one two three four five list match arrange order
sequence identify select regarding related assertion reason based question questions""".split())


def _tokens(t: str) -> list[str]:
    return [w for w in re.findall(r"[a-z][a-z\-]{2,}", t.lower()) if w not in STOP]


def families(questions: list[dict], threshold: float = 0.35) -> dict:
    """Group questions that ask about the same thing (within a unit) using TF-IDF cosine similarity.

    Returns {question_key: family_id}; family ids are shared by look-alike questions.
    """
    docs = {q["key"]: _tokens(q["text"] + " " + " ".join(q.get("options") or [])) for q in questions}
    df = Counter()
    for toks in docs.values():
        df.update(set(toks))
    n = max(len(docs), 1)
    vecs = {}
    for k, toks in docs.items():
        tf = Counter(toks)
        v = {w: (c / len(toks)) * math.log((1 + n) / (1 + df[w])) for w, c in tf.items()} if toks else {}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs[k] = {w: x / norm for w, x in v.items()}

    parent = {k: k for k in docs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    by_unit: dict = {}
    session = {q["key"]: q.get("session") for q in questions}
    for q in questions:
        by_unit.setdefault(q.get("unit") or q.get("unit_guess") or "?", []).append(q["key"])
    for keys in by_unit.values():
        for i in range(len(keys)):
            vi = vecs[keys[i]]
            for j in range(i + 1, len(keys)):
                if session[keys[i]] == session[keys[j]]:
                    continue          # recurring = asked again in a different shift/session
                vj = vecs[keys[j]]
                if len(vi) > len(vj):
                    sim = sum(x * vi.get(w, 0) for w, x in vj.items())
                else:
                    sim = sum(x * vj.get(w, 0) for w, x in vi.items())
                if sim >= threshold:
                    parent[find(keys[i])] = find(keys[j])
    return {k: find(k) for k in docs}


def family_label(questions: list[dict]) -> str:
    """Short label from the words the family's questions share most."""
    c = Counter()
    for q in questions:
        c.update(set(_tokens(q["text"])))
    common = [w for w, n in c.most_common(6) if n >= max(2, len(questions) // 2)]
    return ", ".join(common[:4]) or (questions[0]["text"][:50] + "…")


def subtopic_within(unit: str, text: str, options: list | None = None) -> str:
    """Best-matching topic inside a known unit, or the unit's 'Other topics' bucket."""
    scores, _ = score_subtopics(text + "\n" + "\n".join(options or []))
    inside = {sid: v for sid, v in scores.items() if sid.split(".")[0] == unit}
    return max(inside, key=inside.get) if inside else f"{unit}.99"


def block_units(questions: list) -> dict | None:
    """NTA papers set Paper 1 in ten blocks of five questions, one block per unit
    (the syllabus says five questions per unit). If the keyword guesses show that layout clearly,
    return {block_index: unit}; otherwise None and per-question keywords are used."""
    by_q = {q["qno"]: q for q in questions}
    if len([n for n in range(1, 51) if n in by_q]) < 45:
        return None
    blocks = {}
    for b in range(10):
        votes = Counter((by_q[n].get("unit") or by_q[n].get("unit_guess")) for n in range(b * 5 + 1, b * 5 + 6)
                        if n in by_q and (by_q[n].get("unit") or by_q[n].get("unit_guess")))
        if votes:
            u, c = votes.most_common(1)[0]
            if c >= 3:
                blocks[b] = u
    if len(blocks) < 8 or len(set(blocks.values())) != len(blocks):
        return None
    missing_b = [b for b in range(10) if b not in blocks]
    missing_u = [u for u in UNITS if u not in blocks.values()]
    if len(missing_b) == 1 and len(missing_u) == 1:
        blocks[missing_b[0]] = missing_u[0]
    return blocks
