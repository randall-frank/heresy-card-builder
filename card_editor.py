#
# T.I.M.E Stories compatible card editor
# Copyright (C) 2017 Randall Frank
# See LICENSE for details
#

import argparse
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

import card_editor_res_rc
from ui_card_editor_main import Ui_card_editor_main

__version__ = "0.1.0.0"


class CardEditorMain(QtWidgets.QMainWindow, Ui_card_editor_main):
    def __init__(self, parent=None):
        super(CardEditorMain, self).__init__(parent)
        self.setupUi(self)

    @QtCore.pyqtSlot()
    def do_about(self):
        s = "T.I.M.E Stories card editor\n"
        s += "Copyright (C) 2017 Randall Frank\n"
        s += "Version: " + __version__
        QtWidgets.QMessageBox.about(self, "Card Editor", s)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Edit/process T.I.M.E Stories cards from art assets.')
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('cardfile', nargs='?', default=None, help='The name of a saved project.')
    args = parser.parse_args()
    # bootstrap Qt
    app = QtWidgets.QApplication(sys.argv)
    app.lastWindowClosed.connect(app.quit)
    main_win = CardEditorMain()
    main_win.show()
    if args.cardfile:
        print("Reading {}\n".format(args.cardfile))
    sys.exit(app.exec_())
