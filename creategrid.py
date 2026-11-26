from string import Template

from PySide6.QtCore import QPointF, QRegularExpression, QSettings, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QPainter,
    QPalette,
    QPen,
    QPolygonF,
    QRegularExpressionValidator,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from solve import find_path, group_by_length, group_by_letter, solve

# Options in the results page's Sort drop-down: label -> grouping function.
SORT_OPTIONS = {
    "Length, then A–Z": group_by_length,
    "A–Z, then length": group_by_letter,
}

DEFAULT_ROWS = 4
DEFAULT_COLS = 4
SIZE_CHOICES = range(4, 21)  # sizes offered in the Rows and Columns drop-downs
SQUARE_ONLY_ABOVE = 12  # a grid with more rows or columns than this must be square
SQUARE_SIZE = 80

# Same colours as the web version.
THEMES = {
    "light": {
        "bg": "#f4efe3", "surface": "#ffffff", "ink": "#172030", "muted": "#586477",
        "line": "#c7cfdc", "accent": "#2c55e0", "accent_ink": "#ffffff",
        "solve": "#9b783d", "solve_ink": "#ffffff",
        "tile": "#fffdf7", "tile_edge": "#b9c3d3", "removed": "#3a4354",
    },
    "dark": {
        "bg": "#1b1c1e", "surface": "#171d27", "ink": "#e6eaf1", "muted": "#9aa5b6",
        "line": "#2e3746", "accent": "#7896ff", "accent_ink": "#0d1220",
        "solve": "#7896ff", "solve_ink": "#0d1220",
        "tile": "#1e2532", "tile_edge": "#3a4558", "removed": "#0a0d12",
    },
}

STYLE = Template("""
QLineEdit {
    background-color: $tile;
    color: $ink;
    border: 2px solid $tile_edge;
    border-bottom-width: 4px;
    border-radius: 8px;
}
QLineEdit:focus {
    background-color: $surface;
    border-color: $accent;
}
QLineEdit[removed="true"] {
    background-color: $removed;
    border: 2px dashed $tile_edge;
}
QLineEdit[path="on"], QLineEdit[path="start"] {
    background-color: $accent;
    border-color: $accent;
    color: $accent_ink;
}
QLineEdit[path="start"] {
    border: 3px solid $ink;
    border-bottom-width: 4px;
}
QLineEdit#searchBox {
    background-color: $surface;
    border: 1px solid $line;
    padding: 6px;
    font-size: 16px;
}
QLineEdit#searchBox:focus {
    border: 2px solid $accent;
}
QPushButton {
    background-color: $surface;
    color: $ink;
    border: 1px solid $line;
    border-radius: 8px;
    padding: 6px 12px;
}
QPushButton:hover {
    border-color: $accent;
}
QPushButton#solveButton {
    background-color: $solve;
    border-color: $solve;
    color: $solve_ink;
    font-weight: bold;
}
QPushButton#solveButton, QPushButton#backButton {
    padding: 8px;
    font-size: 16px;
}
QLabel#resultsTitle {
    font-size: 18px;
    font-weight: bold;
}
QLabel.groupTitle {
    font-size: 14px;
    font-weight: bold;
    margin-top: 8px;
}
""")


class LetterSquare(QLineEdit):
    """A square that holds a single letter. Double-click to remove it; double-click again to restore it."""

    removed_changed = Signal()

    def __init__(self, row: int, col: int, size: int = SQUARE_SIZE):
        super().__init__()
        self.row = row
        self.col = col
        self.removed = False
        self.saved_letter = ""
        self.setMaxLength(1)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", max(8, round(28 * size / SQUARE_SIZE)), QFont.Bold))
        self.setValidator(QRegularExpressionValidator(QRegularExpression("[A-Za-z]")))

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.selectAll()  # typing a new letter replaces the old one

    def mouseDoubleClickEvent(self, event):
        self.set_removed(not self.removed)

    def set_removed(self, removed: bool):
        self.removed = removed
        if removed:
            self.saved_letter = self.text()
            self.setText("")
        else:
            self.setText(self.saved_letter)
        self.setReadOnly(removed)
        self.setProperty("removed", removed)
        self.style().unpolish(self)  # re-apply the stylesheet for the new look
        self.style().polish(self)
        self.removed_changed.emit()


class PathOverlay(QWidget):
    """Draws a line through the squares of a found word, on top of the grid."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.squares: list[LetterSquare] = []
        self.color = QColor(THEMES["light"]["ink"])

    def set_path(self, squares: list[LetterSquare]):
        self.squares = squares
        self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.update()

    def paintEvent(self, event):
        if len(self.squares) < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor(self.color)
        color.setAlpha(115)
        pen = QPen(color, max(3, self.squares[0].width() * 0.12))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPolyline(QPolygonF([QPointF(sq.geometry().center()) for sq in self.squares]))


class CreateGridWindow(QMainWindow):
    def __init__(self, rows: int = DEFAULT_ROWS, cols: int = DEFAULT_COLS):
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.squares: list[list[LetterSquare]] = []
        self.setWindowTitle("Wordsearch Solver")
        self.settings = QSettings("WordsearchSolver", "WordsearchSolver")
        self.theme = self.settings.value("theme") or self.system_theme()

        self.pages = QStackedWidget()
        self.grid_page = self.build_grid_page()
        self.results_page = self.build_results_page()
        self.pages.addWidget(self.grid_page)
        self.pages.addWidget(self.results_page)
        self.setCentralWidget(self.pages)

        self.build_grid()
        self.apply_theme()

    # ---------- light / dark mode ----------

    @staticmethod
    def system_theme() -> str:
        """'dark' if the operating system is set to dark mode, otherwise 'light'."""
        try:
            return "dark" if QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark else "light"
        except AttributeError:  # Qt older than 6.5 can't tell
            return "light"

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.settings.setValue("theme", self.theme)
        self.apply_theme()

    def apply_theme(self):
        colors = THEMES[self.theme]
        app = QApplication.instance()
        app.setStyle("Fusion")  # follows the palette below on every platform
        palette = QPalette()
        for role, key in [
            (QPalette.Window, "bg"), (QPalette.WindowText, "ink"),
            (QPalette.Base, "surface"), (QPalette.AlternateBase, "tile"),
            (QPalette.Text, "ink"), (QPalette.PlaceholderText, "muted"),
            (QPalette.Button, "surface"), (QPalette.ButtonText, "ink"),
            (QPalette.Highlight, "accent"), (QPalette.HighlightedText, "accent_ink"),
            (QPalette.ToolTipBase, "surface"), (QPalette.ToolTipText, "ink"),
        ]:
            palette.setColor(role, QColor(colors[key]))
        app.setPalette(palette)
        self.setStyleSheet(STYLE.substitute(colors))
        self.theme_button.setText("Light mode" if self.theme == "dark" else "Dark mode")
        self.path_overlay.color = QColor(colors["ink"])
        self.path_overlay.update()

    # ---------- grid page ----------

    def build_grid_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        size_bar = QHBoxLayout()
        self.rows_box = self.make_size_box(self.rows)
        self.cols_box = self.make_size_box(self.cols)
        size_bar.addWidget(QLabel("Rows:"))
        size_bar.addWidget(self.rows_box)
        size_bar.addSpacing(12)
        size_bar.addWidget(QLabel("Columns:"))
        size_bar.addWidget(self.cols_box)
        size_bar.addStretch()
        self.theme_button = QPushButton()
        self.theme_button.clicked.connect(self.toggle_theme)
        size_bar.addWidget(self.theme_button)
        layout.addLayout(size_bar)

        # The squares live in their own widget so it can be swapped out when the size changes.
        self.grid_holder = QVBoxLayout()
        layout.addLayout(self.grid_holder)
        self.grid_widget: QWidget | None = None

        # "Find a word" box: shown once every square has a letter.
        self.search_panel = QWidget()
        search_layout = QVBoxLayout(self.search_panel)
        search_layout.setContentsMargins(0, 8, 0, 0)
        self.search_box = QLineEdit()
        self.search_box.setObjectName("searchBox")
        self.search_box.setPlaceholderText("Find a word: type it to see its path")
        self.search_box.setValidator(QRegularExpressionValidator(QRegularExpression("[A-Za-z]*")))
        self.search_box.textChanged.connect(self.update_search)
        self.search_message = QLabel()
        self.search_message.setWordWrap(True)
        search_layout.addWidget(self.search_box)
        search_layout.addWidget(self.search_message)
        self.search_panel.setVisible(False)
        layout.addWidget(self.search_panel)

        self.solve_button = QPushButton("Solve")
        self.solve_button.setObjectName("solveButton")
        self.solve_button.clicked.connect(self.on_solve_clicked)
        self.solve_button.setVisible(False)
        layout.addWidget(self.solve_button)
        layout.addStretch()
        return page

    def make_size_box(self, current: int) -> QComboBox:
        box = QComboBox()
        for n in SIZE_CHOICES:
            box.addItem(str(n), n)
        box.setCurrentIndex(box.findData(current))
        box.currentIndexChanged.connect(self.on_size_changed)
        return box

    def on_size_changed(self):
        changed, other = (self.rows_box, self.cols_box) if self.sender() is self.rows_box else (self.cols_box, self.rows_box)
        size = changed.currentData()
        # Grids bigger than SQUARE_ONLY_ABOVE must be square, so keep the other size in step.
        if size > SQUARE_ONLY_ABOVE or other.currentData() > SQUARE_ONLY_ABOVE:
            other.blockSignals(True)
            other.setCurrentIndex(other.findData(size))
            other.blockSignals(False)
        self.rows = self.rows_box.currentData()
        self.cols = self.cols_box.currentData()
        self.build_grid()

    def build_grid(self):
        """(Re)create the squares for the current number of rows and columns."""
        if self.grid_widget is not None:
            self.grid_holder.removeWidget(self.grid_widget)
            self.grid_widget.deleteLater()

        self.grid_widget = QWidget()
        grid = QGridLayout(self.grid_widget)
        grid.setSpacing(6)
        grid.setContentsMargins(0, 0, 0, 0)
        self.squares = []
        size = self.square_size()
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                sq = LetterSquare(r, c, size)
                sq.textEdited.connect(lambda text, s=sq: self.on_letter_entered(s, text))
                sq.removed_changed.connect(self.update_solve_button)
                grid.addWidget(sq, r, c)
                row.append(sq)
            self.squares.append(row)
        self.path_overlay = PathOverlay(self.grid_widget)
        self.path_overlay.color = QColor(THEMES[self.theme]["ink"])
        self.grid_holder.addWidget(self.grid_widget, alignment=Qt.AlignCenter)

        self.update_solve_button()
        self.squares[0][0].setFocus()
        self.adjustSize()

    def square_size(self) -> int:
        """Largest square size (up to SQUARE_SIZE) that lets the whole grid fit on screen."""
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return SQUARE_SIZE
        avail = screen.availableGeometry()
        spacing = 6
        # Leave room for the window frame, the size drop-downs and the Solve button.
        fit_w = (avail.width() - 80 - spacing * (self.cols - 1)) // self.cols
        fit_h = (avail.height() - 220 - spacing * (self.rows - 1)) // self.rows
        return max(20, min(SQUARE_SIZE, fit_w, fit_h))

    def on_letter_entered(self, square: LetterSquare, text: str):
        if text:
            square.setText(text.upper())
            self.focus_next(square)
        self.update_solve_button()

    def update_solve_button(self):
        full = self.is_full()
        self.solve_button.setVisible(full)
        self.search_panel.setVisible(full)
        self.update_search()

    def update_search(self):
        """Highlight the path of the word typed in the search box, if the grid has one."""
        word = self.search_box.text().upper()
        path = find_path(self.letters(), word) if word and self.is_full() else None
        if not word or not self.is_full():
            self.search_message.setText("")
        elif path:
            r, c = path[0]
            self.search_message.setText(f"Found {word}, starting at row {r + 1}, column {c + 1}.")
        else:
            self.search_message.setText(f"{word} can't be traced through touching squares in this grid.")

        on_path = path or []
        for row in self.squares:
            for sq in row:
                pos = (sq.row, sq.col)
                value = "start" if on_path and pos == on_path[0] else "on" if pos in on_path else ""
                if sq.property("path") != value:
                    sq.setProperty("path", value)
                    sq.style().unpolish(sq)
                    sq.style().polish(sq)
        self.path_overlay.set_path([self.squares[r][c] for r, c in on_path])

    def focus_next(self, square: LetterSquare):
        """Move the cursor to the next square that hasn't been removed."""
        total = self.rows * self.cols
        index = square.row * self.cols + square.col + 1
        while index < total:
            nxt = self.squares[index // self.cols][index % self.cols]
            if not nxt.removed:
                nxt.setFocus()
                nxt.selectAll()
                return
            index += 1

    def is_full(self) -> bool:
        """True when every square that hasn't been removed has a letter (and at least one does)."""
        active = [sq for row in self.squares for sq in row if not sq.removed]
        return bool(active) and all(sq.text() for sq in active)

    def letters(self) -> list[list[str | None]]:
        """The grid's letters, with None for removed squares."""
        return [[None if sq.removed else sq.text() for sq in row] for row in self.squares]

    def on_solve_clicked(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)  # loading the word bank takes a moment
        try:
            words = solve(self.letters())
        finally:
            QApplication.restoreOverrideCursor()
        self.show_results(words)

    # ---------- results page ----------

    def build_results_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        header = QHBoxLayout()
        self.results_title = QLabel()
        self.results_title.setObjectName("resultsTitle")
        header.addWidget(self.results_title)
        header.addStretch()
        header.addWidget(QLabel("Sort:"))
        self.sort_box = QComboBox()
        self.sort_box.addItems(SORT_OPTIONS)
        self.sort_box.currentIndexChanged.connect(self.render_results)
        header.addWidget(self.sort_box)
        layout.addLayout(header)
        self.found_words: set[str] = set()

        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        layout.addWidget(self.results_scroll, stretch=1)

        back_button = QPushButton("Back to grid")
        back_button.setObjectName("backButton")
        back_button.clicked.connect(self.show_grid)
        layout.addWidget(back_button)
        return page

    def show_results(self, words: set[str]):
        self.found_words = words
        total = len(words)
        self.results_title.setText(f"Found {total} word{'s' if total != 1 else ''}")
        self.render_results()

        self.pages.setCurrentWidget(self.results_page)
        # A small grid makes a small window, so give the word list some room.
        self.resize(max(self.width(), 420), max(self.height(), 520))

    def render_results(self):
        """Fill the results list using the order picked in the Sort drop-down."""
        group_words = SORT_OPTIONS[self.sort_box.currentText()]
        groups = group_words(self.found_words)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        if not groups:
            content_layout.addWidget(QLabel("No words found in this grid."))
        for name, group in groups.items():
            title = QLabel(f"{name} ({len(group)})")
            title.setProperty("class", "groupTitle")
            words_label = QLabel(", ".join(group))
            words_label.setWordWrap(True)
            words_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            content_layout.addWidget(title)
            content_layout.addWidget(words_label)
        content_layout.addStretch()
        self.results_scroll.setWidget(content)  # replaces (and deletes) the previous results

    def show_grid(self):
        self.pages.setCurrentWidget(self.grid_page)
