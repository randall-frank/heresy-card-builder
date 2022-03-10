import sys
import re

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat
from PySide6.QtGui import QContextMenuEvent, QTextCursor, QAction
from PySide6.QtWidgets import QMenu, QPlainTextEdit, QWidget
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from typing import List


class SimpleAction(QAction):
    actionTriggered = Signal(str)

    def __init__(self, *args):
        super().__init__(*args)
        self.triggered.connect(self.emitTriggered)

    def emitTriggered(self) -> None:
        self.actionTriggered.emit(self.text())


class SpellCheckHighlighter(QSyntaxHighlighter):
    wordRegEx = re.compile(r"\b([A-Za-z]{2,})\b")

    def __init__(self, *args):
        super().__init__(*args)
        self._spell = None
        self._misspelledFormat = None

    def setSpeller(self, speller: object) -> None:
        self._spell = speller
        
    def highlightBlock(self, text: str) -> None:
        if not hasattr(self, "_spell"):
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
        try:
            from spellchecker import SpellChecker
            self._spell = SpellChecker()
            self._highlighter = SpellCheckHighlighter(self.document())
            self._highlighter.setSpeller(self._spell)
        except ModuleNotFoundError:
            self._highlighter = None
            self._spell = None
        self._contextMenuCursor = None
        self._contextMenu = None

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self._contextMenu = self.createStandardContextMenu(event.pos())
        if self._spell:
            self._contextMenuCursor = self.cursorForPosition(event.pos())
            self._contextMenuCursor.select(QTextCursor.WordUnderCursor)
            wordToCheck = self._contextMenuCursor.selectedText()
            if wordToCheck:
                if self._spell.unknown([wordToCheck]):
                    self._contextMenu.addSeparator()
                    candidates = list(self._spell.candidates(wordToCheck))
                    suggest = self._spell.correction(wordToCheck)
                    candidates.insert(0, candidates.pop(candidates.index(suggest)))
                    self._contextMenu.addMenu(self.createSuggestionsMenu(wordToCheck, candidates))
        self._contextMenu.exec(event.globalPos())

    def createSuggestionsMenu(self, word: str, suggestions: List[str]) -> QMenu:
        suggestionsMenu = QMenu(f"Replace '{word}' with", self)
        for word in suggestions:
            action = SimpleAction(word, self._contextMenu)
            action.actionTriggered.connect(self.correctWord)
            suggestionsMenu.addAction(action)
        return suggestionsMenu

    @Slot(str)
    def correctWord(self, word: str):
        textCursor = self._contextMenuCursor
        textCursor.beginEditBlock()
        textCursor.removeSelectedText()
        textCursor.insertText(word)
        textCursor.endEditBlock()


class Ui_MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        self.resize(500, 500)
        self.setWindowTitle("Example app")

        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)

        self.layout = QVBoxLayout(self.centralWidget)
        self.centralWidget.setLayout(self.layout)

        self.textEdit1 = SpellTextEdit(self.centralWidget)
        self.layout.addWidget(self.textEdit1)

        self.textEdit2 = SpellTextEdit(self.centralWidget)
        self.layout.addWidget(self.textEdit2)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Ui_MainWindow()
    window.show()
    sys.exit(app.exec())
