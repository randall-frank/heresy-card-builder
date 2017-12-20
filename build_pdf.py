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


def do_card(p, num, w, h, xoffset, yoffset, top):
    pp = "top"
    if not top:
        pp = "bot"
    s = "card_{}_{:03}.png".format(pp, num)
    face = QtGui.QImage(s, "png")
    print("Reading: {}".format(s))
    # paste
    src = QtCore.QRectF(0, 0, face.width(), face.height())
    tgt = QtCore.QRectF(xoffset, yoffset, w, h)
    p.drawImage(tgt, face, src)


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

    # Raw numbers
    w = int(945)
    h = int(1535)

    # MPC numbers
    w = int(825)
    h = int(1425)

    writer = QtGui.QPdfWriter("deck.pdf")
    writer.setPageSize(QtGui.QPagedPaintDevice.Letter)
    #writer.setPageSize(QtGui.QPagedPaintDevice.A4)
    writer.setResolution(300)
    writer.setCreator("build_pdf tool")

    painter = QtGui.QPainter()
    painter.begin(writer)

    r = painter.viewport()
    print("rectangle: {} {} {} {}".format(r.left(), r.top(), r.width(), r.height()))
    pw = r.width()
    ph = r.height()
    xspace = (pw - 2*w)/3
    yspace = (ph - 2*h)/3

    done = 0
    pnum = 1
    while done < num:
        print("Writing page: {}".format(pnum))

        if done+0 < num:
            do_card(painter, done+0, w, h, xspace, yspace, True)
        if done+1 < num:
            do_card(painter, done+1, w, h, 2*xspace+w, yspace, True)
        if done+2 < num:
            do_card(painter, done+2, w, h, xspace, 2*yspace+h, True)
        if done+3 < num:
            do_card(painter, done+3, w, h, 2*xspace+w, 2*yspace+h, True)
        writer.newPage()

        if done+0 < num:
            do_card(painter, done+0, w, h, 2*xspace+w, yspace, False)
        if done+1 < num:
            do_card(painter, done+1, w, h, xspace, yspace, False)
        if done+2 < num:
            do_card(painter, done+2, w, h, 2*xspace+w, 2*yspace+h, False)
        if done+3 < num:
            do_card(painter, done+3, w, h, xspace, 2*yspace+h, False)

        pnum += 1
        done += 4
        if done < num:
            writer.newPage()

    painter.end()

    sys.exit(0)
