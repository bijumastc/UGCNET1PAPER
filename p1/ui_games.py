"""Game-style practice: points bar, daily missions, ⚡ Speed round, 🏆 Daily class challenge, leaderboard."""
from __future__ import annotations

import random
import time
from datetime import datetime

import pandas as pd
import streamlit as st

from . import generators as G
from . import motivate as M
from . import records as R
from .solvers import worked_solution
from .store import IST
from .syllabus import UNITS, subtopic_name, unit_name
from .ui_common import answer_text, option_label, show_question, ss, steps_md

ROUND_LEN = 10
SPEED_LIMIT = 60          # seconds per question in a speed round
CHALLENGE_LIMIT = 72      # exam pace


# ------------------------------------------------------------------ header and missions
def points_bar(C):
    att = C.prog.attempts()
    pts = M.total_points(att)
    name, floor, nxt, nxt_name = M.rank(pts)
    run = M.current_run(att)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⭐ Points", f"{pts:,}")
    c2.metric("Rank", name)
    c3.metric("Combo", f"{run} in a row" + (f" {M.combo_label(run).split()[0]}" if run >= 3 else ""))
    n = M.today_count(att)
    c4.metric("Today", f"{n} answer{'' if n == 1 else 's'}")
    if nxt:
        st.progress(min(1.0, (pts - floor) / (nxt - floor)), text=f"{nxt - pts} points to {nxt_name}")


def _today_rows(att):
    t = datetime.now(IST).date()
    return [r for r in att if datetime.fromtimestamp(r["ts"], IST).date() == t]


def missions(C, goal: int) -> list[tuple[bool, str]]:
    today = _today_rows(C.prog.attempts())
    best = run = 0
    for r in today:
        run = run + 1 if r["correct"] else 0
        best = max(best, run)
    return [(len(today) >= goal, f"Answer {goal} questions today"),
            (best >= 3, "Get a 3-answer combo 🔥"),
            (any(r.get("mode") == "challenge" for r in today), "Play today's 🏆 Daily class challenge"),
            (any(r.get("mode") == "speed" for r in today), "Finish a ⚡ Speed round")]


def show_missions(C, goal: int):
    ms = missions(C, goal)
    done = sum(d for d, _ in ms)
    with st.container(border=True):
        st.markdown(f"**🗺️ Today's missions · {done}/{len(ms)}**" + ("  🎉 All done!" if done == len(ms) else ""))
        st.markdown("  \n".join(f"{'✅' if d else '⬜'} {t}" for d, t in ms))


def leaderboard_on(C) -> bool:
    return C.store.get("class:leaderboard_on", "1") == "1"


def show_leaderboard(C, since_ts: float, mode: str | None, title: str, top: int = 10):
    rows = R.leaderboard(C.store, since_ts, mode)
    st.markdown(f"**{title}**")
    if not rows:
        st.caption("No scores yet. Be the first! 🚀")
        return
    medals = ["🥇", "🥈", "🥉"]
    tab = [{"#": medals[i] if i < 3 else str(i + 1), "Student": r["Student"], "Points": r["points"],
            "Correct": f"{r['correct']}/{r['answers']}"} for i, r in enumerate(rows[:top])]
    st.dataframe(pd.DataFrame(tab), hide_index=True, width="stretch")
    me = next((i for i, r in enumerate(rows) if r["sid"] == str(C.user["id"])), None)
    if me is not None and me >= top:
        st.caption(f"You are #{me + 1} with {rows[me]['points']} points. Keep going! 💪")


def week_start() -> float:
    now = datetime.now(IST)
    monday = now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() - now.weekday() * 86400
    return monday


def day_start() -> float:
    return datetime.now(IST).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()


# ------------------------------------------------------------------ choosing round questions
def _gen_question(gid, level, seed):
    lv = min(max(level, min(G.GEN[gid]["levels"])), max(G.GEN[gid]["levels"]))
    q = G.make(gid, lv, seed)
    if q["key"].count(":") == 4:                    # a data set: use its first question
        q = G.make(gid, lv, int(q["key"].split(":")[3]), 0)
    return q


def daily_keys(C) -> list[str]:
    """The same 10 questions for the whole class today: 6 past-paper questions from different units + 4 generated."""
    seed = datetime.now(IST).date().toordinal()
    rng = random.Random(seed)
    paper = sorted((q for q in C.POOL if q.get("origin") != "ai" and not q.get("group_id")), key=lambda q: q["key"])
    keys = []
    units = list(UNITS)
    rng.shuffle(units)
    for u in units:
        cand = [q for q in paper if q["unit"] == u]
        if cand and len(keys) < 6:
            keys.append(rng.choice(cand)["key"])
    gids = sorted(G.GEN)
    rng.shuffle(gids)
    for i, gid in enumerate(gids[: ROUND_LEN - len(keys)]):
        keys.append(_gen_question(gid, 2, seed * 100 + i)["key"])
    rng.shuffle(keys)
    return keys


def speed_keys(C) -> list[str]:
    """10 questions aimed at the student's weaker areas: past papers where loaded, plus generated ones."""
    keys, used = [], set()
    paper = [q for q in C.POOL if not q.get("group_id")]
    n_paper = min(6, len(paper))
    for _ in range(n_paper):
        q = C.prog.next_question(paper, exclude=used)
        if q:
            keys.append(q["key"])
            used.add(q["key"])
    gids = list(G.GEN)
    random.shuffle(gids)
    for gid in gids[: ROUND_LEN - len(keys)]:
        keys.append(_gen_question(gid, C.prog.level_for(G.GEN[gid]["subtopic"]), random.randrange(10 ** 9))["key"])
    random.shuffle(keys)
    return keys


# ------------------------------------------------------------------ the round itself
def _countdown(limit: float, left: float, uid: str):
    frac = max(0.0, min(1.0, left / limit)) * 100
    anim = "cd" + "".join(ch for ch in uid if ch.isalnum())[-12:]
    st.markdown(
        f"""<div style="height:10px;background:#e5e7eb;border-radius:6px;overflow:hidden;margin:4px 0 2px">
        <div style="height:100%;width:{frac:.1f}%;background:linear-gradient(90deg,#22c55e,#eab308,#ef4444);
        animation:{anim} {max(left, 0.1):.1f}s linear forwards"></div></div>
        <style>@keyframes {anim} {{ from {{ width:{frac:.1f}%; }} to {{ width:0%; }} }}</style>""",
        unsafe_allow_html=True)
    st.caption(f"⏱️ {limit:.0f} seconds per question. Answer within the bar for bonus points.")


def page_round(C, kind: str):
    """kind: 'speed' or 'challenge'."""
    label = "⚡ Speed round" if kind == "speed" else "🏆 Daily class challenge"
    limit = SPEED_LIMIT if kind == "speed" else CHALLENGE_LIMIT
    rnd = ss.get("rnd")
    if rnd and rnd["kind"] != kind:
        rnd = None
    if rnd is None:
        if kind == "challenge":
            st.markdown("Everyone in the class gets **the same 10 questions today**. One go per day. "
                        "Points for correct answers, speed and combos. 🏆")
            played = [r for r in C.prog.attempts() if r.get("mode") == "challenge" and r["ts"] >= day_start()]
            if played and C.user["role"] == "student":
                st.success(f"You've played today's challenge: {sum(r['correct'] for r in played)}/{len(played)} "
                           f"correct, {sum(r.get('points') or 0 for r in played)} points. New one tomorrow! 🌅")
                if leaderboard_on(C):
                    show_leaderboard(C, day_start(), "challenge", "Today's challenge leaderboard")
                return
        else:
            st.markdown(f"**10 quick questions**, {SPEED_LIMIT} seconds each, picked from your weaker areas. "
                        "Beat your best score! ⚡")
            best = max((int(float(r.get("points") or 0)) for r in C.store.rows("Tests", C.user["id"])
                        if r.get("kind") == "Speed round"), default=0)
            if best:
                st.caption(f"Your best speed round: {best} points")
        if st.button(f"Start the {label.split(' ', 1)[1].lower()}", type="primary"):
            keys = daily_keys(C) if kind == "challenge" else speed_keys(C)
            ss.rnd = {"kind": kind, "keys": keys, "i": 0, "res": [], "pts": 0, "run": 0, "t0": time.time(),
                      "qt0": time.time(), "answered": None, "last": None}
            R.log(C.store, C.user, "round_start", label)
            st.rerun()
        if kind == "challenge" and leaderboard_on(C):
            show_leaderboard(C, day_start(), "challenge", "Today's challenge leaderboard")
        return

    if rnd["i"] >= len(rnd["keys"]):
        _round_summary(C, rnd, label)
        return
    q = C.get_q(rnd["keys"][rnd["i"]])
    if q is None:                                   # question no longer available: skip it
        rnd["i"] += 1
        st.rerun()
    right = sum(c is not None and c == qq["answer"] for qq, c in rnd["res"])
    st.markdown(f"**{label}** · Question {rnd['i'] + 1} of {len(rnd['keys'])} · ⭐ {rnd['pts']} pts · "
                f"✅ {right} · {M.combo_label(rnd['run']) or '🎯 no combo yet'}")
    st.progress(rnd["i"] / len(rnd["keys"]))
    st.caption(f"{unit_name(q['unit'])} → {subtopic_name(q['subtopic'])}")
    show_question(C, q)
    if rnd["answered"] is None:
        _countdown(limit, limit - (time.time() - rnd["qt0"]), f"{rnd['i']}{q['key']}")
        choice = st.radio("Your answer", list(range(4)), index=None, format_func=lambda i: option_label(q, i),
                          key=f"rq_{rnd['i']}_{q['key']}", horizontal=q.get("display") == "image")
        b1, b2 = st.columns([1, 1])
        if b1.button("Submit", type="primary", disabled=choice is None):
            _answer(C, rnd, q, choice, limit)
            st.rerun()
        if b2.button("Skip ⏭️"):
            _answer(C, rnd, q, None, limit)
            st.rerun()
        return
    last = rnd["last"]
    if last["ok"]:
        st.success(f"✅ Correct! **+{last['pts']} ⭐**" + (f"  {M.combo_label(rnd['run'])}" if rnd["run"] >= 3 else "")
                   + ("" if last["in_time"] else "  ⏰ (a bit slow: no speed bonus)"))
    else:
        st.error(("⏭️ Skipped. " if last["choice"] is None else "❌ Not this time. ") + f"Answer: **{answer_text(q)}**")
    steps = q.get("steps") or worked_solution(q)
    if steps or q.get("explanation"):
        with st.expander("🛠️ See the working", expanded=not last["ok"]):
            if steps:
                st.markdown(steps_md(steps))
            if q.get("explanation"):
                st.markdown(q["explanation"])
    if st.button("Next ➜" if rnd["i"] + 1 < len(rnd["keys"]) else "See my result 🏁", type="primary"):
        rnd["i"] += 1
        rnd["answered"] = None
        rnd["qt0"] = time.time()
        st.rerun()


def _answer(C, rnd, q, choice, limit):
    secs = time.time() - rnd["qt0"]
    ok = choice is not None and choice == q["answer"]
    rnd["run"] = rnd["run"] + 1 if ok else 0
    in_time = secs <= limit
    pts = M.points(ok, q.get("level") or 1, 0, secs if in_time else 10 ** 6, rnd["run"]) if ok else (1 if choice is not None else 0)
    rnd["pts"] += pts
    rnd["res"].append((q, choice))
    rnd["answered"] = choice
    rnd["last"] = {"ok": ok, "pts": pts, "in_time": in_time, "choice": choice}
    C.prog.record(q, choice, ok, 0, secs, rnd["kind"], pts)


def _round_summary(C, rnd, label):
    res = rnd["res"]
    right = sum(c is not None and c == q["answer"] for q, c in res)
    mins = (time.time() - rnd["t0"]) / 60
    if not rnd.get("logged"):
        kind = "Speed round" if rnd["kind"] == "speed" else "Daily challenge"
        prev_best = max((int(float(r.get("points") or 0)) for r in C.store.rows("Tests", C.user["id"])
                         if r.get("kind") == kind), default=0)
        R.log_test(C.store, C.user, kind, res, mins, rnd["pts"])
        R.refresh_one(C, force=True)
        rnd["logged"] = True
        rnd["best"] = rnd["pts"] > prev_best and prev_best > 0
        if right >= 7 or rnd["best"]:
            st.balloons()
    st.subheader(f"🏁 {label} finished!")
    c1, c2, c3 = st.columns(3)
    c1.metric("Correct", f"{right} / {len(res)}")
    c2.metric("Points", f"⭐ {rnd['pts']}")
    c3.metric("Time", f"{mins:.1f} min")
    if rnd.get("best"):
        st.success("🏆 New personal best! Brilliant!")
    st.info(M.test_message(right / max(len(res), 1), float(C.store.get("class:target", 70)) / 100))
    wrong = [(q, c) for q, c in res if c != q["answer"]]
    if wrong:
        with st.expander(f"Review the {len(wrong)} you missed"):
            for q, c in wrong:
                st.markdown(f"**{unit_name(q['unit'])}** · {' '.join(q['text'].split())[:160]}…  \n"
                            f"Your answer: {'skipped' if c is None else option_label(q, c)} · Correct: {answer_text(q)}")
    if rnd["kind"] == "challenge" and leaderboard_on(C):
        show_leaderboard(C, day_start(), "challenge", "Today's challenge leaderboard")
    if st.button("Done", type="primary"):
        ss.pop("rnd")
        st.rerun()
