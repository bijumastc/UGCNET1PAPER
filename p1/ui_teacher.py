"""Teacher pages: Class dashboard, Students, AI questions, Papers & checks, Class settings."""
from __future__ import annotations

import random
import time
from collections import Counter, defaultdict

import altair as alt
import pandas as pd
import streamlit as st

from . import ai_writer as AI
from . import llm
from . import motivate as M
from . import records as R
from . import ui_games as GM
from . import ui_tutor as TU
from .library import STATUS_TEXT
from .patterns import pattern_name
from .progress import Progress
from datetime import datetime

from .store import IST, now_iso
from .syllabus import UNITS, subtopic_name, unit_label, unit_name
from .ui_common import answer_text, show_question, source_badge, ss
from .ui_student import page_progress


# ================================================================== helpers
def class_rows(C):
    """One summary row per student, from every attempt in the store."""
    att_all = C.store.attempts()
    by = defaultdict(list)
    for r in att_all:
        by[str(r["student_id"])].append(r)
    rows, progs = [], {}
    week = time.time() - 7 * 86400
    target = float(C.store.get("class:target", 70)) / 100
    for s in C.store.students():
        if str(s.get("active", "1")) in ("0", "False", "false", "FALSE"):
            continue
        sid = str(s["student_id"])
        p = Progress(C.store, sid, s["name"])
        p._att = by.get(sid, [])
        progs[sid] = p
        a = p._att
        rep = p.report(C.POOL) if a else {"empty": True}
        mu = p.mastery("unit")
        weakest = min(((u, m) for u, (m, n) in mu.items() if n >= 3), key=lambda x: x[1], default=(None, 0))[0]
        last = max((r["ts"] for r in a), default=0)
        days_idle = (time.time() - last) / 86400 if last else None
        proj = rep.get("projected") if not rep.get("empty") else None
        status = "⚪ not started" if not a else "🔴 inactive 3+ days" if days_idle > 3 else \
            "🟢 on track" if proj and proj >= target * 100 else "🟡 working"
        rows.append({"student_id": sid, "name": s["name"], "status": status,
                     "last_active": datetime.fromtimestamp(last, IST).strftime("%d %b %H:%M") if last else "—",
                     "questions_total": len(a), "questions_7_days": sum(r["ts"] >= week for r in a),
                     "accuracy": round(sum(r["correct"] for r in a) / len(a) * 100) if a else None,
                     "projected_score": round(proj) if proj is not None else None, "day_streak": M.day_streak(a),
                     "weakest_unit": unit_name(weakest) if weakest else "—",
                     "help_share": round(sum(r["help"] >= 2 for r in a) / len(a) * 100) if a else None})
    return rows, progs


# ================================================================== DASHBOARD
def page_dashboard(C):
    st.title("🏫 Class dashboard")
    rows, progs = class_rows(C)
    if not rows:
        st.info("No students yet. Add them in **👥 Students**.")
        return
    df = pd.DataFrame(rows)
    active = sum(r["questions_7_days"] > 0 for r in rows)
    proj = [r["projected_score"] for r in rows if r["projected_score"] is not None]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Students", len(rows))
    c2.metric("Active this week", active)
    c3.metric("Average projected score", f"{sum(proj) / len(proj):.0f}" if proj else "—")
    c4.metric("Answers this week", sum(r["questions_7_days"] for r in rows))

    prow, urows = R.class_summaries(C, progs)
    if time.time() - ss.get("_summary_written", 0) > 600:        # keep the sheet's summary tabs fresh
        try:
            C.store.write_summary("Progress", prow)
            C.store.write_summary("Unit_Scores", urows)
            ss._summary_written = time.time()
        except Exception as ex:
            st.caption(f"Couldn't update the Progress tab just now ({ex}).")

    tabs = st.tabs(["👥 Students", "🗺️ Unit map", "🎯 Teach next", "🔎 One student", "📮 Reports", "🤖 AI tutor use",
                    "🧾 Answers", "📝 Tests & rounds", "🕒 Time & logins", "🏆 Leaderboard"])
    with tabs[5]:
        TU.tutor_usage_table(C)
    with tabs[0]:
        status_icon = {"on track": "🟢 on track", "working": "🟡 working", "inactive 3+ days": "🔴 inactive 3+ days",
                       "not started": "⚪ not started"}
        show = pd.DataFrame(prow).drop(columns=["student_id", "updated", "batch"]).assign(
            status=lambda d: d["status"].map(lambda s: status_icon.get(s, s))).rename(columns={
            "name": "Student", "status": "Status", "last_active": "Last active", "logins": "Logins",
            "days_active": "Days active", "minutes_total": "Minutes", "minutes_7_days": "Min. this week",
            "practice_sessions": "Sessions", "questions_total": "Answers", "questions_7_days": "This week",
            "correct_total": "Correct", "accuracy": "Accuracy %", "tests_taken": "Tests", "last_test_pct": "Last test %",
            "best_test_pct": "Best test %", "projected_score": "Projected /100", "day_streak": "Day streak",
            "points": "Points", "rank": "Rank", "weakest_unit": "Weakest unit", "top_deficits": "Top deficits",
            "help_share": "Needs help %", "ai_tutor_questions": "AI questions"})
        st.dataframe(show, hide_index=True, width="stretch")
        c1, c2 = st.columns(2)
        if c1.button("📤 Update Progress & Unit_Scores in the Google Sheet now" if C.store.kind == "sheet"
                     else "📤 Save progress tables"):
            C.store.write_summary("Progress", prow)
            C.store.write_summary("Unit_Scores", urows)
            ss._summary_written = time.time()
            st.success("Updated.")
        if C.store.kind == "sheet":
            c2.markdown(f"[Open the Google Sheet]({C.store.link()})")
        st.caption("The sheet's Progress tab updates by itself when you open this dashboard (at most every 10 "
                   "minutes) and after every 10 answers, each test and each logout of a student.")
        st.download_button("Download this table (CSV)", show.to_csv(index=False).encode("utf-8-sig"), "class_progress.csv")
    names = {str(r["student_id"]): r["name"] for r in rows}
    with tabs[6]:
        att = pd.DataFrame(C.store.attempts())
        if att.empty:
            st.caption("No answers yet.")
        else:
            who = st.selectbox("Student", ["Everyone"] + list(names), format_func=lambda s: names.get(s, s), key="ans_who")
            if who != "Everyone":
                att = att[att["student_id"].astype(str) == who]
            att = att.sort_values("ts", ascending=False).head(300)
            cols = [c for c in ["time", "name", "mode", "unit", "topic", "question", "your_answer", "correct_answer",
                                "correct", "help_used", "seconds", "points"] if c in att]
            st.dataframe(att[cols].assign(correct=att["correct"].map({1: "✅", 0: "❌"}),
                                         topic=att["topic"].map(lambda s: subtopic_name(s) if s else "")),
                         hide_index=True, width="stretch")
            st.caption("Latest 300 answers. Every answer is also in the sheet's Attempts tab.")
    with tabs[7]:
        tr = pd.DataFrame(C.store.rows("Tests"))
        if tr.empty:
            st.caption("No tests or rounds yet.")
        else:
            st.dataframe(tr.sort_values("time", ascending=False), hide_index=True, width="stretch")
    with tabs[8]:
        st.dataframe(pd.DataFrame(prow)[["name", "logins", "days_active", "minutes_total", "minutes_7_days",
                                         "practice_sessions", "last_active"]].rename(columns={
            "name": "Student", "logins": "Logins", "days_active": "Days active", "minutes_total": "Total minutes",
            "minutes_7_days": "Minutes this week", "practice_sessions": "Study sessions", "last_active": "Last active"}),
            hide_index=True, width="stretch")
        st.caption("Time is worked out from answers, page visits and AI questions; a gap of 15+ minutes starts a "
                   "new session. Every login and page visit is in the sheet's Activity tab.")
        act = pd.DataFrame(C.store.rows("Activity"))
        if not act.empty:
            st.dataframe(act.sort_values("time", ascending=False).head(200), hide_index=True, width="stretch")
    with tabs[9]:
        GM.show_leaderboard(C, GM.week_start(), None, "This week (points)", top=50)
        GM.show_leaderboard(C, GM.day_start(), "challenge", "Today's daily challenge", top=50)
    with tabs[1]:
        data = []
        for sid, p in progs.items():
            mu = p.mastery("unit")
            for u in UNITS:
                m = mu.get(u)
                data.append({"Student": p.name, "Unit": unit_label(u), "Mastery": m[0] if m else None,
                             "Answers": m[1] if m else 0})
        dm = pd.DataFrame(data)
        st.caption("Each cell is a student's mastery in a unit (darker = stronger, blank = not tried).")
        st.altair_chart(alt.Chart(dm.dropna()).mark_rect(stroke="white", strokeWidth=2, cornerRadius=3).encode(
            x=alt.X("Unit:N", title=None, axis=alt.Axis(labelAngle=-35, labelLimit=200)),
            y=alt.Y("Student:N", title=None),
            color=alt.Color("Mastery:Q", scale=alt.Scale(domain=[0, 1], range=["#fee2e2", "#fde68a", "#1e3a8a"]),
                            legend=alt.Legend(format="%")),
            tooltip=["Student", "Unit", alt.Tooltip("Mastery:Q", format=".0%"), "Answers"]
        ).properties(height=max(200, 28 * len(progs))), width="stretch")
    with tabs[2]:
        agg = defaultdict(lambda: [0, 0])
        for p in progs.values():
            for r in p._att:
                if r.get("subtopic"):
                    agg[r["subtopic"]][0] += r["correct"]
                    agg[r["subtopic"]][1] += 1
        t = [{"Unit": unit_name(s.split(".")[0]), "Topic": subtopic_name(s), "Class accuracy": a / n, "Answers": n,
              "Students": sum(any(r.get("subtopic") == s for r in p._att) for p in progs.values())}
             for s, (a, n) in agg.items() if n >= 5]
        if not t:
            st.caption("Needs at least 5 answers per topic.")
        else:
            tdf = pd.DataFrame(t).sort_values("Class accuracy")
            st.caption("Topics where the class does worst: good candidates for your next lesson.")
            st.dataframe(tdf.assign(**{"Class accuracy": (tdf["Class accuracy"] * 100).round().astype(int).astype(str) + "%"}),
                         hide_index=True, width="stretch")
    with tabs[3]:
        names = {r["student_id"]: r["name"] for r in rows}
        sid = st.selectbox("Student", list(names), format_func=lambda s: f"{names[s]} ({s})")
        if sid:
            page_progress(C, prog=progs[sid], title=f"📈 {names[sid]}")
    with tabs[4]:
        reps = [r for r in C.store.reports() if r.get("status") in ("", "open", None)]
        if not reps:
            st.success("No open problem reports. 🙂")
        for r in reps:
            q = C.get_q(r["question_key"])
            with st.container(border=True):
                st.caption(f"{r['time']} · reported by {r['student_id']}" + (f" · {source_badge(q)}" if q else ""))
                if q:
                    show_question(C, q, show_group=False)
                    st.write(f"Answer in the app: **{answer_text(q)}** · {q.get('answer_source', '')}")
                c1, c2 = st.columns(2)
                if c1.button("Leave this question out", key="rx_" + r["time"] + r["student_id"]):
                    C.store.save_correction(r["question_key"], exclude=True, by="teacher")
                    C.store.set_report_status(r["time"], r["student_id"], r["question_key"], "excluded")
                    st.rerun()
                if c2.button("It's fine: dismiss", key="rd_" + r["time"] + r["student_id"]):
                    C.store.set_report_status(r["time"], r["student_id"], r["question_key"], "dismissed")
                    st.rerun()


# ================================================================== STUDENTS
def _next_id(existing):
    nums = [int(s[1:]) for s in existing if s[:1] == "S" and s[1:].isdigit()]
    return f"S{(max(nums) + 1 if nums else 1):03d}"


def page_students(C):
    st.title("👥 Students")
    roster = C.store.students()
    if roster:
        df = pd.DataFrame(roster)[["student_id", "name", "pin", "email", "batch", "active"]].astype(str)
        df["active"] = df["active"].map(lambda v: "no" if v in ("0", "False", "false", "FALSE") else "yes")
        st.dataframe(df.rename(columns={"student_id": "Student ID", "name": "Name", "pin": "PIN", "email": "Email",
                                        "batch": "Batch", "active": "Active"}), hide_index=True, width="stretch")
        st.caption("Students log in with their **Student ID and PIN** (or automatically with the Google email you "
                   "invited, on the online app). Keep this list private.")
    with st.expander("➕ Add students", expanded=not roster):
        st.markdown("One student per line: `Name, email` (email optional). IDs and PINs are created for you.")
        text = st.text_area("Students", placeholder="Anu Raj, anu@gmail.com\nBiju Thomas")
        batch = st.text_input("Batch (optional)", placeholder="NET Dec 2026")
        if st.button("Add", type="primary") and text.strip():
            ids = [s["student_id"] for s in roster]
            added = []
            for line in text.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if not parts[0]:
                    continue
                sid = _next_id(ids)
                ids.append(sid)
                row = {"student_id": sid, "name": parts[0], "pin": f"{random.randint(1000, 9999)}",
                       "email": parts[1].lower() if len(parts) > 1 else "", "batch": batch, "active": 1, "joined": now_iso()}
                C.store.save_student(row)
                added.append(row)
            st.success("Added: " + ", ".join(f"{r['name']} (ID {r['student_id']}, PIN {r['pin']})" for r in added))
            st.rerun()
    if roster:
        with st.expander("✏️ Edit a student"):
            names = {s["student_id"]: s for s in roster}
            sid = st.selectbox("Student", list(names), format_func=lambda s: f"{names[s]['name']} ({s})")
            s = dict(names[sid])
            s["name"] = st.text_input("Name", s["name"])
            s["email"] = st.text_input("Email", s.get("email", "")).lower()
            s["batch"] = st.text_input("Batch", s.get("batch", ""))
            s["active"] = 1 if st.checkbox("Active", value=str(s.get("active", "1")) not in ("0", "False", "false")) else 0
            c1, c2 = st.columns(2)
            if c1.button("Save changes"):
                C.store.save_student(s)
                st.success("Saved.")
                st.rerun()
            if c2.button("🔑 New PIN"):
                s["pin"] = f"{random.randint(1000, 9999)}"
                C.store.save_student(s)
                st.success(f"New PIN for {s['name']}: {s['pin']}")
    st.markdown("**What to send a student**")
    st.code("Paper 1 Trainer: <link to the app>\nStudent ID: S001\nPIN: 1234\n"
            "Practise a little every day. Your progress is saved automatically.", language=None)


# ================================================================== AI QUESTIONS
def page_ai(C):
    st.title("🤖 AI questions")
    key = C.gemini_key
    rows = C.store.ai_questions()
    pending = [r for r in rows if r["status"] == "pending"]
    approved = [r for r in rows if r["status"] == "approved"]
    t1, t2, t3 = st.tabs([f"✍️ Write new", f"🧐 Review ({len(pending)})", f"✅ Approved ({len(approved)})"])
    with t1:
        lcfg = llm.config(C.secrets, C.store, C.gemini_model)
        if lcfg:     # the question writer uses only the free services; Gemini has its own option
            lcfg["chain"] = [s for s in lcfg["chain"] if s["provider"] != "gemini"]
        free = "Free AI (" + " → ".join(dict.fromkeys(s["label"] for s in lcfg["chain"])) + ")" if lcfg and lcfg["chain"] else None
        engines = (["Gemini"] if key else []) + ([free] if free else [])
        if not engines:
            st.warning("Set up Gemini or a free AI key first (⚙️ Class settings locally, or Secrets online).")
            return
        engine = st.radio("Writer", engines, horizontal=True)
        st.caption("The AI writes new questions in the style of real past questions on the topic you choose. "
                   "Nothing reaches students until you approve it.")
        c1, c2 = st.columns(2)
        unit = c1.selectbox("Unit", list(UNITS), format_func=unit_label, key="ai_u")
        subs = [s for s in UNITS[unit]["subtopics"] if not s.endswith(".99")]
        sub = c2.selectbox("Topic", subs, format_func=subtopic_name, key="ai_s")
        c3, c4, c5 = st.columns(3)
        pats = AI.formats_for(unit)
        real = [q for q in C.QUESTIONS if q.get("subtopic") == sub and q["status"] == "ok"]
        common = Counter(q["pattern"] for q in real).most_common(1)
        default_p = common[0][0] if common and common[0][0] in pats else pats[0]
        pat = c3.selectbox("Format", pats, index=pats.index(default_p), format_func=pattern_name, key="ai_p")
        level = c4.selectbox("Difficulty", [1, 2, 3], index=1, format_func=lambda v: ["Easy", "Medium", "Hard"][v - 1])
        n = c5.slider("How many", 3, 10, 5)
        examples = [q for q in real if q["pattern"] == pat][:4] + [q for q in real if q["pattern"] != pat][:2]
        st.caption(f"Will use {len(examples)} real questions as style examples.")
        if st.button("Write questions", type="primary"):
            reals = [q for q in C.QUESTIONS if q.get("unit") == unit]
            with st.spinner("The AI is writing…"):
                try:
                    if engine == "Gemini":
                        new, problems = AI.generate(key, C.gemini_model, unit, sub, pat, n, level, examples, reals)
                    else:
                        new, problems = AI.generate_llama(lcfg, unit, sub, pat, n, level, examples, reals)
                except Exception as e:
                    st.error(f"The AI request failed: {type(e).__name__}: {e}")
                    new, problems = [], []
            for r in new:
                C.store.save_ai_question(r)
            if new:
                st.success(f"{len(new)} questions added to the review queue.")
            for p in problems:
                st.caption(p)
    with t2:
        if not pending:
            st.info("Nothing waiting for review.")
        for r in pending[:10]:
            with st.container(border=True):
                st.caption(f"{unit_name(r['unit'])} → {subtopic_name(r['subtopic'])} · {pattern_name(r['pattern'])} · "
                           f"level {r['level']} · {r['model']}")
                r2 = dict(r)
                r2["question"] = st.text_area("Question", r["question"], key="aq_" + r["id"], height=120)
                cols = st.columns(2)
                for i in range(4):
                    r2[f"option{i + 1}"] = cols[i % 2].text_input(f"Option {i + 1}", r[f"option{i + 1}"], key=f"ao{i}_{r['id']}")
                r2["answer"] = st.radio("Correct option", [1, 2, 3, 4], index=int(r["answer"]) - 1, horizontal=True,
                                        key="aa_" + r["id"])
                r2["explanation"] = st.text_area("Explanation", r["explanation"], key="ae_" + r["id"])
                c1, c2 = st.columns(2)
                if c1.button("✅ Approve", key="ok_" + r["id"], type="primary"):
                    r2["status"] = "approved"
                    C.store.save_ai_question(r2)
                    st.rerun()
                if c2.button("🗑️ Reject", key="no_" + r["id"]):
                    r2["status"] = "rejected"
                    C.store.save_ai_question(r2)
                    st.rerun()
        if len(pending) > 10:
            st.caption(f"{len(pending) - 10} more after these.")
    with t3:
        for r in approved:
            with st.expander(f"{unit_name(r['unit'])} · {r['question'][:90]}"):
                q = AI.as_question(r)
                st.markdown(q["text"])
                st.write(f"Answer: {answer_text(q)}")
                st.caption(r["explanation"])
                if st.button("Withdraw from practice", key="wd_" + r["id"]):
                    r["status"] = "rejected"
                    C.store.save_ai_question(r)
                    st.rerun()


# ================================================================== PAPERS & CHECKS
def page_library(C):
    st.title("📂 Papers & checks")
    t1, t2, t3, t4 = st.tabs(["Files", "Skipped questions", "Needs review", "Spot-check answers"])
    with t1:
        rows = []
        for f in C.lib.get("files", []):
            qs = [q for q in C.QUESTIONS if q.get("source_file") == f["file"]]
            rows.append({"File": f["file"], "Type": {"paper": "Question paper", "key": "Answer key"}.get(f["role"], f["role"]),
                         "Session": f.get("session") or "", "Memory-based": "yes" if f.get("memory_based") else "",
                         "Questions": len(qs) if f["role"] == "paper" else None,
                         "Verified": sum(q["status"] == "ok" for q in qs) if f["role"] == "paper" else None,
                         "Problem": f.get("error") or ""})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        if C.lib.get("pairing"):
            st.markdown("**How keys were matched**")
            st.dataframe(pd.DataFrame(C.lib["pairing"]), hide_index=True, width="stretch")
    with t2:
        bad = [q for q in C.QUESTIONS if q["status"] != "ok"]
        st.caption("Left out of practice so students never learn from a doubtful answer.")
        st.dataframe(pd.DataFrame([{"Session": q["session"], "Q": q["qno"], "Reason": STATUS_TEXT[q["status"]],
                                    "Question": q["text"][:90]} for q in bad]), hide_index=True, width="stretch")
    with t3:
        review = [q for q in C.QUESTIONS if q.get("needs_review") and q["status"] == "ok"]
        if not review:
            st.success("Every verified question has a unit.")
        for q in review[:20]:
            with st.container(border=True):
                st.caption(source_badge(q))
                show_question(C, q, show_group=False)
                opts = list(UNITS)
                u = st.selectbox("Unit", opts, index=opts.index(q.get("unit_guess")) if q.get("unit_guess") in opts else 0,
                                 format_func=unit_label, key="rv_u_" + q["key"])
                s = st.selectbox("Topic", list(UNITS[u]["subtopics"]), format_func=subtopic_name, key="rv_s_" + q["key"])
                c1, c2 = st.columns(2)
                if c1.button("Save", key="rv_b_" + q["key"]):
                    C.store.save_correction(q["key"], unit=u, subtopic=s, by="teacher")
                    st.rerun()
                if c2.button("Leave it out", key="rv_x_" + q["key"]):
                    C.store.save_correction(q["key"], exclude=True, by="teacher")
                    st.rerun()
    with t4:
        pool = [q for q in C.POOL if q.get("origin") in ("official", "memory", "paper")]
        if not pool:
            st.info("No verified questions yet.")
            return
        if st.button("Show a random question") or ss.get("spot") not in {q["key"] for q in pool}:
            ss.spot = random.choice(pool)["key"]
        q = C.get_q(ss.spot)
        st.caption(source_badge(q) + f" · {unit_label(q['unit'])} → {subtopic_name(q['subtopic'])} "
                   f"(sorted by {q.get('unit_method', 'keywords')})")
        show_question(C, q)
        st.success(f"Answer used: **{answer_text(q)}** · from {q['answer_source']}")
        if st.button("❌ Something's wrong: leave this question out"):
            C.store.save_correction(q["key"], exclude=True, by="teacher")
            st.success("Left out.")


# ================================================================== CLASS SETTINGS
def page_class_settings(C):
    st.title("⚙️ Class settings")
    s = C.store
    c1, c2 = st.columns(2)
    tg = c1.slider("Class target for Paper 1 (out of 100)", 40, 100, int(float(s.get("class:target", 70))))
    goal = c2.slider("Default daily goal (questions)", 5, 100, int(float(s.get("class:daily_goal", 20))), step=5)
    mem = st.checkbox("Include memory-based papers (answers from coaching, not NTA)",
                      value=s.get("class:allow_memory", "1") == "1")
    ai = st.checkbox("Include teacher-approved AI questions in practice and tests", value=s.get("class:allow_ai", "1") == "1")
    lb = st.checkbox("Show the class leaderboard to students (first name + initial only)",
                     value=s.get("class:leaderboard_on", "1") == "1")
    model = st.text_input("Gemini model", s.get("class:gemini_model", AI.DEFAULT_MODEL),
                          help="Any model name listed in your Google AI Studio account, e.g. a 'flash' model.")
    if C.mode == "local":
        key = st.text_input("Gemini API key (kept in this computer's class.db)", s.get("class:gemini_api_key", ""),
                            type="password")
        pw = st.text_input("Teacher password (turns on student logins on this computer)", s.get("class:teacher_password", ""),
                           type="password")
    else:
        key = pw = None
        st.caption("Online, the Gemini key and teacher password live in the app's **Secrets** (see DEPLOY.md).")
    if st.button("Save", type="primary"):
        s.set("class:target", tg)
        s.set("class:daily_goal", goal)
        s.set("class:allow_memory", "1" if mem else "0")
        s.set("class:allow_ai", "1" if ai else "0")
        s.set("class:leaderboard_on", "1" if lb else "0")
        s.set("class:gemini_model", model)
        if key is not None:
            s.set("class:gemini_api_key", key)
        if pw is not None:
            s.set("class:teacher_password", pw)
        st.success("Saved.")
    st.subheader("🤖 AI tutor (free AI services, automatic backup)")
    st.caption("Add as many keys as you like. Each question tries them in order; if one is busy the next answers. "
               "Gemini (your paid key) is used only when all the free ones are busy.")
    on = st.toggle("AI tutor on for students", value=s.get("class:ai_tutor_on", "1") == "1")
    limit = st.slider("Questions per student per day", 5, 100, int(float(s.get("class:ai_daily_limit", 30))), step=5,
                      help="Keeps a class within the free services' daily limits.")
    vals = {}
    for pid, p in llm.PROVIDERS.items():
        has = bool(llm.provider_key(pid, C.secrets, s))
        with st.expander(f"{'✅' if has else '➖'} {p['label']}", expanded=False):
            c1, c2 = st.columns([1, 2])
            vals[f"class:llm_on_{pid}"] = "1" if c1.toggle("Use", value=llm.provider_on(pid, s), key=f"on_{pid}") else "0"
            if pid == "gemini":
                c2.caption("Uses the Gemini key and model set above. Costs a little per question (paid).")
                continue
            c2.caption(f"Get a free key: {p['key_url']}")
            if p.get("note"):
                st.caption("ℹ️ " + p["note"])
            if C.mode == "local":
                vals[f"class:{p['secret']}"] = st.text_input("API key", s.get(f"class:{p['secret']}", ""),
                                                            type="password", key=f"k_{pid}")
            else:
                st.caption(f"Online: put `{p['secret']}` in Secrets. " + ("Found ✅" if has else "Not found."))
            default = ", ".join(p["models"] + p.get("late_models", []))
            vals[f"class:llm_models_{pid}"] = st.text_input(
                "Models, in order (comma-separated)", s.get(f"class:llm_models_{pid}", "") or default, key=f"m_{pid}",
                help="Change only if the service renames its models. Leave as is otherwise.")
            if vals[f"class:llm_models_{pid}"].strip() == default:
                vals[f"class:llm_models_{pid}"] = ""
    rest = llm.resting()
    st.caption("Skipped right now (busy or not answering): " + ", ".join(rest) if rest else
               "All added services are available right now. ✅")
    b1, b2 = st.columns(2)
    if b1.button("Save AI tutor settings"):
        s.set("class:ai_tutor_on", "1" if on else "0")
        s.set("class:ai_daily_limit", limit)
        for k, v in vals.items():
            s.set(k, v)
        st.success("Saved.")
    if b2.button("🔌 Test every service"):
        cfg = llm.config(C.secrets, s, C.gemini_model)
        if not cfg:
            st.warning("No keys yet. Paste at least one key and press Save first.")
        else:
            with st.spinner("Testing each service…"):
                st.dataframe(pd.DataFrame(llm.test_each(cfg)), hide_index=True, width="stretch")
            st.caption("❌ on one service is fine as long as another shows ✅; the backup takes over.")

    st.subheader("Data")
    st.write(f"Stored in: {'Google Sheet' if s.kind == 'sheet' else 'this computer'}: `{s.link()}`")
    att = pd.DataFrame(s.attempts())
    if len(att):
        st.download_button("Download all answers (CSV)", att.drop(columns=["ts"], errors="ignore").to_csv(index=False)
                           .encode("utf-8-sig"), "all_answers.csv")
    if st.button("Undo all unit corrections and left-out questions"):
        s.clear_corrections()
        st.success("Cleared.")
    if getattr(s, "errors", None):
        st.warning("Recent Google Sheet write problems: " + "; ".join(s.errors[-3:]))
