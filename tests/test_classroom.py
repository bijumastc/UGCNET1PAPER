"""Tests for generated questions, the Google Sheet store (in-memory stand-in) and encouragement."""
import re
import sys
import time
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fake_gspread import FakeClient  # noqa: E402
from p1 import motivate as M  # noqa: E402
from p1.generators import GEN, from_key, make  # noqa: E402
from p1.progress import Progress  # noqa: E402
from p1.solvers import series_rule  # noqa: E402
from p1.store import SheetStore  # noqa: E402


def test_every_generator_makes_sound_questions():
    for gid, g in GEN.items():
        for lv in g["levels"]:
            for seed in range(60):
                q = make(gid, lv, seed)
                assert len(q["options"]) == 4 and len(set(q["options"])) == 4, (gid, lv, seed)
                assert 0 <= q["answer"] < 4 and q["steps"], (gid, lv, seed)
                assert from_key(q["key"])["text"] == q["text"]


def test_series_answers_are_unique():
    for seed in range(100):
        q = make("num_series", 2, seed)
        nums = [x.strip() for x in q["text"].split("\n")[1].split(",")]
        for i, opt in enumerate(q["options"]):
            fits = series_rule([F(opt) if x == "?" else F(x) for x in nums]) is not None
            assert fits == (i == q["answer"])


def test_sheet_store_round_trip():
    st = SheetStore({}, "url", client=FakeClient())
    st.save_student({"student_id": "S001", "name": "Anu", "pin": "1234", "active": 1})
    st.save_student({"student_id": "S002", "name": "Biju", "pin": "1111", "active": 1})
    p = Progress(st, "S001", "Anu")
    q = {"key": "k1", "unit": "U5", "subtopic": "U5.1", "pattern": "numerical", "level": 1}
    for i in range(5):
        p.record(q, 1, True, 0, 30, "practice")
    assert len(Progress(st, "S001").attempts()) == 5          # visible before Google confirms
    st.flush()
    st.cache.clear()
    assert len(st.attempts("S001")) == 5 and len(st.students()) == 2


def test_encouragement():
    now = time.time()
    att = [{"ts": now - d * 86400, "correct": 1, "help": 0, "mode": "practice"} for d in (0, 1, 2) for _ in range(5)]
    assert M.day_streak(att) == 3 and M.today_count(att) == 5
    assert "3 in a row" in M.feedback(True, 0, 3)
    assert M.feedback(False, 0, 0)
