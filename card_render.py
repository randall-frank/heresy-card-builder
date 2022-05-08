#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#

import copy
import logging
import os
from typing import Optional, List

from PySide6 import QtCore, QtGui, QtWidgets

from card_objects import Deck, Card, Face, Location
from card_objects import RectRender, TextRender, ImageRender, Renderable
from card_objects import Style

from graphics_item_handles import GraphicsRectItem, GraphicsTextItem, GraphicsPixmapItem

# http://www.makeplayingcards.com
# 897x1497=min size with 36pixel safe zone
# Tarrot card is 70mmx120mm


class Renderer(object):
    def __init__(self, the_deck: Deck, output_dir: str = "", parent: QtWidgets.QWidget = None):
        self.deck: Deck = the_deck
        self.outdir: str = output_dir
        self.scene: QtWidgets.QGraphicsScene = QtWidgets.QGraphicsScene()
        self.view: QtWidgets.QGraphicsView = QtWidgets.QGraphicsView(parent)
        self.view.setScene(self.scene)
        self.card_size: List[int] = the_deck.get_card_size()
        self.pad_size: int = 0
        self.view.setSceneRect(0, 0, self.card_size[0], self.card_size[1])
        self.scene.setSceneRect(self.view.sceneRect())
        self.image: Optional[QtGui.QImage] = None
        self.painter: Optional[QtGui.QPainter] = None
        if parent is None:
            self.image = QtGui.QImage(self.scene.sceneRect().size().toSize(), QtGui.QImage.Format_RGBA8888)
            self.painter = QtGui.QPainter(self.image)
        else:
            # clear the old layout (if any)
            layout = parent.layout()
            if layout:
                for i in reversed(range(layout.count())):
                    remove = layout.itemAt(i).widget()
                    # remove it from the layout list
                    layout.removeWidget(remove)
                    # remove it from the gui
                    remove.setParent(None)
                parent.setLayout(None)
            else:
                layout = QtWidgets.QVBoxLayout()
                parent.setLayout(layout)
            layout.addWidget(self.view)
            self.view.show()
        self.output_card_number = 0
        self.target_card = None

    def pad_image(self, img: QtGui.QImage) -> QtGui.QImage:
        if self.pad_size == 0:
            return img
        w = img.width()
        h = img.height()
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
        p.drawImage(tgt, img, src)
        # Top trapezoid
        src = QtCore.QRectF(0, 0, w, 1)
        f = float(l + r + 1) / float(t - 1)
        for i in range(t):
            tgt = QtCore.QRectF(l - i * f * 0.5 - 1, t - i - 1, w + f * i + 2, 1)
            p.drawImage(tgt, img, src)
        # Bottom trapezoid
        src = QtCore.QRectF(0, h - 1, w, 1)
        f = float(l + r + 1) / float(b - 1)
        for i in range(b):
            tgt = QtCore.QRectF(l - i * f * 0.5 - 1, t + h + i, w + f * i + 2, 1)
            p.drawImage(tgt, img, src)
        # Left trapezoid
        src = QtCore.QRectF(0, 0, 1, h)
        f = float(t + b + 1) / float(l - 1)
        for i in range(l):
            tgt = QtCore.QRectF(l - i - 1, t - i * f * 0.5 - 1, 1, h + f * i + 2)
            p.drawImage(tgt, img, src)
        # Right trapezoid
        src = QtCore.QRectF(w - 1, 0, 1, h)
        f = float(t + b + 1) / float(r - 1)
        for i in range(r):
            tgt = QtCore.QRectF(l + w + i, t - i * f * 0.5 - 1, 1, h + f * i + 2)
            p.drawImage(tgt, img, src)
        p.end()
        return out

    def render(self, face: str, number: int):
        self.image.fill(0)
        self.scene.render(self.painter)
        pathname = os.path.join(self.outdir, "card_{}_{:03}.png".format(face, number))
        # print("Output file: {}".format(pathname))
        if (self.card_size[0] != 825) or (self.card_size[1] != 1425):
            # resize to 825x1425
            tmp = self.image.scaled(825, 1425, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
            img = self.pad_image(tmp)
        else:
            img = self.pad_image(self.image)
        img.save(pathname)

    def replace_macros(self, cur_card: Card, text: str):
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
                    current = cur_card
                    opt = macro[2]
                    if opt in 'NnsAa':
                        # get the referenced object
                        offset = macro.find(":")
                        # the "current" object
                        if offset == -1:
                            current = cur_card
                            if key == 'l':
                                try:
                                    current = cur_card.location
                                except AttributeError:
                                    current = None
                        # by name lookup
                        else:
                            name = macro[offset+1:-1]
                            if len(name):
                                if key == 'l':
                                    current = self.deck.find_location(name, default=cur_card)
                                elif key == 'i':
                                    current = self.deck.find_item(name, default=cur_card)
                                else:
                                    current = self.deck.find_card(name, default=cur_card)
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

    def build_text_document(self, the_card: Card, text: str, base_style: Style, width: int):
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
        text = self.replace_macros(the_card, text)
        # Break the text into blocks as styles change
        # {s:style_name} - pick another style
        text_format = self.build_text_format(base_style)
        while True:
            # find the next style change or image
            start_style = text.find("{s:")
            start_image = text.find("{I:")
            # if no more, done looping...
            if (start_style == -1) and (start_image == -1):
                break
            # a style or an image on the left?
            if (start_style > -1) and (start_image > -1):
                if start_style < start_image:
                    start_image = -1
                else:
                    start_style = -1
            # we should only have one or the other
            if start_style > -1:
                is_style = True
                start = start_style
            elif start_image > -1:
                is_style = False
                start = start_image
            else:
                is_style = False
                start = 0
            # terminator
            end = text[start:].find("}")
            if end == -1:
                break
            # send text up to the format
            cursor.insertText(text[:start], text_format)
            if is_style:
                # update the style and the remaining text
                style = self.deck.find_style(text[start+3:start+end], default=base_style)
                text_format = self.build_text_format(style)
            else:
                # parse image:dx:dy
                info = text[start+3:start+end].split(":")
                if len(info) == 3:
                    image = self.deck.find_image(info[0], default=None)
                    if image is not None:
                        image = image.get_image(self.deck)
                        if image is None:
                            logging.error("Unable to find pixels for image:".format(info[0]))
                        else:
                            try:
                                dx = int(info[1])
                                dy = int(info[2])
                            except ValueError:
                                dx = image.width()
                                dy = image.height()
                            if dx == -1:
                                dx = image.width()
                            if dy == -1:
                                dy = image.height()
                            if dx == -2:
                                dx = image.width()
                                if dy > 0:
                                    dx = int(float(dy)/float(image.height()) * float(dx))
                            if dy == -2:
                                dy = image.height()
                                if dx > 0:
                                    dy = int(float(dx)/float(image.width()) * float(dy))
                            # resize the image
                            final_image = image.scaled(dx, dy, QtCore.Qt.IgnoreAspectRatio,
                                                       QtCore.Qt.SmoothTransformation)
                            cursor.insertImage(final_image)
                else:
                    logging.error("Invalid image token: {}".format(text[start+3:start+end]))
            # remove the {} clause
            text = text[start+end+1:]
        # send the remaining text in the last format
        if len(text):
            cursor.insertText(text, text_format)
        return doc

    def build_text_format(self, style: Style):
        tf = QtGui.QTextCharFormat()
        font = self.build_font(style)
        tf.setFont(font)
        color = QtGui.QColor(style.textcolor[0],
                             style.textcolor[1],
                             style.textcolor[2],
                             style.textcolor[3])
        tf.setForeground(QtGui.QBrush(color))
        return tf

    def build_font(self, style: Style):
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
        pixel_size = style.typesize * (dpi / 72.)
        # Between Qt5 and Qt6 the default line spacing changed
        # in Qt5 the leading value is 0, in Qt6 is tends to be
        # much larger.  So if we see 0, no changes.  If we see
        # something larger, adjust by a fraction of leading()
        fm = QtGui.QFontMetrics(font)
        if fm.leading() > 0.:
            pixel_size *= (fm.height()/(fm.height() + fm.leading()*0.75))
        font.setPixelSize(pixel_size)
        font.setBold("bold" in modifiers)
        font.setItalic("italic" in modifiers)
        return font

    def update_gfx_items(self, the_card: Card, r: Renderable):
        height = r.rectangle[3]
        if isinstance(r, TextRender) or isinstance(r, RectRender):
            if isinstance(r, TextRender):
                height = self.update_text_gfx_obj(the_card, r, r.gfx_list[0], r.gfx_list[1:-1])
            obj = r.gfx_list[-1]
            self.update_rect_gfx_obj(the_card, r, obj, height=height)
        elif isinstance(r, ImageRender):
            self.update_image_gfx_obj(the_card, r, r.gfx_list[0])
        r.set_gfx_depths()

    def make_gfx_items(self, the_card: Card, r: Renderable, selectable: bool):
        objs = list()
        # return a list of QGraphicsItem objects in order top to bottom
        if isinstance(r, TextRender) or isinstance(r, RectRender):
            width = r.rectangle[2]
            height = r.rectangle[3]
            base_style = self.deck.find_style(r.style)
            if isinstance(r, TextRender):
                #obj = GraphicsTextItem(selectable)
                obj = QtWidgets.QGraphicsTextItem()
                obj.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, selectable)
                objs.append(obj)
                halo = []
                # Always create the halo items, but we might hide them
                for i in range(8):
                    halo_obj = QtWidgets.QGraphicsTextItem()
                    halo.append(halo_obj)
                    objs.append(halo_obj)
                height = self.update_text_gfx_obj(the_card, r, obj, halo)

            # backdrop (or rectangle)
            #obj = GraphicsRectItem(selectable and isinstance(r, RectRender))
            obj = QtWidgets.QGraphicsRectItem()
            obj.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, selectable and isinstance(obj, RectRender))
            self.update_rect_gfx_obj(the_card, r, obj, height=height)
            objs.append(obj)

        elif isinstance(r, ImageRender):
            #obj = GraphicsPixmapItem(selectable)
            obj = QtWidgets.QGraphicsPixmapItem()
            obj.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, selectable)
            self.update_image_gfx_obj(the_card, r, obj)
            objs.append(obj)

        objs[0].setData(0, r)
        return objs

    def update_text_gfx_obj(self, the_card: Card, r: TextRender, obj: GraphicsTextItem,
                            halo: List[QtWidgets.QGraphicsTextItem]):
        base_style = self.deck.find_style(r.style)
        doc = self.build_text_document(the_card, r.text, base_style, r.rectangle[2])
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
        # handle the 'halo' effect
        if base_style.linestyle == 'halo':
            offsets = [[-1, -1], [-1, 1], [1, -1], [1, 1], [0, 1], [0, -1], [1, 0], [-1, 0]]
            style = copy.deepcopy(base_style)
            style.textcolor = style.bordercolor
            halo_doc = self.build_text_document(the_card, r.text, style, r.rectangle[2])
            for i, offset in enumerate(offsets):
                halo[i].setVisible(True)
                halo[i].setDocument(halo_doc)
                halo[i].setDefaultTextColor(QtGui.QColor(style.textcolor[0], style.textcolor[1],
                                                         style.textcolor[2], style.textcolor[3]))
                halo[i].setTextWidth(r.rectangle[2])
                halo[i].setX(r.rectangle[0] + offset[0]*3)    # x,y,dx,dy
                halo[i].setY(r.rectangle[1] + offset[1]*3)
                halo[i].setRotation(r.rotation)
        else:
            for item in halo:
                item.setVisible(False)
        if isinstance(obj, GraphicsTextItem):
            obj.updateHandlesPos()
        return height

    def update_rect_gfx_obj(self, the_card: Card, r: RectRender, obj: QtWidgets.QGraphicsRectItem, height: Optional[int] = None):
        base_style = self.deck.find_style(r.style)
        # backdrop
        if r.rectangle[3] > 0:
            height = r.rectangle[3]
        # "outset" the rectangle by the boundary_offset
        left = r.rectangle[0] - base_style.boundary_offset
        top = r.rectangle[1] - base_style.boundary_offset
        width = r.rectangle[2] + 2*base_style.boundary_offset
        height += 2*base_style.boundary_offset
        obj.setRect(left, top, width, height)
        obj.setTransformOriginPoint(QtCore.QPointF(left, top))
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
        if isinstance(obj, GraphicsRectItem):
            obj.updateHandlesPos()

    def update_image_gfx_obj(self, the_card: Card, r: ImageRender, obj: QtWidgets.QGraphicsPixmapItem):
        image = self.deck.find_image(r.image)
        if image is not None:
            sub_image = image.get_image(self.deck)
            if sub_image is None:
                logging.error("Unable to find the reference file {} for image {}".format(image.file, r.image))
            else:
                pixmap = QtGui.QPixmap.fromImage(sub_image)
                obj.setPixmap(pixmap)
                obj.setX(r.rectangle[0])    # x,y,dx,dy
                obj.setY(r.rectangle[1])
                transform = QtGui.QTransform()
                transform.rotate(r.rotation)
                w = r.rectangle[2]
                h = r.rectangle[3]
                if w == -1:
                    w = sub_image.width()
                if h == -1:
                    h = sub_image.height()
                if w == -2:
                    w = sub_image.width()
                    if h > 0:
                        w = float(h)/float(sub_image.height()) * float(w)
                if h == -2:
                    h = sub_image.height()
                    if w > 0:
                        h = float(w)/float(sub_image.width()) * float(h)
                sx = float(w)/float(sub_image.width())
                sy = float(h)/float(sub_image.height())
                transform.scale(sx, sy)
                obj.setTransform(transform, False)
        else:
            logging.error("Unable to find the reference image {}".format(r.image))
        if isinstance(obj, GraphicsPixmapItem):
            obj.updateHandlesPos()

    def build_card_face_scene(self, the_card: Card, top_bottom: str) -> list:
        # reset the scene
        self.scene.clear()
        if the_card is None:
            return list()
        if isinstance(the_card, Location):
            return list()
        # find the background face
        the_background = the_card.background
        background_face = None
        if the_background is not None:
            if top_bottom == "top":
                background_face = the_background.top_face
            else:
                background_face = the_background.bot_face
        # Which face
        face = the_card.bot_face
        if top_bottom == "top":
            face = the_card.top_face
        # light blue background
        base = QtWidgets.QGraphicsRectItem(0, 0, self.card_size[0], self.card_size[1])
        base.setBrush(QtGui.QBrush(QtGui.QColor("#E0E0FF")))
        base.setZValue(-1000.0)
        self.scene.addItem(base)
        # generate the QGraphicsItems from the face and the background
        render_list = list()
        for renderable in face.renderables:
            renderable.gfx_list = list()
            render_list.append(renderable)
            gfx_items = self.make_gfx_items(the_card, renderable, True)
            for gfx_item in gfx_items:
                self.scene.addItem(gfx_item)
                renderable.gfx_list.append(gfx_item)
        # compute graphics item offsets
        face.recompute_renderable_order()
        # now the background face/gfx items
        if background_face is not None:
            # Do not add background render items to the return list
            for renderable in background_face.renderables:
                renderable.gfx_list = list()
                gfx_items = self.make_gfx_items(the_card, renderable, False)
                for gfx_item in gfx_items:
                    self.scene.addItem(gfx_item)
                    renderable.gfx_list.append(gfx_item)
            # compute the graphics item offsets using the previous depth limits
            background_face.recompute_renderable_order(background=True)
        self.scene.update(self.scene.sceneRect())
        return render_list

    def render_card_to_disk(self, the_card: Card):
        if (self.target_card is None) or (self.target_card == self.output_card_number):
            logging.info("Rendering card number {}: {}".format(self.output_card_number, the_card.name))
            self.build_card_face_scene(the_card, "top")
            self.render("top", self.output_card_number)  # render the scene to a file
            self.build_card_face_scene(the_card, "bot")
            self.render("bot", self.output_card_number)  # render the scene to a file
        self.output_card_number += 1

    def render_deck(self, target_card: int = None):
        self.output_card_number = 0
        self.target_card = target_card
        # Walk all cards, rendering them to images
        # misc - the catacomb attackers, success/failure
        # base, items, plan, misc, characters, reference, locations
        self.deck.renumber_entities()
        # deckcards
        for card in self.deck.deckcards:
            self.render_card_to_disk(card)
        # base
        for card in self.deck.base:
            self.render_card_to_disk(card)
        # items
        for card in self.deck.items:
            self.render_card_to_disk(card)
        # plan
        for card in self.deck.plan:
            self.render_card_to_disk(card)
        # misc
        for card in self.deck.misc:
            self.render_card_to_disk(card)
        # characters
        for card in self.deck.characters:
            self.render_card_to_disk(card)
        # reference card
        self.render_card_to_disk(self.deck.icon_reference)
        # locations
        for location in self.deck.locations:
            logging.info("Rendering location {}".format(location.name))
            for card in location.cards:
                self.render_card_to_disk(card)
