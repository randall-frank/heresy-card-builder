#
# T.I.M.E Stories card editor
# Copyright (C) 2017 Randall Frank
# See LICENSE for details
#

import argparse
import sys
from PyQt5 import QtWidgets
from card_editor_main import CardEditorMain
import platform

__version__ = "0.1.0.0"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Edit/process T.I.M.E Stories cards from art assets.')
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('cardfile', nargs='?', default=None, help='The name of a saved project.')
    args = parser.parse_args()
    # bootstrap Qt
    app = QtWidgets.QApplication(sys.argv)
    app.lastWindowClosed.connect(app.quit)

    # Windows specific for taskbar icons
    if platform.system().startswith("Wind"):
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("card.editor")

    main_win = CardEditorMain(__version__)
    main_win.show()
    if args.cardfile:
        print("Reading {}\n".format(args.cardfile))
    sys.exit(app.exec_())
