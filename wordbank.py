"""Word bank: downloads an English word list once and caches it locally."""

import urllib.request
from pathlib import Path

# ENABLE word list: ~173k English words, commonly used for word games.
WORD_LIST_URL = "https://raw.githubusercontent.com/dolph/dictionary/master/enable1.txt"
CACHE_FILE = Path(__file__).with_name("words.txt")

MIN_WORD_LENGTH = 4
# A 4x4 grid has 16 cells, so no word found in it can be longer than this.
MAX_WORD_LENGTH = 16


def keep_word(word: str) -> bool:
    return MIN_WORD_LENGTH <= len(word) <= MAX_WORD_LENGTH


def save_words(words: list[str]) -> None:
    CACHE_FILE.write_text("\n".join(words) + "\n", encoding="utf-8", newline="\n")


def download_words() -> None:
    print(f"Downloading word list from {WORD_LIST_URL} ...")
    with urllib.request.urlopen(WORD_LIST_URL, timeout=30) as response:
        words = response.read().decode("utf-8").split()
    save_words([w for w in words if keep_word(w)])
    print(f"Saved to {CACHE_FILE}")


class WordBank:
    def __init__(self):
        if not CACHE_FILE.exists():
            download_words()
        all_words = CACHE_FILE.read_text(encoding="utf-8").split()
        kept = [w for w in all_words if keep_word(w)]
        if len(kept) < len(all_words):
            save_words(kept)  # shrink a cache saved before the length limits changed

        self.words: set[str] = {w.upper() for w in kept}
        # Every beginning of a word, e.g. "CAT" -> "C", "CA", "CAT".
        # Lets a solver stop following a path as soon as no word can start with it.
        self.prefixes: set[str] = {w[:i] for w in self.words for i in range(1, len(w) + 1)}

    def is_word(self, text: str) -> bool:
        return text.upper() in self.words

    def is_prefix(self, text: str) -> bool:
        return text.upper() in self.prefixes

    def __len__(self) -> int:
        return len(self.words)


_bank: WordBank | None = None


def get_word_bank() -> WordBank:
    """Load the word bank once and reuse it afterwards."""
    global _bank
    if _bank is None:
        _bank = WordBank()
    return _bank
