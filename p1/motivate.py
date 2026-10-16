"""Encouragement: smiley feedback, streaks, a daily goal and badges.

Tone: warm and specific, never shaming. Mistakes are framed as information for the next step.
"""
from __future__ import annotations

import random
import time
from collections import Counter, defaultdict
from datetime import date, datetime

from .store import IST
from .syllabus import UNITS, unit_name

CORRECT_FIRST = ["🌟 Excellent! Right first time, no help.", "😃 Spot on!", "🎯 Bull's-eye!",
                 "👏 Well done, you've got this one.", "💡 Sharp thinking!"]
CORRECT_HELPED = ["👍 Got there with some help. Next time try one step less.",
                  "🙂 Correct! The help did its job; now you know the method.",
                  "🌱 Nice. You're learning the approach; soon you won't need the hint."]
WRONG = ["🙂 Not this time. Mistakes show us exactly what to learn next.",
         "💪 Good try! Read the method below, then try a similar one.",
         "🤗 No worries. Every topper has got this kind wrong at least once.",
         "🧭 Close call. Look at the working below; it will click."]
REVEALED = ["📘 Good choice to look. Read the working carefully, then try a similar one."]
STREAK = {3: "🔥 3 in a row!", 5: "🚀 5 in a row, you're on fire!", 10: "🏆 10 in a row! Outstanding!",
          15: "👑 15 in a row! Unstoppable!"}


def feedback(correct: bool, help_used: int, run: int, rng=random) -> str:
    """Message after an answer. run = current streak of correct answers (including this one)."""
    if help_used >= 4:
        return rng.choice(REVEALED)
    if not correct:
        return rng.choice(WRONG)
    msg = rng.choice(CORRECT_FIRST if help_used == 0 else CORRECT_HELPED)
    if run in STREAK:
        msg += "  " + STREAK[run]
    return msg


def current_run(attempts: list[dict]) -> int:
    n = 0
    for r in reversed(attempts):
        if r["correct"]:
            n += 1
        else:
            break
    return n


def _day(ts: float) -> date:
    return datetime.fromtimestamp(ts, IST).date()


def _today() -> date:
    return datetime.now(IST).date()


def today_count(attempts: list[dict]) -> int:
    t = _today()
    return sum(1 for r in attempts if _day(r["ts"]) == t)


def day_streak(attempts: list[dict], min_per_day: int = 5) -> int:
    """Consecutive days (ending today or yesterday) with at least min_per_day answers."""
    per = Counter(_day(r["ts"]) for r in attempts)
    days = {d for d, n in per.items() if n >= min_per_day}
    if not days:
        return 0
    d = _today()
    if d not in days:
        d = date.fromordinal(d.toordinal() - 1)
        if d not in days:
            return 0
    n = 0
    while d in days:
        n += 1
        d = date.fromordinal(d.toordinal() - 1)
    return n


def goal_plant(done: int, goal: int) -> str:
    f = done / max(goal, 1)
    return "🌰" if f == 0 else "🌱" if f < 0.34 else "🌿" if f < 0.67 else "🪴" if f < 1 else "🌳"


def greeting(name: str) -> str:
    h = datetime.now(IST).hour
    part = "Good morning" if h < 12 else "Good afternoon" if h < 17 else "Good evening"
    first = (name or "").split()[0] if name else ""
    return f"{part}{', ' + first if first else ''}! 😊"


def badges(attempts: list[dict], unit_mastery: dict, target: float) -> list[tuple[str, str]]:
    """(emoji+title, how it was earned) for every badge earned so far."""
    out = []
    n = len(attempts)
    for k, title in [(1, "🐣 First step"), (25, "🥉 25 questions"), (100, "🥈 100 questions"), (250, "🥇 250 questions"),
                     (500, "💎 500 questions")]:
        if n >= k:
            out.append((title, f"Answered {k} question{'s' if k > 1 else ''}"))
    best = 0
    run = 0
    for r in attempts:
        run = run + 1 if r["correct"] else 0
        best = max(best, run)
    for k, title in [(5, "🔥 Hot streak"), (10, "🚀 Rocket"), (20, "👑 Unstoppable")]:
        if best >= k:
            out.append((title, f"{k} correct answers in a row"))
    ds = day_streak(attempts)
    for k, title in [(3, "📅 3-day habit"), (7, "🗓️ 7-day habit"), (21, "🏅 21-day habit")]:
        if ds >= k:
            out.append((title, f"Practised {k} days in a row"))
    for u, (m, cnt) in unit_mastery.items():
        if cnt >= 10 and m >= target:
            out.append((f"🏅 {unit_name(u)} master", f"Mastery above your target with {cnt} answers"))
    tests = [r for r in attempts if r["mode"] == "test"]
    by_test = defaultdict(list)
    for r in tests:
        by_test[int(r["ts"] // 60)].append(r["correct"])   # answers submitted together = one test
    if any(len(v) >= 40 and sum(v) / len(v) >= target for v in by_test.values()):
        out.append(("🎓 Mock champion", "Scored above target in a full mock"))
    return out


def level_up_message(topic: str, new_level: int) -> str:
    return {2: f"🎉 Level up! You've moved to Level 2 in {topic}. Questions now need a little more thinking.",
            3: f"🏆 Level 3 unlocked in {topic}! You're working at exam level now."}.get(new_level, "")


def test_message(pct: float, target: float) -> str:
    if pct >= target:
        return "🎉 Above your target! This is JRF-level work. Keep it steady."
    if pct >= target - 0.1:
        return "😊 So close to your target! A little more practice on your weak units will get you there."
    if pct >= 0.4:
        return "💪 Solid base. Check 'My progress' for the 2–3 topics that will lift your score fastest."
    return "🌱 Every expert started here. Begin with Learn, then Level 1 practice; you'll see the score climb."


# ------------------------------------------------------------------ points and ranks (a bit of game)
RANKS = [(0, "🌱 Seedling"), (150, "📗 Learner"), (500, "📘 Achiever"), (1200, "🎓 Scholar"),
         (2500, "🏅 NET Ready"), (5000, "🥇 JRF Contender"), (9000, "👑 JRF Ready")]
FAST_SECONDS = 72                     # the exam's average time per question


def points(correct: bool, level: int, help_used: int, seconds: float, run: int) -> int:
    """Points for one answer. run = correct answers in a row including this one.
    Right: 10 per level, +5 without help, +5 if within exam pace, ×1.5 on a 3-combo, ×2 on a 5-combo.
    Help reduces points step by step. A wrong answer still earns 2 for the effort."""
    if help_used >= 4:
        return 1
    if not correct:
        return 2
    p = 10 * max(1, int(level or 1))
    if help_used == 0:
        p += 5
    if seconds and seconds <= FAST_SECONDS:
        p += 5
    p = p * {0: 1.0, 1: 0.8, 2: 0.6, 3: 0.3}.get(help_used, 0.3)
    if run >= 5:
        p *= 2
    elif run >= 3:
        p *= 1.5
    return max(1, round(p))


def total_points(attempts: list[dict]) -> int:
    return sum(int(float(r.get("points") or 0)) for r in attempts)


def rank(pts: int) -> tuple[str, int, int | None, str | None]:
    """(rank name, floor, next floor, next rank name)."""
    cur = RANKS[0]
    for i, (floor, name) in enumerate(RANKS):
        if pts >= floor:
            cur = (name, floor, RANKS[i + 1][0] if i + 1 < len(RANKS) else None,
                   RANKS[i + 1][1] if i + 1 < len(RANKS) else None)
    return cur


def combo_label(run: int) -> str:
    return "" if run < 3 else "🔥 ×1.5 combo" if run < 5 else "⚡ ×2 combo"


def public_name(name: str) -> str:
    """First name + initial for leaderboards (privacy)."""
    parts = (name or "").split()
    return parts[0] + (f" {parts[-1][0]}." if len(parts) > 1 else "") if parts else "Student"
