#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#

import argparse
import logging
import platform
import sys

from PySide6 import QtWidgets, QtCore

from card_editor_main import CardEditorMain
from utilities import qt_message_handler


__version__ = "0.3.0.0"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Edit/process T.I.M.E Stories cards from art assets.')
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('cardfile', nargs='?', default=None, help='The name of a saved project.')
    parser.add_argument('--verbose', action='store_true', default=False,  help="Enable verbose mode")
    parser.add_argument('--logfile', default=None,  help="Save console output to the specified file")
    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    logging.basicConfig(filename=args.logfile, level=log_level, format="%(levelname)s: %(message)s")

    # bootstrap Qt
    QtCore.qInstallMessageHandler(qt_message_handler)
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
    sys.exit(app.exec())
