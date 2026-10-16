"""Sort a folder of Paper 1 papers into an Excel workbook (no app needed).

    python sort_papers.py "D:/NET/Paper1"            -> D:/NET/Paper1/paper1_sorted.xlsx

Sheets: Questions (sorted by unit and topic), Units, Topic x Format, Asked again, Skipped, Files.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p1.library import STATUS_TEXT, apply_overrides, build_library, load_overrides  # noqa: E402
from p1.patterns import pattern_name  # noqa: E402
from p1.syllabus import subtopic_name, unit_label  # noqa: E402


def main():
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    lib = build_library(folder, log=print)
    qs = apply_overrides(lib["questions"], load_overrides(folder))
    rows = [{"Unit": unit_label(q.get("unit")), "Topic": subtopic_name(q.get("subtopic")),
             "Format": pattern_name(q.get("pattern")), "Level": q.get("level"), "Session": q["session"],
             "Q": q["qno"], "Question ID": q.get("qid"), "Source": q["origin"], "Status": STATUS_TEXT[q["status"]],
             "Answer (option)": (q["answer"] + 1) if q.get("answer") is not None else None,
             "Answer source": q.get("answer_source"), "Question": q["text"],
             **{f"Option {i+1}": (q["options"][i] if len(q.get("options") or []) == 4 else "") for i in range(4)},
             "Repeated in sessions": q.get("family_sessions") if (q.get("family_sessions") or 0) > 1 else None}
            for q in qs]
    df = pd.DataFrame(rows).sort_values(["Unit", "Topic", "Session", "Q"])
    ok = df[df["Status"] == "Verified"]
    out = folder / "paper1_sorted.xlsx"
    with pd.ExcelWriter(out) as xl:
        df.to_excel(xl, sheet_name="Questions", index=False)
        df.groupby("Unit").agg(Questions=("Q", "size"), Verified=("Status", lambda s: (s == "Verified").sum()),
                               Sessions=("Session", "nunique")).to_excel(xl, sheet_name="Units")
        pd.crosstab(df["Topic"], df["Format"], margins=True, margins_name="Total").to_excel(xl, sheet_name="Topic x Format")
        df[df["Repeated in sessions"].notna()].to_excel(xl, sheet_name="Asked again", index=False)
        df[df["Status"] != "Verified"][["Session", "Q", "Status", "Question"]].to_excel(xl, sheet_name="Skipped", index=False)
        pd.DataFrame(lib["files"]).drop(columns=["issues"]).to_excel(xl, sheet_name="Files", index=False)
    print(f"\n{len(df)} English questions, {len(ok)} verified. Saved {out}")
    print(df.groupby("Unit").size().to_string())


if __name__ == "__main__":
    main()
