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

    w = int(945/2)
    h = int(1535/2)
    nx = int(5000/w)
    ny = int(5000/h)
    count = nx*ny - 1
    dx = w*nx
    dy = h*ny

    for pp in ["top", "bot"]:
        tile = 0
        done = 0
        while done < num:
            img = QtGui.QImage(dx, dy, QtGui.QImage.Format_RGBA8888)
            p = QtGui.QPainter()
            p.begin(img)
            for y in range(ny):
                for x in range(nx):
                    if done < num:
                        s = "card_{}_{:03}.png".format(pp, done)
                        face = QtGui.QImage(s, "png")
                        print("Reading: {}".format(s))
                        # scale
                        tmp = face.scaled(w, h, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
                        # paste
                        src = QtCore.QRectF(0, 0, w, h)
                        tgt = QtCore.QRectF(x*w, y*h, w, h)
                        p.drawImage(tgt, tmp, src)
                        #
                        done += 1
            p.end()
            s = "deck_{}_{}.png".format(pp, tile)
            img.save(s, "png")
            print("Saving {}".format(s))
            tile += 1

    sys.exit(0)
