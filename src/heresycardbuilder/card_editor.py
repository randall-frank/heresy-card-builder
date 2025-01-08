#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#

import argparse
import logging
import os
import platform
import sys

from PySide6 import QtCore, QtWidgets

import heresycardbuilder
__version__ = heresycardbuilder.__version__
sys.path.append(os.path.dirname(heresycardbuilder.__file__))

from card_editor_main import CardEditorMain
from card_objects import Deck
from utilities import qt_message_handler


def run() -> None:
    parser = argparse.ArgumentParser(description="Edit/process T.I.M.E Stories cards from art assets.")
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s {version}'.format(version=__version__))
    parser.add_argument("cardfile", nargs="?", default=None, help="The name of a saved project.")
    parser.add_argument("--verbose", action="store_true", default=False, help="Enable verbose mode")
    parser.add_argument("--logfile", default=None, help="Save console output to the specified file")
    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    logging.basicConfig(filename=args.logfile, level=log_level, format="%(levelname)s: %(message)s")

    # bootstrap Qt
    os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=0"
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
        logging.info("Reading {}\n".format(args.cardfile))
        tmp = Deck()
        if not tmp.load(args.cardfile):
            logging.info("Error: Unable to read deck: {}\n".format(args.cardfile))
        else:
            main_win.deck_loaded(tmp, args.cardfile)

    sys.exit(app.exec())


if __name__ == "__main__":
    run()
