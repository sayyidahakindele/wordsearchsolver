# Wordsearch solver

A solver for word-grid puzzles. Type the letters from a puzzle into the grid and it lists every English word you can trace through touching squares, longest first.

**Try it in your browser (works on phones):** https://sayyidahakindele.github.io/wordsearchsolver/

It runs entirely in the browser: plain HTML, CSS and JavaScript, deployed to GitHub Pages.

## Features

- Grids from 4×4 up to 20×20, chosen from drop-downs. Any shape works up to 9×9; anything larger has to be square, so changing one size changes the other.
- Words can run in all 8 directions, including diagonals, and each square is used at most once per word.
- Remove a square to mark it as a gap that no word can pass through: double-click it, or double-tap or press and hold on a phone. Do it again to restore the square with its letter.
- **Find a word:** once the grid is full, type a word to see its path. The squares light up and a line joins them in order, starting from the outlined square.
- The word list appears beside the grid (below it on phones), grouped by length or by first letter. Click a word to see its path; double-click it to cross it out, and again to bring it back.
- If you change the grid after solving, a note says the list is out of date until you solve again.
- Light and dark mode. It follows your device's setting until you pick one with the button.
- Remembers your grid between visits.
- 169,429-word dictionary (the ENABLE word list, limited to words of 4 to 16 letters, plus a few additions).

## How it works

1. **Build an adjacency map.** Each square is mapped to its letter and the positions of its neighbours. Removed squares are left out, so nothing treats them as a neighbour.
2. **Search every path with pruning.** A depth-first search starts from each square and extends the current path one neighbour at a time, never revisiting a square already on the path.
3. **Stop dead ends early.** The word bank stores every word and also every prefix of every word (`C`, `CA`, `CAT`, …). As soon as the letters on a path aren't the start of any word, the search abandons that path. This turns an exponential number of possible paths into a fast search.

Finding a single word's path uses the same walk, following only the letters of that word. It first checks that the grid has enough of each letter, so words that can't fit are rejected straight away.

The code is `findWords` and `findPath` in [web/solver.js](web/solver.js).

## Running it locally

```
python build_site.py
python -m http.server -d _site
```

Then open http://localhost:8000. The page loads its word list over HTTP, so opening `index.html` directly from disk doesn't work. After editing anything in `web/` or `words.txt`, run `python build_site.py` again and refresh.

To try it on a phone on the same Wi-Fi, start the server with `--bind 0.0.0.0` and open `http://<your computer's IP>:8000`.

## Project structure

| Path | What it is |
| --- | --- |
| `web/index.html` | The page: layout, styles, grid, search and results behaviour. |
| `web/solver.js` | The word bank and solver. |
| `words.txt` | The word list (one word per line, in alphabetical order). |
| `build_site.py` | Wraps the page in a full HTML document and copies it with the solver and word list into `_site/` for hosting. |
| `.github/workflows/pages.yml` | Builds and deploys the site to GitHub Pages on every push to `main`. |

## Tech

Plain HTML/CSS/JavaScript with no frameworks or build tools, and GitHub Actions with GitHub Pages for deployment.
