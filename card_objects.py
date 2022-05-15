#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#

import base64
import os
import os.path
from PySide6 import QtXml
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets
from typing import List, Optional, Tuple

# these are the core objects that represent a deck of cards to the editor


class Base(object):
    def __init__(self, name: str, xml_tag: str):
        self.name = name
        self.xml_tag = xml_tag

    def __str__(self):
        return f"Core object: '{self.name}'  class: {self.__class__}"

    def get_column_info(self, col: int) -> str:
        return ""

    def set_xml_name(self, name: str):
        self.xml_tag = name

    def get_xml_name(self) -> str:
        return self.xml_tag

    def load_attrib_string(self, elem, name: str, default: Optional[str] = None):
        QtWidgets.QApplication.processEvents()
        tmp = elem.firstChildElement(name)
        v = default
        if not tmp.isNull():
            v = str(tmp.text())
        if v is not None:
            self.__setattr__(name, v)

    def save_attrib_string(self, doc, parent, name: str):
        tmp = doc.createElement(name)
        parent.appendChild(tmp)
        s = self.__getattribute__(name)
        text = doc.createTextNode(str(s))
        tmp.appendChild(text)

    def load_attrib_int(self, elem, name, default: Optional[int] = None):
        tmp = elem.firstChildElement(name)
        v = default
        if not tmp.isNull():
            try:
                v = int(str(tmp.text()))
            except ValueError:
                v = default
        if v is not None:
            self.__setattr__(name, v)

    def save_attrib_int(self, doc, parent, name: str):
        self.save_attrib_string(doc, parent, name)

    def load_attrib_float(self, elem, name: str, default=None):
        tmp = elem.firstChildElement(name)
        v = default
        if not tmp.isNull():
            try:
                v = float(str(tmp.text()))
            except ValueError:
                v = default
        if v is not None:
            self.__setattr__(name, v)

    def save_attrib_float(self, doc, parent, name: str):
        self.save_attrib_string(doc, parent, name)

    def load_attrib_obj(self, elem, name: str, default=None):
        tmp = elem.firstChildElement(name)
        obj = default
        if not tmp.isNull():
            obj = eval(str(tmp.text()))
        if obj is not None:
            self.__setattr__(name, obj)

    def save_attrib_obj(self, doc, parent, name: str):
        tmp = doc.createElement(name)
        parent.appendChild(tmp)
        obj = self.__getattribute__(name)
        text = doc.createTextNode(obj.__repr__())
        tmp.appendChild(text)

    def to_xml(self, doc, parent):
        QtWidgets.QApplication.processEvents()
        tmp = doc.createElement(self.xml_tag)
        tmp.setAttribute('name', self.name)
        parent.appendChild(tmp)
        return self.to_element(doc, tmp)

    def to_element(self, doc, elem):
        return True


class Renderable(Base):
    def __init__(self, name: str, xml_tag: str = 'renderable'):
        super(Renderable, self).__init__(name, xml_tag)
        self.order: float = 0.  # Z depth...  higher values on top of lower values
        self.underlay: int = 0   # Z below 0
        self.rotation: int = 0
        self.rectangle: List[int, int, int, int] = [0, 0, -1, -1]
        # the list of QGraphicsItem objects that make up this instance
        self.gfx_list: List[QtWidgets.QGraphicsItem] = list()
        self.name: str = "unknown"

    def render_object(self):
        return

    def set_gfx_depths(self):
        # Within a renderable there may be multiple graphics items.
        # The z value will be in the physical order in the gfx_list,
        # first items will be on top.  Returns the top and bottom orders
        z = float(self.order)
        for item in self.gfx_list:
            item.setZValue(z)
            z -= 0.001


class ImageRender(Renderable):
    def __init__(self, name: str = "image"):
        super(ImageRender, self).__init__(name, 'render_image')
        self.image = ""
        self.name = "Image"

    def get_column_info(self, col: int):
        if col != 1:
            return super(ImageRender, self).get_column_info(col)
        return "%d,%d - %d,%d" % tuple(self.rectangle)

    @classmethod
    def from_element(cls, elem, deck):
        obj = ImageRender()
        obj.load_attrib_string(elem, "image")
        obj.load_attrib_obj(elem, "rectangle")
        obj.load_attrib_int(elem, "rotation")
        obj.load_attrib_float(elem, "order")
        underlay = 0
        if obj.order < 0:
            underlay = 1
        obj.load_attrib_int(elem, "underlay", default=underlay)
        return obj

    def to_element(self, doc, elem):
        self.save_attrib_string(doc, elem, "image")
        self.save_attrib_int(doc, elem, "rotation")
        self.save_attrib_obj(doc, elem, "rectangle")
        self.save_attrib_float(doc, elem, "order")
        self.save_attrib_int(doc, elem, "underlay")
        return True


class TextRender(Renderable):
    def __init__(self, name="text"):
        super(TextRender, self).__init__(name, 'render_text')
        self.style = "default"
        self.text = ""
        self.name = "Text Box"

    def get_column_info(self, col) -> str:
        if col != 1:
            return super(TextRender, self).get_column_info(col)
        return "%d,%d - %d,%d" % tuple(self.rectangle)

    @classmethod
    def from_element(cls, elem, deck):
        obj = TextRender()
        obj.load_attrib_string(elem, "text")
        obj.load_attrib_string(elem, "style")
        obj.load_attrib_int(elem, "rotation")
        obj.load_attrib_obj(elem, "rectangle")
        obj.load_attrib_float(elem, "order")
        underlay = 0
        if obj.order < 0:
            underlay = 1
        obj.load_attrib_int(elem, "underlay", default=underlay)
        return obj

    def to_element(self, doc, elem):
        self.save_attrib_string(doc, elem, "text")
        self.save_attrib_string(doc, elem, "style")
        self.save_attrib_int(doc, elem, "rotation")
        self.save_attrib_obj(doc, elem, "rectangle")
        self.save_attrib_float(doc, elem, "order")
        self.save_attrib_int(doc, elem, "underlay")
        return True


class RectRender(Renderable):
    def __init__(self, name: str = "rect"):
        super(RectRender, self).__init__(name, 'render_rect')
        self.style = "default"
        self.rectangle = [10, 10, 110, 110]
        self.name = "Rectangle"

    def get_column_info(self, col: int) -> str:
        if col != 1:
            return super(RectRender, self).get_column_info(col)
        return "%d,%d - %d,%d" % tuple(self.rectangle)

    @classmethod
    def from_element(cls, elem, deck):
        obj = RectRender()
        obj.load_attrib_string(elem, "style")
        obj.load_attrib_int(elem, "rotation")
        obj.load_attrib_obj(elem, "rectangle")
        obj.load_attrib_float(elem, "order")
        underlay = 0
        if obj.order < 0:
            underlay = 1
        obj.load_attrib_int(elem, "underlay", default=underlay)
        return obj

    def to_element(self, doc, elem):
        self.save_attrib_string(doc, elem, "style")
        self.save_attrib_int(doc, elem, "rotation")
        self.save_attrib_obj(doc, elem, "rectangle")
        self.save_attrib_float(doc, elem, "order")
        self.save_attrib_int(doc, elem, "underlay")
        return True


# Essentially, a Face is a list of renderable items.  Right now, text or image items
# that reference styles and images, along with content.
class Face(Base):
    def __init__(self, name: str):
        super(Face, self).__init__(name, name)
        self.renderables: List[Renderable] = list()   # a face is an array of Renderable instances

    def recompute_renderable_order(self, background: bool = False):
        # There are two cases:  1) normal cards  2) background cards
        # When computing complete faces there are 3 rules:
        #  rule 0: [-100+] background underlay renderables
        #  rule 1: [0+] normal card renderables
        #  rule 2: [100+] background non-underlay renderables
        # For basic storage, all order values are from [0+]
        # if background is True, renumber using rules 0 and 2
        # if background is False, renumber using rule 1
        underlay = list()
        core = list()
        overlay = list()
        for r in self.renderables:
            if background:
                if r.underlay:
                    underlay.append(r)
                else:
                    overlay.append(r)
            else:
                core.append(r)

        # renumber and rebuild
        self.renderables = list()
        order = 100.
        for r in overlay:
            r.order = order
            self.renderables.append(r)
            order += 0.1
        order = 0.
        for r in core:
            r.order = order
            self.renderables.append(r)
            order += 0.1
        order = -100.
        for r in underlay:
            r.order = order
            self.renderables.append(r)
            order += 0.1

        # Now that the renderable order numbers have been set, we
        # can update the (Z) depth numbers within any renderables
        # that have been realized
        self.set_gfx_item_depths()

    def set_gfx_item_depths(self):
        # Actually set the QGraphicsItem depth values for the individual items
        # If this face is actually a non-editable background face, an order_base
        # will be passed via order_base
        for renderable in self.renderables:
            renderable.set_gfx_depths()

    @classmethod
    def from_element(cls, elem, deck, is_top):
        name = "top"
        if not is_top:
            name = "bottom"
        obj = Face(name)
        obj.set_xml_name(name)
        # walk element children... and map to 'renderables'
        obj.renderables = list()
        tmp = elem.firstChildElement()
        while not tmp.isNull():
            tag = str(tmp.tagName())
            if tag.endswith('image'):
                tmp_obj = ImageRender.from_element(tmp, deck)
            elif tag.endswith('text'):
                tmp_obj = TextRender.from_element(tmp, deck)
            elif tag.endswith('rect'):
                tmp_obj = RectRender.from_element(tmp, deck)
            else:
                tmp_obj = None
            if tmp_obj is not None:
                obj.renderables.append(tmp_obj)
            tmp = tmp.nextSiblingElement()
        # If we have renderables, we will look at the "order" fields
        if len(obj.renderables):
            # Here we rebuild the "order" fields.  We start by sorting by the
            # incoming "order" value.  When there is a tie, we try to preserve
            # the native order in the input list.  The first item in the list
            # will be on the "bottom" and will have the lowest order number.
            tmp = []
            # start with a list of tuples (order, original index, object)
            for i, v in enumerate(obj.renderables):
                tmp.append((v.order, i, v))
            tmp.sort()
            # Ok, we have the new renderable order, save it
            obj.renderables = []
            for v in tmp:
                obj.renderables.append(v[2])
            # Rebuild the "order" numbers to match the new list
            obj.recompute_renderable_order()
        return obj

    def to_element(self, doc, elem):
        for r in self.renderables:
            r.to_xml(doc, elem)
        return True


class Card(Base):
    def __init__(self, name: str, xml_tag: str = 'card', background: bool = False):
        super(Card, self).__init__(name, xml_tag)
        self.top_face: Face = Face('top')
        self.bot_face: Face = Face('bottom')
        self.card_number: int = 0
        self.local_card_number: int = 0
        self.background: bool = background  # is this a background "default" card
        self.location: Optional[Card] = None    # for location cards, the parent location
        self.background_card: Optional[Card] = None  # the background card for this card

    def is_background(self) -> bool:
        return self.background

    @classmethod
    def from_element(cls, elem, deck):
        name = elem.attribute("name", "Unnamed Card")
        obj = Card(str(name))
        tmp = elem.firstChildElement("top")
        if not tmp.isNull():
            obj.top_face = Face.from_element(tmp, deck, True)
        tmp = elem.firstChildElement("bottom")
        if not tmp.isNull():
            obj.bot_face = Face.from_element(tmp, deck, False)
        return obj

    def to_element(self, doc, elem):
        self.top_face.to_xml(doc, elem)
        self.bot_face.to_xml(doc, elem)
        return True


class Location(Base):
    def __init__(self, name: str):
        super(Location, self).__init__(name, 'location')
        self.cards: List[Card] = list()
        self.card_number: int = 0
        self.local_card_number: int = 0

    @classmethod
    def from_element(cls, elem, deck):
        name = elem.attribute("name", "Unnamed Location")
        obj = Location(str(name))
        tmp = elem.firstChildElement("card")
        while not tmp.isNull():
            tmp_card = Card.from_element(tmp, deck)
            if tmp_card is not None:
                tmp_card.location = obj
                obj.cards.append(tmp_card)
            tmp = tmp.nextSiblingElement('card')
        return obj

    def to_element(self, doc, elem):
        for c in self.cards:
            c.to_xml(doc, elem)
        return True

    def is_background(self) -> bool:
        return False


class Style(Base):
    def __init__(self, name):
        super(Style, self).__init__(name, 'style')
        self.typeface = "Arial"
        self.typesize = 12
        self.fillcolor = [255, 255, 255, 255]
        self.borderthickness = 0
        self.bordercolor = [0, 0, 0, 255]
        self.textcolor = [0, 0, 0, 255]
        self.linestyle = "solid"
        self.justification = "full"
        self.boundary_offset = 0

    @classmethod
    def from_element(cls, elem, deck):
        name = elem.attribute("name", "Unnamed Image")
        obj = Style(str(name))
        obj.load_attrib_string(elem, "typeface", "Arial")
        obj.load_attrib_string(elem, "linestyle")
        obj.load_attrib_string(elem, "justification")
        obj.load_attrib_obj(elem, "fillcolor")
        obj.load_attrib_obj(elem, "bordercolor")
        obj.load_attrib_obj(elem, "textcolor")
        obj.load_attrib_int(elem, "typesize")
        obj.load_attrib_int(elem, "borderthickness")
        obj.load_attrib_int(elem, "boundary_offset")
        return obj

    def to_element(self, doc, elem):
        self.save_attrib_string(doc, elem, "typeface")
        self.save_attrib_string(doc, elem, "linestyle")
        self.save_attrib_string(doc, elem, "justification")
        self.save_attrib_obj(doc, elem, "fillcolor")
        self.save_attrib_obj(doc, elem, "bordercolor")
        self.save_attrib_obj(doc, elem, "textcolor")
        self.save_attrib_int(doc, elem, "typesize")
        self.save_attrib_int(doc, elem, "borderthickness")
        self.save_attrib_int(doc, elem, "boundary_offset")
        return True


class Image(Base):
    def __init__(self, name: str):
        super(Image, self).__init__(name, 'image')
        self.file = ''
        self.rectangle = [0, 0, -1, -1]  # x,y,dx,dy
        self.usage = 'any'

    def get_file(self, deck: "Deck") -> "File":
        return deck.find_file(self.file)

    def get_file_image(self, deck: "Deck", mask=False) -> QtGui.QImage:
        f = deck.find_file(self.file)
        if f is None:
            image = QtGui.QImage()
            image.load(":/default_files/Default")
            return image
        img = f.get_image()
        if not mask:
            return img
        r = self.rectangle
        s = f.size()
        if r[2] == -1:
            r[2] = s[0]
        if r[3] == -1:
            r[3] = s[1]
        img = img.convertToFormat(QtGui.QImage.Format_ARGB32)
        painter = QtGui.QPainter()
        painter.begin(img)
        rect = QtCore.QRect(r[0], r[1], r[2], r[3])
        painter.fillRect(rect, QtGui.QBrush(QtGui.QColor(128, 128, 255, 128)))
        painter.end()
        return img

    def get_image(self, deck: "Deck") -> QtGui.QImage:
        f = self.get_file(deck)
        if f is None:
            image = QtGui.QImage()
            image.load(":/default_files/Default")
            return image
        w = self.rectangle[2]
        if w < 0:
            w = f.image.width()
        h = self.rectangle[3]
        if h < 0:
            h = f.image.height()
        img = f.image.copy(self.rectangle[0], self.rectangle[1], w, h)  # QImage
        return img

    def get_pixmap(self, deck) -> QtGui.QPixmap:
        image = self.get_image(deck)
        return QtGui.QPixmap.fromImage(image)

    def get_column_info(self, col) -> str:
        if col != 1:
            return super(Image, self).get_column_info(col)
        return "%d,%d - %d,%d" % tuple(self.rectangle)

    @classmethod
    def from_element(cls, elem, deck):
        name = elem.attribute("name", "Unnamed Image")
        obj = Image(str(name))
        obj.load_attrib_string(elem, "file")
        obj.load_attrib_obj(elem, "rectangle")
        obj.load_attrib_string(elem, "usage")
        return obj

    def to_element(self, doc, elem):
        self.save_attrib_string(doc, elem, "file")
        self.save_attrib_obj(doc, elem, "rectangle")
        self.save_attrib_string(doc, elem, "usage")
        return True


class File(Base):
    def __init__(self, name):
        super(File, self).__init__(name, 'file')
        self.image = QtGui.QImage()
        self.image.load(":Default")
        self.filename = ""
        self.store_inline = False

    def get_full_pathname(self, deck: "Deck") -> str:
        if self.filename.startswith(':'):
            return self.filename
        pathname = self.filename
        tmp = QtCore.QFileInfo(pathname)
        if tmp.isRelative():
            pathname = os.path.join(deck.deck_dirname, self.filename)
        return pathname

    def load_file(self, deck: "Deck", filename: str):
        try:
            if filename.startswith(':'):
                self.image.load(filename)
                self.filename = filename
            else:
                pathname = filename
                tmp = QtCore.QFileInfo(pathname)
                if tmp.isRelative():
                    pathname = os.path.join(deck.deck_dirname, filename)
                tmp = QtCore.QFileInfo(pathname)
                pathname = tmp.canonicalFilePath()
                self.image.load(pathname)
                # try to remove desk.deck_dirname from the pathname
                tmp = QtCore.QFileInfo(deck.deck_dirname)
                deck_dirname = tmp.canonicalFilePath()
                if pathname.startswith(deck_dirname):
                    pathname = pathname[len(deck_dirname)+1:]
                self.filename = pathname
        except:
            return False
        return True

    def get_image(self):
        return self.image

    def get_column_info(self, col):
        if col != 1:
            return super(File, self).get_column_info(col)
        return "%dx%d" % tuple(self.size())

    def size(self):
        return [self.image.width(), self.image.height()]

    @classmethod
    def from_element(cls, elem, deck):
        QtWidgets.QApplication.processEvents()
        name = elem.attribute("name", "Unnamed File")
        filename = elem.attribute("filename", None)
        obj = File(name)
        if filename:
            obj.filename = filename
        # two cases: text is the file content or text is empty
        # in the latter case, try to read the 'name' as a file
        try:
            tmp = elem.text()  # get unicode string
            if len(tmp) == 0:
                if not obj.load_file(deck, filename):
                    print(f"Warning, failed to load file: {filename}")
                    return None
            else:
                tmp = bytes(tmp, "UTF-8")  # convert to ASCII 8bit bytes
                s = base64.b64decode(tmp)   # decode to binary
                buffer = QtCore.QBuffer()   # do the I/O
                buffer.setData(s)
                buffer.open(QtCore.QIODevice.ReadWrite)
                if not obj.image.load(buffer, "png"):
                    if not obj.image.load(filename, name):
                        return None
        except Exception as e:
            print("File from_element Error", str(e))
            return None
        return obj

    def to_element(self, doc, elem):
        try:
            if self.store_inline:
                buffer = QtCore.QBuffer()
                buffer.open(QtCore.QIODevice.ReadWrite)
                self.image.save(buffer, "png")   # Do the I/O
                s = base64.b64encode(buffer.data())   # encode binary data as ASCII 8bit bytes
                tmp = s.decode(encoding="UTF-8")   # convert the ASCII 8bit sequence to Unicode
                text = doc.createTextNode(tmp)  # Add it to the DOM
                elem.appendChild(text)
            elem.setAttribute('filename', self.filename)
        except Exception as e:
            print("File to_element Error", str(e))
            return False
        return True


class Deck(Base):
    def __init__(self, name=""):
        super(Deck, self).__init__(name, 'deck')
        self.files: list = list()  # of Files
        self.images: list = list()  # of Images
        self.styles: list = list()  # of Styles
        self.default_card: Card = Card("Card Base", xml_tag="defaultcard", background=True)
        self.default_item_card: Card = Card("Item Card Base", xml_tag="defaultitemcard", background=True)
        self.default_location_card: Card = Card("Location Card Base", xml_tag="defaultlocationcard", background=True)
        # un-numbered cards
        self.deckcards: list = list()
        # Proper order of a deck
        self.base: list = list()  # of Cards
        self.items: list = list()  # of Cards
        self.plan: list = list()  # of Cards
        self.misc: list = list()  # of Cards
        self.characters: list = list()  # of Cards
        self.icon_reference: Card = Card("Icon Reference", xml_tag='iconreference')
        self.locations: list = list()  # of Locations
        self.card_size: list = [825, 1425]       # [945, 1535]
        # 2.75" * 300dpi = 825
        # 4.75" * 300dpi = 1425
        self.deck_filename: Optional[str] = None
        self.deck_dirname: Optional[str] = None

    def get_card_size(self) -> List[int]:
        return self.card_size

    def find_file(self, name: str, default=None) -> File:
        for f in self.files:
            if f.name == name:
                return f
        return default

    def find_image(self, name: str, default=None) -> Image:
        for i in self.images:
            if i.name == name:
                return i
        return default

    def find_style(self, name: str, default=Style("default")) -> Style:
        for s in self.styles:
            if s.name == name:
                return s
        return default

    def find_item(self, name: str, default=None) -> Card:
        for i in self.items:
            if i.name == name:
                return i
        return default

    def find_location(self, name: str, default=None) -> Location:
        for l in self.locations:
            if l.name == name:
                return l
        return default

    def find_card(self, name: str, default=None) -> Card:
        for chunk in [self.base, self.items, self.plan, self.misc, self.characters, self.deckcards]:
            for card in chunk:
                if card.name == name:
                    return card
        if self.icon_reference.name == name:
            return self.icon_reference
        for location in self.locations:
            for card in location.cards:
                if card.name == name:
                    return card
        return default

    def renumber_entities(self):
        # set up the card numbering and fill in the background and location
        # card fields.
        local_count = 1
        for card in self.deckcards:
            card.card_number = 1
            card.local_card_number = local_count
            card.background_card = None
            card.location = None
            local_count += 1
        global_count = 1
        # card blocks
        for chunk in [self.base, self.items, self.plan, self.misc, self.characters]:
            local_count = 1
            for card in chunk:
                card.card_number = global_count
                card.local_card_number = local_count
                card.background_card = self.default_card
                if chunk == self.items:
                    card.background_card = self.default_item_card
                card.location = None
                global_count += 1
                local_count += 1
        # reference card
        self.icon_reference.card_number = global_count
        self.icon_reference.local_card_number = local_count
        self.icon_reference.background_card = self.default_card
        self.icon_reference.location = None
        global_count += 1
        local_count += 1
        # locations
        location_count = 1
        for location in self.locations:
            location.card_number = global_count
            location.local_card_number = location_count
            location_count += 1
            local_count = 1
            for card in location.cards:
                card.card_number = global_count
                card.local_card_number = local_count
                card.background_card = self.default_location_card
                card.location = location
                global_count += 1
                local_count += 1

    def save(self, filename: str) -> bool:
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        doc = QtXml.QDomDocument()
        # build the DOM
        self.to_xml(doc, doc)
        # convert the DOM to a string
        s = doc.toString()
        success = True
        try:
            fp = open(filename, "wb")
            fp.write(bytes(s, "UTF-8"))
            fp.close()
        except Exception as e:
            success = False
        QtWidgets.QApplication.restoreOverrideCursor()
        return success

    def load(self, filename: str) -> bool:
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            fp = open(filename, "rb")
            xml = fp.read()
            fp.close()
        except:
            QtWidgets.QApplication.restoreOverrideCursor()
            return False
        self.deck_filename = filename
        self.deck_dirname = os.path.dirname(filename)
        doc = QtXml.QDomDocument()
        ok, msg, line, col = doc.setContent(xml)
        if not ok:
            print("Parsing error on line {}, column {}: {}".format(line, col, msg))
            QtWidgets.QApplication.restoreOverrideCursor()
            return False
        deck = doc.firstChildElement("deck")
        if not deck.isNull():
            decksize = deck.firstChildElement("decksize")  # the <decksize> block
            if not decksize.isNull():
                self.card_size = eval(str(decksize.text()))
            assets = deck.firstChildElement("assets")  # the <assets> block
            if not assets.isNull():
                if not self.parse_assets(assets):
                    QtWidgets.QApplication.restoreOverrideCursor()
                    return False
            cards = deck.firstChildElement("cards")  # the <cards> block
            if not cards.isNull():
                if not self.parse_cards(cards):
                    QtWidgets.QApplication.restoreOverrideCursor()
                    return False
        QtWidgets.QApplication.restoreOverrideCursor()
        return True

    def parse_cards(self, root):
        # single cards
        # default cards (layering) and the reference card
        work = dict(defaultcard=[Card, 'default_card'],
                    defaultitemcard=[Card, 'default_item_card'],
                    defaultlocationcard=[Card, 'default_location_card'],
                    iconreference=[Card, 'icon_reference'])
        for tag, v in work.items():
            tmp = root.firstChildElement(tag)
            if not tmp.isNull():
                tmp_obj = v[0].from_element(tmp, self)
                if tmp_obj is not None:
                    tmp_obj.set_xml_name(tag)
                    self.__setattr__(v[1], tmp_obj)
                    tmp_obj.background = True

        # Plan, Items, Base, Characters, Locations - simple lists
        # [v0, v1, v2] use v0.from_element() to create an object starting at the tag v2
        # make a list of objects at self.{v1}
        work = dict(base=[Card, 'base', 'card'],
                    items=[Card, 'items', 'card'],
                    plan=[Card, 'plan', 'card'],
                    misc=[Card, 'misc', 'card'],
                    characters=[Card, 'characters', 'card'],
                    locations=[Location, 'locations', 'location'],
                    deckcards=[Card, "deckcards", "card"])
        for tag, v in work.items():
            tmp_root = root.firstChildElement(tag)
            if not tmp_root.isNull():
                self.__setattr__(v[1], list())
                tmp = tmp_root.firstChildElement(v[2])
                while not tmp.isNull():
                    tmp_obj = v[0].from_element(tmp, self)
                    if tmp_obj is not None:
                        self.__getattribute__(v[1]).append(tmp_obj)
                        tmp_obj.background = False
                    tmp = tmp.nextSiblingElement(v[2])
        return True

    def parse_assets(self, root):
        work = dict(file=[File, self.files],
                    image=[Image, self.images],
                    style=[Style, self.styles])
        for tag, v in work.items():
            tmp = root.firstChildElement(tag)
            while not tmp.isNull():
                tmp_obj = v[0].from_element(tmp, self)
                if tmp_obj is not None:
                    v[1].append(tmp_obj)
                tmp = tmp.nextSiblingElement(tag)
        return True

    def to_element(self, doc, elem):  # the deck element
        # decksize
        tmp = doc.createElement("decksize")
        elem.appendChild(tmp)
        text = doc.createTextNode(self.card_size.__repr__())
        tmp.appendChild(text)
        # assets
        tmp = doc.createElement("assets")
        elem.appendChild(tmp)
        # files, styles, images
        for f in self.files:
            f.to_xml(doc, tmp)
        for s in self.styles:
            s.to_xml(doc, tmp)
        for i in self.images:
            i.to_xml(doc, tmp)
        # cards
        card_root = doc.createElement("cards")
        elem.appendChild(card_root)
        # singletons
        self.default_card.to_xml(doc, card_root)
        self.default_item_card.to_xml(doc, card_root)
        self.default_location_card.to_xml(doc, card_root)
        self.icon_reference.to_xml(doc, card_root)
        # lists: base, items,  plan, misc, characters, locations, deckcards
        blocks = dict(base=self.base, plan=self.plan, items=self.items, misc=self.misc,
                      characters=self.characters, locations=self.locations, deckcards=self.deckcards)
        for tag, v in blocks.items():
            tag_elem = doc.createElement(tag)  # make an element inside <cards>
            card_root.appendChild(tag_elem)
            for i in v:
                i.to_xml(doc, tag_elem)  # write all the cards into the new element
        return True


def build_empty_deck(media_dirs=None):
    deck = Deck()
    if media_dirs is None:
        # Load images from resources
        d = QtCore.QDir(":/default_files")
        for name in d.entryList():
            f = File(name)
            f.load_file(deck, ":/default_files/"+name)
            deck.files.append(f)
    else:
        for d in media_dirs:
            for root, dirs, files in os.walk(d):
                for name in files:
                    filename = os.path.join(root, name)
                    basename, ext = os.path.splitext(os.path.basename(filename))
                    if ext.lower() in [".jpg", ".png"]:
                        print("Adding image: {} ({})".format(filename, basename))
                        f = File(basename)
                        f.load_file(deck, filename)
                        deck.files.append(f)
    # a default style
    deck.styles.append(Style("default"))
    return deck

