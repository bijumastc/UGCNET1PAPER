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


@st.cache_resource(show_spinner=False)
def _bundle_zips(bundle_dir: str) -> dict:
    """Which images_N.zip holds each picture (the bundle packs pictures into a few zip files)."""
    import zipfile

    index = {}
    for zp in sorted(Path(bundle_dir).glob("images_*.zip")):
        z = zipfile.ZipFile(zp)
        for name in z.namelist():
            index[name] = z
    return index


def _bundle_image(app_dir: str, rel: str):
    bundle = Path(app_dir) / "bundle"
    loose = bundle / rel
    if loose.exists():                                # older bundles: a plain img/ folder
        return str(loose)
    z = _bundle_zips(str(bundle)).get(rel)
    return z.read(rel) if z else None


def _images(C, q, field_img, field_regions):
    if q.get(field_img):                              # cloud bundle: pre-cut images
        return [im for im in (_bundle_image(C.app_dir, p) for p in q[field_img]) if im is not None]
    path = source_path(C, q)
    if path and q.get(field_regions):
        return crop_regions(path, q[field_regions], Path(C.folder) / ".p1_trainer" / "crops")
    return []


_KEEP_BREAK = None


def reflow(text: str) -> str:
    """Join lines that a PDF wrapped in mid-sentence; keep list items (A., (1), i., Statement I…) on their own lines."""
    import re

    global _KEEP_BREAK
    if _KEEP_BREAK is None:
        _KEEP_BREAK = re.compile(r"^\s*(?:\(?[A-Ea-e1-9]\s*[\.\)]|\([ivxIVX]+\)|[ivxIVX]+[\.\)]\s|list\b|statement\b|"
                                 r"assertion\b|reason\b|choose\b|select\b|codes?\b|[-•*]\s)", re.I)
    out = []
    for line in (text or "").splitlines():
        s = line.strip()
        if not s:
            continue
        if out and not out[-1].endswith((":", "?")) and not _KEEP_BREAK.match(s):
            out[-1] += " " + s
        else:
            out.append(s)
    return "\n".join(out)


def show_question(C, q, show_group=True):
    """The original picture for scanned NTA questions, text otherwise."""
    if show_group and (q.get("group_text") or q.get("group_img") or q.get("group_regions")):
        with st.expander("📄 Passage / data for this question", expanded=True):
            imgs = _images(C, q, "group_img", "group_regions") if q.get("display") == "image" else []
            if imgs:
                for im in imgs:
                    st.image(im, width="stretch")
            else:
                st.markdown(reflow(q["group_text"]).replace("\n", "  \n"))
    imgs = _images(C, q, "img", "regions") if q.get("display") == "image" else []
    if imgs:
        for im in imgs:
            st.image(im, width="stretch")
    else:
        first, _, rest = reflow(q["text"]).partition("\n")
        st.markdown("#### " + first)
        if rest:
            st.markdown(rest.replace("\n", "  \n"))


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
