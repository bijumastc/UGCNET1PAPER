"""Where the class's data lives.

SheetStore  - a Google Sheet (online use). Your sheet gets these tabs:
              Students (the roster), Attempts (every answer, with the question and both answers),
              Tests (every diagnostic/mock/speed round/daily challenge), Activity (logins, pages, time),
              AI_Chats (every AI tutor question and reply), AI_Questions (AI-written questions and their
              review status), Progress (one summary row per student), Unit_Scores (mastery per unit),
              Corrections, Reports, Settings.
              New columns are only ever added at the end, and an older sheet is upgraded automatically.
              Scores are written in small batches every few seconds, so the app stays fast.
LocalStore  - a file on your computer (.p1_trainer/class.db) when no Google Sheet is set up.

Both offer the same methods, so the rest of the app doesn't care which one is in use.
"""
from __future__ import annotations

import json
import queue
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))      # India Standard Time (no daylight saving)

UNIT_COLS = [f"U{i}" for i in range(1, 11)]
TABS = {
    "Students": ["student_id", "name", "pin", "email", "batch", "active", "joined", "phone", "notes"],
    "Attempts": ["time", "student_id", "name", "question_key", "source", "session", "qno", "unit", "topic",
                 "format", "level", "chosen", "correct", "help_used", "seconds", "mode",
                 "question", "your_answer", "correct_answer", "points"],
    "Tests": ["time", "student_id", "name", "kind", "questions", "correct", "marks", "out_of", "percent", "minutes",
              "points", "by_unit"],
    "Activity": ["time", "student_id", "name", "event", "detail"],
    "AI_Questions": ["id", "created", "status", "unit", "subtopic", "pattern", "level", "question", "option1",
                     "option2", "option3", "option4", "answer", "explanation", "hint", "model", "note"],
    "AI_Chats": ["time", "student_id", "unit", "topic", "kind", "question", "reply_chars", "reply", "model"],
    "Progress": ["student_id", "name", "batch", "status", "last_active", "logins", "days_active", "minutes_total",
                 "minutes_7_days", "practice_sessions", "questions_total", "questions_7_days", "correct_total",
                 "accuracy", "tests_taken", "last_test_pct", "best_test_pct", "projected_score", "day_streak",
                 "points", "rank", "weakest_unit", "top_deficits", "help_share", "ai_tutor_questions", "updated"],
    "Unit_Scores": ["student_id", "name"] + UNIT_COLS + ["updated"],
    "Corrections": ["question_key", "unit", "subtopic", "exclude", "by", "time"],
    "Reports": ["time", "student_id", "question_key", "message", "status"],
    "Settings": ["key", "value"],
}
SUMMARY_TABS = ("Progress", "Unit_Scores")      # rewritten by the app; safe to reshape

ATTEMPT_FIELDS = TABS["Attempts"]


def now_iso() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def to_ts(s) -> float:
    if isinstance(s, (int, float)):
        return float(s)
    try:
        return datetime.strptime(str(s), "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST).timestamp()
    except Exception:
        return 0.0


def _norm_attempt(r: dict) -> dict:
    """Make sheet/DB rows uniform: numbers as numbers, plus a float 'ts'."""
    def num(x, f=float, d=0):
        try:
            return f(x) if x not in (None, "") else d
        except Exception:
            return d
    return {**r, "ts": to_ts(r.get("time")), "correct": num(r.get("correct"), int), "help": num(r.get("help_used"), int),
            "seconds": num(r.get("seconds")), "level": num(r.get("level"), int, 1),
            "points": num(r.get("points"), int),
            "chosen": None if r.get("chosen") in (None, "") else num(r.get("chosen"), int),
            "qkey": r.get("question_key"), "subtopic": r.get("topic"), "pattern": r.get("format")}


# ====================================================================== local
class LocalStore:
    kind = "local"

    def __init__(self, folder):
        p = Path(folder).resolve() / ".p1_trainer"
        p.mkdir(parents=True, exist_ok=True)
        self.path = p / "class.db"
        self.lock = threading.Lock()
        self.db = sqlite3.connect(str(self.path), check_same_thread=False)
        for tab, cols in TABS.items():
            have = [r[1] for r in self.db.execute(f'PRAGMA table_info("{tab}")').fetchall()]
            if have and tab in SUMMARY_TABS and have != cols:
                self.db.execute(f'DROP TABLE "{tab}"')
                have = []
            if not have:
                self.db.execute(f'CREATE TABLE "{tab}" ({", ".join(f"{c} TEXT" for c in cols)})')
            for c in cols:
                if c not in have and have:                       # upgrade an older file: add new columns
                    self.db.execute(f'ALTER TABLE "{tab}" ADD COLUMN {c} TEXT')
        self.db.commit()

    def _rows(self, tab, where="", args=()):
        cols = TABS[tab]
        with self.lock:
            cur = self.db.execute(f'SELECT {", ".join(cols)} FROM "{tab}" {where}', args)
            return [dict(zip(cols, r)) for r in cur.fetchall()]

    def _insert(self, tab, rows):
        cols = TABS[tab]
        with self.lock:
            self.db.executemany(f'INSERT INTO "{tab}" ({", ".join(cols)}) VALUES ({",".join("?" * len(cols))})',
                                [[None if r.get(c) is None else str(r.get(c)) for c in cols] for r in rows])
            self.db.commit()

    def _replace(self, tab, keycol, row):
        with self.lock:
            self.db.execute(f'DELETE FROM "{tab}" WHERE {keycol}=?', (str(row[keycol]),))
            self.db.commit()
        self._insert(tab, [row])

    # students
    def students(self):
        return self._rows("Students")

    def save_student(self, row):
        self._replace("Students", "student_id", row)

    # attempts
    def attempts(self, student_id=None):
        rows = self._rows("Attempts", "WHERE student_id=?", (student_id,)) if student_id else self._rows("Attempts")
        return sorted((_norm_attempt(r) for r in rows), key=lambda r: r["ts"])

    def add_attempt(self, row):
        self._insert("Attempts", [row])

    def delete_attempts(self, student_id):
        with self.lock:
            self.db.execute('DELETE FROM "Attempts" WHERE student_id=?', (student_id,))
            self.db.commit()

    # AI questions
    def ai_questions(self):
        return self._rows("AI_Questions")

    def save_ai_question(self, row):
        self._replace("AI_Questions", "id", row)

    # corrections & reports
    def corrections(self):
        out = {}
        for r in self._rows("Corrections"):
            out[r["question_key"]] = {"unit": r["unit"] or None, "subtopic": r["subtopic"] or None,
                                      "exclude": str(r["exclude"]) in ("1", "True", "true")}
        return out

    def save_correction(self, key, unit=None, subtopic=None, exclude=False, by=""):
        self._replace("Corrections", "question_key", {"question_key": key, "unit": unit or "", "subtopic": subtopic or "",
                                                      "exclude": int(bool(exclude)), "by": by, "time": now_iso()})

    def clear_corrections(self):
        with self.lock:
            self.db.execute('DELETE FROM "Corrections"')
            self.db.commit()

    def reports(self):
        return self._rows("Reports")

    def add_report(self, row):
        self._insert("Reports", [row])

    def set_report_status(self, time_, student_id, key, status):
        with self.lock:
            self.db.execute('UPDATE "Reports" SET status=? WHERE time=? AND student_id=? AND question_key=?',
                            (status, time_, student_id, key))
            self.db.commit()

    # AI tutor log
    def ai_log(self, student_id=None):
        return self._rows("AI_Chats", "WHERE student_id=?", (student_id,)) if student_id else self._rows("AI_Chats")

    def add_ai_log(self, row):
        self._insert("AI_Chats", [row])

    # settings
    def get(self, key, default=None):
        r = self._rows("Settings", "WHERE key=?", (key,))
        return r[0]["value"] if r else default

    def set(self, key, value):
        self._replace("Settings", "key", {"key": key, "value": str(value)})

    # generic rows (Tests, Activity) and summaries (Progress, Unit_Scores)
    def rows(self, tab, student_id=None):
        return self._rows(tab, "WHERE student_id=?", (student_id,)) if student_id else self._rows(tab)

    def add_row(self, tab, row):
        self._insert(tab, [row])

    def write_summary(self, tab, rows):
        with self.lock:
            self.db.execute(f'DELETE FROM "{tab}"')
            self.db.commit()
        self._insert(tab, rows)

    def upsert_summary(self, tab, row):
        self._replace(tab, "student_id", row)

    def write_progress(self, rows):
        self.write_summary("Progress", rows)

    def flush(self):
        pass

    def link(self):
        return str(self.path)


# ====================================================================== Google Sheet
class SheetStore:
    """Google Sheet backend. Reads are cached for a short time; writes go through a background
    queue in batches, so answering a question never waits for Google."""
    kind = "sheet"
    READ_TTL = 90          # seconds between re-reading a tab

    def __init__(self, service_account_info: dict, sheet_url: str, client=None):
        if client is None:
            import gspread

            client = gspread.service_account_from_dict(service_account_info)
        self.sh = client.open_by_url(sheet_url)
        self.url = sheet_url
        self.lock = threading.RLock()
        self.ws = {}
        existing = {w.title: w for w in self.sh.worksheets()}
        for tab, cols in TABS.items():
            w = existing.get(tab)
            if w is None:
                w = self.sh.add_worksheet(title=tab, rows=1000, cols=len(cols))
                w.update([cols], "A1")
            else:
                head = w.row_values(1)
                if head != cols and (not head or cols[:len(head)] == head or tab in SUMMARY_TABS):
                    if getattr(w, "col_count", len(cols)) < len(cols):      # make room for new columns
                        w.add_cols(len(cols) - w.col_count)
                    w.update([cols], "A1")                                 # upgrade an older sheet
            self.ws[tab] = w
        self.cache: dict = {}
        self.pending: dict = {t: [] for t in TABS}      # written by us, not yet confirmed by Google
        self.q: queue.Queue = queue.Queue()
        self.errors: list = []
        threading.Thread(target=self._writer, daemon=True).start()

    # ---------------- reading (cached)
    def _rows(self, tab, fresh=False):
        with self.lock:
            hit = self.cache.get(tab)
            if hit and not fresh and time.time() - hit[0] < self.READ_TTL:
                return hit[1] + list(self.pending[tab])
        vals = self.ws[tab].get_all_values()
        cols = vals[0] if vals else TABS[tab]
        rows = [dict(zip(cols, r + [""] * (len(cols) - len(r)))) for r in vals[1:] if any(r)]
        with self.lock:
            self.cache[tab] = (time.time(), rows)
            return rows + list(self.pending[tab])

    # ---------------- writing (background, batched)
    def _writer(self):
        while True:
            try:
                first = self.q.get(timeout=5)
            except queue.Empty:
                continue
            batch = [first]
            t_end = time.time() + 3                       # gather a few seconds of answers into one call
            while time.time() < t_end:
                try:
                    batch.append(self.q.get(timeout=0.5))
                except queue.Empty:
                    pass
            by_tab = {}
            for tab, row in batch:
                by_tab.setdefault(tab, []).append(row)
            for tab, rows in by_tab.items():
                for attempt in range(5):
                    try:
                        self.ws[tab].append_rows([[("" if r.get(c) is None else r.get(c)) for c in TABS[tab]]
                                                  for r in rows], value_input_option="RAW")
                        with self.lock:
                            if tab in self.cache:            # now part of the sheet: move into the cache
                                self.cache[tab][1].extend(rows)
                            for r in rows:
                                if r in self.pending[tab]:
                                    self.pending[tab].remove(r)
                        break
                    except Exception as e:            # quota or network hiccup: wait and retry
                        if attempt == 4:
                            self.errors.append(f"{tab}: {e}")
                        time.sleep(5 * (attempt + 1))

    def flush(self, timeout=20):
        """Wait until everything we wrote is in the Google Sheet."""
        t = time.time() + timeout
        while any(self.pending.values()) and time.time() < t:
            time.sleep(0.3)

    def _append(self, tab, row):
        with self.lock:
            self.pending[tab].append(row)
        self.q.put((tab, row))

    def _upsert(self, tab, keycol, row):
        """Update the row whose keycol matches, or append a new one (immediate, not queued)."""
        with self.lock:
            self._rows(tab, fresh=True)
            rows = self.cache[tab][1]            # edit the cached list itself so reads see the change
            cols = TABS[tab]
            values = [["" if row.get(c) is None else row.get(c) for c in cols]]
            for i, r in enumerate(rows):
                if str(r.get(keycol)) == str(row[keycol]):
                    import gspread.utils as gu

                    end = gu.rowcol_to_a1(i + 2, len(cols))
                    self.ws[tab].update(values, f"A{i + 2}:{end}", value_input_option="RAW")
                    rows[i] = {c: v for c, v in zip(cols, values[0])}
                    return
            self.ws[tab].append_rows(values, value_input_option="RAW")
            rows.append({c: v for c, v in zip(cols, values[0])})

    # ---------------- API (same as LocalStore)
    def students(self):
        return self._rows("Students")

    def save_student(self, row):
        self._upsert("Students", "student_id", row)

    def attempts(self, student_id=None):
        rows = self._rows("Attempts")
        if student_id:
            rows = [r for r in rows if str(r.get("student_id")) == str(student_id)]
        return sorted((_norm_attempt(r) for r in rows), key=lambda r: r["ts"])

    def add_attempt(self, row):
        self._append("Attempts", {c: row.get(c) for c in TABS["Attempts"]})

    def delete_attempts(self, student_id):
        raise NotImplementedError("Delete rows in the Google Sheet itself (filter the Attempts tab by student_id).")

    def ai_questions(self):
        return self._rows("AI_Questions")

    def save_ai_question(self, row):
        self._upsert("AI_Questions", "id", row)

    def corrections(self):
        out = {}
        for r in self._rows("Corrections"):
            out[r["question_key"]] = {"unit": r.get("unit") or None, "subtopic": r.get("subtopic") or None,
                                      "exclude": str(r.get("exclude")) in ("1", "True", "true", "TRUE")}
        return out

    def save_correction(self, key, unit=None, subtopic=None, exclude=False, by=""):
        self._upsert("Corrections", "question_key", {"question_key": key, "unit": unit or "", "subtopic": subtopic or "",
                                                     "exclude": int(bool(exclude)), "by": by, "time": now_iso()})

    def clear_corrections(self):
        self.ws["Corrections"].batch_clear(["A2:Z"])
        self.cache.pop("Corrections", None)

    def reports(self):
        return self._rows("Reports")

    def add_report(self, row):
        self._append("Reports", row)

    def set_report_status(self, time_, student_id, key, status):
        self.flush()
        self._rows("Reports", fresh=True)
        rows = self.cache["Reports"][1]
        for i, r in enumerate(rows):
            if r["time"] == time_ and str(r["student_id"]) == str(student_id) and r["question_key"] == key:
                self.ws["Reports"].update([[status]], f"E{i + 2}")
                r["status"] = status
                return

    def ai_log(self, student_id=None):
        rows = self._rows("AI_Chats")
        return [r for r in rows if str(r.get("student_id")) == str(student_id)] if student_id else rows

    def add_ai_log(self, row):
        self._append("AI_Chats", {c: row.get(c) for c in TABS["AI_Chats"]})

    def get(self, key, default=None):
        for r in self._rows("Settings"):
            if r.get("key") == key:
                return r.get("value")
        return default

    def set(self, key, value):
        self._upsert("Settings", "key", {"key": key, "value": str(value)})

    def rows(self, tab, student_id=None):
        rows = self._rows(tab)
        return [r for r in rows if str(r.get("student_id")) == str(student_id)] if student_id else rows

    def add_row(self, tab, row):
        self._append(tab, {c: row.get(c) for c in TABS[tab]})

    def write_summary(self, tab, rows):
        cols = TABS[tab]
        with self.lock:
            self.ws[tab].batch_clear(["A2:AZ"])
            if rows:
                self.ws[tab].update([["" if r.get(c) is None else r.get(c) for c in cols] for r in rows], "A2",
                                    value_input_option="RAW")
            self.cache[tab] = (time.time(), [{c: r.get(c, "") for c in cols} for r in rows])

    def upsert_summary(self, tab, row):
        self._upsert(tab, "student_id", row)

    def write_progress(self, rows):
        self.write_summary("Progress", rows)

    def link(self):
        return self.url


_FAKE = {}


def service_account_info(secrets: dict) -> dict | None:
    """The Google key from Secrets, in either form:
         [gcp_service_account]  with  key = "value"  lines (TOML), or
         gcp_service_account_json = '''{ ...the downloaded JSON file pasted as it is... }'''"""
    raw = secrets.get("gcp_service_account_json")
    if raw:
        return json.loads(raw) if isinstance(raw, str) else dict(raw)
    if "gcp_service_account" in secrets:
        return dict(secrets["gcp_service_account"])
    return None


def open_store(folder, secrets=None):
    """SheetStore when Google credentials are in Streamlit secrets, else LocalStore."""
    import os

    if os.environ.get("P1_TEST_FAKE_SHEET"):              # automated tests only: an in-memory Google Sheet
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
        from fake_gspread import FakeClient

        if "store" not in _FAKE:
            _FAKE["store"] = SheetStore({}, "https://docs.google.com/fake", client=FakeClient())
        return _FAKE["store"]
    try:
        info = service_account_info(secrets or {})
        if info and secrets.get("sheet_url"):
            return SheetStore(info, secrets["sheet_url"])
    except Exception as e:
        st_error = f"Could not open the Google Sheet ({type(e).__name__}: {e}). Using local storage."
        store = LocalStore(folder)
        store.open_error = st_error
        return store
    return LocalStore(folder)
