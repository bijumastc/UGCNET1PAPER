"""Prepare your scanned papers for the online (Streamlit Cloud) app.

    python make_bundle.py ..

Reads the library made by scan_papers.py (plus your corrections) and writes, inside the app folder:
    bundle/library.json   - every question, its unit/topic/format and its verified answer
    bundle/images_1.zip   - the scanned NTA questions cut from their pages (small grey pictures),
    bundle/images_2.zip     packed into a few zip files of at most ~20 MB each, so the bundle is only a
    ...                     handful of files (GitHub's website takes 100 files / 25 MB per file per upload)
The online app uses only this bundle: no PDFs, no OCR, nothing to install for students.
Run it again whenever you add papers, then upload (push) the app folder to GitHub.
"""
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))
from p1.library import apply_overrides, load_library, load_overrides  # noqa: E402
from p1.store import LocalStore  # noqa: E402


def crop(doc_cache, pdf_path, page, y0, y1, out: Path, scale=1.7):
    import pypdfium2 as pdfium

    if pdf_path not in doc_cache:
        doc_cache[pdf_path] = pdfium.PdfDocument(pdf_path)
    img = doc_cache[pdf_path][page - 1].render(scale=scale).to_pil()
    h = img.height
    top, bottom = max(0, int((y0 - 0.003) * h)), min(h, int((y1 + 0.005) * h))
    if bottom - top < 20:
        return False
    img.crop((0, top, img.width, bottom)).convert("L").quantize(16).save(out, optimize=True)   # crisp, ~25 KB
    return True


def main():
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "..").resolve()
    lib = load_library(folder)
    if not lib:
        print("No scanned library found. Run first:  python scan_papers.py ..")
        return
    store = LocalStore(folder)
    corrections = {**load_overrides(folder), **store.corrections()}
    qs = apply_overrides(lib["questions"], corrections)

    out = APP / "bundle"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    tmp = Path(tempfile.mkdtemp(prefix="p1_bundle_"))
    (tmp / "img").mkdir()
    docs, made = {}, 0
    for i, q in enumerate(qs):
        q.pop("source_path", None)
        if q.get("display") == "image":
            pdf = next(iter(folder.rglob(q["source_file"])), None)
            if pdf is None:
                q["display"] = "text"
                continue
            for field, regions in (("img", q.get("regions") or []), ("group_img", q.get("group_regions") or [])):
                files = []
                for page, y0, y1 in regions:
                    name = hashlib.sha1(f"{q['source_file']}|{page}|{y0:.4f}|{y1:.4f}".encode()).hexdigest()[:16] + ".png"
                    path = tmp / "img" / name
                    if path.exists() or crop(docs, str(pdf), page, y0, y1, path):
                        files.append(f"img/{name}")
                        made += 1
                q[field] = files
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(qs)} questions")
    lib["questions"] = qs
    lib["bundle"] = True
    (out / "library.json").write_text(json.dumps(lib), encoding="utf-8")
    pack(tmp / "img", out)
    shutil.rmtree(tmp, ignore_errors=True)
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file()) / 1e6
    ok = sum(q["status"] == "ok" for q in qs)
    print(f"\nBundle ready: {len(qs)} questions ({ok} verified), {made} images, {size:.1f} MB in {out}")
    files = sorted(p.name for p in out.iterdir())
    print(f"The bundle folder has {len(files)} files: {', '.join(files)}")
    print("Next: upload the app folder (with 'bundle') to your private GitHub repository.")


def pack(img_dir: Path, out: Path, max_bytes: int = 20 * 1024 * 1024):
    """Put the pictures into images_1.zip, images_2.zip, … (PNGs are already compressed: store them)."""
    n, z, size = 0, None, 0
    for f in sorted(img_dir.glob("*.png")):
        if z is None or size + f.stat().st_size > max_bytes:
            if z:
                z.close()
            n += 1
            z, size = zipfile.ZipFile(out / f"images_{n}.zip", "w", zipfile.ZIP_STORED), 0
        z.write(f, f"img/{f.name}")
        size += f.stat().st_size
    if z:
        z.close()


if __name__ == "__main__":
    main()
