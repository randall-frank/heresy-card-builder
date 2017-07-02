#
# T.I.M.E Stories card editor
# Copyright (C) 2017 Randall Frank
# See LICENSE for details
#

import base64
from PyQt5 import QtXml
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets

# these are the core objects that represent a deck of cards to the editor


class Base(object):
    def __init__(self, name, xml_tag):
        self.name = name
        self.xml_tag = xml_tag

    def get_column_info(self, col):
        return ""

    def set_xml_name(self, name):
        self.xml_tag = name

    def get_xml_name(self):
        return self.xml_tag

    def load_attrib_string(self, elem, name, default=None):
        QtWidgets.QApplication.processEvents()
        tmp = elem.firstChildElement(name)
        v = default
        if not tmp.isNull():
            v = str(tmp.text())
        if v is not None:
            self.__setattr__(name, v)

    def save_attrib_string(self, doc, parent, name):
        tmp = doc.createElement(name)
        parent.appendChild(tmp)
        s = self.__getattribute__(name)
        text = doc.createTextNode(str(s))
        tmp.appendChild(text)

    def load_attrib_int(self, elem, name, default=None):
        tmp = elem.firstChildElement(name)
        v = default
        if not tmp.isNull():
            v = int(str(tmp.text()))
        if v is not None:
            self.__setattr__(name, v)

    def save_attrib_int(self, doc, parent, name):
        self.save_attrib_string(doc, parent, name)

    def load_attrib_obj(self, elem, name, default=None):
        tmp = elem.firstChildElement(name)
        obj = default
        if not tmp.isNull():
            obj = eval(str(tmp.text()))
        if obj is not None:
            self.__setattr__(name, obj)

    def save_attrib_obj(self, doc, parent, name):
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
    def __init__(self, name, xml_tag='renderable'):
        super(Renderable, self).__init__(name, xml_tag)

    def render_object(self):
        return


class ImageRender(Renderable):
    def __init__(self, name="image"):
        super(ImageRender, self).__init__(name, 'render_image')
        self.image = ""
        self.rectangle = [0, 0, 0, 0]

    def get_column_info(self, col):
        if col != 1:
            return super(ImageRender, self).get_column_info(col)
        return "%d,%d - %d,%d" % tuple(self.rectangle)

    @classmethod
    def from_element(cls, elem):
        obj = ImageRender()
        obj.load_attrib_string(elem, "image")
        obj.load_attrib_obj(elem, "rectangle")
        return obj

    def to_element(self, doc, elem):
        self.save_attrib_string(doc, elem, "image")
        self.save_attrib_obj(doc, elem, "rectangle")
        return True


class TextRender(Renderable):
    def __init__(self, name="text"):
        super(TextRender, self).__init__(name, 'render_text')
        self.rotation = 0
        self.style = "default"
        self.rectangle = [0, 0, 0, 0]
        self.text = ""

    def get_column_info(self, col):
        if col != 1:
            return super(TextRender, self).get_column_info(col)
        return "%d,%d - %d,%d" % tuple(self.rectangle)

    @classmethod
    def from_element(cls, elem):
        obj = TextRender()
        obj.load_attrib_string(elem, "text")
        obj.load_attrib_string(elem, "style")
        obj.load_attrib_int(elem, "rotation")
        obj.load_attrib_obj(elem, "rectangle")
        return obj

    def to_element(self, doc, elem):
        self.save_attrib_string(doc, elem, "text")
        self.save_attrib_string(doc, elem, "style")
        self.save_attrib_int(doc, elem, "rotation")
        self.save_attrib_obj(doc, elem, "rectangle")
        return True


# Essentially, a Face is a list of renderable items.  Right now, text or image items
# that reference styles and images, along with content.
class Face(Base):
    def __init__(self, name):
        super(Face, self).__init__(name, name)
        self.renderables = list()   # a face is an array of Renderable instances

    @classmethod
    def from_element(cls, elem, is_top):
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
                tmp_obj = ImageRender.from_element(tmp)
            elif tag.endswith('text'):
                tmp_obj = TextRender.from_element(tmp)
            else:
                tmp_obj = None
            if tmp_obj is not None:
                obj.renderables.append(tmp_obj)
            tmp = tmp.nextSiblingElement()
        return obj

    def to_element(self, doc, elem):
        for r in self.renderables:
            r.to_xml(doc, elem)
        return True


class Card(Base):
    def __init__(self, name, xml_tag='card'):
        super(Card, self).__init__(name, xml_tag)
        self.top_face = Face('top')
        self.bot_face = Face('bottom')

    @classmethod
    def from_element(cls, elem):
        name = elem.attribute("name", "Unnamed Card")
        obj = Card(str(name))
        tmp = elem.firstChildElement("top")
        if not tmp.isNull():
            obj.top_face = Face.from_element(tmp, True)
        tmp = elem.firstChildElement("bottom")
        if not tmp.isNull():
            obj.bot_face = Face.from_element(tmp, False)
        return obj

    def to_element(self, doc, elem):
        self.top_face.to_xml(doc, elem)
        self.bot_face.to_xml(doc, elem)
        return True


class Location(Base):
    def __init__(self, name):
        super(Location, self).__init__(name, 'location')
        self.cards = list()

    @classmethod
    def from_element(cls, elem):
        name = elem.attribute("name", "Unnamed Location")
        obj = Location(str(name))
        tmp = elem.firstChildElement("card")
        while not tmp.isNull():
            tmp_card = Card.from_element(tmp)
            if tmp_card is not None:
                obj.cards.append(tmp_card)
            tmp = tmp.nextSiblingElement('card')
        return None

    def to_element(self, doc, elem):
        for c in self.cards:
            c.to_xml(doc, elem)
        return True


class Style(Base):
    def __init__(self, name):
        super(Style, self).__init__(name, 'style')
        self.typeface = ""
        self.typesize = 12
        self.fillcolor = [255, 255, 255, 255]
        self.borderthickness = 0
        self.bordercolor = [0, 0, 0, 255]
        self.textcolor = [0, 0, 0, 255]
        self.linestyle = "solid"

    @classmethod
    def from_element(cls, elem):
        name = elem.attribute("name", "Unnamed Image")
        obj = Style(str(name))
        obj.load_attrib_string(elem, "linestyle")
        obj.load_attrib_obj(elem, "fillcolor")
        obj.load_attrib_obj(elem, "bordercolor")
        obj.load_attrib_obj(elem, "textcolor")
        obj.load_attrib_int(elem, "typesize")
        obj.load_attrib_int(elem, "borderthickness")
        return obj

    def to_element(self, doc, elem):
        self.save_attrib_string(doc, elem, "linestyle")
        self.save_attrib_obj(doc, elem, "fillcolor")
        self.save_attrib_obj(doc, elem, "bordercolor")
        self.save_attrib_obj(doc, elem, "textcolor")
        self.save_attrib_int(doc, elem, "typesize")
        self.save_attrib_int(doc, elem, "borderthickness")
        return True


class Image(Base):
    def __init__(self, name):
        super(Image, self).__init__(name, 'image')
        self.file = ''
        self.rectangle = [0, 0, 0, 0]  # x,y,dx,dy
        self.usage = 'any'

    def get_column_info(self, col):
        if col != 1:
            return super(Image, self).get_column_info(col)
        return "%d,%d - %d,%d" % tuple(self.rectangle)

    @classmethod
    def from_element(cls, elem):
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

    def load_file(self, filename, name=None):
        self.image.load(filename)
        self.name = filename
        if name:
            self.name = name

    def get_column_info(self, col):
        if col != 1:
            return super(File, self).get_column_info(col)
        return "%dx%d" % tuple(self.size())

    def size(self):
        return [self.image.width(), self.image.height()]

    @classmethod
    def from_element(cls, elem):
        QtWidgets.QApplication.processEvents()
        name = elem.attribute("name", "Unnamed File")
        obj = File(name)
        # two cases: text is the file content or text is empty
        # in the latter case, try to read the 'name' as a file
        try:
            tmp = elem.text()  # get unicode string
            tmp = bytes(tmp, "UTF-8")  # convert to ASCII 8bit bytes
            s = base64.b64decode(tmp)   # decode to binary
            buffer = QtCore.QBuffer()   # do the I/O
            buffer.setData(s)
            buffer.open(QtCore.QIODevice.ReadWrite)
            if not obj.image.load(buffer, "png"):
                if not obj.image.load(obj.name):
                    return None
        except Exception as e:
            # print("Error", str(e))
            return None
        return obj

    def to_element(self, doc, elem):
        try:
            buffer = QtCore.QBuffer()
            buffer.open(QtCore.QIODevice.ReadWrite)
            self.image.save(buffer, "png")   # Do the I/O
            s = base64.b64encode(buffer.data())   # encode binary data as ASCII 8bit bytes
            tmp = s.decode(encoding="UTF-8")   # convert the ASCII 8bit sequence to Unicode
            text = doc.createTextNode(tmp)  # Add it to the DOM
            elem.appendChild(text)
            self.save_attrib_string(doc, elem, "name")
        except Exception as e:
            # print("Error", str(e))
            return False
        return True


class Deck(Base):
    def __init__(self, name=""):
        super(Deck, self).__init__(name, 'deck')
        self.files = list()  # of Files
        self.images = list()  # of Images
        self.styles = list()  # of Styles
        self.default_card = Card("Card Base", xml_tag="defaultcard")
        self.default_item_card = Card("Item Card Base", xml_tag="defaultitemcard")
        self.default_location_card = Card("Location Card Base", xml_tag="defaultlocationcard")
        self.icon_reference = Card("Icon Reference", xml_tag='iconreference')
        self.base = list()  # of Cards
        self.plan = list()  # of Cards
        self.items = list()  # of Cards
        self.characters = list()  # of Cards
        self.locations = list()  # of Locations

    def save(self, filename):
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

    def load(self, filename):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            fp = open(filename, "rb")
            xml = fp.read()
            fp.close()
        except:
            QtWidgets.QApplication.restoreOverrideCursor()
            return False
        doc = QtXml.QDomDocument()
        ok, msg, line, col = doc.setContent(xml)
        if not ok:
            QtWidgets.QApplication.restoreOverrideCursor()
            return False
        deck = doc.firstChildElement("deck")
        if not deck.isNull():
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
                tmp_obj = v[0].from_element(tmp)
                if tmp_obj is not None:
                    tmp_obj.set_xml_name(tag)
                    self.__setattr__(v[1], tmp_obj)

        # Plan, Items, Base, Characters, Locations - simple lists
        # [v0, v1, v2] use v0.from_element() to create an object starting at the tag v2
        # make a list of objects at self.{v1}
        work = dict(plan=[Card, 'plan', 'card'],
                    items=[Card, 'items', 'card'],
                    base=[Card, 'base', 'card'],
                    characters=[Card, 'characters', 'card'],
                    locations=[Location, 'locations', 'location'])
        for tag, v in work.items():
            tmp_root = root.firstChildElement(tag)
            if not tmp_root.isNull():
                self.__setattr__(v[1], list())
                tmp = tmp_root.firstChildElement(v[2])
                while not tmp.isNull():
                    tmp_obj = v[0].from_element(tmp)
                    if tmp_obj is not None:
                        self.__getattribute__(v[1]).append(tmp_obj)
                    tmp = tmp.nextSiblingElement(v[2])

        return True

    def parse_assets(self, root):
        work = dict(file=[File, self.files],
                    image=[Image, self.images],
                    style=[Style, self.styles])
        for tag, v in work.items():
            tmp = root.firstChildElement(tag)
            while not tmp.isNull():
                tmp_obj = v[0].from_element(tmp)
                if tmp_obj is not None:
                    v[1].append(tmp_obj)
                tmp = tmp.nextSiblingElement(tag)
        return True

    def to_element(self, doc, elem):  # the deck element
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
        tmp = doc.createElement("cards")
        elem.appendChild(tmp)
        # singletons
        self.default_card.to_xml(doc, tmp)
        self.default_item_card.to_xml(doc, tmp)
        self.default_location_card.to_xml(doc, tmp)
        self.icon_reference.to_xml(doc, tmp)
        # lists: base, plan, items, characters, locations
        blocks = dict(base=self.base, plan=self.plan, items=self.items,
                      characters=self.characters, locations=self.locations)
        for tag, v in blocks.items():
            tag_elem = doc.createElement(tag)  # make an element inside of <cards>
            elem.appendChild(tag_elem)
            for i in v:
                i.to_xml(doc, tag_elem)  # write all of the cards into the new element
        return True


def build_empty_deck():
    deck = Deck()
    # Load images from resources
    d = QtCore.QDir(":/default_files")
    for name in d.entryList():
        f = File(name)
        f.load_file(":/default_files/"+name, name)
        deck.files.append(f)
    # Init the default style
    # default card
    # default item card
    # default location card
    # icon reference
    # plan
    return deck

# <deck>
# 	<assets>
# 	   <file name="name">pngcontent</file>
#      <image name="name">
#   		<file>name</file>
#  			<rect_pix>x0 y0 dx dy</rect_pix>
#   		<usage>face|badge|token...</usage>
#   		</locked/>
#   	</image>
# 		<style name="name">
# 			<typeface>name</typeface>
# 			<typesize>size</typesize>
# 			<fillcolor></fillcolor>
# 			<borderthickness></borderthickness>
# 			<bordercolor></bordercolor>
# 			<textcolor></textcolor>
# 			<linestyle></linestyle>
# 		</style>
# 	</assets>
# 	<cards>
# 		<defaultcard>
# 			<top>
# 				<image name="top"></image>
# 				<textblock name="locationname"></textblock>
# 			</top>
# 			<bottom>
# 				<image name="bottom"></image>
# 			</bottom>
# 		</defaultcard>
# 		<defaultitemcard>
# 			<top>
# 				<image name="top"></image>
# 				<textblock name="locationname"></textblock>
# 			</top>
# 			<bottom>
# 				<image name="bottom"></image>
# 			</bottom>
# 		</defaultitemcard>
# 		<defaultlocationcard>
# 			<top>
# 				<image name="top"></image>
# 				<textblock name="locationname"></textblock>
# 			</top>
# 			<bottom>
# 				<image name="bottom"></image>
# 			</bottom>
# 		</defaultlocationcard>
# 		<base>
# 			<card></card>
# 			<card></card>
# 			<card></card>
# 			<card></card>
# 			<card></card>
# 		</base>
# 		<iconreference>
# 			<top></top>
#           <bottom></bottom>
# 		</iconreference>
# 		<characters>
# 			<card></card>
# 			<card></card>
# 			<card></card>
# 		</characters>
# 		<plan>
# 			<card></card>
# 			<card></card>
# 			<card></card>
# 			<card></card>
# 		</plan>
# 		<items>
# 			<card></card>
# 			<card></card>
# 		</items>
# 		<locations>
# 			<location>
# 				<card></card>
# 				<card></card>
# 				<card></card>
# 			</location>
# 			<location>
# 				<card></card>
# 				<card></card>
# 				<card></card>
# 			</location>
# 		</locations>
# 	</cards>
# </deck>
# <card name="name">
# 	<top>
# 		<render_text name="">
# 			<rotation>angle</rotation>
# 			<style>style</style>
# 			<rectangle>x y dx dy</rectangle>
# 		</render_text>
# 		<render_image name="">
# 			<image>name</image>
# 			<rectangle>x y dx dy</rectangle>
# 		</render_image>
# 	</top>
# 	<bottom>
# 	</bottom>
# </card>
