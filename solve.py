from collections import Counter

from wordbank import WordBank, get_word_bank

Cell = tuple[int, int]

# All 8 directions, including diagonals.
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# Maps each cell to its valid neighbors
def build_cells(grid: list[list[str | None]]) -> dict[Cell, dict]:
    rows, cols = len(grid), len(grid[0])
    cells: dict[Cell, dict] = {}
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] is None:
                continue
            neighbors = {}
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] is not None:
                    neighbors[(nr, nc)] = grid[nr][nc]
            cells[(r, c)] = {"letter": grid[r][c], "neighbors": neighbors}
    return cells

def find_words(cells: dict[Cell, dict], bank: WordBank) -> set[str]:
    """Find every word made by walking between adjacent cells, using each cell at most once."""
    found: set[str] = set()

    def walk(pos: Cell, text: str, used: set[Cell]) -> None:
        text += cells[pos]["letter"]
        if not bank.is_prefix(text):
            return  # no word starts with these letters, so stop following this path
        if bank.is_word(text):
            found.add(text)
        used.add(pos)
        for neighbor in cells[pos]["neighbors"]:
            if neighbor not in used:
                walk(neighbor, text, used)
        used.remove(pos)

    for start in cells:
        walk(start, "", set())
    return found


def find_path(grid: list[list[str | None]], word: str) -> list[Cell] | None:
    """The cells that spell `word` by walking between adjacent cells (each used at most once),
    in order, or None if it can't be traced. Doesn't check the word list."""
    word = word.upper()
    cells = build_cells(grid)
    if not word or len(word) > len(cells):
        return None
    # Quick exit when the grid doesn't have enough of some letter.
    have = Counter(cell["letter"].upper() for cell in cells.values())
    if any(have[ch] < n for ch, n in Counter(word).items()):
        return None

    path: list[Cell] = []

    def walk(pos: Cell, i: int) -> bool:
        if cells[pos]["letter"].upper() != word[i]:
            return False
        path.append(pos)
        if i == len(word) - 1:
            return True
        for neighbor in cells[pos]["neighbors"]:
            if neighbor not in path and walk(neighbor, i + 1):
                return True
        path.pop()
        return False

    for start in cells:
        if walk(start, 0):
            return path
    return None


def group_by_length(words: set[str]) -> dict[str, list[str]]:
    """Group words by length (longest first), each group sorted alphabetically."""
    groups: dict[int, list[str]] = {}
    for word in words:
        groups.setdefault(len(word), []).append(word)
    return {f"{length} letters": sorted(groups[length]) for length in sorted(groups, reverse=True)}


def group_by_letter(words: set[str]) -> dict[str, list[str]]:
    """Group words by first letter (A to Z), each group sorted longest first, then alphabetically."""
    groups: dict[str, list[str]] = {}
    for word in words:
        groups.setdefault(word[0], []).append(word)
    return {letter: sorted(groups[letter], key=lambda w: (-len(w), w)) for letter in sorted(groups)}


def solve(grid: list[list[str | None]]) -> set[str]:
    """Called when the Solve button is clicked. `grid` is a list of rows of letters,
    with None for removed cells.

    Returns every word found in the grid.
    """
    cells = build_cells(grid)
    bank = get_word_bank()
    return find_words(cells, bank)
