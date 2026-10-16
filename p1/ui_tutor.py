"""AI tutor (free AI services with automatic backup): topic chat in Learn, and 'explain this question' in Practice."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from . import llm
from .learn import primer
from .store import IST, now_iso
from .syllabus import UNITS, subtopic_name, unit_label, unit_name
from .ui_common import ss

QUICK = [("🌱 Explain from zero", "Explain this topic from zero, as if I am a complete beginner."),
         ("🧮 Worked example", "Show me one fully worked example of a typical exam question on this topic, step by step."),
         ("❓ Quiz me", "Quiz me: ask me ONE exam-style multiple-choice question on this topic. Wait for my answer "
                       "before telling me if I'm right."),
         ("⚠️ Common mistakes", "What are the most common mistakes students make on this topic, and how do I avoid them?"),
         ("🧠 Memory tricks", "Give me simple memory tricks (mnemonics) for the key facts in this topic.")]


def tutor_cfg(C) -> dict:
    if C.store.get("class:ai_tutor_on", "1") != "1":
        return {}
    return llm.config(C.secrets, C.store, C.gemini_model)


def _today_used(C) -> int:
    today = datetime.now(IST).strftime("%Y-%m-%d")
    return sum(1 for r in C.store.ai_log(C.user["id"]) if str(r.get("time", "")).startswith(today))


def _limit(C) -> int:
    return int(float(C.store.get("class:ai_daily_limit", 30)))


def _ask(C, cfg, messages, unit, topic, kind, question) -> str | None:
    if C.user["role"] == "student" and _today_used(C) >= _limit(C):
        st.warning(f"You've used today's {_limit(C)} AI questions. 🙂 They reset tomorrow. Meanwhile, Practice and "
                   "the Learn cards are unlimited!")
        return None
    try:
        with st.spinner("🤖 The tutor is thinking…"):
            reply = llm.chat(cfg, messages)
    except llm.LLMError as e:
        st.error(str(e))
        if C.user["role"] != "student" and e.details:
            st.caption("Details for the teacher: " + " | ".join(e.details))
        return None
    C.store.add_ai_log({"time": now_iso(), "student_id": C.user["id"], "unit": unit, "topic": topic, "kind": kind,
                        "question": question[:1000], "reply_chars": len(reply), "reply": reply[:5000],
                        "model": cfg.get("used", "")})
    return reply


def page_tutor(C):
    st.title("🤖 AI tutor")
    cfg = tutor_cfg(C)
    if not cfg:
        if C.user["role"] in ("teacher", "owner"):
            st.info("The AI tutor isn't set up yet. Open **⚙️ Class settings → AI tutor**, paste at least one free "
                    "key (Groq is easiest) and press **🔌 Test**. Online, put the keys in Secrets (DEPLOY.md, Part 3b).")
        else:
            st.info("Your teacher hasn't switched on the AI tutor yet. Learn cards and Practice work as usual. 🙂")
        return
    units = list(UNITS)
    c1, c2 = st.columns(2)
    uid = c1.selectbox("Unit", units, format_func=unit_label,
                       index=units.index(ss.get("tutor_unit")) if ss.get("tutor_unit") in units else 0)
    subs = [s for s in UNITS[uid]["subtopics"] if not s.endswith(".99")]
    sid = c2.selectbox("Topic", subs, format_func=subtopic_name,
                       index=subs.index(ss.get("tutor_sub")) if ss.get("tutor_sub") in subs else 0)
    ss.tutor_unit, ss.tutor_sub = uid, sid
    st.caption(f"AI: {cfg['model']} (automatic backup) · The AI can make mistakes. For scored practice use ✍️ Practice; your "
               f"teacher's key and the Learn cards come first."
               + (f" · Today: {_today_used(C)}/{_limit(C)} questions" if C.user["role"] == "student" else ""))
    hist = ss.setdefault("tutor_hist", {}).setdefault(sid, [])
    examples = [q for q in C.QUESTIONS if q.get("subtopic") == sid and q["status"] == "ok"][:3]
    system = [{"role": "system", "content": llm.TUTOR_SYSTEM},
              {"role": "system", "content": llm.tutor_context(unit_name(uid), subtopic_name(sid), primer(sid), examples)}]

    cols = st.columns(len(QUICK))
    asked = None
    for col, (label, prompt) in zip(cols, QUICK):
        if col.button(label, key=f"tq_{label}"):
            asked = prompt
    for m in hist:
        with st.chat_message(m["role"], avatar="🧑‍🎓" if m["role"] == "user" else "🤖"):
            st.markdown(m["content"])
            if m.get("by") and C.user["role"] != "student":
                st.caption(f"answered by {m['by']}")
    typed = st.chat_input(f"Ask about {subtopic_name(sid)}…")
    asked = typed or asked
    if asked:
        hist.append({"role": "user", "content": asked})
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(asked)
        msgs = system + [{"role": m["role"], "content": m["content"]} for m in hist[-8:]]   # short history: fits free token limits
        reply = _ask(C, cfg, msgs, uid, sid, "chat", asked)
        if reply:
            hist.append({"role": "assistant", "content": reply, "by": cfg.get("used", "")})
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(reply)
                if C.user["role"] != "student":
                    st.caption(f"answered by {cfg.get('used', '')}")
        else:
            hist.pop()
    if hist and st.button("🧹 Start a fresh conversation"):
        ss.tutor_hist[sid] = []
        st.rerun()


def explain_button(C, q, chosen):
    """In Practice feedback: ask the AI tutor to explain the question (official answer stays authoritative)."""
    cfg = tutor_cfg(C)
    if not cfg or q.get("origin") == "generated":
        return
    k = f"aiexp_{q['key']}"
    if k not in ss and st.button("🤖 Explain this with the AI tutor"):
        msgs = [{"role": "system", "content": llm.TUTOR_SYSTEM},
                {"role": "user", "content": llm.explain_question_prompt(q, chosen)}]
        reply = _ask(C, cfg, msgs, q.get("unit"), q.get("subtopic"), "explain", q["text"][:200])
        if reply:
            ss[k] = reply
    if k in ss:
        st.info("🤖 **AI tutor** (may contain mistakes; the official answer above is what counts)\n\n" + ss[k])


def tutor_usage_table(C):
    """Teacher view: who uses the AI tutor and what they ask."""
    rows = C.store.ai_log()
    if not rows:
        st.caption("No AI tutor questions yet.")
        return
    df = pd.DataFrame(rows)
    names = {s["student_id"]: s["name"] for s in C.store.students()}
    df["student"] = df["student_id"].map(lambda s: names.get(s, s))
    df["topic"] = df["topic"].map(lambda s: subtopic_name(s) if s else "")
    st.dataframe(df.groupby("student").agg(questions=("time", "size"), last=("time", "max")).reset_index()
                 .sort_values("questions", ascending=False), hide_index=True, width="stretch")
    st.markdown("**Most-asked topics**")
    st.dataframe(df.groupby("topic").size().reset_index(name="questions").sort_values("questions", ascending=False)
                 .head(10), hide_index=True, width="stretch")
    st.markdown("**Latest questions**")
    st.dataframe(df.sort_values("time", ascending=False)[["time", "student", "topic", "question"]].head(25),
                 hide_index=True, width="stretch")
