"""Student pages: Home, Learn, Practice, Tests, My progress, Patterns, My settings."""
from __future__ import annotations

import random
import time
from collections import Counter

import altair as alt
import pandas as pd
import streamlit as st

from . import generators as G
from . import motivate as M
from . import records as R
from . import ui_games as GM
from . import ui_tutor as TU
from .learn import GENERAL_RESOURCES, UNIT_GUIDES, primer
from .library import STATUS_TEXT
from .patterns import LEVEL_NAMES, PATTERNS, pattern_name, pattern_strategy
from .solvers import worked_solution
from .syllabus import UNITS, subtopic_name, unit_label, unit_name
from .ui_common import (BLUE, answer_text, bar_chart, go, option_label, show_question, source_badge, ss,
                        steps_md)


def daily_goal(C) -> int:
    return int(float(C.prog.get("daily_goal", C.store.get("class:daily_goal", 20))))


def target(C) -> float:
    return float(C.prog.get("target", C.store.get("class:target", 70))) / 100


# ================================================================== HOME
def page_home(C):
    att = C.prog.attempts()
    st.title(M.greeting(C.user["name"]))
    goal, done = daily_goal(C), M.today_count(att)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{M.goal_plant(done, goal)} Today", f"{done} / {goal}")
    c2.metric("📅 Day streak", f"{M.day_streak(att)} days")
    rep = C.prog.report(C.POOL) if att else {"empty": True}
    c3.metric("🎯 Projected Paper 1", "—" if rep.get("empty") else f"{rep['projected']:.0f} / 100")
    c4.metric("✅ Answered", len(att))
    st.progress(min(1.0, done / max(goal, 1)), text="Daily goal reached! 🎯🌳" if done >= goal else
                f"{goal - done} more to reach today's goal")
    pts = M.total_points(att)
    rk, floor, nxt, nxt_name = M.rank(pts)
    h1, h2 = st.columns([3, 2])
    with h1:
        GM.show_missions(C, goal)
        b1, b2 = st.columns(2)
        b1.button("🏆 Play today's class challenge", on_click=go, args=("✍️ Practice",),
                  kwargs=dict(pr_mode="🏆 Daily class challenge", pq=None))
        b2.button("⚡ Speed round", on_click=go, args=("✍️ Practice",), kwargs=dict(pr_mode="⚡ Speed round", pq=None))
    with h2:
        st.metric("⭐ Points", f"{pts:,}")
        st.markdown(f"**Rank: {rk}**")
        if nxt:
            st.progress(min(1.0, (pts - floor) / (nxt - floor)), text=f"{nxt - pts} to {nxt_name}")
        if GM.leaderboard_on(C) and C.user["role"] == "student":
            GM.show_leaderboard(C, GM.week_start(), None, "🏆 This week's class leaderboard", top=5)
    if not C.POOL:
        st.info("Your teacher hasn't loaded the question papers yet. Meanwhile, **📖 Learn** is ready, and "
                "**✍️ Practice → Unlimited practice** works right away.")
    if not att:
        st.subheader("Let's begin 🚀")
        st.markdown("1. **📝 Tests → Diagnostic**: about 20 questions to find your starting point (no pressure!).\n"
                    "2. **📈 My progress**: see your top focus areas.\n"
                    "3. **📖 Learn** the topic, then **✍️ Practice** it. A little every day beats a lot once a week.")
        st.button("Start the diagnostic test", type="primary", on_click=go, args=("📝 Tests",))
        return
    st.subheader("Your next focus")
    for i, d in enumerate(rep["deficits"][:3], 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {d['area']}**  \n{d['evidence']}  \n👉 {d['action']}")
            if d.get("subtopic") and any(q["subtopic"] == d["subtopic"] for q in C.POOL):
                st.button("Practise this", key=f"hf{i}", on_click=go, args=("✍️ Practice",),
                          kwargs=dict(pr_mode="📚 By topic (past papers)", pr_unit=d["unit"], pr_sub=d["subtopic"], pq=None))
    if not rep["deficits"]:
        st.success("No clear weak spots right now. 🌟 Keep mixing units in Adaptive practice.")
    due = C.prog.due_reviews({q["key"] for q in C.POOL} | {r["qkey"] for r in att if str(r["qkey"]).startswith("gen:")})
    if due:
        st.info(f"🔁 {len(due)} earlier mistakes are ready for a second try (Practice → Review my mistakes).")
    b = M.badges(att, C.prog.mastery("unit"), target(C))
    if b:
        st.subheader("Your badges")
        st.markdown("  ".join(f"`{t}`" for t, _ in b))


# ================================================================== LEARN
def page_learn(C):
    st.title("📖 Learn")
    units = list(UNITS)
    uid = st.selectbox("Unit", units, format_func=unit_label, index=units.index(ss.get("learn_unit") or "U1"))
    ss.learn_unit = uid
    g = UNIT_GUIDES[uid]
    st.markdown(f"**What this unit covers.** {g['overview']}")
    qs = [q for q in C.QUESTIONS if q.get("unit") == uid and q["status"] != "duplicate"]
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(f"**What past papers ask** ({len(qs)} questions; the syllabus sets 5 per paper)")
        if qs:
            st.markdown("Topics: " + ", ".join(f"{subtopic_name(s)} ({n})" for s, n in
                                               Counter(q["subtopic"] for q in qs).most_common()))
            st.markdown("Formats: " + ", ".join(f"{pattern_name(p)} ({n})" for p, n in
                                                Counter(q["pattern"] for q in qs).most_common()))
    with c2:
        st.markdown("**Typically tested**")
        for w in g["watch"]:
            st.markdown(f"- {w}")
    st.subheader("Topics")
    ms = C.prog.mastery("subtopic")
    gen_subs = G.subtopics_covered()
    for sid, (name, _) in UNITS[uid]["subtopics"].items():
        n = sum(q["subtopic"] == sid for q in qs)
        if sid.endswith(".99") and not n:
            continue
        m = ms.get(sid)
        tag = f" · your mastery {m[0] * 100:.0f}%" if m else ""
        pr = primer(sid)
        with st.expander(f"{name} · {n} in past papers{tag}" + (" · ♾️ unlimited practice" if sid in gen_subs else "")):
            if pr:
                st.markdown("**🌱 From zero.** " + pr["zero"])
                st.markdown("**🛠️ Method**\n" + steps_md(pr["method"]))
                st.markdown("**⚠️ Common traps**\n" + "\n".join(f"- {s}" for s in pr["traps"]))
                st.markdown("**🚀 Scale up.** " + pr["scale_up"])
            else:
                st.caption("Recall-based topic: learn it from the resources below, then practise the real questions.")
            for q in [q for q in qs if q["subtopic"] == sid and q["status"] == "ok"][:2]:
                with st.container(border=True):
                    st.caption("Real question · " + source_badge(q))
                    show_question(C, q, show_group=False)
                    if st.toggle("Show answer", key=f"lx_{q['key']}"):
                        st.success(answer_text(q))
                        ws = worked_solution(q)
                        if ws:
                            st.markdown(steps_md(ws))
            cols = st.columns(4)
            if any(q["subtopic"] == sid for q in C.POOL):
                cols[0].button("Practise past questions", key="lp_" + sid, on_click=go, args=("✍️ Practice",),
                               kwargs=dict(pr_mode="📚 By topic (past papers)", pr_unit=uid, pr_sub=sid, pq=None))
            if sid in gen_subs:
                cols[1].button("♾️ Unlimited practice", key="lg_" + sid, on_click=go, args=("✍️ Practice",),
                               kwargs=dict(pr_mode="♾️ Unlimited practice (worked solutions)", pr_gen=G.for_subtopic(sid)[0],
                                           pq=None))
            if TU.tutor_cfg(C) and not sid.endswith(".99"):
                cols[2].button("🤖 Ask the AI tutor", key="lt_" + sid, on_click=go, args=("🤖 AI tutor",),
                               kwargs=dict(tutor_unit=uid, tutor_sub=sid))
            if sid in ("U2.3", "U2.4", "U6.2", "U6.3"):
                cols[3].button("🧪 Try the simulator", key="ls_" + sid, on_click=go, args=("🧪 Simulators",))
    st.subheader("Where to read more")
    for name, url in g["resources"] + GENERAL_RESOURCES:
        st.markdown(f"- [{name}]({url})" if url else f"- {name}")


# ================================================================== PRACTICE
MODES = ["🎯 Adaptive (past papers)", "🏆 Daily class challenge", "⚡ Speed round", "📚 By topic (past papers)", "♾️ Unlimited practice (worked solutions)",
         "🧩 Drill a format", "🔁 Asked again in another session", "🤖 Teacher-approved AI questions",
         "🔄 Review my mistakes"]


def start_question(q):
    ss.update(pq=q["key"] if q else None, help=0, removed=[], answered=None, t0=time.time(), fb=None)


def page_practice(C):
    st.title("✍️ Practice")
    GM.points_bar(C)
    modes = [m for m in MODES if m != "🤖 Teacher-approved AI questions" or C.AIQ]
    c1, c2, c3 = st.columns([2, 2, 2])
    mode = c1.selectbox("How to practise", modes, index=modes.index(ss.get("pr_mode")) if ss.get("pr_mode") in modes else 0)
    ss.pr_mode = mode
    if mode in ("🏆 Daily class challenge", "⚡ Speed round"):
        GM.page_round(C, "challenge" if mode.startswith("🏆") else "speed")
        return
    if ss.get("rnd"):
        ss.pop("rnd")                     # left a round half-way: start fresh next time
    unit = sub = pattern = family = gen = None
    lvl_choice = None
    paper_pool = [q for q in C.POOL if q.get("origin") != "ai"]
    if mode == "📚 By topic (past papers)":
        units = [u for u in UNITS if any(q["unit"] == u for q in paper_pool)]
        if not units:
            st.info("No past-paper questions loaded yet. Try ♾️ Unlimited practice.")
            return
        unit = c2.selectbox("Unit", units, format_func=unit_label,
                            index=units.index(ss.get("pr_unit")) if ss.get("pr_unit") in units else 0)
        subs = ["All"] + [s for s in UNITS[unit]["subtopics"] if any(q["subtopic"] == s for q in paper_pool)]
        sub = c3.selectbox("Topic", subs, format_func=lambda s: s if s == "All" else subtopic_name(s),
                           index=subs.index(ss.get("pr_sub")) if ss.get("pr_sub") in subs else 0)
        sub = None if sub == "All" else sub
    elif mode == "♾️ Unlimited practice (worked solutions)":
        cat = G.catalogue()
        gids = [c[0] for c in cat]
        gen = c2.selectbox("Question type", gids, format_func=lambda g: f"{unit_name(G.GEN[g]['unit'])} · {G.GEN[g]['name']}",
                           index=gids.index(ss.get("pr_gen")) if ss.get("pr_gen") in gids else 0)
        levels = list(G.GEN[gen]["levels"])
        lvl_choice = c3.selectbox("Level", ["Auto (grows with you)"] + levels,
                                  format_func=lambda v: v if isinstance(v, str) else LEVEL_NAMES.get(v, f"Level {v}").split(" · ")[0])
    elif mode == "🧩 Drill a format":
        pats = [p["id"] for p in PATTERNS if any(q["pattern"] == p["id"] for q in C.POOL)]
        if not pats:
            st.info("No past-paper questions loaded yet.")
            return
        pattern = c2.selectbox("Format", pats, format_func=pattern_name,
                               index=pats.index(ss.get("pr_pattern")) if ss.get("pr_pattern") in pats else 0)
        c3.info(pattern_strategy(pattern), icon="🧭")
    elif mode == "🔁 Asked again in another session":
        fams = [f for f in C.lib.get("families", {}) if any(q.get("family") == f for q in paper_pool)]
        if not fams:
            st.info("No repeated questions with verified answers yet.")
            return
        family = c2.selectbox("Repeated topic", fams, format_func=lambda f: C.lib["families"][f]["label"])

    sig = (mode, unit, sub, pattern, family, gen, str(lvl_choice))
    if ss.get("pr_sig") != sig or not ss.get("pq"):
        ss.pr_sig, ss.pr_mode = sig, mode
        q = pick(C, mode, unit, sub, pattern, family, gen, lvl_choice)
        if not q:
            return
        start_question(q)
    q = C.get_q(ss.pq)
    if q is None:
        ss.pq = None
        st.rerun()
    render_question(C, q, mode, gen, lvl_choice)


def pick(C, mode, unit, sub, pattern, family, gen, lvl_choice):
    recent = set(ss.get("recent", [])[-25:])
    if mode == "♾️ Unlimited practice (worked solutions)":
        sid = G.GEN[gen]["subtopic"]
        lv = C.prog.level_for(sid) if not isinstance(lvl_choice, int) else lvl_choice
        lv = min(max(lv, min(G.GEN[gen]["levels"])), max(G.GEN[gen]["levels"]))
        q = G.make(gen, lv, random.randrange(10 ** 9))
        if q["key"].count(":") == 4:              # a data set: start at its first question
            q = G.make(gen, lv, int(q["key"].split(":")[3]), 0)
        return q
    if mode == "🔄 Review my mistakes":
        keys = {q["key"] for q in C.POOL} | {r["qkey"] for r in C.prog.attempts() if str(r["qkey"]).startswith("gen:")}
        due = C.prog.due_reviews(keys)
        if not due:
            st.success("Nothing to review right now. 🎉 Your earlier mistakes are all fixed or not due yet.")
            return None
        return C.get_q(random.choice(due))
    if mode == "🤖 Teacher-approved AI questions":
        cand = [q for q in C.AIQ if q["key"] not in recent] or C.AIQ
        return random.choice(cand) if cand else None
    pool = [q for q in C.POOL if q.get("origin") != "ai"] if mode != "🧩 Drill a format" else C.POOL
    q = C.prog.next_question(pool, unit, sub, pattern, family, exclude=recent)
    if not q:
        if not pool:
            st.info("No past-paper questions loaded yet. Try ♾️ Unlimited practice, which needs no papers.")
        else:
            st.warning("No questions match. Try another choice.")
    return q


def render_question(C, q, mode, gen, lvl_choice):
    recent = ss.setdefault("recent", [])
    if not recent or recent[-1] != q["key"]:
        recent.append(q["key"])
    st.divider()
    lvl = q.get("level") or 1
    st.caption(f"{unit_label(q['unit'])} → {subtopic_name(q['subtopic'])} · {pattern_name(q['pattern'])} · "
               f"{LEVEL_NAMES.get(lvl, '')} · {source_badge(q)}")
    show_question(C, q)

    choices = [i for i in range(4) if i not in ss.removed]
    answered = ss.answered is not None
    choice = st.radio("Your answer", choices, index=None, format_func=lambda i: option_label(q, i),
                      key=f"ch_{q['key']}_{len(ss.removed)}", disabled=answered,
                      horizontal=q.get("display") == "image")
    if not answered:
        st.caption("Stuck? Take help one step at a time 🪜 (each step lowers the credit a little).")
        b = st.columns(4)
        if b[0].button("🧭 Strategy", disabled=ss.help >= 1):
            ss.help = 1
        if b[1].button("📘 Concept", disabled=ss.help >= 2):
            ss.help = 2
        if b[2].button("✂️ Remove 2", disabled=ss.help >= 3):
            ss.help = 3
            ss.removed = random.sample([i for i in range(4) if i != q["answer"]], 2)
            st.rerun()
        if b[3].button("👁️ Show answer"):
            ss.help, ss.answered = 4, -1
            submit(C, q, None)
            st.rerun()
        if ss.help >= 1:
            st.info(q.get("hint") or pattern_strategy(q["pattern"]), icon="🧭")
            if q.get("hint"):
                st.caption("Format strategy: " + pattern_strategy(q["pattern"]))
        if ss.help >= 2:
            pr = primer(q["subtopic"])
            if pr:
                st.info(f"**{subtopic_name(q['subtopic'])}.** {pr['zero']}\n\n" + steps_md(pr["method"]), icon="📘")
            else:
                st.info("**Usually tested here:** " + "; ".join(UNIT_GUIDES[q["unit"]]["watch"]), icon="📘")
        if st.button("Submit", type="primary", disabled=choice is None):
            ss.answered = choice
            submit(C, q, choice)
            st.rerun()
        return

    # ---------------- feedback
    ok = ss.answered == q["answer"]
    fb = ss.get("fb") or {}
    if fb.get("celebrate"):
        st.balloons()
        fb["celebrate"] = False
    if ss.answered == -1:
        st.info(f"{fb.get('msg', '')}\n\nAnswer: **{answer_text(q)}**")
    elif ok:
        st.success(f"{fb.get('msg', '')}\n\n✅ {answer_text(q)}")
    else:
        st.error(f"{fb.get('msg', '')}\n\nYou chose option {ss.answered + 1}; the answer is **{answer_text(q)}**.")
    for extra in fb.get("extras", []):
        st.success(extra)
    st.caption("Answer source: " + q.get("answer_source", ""))
    steps = q.get("steps") or worked_solution(q)
    if steps:
        st.markdown("**🛠️ Worked solution**\n" + steps_md(steps))
    if q.get("explanation"):
        st.markdown("**💬 Explanation:** " + q["explanation"])
    TU.explain_button(C, q, ss.answered)
    with st.expander("🧭 How to approach this kind of question", expanded=not ok and not steps):
        st.markdown(pattern_strategy(q["pattern"]))
        pr = primer(q["subtopic"])
        if pr:
            st.markdown(f"**Method for {subtopic_name(q['subtopic'])}**\n" + steps_md(pr["method"]))
            st.markdown("**Watch out:** " + " ".join(pr["traps"]))
    c1, c2, c3 = st.columns(3)
    if c1.button("Next question ➜", type="primary"):
        ss.pq = None
        st.rerun()
    if c2.button("🔁 A similar one"):
        if q.get("origin") == "generated":
            gid = q["generator"]
            q2 = G.make(gid, q["level"], random.randrange(10 ** 9))
            if q2["key"].count(":") == 4:
                q2 = G.make(gid, q["level"], int(q2["key"].split(":")[3]), 0)
        else:
            q2 = (C.prog.next_question(C.POOL, family=q.get("family"), exclude={q["key"]}) if q.get("family_size", 1) > 1 else None) \
                 or C.prog.next_question(C.POOL, subtopic=q["subtopic"], exclude={q["key"]}) \
                 or (G.make(G.for_subtopic(q["subtopic"])[0], q.get("level") or 1, random.randrange(10 ** 9))
                     if G.for_subtopic(q["subtopic"]) else None) \
                 or C.prog.next_question(C.POOL, unit=q["unit"], exclude={q["key"]})
        start_question(q2)
        st.rerun()
    if q.get("origin") != "generated" and c3.button("⚠️ Report a problem"):
        C.report_problem(q)
        ss.pq = None
        st.rerun()
    if q.get("origin") == "generated" and q["key"].count(":") == 4:     # next question of the same data set
        gid, lv, seed, part = q["key"].split(":")[1:]
        nxt = int(part) + 1
        try:
            q2 = G.make(gid, int(lv), int(seed), nxt)
            if c3.button(f"➡️ Next question on this table ({nxt + 1})"):
                start_question(q2)
                st.rerun()
        except IndexError:
            pass
    m = C.prog.mastery("subtopic").get(q["subtopic"])
    if m:
        st.caption(f"Your mastery in {subtopic_name(q['subtopic'])}: {m[0] * 100:.0f}% over {m[1]} questions · "
                   f"you're at {LEVEL_NAMES[C.prog.level_for(q['subtopic'])]}")


def submit(C, q, choice):
    """Record the answer and prepare the encouraging feedback."""
    before = C.prog.level_for(q["subtopic"])
    goal, done_before = daily_goal(C), M.today_count(C.prog.attempts())
    ok = choice is not None and choice == q["answer"]
    secs = time.time() - ss.t0
    run = M.current_run(C.prog.attempts()) + 1 if ok else 0
    pts = M.points(ok, q.get("level") or 1, ss.help, secs, run)
    rank_before = M.rank(M.total_points(C.prog.attempts()))[0]
    C.prog.record(q, choice, ok, ss.help, secs, "practice", pts)
    att = C.prog.attempts()
    fb = {"msg": M.feedback(ok, ss.help, M.current_run(att)) + f"  **+{pts} ⭐**"
          + (f" ({M.combo_label(run)})" if ok and run >= 3 else ""), "extras": [], "celebrate": False}
    rank_after = M.rank(M.total_points(att))[0]
    if rank_after != rank_before:
        fb["extras"].append(f"🎖️ New rank: **{rank_after}**! Your hard work is showing.")
        fb["celebrate"] = True
    R.refresh_one(C)
    after = C.prog.level_for(q["subtopic"])
    if after > before:
        fb["extras"].append(M.level_up_message(subtopic_name(q["subtopic"]), after))
        fb["celebrate"] = True
    if done_before < goal <= done_before + 1:
        fb["extras"].append(f"🎯🌳 Daily goal reached: {goal} questions today! Brilliant consistency.")
        fb["celebrate"] = True
    ss.fb = fb


# ================================================================== TESTS
def page_tests(C):
    st.title("📝 Tests")
    if "test" not in ss:
        kind = st.radio("Type", ["Diagnostic: 2 questions per unit (about 20)",
                                 "Mock: 50 questions, 5 from every unit, like the real paper"])
        st.caption("No help and no feedback until you submit. The real exam gives 60 minutes for 50 questions "
                   "(about 72 seconds each). Relax and do your best 🙂")
        if st.button("Start", type="primary"):
            qs = C.prog.diagnostic_set(C.POOL) if kind.startswith("Diag") else C.prog.mock_set(C.POOL, 50)
            if not qs:
                st.warning("Not enough questions loaded yet. Ask your teacher, or use ♾️ Unlimited practice.")
                return
            ss.test = {"kind": kind.split(":")[0], "keys": [q["key"] for q in qs], "t0": time.time(), "done": False}
            R.log(C.store, C.user, "test_start", ss.test["kind"])
            st.rerun()
        return
    t = ss.test
    qs = [q for q in (C.get_q(k) for k in t["keys"]) if q]
    st.caption(f"{t['kind']} · {len(qs)} questions · suggested time {len(qs) * 1.2:.0f} min · "
               f"started {(time.time() - t['t0']) / 60:.0f} min ago")
    if not t["done"]:
        with st.form("test_form"):
            for i, q in enumerate(qs, 1):
                st.markdown(f"**Question {i}** · {unit_name(q['unit'])}")
                show_question(C, q)
                st.radio("Answer", list(range(4)), index=None, key="t_" + q["key"],
                         format_func=lambda j, q=q: option_label(q, j), horizontal=q.get("display") == "image")
                st.divider()
            if st.form_submit_button("Submit test", type="primary"):
                per = (time.time() - t["t0"]) / max(len(qs), 1)
                total = 0
                for q in qs:
                    c = ss.get("t_" + q["key"])
                    pts = 10 * (q.get("level") or 1) if c == q["answer"] else 0
                    total += pts
                    C.prog.record(q, c, c == q["answer"], 0, per, "test", pts)
                R.log_test(C.store, C.user, t["kind"], [(q, ss.get("t_" + q["key"])) for q in qs],
                           (time.time() - t["t0"]) / 60, total)
                R.refresh_one(C, force=True)
                C.store.flush()
                t["done"] = True
                st.rerun()
        if st.button("Abandon test"):
            ss.pop("test")
            st.rerun()
        return
    res = [{"Unit": unit_label(q["unit"]), "Correct": int(ss.get("t_" + q["key"]) == q["answer"]), "q": q,
            "c": ss.get("t_" + q["key"])} for q in qs]
    score = sum(r["Correct"] for r in res)
    pct = score / max(len(qs), 1)
    st.metric("Score", f"{score * 2} / {len(qs) * 2}", f"{pct * 100:.0f}%")
    msg = M.test_message(pct, target(C))
    (st.success if pct >= target(C) else st.info)(msg)
    if pct >= target(C) and not t.get("celebrated"):
        st.balloons()
        t["celebrated"] = True
    df = pd.DataFrame(res).groupby("Unit")["Correct"].agg(["sum", "count"]).reset_index()
    df["Accuracy"] = df["sum"] / df["count"]
    st.altair_chart(bar_chart(df[["Unit", "Accuracy"]], "Accuracy", "Unit", pct=True), width="stretch")
    st.subheader("Review")
    for i, r in enumerate(res, 1):
        q = r["q"]
        with st.expander(f"{'✅' if r['Correct'] else '❌'} Question {i} · {unit_name(q['unit'])}"):
            show_question(C, q)
            st.write(f"Your answer: {'—' if r['c'] is None else 'option ' + str(r['c'] + 1)} · Correct: {answer_text(q)}")
            ws = q.get("steps") or worked_solution(q)
            if ws:
                st.markdown(steps_md(ws))
            if q.get("explanation"):
                st.caption(q["explanation"])
    if st.button("Done"):
        ss.pop("test")
        st.rerun()


# ================================================================== MY PROGRESS
def page_progress(C, prog=None, title="📈 My progress"):
    prog = prog or C.prog
    st.title(title)
    att = prog.attempts()
    rep = prog.report(C.POOL)
    if rep.get("empty"):
        st.info("No answers yet. A Diagnostic test (📝 Tests) is the quickest start. 🙂")
        return
    tg = target(C)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎯 Projected score", f"{rep['projected']:.0f} / 100")
    c2.metric("🏁 Target", f"{tg * 100:.0f} / 100")
    c3.metric("✅ Accuracy", f"{rep['overall'] * 100:.0f}%")
    c4.metric("⏱️ Median time", f"{rep['median_seconds']:.0f}s" if rep["median_seconds"] else "—")
    gap = tg * 100 - rep["projected"]
    st.caption("😊 You're at or above target. Keep it steady!" if gap <= 0 else
               f"🚀 {gap:.0f} marks to your target. The focus list below shows the fastest way to close the gap.")
    b = M.badges(att, prog.mastery("unit"), tg)
    if b:
        st.markdown("**Badges:** " + "  ".join(f"`{t}`" for t, _ in b))
    st.subheader("Next focus, in order")
    if not rep["deficits"]:
        st.success("No clear gaps yet. 🌟 Keep practising across all units.")
    for i, d in enumerate(rep["deficits"][:8], 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {d['type']}: {d['area']}**  \n{d['evidence']}  \n👉 {d['action']}")
            if prog is C.prog:
                cols = st.columns(3)
                if d.get("subtopic") and any(q["subtopic"] == d["subtopic"] for q in C.POOL):
                    cols[0].button("Practise it", key=f"gp_{i}", on_click=go, args=("✍️ Practice",),
                                   kwargs=dict(pr_mode="📚 By topic (past papers)", pr_unit=d["unit"],
                                               pr_sub=d["subtopic"], pq=None))
                if d.get("pattern"):
                    cols[0].button("Drill it", key=f"gd_{i}", on_click=go, args=("✍️ Practice",),
                                   kwargs=dict(pr_mode="🧩 Drill a format", pr_pattern=d["pattern"], pq=None))
                if d.get("unit"):
                    cols[1].button("Learn it", key=f"gl_{i}", on_click=go, args=("📖 Learn",),
                                   kwargs=dict(learn_unit=d["unit"]))
    st.subheader("Mastery by unit (each unit = 10 marks)")
    rows = [{"Unit": unit_label(u), "Mastery": (rep["unit_mastery"].get(u) or (0.0, 0))[0],
             "Answered": (rep["unit_mastery"].get(u) or (0, 0))[1]} for u in UNITS]
    df = pd.DataFrame(rows)
    rule = alt.Chart(pd.DataFrame({"t": [tg]})).mark_rule(strokeDash=[4, 4], color="#64748b").encode(x="t:Q")
    st.altair_chart(bar_chart(df, "Mastery", "Unit", pct=True) + rule, width="stretch")
    st.caption("Dashed line = target. Units not tried yet show as 0.")
    st.subheader("By question format")
    st.dataframe(pd.DataFrame([{"Format": pattern_name(p), "Mastery": f"{m * 100:.0f}%", "Answered": n}
                               for p, (m, n) in sorted(rep["pattern_mastery"].items(), key=lambda x: x[1][0])]),
                 hide_index=True, width="stretch")
    a = pd.DataFrame(att)
    a["date"] = pd.to_datetime(a["ts"], unit="s", utc=True).dt.tz_convert("Asia/Kolkata").dt.date
    daily = a.groupby("date").agg(answers=("correct", "size"), accuracy=("correct", "mean")).reset_index()
    if len(daily) > 1:
        daily["date"] = pd.to_datetime(daily["date"])
        st.subheader("Day by day")
        st.altair_chart(alt.Chart(daily).mark_line(color=BLUE, strokeWidth=2, point=True).encode(
            x=alt.X("date:T", title=None), y=alt.Y("accuracy:Q", title="Accuracy", axis=alt.Axis(format="%"),
                                                    scale=alt.Scale(domain=[0, 1])),
            tooltip=["date:T", alt.Tooltip("accuracy:Q", format=".0%"), "answers"]), width="stretch")


# ================================================================== PATTERNS
def page_patterns(C):
    st.title("🔍 Patterns in past papers")
    all_q = [q for q in C.QUESTIONS if q["status"] != "duplicate" and q.get("unit")]
    if not all_q:
        st.info("No papers loaded yet.")
        return
    df = pd.DataFrame([{"Unit": unit_label(q["unit"]), "Topic": subtopic_name(q["subtopic"]),
                        "Format": pattern_name(q["pattern"]), "Session": q["session"], "key": q["key"]} for q in all_q])
    st.caption(f"{len(df)} questions from {df['Session'].nunique()} sessions. The syllabus sets 5 questions per unit.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Most-asked topics**")
        t = df.groupby(["Unit", "Topic"]).agg(Questions=("key", "size"), Sessions=("Session", "nunique")).reset_index()
        st.dataframe(t.sort_values(["Questions", "Sessions"], ascending=False), hide_index=True, width="stretch", height=380)
    with c2:
        st.markdown("**Question formats**")
        f = df.groupby("Format").size().reset_index(name="Questions")
        st.altair_chart(bar_chart(f, "Questions", "Format", height=380), width="stretch")
    st.markdown("**Which formats each unit uses** (darker = more)")
    uf = df.groupby(["Unit", "Format"]).size().reset_index(name="Questions")
    st.altair_chart(alt.Chart(uf).mark_rect(stroke="white", strokeWidth=2, cornerRadius=3).encode(
        x=alt.X("Format:N", title=None, axis=alt.Axis(labelAngle=-35, labelLimit=200, labelOverlap=False)),
        y=alt.Y("Unit:N", title=None, axis=alt.Axis(labelLimit=260)),
        color=alt.Color("Questions:Q", scale=alt.Scale(range=["#dbeafe", "#1e3a8a"])),
        tooltip=["Unit", "Format", "Questions"]).properties(height=380), width="stretch")
    st.markdown("**Asked again in another session**")
    fams = C.lib.get("families", {})
    if not fams:
        st.caption("No repeats found yet.")
    for fid, info in sorted(fams.items(), key=lambda x: -len(x[1]["sessions"])):
        members = [q for q in C.QUESTIONS if q.get("family") == fid]
        with st.expander(f"{info['label']} · {len(members)} questions in {len(info['sessions'])} sessions"):
            for q in members:
                st.markdown(f"- *{q['session']} Q{q['qno']}*: {q['text'][:160]}")
    st.markdown("**Question bank by unit → topic → format**")
    c1, c2 = st.columns(2)
    bu = c1.selectbox("Unit", list(UNITS), format_func=unit_label, key="bank_u")
    subs = [s for s in UNITS[bu]["subtopics"] if any(q["subtopic"] == s for q in all_q)]
    if not subs:
        st.caption("No questions from this unit yet.")
        return
    bs = c2.selectbox("Topic", subs, format_func=subtopic_name, key="bank_s")
    group = [q for q in all_q if q["subtopic"] == bs]
    for pid in sorted({q["pattern"] for q in group}, key=lambda p: -sum(q["pattern"] == p for q in group)):
        members = [q for q in group if q["pattern"] == pid]
        st.markdown(f"*{pattern_name(pid)}* ({len(members)}). {pattern_strategy(pid)}")
        for q in members:
            with st.expander(f"{q['session']} · Q{q['qno']}: {q['text'][:90]}"):
                show_question(C, q)
                if q["status"] == "ok":
                    if st.toggle("Show answer", key="bk_" + q["key"]):
                        st.success(f"{answer_text(q)} · {q['answer_source']}")
                else:
                    st.caption("No verified answer: " + STATUS_TEXT[q["status"]])


# ================================================================== MY SETTINGS
def page_my_settings(C):
    st.title("⚙️ My settings")
    t = st.slider("My Paper 1 target (out of 100)", 40, 100, int(target(C) * 100))
    g = st.slider("Daily goal (questions per day)", 5, 100, daily_goal(C), step=5)
    if st.button("Save", type="primary"):
        C.prog.set("target", t)
        C.prog.set("daily_goal", g)
        st.success("Saved. 🙂")
    st.caption("Tip: 20–30 questions a day, every day, beats 150 once a week.")
