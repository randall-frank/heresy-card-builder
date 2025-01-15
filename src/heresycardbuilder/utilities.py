#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#

import logging
import os

from PySide6 import QtCore


def qt_message_handler(mode, context, message) -> None:
    if "warning: iCCP" in message:
        return
    if mode == QtCore.QtInfoMsg:
        logging.info(message)
    elif mode == QtCore.QtWarningMsg:
        logging.debug(message)
    elif mode == QtCore.QtCriticalMsg:
        logging.critical(message)
    elif mode == QtCore.QtFatalMsg:
        logging.critical(message)
    else:
        logging.debug(message)
    # print("%s: %s (%s:%d, %s)" % (mode, message, context.file, context.line, context.file))


def is_directory(pathname: str, empty: bool = False) -> bool:
    """
     Check to see if the pathname is indeed an existing directory.

     Parameters
     ----------
     pathname: str
         The pathname to verify is a directory.
     empty: bool
         If True, check to see if the directory is empty as well.

     Returns
    --------
     bool
         True if it is a directory and has the appropriate "empty" status.
    """
    if not os.path.isdir(pathname):
        return False
    if empty:
        if any(os.scandir(pathname)):
            return False
    return True
