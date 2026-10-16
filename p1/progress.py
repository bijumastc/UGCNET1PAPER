"""A student's learning record: attempts, mastery, gaps, and what to practise next.

Mastery is a recency-weighted estimate (newer answers count more). Answers that needed
help earn partial credit. Attempts are kept in the class store (Google Sheet or local file).
"""
from __future__ import annotations

import random
import statistics
import time
from collections import Counter, defaultdict

from .patterns import pattern_level, pattern_name
from .store import now_iso
from .syllabus import QUESTIONS_PER_UNIT, UNITS, subtopic_name, unit_name

DECAY = 0.9
HINT_CREDIT = {0: 1.0, 1: 0.8, 2: 0.6, 3: 0.3, 4: 0.0}   # by help used: none, strategy, concept, 50-50, revealed
SECONDS_PER_Q = 72        # Paper 1: 50 questions in 60 minutes
LEVEL_UP = 0.7            # accuracy needed at a level before moving up


class Progress:
    def __init__(self, store, student_id: str = "me", name: str = ""):
        self.store, self.sid, self.name = store, str(student_id), name
        self._att = None

    # ------------------------------------------------------------ storage
    def record(self, q: dict, chosen, correct: bool, help_used: int, seconds: float, mode: str, points: int = 0):
        opts = q.get("options") or []

        def opt(i):
            if i is None or i == "" or not 0 <= int(i) < 4:
                return ""
            return f"({int(i) + 1}) " + (str(opts[int(i)])[:200] if len(opts) == 4 else "")
        row = {"time": now_iso(), "student_id": self.sid, "name": self.name, "question_key": q["key"],
               "source": q.get("origin", "paper"), "session": q.get("session", ""), "qno": q.get("qno", ""),
               "unit": q.get("unit"), "topic": q.get("subtopic"), "format": q.get("pattern"),
               "level": q.get("level") or pattern_level(q.get("pattern")),
               "chosen": "" if chosen is None else chosen, "correct": int(bool(correct)), "help_used": help_used,
               "seconds": round(float(seconds), 1), "mode": mode,
               "question": " ".join(str(q.get("text", "")).split())[:500],
               "your_answer": "shown answer" if chosen in (None, -1) and help_used >= 4 else opt(chosen),
               "correct_answer": opt(q.get("answer")), "points": int(points)}
        self.store.add_attempt(row)
        if self._att is not None:
            from .store import _norm_attempt

            self._att.append(_norm_attempt(row))

    def attempts(self) -> list[dict]:
        if self._att is None:
            self._att = self.store.attempts(self.sid)
        return self._att

    def get(self, key, default=None):
        return self.store.get(f"{self.sid}:{key}", default)

    def set(self, key, value):
        self.store.set(f"{self.sid}:{key}", value)

    def reset(self):
        self.store.delete_attempts(self.sid)
        self._att = None

    # ------------------------------------------------------------ mastery
    @staticmethod
    def _estimate(rows: list[dict]) -> tuple[float, int]:
        a = b = 1.0
        w = 1.0
        for r in reversed(rows):
            credit = HINT_CREDIT.get(min(r["help"], 4), 0) if r["correct"] else 0.0
            a += w * credit
            b += w * (1 - credit)
            w *= DECAY
        return a / (a + b), len(rows)

    def mastery(self, by: str = "unit") -> dict:
        groups = defaultdict(list)
        for r in self.attempts():
            k = r[by] if by != "unit_level" else (r["subtopic"], r["level"])
            if k:
                groups[k].append(r)
        return {k: self._estimate(v) for k, v in groups.items()}

    def level_for(self, subtopic: str) -> int:
        """Scaffold level the learner is working at in a sub-topic (1 → 3)."""
        rows = [r for r in self.attempts() if r["subtopic"] == subtopic]
        level = 1
        for lv in (1, 2):
            at = [r for r in rows if r["level"] == lv][-5:]
            if len(at) >= 3 and sum(r["correct"] and r["help"] <= 1 for r in at) / len(at) >= LEVEL_UP:
                level = lv + 1
            else:
                break
        return level

    # ------------------------------------------------------------ picking questions
    def weights(self, pool: list[dict] | None = None) -> dict:
        """Share of the exam per unit. The syllabus sets 5 questions (10 marks) in every unit."""
        return {u: QUESTIONS_PER_UNIT / (QUESTIONS_PER_UNIT * len(UNITS)) for u in UNITS}

    def due_reviews(self, pool_keys: set) -> list[str]:
        """Questions answered wrong (or only with heavy help) that are due again: after 10 min, 1, 3, 7 days."""
        gaps = [600, 86400, 3 * 86400, 7 * 86400]
        by = defaultdict(list)
        for r in self.attempts():
            by[r["qkey"]].append(r)
        now, due = time.time(), []
        for k, rows in by.items():
            if k not in pool_keys or not any((not r["correct"]) or r["help"] >= 3 for r in rows):
                continue
            streak = 0
            for r in reversed(rows):
                if r["correct"] and r["help"] <= 1:
                    streak += 1
                else:
                    break
            if streak >= len(gaps):
                continue
            if now - rows[-1]["ts"] >= gaps[streak]:
                due.append(k)
        return due

    def next_question(self, pool: list[dict], unit=None, subtopic=None, pattern=None, family=None,
                      exclude: set | None = None) -> dict | None:
        exclude = exclude or set()
        cand = [q for q in pool if q["key"] not in exclude]
        if unit:
            cand = [q for q in cand if q["unit"] == unit]
        if subtopic:
            cand = [q for q in cand if q["subtopic"] == subtopic]
        if pattern:
            cand = [q for q in cand if q["pattern"] == pattern]
        if family:
            cand = [q for q in cand if q.get("family") == family]
        if not cand:
            return None
        due = set(self.due_reviews({q["key"] for q in cand}))
        if due and random.random() < 0.3:
            return random.choice([q for q in cand if q["key"] in due])

        mu = self.mastery("unit")
        if not (unit or subtopic or family):
            w = self.weights(pool)
            units = sorted({q["unit"] for q in cand})
            prio = [((0.1 + w.get(u, 0)) * (1 - mu.get(u, (0.5, 0))[0]) + 0.3 / (1 + mu.get(u, (0, 0))[1]), u)
                    for u in units]
            prio.sort(reverse=True)
            top = prio[:4]
            pick = random.choices([u for _, u in top], weights=[p for p, _ in top])[0]
            cand = [q for q in cand if q["unit"] == pick]

        # scaffold: prefer questions at the learner's level in the chosen sub-topic
        ms = self.mastery("subtopic")
        sub = subtopic or min({q["subtopic"] for q in cand}, key=lambda s: ms.get(s, (0.5, 0))[0])
        lvl = self.level_for(sub)
        in_sub = [q for q in cand if q["subtopic"] == sub] or cand
        seen = Counter(r["qkey"] for r in self.attempts())
        in_sub.sort(key=lambda q: (abs((q.get("level") or 1) - lvl), seen.get(q["key"], 0), random.random()))
        return in_sub[0]

    def diagnostic_set(self, pool: list[dict], per_unit: int = 2) -> list[dict]:
        out = []
        by = defaultdict(list)
        for q in pool:
            by[q["unit"]].append(q)
        for u in UNITS:
            qs = by.get(u, [])
            random.shuffle(qs)
            qs.sort(key=lambda q: q.get("level") or 1)       # start easy within each unit
            out.extend(qs[:per_unit])
        random.shuffle(out)
        return out

    def mock_set(self, pool: list[dict], n: int = 50) -> list[dict]:
        """Like the real paper: 5 questions from every unit (fewer if a unit has fewer verified questions).
        Passage and data-set questions are kept together as in the exam."""
        by = defaultdict(list)
        for q in pool:
            by[q["unit"]].append(q)
        per = max(1, n // len(UNITS))
        out = []
        for u in UNITS:
            qs = by.get(u, [])
            groups = defaultdict(list)
            for q in qs:
                groups[q.get("group_id") or q["key"]].append(q)
            sets = list(groups.values())
            random.shuffle(sets)
            sets.sort(key=lambda g: -len(g) if u in ("U3", "U7") else 0)   # a whole passage / data set first
            picked = []
            for g in sets:
                if len(picked) >= per:
                    break
                picked.extend(sorted(g, key=lambda q: q["qno"])[: per - len(picked)])
            out.extend(picked)
        return out

    # ------------------------------------------------------------ deficits
    def report(self, pool: list[dict]) -> dict:
        rows = self.attempts()
        if not rows:
            return {"empty": True}
        overall = sum(r["correct"] for r in rows) / len(rows)
        w = self.weights(pool)
        mu, ms, mp = self.mastery("unit"), self.mastery("subtopic"), self.mastery("pattern")
        deficits = []

        # content gaps: weak sub-topics, weighted by how often they appear in the papers
        sub_freq = Counter(q["subtopic"] for q in pool if q.get("subtopic"))
        for sid, (m, n) in ms.items():
            if n >= 3 and m < 0.6:
                deficits.append({"type": "Content", "area": f"{unit_name(sid.split('.')[0])} → {subtopic_name(sid)}",
                                 "evidence": f"{m*100:.0f}% mastery over {n} questions",
                                 "action": "Re-read the Learn card for this topic, then practise it at Level 1.",
                                 "unit": sid.split(".")[0], "subtopic": sid,
                                 "priority": (1 - m) * (1 + sub_freq.get(sid, 0))})
        # format gaps: a question type that costs marks across topics
        by_pat = defaultdict(list)
        for r in rows:
            by_pat[r["pattern"]].append(r["correct"])
        for pid, vals in by_pat.items():
            acc = sum(vals) / len(vals)
            if len(vals) >= 4 and acc < overall - 0.15:
                deficits.append({"type": "Question format", "area": pattern_name(pid),
                                 "evidence": f"{acc*100:.0f}% correct vs {overall*100:.0f}% overall ({len(vals)} tries)",
                                 "action": "Drill this format (Practice → Drill a format) and use its strategy every time.",
                                 "pattern": pid, "priority": (overall - acc) * len(vals)})
        # speed
        secs = [r["seconds"] for r in rows if r["mode"] != "learn"]
        if len(secs) >= 8 and statistics.median(secs) > SECONDS_PER_Q:
            deficits.append({"type": "Speed", "area": "Time per question",
                             "evidence": f"median {statistics.median(secs):.0f}s; the exam allows about {SECONDS_PER_Q}s",
                             "action": "Take timed mock tests; skip and return to long questions.",
                             "priority": statistics.median(secs) / SECONDS_PER_Q})
        by_unit_time = defaultdict(list)
        for r in rows:
            by_unit_time[r["unit"]].append(r["seconds"])
        for u, v in by_unit_time.items():
            if len(v) >= 4 and statistics.median(v) > 1.6 * SECONDS_PER_Q:
                deficits.append({"type": "Speed", "area": unit_name(u),
                                 "evidence": f"median {statistics.median(v):.0f}s per question",
                                 "action": "Learn the shortcut methods in this unit's Learn cards.", "unit": u,
                                 "priority": statistics.median(v) / SECONDS_PER_Q})
        # help dependence
        right = [r for r in rows if r["correct"]]
        if len(right) >= 8:
            helped = sum(r["help"] >= 2 for r in right) / len(right)
            if helped > 0.4:
                deficits.append({"type": "Independence", "area": "Needs help to get answers right",
                                 "evidence": f"{helped*100:.0f}% of correct answers used concept help or 50-50",
                                 "action": "Try each question once without help; use help only after a first attempt.",
                                 "priority": helped * 2})
        # careless slips: fast wrong answers on easy questions
        slips = [r for r in rows if r["mode"] == "practice" and not r["correct"] and r["seconds"] < 20
                 and r["level"] == 1 and r["help"] == 0]
        if len(slips) >= 3:
            deficits.append({"type": "Careless slips", "area": "Fast wrong answers on Level-1 questions",
                             "evidence": f"{len(slips)} answers under 20 s were wrong",
                             "action": "Slow down on recall questions: read every option, watch for NOT/EXCEPT.",
                             "priority": len(slips) / 3})
        # coverage
        tried = {r["subtopic"] for r in rows}
        untried = [(sid, n) for sid, n in sub_freq.items() if sid not in tried and n >= 2]
        for sid, n in sorted(untried, key=lambda x: -x[1])[:5]:
            deficits.append({"type": "Not practised yet", "area": f"{unit_name(sid.split('.')[0])} → {subtopic_name(sid)}",
                             "evidence": f"{n} questions in your papers, none attempted",
                             "action": "Start with the Learn card, then Level 1 questions.", "unit": sid.split(".")[0],
                             "subtopic": sid, "priority": 0.3 * n})
        deficits.sort(key=lambda d: -d["priority"])

        projected = sum(w[u] * mu.get(u, (0.25, 0))[0] for u in UNITS) * 100
        return {"empty": False, "overall": overall, "n": len(rows), "projected": projected,
                "unit_mastery": mu, "subtopic_mastery": ms, "pattern_mastery": mp, "weights": w,
                "deficits": deficits, "median_seconds": statistics.median(secs) if secs else None}
