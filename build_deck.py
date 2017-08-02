#
# T.I.M.E Stories card generator
# Copyright (C) 2017 Randall Frank
# See LICENSE for details
#

import argparse
import copy
import card_objects
import os
import os.path
import shutil
import sys
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

# Bug: text word wrapping not correct yet

__version__ = "0.2.0.0"

# http://www.makeplayingcards.com
# 827x1416 - 897x1497=min size with 36pixel borders
# Tarrot card is 70mmx120mm


class Renderer(object):
    def __init__(self, the_deck, output_dir):
        self.deck = the_deck
        self.outdir = output_dir
        self.scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView()
        self.view.setScene(self.scene)
        self.card_size = (945, 1535)
        self.pad_size = 0
        self.view.setSceneRect(0, 0, self.card_size[0], self.card_size[1])
        self.scene.setSceneRect(self.view.sceneRect())
        self.image = QtGui.QImage(self.scene.sceneRect().size().toSize(), QtGui.QImage.Format_RGBA8888)
        self.painter = QtGui.QPainter(self.image)
        self.cur_location = None
        self.cur_card = None
        self.output_card_number = 0

    def pad_image(self):
        if self.pad_size == 0:
            return self.image
        w = self.image.width()
        h = self.image.height()
        s = [self.pad_size*2 + w, self.pad_size*2 + h]
        l = int((s[0] - w) / 2)
        r = int((s[0] - w) - l)
        t = int((s[1] - h) / 2)
        b = int((s[1] - h) - l)
        # ok, pad by l,r,t,b
        out = QtGui.QImage(s[0], s[1], QtGui.QImage.Format_RGBA8888)
        p = QtGui.QPainter()
        p.begin(out)
        # Paint the center rect
        src = QtCore.QRectF(0, 0, w, h)
        tgt = QtCore.QRectF(l, t, w, h)
        p.drawImage(tgt, self.image, src)
        # Top trapezoid
        src = QtCore.QRectF(0, 0, w, 1)
        f = float(l + r + 1) / float(t - 1)
        for i in range(t):
            tgt = QtCore.QRectF(l - i * f * 0.5 - 1, t - i - 1, w + f * i + 2, 1)
            p.drawImage(tgt, self.image, src)
        # Bottom trapezoid
        src = QtCore.QRectF(0, h - 1, w, 1)
        f = float(l + r + 1) / float(b - 1)
        for i in range(b):
            tgt = QtCore.QRectF(l - i * f * 0.5 - 1, t + h + i, w + f * i + 2, 1)
            p.drawImage(tgt, self.image, src)
        # Left trapezoid
        src = QtCore.QRectF(0, 0, 1, h)
        f = float(t + b + 1) / float(l - 1)
        for i in range(l):
            tgt = QtCore.QRectF(l - i - 1, t - i * f * 0.5 - 1, 1, h + f * i + 2)
            p.drawImage(tgt, self.image, src)
        # Right trapezoid
        src = QtCore.QRectF(w - 1, 0, 1, h)
        f = float(t + b + 1) / float(r - 1)
        for i in range(r):
            tgt = QtCore.QRectF(l + w + i, t - i * f * 0.5 - 1, 1, h + f * i + 2)
            p.drawImage(tgt, self.image, src)
        p.end()
        return out

    def render(self, face, number):
        self.image.fill(0)
        self.scene.render(self.painter)
        pathname = os.path.join(self.outdir, "card_{}_{:03}.png".format(face, number))
        # print("Output file: {}".format(pathname))
        img = self.pad_image()
        img.save(pathname)

    def replace_macros(self, text):
        # {XY:name} - ':name' is optional and defaults to 'current'
        # X - c=card, i=item, l=location
        # Y - N=global number, n=local number, s=string name,  A=global letter, a=local letter
        # {n} - new line
        for key in 'ciln':
            while True:
                start = text.find("{"+key)
                if start == -1:
                    break
                end = text[start:].find("}")
                if end == -1:
                    break
                macro = text[start:start+end+1]
                replacement = "{err}"
                if key == 'n':
                    replacement = "\n"
                else:
                    opt = macro[2]
                    if opt in 'NnsAa':
                        # get the referenced object
                        offset = macro.find(":")
                        # the "current" object
                        if offset == -1:
                            current = self.cur_card
                            if key == 'l':
                                current = self.cur_location
                        # by name lookup
                        else:
                            name = macro[offset+1:-1]
                            if key == 'l':
                                current = self.deck.find_location(name, default=self.cur_card)
                            elif key == 'i':
                                current = self.deck.find_item(name, default=self.cur_card)
                            else:
                                current = self.deck.find_card(name, default=self.cur_card)
                        if current is not None:
                            # we have a target card
                            if opt == 'N':
                                replacement = str(current.card_number)
                            elif opt == 'n':
                                replacement = str(current.local_card_number)
                            elif opt == 's':
                                replacement = current.name
                            elif opt == 'A':
                                replacement = chr(ord('A') + current.card_number - 1)
                            elif opt == 'a':
                                replacement = chr(ord('A') + current.local_card_number - 1)
                text = text[:start] + replacement + text[start+end+1:]
        return text

    def build_text_document(self, text, base_style, width):
        doc = QtGui.QTextDocument()
        font = self.build_font(base_style)
        doc.setDefaultFont(font)
        text_option = QtGui.QTextOption()
        if base_style.justification == "center":
            text_option.setAlignment(QtCore.Qt.AlignCenter)
        elif base_style.justification == "left":
            text_option.setAlignment(QtCore.Qt.AlignLeft)
        elif base_style.justification == "right":
            text_option.setAlignment(QtCore.Qt.AlignRight)
        else:
            text_option.setAlignment(QtCore.Qt.AlignJustify)
        text_option.setWrapMode(QtGui.QTextOption.WordWrap)
        doc.setDefaultTextOption(text_option)
        cursor = QtGui.QTextCursor(doc)
        text = self.replace_macros(text)
        # Break the text into blocks as styles change
        # {s:style_name} - pick another style
        text_format = self.build_text_format(base_style)
        while True:
            # find the next style change
            start = text.find("{s:")
            # if no more, done looping...
            if start == -1:
                break
            end = text[start:].find("}")
            if end == -1:
                break
            # send text up to the format
            cursor.insertText(text[:start], text_format)
            # update the style and the remaining text
            style = self.deck.find_style(text[start+3:start+end], default=base_style)
            text_format = self.build_text_format(style)
            text = text[start+end+1:]
        # send the remaining text in the last format
        if len(text):
            cursor.insertText(text, text_format)
        return doc

    def build_text_format(self, style):
        tf = QtGui.QTextCharFormat()
        font = self.build_font(style)
        tf.setFont(font)
        color = QtGui.QColor(style.textcolor[0],
                             style.textcolor[1],
                             style.textcolor[2],
                             style.textcolor[3])
        tf.setForeground(QtGui.QBrush(color))
        return tf

    def build_font(self, style):
        name = style.typeface
        modifiers = ""
        pos = name.find(':')
        if pos > 0:
            modifiers = name[pos+1:]
            name = name[:pos]
        font = QtGui.QFont(name)
        # typeface and size, convert points to pixels
        dpi = self.card_size[0] / 2.75  # the card is 2.75 inches wide
        # base points on 72dpi
        font.setPixelSize(style.typesize * (dpi / 72.))
        font.setBold("bold" in modifiers)
        font.setItalic("italic" in modifiers)
        return font

    def make_gfx_items(self, r):
        objs = list()
        # return a list of QGraphicsItem objects in order top to bottom
        if isinstance(r, card_objects.TextRender) or isinstance(r, card_objects.RectRender):
            width = r.rectangle[2]
            height = r.rectangle[3]
            if isinstance(r, card_objects.TextRender):
                # actual text item
                obj = QtWidgets.QGraphicsTextItem()
                base_style = self.deck.find_style(r.style)
                doc = self.build_text_document(r.text, base_style, r.rectangle[2])
                # some defaults
                obj.setDefaultTextColor(QtGui.QColor(base_style.textcolor[0],
                                                     base_style.textcolor[1],
                                                     base_style.textcolor[2],
                                                     base_style.textcolor[3]))
                obj.setDocument(doc)
                obj.setTextWidth(r.rectangle[2])
                obj.setX(r.rectangle[0])    # x,y,dx,dy
                obj.setY(r.rectangle[1])
                # compute the bounding box and snag the height for the backdrop...
                height = int(obj.boundingRect().height())
                width = int(obj.boundingRect().width())
                obj.setRotation(r.rotation)
                objs.append(obj)
                # handle the 'halo' effect
                if base_style.linestyle == 'halo':
                    offsets = [[-1, -1], [-1, 1], [1, -1], [1, 1], [0, 1], [0, -1], [1, 0], [-1, 0]]
                    tmp = copy.deepcopy(base_style.textcolor)
                    base_style.textcolor = base_style.bordercolor
                    doc = self.build_text_document(r.text, base_style, r.rectangle[2])
                    for pair in offsets:
                        obj = QtWidgets.QGraphicsTextItem()
                        obj.setDefaultTextColor(QtGui.QColor(base_style.textcolor[0],
                                                             base_style.textcolor[1],
                                                             base_style.textcolor[2],
                                                             base_style.textcolor[3]))
                        obj.setDocument(doc)
                        obj.setTextWidth(r.rectangle[2])
                        obj.setX(r.rectangle[0] + pair[0]*3)    # x,y,dx,dy
                        obj.setY(r.rectangle[1] + pair[1]*3)
                        obj.setRotation(r.rotation)
                        objs.append(obj)
                    base_style.textcolor = tmp
            # backdrop
            obj = QtWidgets.QGraphicsRectItem(r.rectangle[0], r.rectangle[1], r.rectangle[2], height)
            obj.setTransformOriginPoint(QtCore.QPointF(r.rectangle[0], r.rectangle[1]))
            color = QtGui.QColor(base_style.fillcolor[0],
                                 base_style.fillcolor[1],
                                 base_style.fillcolor[2],
                                 base_style.fillcolor[3])
            obj.setBrush(QtGui.QBrush(color))
            pen = QtGui.QPen()
            tmp = copy.deepcopy(base_style.bordercolor)
            if (base_style.borderthickness == 0) or (base_style.linestyle == 'halo'):
                tmp[3] = 0
            color = QtGui.QColor(tmp[0], tmp[1], tmp[2], tmp[3])
            pen.setColor(color)
            pen.setWidth(base_style.borderthickness)
            if base_style.linestyle == 'dash':
                pen.setStyle(QtCore.Qt.DashLine)
            elif base_style.linestyle == 'dot':
                pen.setStyle(QtCore.Qt.DotLine)
            elif base_style.linestyle == 'dashdot':
                pen.setStyle(QtCore.Qt.DashDotLine)
            obj.setPen(pen)
            obj.setRotation(r.rotation)
            objs.append(obj)
        elif isinstance(r, card_objects.ImageRender):
            image = deck.find_image(r.image)
            if image is not None:
                sub_image = image.get_image(self.deck)
                if sub_image is None:
                    print("Unable to find the reference file {} for image {}".format(image.file, r.image))
                else:
                    pixmap = QtGui.QPixmap.fromImage(sub_image)
                    obj = QtWidgets.QGraphicsPixmapItem(pixmap)
                    obj.setX(r.rectangle[0])    # x,y,dx,dy
                    obj.setY(r.rectangle[1])
                    transform = QtGui.QTransform()
                    transform.rotate(r.rotation)
                    if (r.rectangle[2] > 0) and (r.rectangle[3] > 0):
                        sx = float(r.rectangle[2])/float(sub_image.width())
                        sy = float(r.rectangle[3])/float(sub_image.height())
                        transform.scale(sx, sy)
                    obj.setTransform(transform, False)
                    objs.append(obj)
        return objs

    def render_face(self, face, background, top_bottom, number):
        self.scene.clear()
        # light blue background
        base = QtWidgets.QGraphicsRectItem(0, 0, self.card_size[0], self.card_size[1])
        base.setBrush(QtGui.QBrush(QtGui.QColor("#E0E0FF")))
        base.setZValue(-1000)
        self.scene.addItem(base)
        # generate the QGraphicsItems from the face and the background
        for renderable in face.renderables:
            z = float(renderable.order)
            gfx_items = self.make_gfx_items(renderable)
            for gfx_item in gfx_items:
                gfx_item.setZValue(z)
                z -= 0.01
                self.scene.addItem(gfx_item)
        if background is not None:
            for renderable in background.renderables:
                z = float(renderable.order)
                gfx_items = self.make_gfx_items(renderable)
                for gfx_item in gfx_items:
                    gfx_item.setZValue(z)
                    z -= 0.01
                    self.scene.addItem(gfx_item)
        # render them to a file
        self.render(top_bottom, number)

    def render_card(self, the_card, the_background):
        self.cur_card = the_card
        print("rendering card number {}: {}".format(self.output_card_number, the_card.name))
        face = None
        if the_background is not None:
            face = the_background.top_face
        self.render_face(the_card.top_face, face, "top", self.output_card_number)
        if the_background is not None:
            face = the_background.bot_face
        self.render_face(the_card.bot_face, face, "bot", self.output_card_number)
        self.output_card_number += 1

    def render_deck(self):
        self.output_card_number = 0
        # Walk all of the cards, rendering them to images
        # misc - the catacomb attackers, success/failure
        # base, items, plan, misc, characters, reference, locations
        self.deck.renumber_entities()
        # deckcards
        for card in self.deck.deckcards:
            render.render_card(card, None)
        # base
        for card in self.deck.base:
            render.render_card(card, self.deck.default_card)
        # items
        for card in self.deck.items:
            render.render_card(card, self.deck.default_item_card)
        # plan
        for card in self.deck.plan:
            render.render_card(card, self.deck.default_card)
        # misc
        for card in self.deck.misc:
            render.render_card(card, self.deck.default_card)
        # characters
        for card in self.deck.characters:
            render.render_card(card, self.deck.default_card)
        # reference card
        render.render_card(self.deck.icon_reference, self.deck.default_card)
        # locations
        for location in self.deck.locations:
            print("Rendering location {}".format(location.name))
            self.cur_location = location
            for card in location.cards:
                render.render_card(card, self.deck.default_location_card)
            self.cur_location = None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate T.I.M.E Stories cards from art assets.')
    parser.add_argument('cardfile', nargs=1, help='The name of a saved project.')
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('--outdir', default=None, nargs='?', help='The name of a saved project.')
    parser.add_argument('--pad_width', default=[0], nargs=1, help="Extra border padding for printing.")
    parser.add_argument('--default_deck', default=None, metavar='dirname', nargs='*',
                        help='Create new deck from images in directories')
    args = parser.parse_args()

    # bootstrap Qt
    app = QtWidgets.QApplication(sys.argv)

    if args.default_deck is not None:
        print("Building deck {}...".format(args.cardfile[0]))
        deck = card_objects.build_empty_deck(media_dirs=args.default_deck)
        deck.save(args.cardfile[0])
        sys.exit(0)
    print("Reading {}...".format(args.cardfile[0]))
    filename = os.path.abspath(args.cardfile[0])
    directory = os.path.dirname(filename)
    os.chdir(directory)
    outdir = directory
    if args.outdir is not None:
        outdir = args.outdir
    deck = card_objects.Deck()
    if not deck.load(filename):
        print("Unable to read the file: {}\n".format(filename))
        sys.exit(1)
    # remove and set up the output directory
    outdir = os.path.join(outdir, "generated_cards")
    try:
        shutil.rmtree(outdir)
    except:
        pass
    try:
        os.mkdir(outdir)
    except Exception as e:
        print("Unable to create output directory {} : {}".format(outdir, str(e)))
        sys.exit(1)

    # set up the renderer
    render = Renderer(deck, outdir)
    render.pad_size = int(args.pad_width[0])
    render.render_deck()

    sys.exit(0)
