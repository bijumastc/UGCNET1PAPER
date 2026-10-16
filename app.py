"""UGC NET Paper 1 Trainer.

On your computer:   streamlit run app.py -- --folder ".."        (papers folder)
Online:             deployed on Streamlit Community Cloud from a private GitHub repo (see DEPLOY.md).
"""
import argparse
import hmac
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
from p1 import ai_writer as AI  # noqa: E402
from p1 import generators as G  # noqa: E402
from p1.extract import ocr_available  # noqa: E402
from p1.library import (DATA_DIR, apply_overrides, build_library, current_stamp, load_library,  # noqa: E402
                        load_overrides, practice_pool)
from p1.progress import Progress  # noqa: E402
from p1.store import LocalStore, now_iso, open_store  # noqa: E402
from p1.ui_common import ss  # noqa: E402
from p1 import records as R  # noqa: E402
from p1 import simulators as SIM  # noqa: E402
from p1 import ui_student as S  # noqa: E402
from p1 import ui_teacher as T  # noqa: E402
from p1 import ui_tutor as TU  # noqa: E402

st.set_page_config(page_title="Paper 1 Trainer", page_icon="📘", layout="wide")


# ================================================================== where things live
def secrets() -> dict:
    try:
        return {k: st.secrets[k] for k in st.secrets}
    except Exception:
        return {}


SECRETS = secrets()


def cli_folder():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--folder")
    a, _ = ap.parse_known_args()
    return a.folder or os.environ.get("P1_FOLDER")


BUNDLE = APP_DIR / "bundle" / "library.json"
if "folder" not in ss:
    ss.folder = cli_folder() or (str(APP_DIR) if BUNDLE.exists() else os.getcwd())
folder = Path(ss.folder).expanduser().resolve()
MODE = "local" if (folder / DATA_DIR / "library.json").exists() or not BUNDLE.exists() else "bundle"
if SECRETS.get("sheet_url") and BUNDLE.exists():
    MODE = "bundle"                                       # online deployment always uses the bundle


@st.cache_resource(show_spinner="Connecting to the class sheet…")
def get_store(folder_str: str):
    return open_store(folder_str, SECRETS)


@st.cache_data(show_spinner=False)
def load_bundle(mtime: float):
    return json.loads(BUNDLE.read_text(encoding="utf-8"))


store = get_store(str(folder))
lib = (load_bundle(BUNDLE.stat().st_mtime) if MODE == "bundle" else load_library(folder)) or \
    {"questions": [], "files": [], "pairing": [], "families": {}}


# ================================================================== who is using the app
def teacher_password():
    return SECRETS.get("teacher_password") or store.get("class:teacher_password", "")


def viewer_email():
    try:
        e = st.user.get("email") if hasattr(st, "user") else None
        return (e or "").strip().lower() or None
    except Exception:
        return None


def login_screen():
    roster = [s for s in store.students() if str(s.get("active", "1")) not in ("0", "False", "false", "FALSE")]
    email = viewer_email()
    if email:
        if email == str(SECRETS.get("teacher_email", "")).lower():
            ss.user = {"id": "teacher", "name": "Teacher", "role": "teacher"}
            st.rerun()
        match = [s for s in roster if (s.get("email") or "").lower() == email]
        if match:
            ss.user = {"id": match[0]["student_id"], "name": match[0]["name"], "role": "student"}
            st.rerun()
    st.title("📘 Paper 1 Trainer")
    st.caption("UGC NET General Paper on Teaching & Research Aptitude")
    t1, t2 = st.tabs(["🎓 Student", "🧑‍🏫 Teacher"])
    with t1:
        with st.form("student_login"):
            sid = st.text_input("Student ID", placeholder="S001").strip().upper()
            pin = st.text_input("PIN", type="password").strip()
            if st.form_submit_button("Log in", type="primary"):
                m = [s for s in roster if str(s["student_id"]).upper() == sid and str(s.get("pin")) == pin]
                if m:
                    ss.user = {"id": m[0]["student_id"], "name": m[0]["name"], "role": "student"}
                    st.rerun()
                st.error("That ID and PIN don't match. Please check with your teacher. 🙂")
    with t2:
        with st.form("teacher_login"):
            pw = st.text_input("Teacher password", type="password")
            if st.form_submit_button("Log in"):
                if teacher_password() and hmac.compare_digest(pw, teacher_password()):
                    ss.user = {"id": "teacher", "name": "Teacher", "role": "teacher"}
                    st.rerun()
                st.error("Wrong password.")
    st.stop()


if "user" not in ss:
    if not teacher_password() and MODE == "local" and not store.students():
        ss.user = {"id": "me", "name": "", "role": "owner"}          # personal use: no login needed
    else:
        login_screen()
USER = ss.user
IS_TEACHER = USER["role"] in ("teacher", "owner")


# ================================================================== questions available
def corrections():
    c = load_overrides(folder) if MODE == "local" else {}
    c.update(store.corrections())
    return c


QUESTIONS = apply_overrides(lib["questions"], corrections())
allow_memory = store.get("class:allow_memory", "1") == "1"
allow_ai = store.get("class:allow_ai", "1") == "1"
AIQ = [AI.as_question(r) for r in store.ai_questions() if r.get("status") == "approved"] if allow_ai else []
POOL = practice_pool(QUESTIONS, allow_memory) + AIQ
BY_KEY = {q["key"]: q for q in QUESTIONS}
BY_KEY.update({q["key"]: q for q in AIQ})


def get_q(key):
    if key is None:
        return None
    if str(key).startswith("gen:"):
        return G.from_key(key)
    return BY_KEY.get(key)


def report_problem(q):
    if IS_TEACHER:
        store.save_correction(q["key"], exclude=True, by="teacher")
        st.toast("Question left out of practice.")
    else:
        store.add_report({"time": now_iso(), "student_id": USER["id"], "question_key": q["key"],
                          "message": "", "status": "open"})
        st.toast("Thanks! Your teacher will check this question. 🙏")


C = SimpleNamespace(
    store=store, lib=lib, folder=str(folder), app_dir=str(APP_DIR), mode=MODE, user=USER,
    prog=Progress(store, USER["id"], USER["name"]), QUESTIONS=QUESTIONS, AIQ=AIQ, POOL=POOL, get_q=get_q,
    report_problem=report_problem, secrets=SECRETS,
    gemini_key=SECRETS.get("gemini_api_key") or store.get("class:gemini_api_key", ""),
    gemini_model=SECRETS.get("gemini_model") or store.get("class:gemini_model", AI.DEFAULT_MODEL),
)

# ================================================================== sidebar & pages
st.sidebar.title("📘 Paper 1 Trainer")
who = {"teacher": "🧑‍🏫 Teacher", "owner": "🧑‍🏫 You (teacher & learner)"}.get(USER["role"], f"🎓 {USER['name']}")
st.sidebar.markdown(f"**{who}**")
if getattr(store, "open_error", None) and IS_TEACHER:
    st.sidebar.error(store.open_error)

if MODE == "local" and IS_TEACHER:
    with st.sidebar.expander("📂 Papers folder", expanded=not lib["questions"]):
        f_in = st.text_input("Folder", ss.folder)
        if f_in != ss.folder:
            ss.folder = f_in
            st.rerun()
        stale = lib.get("questions") and lib.get("complete", True) and lib.get("file_stamp") != current_stamp(folder)
        if st.button("🔄 Scan" + (" new files" if stale else ""), help="Reads only new or unfinished papers."):
            box = st.status("Reading papers…", expanded=True)
            bar = box.progress(0.0)
            build_library(folder, progress=lambda f, m="": bar.progress(min(1.0, f), text=m), log=box.write)
            box.update(label="Done.", state="complete")
            st.rerun()
        st.button("↻ Reload")
        st.caption("Many papers? In Command Prompt: `python scan_papers.py .. --light`")
        if not ocr_available():
            st.warning("Tesseract OCR not found.")

STUDENT_PAGES = {"🏠 Home": S.page_home, "📖 Learn": S.page_learn, "🤖 AI tutor": TU.page_tutor,
                 "🧪 Simulators": SIM.page_simulators, "✍️ Practice": S.page_practice, "📝 Tests": S.page_tests,
                 "📈 My progress": S.page_progress, "🔍 Patterns": S.page_patterns, "⚙️ My settings": S.page_my_settings}
TEACHER_PAGES = {"🏫 Class dashboard": T.page_dashboard, "👥 Students": T.page_students,
                 "🪄 AI question writer": T.page_ai, "📂 Papers & checks": T.page_library, "📖 Learn": S.page_learn,
                 "🤖 AI tutor": TU.page_tutor, "🧪 Simulators": SIM.page_simulators, "✍️ Practice": S.page_practice,
                 "📝 Tests": S.page_tests, "🔍 Patterns": S.page_patterns, "⚙️ Class settings": T.page_class_settings}
if USER["role"] == "owner":
    PAGES = {"🏠 Home": S.page_home, **TEACHER_PAGES, "📈 My progress": S.page_progress}
elif USER["role"] == "teacher":
    PAGES = TEACHER_PAGES
else:
    PAGES = STUDENT_PAGES
if ss.get("nav") not in PAGES:
    ss.nav = next(iter(PAGES))
page = st.sidebar.radio("Go to", list(PAGES), key="nav")
if not ss.get("_logged_login"):                       # Activity tab: login, pages visited, logout
    ss._logged_login = True
    R.log(store, USER, "login", "email" if viewer_email() else "")
if ss.get("_last_page") != page:
    ss._last_page = page
    R.log(store, USER, "page", page)
st.sidebar.caption(f"{len(POOL)} past-paper questions ready · ♾️ unlimited generated practice")
if USER["role"] != "owner" and st.sidebar.button("Log out"):
    R.log(store, USER, "logout")
    R.refresh_one(C, force=True)
    store.flush()
    for k in list(ss.keys()):
        del ss[k]
    st.rerun()

PAGES[page](C)
