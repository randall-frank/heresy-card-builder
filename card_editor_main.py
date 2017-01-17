#
# T.I.M.E Stories card editor
# Copyright (C) 2017 Randall Frank
# See LICENSE for details
#

from PyQt5 import QtCore, QtGui, QtWidgets

from ui_card_editor_main import Ui_card_editor_main
import card_objects


class CardEditorMain(QtWidgets.QMainWindow, Ui_card_editor_main):
    def __init__(self, version, parent=None):
        super(CardEditorMain, self).__init__(parent)
        self.setupUi(self)
        self._version = version
        self._dirty = False
        self._deck = None
        self._deck_filename = None
        self.do_new()

    def do_new(self):
        if self._deck and self._dirty:
            s = "There are unsaved changes, are you sure you want to start a new deck?"
            btn = QtWidgets.QMessageBox.question(self, "Start a new deck", s)
            if btn != QtWidgets.QMessageBox.Yes:
                return
        self._deck = card_objects.build_empty_deck()
        self._deck_filename = None
        self._dirty = False
        self.lblInfo.setText("Deck: Untitled")

    def do_saveas(self):
        tmp = QtWidgets.QFileDialog.getSaveFileName(self, "Save deck as", "Untitled.deck",
                                                    "Card deck (*.deck);;All files (*)")
        if len(tmp[0]) == 0:
            return
        filename = tmp[0]
        if not self._deck.save(filename):
            QtWidgets.QMessageBox.critical(self, "Unable to save deck",
                                           "An error occurred while saving the deck")
            return
        self._dirty = False
        self._deck_filename = filename
        self.lblInfo.setText("Deck: " + filename)

    def do_save(self):
        if self._deck is None:
            return
        if self._deck_filename is None:
            self.do_saveas()
            return
        if not self._deck.save(self._deck_filename):
            QtWidgets.QMessageBox.critical(self, "Unable to save deck",
                                           "An error occurred while saving the deck")
            return
        self._dirty = False

    def do_load(self):
        if self._deck and self._dirty:
            s = "There are unsaved changes, are you sure you want to load a new deck?"
            btn = QtWidgets.QMessageBox.question(self, "Load a new deck", s)
            if btn != QtWidgets.QMessageBox.Yes:
                return
        tmp = QtWidgets.QFileDialog.getOpenFileName(self, "Save deck as", "",
                                                    "Card deck (*.deck);;All files (*)")
        if len(tmp[0]) == 0:
            return
        filename = tmp[0]
        tmp = card_objects.Deck()
        if not tmp.load(filename):
            QtWidgets.QMessageBox.critical(self, "Unable to load deck",
                                           "An error occurred while loading the deck")
            return
        self._deck = tmp
        self._deck_filename = filename
        self.lblInfo.setText("Deck: " + filename)
        self._dirty = False

    def set_dirty(self, d):
        self._dirty = d

    @QtCore.pyqtSlot()
    def do_about(self):
        s = "T.I.M.E Stories card editor\n"
        s += "Copyright (C) 2017 Randall Frank\n"
        s += "Version: " + self._version
        QtWidgets.QMessageBox.about(self, "Card Editor", s)

    def closeEvent(self, event):
        if self._dirty:
            # prompt user
            s = "There are unsaved changes, are you sure you want to quit?"
            btn = QtWidgets.QMessageBox.question(self, "Quit Card Editor", s)
            if btn != QtWidgets.QMessageBox.Yes:
                event.ignore()
                return
        event.accept()  # let the window close
