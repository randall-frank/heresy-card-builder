#
# T.I.M.E Stories card generator
# Copyright (C) Randall Frank
# See LICENSE for details
#

import os.path
from PyQt5 import QtGui
from PyQt5 import QtCore


def generate_tts(render):

    num = 0
    while True:
        s = "card_bot_{:03}.png".format(num)
        tmp = os.path.join(render.outdir, s)
        if os.path.exists(tmp):
            num += 1
        else:
            break
    print("Num files {}".format(num))

    w = int(945/2)
    h = int(1535/2)
    w = int(825/2)
    h = int(1425/2)

    # 150dpi
    w = render.card_size[0]*0.5
    h = render.card_size[1]*0.5

    # maximum texture size should be 5kx5k
    nx = int(5000/w)
    ny = int(5000/h)
    # and no more that 10 cards by 7 cards
    if nx > 10:
        nx = 10
    if ny > 7:
        ny = 7
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
                        tmp = os.path.join(render.outdir, s)
                        face = QtGui.QImage(tmp, "png")
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
            tmp = os.path.join(render.outdir, s)
            img.save(tmp, "png")
            print("Saving {}".format(s))
            tile += 1

    return
