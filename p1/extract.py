"""Read question papers and answer keys into structured, English-only questions.

Handles three layouts seen in UGC NET material:
  1. NTA master question papers ("Question Number : 1 Question Id : ..."), where the
     question and options are often images (OCR is used) and each question appears
     twice, in English and in Hindi. Only the English copy is kept.
  2. Coaching / memory-based papers in plain text ("Q5. ...", "(a) ...", "Ans.(b)").
  3. Answer keys: NTA keys (Question ID -> option ID or option number) and coaching
     keys (question number -> option number, "Dropped").

Nothing is invented: a question without four readable options or without readable
English text is reported as skipped, never filled in.
"""
from __future__ import annotations

import io
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field

PARSER_VERSION = 10
OCR_SCALE = 2.0

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
EN_STOP = set("""the of and to in is are was were be by for on as at or if that this these those which what
who whom whose when where why how with from into than then there their they them it its not no
all any some each both following given below above correct statement statements choose answer
options option between among about after before during under over only also can could would
should will shall may might must has have had been being does did do most more less least true
false following has type types an his her our your we you one two three four first second
match list arrange order sequence based passage author according following""".split())

OPT_ID_LINE = re.compile(r"^\s*(\d{6,})\s*[\.,:]?\s*([1-4])\s*$")
OPT_PLACEHOLDER = re.compile(r"^\s*([1-4])\s*[\.,:]\s*([1-4])\s*$")
OPT_NUM_LINE = re.compile(r"^\s*([1-4])\s*[\.\),:]\s*(.*)$")

NTA_QHEAD = re.compile(r"Question\s*Number\s*[:;]?\s*(\d{1,3})\s*Question\s*I[dD]\s*[:;]?\s*(\d{6,})")
NTA_GHEAD = re.compile(r"Question\s*I[dD]\s*[:;]?\s*(\d{6,})\s*Question\s*Type\s*[:;]?\s*COMPREHENSION", re.I)
NTA_QRANGE = re.compile(r"Question\s*Numbers?\s*[:;]?\s*\(?\s*(\d{1,3})\s*to\s*(\d{1,3})", re.I)
NTA_SECTION_NUM = re.compile(r"(?<![-\w])(?<!Sub-)(?<!Sub\s)Section\s*Number\s*[:;]?\s*(\d+)", re.I)
NTA_META = re.compile(
    r"Question\s*Type|Option\s*Shuffling|Correct\s*Marks|Wrong\s*Marks|Display\s*Question|Question\s*Mandatory|"
    r"Single\s*Line\s*Question|Option\s*Orientation|Number\s*:\s*Yes|Question\s*Label|Sub\s*Question\s*Shuffling|"
    r"Group\s*Comprehension|Question\s*Pattern\s*Type|Section\s*Id|Sub-?\s*Section|Section\s*Number|"
    r"Section\s*type|Mandatory\s*or\s*Optional|Number\s*of\s*Questions|Section\s*Marks|Maximum\s*Instruction|"
    r"Question\s*Shuffling|Is\s*Section\s*Default|Group\s*Number|Group\s*Id|Group\s*Maximum|Group\s*Minimum|"
    r"Show\s*Attended|Edit\s*Attended|Break\s*time|Group\s*Marks|Question\s*Paper\s*Name|Subject\s*Name|"
    r"Creation\s*Date|^\s*Duration\s*:|Total\s*Marks|Display\s*Marks|National\s*Testing\s*Agency|"
    r"Question\s*Numbers?\s*[:;]|^\s*:\s*Yes", re.I)

# coaching / plain-text layout
G_QSTART = re.compile(r"^\s*(?:(?:Q\s*\.\s*|Ques(?:tion)?\s*(?:No\.?\s*)?)(\d{1,3})\s*[\.\):]?|Q(\d{1,3})\s*[\.\):]|(\d{1,3})\s*[\.\)])\s*(.*)$", re.I)
G_ANSWER = re.compile(r"^\s*(?:correct\s+)?(?:ans(?:wer)?|key|correct\s+option)\s*[:\-\.]?\s*\(?\s*([1-4A-Da-d])\s*\)?\s*\.?\s*$", re.I)
G_SOL = re.compile(r"^\s*(sol(?:ution)?|explanation|exp)\s*[\.:\-]", re.I)
G_OPT = {
    "paren": re.compile(r"^\s*\(\s*([1-4A-Da-d])\s*\)\s*(.+)$"),
    "dot": re.compile(r"^\s*([1-4])\s*[\.\)]\s+(.+)$"),
    "letter": re.compile(r"^\s*([A-Da-d])\s*[\.\)]\s+(.+)$"),
}
G_INLINE_OPTS = re.compile(r"\(\s*([1-4a-d])\s*\)\s*(.+?)(?=\s*\(\s*[1-4a-d]\s*\)|$)")
LETTER_INDEX = {"1": 0, "2": 1, "3": 2, "4": 3, "a": 0, "b": 1, "c": 2, "d": 3}


@dataclass
class RawQuestion:
    qno: int
    text: str
    options: list = field(default_factory=list)
    qid: str | None = None
    option_ids: list = field(default_factory=list)
    inline_answer: int | None = None      # answer printed in the paper itself
    explanation: str | None = None
    group_text: str | None = None         # passage / data set shared by several questions
    group_id: str | None = None
    pages: list = field(default_factory=list)
    regions: list = field(default_factory=list)        # [[page, y0, y1], ...] of the English question on the page
    group_regions: list = field(default_factory=list)  # same, for the shared passage / data set
    from_ocr: bool = False
    english_score: float = 0.0

    def to_dict(self):
        return asdict(self)


# ------------------------------------------------------------------ helpers
def english_score(text: str) -> float:
    """Share of word tokens that are common English function/exam words."""
    toks = re.findall(r"[A-Za-z]+", text)
    if not toks:
        return 0.0
    hits = sum(1 for t in toks if t.lower() in EN_STOP)
    return hits / len(toks)


def english_quality(text: str) -> float:
    """Higher = more like real English. OCR'd Hindi produces few function words and odd casing."""
    toks = re.findall(r"[A-Za-z]+", text)
    if not toks:
        return 0.0
    weird = sum(1 for t in toks if re.search(r"[a-z][A-Z]", t)) / len(toks)
    return english_score(text) - 0.5 * weird


def is_english(text: str, min_score: float = 0.12) -> bool:
    if DEVANAGARI.search(text) and len(DEVANAGARI.findall(text)) > 0.2 * len(text):
        return False
    toks = re.findall(r"[A-Za-z]+", text)
    if len(toks) < 4:          # very short stems (e.g. pure numbers) can't be judged; accept if ASCII
        return all(ord(c) < 128 or c in "°–—’‘“”…×÷√" for c in text)
    return english_score(text) >= min_score


def drop_devanagari(line: str) -> str:
    if not DEVANAGARI.search(line):
        return line
    latin = DEVANAGARI.sub(" ", line)
    latin = re.sub(r"\s{2,}", " ", latin).strip(" /|-")
    letters = len(re.findall(r"[A-Za-z0-9]", latin))
    return latin if letters >= 6 and letters >= 0.5 * len(line.replace(" ", "")) else ""


def tidy(s: str) -> str:
    return re.sub(r"[ \t]{2,}", " ", s).strip()


# ------------------------------------------------------------------ reading
def _ocr_image(img) -> list:
    """OCR a page image; return [[text, y0, y1], ...] with y as a fraction of page height."""
    import os

    import pytesseract

    os.environ["OMP_THREAD_LIMIT"] = "1"   # one thread per Tesseract process: no CPU over-subscription

    d = pytesseract.image_to_data(img, lang="eng", config="--psm 4", output_type=pytesseract.Output.DICT)
    lines = {}
    for i, w in enumerate(d["text"]):
        w = (w or "").strip()
        if not w:
            continue
        key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        L = lines.setdefault(key, {"w": [], "y0": 10**9, "y1": 0})
        L["w"].append(w)
        L["y0"] = min(L["y0"], d["top"][i])
        L["y1"] = max(L["y1"], d["top"][i] + d["height"][i])
    H = float(img.height)
    return [[" ".join(L["w"]), L["y0"] / H, L["y1"] / H] for L in sorted(lines.values(), key=lambda L: L["y0"])]


def _find_tesseract():
    """Point pytesseract at Tesseract if it is installed but not on PATH (common on Windows)."""
    import os
    import shutil

    import pytesseract

    if shutil.which("tesseract"):
        return
    for c in (os.environ.get("TESSERACT_CMD", ""), r"C:\Program Files\Tesseract-OCR\tesseract.exe",
              r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
              os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
              "/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract"):
        if c and os.path.exists(c):
            pytesseract.pytesseract.tesseract_cmd = c
            return


def ocr_available() -> bool:
    try:
        import pytesseract

        _find_tesseract()
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _total_ram_gb():
    """Installed memory in GB (Windows, Linux, macOS), or None if it can't be read."""
    import os
    import sys

    try:
        if sys.platform == "win32":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MS()
            m.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.ullTotalPhys / 1024 ** 3
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024 ** 3
    except Exception:
        return None


def _ocr_workers() -> int:
    """How many pages to OCR at once: 1 on small machines (< 6 GB RAM) or with --light, else at most 2."""
    import os

    if os.environ.get("P1_OCR_WORKERS"):
        return max(1, int(os.environ["P1_OCR_WORKERS"]))
    ram = _total_ram_gb()
    if ram is not None and ram < 6:
        return 1
    return max(1, min(2, (os.cpu_count() or 2) // 2))


def _ocr_page_safely(doc, i: int) -> tuple:
    """OCR one page; on a memory error retry once at lower resolution. Returns (lines, error)."""
    import gc

    for scale in (OCR_SCALE, 1.6):
        try:
            img = doc[i].render(scale=scale).to_pil()
            try:
                return _ocr_image(img), None
            finally:
                del img
        except MemoryError:
            gc.collect()
    return [], f"page {i + 1}: not enough memory to read it"


def _past_paper1(text: str) -> bool:
    """True once a page reaches the subject paper (Section 2) or question 51+."""
    for line in text.splitlines():
        if not re.search(r"sub", line, re.I):
            m = NTA_SECTION_NUM.search(line)
            if m and int(m.group(1)) >= 2:
                return True
    return any(int(n) > 50 for n, _ in NTA_QHEAD.findall(text))


def _hindi_repeat_pages(pdf, layer: list) -> set:
    """Pages (0-based) that only repeat questions already seen earlier (NTA's Hindi copy).

    Judged from the PDF's text layer: every Question ID on the page appeared on an earlier page and
    nothing (no text, no picture) sits above the page's first question header, so the page holds no
    leftover part of an English question."""
    seen, skip = set(), set()
    for i, page in enumerate(pdf.pages):
        t = layer[i]
        ids = [qid for _, qid in NTA_QHEAD.findall(t)] + NTA_GHEAD.findall(t)
        if ids and all(x in seen for x in ids):
            try:
                lines = page.extract_text_lines()
                head_top = min(l["top"] for l in lines if NTA_QHEAD.search(l["text"]) or NTA_GHEAD.search(l["text"]))
                above = any(l["top"] < head_top - 1 and l["text"].strip() for l in lines) or \
                    any(img["top"] < head_top - 1 for img in page.images)
                if not above:
                    skip.add(i)
            except Exception:
                pass
        seen.update(ids)
    return skip


def read_pdf(path: str, progress=None, cache_dir=None) -> dict:
    """Read a PDF into pages of positioned lines, OCR-ing picture pages.

    Light on the computer: at most 2 OCR processes, 2 pages in memory at a time, pages after
    Paper 1 are not read, NTA's Hindi repeat pages are skipped where the text layer shows them,
    and each OCR'd page is saved to cache_dir so an interrupted scan resumes where it stopped.

    progress(fraction, message) is called as pages finish.
    Returns {'pages': [{'lines': [[text, y0, y1], ...], 'ocr': bool}], 'kind', 'qno_qid', 'error'}.
    """
    import hashlib
    import json
    from pathlib import Path

    import pdfplumber

    with pdfplumber.open(path) as pdf:
        layer = [(p.extract_text() or "") for p in pdf.pages]
        has_img = [len(p.images) > 0 for p in pdf.pages]
        nta_layer = sum(len(NTA_QHEAD.findall(t)) for t in layer)
        skip = _hindi_repeat_pages(pdf, layer) if nta_layer >= 3 else set()
    n = len(layer)
    total = sum(len(t) for t in layer)
    scanned = total < 150 * max(n, 1)

    qno_qid = {}
    for t in layer:                      # the text layer is more reliable than OCR digits
        for qno, qid in NTA_QHEAD.findall(t):
            if int(qno) <= 50:
                qno_qid.setdefault(int(qno), qid)

    # last page we need: the page where Paper 2 starts (it may still hold the end of Q50)
    last = n - 1
    for i, t in enumerate(layer):
        if _past_paper1(t):
            last = i
            break

    if nta_layer >= 3 or scanned:
        to_ocr = [i for i in range(last + 1) if (has_img[i] or len(layer[i].strip()) < 40) and i not in skip]
        kind = "nta" if nta_layer >= 3 else "scanned"
    else:
        to_ocr, kind = [], "text"

    pages = [{"lines": [[l, None, None] for l in t.splitlines()], "ocr": False} for t in layer]
    for i in range(last + 1, n):
        pages[i] = {"lines": [], "ocr": False}            # Paper 2 pages: not needed
    for i in skip:
        pages[i] = {"lines": [], "ocr": False}            # Hindi repeat pages
    if not to_ocr:
        return {"pages": pages, "kind": kind, "qno_qid": qno_qid, "error": None}
    if not ocr_available():
        return {"pages": pages, "kind": kind, "qno_qid": qno_qid,
                "error": "This PDF's questions are images, so it needs OCR, but Tesseract is not installed."}

    import pypdfium2 as pdfium

    cdir = Path(cache_dir) if cache_dir else None
    if cdir:
        cdir.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha1(Path(path).read_bytes()).hexdigest()[:16]

    def cached(i):
        return cdir / f"{h}_p{i}_s{OCR_SCALE}.json" if cdir else None

    doc = pdfium.PdfDocument(path)
    workers = _ocr_workers()
    done, stop_after, warnings = 0, None, []
    try:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for start in range(0, len(to_ocr), workers):
                chunk = [i for i in to_ocr[start:start + workers] if stop_after is None or i <= stop_after]
                if not chunk:
                    break
                futs = {}
                for i in chunk:
                    c = cached(i)
                    if c and c.exists():
                        pages[i] = {"lines": json.loads(c.read_text(encoding="utf-8")), "ocr": True}
                        continue
                    try:
                        img = doc[i].render(scale=OCR_SCALE).to_pil()
                        futs[ex.submit(_ocr_image, img)] = i
                        del img
                    except MemoryError:
                        futs[ex.submit(_ocr_page_safely, doc, i)] = ("safe", i)
                for f, tag in futs.items():
                    i = tag[1] if isinstance(tag, tuple) else tag
                    try:
                        res = f.result()
                        lines, err = res if isinstance(tag, tuple) else (res, None)
                    except MemoryError:
                        import gc

                        gc.collect()
                        lines, err = _ocr_page_safely(doc, i)      # retry alone, smaller
                    if err:
                        warnings.append(err)
                        continue
                    pages[i] = {"lines": lines, "ocr": True}
                    if cached(i):
                        cached(i).write_text(json.dumps(lines), encoding="utf-8")
                for i in chunk:
                    done += 1
                    if stop_after is None and _past_paper1("\n".join(l[0] for l in pages[i]["lines"])):
                        stop_after = i                     # scanned paper: Paper 2 starts here
                    if progress:
                        progress(done / len(to_ocr), f"page {i + 1} of {last + 1}")
    finally:
        doc.close()
    if stop_after is not None:
        for i in range(stop_after + 1, n):
            pages[i] = {"lines": [], "ocr": False}

    if kind == "scanned" and any(NTA_QHEAD.search(l[0]) for p in pages for l in p["lines"]):
        kind = "nta"
    return {"pages": pages, "kind": kind, "qno_qid": qno_qid,
            "error": ("; ".join(warnings) + ". Questions on these pages are skipped; run the scan with --light "
                      "and close other programs to read them.") if warnings else None}


def page_lines(pages: list) -> list:
    """Flatten to [(page_no, text, y0, y1)], dropping Devanagari (English only)."""
    out = []
    for pno, page in enumerate(pages, 1):
        for text, y0, y1 in page["lines"]:
            text = tidy(drop_devanagari(text))
            if text:
                out.append((pno, text, y0, y1))
    return out


# ------------------------------------------------------------------ NTA layout
def _split_options(body: list):
    """body: [(pno, text, y0, y1)]. Find the LAST run of lines numbered 1., 2., 3., 4. in order.
    Returns (stem_lines, options)."""
    idx = [(k, int(m.group(1)), m.group(2)) for k, row in enumerate(body) if (m := OPT_NUM_LINE.match(row[1]))]
    for start in range(len(idx) - 1, -1, -1):
        if idx[start][1] != 4:
            continue
        chain, want = [idx[start]], 3
        for j in range(start - 1, -1, -1):
            if idx[j][1] == want:
                chain.insert(0, idx[j])
                want -= 1
                if want == 0:
                    break
        if len(chain) == 4:
            stem = [row[1] for row in body[:chain[0][0]]]
            opts = []
            for c, (k, num, first) in enumerate(chain):
                end = chain[c + 1][0] if c < 3 else len(body)
                extra = [row[1] for row in body[k + 1:end]]
                opts.append(tidy(" ".join([first] + extra)))
            if all(o.strip() for o in opts):
                return stem, opts
    # no clean option run: stem is everything up to the first line that starts like an option
    first_opt = next((k for k, row in enumerate(body) if OPT_NUM_LINE.match(row[1])), len(body))
    return [row[1] for row in body[:first_opt]], []


def _regions(rows: list) -> list:
    """Bounding y-range per page for positioned rows [(pno, text, y0, y1)]."""
    reg = {}
    for pno, _, y0, y1 in rows:
        if y0 is None:
            continue
        r = reg.setdefault(pno, [pno, y0, y1])
        r[1], r[2] = min(r[1], y0), max(r[2], y1)
    return [reg[k] for k in sorted(reg)]


def parse_nta(lines: list, from_ocr: set, qno_qid: dict) -> tuple[list[RawQuestion], list[dict]]:
    """Parse NTA master-paper text (lines = [(pno, text, y0, y1)]).

    Each question appears in English and in Hindi; the English copy is chosen by its
    question text. Returns (questions, issues)."""
    blocks = []
    cur = None
    stop = False
    for row in lines:
        pno, line = row[0], row[1]
        m_sec = None if re.search(r"sub", line, re.I) else NTA_SECTION_NUM.search(line)
        if m_sec and int(m_sec.group(1)) >= 2:
            stop = True            # Section 2 is the subject paper (Paper 2): not needed
        if stop:
            continue
        m_g = NTA_GHEAD.search(line)
        m_q = NTA_QHEAD.search(line)
        if m_g and not m_q:
            cur = {"kind": "g", "qid": m_g.group(1), "rng": None, "rows": [row], "open": True}
            blocks.append(cur)
            continue
        if m_q:
            cur = {"kind": "q", "qno": int(m_q.group(1)), "qid": m_q.group(2), "rows": [row], "body": [],
                   "ids": [], "open": True}
            blocks.append(cur)
            continue
        if cur is None:
            continue
        if cur["kind"] == "g":
            m_r = NTA_QRANGE.search(line)
            if m_r:
                cur["rng"] = (int(m_r.group(1)), int(m_r.group(2)))
                continue
            if re.match(r"^\s*Sub\s*questions", line, re.I):
                cur["open"] = False
                continue
            if cur["open"] and not NTA_META.search(line):
                cur["rows"].append(row)
            continue
        # question block
        if re.match(r"^\s*Options?\s*[:;]?\s*$", line, re.I):
            cur["open"] = False          # what follows is option IDs, not visible content
            continue
        if not cur["open"]:
            m_id = OPT_ID_LINE.match(line)
            if m_id:
                cur["ids"].append(m_id.group(1))
            continue
        if NTA_META.search(line):
            cur["rows"].append(row)      # keep for the crop region (header lines)
            continue
        cur["rows"].append(row)
        cur["body"].append(row)

    groups = {}
    for b in blocks:
        if b["kind"] != "g":
            continue
        text = "\n".join(r[1] for r in b["rows"][1:] if not NTA_META.search(r[1])).strip()
        prev = groups.get(b["qid"])
        if prev is None or english_quality(text) > english_quality(prev["text"]) + 0.15:
            body_rows = [r for r in b["rows"][1:] if not NTA_META.search(r[1])]
            groups[b["qid"]] = {"text": text, "rng": b["rng"] or (prev or {}).get("rng"),
                                "regions": _regions(body_rows or b["rows"])}
        elif prev and not prev["rng"]:
            prev["rng"] = b["rng"]

    candidates: dict = {}
    for b in blocks:
        if b["kind"] != "q" or b["qno"] > 50:
            continue
        stem, opts = _split_options(b["body"])
        qid = qno_qid.get(b["qno"]) or b["qid"]
        q = RawQuestion(qno=b["qno"], qid=qid, text=tidy("\n".join(stem)), options=opts,
                        option_ids=b["ids"] if len(b["ids"]) == 4 else [],
                        pages=sorted({r[0] for r in b["rows"]}), regions=_regions(b["body"] or b["rows"]),
                        from_ocr=bool({r[0] for r in b["rows"]} & from_ocr))
        q.english_score = english_quality(q.text)
        candidates.setdefault(qid, []).append(q)

    for g_id, g in groups.items():
        if not g["rng"]:
            continue
        lo, hi = g["rng"]
        for qs in candidates.values():
            for q in qs:
                if lo <= q.qno <= hi:
                    q.group_text, q.group_id, q.group_regions = g["text"], g_id, g["regions"]

    out, issues = [], []
    for qid, qs in candidates.items():
        # NTA prints the English copy first; give it a small tie-break bonus over the Hindi copy
        best = max(enumerate(qs), key=lambda kq: kq[1].english_score + (0.15 if kq[0] == 0 else 0))[1]
        # option IDs are identical in both language copies; take them from any copy
        if not best.option_ids:
            best.option_ids = next((q.option_ids for q in qs if q.option_ids), [])
        if not is_english(best.text, min_score=0.08) or len(re.findall(r"[A-Za-z]{3,}", best.text)) < 3:
            issues.append({"qno": best.qno, "qid": qid, "reason": "No readable English question text"})
            continue
        out.append(best)
    out.sort(key=lambda q: q.qno)
    return out, issues


# ------------------------------------------------------------------ generic layout
def _option_style(lines: list[str]) -> str:
    paren = sum(1 for l in lines if re.match(r"^\s*\(\s*[1-4A-Da-d]\s*\)", l))
    dot = sum(1 for l in lines if re.match(r"^\s*[1-4][\.\)]\s", l))
    if paren >= 8:
        return "paren"
    return "dot" if dot >= 8 else "letter"


def parse_generic(lines: list[tuple[int, str]]) -> tuple[list[RawQuestion], list[dict]]:
    style = _option_style([r[1] for r in lines])
    opt_re = G_OPT[style]
    qs: list[RawQuestion] = []
    cur: RawQuestion | None = None
    expected = None
    mode = "stem"          # stem | options | after_answer | explanation
    carry: list[str] = []  # text after an answer that is not a solution: preamble for the next question(s)
    shared: str | None = None

    def close():
        nonlocal cur
        if cur:
            qs.append(cur)
        cur = None

    for pno, line, *_ in lines:
        m_q = G_QSTART.match(line)
        if m_q:
            n = int(m_q.group(1) or m_q.group(2) or m_q.group(3))
            rest = m_q.group(4).strip()
            prefixed = m_q.group(3) is None
            option_like = (style == "dot" and not prefixed and cur is not None and mode in ("stem", "options")
                           and len(cur.options) < 4 and n == len(cur.options) + 1)
            jump_ok = prefixed and expected is not None and expected < n <= expected + 3 and mode != "stem"
            if not option_like and (expected is None or n == expected or jump_ok):
                close()
                if carry:
                    shared = "\n".join(carry)
                    carry = []
                cur = RawQuestion(qno=n, text=rest, pages=[pno])
                if shared and mode != "stem":
                    cur.group_text = shared
                expected, mode = n + 1, "stem"
                continue
        if cur is None:
            continue
        if pno not in cur.pages:
            cur.pages.append(pno)

        m_a = G_ANSWER.match(line)
        if m_a:
            cur.inline_answer = LETTER_INDEX.get(m_a.group(1).lower())
            mode = "after_answer"
            shared = None
            continue
        if mode in ("after_answer", "explanation"):
            if G_SOL.match(line) or mode == "explanation":
                cur.explanation = ((cur.explanation or "") + "\n" + G_SOL.sub("", line)).strip()
                mode = "explanation"
            else:
                carry.append(line)
            continue

        inline = G_INLINE_OPTS.findall(line) if style == "paren" else []
        if len(inline) >= 2 and len(cur.options) < 4:
            cur.options.extend(tidy(t) for _, t in inline)
            mode = "options"
            continue
        m_o = opt_re.match(line)
        if m_o and len(cur.options) < 4:
            cur.options.append(tidy(m_o.groups()[-1]))
            mode = "options"
            continue
        if mode == "options" and cur.options:
            cur.options[-1] = tidy(cur.options[-1] + " " + line)
        else:
            cur.text = (cur.text + "\n" + line).strip()
    close()

    out, issues = [], []
    for q in qs:
        if q.qno > 50:
            continue
        q.english_score = english_score(q.text + " " + " ".join(q.options))
        if not is_english(q.text + " " + " ".join(q.options)):
            issues.append({"qno": q.qno, "reason": "No readable English version"})
            continue
        out.append(q)
    return out, issues


# ------------------------------------------------------------------ answer keys
def read_key_text(path: str) -> str:
    if path.lower().endswith(".pdf"):
        doc = read_pdf(path)
        return "\n".join(l[0] for p in doc["pages"] for l in p["lines"])
    with open(path, "rb") as f:
        return f.read().decode("utf-8", errors="ignore")


def parse_key(text: str) -> dict:
    """Return {'tokens': [...long-number/answer tokens...], 'by_qno': {qno: idx|'DROP'} or None, 'official': bool}."""
    official = bool(re.search(r"national\s+testing\s+agency|\bNTA\b", text, re.I)) and \
        len(re.findall(r"\d{8,}", text)) >= 10
    tokens = re.findall(r"\d{6,}|\b(?:Drop(?:ped)?|Bonus|D)\b|\b[1-4]\b", text, re.I)

    # question-number keys: use lines made only of numbers / 'Dropped' tokens
    seq = []
    for line in text.splitlines():
        s = line.strip()
        if not s or not re.fullmatch(r"(?:(?:\d{1,3}|Drop(?:ped)?|Bonus|[A-Da-d])[\s\.\)\-:,]*)+", s, re.I):
            continue
        seq.extend(re.findall(r"\d{1,3}|Drop(?:ped)?|Bonus|[A-Da-d]\b", s, re.I))
    by_qno = _pair_qno_tokens(seq)
    return {"tokens": tokens, "by_qno": by_qno, "official": official, "text": text}


def _pair_qno_tokens(seq: list[str]) -> dict | None:
    """Pair (qno, answer) tokens and accept only if they form a clean 1..N key."""
    for offset in (0, 1):
        pairs, ok = {}, True
        s = seq[offset:]
        for i in range(0, len(s) - 1, 2):
            qno, ans = s[i], s[i + 1]
            if not qno.isdigit() or not (1 <= int(qno) <= 150):
                ok = False
                break
            a = ans.lower()
            if a.startswith("drop") or a == "bonus":
                val = "DROP"
            elif a in LETTER_INDEX:
                val = LETTER_INDEX[a]
            else:
                ok = False
                break
            if int(qno) in pairs:
                ok = False
                break
            pairs[int(qno)] = val
        if ok and len(pairs) >= 10:
            nums = sorted(pairs)
            if nums == list(range(nums[0], nums[0] + len(nums))):   # contiguous: no misread rows
                return pairs
    return None


ANS_TOKEN = re.compile(r"\d{6,}|\b(?:Drop(?:ped)?|Bonus)\b|\bD\b|\b[1-4]\b", re.I)


def answers_from_qid_tokens(tokens_or_text, questions: dict) -> dict:
    """Read an NTA-style key against known Question IDs.

    questions: {qid: question dict with 'option_ids'}. Returns {qid: [option index | 'DROP', ...]}.
    The answer must be the token right after the Question ID. A second answer is accepted only if it
    is joined to the first by a comma, '/', '&' or 'or' (NTA's way of listing more than one correct
    option), so row serial numbers are never mistaken for answers.
    """
    text = tokens_or_text if isinstance(tokens_or_text, str) else " ".join(tokens_or_text)
    toks = [(m.group(0), m.start(), m.end()) for m in ANS_TOKEN.finditer(text)]

    def conv(tok, q):
        if tok in (q.get("option_ids") or []):
            return q["option_ids"].index(tok)
        if re.fullmatch(r"[1-4]", tok):
            return int(tok) - 1
        if tok.lower().startswith("d") or tok.lower() == "bonus":
            return "DROP"
        return None          # an option ID this paper doesn't have

    out = {}
    for i, (tok, _, end) in enumerate(toks):
        if tok not in questions or i + 1 >= len(toks):
            continue
        q = questions[tok]
        nxt, s1, e1 = toks[i + 1]
        if nxt in questions:
            continue
        first = conv(nxt, q)
        ans = [first] if first is not None else []
        j, prev_end = i + 2, e1
        while j < len(toks):
            t2, s2, e2 = toks[j]
            sep = text[prev_end:s2]
            if t2 in questions or not re.fullmatch(r"\s*(,|/|&|or|and)\s*", sep, re.I):
                break
            v = conv(t2, q)
            if v is not None:
                ans.append(v)
            prev_end, j = e2, j + 1
        out[tok] = ans
    return out
