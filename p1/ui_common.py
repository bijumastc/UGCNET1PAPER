"""Widgets shared by the student and teacher pages."""
from __future__ import annotations

from pathlib import Path

import altair as alt
import streamlit as st

from .crops import crop_regions

BLUE = "#2563eb"
ss = st.session_state


def go(target: str, **state):
    """Button callback: jump to another page with some settings pre-filled."""
    ss.update(state)
    ss.nav = target


def source_path(C, q) -> str | None:
    if C.mode == "bundle":
        return None
    p = Path(q.get("source_path") or "")
    if p.exists():
        return str(p)
    hits = list(Path(C.folder).rglob(q.get("source_file", "?")))
    return str(hits[0]) if hits else None


def _images(C, q, field_img, field_regions):
    if q.get(field_img):                              # cloud bundle: pre-cut images
        return [str(Path(C.app_dir) / "bundle" / p) for p in q[field_img]]
    path = source_path(C, q)
    if path and q.get(field_regions):
        return crop_regions(path, q[field_regions], Path(C.folder) / ".p1_trainer" / "crops")
    return []


def show_question(C, q, show_group=True):
    """The original picture for scanned NTA questions, text otherwise."""
    if show_group and (q.get("group_text") or q.get("group_img") or q.get("group_regions")):
        with st.expander("📄 Passage / data for this question", expanded=True):
            imgs = _images(C, q, "group_img", "group_regions") if q.get("display") == "image" else []
            if imgs:
                for im in imgs:
                    st.image(im, width="stretch")
            else:
                st.markdown(q["group_text"])
    imgs = _images(C, q, "img", "regions") if q.get("display") == "image" else []
    if imgs:
        for im in imgs:
            st.image(im, width="stretch")
    else:
        st.markdown("#### " + q["text"].replace("\n", "  \n"))


def has_option_text(q) -> bool:
    return q.get("display") == "text" and len(q.get("options") or []) == 4


def option_label(q, i):
    return f"({i + 1}) {q['options'][i]}" if has_option_text(q) else f"Option {i + 1}"


def answer_text(q):
    a = q["answer"]
    return f"({a + 1}) {q['options'][a]}" if has_option_text(q) else f"Option {a + 1}"


def source_badge(q):
    kind = {"official": "🏛️ NTA paper", "memory": "🧠 memory-based (coaching)", "generated": "♾️ generated practice",
            "ai": "🤖 AI-written, teacher-approved"}.get(q.get("origin"), "📄 paper")
    if q.get("origin") in ("generated", "ai"):
        return kind
    return f"{q.get('session', '')} · Q{q.get('qno', '')} · {kind}"


def bar_chart(df, x, y, pct=False, height=320):
    enc_x = alt.X(f"{x}:Q", axis=alt.Axis(format="%") if pct else alt.Axis(tickMinStep=1),
                  scale=alt.Scale(domain=[0, 1]) if pct else alt.Undefined)
    return alt.Chart(df).mark_bar(color=BLUE, cornerRadiusEnd=4, size=14).encode(
        x=enc_x, y=alt.Y(f"{y}:N", sort="-x" if not pct else None, title=None, axis=alt.Axis(labelLimit=260)),
        tooltip=list(df.columns)).properties(height=height)


def steps_md(steps) -> str:
    return "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
