"""Tests for points, ranks, time spent, the sheet upgrade, summaries and the daily challenge."""
import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fake_gspread import FakeClient  # noqa: E402
from p1 import generators as G  # noqa: E402
from p1 import motivate as M  # noqa: E402
from p1 import records as R  # noqa: E402
from p1.progress import Progress  # noqa: E402
from p1.store import TABS, LocalStore, SheetStore  # noqa: E402


def test_points_reward_independence_speed_and_combos():
    base = M.points(True, 1, 0, 30, 1)
    assert base == 20                                   # 10 + no-help 5 + speed 5
    assert M.points(True, 1, 2, 30, 1) < base           # help lowers points
    assert M.points(True, 1, 0, 200, 1) == 15           # slow: no speed bonus
    assert M.points(True, 1, 0, 30, 3) == 30 and M.points(True, 1, 0, 30, 5) == 40   # combos
    assert M.points(False, 3, 0, 30, 0) == 2 and M.points(False, 1, 4, 5, 0) == 1
    assert M.rank(0)[0].endswith("Seedling") and M.rank(1300)[0].endswith("Scholar")
    assert M.public_name("Anu Mary Joseph") == "Anu J."


def test_study_blocks_merge_and_split():
    t = 1_000_000.0
    att = [{"ts": t, "seconds": 30}, {"ts": t + 120, "seconds": 60}, {"ts": t + 5000, "seconds": 40}]
    blocks = R.study_blocks(att, [t + 300])
    assert len(blocks) == 2
    assert abs((blocks[0][1] - blocks[0][0]) - 390) < 1      # 30 s before first answer → page visit + 60 s


def test_old_sheet_is_upgraded_without_losing_rows():
    client = FakeClient()
    book = client.book
    old_cols = TABS["Attempts"][:16]
    w = book.add_worksheet("Attempts", 1000, 16)
    w.update([old_cols, ["2026-10-01 10:00:00", "S001", "Anu", "k1"] + [""] * 8 + ["1", "0", "12", "practice"]], "A1")
    p = book.add_worksheet("Progress", 1000, 11)
    p.update([["student_id", "name", "last_active"]], "A1")
    st = SheetStore({}, "url", client=client)
    assert w.row_values(1) == TABS["Attempts"] and w.col_count >= len(TABS["Attempts"])
    assert p.row_values(1) == TABS["Progress"]
    assert {"Tests", "Activity", "Unit_Scores"} <= set(book.sheets)
    assert st.attempts("S001")[0]["correct"] == 1                # old row still readable


def test_local_db_upgrade(tmp_path):
    import sqlite3

    d = tmp_path / ".p1_trainer"
    d.mkdir()
    db = sqlite3.connect(d / "class.db")
    db.execute('CREATE TABLE "Attempts" (' + ", ".join(f"{c} TEXT" for c in TABS["Attempts"][:16]) + ")")
    db.execute('CREATE TABLE "Progress" (student_id TEXT, name TEXT)')
    db.commit()
    db.close()
    st = LocalStore(tmp_path)
    st.add_attempt({"time": "2026-10-01 10:00:00", "student_id": "S1", "correct": 1, "question": "Q?", "points": 15})
    assert st.attempts("S1")[0]["points"] == 15
    st.write_summary("Progress", [{"student_id": "S1", "name": "A", "points": 15}])
    assert st.rows("Progress")[0]["points"] == "15"


def test_full_record_in_sheet():
    st = SheetStore({}, "url", client=FakeClient())
    st.save_student({"student_id": "S001", "name": "Anu Mary", "pin": "1", "active": 1})
    prog = Progress(st, "S001", "Anu Mary")
    q = G.make("num_series", 1, 7)
    prog.record(q, q["answer"], True, 0, 25, "practice", 20)
    prog.record(q, (q["answer"] + 1) % 4, False, 1, 40, "speed", 2)
    user = {"id": "S001", "name": "Anu Mary", "role": "student"}
    R.log(st, user, "login")
    R.log_test(st, user, "Mock", [(q, q["answer"]), (q, None)], 3.5, 10)
    st.add_ai_log({"time": "2026-10-01 10:00:00", "student_id": "S001", "question": "What is pedagogy?",
                   "reply": "Pedagogy is…", "model": "Groq · x"})
    st.flush()
    a = st.ws["Attempts"].get_all_values()
    head = a[0]
    assert a[1][head.index("question")].startswith(q["text"].split()[0])
    assert a[1][head.index("correct_answer")].startswith(f"({q['answer'] + 1})")
    assert a[1][head.index("points")] == "20"
    t = dict(zip(st.ws["Tests"].row_values(1), st.ws["Tests"].get_all_values()[1]))
    assert t["marks"] == "2" and t["out_of"] == "4" and t["percent"] == "50"
    row, units = R.summary(st.students()[0], prog, [], st.rows("Activity", "S001"), st.ai_log("S001"),
                           st.rows("Tests", "S001"), 0.7)
    assert row["questions_total"] == 2 and row["points"] == 22 and row["logins"] == 1 and row["tests_taken"] == 1
    assert row["ai_tutor_questions"] == 1 and row["minutes_total"] >= 1
    st.upsert_summary("Progress", row)
    st.upsert_summary("Progress", {**row, "points": 99})          # same student: updated, not duplicated
    assert len(st.rows("Progress")) == 1 and str(st.rows("Progress")[0]["points"]) == "99"
    assert R.leaderboard(st, 0)[0]["points"] == 22


def test_daily_challenge_is_the_same_for_everyone_today():
    from p1.ui_games import daily_keys

    C = SimpleNamespace(POOL=[])
    a, b = daily_keys(C), daily_keys(C)
    assert a == b and len(a) == 10
    assert all(G.from_key(k) for k in a)


def test_google_key_can_be_pasted_as_json():
    import tomllib

    from p1.store import service_account_info

    s = tomllib.loads('sheet_url = "u"\ngroq_api_key = "g"\ngcp_service_account_json = \'\'\'\n'
                      '{"type": "service_account", "private_key": "-----BEGIN-----\\nAB\\n-----END-----\\n",'
                      ' "client_email": "bot@x.iam.gserviceaccount.com"}\n\'\'\'\n')
    info = service_account_info(s)
    assert info["client_email"].startswith("bot@") and "\nAB\n" in info["private_key"]
    assert service_account_info({"gcp_service_account": {"type": "service_account"}})["type"] == "service_account"
    assert service_account_info({}) is None
