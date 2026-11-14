// Word bank and grid solver. Same logic as wordbank.py and solve.py in the desktop app.

const DIRECTIONS = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]];

/** Build the word bank from the text of words.txt (one word per line). */
function buildWordBank(text) {
  const words = new Set();
  const prefixes = new Set();
  for (const raw of text.split(/\s+/)) {
    if (!raw) continue;
    const word = raw.toUpperCase();
    words.add(word);
    for (let i = 1; i <= word.length; i++) prefixes.add(word.slice(0, i));
  }
  return { words, prefixes, size: words.size };
}

/**
 * Map each cell "r,c" to its letter and its neighbours' keys.
 * `grid` is an array of rows; a removed cell is null and is nobody's neighbour.
 */
function buildCells(grid) {
  const rows = grid.length;
  const cols = grid[0].length;
  const cells = new Map();
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (grid[r][c] === null) continue;
      const neighbors = [];
      for (const [dr, dc] of DIRECTIONS) {
        const nr = r + dr;
        const nc = c + dc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] !== null) {
          neighbors.push(`${nr},${nc}`);
        }
      }
      cells.set(`${r},${c}`, { letter: grid[r][c].toUpperCase(), neighbors });
    }
  }
  return cells;
}

/** Every word made by walking between adjacent cells, using each cell at most once. */
function findWords(grid, bank) {
  const cells = buildCells(grid);
  const found = new Set();
  const used = new Set();

  function walk(key, text) {
    text += cells.get(key).letter;
    if (!bank.prefixes.has(text)) return; // no word starts with these letters
    if (bank.words.has(text)) found.add(text);
    used.add(key);
    for (const next of cells.get(key).neighbors) {
      if (!used.has(next)) walk(next, text);
    }
    used.delete(key);
  }

  for (const key of cells.keys()) walk(key, "");
  return found;
}

/** Group by length (longest first), alphabetical within each group. */
function groupByLength(words) {
  const groups = new Map();
  for (const w of words) {
    if (!groups.has(w.length)) groups.set(w.length, []);
    groups.get(w.length).push(w);
  }
  return [...groups.keys()]
    .sort((a, b) => b - a)
    .map((len) => ({ name: `${len} letters`, words: groups.get(len).sort() }));
}

/** Group by first letter (A to Z), longest first within each letter, then alphabetical. */
function groupByLetter(words) {
  const groups = new Map();
  for (const w of words) {
    if (!groups.has(w[0])) groups.set(w[0], []);
    groups.get(w[0]).push(w);
  }
  return [...groups.keys()]
    .sort()
    .map((letter) => ({
      name: letter,
      words: groups.get(letter).sort((a, b) => b.length - a.length || (a < b ? -1 : a > b ? 1 : 0)),
    }));
}

if (typeof module !== "undefined") {
  module.exports = { buildWordBank, buildCells, findWords, groupByLength, groupByLetter };
}
