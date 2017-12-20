#
# T.I.M.E Stories card generator
# Copyright (C) 2017 Randall Frank
# See LICENSE for details
#

import os
import os.path
import sys
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore


if __name__ == '__main__':

    # bootstrap Qt
    app = QtWidgets.QApplication(sys.argv)

    num = 0
    while True:
        s = "card_bot_{:03}.png".format(num)
        if os.path.exists(s):
            num += 1
        else:
            break
    print("Num files {}".format(num))

    w = int(945)
    h = int(1535)

    writer = QtGui.QPdfWriter("desk.pdf")
    writer.setPageSize(QtGui.QPagedPaintDevice.A4)
    writer.setPageMargins(QtCore.QMargins(30, 30, 30, 30))

    painter = QtGui.QPainter(writer)
    r = painter.rect()
    done = 0
    while done < num:
        done += 4
    painter.end()

    '''

                        s = "card_{}_{:03}.png".format(pp, done)
                        face = QtGui.QImage(s, "png")
                        print("Reading: {}".format(s))
                        # scale
                        tmp = face.scaled(w, h, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
                        # paste
                        src = QtCore.QRectF(0, 0, w, h)
                        tgt = QtCore.QRectF(x*w, y*h, w, h)
                        p.drawImage(tgt, tmp, src)
    '''
    sys.exit(0)
