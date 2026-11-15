# Word search solver

A solver for word-grid puzzles. Type the letters from a puzzle into the grid and it lists every English word you can trace through touching squares, longest first.

**Try it in your browser (works on phones):** https://sayyidahakindele.github.io/wordsearchsolver/

There are two versions that share the same approach:

- **Web app** (JavaScript): runs entirely in the browser, deployed to GitHub Pages.
- **Desktop app** (Python, Qt/PySide6): the original version.

## Features

- Grids from 2×2 up to 8×8, chosen from drop-downs.
- Words can run in all 8 directions, including diagonals, and each square is used at most once per word.
- Remove a square to mark it as a gap that no word can pass through. Double-click on desktop; double-tap or press and hold on a phone. Do it again to restore the square with its letter.
- Results grouped either by length (longest first) or by first letter, A to Z.
- 169,426-word dictionary (the ENABLE word list, limited to words of 4 to 16 letters).
- The web app remembers your grid between visits and supports the phone's back gesture.

## How it works

1. **Build an adjacency map.** Each square is mapped to its letter and the positions of its neighbours. Removed squares are left out, so nothing treats them as a neighbour.
2. **Search every path with pruning.** A depth-first search starts from each square and extends the current path one neighbour at a time, never revisiting a square already on the path.
3. **Stop dead ends early.** The word bank stores every word and also every prefix of every word (`C`, `CA`, `CAT`, …). As soon as the letters on a path aren't the start of any word, the search abandons that path. This turns an exponential number of possible paths into a fast search. A 4×4 grid solves in a few milliseconds and an 8×8 in under a tenth of a second.

The search is about 20 lines: `find_words` in [solve.py](solve.py) and `findWords` in [web/solver.js](web/solver.js).

## Running it

### Web app

The live version is linked above. To run it locally:

```
python build_site.py
python -m http.server -d _site
```

Then open http://localhost:8000. The page loads its word list over HTTP, so opening `index.html` directly from disk doesn't work.

### Desktop app

Requires Python 3.10 or newer.

```
pip install -r requirements.txt
python main.py
```

Fill every square, then click **Solve**. **Back to grid** returns to the letters you entered.

## Project structure

| Path | What it is |
| --- | --- |
| `main.py` | Starts the desktop app. |
| `creategrid.py` | Desktop window: size drop-downs, letter grid, Solve button, results page. |
| `solve.py` | Builds the adjacency map, finds words, groups results. |
| `wordbank.py` | Loads `words.txt` into word and prefix sets, downloading the ENABLE list on first run if the file is missing. |
| `words.txt` | The word list (4 to 16 letters, one per line). |
| `web/index.html` | The web app's page: layout, styles, grid and results behaviour. |
| `web/solver.js` | JavaScript port of the solver and word bank. |
| `build_site.py` | Wraps the web app in a full HTML page and copies it with the word list into `_site/` for hosting. |
| `.github/workflows/pages.yml` | Builds and deploys the web app to GitHub Pages on every push to `main`. |

## Tech

Python 3, PySide6 (Qt 6), plain HTML/CSS/JavaScript with no frameworks or build tools, and GitHub Actions with GitHub Pages for deployment.
