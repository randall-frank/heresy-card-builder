#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#

import logging
from PySide6 import QtCore


def qt_message_handler(mode, context, message):
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
