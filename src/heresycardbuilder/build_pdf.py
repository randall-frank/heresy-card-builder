#
# T.I.M.E Stories card generator
# Copyright (C) Randall Frank
# See LICENSE for details
#

import logging
import os
import os.path

from PySide6 import QtCore, QtGui


def do_card(p, num, w, h, xoffset, yoffset, top, renderer):
    pp = "top"
    if not top:
        pp = "bot"
    s = "card_{}_{:03}.png".format(pp, num)
    tmp = os.path.join(renderer.outdir, s)
    face = QtGui.QImage(tmp, "png")
    logging.info("Reading: {}".format(s))
    # paste
    src = QtCore.QRectF(0, 0, face.width(), face.height())
    tgt = QtCore.QRectF(xoffset, yoffset, w, h)
    p.drawImage(tgt, face, src)


def generate_pdf(renderer):
    # count the input files
    num = 0
    while True:
        s = "card_bot_{:03}.png".format(num)
        tmp = os.path.join(renderer.outdir, s)
        if os.path.exists(tmp):
            num += 1
        else:
            break
    logging.info("Num files {}".format(num))

    # Raw numbers
    w = int(945)
    h = int(1535)

    # MPC numbers
    w = int(825)
    h = int(1425)

    w = renderer.card_size[0]
    h = renderer.card_size[1]

    for pagesize, name in [(QtGui.QPageSize.Letter, "Letter"), (QtGui.QPageSize.A4, "A4")]:
        s = "deck_{}.pdf".format(name)
        tmp = os.path.join(renderer.outdir, s)
        writer = QtGui.QPdfWriter(tmp)
        writer.setPageSize(pagesize)
        writer.setResolution(300)
        writer.setCreator("build_pdf tool")

        painter = QtGui.QPainter()
        painter.begin(writer)

        r = painter.viewport()
        logging.info(
            "{} page rectangle: {} {} {} {}".format(name, r.left(), r.top(), r.width(), r.height())
        )
        pw = r.width()
        ph = r.height()
        xspace = (pw - 2 * w) / 3
        yspace = (ph - 2 * h) / 3

        done = 0
        pnum = 1
        while done < num:
            logging.info("Writing page: {}".format(pnum))

            if done + 0 < num:
                do_card(painter, done + 0, w, h, xspace, yspace, True, renderer)
            if done + 1 < num:
                do_card(painter, done + 1, w, h, 2 * xspace + w, yspace, True, renderer)
            if done + 2 < num:
                do_card(painter, done + 2, w, h, xspace, 2 * yspace + h, True, renderer)
            if done + 3 < num:
                do_card(painter, done + 3, w, h, 2 * xspace + w, 2 * yspace + h, True, renderer)
            writer.newPage()

            if done + 0 < num:
                do_card(painter, done + 0, w, h, 2 * xspace + w, yspace, False, renderer)
            if done + 1 < num:
                do_card(painter, done + 1, w, h, xspace, yspace, False, renderer)
            if done + 2 < num:
                do_card(painter, done + 2, w, h, 2 * xspace + w, 2 * yspace + h, False, renderer)
            if done + 3 < num:
                do_card(painter, done + 3, w, h, xspace, 2 * yspace + h, False, renderer)

            pnum += 1
            done += 4
            if done < num:
                writer.newPage()

        painter.end()

    return
