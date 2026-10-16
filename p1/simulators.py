"""Interactive simulators for Paper 1: hypothesis testing, syllogisms with Venn diagrams, square of opposition.

All results are calculated (normal distribution maths; every possible Venn situation checked), never hard-coded.
"""
from __future__ import annotations

import random
from statistics import NormalDist

import altair as alt
import pandas as pd
import streamlit as st

from .generators import FORMS, REGIONS, RELATION, SQUARE, _holds, _models
from .ui_common import ss

N01 = NormalDist()


# ================================================================== hypothesis testing
def power_calc(alpha: float, n_per_group: int, d: float, tails: int = 2) -> dict:
    """Two-group comparison (z approximation): power, beta, critical z and the shift of the alternative."""
    z = N01.inv_cdf(1 - alpha / tails)
    delta = d * (n_per_group / 2) ** 0.5
    power = N01.cdf(delta - z) + (N01.cdf(-delta - z) if tails == 2 else 0.0)
    z80 = N01.inv_cdf(0.80)
    n80 = 2 * ((z + z80) / d) ** 2
    return {"z": z, "delta": delta, "power": power, "beta": 1 - power, "n80": n80}


def page_hypothesis():
    st.subheader("🔬 Hypothesis testing: Type I and Type II errors")
    st.markdown("Move the sliders and watch how **α (significance level)**, **sample size** and **effect size** "
                "change the risk of each error. Two groups are compared (e.g. a new teaching method vs the old one).")
    c1, c2, c3 = st.columns(3)
    alpha = c1.select_slider("Significance level α (Type I risk)", [0.01, 0.02, 0.05, 0.10], value=0.05)
    n = c2.slider("Sample size (students per group)", 5, 300, 50, step=5)
    d = c3.slider("True effect size (Cohen's d)", 0.1, 1.5, 0.5, step=0.1,
                  help="0.2 = small, 0.5 = medium, 0.8 = large difference between the groups")
    tails = 2 if st.radio("Test", ["Two-tailed (any difference)", "One-tailed (new method is better)"],
                          horizontal=True).startswith("Two") else 1
    r = power_calc(alpha, n, d, tails)
    m = st.columns(4)
    m[0].metric("Type I error (α)", f"{alpha * 100:.0f}%", help="Rejecting H₀ when it is actually true: a false alarm")
    m[1].metric("Type II error (β)", f"{r['beta'] * 100:.1f}%", help="Missing a real effect: failing to reject a false H₀")
    m[2].metric("Power (1 − β)", f"{r['power'] * 100:.1f}%")
    m[3].metric("Students needed for 80% power", f"{r['n80']:.0f} per group")

    prev = ss.get("hyp_prev")
    if prev and prev != (alpha, n, d, tails):
        pa, pn, pd_, pt = prev
        old = power_calc(pa, pn, pd_, pt)["power"]
        change = "rose" if r["power"] > old else "fell"
        why = []
        if alpha != pa:
            why.append(f"α {'increased' if alpha > pa else 'decreased'} → Type I risk {'up' if alpha > pa else 'down'}, "
                       f"so the rejection region {'grows' if alpha > pa else 'shrinks'}")
        if n != pn:
            why.append(f"sample size {'grew' if n > pn else 'shrank'} → the curves {'separate' if n > pn else 'overlap'} more")
        if d != pd_:
            why.append(f"the true effect is {'bigger' if d > pd_ else 'smaller'}")
        if why:
            st.info(f"Power {change} from {old * 100:.1f}% to {r['power'] * 100:.1f}%: " + "; ".join(why) + ".")
    ss.hyp_prev = (alpha, n, d, tails)

    lo, hi = -4.0, max(4.0, r["delta"] + 4)
    xs = [lo + (hi - lo) * i / 400 for i in range(401)]
    rows = []
    for x in xs:
        h0, h1 = N01.pdf(x), N01.pdf(x - r["delta"])
        reject = x > r["z"] or (tails == 2 and x < -r["z"])
        rows.append({"z": x, "H₀ true (no real difference)": h0, "H₁ true (real difference)": h1,
                     "Type I (α)": h0 if reject else 0.0, "Type II (β)": 0.0 if reject else h1})
    df = pd.DataFrame(rows)
    base = alt.Chart(df).encode(x=alt.X("z:Q", title="Test statistic"))
    curves = df.melt("z", ["H₀ true (no real difference)", "H₁ true (real difference)"], "Curve", "density")
    areas = df.melt("z", ["Type I (α)", "Type II (β)"], "Error", "density")
    chart = (alt.Chart(areas).mark_area(opacity=0.45).encode(
                 x="z:Q", y=alt.Y("density:Q", title=None, axis=None),
                 color=alt.Color("Error:N", scale=alt.Scale(domain=["Type I (α)", "Type II (β)"],
                                                            range=["#dc2626", "#f59e0b"]), title="Shaded")) +
             alt.Chart(curves).mark_line(strokeWidth=2).encode(
                 x="z:Q", y="density:Q", strokeDash=alt.StrokeDash("Curve:N", title=None),
                 color=alt.value("#1e293b")) +
             alt.Chart(pd.DataFrame({"z": [r["z"]] + ([-r["z"]] if tails == 2 else [])})).mark_rule(
                 color="#64748b", strokeDash=[4, 4]).encode(x="z:Q"))
    st.altair_chart(chart.properties(height=280), width="stretch")
    st.caption("Dashed vertical line(s) = critical value. Red = Type I region (under H₀). Orange = Type II region "
               "(under H₁). Bigger samples or bigger effects push the H₁ curve right, shrinking the orange area.")
    with st.expander("📌 What the exam asks about this", expanded=True):
        st.markdown("""
- **Type I error**: rejecting a **true** null hypothesis (a false positive). Its probability is **α**.
- **Type II error**: failing to reject a **false** null hypothesis (a false negative). Its probability is **β**.
- **Power = 1 − β**: the chance of detecting an effect that really exists.
- Lowering α (e.g. 0.05 → 0.01) reduces Type I risk **but increases** Type II risk, at the same sample size.
- Power rises with a **larger sample**, a **larger effect**, a **larger α**, and a **one-tailed** test
  (when the direction is predicted correctly).
""")


# ================================================================== syllogisms + Venn diagrams
FORM_WORDS = {"A": "All", "E": "No", "I": "Some", "O": "Some … not"}
GEO = {"S": (150, 130), "P": (250, 130), "M": (200, 215)}
R = 88


def _sentence(form, x, y):
    return FORMS[form].format(x=x, y=y)


def analyse(premises, conclusion):
    """premises: [(form, X, Y), ...] over S/M/P letters. Returns verdict, shaded regions, X marks, counterexample."""
    modern = _follows(premises, conclusion, existential=False)
    traditional = _follows(premises, conclusion, existential=True)
    sat = [m for m in _models(False) if all(_holds(f, a, b, m) for f, a, b in premises)]
    shaded = [r for r in REGIONS if all(r not in m for m in sat)]
    marks = []
    for f, a, b in premises:
        if f in "IO":
            cands = [r for r in REGIONS if a in r and ((b in r) == (f == "I")) and r not in shaded]
            marks.append(cands)
    counter = None
    if not modern:
        bad = [m for m in sat if not _holds(*conclusion, m)]
        counter = min(bad, key=len) if bad else None
    return {"modern": modern, "traditional": traditional, "shaded": shaded, "marks": marks, "counter": counter}


def _follows(premises, conclusion, existential):
    for m in _models(existential):
        if all(_holds(f, a, b, m) for f, a, b in premises) and not _holds(*conclusion, m):
            return False
    return True


def distributed(form, pos):
    return (pos == "subj" and form in "AE") or (pos == "pred" and form in "EO")


def rule_check(premises, conclusion, names):
    """Classical rules. Returns a list of broken rules in plain words."""
    out = []
    in_prem = {}
    for f, a, b in premises:
        in_prem.setdefault(a, []).append(distributed(f, "subj"))
        in_prem.setdefault(b, []).append(distributed(f, "pred"))
    if len(premises) == 2 and not any(in_prem.get("M", [])):
        out.append(f"**Undistributed middle**: the middle term '{names['M']}' is not distributed (not covered by "
                   f"'All'/'No') in either premise, so the premises never link {names['S']} and {names['P']} for sure.")
    cf, ca, cb = conclusion
    for term, pos in ((ca, "subj"), (cb, "pred")):
        if distributed(cf, pos) and not any(in_prem.get(term, [])):
            kind = "major" if term == "P" else "minor"
            out.append(f"**Illicit {kind}**: '{names[term]}' is distributed in the conclusion but not in its premise.")
    neg = [f for f, _, _ in premises if f in "EO"]
    if len(neg) == 2:
        out.append("**Exclusive premises**: two negative premises give no conclusion.")
    elif len(neg) == 1 and cf in "AI":
        out.append("**Affirmative conclusion from a negative premise**: if a premise is negative, the conclusion must be negative.")
    elif not neg and cf in "EO":
        out.append("**Negative conclusion from affirmative premises**.")
    if len(premises) == 2 and all(f in "IO" for f, _, _ in premises) and not out:
        out.append("**Two particular premises**: nothing follows from two 'Some' statements.")
    return out


def mood_figure(premises, conclusion):
    if len(premises) != 2:
        return ""
    major = next(p for p in premises if "P" in p[1:])
    minor = next(p for p in premises if "S" in p[1:])
    fig = {("M", "S"): {("M", "P"): 3, ("P", "M"): 4}, ("S", "M"): {("M", "P"): 1, ("P", "M"): 2}}
    f = fig[(minor[1], minor[2])][(major[1], major[2])]
    return f"Mood **{major[0]}{minor[0]}{conclusion[0]}**, Figure **{f}**"


def _region_words(r, names):
    inside = [names[t] for t in "SMP" if t in r]
    outside = [names[t] for t in "SMP" if t not in r]
    return f"some things that are {' and '.join(inside)}" + (f" but not {' or '.join(outside)}" if outside else "")


def venn_image(analysis, names, scale: int = 2):
    key = (tuple(sorted("".join(sorted(r)) for r in analysis["shaded"])),
           tuple(tuple(sorted("".join(sorted(r)) for r in m)) for m in analysis["marks"]),
           tuple(names[t] for t in "SMP"), scale)
    return _venn_cached(key, analysis, names, scale)


_VENN_CACHE: dict = {}


def _venn_cached(key, analysis, names, scale):
    if key not in _VENN_CACHE:
        if len(_VENN_CACHE) > 200:
            _VENN_CACHE.clear()
        _VENN_CACHE[key] = _venn_draw(analysis, names, scale)
    return _VENN_CACHE[key]


def _venn_draw(analysis, names, scale: int = 2):
    """Exact Venn diagram as a picture: each pixel is tested against the three circles, so shading is always
    precise. Hatched = must be empty; X = something must be there (on a line = could be either side)."""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 400 * scale, 330 * scale
    img = Image.new("RGB", (W, H), "white")
    px = img.load()
    shaded = set(analysis["shaded"])
    sums = {r: [0, 0, 0] for r in REGIONS}
    for yy in range(H):
        for xx in range(W):
            x, y = xx / scale, yy / scale
            inside = frozenset(t for t, (cx, cy) in GEO.items() if (x - cx) ** 2 + (y - cy) ** 2 < R * R)
            if inside in shaded:
                px[xx, yy] = (100, 116, 139) if (xx + yy) % (7 * scale) < 2 * scale else (226, 232, 240)
            if inside in sums and xx % 4 == 0 and yy % 4 == 0:
                s_ = sums[inside]
                s_[0] += x
                s_[1] += y
                s_[2] += 1
    cen = {r: (v[0] / v[2], v[1] / v[2]) for r, v in sums.items() if v[2]}
    d = ImageDraw.Draw(img)
    colors = {"S": (37, 99, 235), "M": (22, 163, 74), "P": (220, 38, 38)}
    for t, (cx, cy) in GEO.items():
        d.ellipse([(cx - R) * scale, (cy - R) * scale, (cx + R) * scale, (cy + R) * scale],
                  outline=colors[t], width=3 * scale)
    try:
        font = ImageFont.load_default(size=15 * scale)
    except TypeError:                                   # older Pillow
        font = ImageFont.load_default()
    for t, (x, y, anchor) in {"S": (85, 30, "rm"), "P": (315, 30, "lm"), "M": (200, 318, "mm")}.items():
        d.text((x * scale, y * scale), names[t][:18], fill=colors[t], font=font, anchor=anchor)

    def cross(x, y, color):
        k = 7 * scale
        x, y = x * scale, y * scale
        d.line([x - k, y - k, x + k, y + k], fill=color, width=3 * scale)
        d.line([x - k, y + k, x + k, y - k], fill=color, width=3 * scale)

    for cands in analysis["marks"]:
        if len(cands) == 1:
            cross(*cen[cands[0]], (17, 17, 17))
        elif len(cands) == 2:
            (x1, y1), (x2, y2) = cen[cands[0]], cen[cands[1]]
            cross((x1 + x2) / 2, (y1 + y2) / 2, (124, 58, 237))
    return img.resize((400, 330), Image.LANCZOS)


def page_syllogism():
    st.subheader("🧩 Syllogism tester with Venn diagram")
    st.markdown("Build any syllogism. The app checks **every possible situation** (all 128 ways the three circles "
                "can be filled) to decide whether the conclusion must follow, and draws the Venn diagram.")
    defaults = {"syl_S": "Teachers", "syl_M": "Researchers", "syl_P": "Innovators",
                "syl_f1": "A", "syl_o1": "S–M", "syl_f2": "I", "syl_o2": "M–P", "syl_fc": "I", "syl_oc": "S–P"}
    for k, v in defaults.items():
        ss.setdefault(k, v)
    if st.button("🎲 Random syllogism"):
        ss.syl_f1, ss.syl_f2, ss.syl_fc = (random.choice("AEIO") for _ in range(3))
        ss.syl_o1, ss.syl_o2 = random.choice(["S–M", "M–S"]), random.choice(["M–P", "P–M"])
        ss.syl_oc = "S–P"
    c = st.columns(3)
    names = {"S": c[0].text_input("Subject of the conclusion (S)", key="syl_S"),
             "M": c[1].text_input("Middle term (M)", key="syl_M"),
             "P": c[2].text_input("Predicate of the conclusion (P)", key="syl_P")}
    fmt = lambda f: FORM_WORDS[f]

    def row(label, fkey, okey, orders):
        cc = st.columns([1, 1, 3])
        f = cc[0].selectbox(label, list("AEIO"), format_func=fmt, key=fkey)
        o = cc[1].selectbox("Order", orders, key=okey)
        a, b = o.split("–")
        cc[2].markdown(f"<div style='padding-top:1.9rem'><b>{_sentence(f, names[a], names[b])}</b></div>",
                       unsafe_allow_html=True)
        return (f, a, b)

    p1 = row("Premise 1", "syl_f1", "syl_o1", ["S–M", "M–S"])
    p2 = row("Premise 2", "syl_f2", "syl_o2", ["M–P", "P–M"])
    cn = row("Conclusion", "syl_fc", "syl_oc", ["S–P", "P–S"])
    a = analyse([p1, p2], cn)
    if a["modern"]:
        st.success("✅ **Valid**: the conclusion follows in every possible situation.")
    elif a["traditional"]:
        st.warning("🟡 **Valid only in traditional logic**: it follows only if we assume every class has members "
                   "(existential import). Modern logic calls this the *existential fallacy*.")
    else:
        st.error("❌ **Invalid**: the premises can be true while the conclusion is false.")
    mf = mood_figure([p1, p2], cn)
    if mf:
        st.caption(mf)
    left, right = st.columns([1, 1])
    with left:
        st.image(venn_image(a, names), width=380)
        st.caption("Hatched = must be empty. ✕ = something must be there; a purple ✕ on a line means it could be "
                   "on either side.")
    with right:
        problems = rule_check([p1, p2], cn, names)
        if problems:
            st.markdown("**Why:**\n" + "\n".join(f"- {p}" for p in problems))
        if a["counter"] is not None:
            st.markdown("**A situation that breaks it:** imagine there are " +
                        "; ".join(_region_words(r, names) for r in a["counter"]) + ", and nothing else. Both premises "
                        f"are true, but '{_sentence(cn[0], names[cn[1]], names[cn[2]])}' is false.")
        good = [(f, x, y) for f in "AEIO" for x, y in (("S", "P"), ("P", "S"))
                if _follows([p1, p2], (f, x, y), False)]
        st.markdown("**Conclusions that do follow:** " + (", ".join(f"'{_sentence(f, names[x], names[y])}'" for f, x, y in good)
                                                         if good else "none (no valid conclusion about these two terms)."))


# ================================================================== square of opposition
def page_square():
    st.subheader("⬛ Square of opposition explorer")
    c = st.columns(3)
    x = c[0].text_input("Subject", "students", key="sq_x")
    y = c[1].text_input("Predicate", "learners", key="sq_y")
    given = c[2].selectbox("Given proposition", list("AEIO"), format_func=lambda f: f"{f}: {_sentence(f, x, y)}")
    truth = st.radio("It is…", ["True", "False"], horizontal=True) == "True"
    table = SQUARE[(given, truth)]
    rows = [{"Proposition": f"{given}: {_sentence(given, x, y)}", "Relation to given": "(given)",
             "Truth value": "✅ True" if truth else "❌ False"}]
    lab = {True: "✅ True", False: "❌ False", None: "❓ Undetermined"}
    for k in "AEIO":
        if k == given:
            continue
        rel, _ = RELATION[frozenset((given, k))]
        rows.append({"Proposition": f"{k}: {_sentence(k, x, y)}", "Relation to given": rel, "Truth value": lab[table[k]]})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.markdown("""
- **Contradictories** (A–O, E–I): always opposite truth values.
- **Contraries** (A–E): cannot both be true; can both be false.
- **Sub-contraries** (I–O): cannot both be false; can both be true.
- **Subalternation** (A→I, E→O): truth flows **down**, falsity flows **up**.
""")


def page_simulators(C):
    st.title("🧪 Simulators")
    st.caption("Play with the ideas behind the questions. Every result is calculated, not memorised.")
    t1, t2, t3 = st.tabs(["🔬 Type I / II errors", "🧩 Syllogisms & Venn", "⬛ Square of opposition"])
    with t1:
        page_hypothesis()
    with t2:
        page_syllogism()
    with t3:
        page_square()
