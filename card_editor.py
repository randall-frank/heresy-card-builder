#
# T.I.M.E Stories compatible card editor
# Copyright (C) 2017 Randall Frank
# See LICENSE for details
#

import argparse
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

import card_editor_res
from ui_card_editor_main import Ui_card_editor_main


class CardEditorMain(QtWidgets.QMainWindow, Ui_card_editor_main):
    def __init__(self, parent=None):
        super(CardEditorMain, self).__init__(parent)
        self.setupUi(self)


__version__ = "0.1.0.0"

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
        print("Reading {}".format(args.cardfile))
    sys.exit(app.exec_())
