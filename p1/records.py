"""What goes into the Google Sheet beyond single answers: activity (logins, pages), test results,
time spent, and the per-student summary rows (Progress, Unit_Scores)."""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime

from . import motivate as M
from .progress import Progress
from .store import IST, UNIT_COLS, now_iso, to_ts
from .syllabus import UNITS, subtopic_name, unit_name

SESSION_GAP = 15 * 60          # a pause longer than this starts a new study session


def log(store, user: dict, event: str, detail: str = ""):
    """Append one line to the Activity tab (login, logout, page, test_start…)."""
    if user.get("role") == "owner":
        return
    store.add_row("Activity", {"time": now_iso(), "student_id": user["id"], "name": user.get("name", ""),
                               "event": event, "detail": str(detail)[:200]})


def log_test(store, user: dict, kind: str, results: list[tuple[dict, int | None]], minutes: float, pts: int = 0):
    """results = [(question, chosen)], recorded in the Tests tab."""
    by = defaultdict(lambda: [0, 0])
    for q, c in results:
        by[q["unit"]][0] += int(c is not None and c == q["answer"])
        by[q["unit"]][1] += 1
    right = sum(v[0] for v in by.values())
    n = len(results)
    store.add_row("Tests", {"time": now_iso(), "student_id": user["id"], "name": user.get("name", ""), "kind": kind,
                            "questions": n, "correct": right, "marks": right * 2, "out_of": n * 2,
                            "percent": round(100 * right / max(n, 1)), "minutes": round(minutes, 1), "points": pts,
                            "by_unit": "; ".join(f"{u} {a}/{b}" for u, (a, b) in sorted(by.items(),
                                                                                     key=lambda x: int(x[0][1:])))})


def study_blocks(attempts: list[dict], other_times: list[float]) -> list[tuple[float, float]]:
    """Merge every sign of activity into study sessions [(start, end)].
    An answer covers the seconds spent on it; a page visit or AI question counts one minute."""
    spans = [(r["ts"] - min(float(r.get("seconds") or 0), 600), r["ts"]) for r in attempts if r.get("ts")]
    spans += [(t, t + 60) for t in other_times if t]
    spans.sort()
    out = []
    for s, e in spans:
        if out and s - out[-1][1] <= SESSION_GAP:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, max(e, s + 60)))
    return out


def summary(student: dict, prog: Progress, pool: list[dict], activity: list[dict], chats: list[dict],
            tests: list[dict], target: float) -> tuple[dict, dict]:
    """(Progress row, Unit_Scores row) for one student."""
    a = prog.attempts()
    act_ts = [to_ts(r.get("time")) for r in activity]
    blocks = study_blocks(a, act_ts + [to_ts(r.get("time")) for r in chats])
    now, week = time.time(), time.time() - 7 * 86400
    mins = sum(e - s for s, e in blocks) / 60
    mins7 = sum(max(0, e - max(s, week)) for s, e in blocks) / 60
    rep = prog.report(pool) if a else {"empty": True}
    mu = prog.mastery("unit")
    weakest = min(((u, m) for u, (m, n) in mu.items() if n >= 3), key=lambda x: x[1], default=(None, 0))[0]
    last = max([r["ts"] for r in a] + act_ts, default=0)
    proj = None if rep.get("empty") else rep["projected"]
    idle = (now - last) / 86400 if last else None
    status = "not started" if not a else "inactive 3+ days" if idle > 3 else \
        "on track" if proj and proj >= target * 100 else "working"
    pts = M.total_points(a)
    tests = sorted(tests, key=lambda r: to_ts(r.get("time")))
    pcts = [float(r.get("percent") or 0) for r in tests if r.get("kind") in ("Diagnostic", "Mock")]
    days = {datetime.fromtimestamp(t, IST).date() for t in [r["ts"] for r in a] + act_ts if t}
    deficits = [] if rep.get("empty") else rep["deficits"][:3]
    row = {"student_id": student["student_id"], "name": student["name"], "batch": student.get("batch", ""),
           "status": status, "last_active": datetime.fromtimestamp(last, IST).strftime("%Y-%m-%d %H:%M") if last else "",
           "logins": sum(r.get("event") == "login" for r in activity), "days_active": len(days),
           "minutes_total": round(mins), "minutes_7_days": round(mins7),
           "practice_sessions": sum(1 for s, e in blocks if any(s <= r["ts"] <= e for r in a)),
           "questions_total": len(a), "questions_7_days": sum(r["ts"] >= week for r in a),
           "correct_total": sum(r["correct"] for r in a),
           "accuracy": round(sum(r["correct"] for r in a) / len(a) * 100) if a else "",
           "tests_taken": len(tests), "last_test_pct": round(pcts[-1]) if pcts else "",
           "best_test_pct": round(max(pcts)) if pcts else "",
           "projected_score": round(proj) if proj is not None else "", "day_streak": M.day_streak(a),
           "points": pts, "rank": M.rank(pts)[0], "weakest_unit": unit_name(weakest) if weakest else "",
           "top_deficits": " | ".join(f"{d['type']}: {d['area']} ({d['evidence']})" for d in deficits),
           "help_share": round(sum(r["help"] >= 2 for r in a) / len(a) * 100) if a else "",
           "ai_tutor_questions": len(chats), "updated": now_iso()}
    units = {"student_id": student["student_id"], "name": student["name"], "updated": now_iso()}
    for u in UNITS:
        m = mu.get(u)
        units[u] = f"{round(m[0] * 100)}% ({m[1]})" if m else ""
    return row, units


def refresh_one(C, every: int = 10, force: bool = False):
    """Keep this student's Progress and Unit_Scores rows current (after every few answers, tests, logout)."""
    if C.user["role"] != "student":
        return
    n = len(C.prog.attempts())
    import streamlit as st

    key = "_last_summary_n"
    if not force and n - st.session_state.get(key, 0) < every:
        return
    st.session_state[key] = n
    s = next((x for x in C.store.students() if str(x["student_id"]) == str(C.user["id"])),
             {"student_id": C.user["id"], "name": C.user["name"]})
    try:
        row, units = summary(s, C.prog, C.POOL, C.store.rows("Activity", C.user["id"]), C.store.ai_log(C.user["id"]),
                             C.store.rows("Tests", C.user["id"]), float(C.store.get("class:target", 70)) / 100)
        C.store.upsert_summary("Progress", row)
        C.store.upsert_summary("Unit_Scores", units)
    except Exception as e:                       # never interrupt a student because of the sheet
        getattr(C.store, "errors", []).append(f"summary: {e}")


def class_summaries(C, progs: dict) -> tuple[list[dict], list[dict]]:
    """Progress and Unit_Scores rows for the whole class (teacher dashboard)."""
    act, chats, tests = defaultdict(list), defaultdict(list), defaultdict(list)
    for r in C.store.rows("Activity"):
        act[str(r.get("student_id"))].append(r)
    for r in C.store.ai_log():
        chats[str(r.get("student_id"))].append(r)
    for r in C.store.rows("Tests"):
        tests[str(r.get("student_id"))].append(r)
    target = float(C.store.get("class:target", 70)) / 100
    rows, units = [], []
    studs = {str(s["student_id"]): s for s in C.store.students()}
    for sid, p in progs.items():
        r, u = summary(studs.get(sid, {"student_id": sid, "name": p.name}), p, C.POOL, act[sid], chats[sid],
                       tests[sid], target)
        rows.append(r)
        units.append(u)
    return rows, units


def leaderboard(store, since_ts: float, mode: str | None = None) -> list[dict]:
    """Points per student since a time (optionally one mode, e.g. 'challenge'). First names only."""
    names = {str(s["student_id"]): s["name"] for s in store.students()}
    agg = defaultdict(lambda: {"points": 0, "correct": 0, "answers": 0, "seconds": 0.0})
    for r in store.attempts():
        if r["ts"] < since_ts or (mode and r.get("mode") != mode):
            continue
        g = agg[str(r["student_id"])]
        g["points"] += int(r.get("points") or 0)
        g["correct"] += r["correct"]
        g["answers"] += 1
        g["seconds"] += float(r.get("seconds") or 0)
    out = [{"sid": sid, "Student": M.public_name(names.get(sid, sid)), **g} for sid, g in agg.items() if sid in names]
    out.sort(key=lambda x: (-x["points"], x["seconds"]))
    return out
