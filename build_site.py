"""Build the web version into _site/ for GitHub Pages (or any static host).

web/index.html is written as page content only (no <html>/<head> skeleton), so this
script wraps it in a full HTML document and copies in the solver and the word list.

    python build_site.py
    python -m http.server -d _site      # then open http://localhost:8000
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).parent
WEB = ROOT / "web"
OUT = ROOT / "_site"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Type the letters from a word-grid puzzle and list every word you can trace through touching squares.">
<style>
  :root { color-scheme: light; padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
  body { margin: 0; font: 14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
  img { max-width: 100%; }
  [hidden] { display: none !important; }
</style>
"""


def build() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    page = (WEB / "index.html").read_text(encoding="utf-8")
    (OUT / "index.html").write_text(HEAD + page + "\n</html>\n", encoding="utf-8", newline="\n")
    shutil.copy(WEB / "solver.js", OUT / "solver.js")
    shutil.copy(ROOT / "words.txt", OUT / "words.txt")
    print(f"Built {OUT}")


if __name__ == "__main__":
    build()
