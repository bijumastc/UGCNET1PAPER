"""Scan your papers folder from the Command Prompt (the app can stay open meanwhile).

    python scan_papers.py ..          (".." = the folder above the app = your papers folder)
    python scan_papers.py .. --light  (gentlest: one page at a time, for computers with little memory)

Shows progress page by page. Safe to stop with Ctrl+C: finished pages and papers are saved,
and running it again continues where it stopped. When it finishes, click "Reload" in the app.
"""
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p1.extract import ocr_available  # noqa: E402
from p1.library import STATUS_TEXT, build_library  # noqa: E402


def main():
    import os

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--light" in sys.argv:
        os.environ["P1_OCR_WORKERS"] = "1"
    folder = Path(args[0] if args else "..").resolve()
    print(f"Scanning {folder}")
    if not ocr_available():
        print("WARNING: Tesseract OCR not found. NTA papers whose questions are pictures can't be read.")
    t0 = time.time()

    def progress(frac, msg=""):
        sys.stdout.write(f"\r  {frac * 100:5.1f}%  {msg[:90]:<90}")
        sys.stdout.flush()

    try:
        lib = build_library(folder, progress=progress, log=lambda m: print("\n" + m))
    except KeyboardInterrupt:
        print("\n\nStopped. Everything finished so far is saved; run the same command again to continue.")
        return
    qs = lib["questions"]
    print(f"\n\nDone in {(time.time() - t0) / 60:.1f} min.")
    for f in lib["files"]:
        if f["role"] == "paper":
            n_ok = sum(q["status"] == "ok" for q in qs if q["source_file"] == f["file"])
            print(f"  paper  {f['file']}: {f['questions']} questions, {n_ok} verified")
        else:
            print(f"  {f['role']:<6} {f['file']}" + (f"  ({f['error']})" if f.get("error") else ""))
    print("\nNot used for practice:", dict(Counter(STATUS_TEXT[q["status"]] for q in qs if q["status"] != "ok")) or "none")
    print(f"Ready to practise: {sum(q['status'] == 'ok' for q in qs)} questions. Open the app and click Reload.")


if __name__ == "__main__":
    main()
