"""Cut a question (or its shared passage/table) out of the original PDF page as an image."""
from __future__ import annotations

import hashlib
from pathlib import Path


def crop_regions(pdf_path: str, regions: list, cache_dir: Path, scale: float = 2.0):
    """regions: [[page, y0, y1], ...] (page 1-based, y as page fraction). Returns list of PNG paths."""
    if not regions:
        return []
    import pypdfium2 as pdfium

    cache_dir.mkdir(parents=True, exist_ok=True)
    out = []
    doc = None
    for page, y0, y1 in regions:
        key = hashlib.sha1(f"{pdf_path}|{page}|{y0:.4f}|{y1:.4f}|{scale}".encode()).hexdigest()[:16]
        png = cache_dir / f"{key}.png"
        if not png.exists():
            if doc is None:
                doc = pdfium.PdfDocument(pdf_path)
            img = doc[page - 1].render(scale=scale).to_pil()
            h = img.height
            top = max(0, int((y0 - 0.003) * h))
            bottom = min(h, int((y1 + 0.005) * h))
            if bottom - top < 20:
                continue
            img.crop((0, top, img.width, bottom)).save(png)
        out.append(str(png))
    if doc is not None:
        doc.close()
    return out


def page_image(pdf_path: str, page: int, cache_dir: Path, scale: float = 1.6) -> str:
    import pypdfium2 as pdfium

    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{pdf_path}|{page}|full|{scale}".encode()).hexdigest()[:16]
    png = cache_dir / f"{key}.png"
    if not png.exists():
        doc = pdfium.PdfDocument(pdf_path)
        doc[page - 1].render(scale=scale).to_pil().save(png)
        doc.close()
    return str(png)
