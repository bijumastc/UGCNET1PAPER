"""Build the question library from a folder of papers and answer keys.

Steps: find files -> decide paper or key -> extract (cached) -> pair keys with papers
-> attach and cross-check answers -> sort by syllabus -> group look-alike questions.
Every question that can't be verified is kept out of practice with a plain reason.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path

from .classify import block_units, classify, families, family_label, subtopic_within
from .extract import (G_QSTART, NTA_QHEAD, PARSER_VERSION, answers_from_qid_tokens, page_lines, parse_generic,
                      parse_key, parse_nta, read_pdf)
from .syllabus import UNITS

DATA_DIR = ".p1_trainer"
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

STATUS_TEXT = {
    "ok": "Verified",
    "dropped": "Dropped / bonus in the key",
    "multi": "Key accepts more than one option",
    "conflict": "Answer sources disagree",
    "no_key": "No answer found for this question",
    "bad_key": "Key option not found in this paper",
    "no_options": "Options could not be read",
    "duplicate": "Same question already taken from an official paper",
}


# ------------------------------------------------------------------ small helpers
def _sha(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def session_info(name: str, text: str = "") -> dict:
    """Date, shift and a readable label from the paper's own header or its filename."""
    src = text[:3000] + " " + name.replace("_", " ").replace("-", " ")
    m = re.search(r"(\d{1,2})\s*(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*,?\s*(20\d\d)",
                  src, re.I)
    date = None
    if m:
        date = f"{m.group(3)}-{MONTHS[m.group(2).lower()[:3]]:02d}-{int(m.group(1)):02d}"
    shift = None
    m_s = re.search(r"shift\s*[-:]?\s*(\d)", src, re.I)
    if m_s:
        shift = f"Shift {m_s.group(1)}"
    elif re.search(r"morning", src, re.I):
        shift = "Shift 1"
    elif re.search(r"e+vening|afternoon", src, re.I):
        shift = "Shift 2"
    label = " · ".join(x for x in [date, shift] if x) or Path(name).stem
    return {"date": date, "shift": shift, "label": label}


def _norm_name(name: str) -> str:
    s = Path(name).stem.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    drop = {"answer", "answers", "key", "keys", "ans", "solution", "solutions", "paper", "question", "questions",
            "qp", "ugc", "net", "final", "provisional", "official", "exam", "pdf", "i", "1", "with"}
    return " ".join(t for t in s.split() if t not in drop)


def _skip_name(name: str) -> bool:
    """Files the app writes itself, or project files, are never treated as papers or keys."""
    n = name.lower()
    return n in ("requirements.txt", "readme.txt") or n.startswith("paper1_sorted")


def _looks_like_key_name(name: str) -> bool:
    return bool(re.search(r"\b(answer|ans|key|solution)s?\b", re.sub(r"[^a-z]+", " ", name.lower())))


# ------------------------------------------------------------------ per-file extraction (cached)
def extract_file(path: Path, cache_dir: Path, progress=None) -> dict:
    sha = _sha(path)
    cache = cache_dir / f"{sha}_v{PARSER_VERSION}.json"
    for v in (PARSER_VERSION,):            # page OCR is cached separately, so re-reading a paper is quick
        old = cache_dir / f"{sha}_v{v}.json"
        if old.exists():
            rec = json.loads(old.read_text(encoding="utf-8"))
            if rec.get("role") != "error":            # a failed read is always tried again
                return rec
            old.unlink(missing_ok=True)

    rec = {"file": path.name, "path": str(path), "sha": sha, "role": None, "questions": [], "issues": [],
           "key": None, "kind": None, "error": None, "session": None, "memory_based": False}
    try:
        if path.suffix.lower() in (".csv", ".txt") and _looks_like_key_name(path.name):
            text = path.read_text(encoding="utf-8", errors="ignore")
            rec.update(role="key", key=parse_key(text), kind="text")
        else:
            doc = read_pdf(str(path), progress=progress, cache_dir=cache_dir / "pages") if path.suffix.lower() == ".pdf" else \
                {"pages": [{"lines": [[l, None, None] for l in path.read_text(encoding="utf-8", errors="ignore").splitlines()],
                            "ocr": False}], "kind": "text", "qno_qid": {}, "error": None}
            rec["kind"], rec["error"] = doc["kind"], doc.get("error")
            lines = page_lines(doc["pages"])
            full = "\n".join(l[1] for l in lines)
            n_nta = len(NTA_QHEAD.findall(full))
            n_q = sum(1 for l in lines if G_QSTART.match(l[1]))
            rec["session"] = session_info(path.name, full)
            rec["memory_based"] = bool(re.search(r"memory[\s\-_]*based", path.name + " " + full[:2000], re.I))
            if n_nta >= 3:
                ocr_pages = {i + 1 for i, p in enumerate(doc["pages"]) if p["ocr"]}
                qs, issues = parse_nta(lines, ocr_pages, {int(k): v for k, v in doc["qno_qid"].items()})
                rec.update(role="paper", questions=[q.to_dict() for q in qs], issues=issues)
            elif n_q >= 10 and not (_looks_like_key_name(path.name) and n_q < 30):
                qs, issues = parse_generic(lines)
                if len(qs) >= 5:
                    rec.update(role="paper", questions=[q.to_dict() for q in qs], issues=issues)
            if rec["role"] is None:
                key = parse_key(full)
                if key["by_qno"] or len([t for t in key["tokens"] if len(t) >= 6]) >= 10:
                    rec.update(role="key", key=key)
                else:
                    rec["role"] = "unknown"
    except Exception as e:  # keep going with other files
        rec.update(role="error", error=f"{type(e).__name__}: {e}")
    temporary = any(w in (rec.get("error") or "") for w in ("not enough memory", "Tesseract"))
    if rec["role"] != "error" and not temporary:       # retried next scan (e.g. after installing Tesseract)
        cache.write_text(json.dumps(rec), encoding="utf-8")   # retried next scan if pages were skipped
    return rec


# ------------------------------------------------------------------ build
def build_library(folder: str | Path, progress=None, log=None) -> dict:
    folder = Path(folder).resolve()
    data = folder / DATA_DIR
    cache_dir = data / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in (".pdf", ".txt", ".csv")
                   and DATA_DIR not in p.parts and not _skip_name(p.name))
    seen, unique = {}, []
    for p in files:                       # the same PDF saved twice (e.g. "… - Copy.pdf") is read once
        h = _sha(p)
        if h in seen:
            if log:
                log(f"Skipping {p.name}: same file as {seen[h]}")
            continue
        seen[h] = p.name
        unique.append(p)
    files = unique
    recs, lib = [], None
    n = max(len(files), 1)
    for i, p in enumerate(files):
        if log:
            log(f"Reading {p.name} ({i + 1}/{len(files)})")
        sub = (lambda f, msg="", i=i, p=p: progress((i + f) / n, f"{p.name}: {msg}")) if progress else None
        recs.append(extract_file(p, cache_dir, sub))
        if progress:
            progress((i + 1) / n, f"Finished {p.name}")
        # save after every file, so Practice can use the papers already read while the rest are scanned
        lib = _assemble(folder, data, recs, files, complete=(i == len(files) - 1))
    return lib or _assemble(folder, data, [], files, complete=True)


def _assemble(folder: Path, data: Path, recs: list, files: list, complete: bool) -> dict:
    """Pair keys with papers, verify answers, sort and group; save library.json."""
    papers = [r for r in recs if r["role"] == "paper"]
    keys = [r for r in recs if r["role"] == "key"]
    for k in keys:   # JSON caching turns int keys into strings
        if k["key"].get("by_qno"):
            k["key"]["by_qno"] = {int(n): a for n, a in k["key"]["by_qno"].items()}

    # ---- question records
    questions = []
    for r in papers:
        stem = Path(r["file"]).stem
        for q in r["questions"]:
            q = dict(q)
            q["key"] = q["qid"] or f"{stem}#{q['qno']}"
            if q.get("group_id") and not q.get("qid"):      # passage groups: unique per paper
                q["group_id"] = f"{stem}#{q['group_id']}"
            q["source_file"] = r["file"]
            q["source_path"] = r["path"]
            q["session"] = (r.get("session") or {}).get("label") or stem
            q["session_date"] = (r.get("session") or {}).get("date")
            q["origin"] = "memory" if r.get("memory_based") else ("official" if r["kind"] == "nta" else "paper")
            q["display"] = "image" if q.get("from_ocr") and q.get("regions") else "text"
            q["answer_sources"] = []
            if q.get("inline_answer") is not None:
                lbl = "Answer printed in the paper" + (" (memory-based, coaching)" if q["origin"] == "memory" else "")
                q["answer_sources"].append({"source": lbl, "answer": [q["inline_answer"]], "official": False})
            questions.append(q)
    by_qid = {q["qid"]: q for q in questions if q.get("qid")}

    # ---- keys by Question ID (NTA keys)
    pairing = []
    for k in keys:
        hits = answers_from_qid_tokens(k["key"].get("text") or k["key"]["tokens"], by_qid) if by_qid else {}
        if hits:
            for qid, ans in hits.items():
                by_qid[qid]["answer_sources"].append({"source": f"Key: {k['file']} (matched by Question ID)",
                                                      "answer": ans, "official": k["key"]["official"]})
            files_hit = Counter(by_qid[qid]["source_file"] for qid in hits)
            pairing.append({"key": k["file"], "paper": ", ".join(files_hit), "how": "Question ID",
                            "matched": len(hits)})
            k["_used"] = True

    # ---- keys by question number: pair with the paper whose filename matches best
    for k in keys:
        if k.get("_used") or not k["key"]["by_qno"]:
            continue
        kn = _norm_name(k["file"])
        scored = sorted(((difflib.SequenceMatcher(None, kn, _norm_name(p["file"])).ratio(), p) for p in papers),
                        key=lambda x: -x[0])
        if not scored or scored[0][0] < 0.6 or (len(scored) > 1 and scored[1][0] > scored[0][0] - 0.05):
            pairing.append({"key": k["file"], "paper": None, "how": "question number",
                            "matched": 0, "note": "Could not tell which paper this key belongs to. "
                                                  "Rename it to match its paper (e.g. add '-Answer-Key')."})
            continue
        paper = scored[0][1]
        n = 0
        for q in questions:
            if q["source_file"] != paper["file"]:
                continue
            a = k["key"]["by_qno"].get(q["qno"])
            if a is not None:
                q["answer_sources"].append({"source": f"Key: {k['file']} (matched by question number)",
                                            "answer": [a], "official": k["key"]["official"]})
                n += 1
        pairing.append({"key": k["file"], "paper": paper["file"], "how": "question number", "matched": n})

    # ---- resolve answers
    for q in questions:
        srcs = q["answer_sources"]
        q["answer"], q["status"] = None, "ok"
        if not srcs:
            q["status"] = "no_key"
        elif any("DROP" in s["answer"] for s in srcs):
            q["status"] = "dropped"
        elif any(len(s["answer"]) == 0 for s in srcs):
            q["status"] = "bad_key"
        elif any(len(set(s["answer"])) > 1 for s in srcs):
            q["status"] = "multi"
        else:
            vals = {s["answer"][0] for s in srcs}
            if len(vals) > 1:
                q["status"] = "conflict"
            else:
                q["answer"] = vals.pop()
        if q["status"] == "ok" and q["display"] == "text" and len(q.get("options") or []) != 4:
            q["status"] = "no_options"
        q["answer_official"] = any(s["official"] for s in srcs)
        q["answer_source"] = "; ".join(s["source"] for s in srcs)

    # ---- classify
    for q in questions:
        c = classify(q["text"], q.get("options"), q.get("group_text"))
        q.update(unit=c["unit"], subtopic=c["subtopic"], pattern=c["pattern"], level=c["level"],
                 unit_confidence=c["confidence"], keywords=c["keywords"], needs_review=c["needs_review"],
                 unit_guess=c.get("guess"), subtopic_guess=c.get("guess_subtopic"))

    # ---- NTA papers: the unit comes from the paper's 5-question block when that layout is clear
    for r in papers:
        qs = [q for q in questions if q["source_file"] == r["file"]]
        blocks = block_units(qs)
        for q in qs:
            q["unit_method"] = "keywords"
            if not blocks:
                continue
            b = (q["qno"] - 1) // 5
            if b not in blocks:
                continue
            u = blocks[b]
            q["unit_method"] = "paper order (5-question block)"
            if q.get("unit") != u:
                q["subtopic"] = "U7.3" if u == "U7" and q.get("group_text") else (
                    "U3.1" if u == "U3" else subtopic_within(u, q["text"], q.get("options")))
            q["unit"], q["needs_review"] = u, False

    # ---- duplicates: a memory-based copy of a question we also have officially
    official = [q for q in questions if q["origin"] == "official"]
    for q in questions:
        if q["origin"] != "memory":
            continue
        a = set(re.findall(r"[a-z]{4,}", q["text"].lower()))
        for o in official:
            if o.get("session_date") != q.get("session_date"):
                continue
            b = set(re.findall(r"[a-z]{4,}", o["text"].lower()))
            if a and b and len(a & b) / len(a | b) > 0.7:
                q["status"], q["duplicate_of"] = "duplicate", o["key"]
                break

    # ---- look-alike families (only among usable questions)
    usable = [q for q in questions if q["status"] != "duplicate"]   # patterns use every English question
    fam = families(usable)
    groups = {}
    for q in usable:
        q["family"] = fam.get(q["key"])
        groups.setdefault(q["family"], []).append(q)
    fam_info = {}
    for fid, qs in groups.items():
        sessions = sorted({q["session"] for q in qs})
        fam_info[fid] = {"size": len(qs), "sessions": sessions, "label": family_label(qs) if len(qs) > 1 else None}
    for q in usable:
        q["family_size"] = fam_info[q["family"]]["size"]
        q["family_sessions"] = len(fam_info[q["family"]]["sessions"])

    lib = {
        "folder": str(folder), "built": time.time(), "parser_version": PARSER_VERSION,
        "files": [{"file": r["file"], "role": r["role"], "kind": r["kind"], "error": r["error"],
                   "session": (r.get("session") or {}).get("label"), "memory_based": r.get("memory_based"),
                   "questions": len(r["questions"]), "issues": r["issues"],
                   "key_entries": (len(r["key"]["by_qno"]) if r.get("key") and r["key"]["by_qno"] else None)}
                  for r in recs],
        "pairing": pairing, "questions": questions,
        "families": {fid: v for fid, v in fam_info.items() if v["size"] > 1},
        "file_stamp": _stamp(files) if complete else "incomplete",
        "complete": complete,
    }
    (data / "library.json").write_text(json.dumps(lib), encoding="utf-8")
    return lib


def _stamp(files) -> str:
    return hashlib.sha1("|".join(f"{p.name}:{p.stat().st_size}:{int(p.stat().st_mtime)}" for p in files).encode()).hexdigest()


def current_stamp(folder: str | Path) -> str:
    folder = Path(folder).resolve()
    files = sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in (".pdf", ".txt", ".csv")
                   and DATA_DIR not in p.parts and not _skip_name(p.name))
    return _stamp(files)


def load_library(folder: str | Path) -> dict | None:
    p = Path(folder).resolve() / DATA_DIR / "library.json"
    if not p.exists():
        return None
    lib = json.loads(p.read_text(encoding="utf-8"))
    return lib if lib.get("parser_version") == PARSER_VERSION else None


# ------------------------------------------------------------------ overrides (your corrections)
def load_overrides(folder) -> dict:
    p = Path(folder).resolve() / DATA_DIR / "overrides.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_override(folder, key: str, **fields):
    p = Path(folder).resolve() / DATA_DIR / "overrides.json"
    ov = load_overrides(folder)
    ov.setdefault(key, {}).update(fields)
    p.write_text(json.dumps(ov, indent=1), encoding="utf-8")


def apply_overrides(questions: list, overrides: dict) -> list:
    out = []
    for q in questions:
        q = dict(q)
        o = overrides.get(q["key"])
        if o:
            if o.get("unit"):
                q["unit"], q["needs_review"] = o["unit"], False
                guess = q.get("subtopic_guess") or ""
                q["subtopic"] = (o.get("subtopic")
                                 or (guess if guess.startswith(o["unit"] + ".") else None)
                                 or next(iter(UNITS[o["unit"]]["subtopics"])))
            if o.get("exclude"):
                q["excluded"] = True
        out.append(q)
    return out


def practice_pool(questions: list, allow_memory: bool = True) -> list:
    return [q for q in questions if q["status"] == "ok" and q.get("unit") and not q.get("needs_review")
            and not q.get("excluded") and (allow_memory or q["origin"] != "memory")]
