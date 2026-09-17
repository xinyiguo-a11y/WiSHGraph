#!/usr/bin/env python3
"""
Inline every local image referenced by a chapter page as a base64 data URI.

Why this exists
---------------
The chapter pages live in output/ and point at ../assets/. That resolves fine
when the page is opened straight from disk, but a sandboxed preview (or any
server rooted at output/) refuses to walk up one level: the browser requests
output/../assets/... , gets a 404 and paints a broken-image icon instead.

Embedding the bytes makes every chapter self-contained -- it can be opened,
mailed or uploaded on its own. Images are downscaled and re-encoded first so the
payload stays small (the whole chapter 3 gallery lands around 300 KB).

Idempotent: <img> tags that already carry a data: URI are left alone.

Usage
-----
    python3 scripts/inline_assets.py output/chapter2.html output/chapter3.html
"""

import base64
import io
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# filename -> (format, max side in px, quality for JPEG)
RULES = {
    "post_wealth_cat_wish.png":           ("JPEG", 640, 90),
    "post_caishen_blessing.png":          ("JPEG", 760, 88),
    "wishgraph_ontology_graph.jpg":       ("JPEG", 1327, 88),
    "case_medicine_buddha_wish.jpg":      ("JPEG", 1000, 84),
    "case_kardashian_manifestation.jpg":  ("JPEG", 1000, 84),
    "conceptual_diagram.png":             ("JPEG", 1300, 92),
    "wishgraph_tbox_ontograf.png":        ("PNG", 1400, None),
}
DEFAULT_RULE = ("JPEG", 1400, 88)

IMG_RE = re.compile(r'(<img\b[^>]*?\bsrc=")((?:\.\./)+assets/[^"]+)(")')

_cache: dict[str, str] = {}


def data_uri(rel_href: str) -> str:
    """Turn ../assets/foo.png into a data: URI, re-encoding to keep it small."""
    if rel_href in _cache:
        return _cache[rel_href]

    name = os.path.basename(rel_href)
    path = os.path.join(ROOT, "assets", name)
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    fmt, max_side, quality = RULES.get(name, DEFAULT_RULE)
    im = Image.open(path)
    im.thumbnail((max_side, max_side), Image.LANCZOS)

    buf = io.BytesIO()
    if fmt == "JPEG":
        im.convert("RGB").save(buf, "JPEG", quality=quality,
                               optimize=True, progressive=True)
        mime = "image/jpeg"
    else:
        im.save(buf, "PNG", optimize=True)
        mime = "image/png"

    raw = buf.getvalue()
    before = os.path.getsize(path)
    print(f"    {name:36s} {im.size[0]}x{im.size[1]}  "
          f"{before/1024:7.1f} KB -> {len(raw)/1024:6.1f} KB")

    uri = f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")
    _cache[rel_href] = uri
    return uri


def inline(page: str) -> None:
    with open(page, encoding="utf-8") as fh:
        src = fh.read()

    hits = [m for m in IMG_RE.finditer(src) if not m.group(2).startswith("data:")]
    if not hits:
        print(f"  {os.path.basename(page)}: nothing to inline (already embedded)")
        return

    print(f"  {os.path.basename(page)}: {len(hits)} image(s)")
    # replace right-to-left so earlier offsets stay valid
    for m in reversed(hits):
        uri = data_uri(m.group(2))
        src = src[:m.start()] + m.group(1) + uri + m.group(3) + src[m.end():]

    with open(page, "w", encoding="utf-8") as fh:
        fh.write(src)
    print(f"    -> {page} is now {len(src)/1024:.0f} KB, self-contained")


def main(argv: list[str]) -> int:
    pages = argv[1:] or [
        os.path.join(ROOT, "output", "chapter2.html"),
        os.path.join(ROOT, "output", "chapter3.html"),
    ]
    for page in pages:
        page = page if os.path.isabs(page) else os.path.join(ROOT, page)
        inline(page)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
