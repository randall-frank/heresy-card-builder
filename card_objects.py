#
# T.I.M.E Stories card editor
# Copyright (C) 2017 Randall Frank
# See LICENSE for details
#

import base64
from PyQt5 import QtXml
from PyQt5 import QtGui
from PyQt5 import QtCore

# these are the core objects that represent a deck of cards to the editor


class Base(object):
    def __init__(self, name, xml_tag):
        self.name = name
        self.xml_tag = xml_tag

    def set_xml_name(self, name):
        self.xml_tag = name

    def get_xml_name(self):
        return self.xml_tag

    def to_xml(self, doc, parent):
        tmp = doc.createElement(self.xml_tag)
        tmp.setElement('name', self.name)
        parent.appendChild(tmp)
        return self.to_element(doc, tmp)

    def to_element(self, doc, elem):
        return True


class Face(Base):
    def __init__(self, name):
        super(Face, self).__init__(name, 'face')

    @classmethod
    def from_element(cls, elem, is_top):
        name = "top"
        if not is_top:
            name = "bottom"
        obj = Face(name)
        return obj

    def to_element(self, doc, elem):
        return True


class Card(Base):
    def __init__(self, name, xml_tag='card'):
        super(Card, self).__init__(name, xml_tag)
        self.top_face = Face('top')
        self.bot_face = Face('bottom')

    @classmethod
    def from_element(cls, elem):
        name = elem.attribute("name", "Unnamed Card")
        obj = Card(str(name.toLocal8Bit()))
        tmp = elem.firstChildElement("top")
        if not tmp.isNull():
            obj.top_face = Face.from_element(tmp, True)
        tmp = elem.firstChildElement("bottom")
        if not tmp.isNull():
            obj.bot_face = Face.from_element(tmp, False)
        return obj

    def to_element(self, doc, elem):
        return True


class Location(Base):
    def __init__(self, name):
        super(Location, self).__init__(name, 'location')
        self.cards = list()

    @classmethod
    def from_element(cls, elem):
        name = elem.attribute("name", "Unnamed Location")
        obj = Location(str(name.toLocal8Bit()))
        tmp = elem.firstChildElement("card")
        while not tmp.isNull():
            tmp_card = Card.from_element(tmp)
            if tmp_card is not None:
                obj.cards.append(tmp_card)
            tmp = tmp.nextSiblingElement('card')
        return None

    def to_element(self, doc, elem):
        return True


class Style(Base):
    def __init__(self, name):
        super(Style, self).__init__(name, 'style')

    @classmethod
    def from_element(cls, elem):
        return None

    def to_element(self, doc, elem):
        return True


class Image(Base):
    def __init__(self, name):
        super(Image, self).__init__(name, 'image')
        self.file = ""
        self.rect = [0, 0, 0, 0]  # x,y,dx,dy
        self.usage = 'any'

    @classmethod
    def from_element(cls, elem):
        name = elem.attribute("name", "Unnamed Image")
        obj = Image(str(name.toLocal8Bit()))
        tmp = elem.firstChildElement("file")
        if not tmp.isNull():
            obj.file = str(tmp.attribute("name", "").toLocal8Bit())
        tmp = elem.firstChildElement("rectangle")
        if not tmp.isNull():
            r = list()
            for a in ['x', 'y', 'dx', 'dy']:
                try:
                    r.append(int(tmp.attribute(a, "0").toLocal8Bit()))
                except:
                    r.append(0)
            self.rect = r
        tmp = elem.firstChildElement("usage")
        if not tmp.isNull():
            obj.usage = str(tmp.attribute("name", "any").toLocal8Bit())
        return obj

    def to_element(self, doc, elem):
        tmp = doc.createElement("file")
        elem.appendChild(tmp)
        tmp.setAttribute("name", self.file)
        tmp = doc.createElement("rectangle")
        elem.appendChild(tmp)
        tmp.setAttribute("x", self.rect[0])
        tmp.setAttribute("y", self.rect[1])
        tmp.setAttribute("dx", self.rect[2])
        tmp.setAttribute("dy", self.rect[3])
        tmp = doc.createElement("usage")
        elem.appendChild(tmp)
        tmp.setAttribute("name", self.usage)
        return True


class File(Base):
    def __init__(self, name):
        super(File, self).__init__(name, 'file')
        self.image = QtGui.QImage()

    def load_file(self, filename):
        self.image.load(filename)
        self.name = filename

    @classmethod
    def from_element(cls, elem):
        name = elem.attribute("name", "Unnamed File")
        obj = File(str(name.toLocal8Bit()))
        s = base64.b64decode(str(elem.text().toLocal8Bit()))
        buffer = QtCore.QBuffer()
        buffer.setData(s)
        buffer.open(QtCore.QIODevice.ReadWrite)
        obj.image.load(buffer, "png")
        return obj

    def to_element(self, doc, elem):
        buffer = QtCore.QBuffer()
        buffer.open(QtCore.QIODevice.ReadWrite)
        self.image.save(buffer, "png")
        s = base64.b64encode(buffer.data())
        text = doc.createTextNode(s)
        elem.appendChild(text)
        return True


class Deck(Base):
    def __init__(self, name=""):
        super(Deck, self).__init__(name, 'deck')
        self.files = list()  # of Files
        self.images = list()  # of Images
        self.styles = list()  # of Styles
        self.default_card = Card("defaultcard", xml_tag="defaultcard")
        self.default_item_card = Card("defaultitemcard", xml_tag="defaultitemcard")
        self.default_location_card = Card("defaultlocationcard", xml_tag="defaultlocationcard")
        self.icon_reference = Card("Icon Reference", xml_tag='iconreference')
        self.base = list()  # of Cards
        self.plan = list()  # of Cards
        self.items = list()  # of Cards
        self.characters = list()  # of Cards
        self.locations = list()  # of Locations

    def save(self, filename):
        doc = QtXml.QDomDocument()
        # build the DOM
        self.to_xml(doc, doc)
        # convert the DOM to a string
        s = doc.toString().toUtf8()
        try:
            fp = open(filename, "wb")
            fp.write(s)
            fp.close()
        except:
            return False
        return True

    def load(self, filename):
        try:
            fp = open(filename, "rb")
            xml = fp.read()
            fp.close()
        except:
            return False
        doc = QtXml.QDomDocument()
        ok, msg, line, col = doc.setContent(xml)
        if not ok:
            return False
        deck = doc.firstChildElement("deck")
        if not deck.isNull():
            assets = deck.firstChildElement("assets")  # the <assets> block
            if not assets.isNull():
                if not self.parse_assets(assets):
                    return False
            cards = deck.firstChildElement("cards")  # the <cards> block
            if not cards.isNull():
                if not self.parse_cards(cards):
                    return False
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
        for tag, v in blocks:
            tag_elem = doc.createElement(tag)  # make an element inside of <cards>
            elem.appendChild(tag_elem)
            for i in v:
                i.to_xml(doc, tag_elem)  # write all of the cards into the new element
        return True

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
# 		<textblock name="">
# 			<rotation>angle</rotation>
# 			<style>style</style>
# 			<location>x y dx dy</location>
# 		</textblock>
# 		<image name="">
# 			<image>name</image>
# 			<location>x y dx dy</location>
# 		</image>
# 	</top>
# 	<bottom>
# 	</bottom>
# </card>
