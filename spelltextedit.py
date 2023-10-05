import re
import sys
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import (QAction, QContextMenuEvent, QSyntaxHighlighter,
                           QTextCharFormat, QTextCursor)
from PySide6.QtWidgets import (QApplication, QMainWindow, QMenu,
                               QPlainTextEdit, QVBoxLayout, QWidget)

has_spell_checker = False
try:
    # python -m pip install pyspellchecker
    from spellchecker import SpellChecker

    has_spell_checker = True
except ModuleNotFoundError:
    pass


class SpellCheckHighlighter(QSyntaxHighlighter):
    wordRegEx = re.compile(r"\b([A-Za-z]{2,})\b")

    def __init__(self, *args):
        super().__init__(*args)
        self._spell = None
        self._misspelledFormat = None

    def set_speller(self, speller: SpellChecker) -> None:
        self._spell = speller

    def highlightBlock(self, text: str) -> None:
        if self._spell is None:
            return

        self._misspelledFormat = QTextCharFormat()
        self._misspelledFormat.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
        self._misspelledFormat.setUnderlineColor(Qt.red)

        for word_object in self.wordRegEx.finditer(text):
            if self._spell.unknown([word_object.group()]):
                self.setFormat(word_object.start(), word_object.end() - word_object.start(), self._misspelledFormat)


class SpellTextEdit(QPlainTextEdit):
    def __init__(self, *args):
        super().__init__(*args)
        self._highlighter = None
        self._spell = None
        if has_spell_checker:
            self._spell = SpellChecker()
            self._highlighter = SpellCheckHighlighter(self.document())
            self._highlighter.set_speller(self._spell)
        self._contextMenuCursor = None
        self._contextMenu = None

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self._contextMenu = self.createStandardContextMenu(event.pos())
        if self._spell:
            self._contextMenuCursor = self.cursorForPosition(event.pos())
            self._contextMenuCursor.select(QTextCursor.WordUnderCursor)
            word = self._contextMenuCursor.selectedText()
            if word:
                if self._spell.unknown([word]):
                    self._contextMenu.addSeparator()
                    candidates = list(self._spell.candidates(word))
                    suggest = self._spell.correction(word)
                    candidates.insert(0, candidates.pop(candidates.index(suggest)))
                    self._contextMenu.addMenu(self.create_suggestions_menu(word, candidates))
        self._contextMenu.exec(event.globalPos())

    def create_suggestions_menu(self, word: str, suggestions: List[str]) -> QMenu:
        menu = QMenu(f"Replace '{word}' with", self)
        # max of 10 suggestions
        for word in suggestions[:10]:
            action = QAction(word, self._contextMenu)
            action.triggered.connect(self.correct_word)
            menu.addAction(action)
        return menu

    def correct_word(self) -> None:
        word = self.sender().text()
        cursor = self._contextMenuCursor
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(word)
        cursor.endEditBlock()


class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._centralWidget = None
        self._layout = None
        self.setup_ui()

    def setup_ui(self):
        self.resize(500, 500)
        self.setWindowTitle("Example app")

        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)

        self._layout = QVBoxLayout(self._centralWidget)
        self._centralWidget.setLayout(self._layout)

        text_edit1 = SpellTextEdit(self._centralWidget)
        self._layout.addWidget(text_edit1)

        text_edit2 = SpellTextEdit(self._centralWidget)
        self._layout.addWidget(text_edit2)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())
