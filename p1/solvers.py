"""Step-by-step worked solutions for series and coding questions.

A solution is shown only when exactly one option fits a rule AND that option is the
answer in the key. If the solver disagrees with the key or finds no unique fit, nothing
is shown, so the learner never sees a made-up explanation.
"""
from __future__ import annotations

import re
from fractions import Fraction

ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _diffs(s):
    return [b - a for a, b in zip(s, s[1:])]


def _const(s):
    return len(s) >= 2 and all(x == s[0] for x in s)


def _fmt(xs):
    return ", ".join(str(int(x)) if x == int(x) else str(float(x)) for x in xs)


def _is_squares(d):
    r = [round(abs(x) ** 0.5) for x in d]
    return all(x >= 0 and r[i] ** 2 == x for i, x in enumerate(d)) and _const(_diffs(r)) and _diffs(r)[0] == 1


def _is_cubes(d):
    r = [round(abs(x) ** (1 / 3)) for x in d]
    return all(x >= 0 and r[i] ** 3 == x for i, x in enumerate(d)) and _const(_diffs(r)) and _diffs(r)[0] == 1


PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]


def series_rule(s: list) -> list[str] | None:
    """If a known rule generates the whole sequence s, return explanation steps, else None."""
    if len(s) < 4:
        return None
    d1 = _diffs(s)
    if _const(d1):
        return [f"Differences between neighbours: {_fmt(d1)}.", f"They are all {_fmt([d1[0]])}: add {_fmt([d1[0]])} each time."]
    d2 = _diffs(d1)
    if _const(d2):
        return [f"Differences: {_fmt(d1)}.", f"Differences of those differences: {_fmt(d2)} (constant).",
                f"So each difference grows by {_fmt([d2[0]])}."]
    if all(x != 0 for x in s):
        r = [Fraction(b) / Fraction(a) for a, b in zip(s, s[1:])]
        if _const(r):
            return [f"Each term divided by the one before: {', '.join(str(x) for x in r)}.",
                    f"Constant ratio {r[0]}: multiply by {r[0]} each time."]
    if _is_squares(d1):
        return [f"Differences: {_fmt(d1)}.", "These are consecutive squares (…, n², (n+1)², …)."]
    if _is_cubes(d1):
        return [f"Differences: {_fmt(d1)}.", "These are consecutive cubes."]
    if len(d1) >= 3 and all(x in PRIMES for x in d1):
        i = PRIMES.index(d1[0])
        if d1 == PRIMES[i:i + len(d1)]:
            return [f"Differences: {_fmt(d1)}.", "These are consecutive prime numbers."]
    if len(d2) >= 3 and all(x != 0 for x in d1):
        r2 = [Fraction(b) / Fraction(a) for a, b in zip(d1, d1[1:])]
        if _const(r2):
            return [f"Differences: {_fmt(d1)}.", f"Each difference is {r2[0]} times the previous one."]
    if len(d2) >= 3 and _const(_diffs(d2)):
        return [f"Differences: {_fmt(d1)}.", f"Second differences: {_fmt(d2)}.",
                f"Third differences are constant ({_fmt([_diffs(d2)[0]])})."]
    # a(n) = a(n-1) * k + c
    a, b, c = s[0], s[1], s[2]
    if a != b:
        k = Fraction(c - b, b - a)
        cc = b - k * a
        if k not in (0, 1) and all(s[i + 1] == s[i] * k + cc for i in range(len(s) - 1)):
            return [f"Each term = previous × {k} {'+' if cc >= 0 else '−'} {abs(cc)}.",
                    "Check: " + "; ".join(f"{_fmt([s[i]])}×{k}{'+' if cc >= 0 else '−'}{abs(cc)}={_fmt([s[i+1]])}"
                                          for i in range(min(3, len(s) - 1)))]
    # a(n) = a(n-1) * n + n  or  a(n-1) * n   (n counting from 1)
    for name, f in (("× 1 + 1, × 2 + 2, × 3 + 3 …", lambda x, n: x * n + n),
                    ("× 1, × 2, × 3 …", lambda x, n: x * n),
                    ("× 2 + 1, × 2 + 2, × 2 + 3 …", lambda x, n: x * 2 + n),
                    ("+ 1², + 2², + 3² …", lambda x, n: x + n * n)):
        for start in (1, 2):
            if all(s[i + 1] == f(s[i], i + start) for i in range(len(s) - 1)):
                return [f"Pattern of operations: {name} (starting at {start})."]
    # alternating series
    if len(s) >= 6:
        odd, even = s[0::2], s[1::2]
        if series_rule_simple(odd) and series_rule_simple(even):
            return ["Two series are mixed together.",
                    f"1st, 3rd, 5th… terms: {_fmt(odd)} → {series_rule_simple(odd)}",
                    f"2nd, 4th, 6th… terms: {_fmt(even)} → {series_rule_simple(even)}"]
    # n^2 or n^3 based
    for name, g in (("n² + n", lambda n: n * n + n), ("n² − 1", lambda n: n * n - 1), ("n² + 1", lambda n: n * n + 1),
                    ("n³ + 1", lambda n: n ** 3 + 1), ("n³ − 1", lambda n: n ** 3 - 1), ("n³ + n", lambda n: n ** 3 + n),
                    ("n²", lambda n: n * n), ("n³", lambda n: n ** 3)):
        for off in range(0, 12):
            if all(s[i] == g(i + off) for i in range(len(s))):
                return [f"Each term is {name} for n = {off}, {off + 1}, {off + 2}, …"]
    return None


def series_rule_simple(s):
    d = _diffs(s)
    if len(s) >= 2 and _const(d):
        return f"add {_fmt([d[0]])}"
    if len(s) >= 2 and all(x != 0 for x in s):
        r = [Fraction(b) / Fraction(a) for a, b in zip(s, s[1:])]
        if _const(r):
            return f"multiply by {r[0]}"
    return None


def _num(tok: str):
    tok = tok.strip().replace(",", "")
    try:
        return Fraction(tok)
    except Exception:
        return None


def solve_number_series(text: str, options: list[str], answer: int):
    """Return explanation lines if the key's option is the unique option that completes the series."""
    if not options or len(options) != 4 or answer is None:
        return None
    if not re.search(r"series|next (number|term)|missing|question mark|\?", text, re.I):
        return None
    m = re.search(r"((?:-?\d+(?:\.\d+)?\s*,\s*){3,}(?:-?\d+(?:\.\d+)?|\?|_+)(?:\s*,\s*(?:-?\d+(?:\.\d+)?|\?|_+))*\s*,?\s*\??)", text)
    if not m:
        return None
    raw = [t.strip() for t in re.split(r"[,\s]+", m.group(1).strip(" ,")) if t.strip()]
    if "?" not in raw and not any(t.startswith("_") for t in raw):
        raw.append("?")
    slot = next(i for i, t in enumerate(raw) if t == "?" or t.startswith("_"))
    known = [_num(t) for i, t in enumerate(raw) if i != slot]
    if any(k is None for k in known):
        return None
    opts = [_num(o) for o in options]
    fits = []
    for i, v in enumerate(opts):
        if v is None:
            continue
        seq = known[:slot] + [v] + known[slot:]
        steps = series_rule(seq)
        if steps:
            fits.append((i, steps, seq))
    if len(fits) != 1 or fits[0][0] != answer:
        return None
    i, steps, seq = fits[0]
    return ["Write the series: " + _fmt(known[:slot]) + ", ?, " + _fmt(known[slot:]) if slot < len(known)
            else "Write the series: " + _fmt(known) + ", ?"] + steps + \
           [f"So the missing term is {options[i]} → option {i + 1}.", "Check: the rule fits every term with this value."]


def solve_coding(text: str, options: list[str], answer: int):
    """Letter-to-letter codes: constant shift, reverse alphabet (A↔Z), or reverse alphabet with shift."""
    if not options or len(options) != 4 or answer is None:
        return None
    pairs = re.findall(r"\b([A-Z]{2,})\b[’'\"]?\s+(?:is|are)\s+(?:coded|written)\s+as\s+[’'\"]?([A-Z]{2,})\b", text)
    target = re.findall(r"(?i:how|what|then)[^?]*?[‘'\"’]?\b([A-Z]{3,})\b[’'\"]?\s*(?i:will|would|be|is|can)", text)
    letter_rule = re.findall(r"\b([A-Z])\s+is\s+coded\s+as\s+([A-Z])\b", text)
    rules = []
    if letter_rule and all(ord(a) + ord(b) == ord("A") + ord("Z") for a, b in letter_rule):
        rules.append(("reverse", "Each letter is replaced by its opposite letter: A↔Z, B↔Y, C↔X… "
                                 "(the two positions always add up to 27)."))
    for w, c in pairs:
        if len(w) != len(c):
            continue
        shifts = {(ord(b) - ord(a)) % 26 for a, b in zip(w, c)}
        if len(shifts) == 1:
            k = shifts.pop()
            k_s = k if k <= 13 else k - 26
            rules.append((("shift", k), f"From {w} → {c}, every letter moves {abs(k_s)} step(s) "
                                        f"{'forward' if k_s > 0 else 'backward'} in the alphabet."))
        if all(ord(a) + ord(b) == ord("A") + ord("Z") for a, b in zip(w, c)):
            rules.append(("reverse", f"From {w} → {c}, each letter is replaced by its opposite (A↔Z, B↔Y…)."))
    if not rules or not target:
        return None
    word = target[-1]
    kind, why = rules[0]
    if kind == "reverse":
        code = "".join(ALPHA[25 - ALPHA.index(ch)] for ch in word)
        detail = " ".join(f"{ch}({ALPHA.index(ch)+1})→{ALPHA[25-ALPHA.index(ch)]}({26-ALPHA.index(ch)})" for ch in word)
    else:
        k = kind[1]
        code = "".join(ALPHA[(ALPHA.index(ch) + k) % 26] for ch in word)
        detail = " ".join(f"{ch}→{ALPHA[(ALPHA.index(ch)+k)%26]}" for ch in word)
    clean = [re.sub(r"[^A-Z]", "", o.upper()) for o in options]
    hits = [i for i, o in enumerate(clean) if o == code]
    if hits != [answer]:
        return None
    return [why, f"Apply it to {word}: {detail}.", f"So {word} is written as {code} → option {answer + 1}."]


def worked_solution(q: dict):
    if q.get("subtopic") in ("U5.1", "U5.2") or re.search(r"\bseries\b|next (number|term)|missing (number|term)|"
                                                          r"question mark", q["text"], re.I):
        s = solve_number_series(q["text"], q.get("options") or [], q.get("answer"))
        if s:
            return s
    if q.get("subtopic") == "U5.3" or re.search(r"\bcoded\b", q["text"], re.I):
        return solve_coding(q["text"], q.get("options") or [], q.get("answer"))
    return None
