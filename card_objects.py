#
# T.I.M.E Stories card editor
# Copyright (C) 2017 Randall Frank
# See LICENSE for details
#

import base64
import os, os.path
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

    def load_attrib_string(self, elem, name, default=None):
        tmp = elem.firstChildElement(name)
        v = default
        if not tmp.isNull():
            v = str(tmp.text().toLocal8Bit())
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
            v = int(str(tmp.text().toLocal8Bit()))
        if v is not None:
            self.__setattr__(name, v)

    def save_attrib_int(self, doc, parent, name):
        self.save_attrib_string(doc, parent, name)

    def load_attrib_obj(self, elem, name, default=None):
        tmp = elem.firstChildElement(name)
        obj = default
        if not tmp.isNull():
            obj = eval(str(tmp.text().toLocal8Bit()))
        if obj is not None:
            self.__setattr__(name, obj)

    def save_attrib_obj(self, doc, parent, name):
        tmp = doc.createElement(name)
        parent.appendChild(tmp)
        obj = self.__getattribute__(name)
        text = doc.createTextNode(obj.__repr__())
        tmp.appendChild(text)

    def to_xml(self, doc, parent):
        tmp = doc.createElement(self.xml_tag)
        tmp.setElement('name', self.name)
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
        super(Face, self).__init__(name, 'face')
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
            tag = str(tmp.tagName().toLocal8Bit())
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
        obj = Card(str(name.toLocal8Bit()))
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
        obj = Location(str(name.toLocal8Bit()))
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
        obj = Style(str(name.toLocal8Bit()))
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

    @classmethod
    def from_element(cls, elem):
        name = elem.attribute("name", "Unnamed Image")
        obj = Image(str(name.toLocal8Bit()))
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

    def load_file(self, filename):
        self.image.load(filename)
        self.name = filename

    def size(self):
        return [self.image.width(), self.image.height()]

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

# Files from the "media" subdirectory  Move this to the .qrc file???
image_list = [
    ["", "TS_ Missions_V_EN.jpg"],
    ["", "TS_ Missions_V_EN2.jpg"],
    ["", "TS_ Missions_V_EN3.jpg"],
    ["", "TS_ Missions_V_EN4.jpg"],
    ["", "TS_ Missions_V_EN5.jpg"],
    ["Success Icon", "TS_CreaPack_Icon-56.png"],
    ["Failure Icon", "TS_CreaPack_Icon-57.png"],
    ["Cancel Icon", "TS_CreaPack_Icon-59.png"],
    ["", "TS_CreaPack_Icon-65.png"],
    ["", "TS_CreaPack_Icon-66.png"],
    ["Time Icon", "TS_CreaPack_Icon-67.png"],
    ["Triple Time Icon", "TS_CreaPack_Icon-68.png"],
    ["Dice Minus One", "TS_CreaPack_Icon_-1-.png"],
    ["Blue One Token", "TS_CreaPack_Icon_-1BL--30.png"],
    ["Gray One Token", "TS_CreaPack_Icon_-1BL--50.png"],
    ["Black One Token", "TS_CreaPack_Icon_-1N-.png"],
    ["Yellow One Token", "TS_CreaPack_Icon_-1OR-.png"],
    ["Pink One Token", "TS_CreaPack_Icon_-1RO-.png"],
    ["Green One Token", "TS_CreaPack_Icon_-1V-.png"],
    ["Gray Two Token", "TS_CreaPack_Icon_-2B-.png"],
    ["Blue Two Token", "TS_CreaPack_Icon_-2BL-.png"],
    ["Black Two Token", "TS_CreaPack_Icon_-2N-.png"],
    ["Yellow Two Token", "TS_CreaPack_Icon_-2OR-.png"],
    ["Pink Two Token", "TS_CreaPack_Icon_-2RO-.png"],
    ["Green Two Token", "TS_CreaPack_Icon_-2V-.png"],
    ["Blue Three Token", "TS_CreaPack_Icon_-3BL--27.png"],
    ["Gray Three Token", "TS_CreaPack_Icon_-3BL--54.png"],
    ["Three Hits", "TS_CreaPack_Icon_-3HIT-.png"],
    ["Black Three Token", "TS_CreaPack_Icon_-3N-.png"],
    ["Yellow Three Token", "TS_CreaPack_Icon_-3OR-.png"],
    ["Pink Three Token", "TS_CreaPack_Icon_-3RO-.png"],
    ["Green Three Token", "TS_CreaPack_Icon_-3V-.png"],
    ["Gray Four Token", "TS_CreaPack_Icon_-4B-.png"],
    ["Blue Four Token", "TS_CreaPack_Icon_-4BL-.png"],
    ["", "TS_CreaPack_Icon_-4C-.png"],
    ["Black Four Token", "TS_CreaPack_Icon_-4N-.png"],
    ["Yellow Four Token", "TS_CreaPack_Icon_-4OR-.png"],
    ["Pink Four Token", "TS_CreaPack_Icon_-4RO-.png"],
    ["Green Four Token", "TS_CreaPack_Icon_-4V-.png"],
    ["Shield Shield", "TS_CreaPack_Icon_-B-.png"],
    ["Shield", "TS_CreaPack_Icon_-BB-.png"],
    ["Time Shield", "TS_CreaPack_Icon_-BCB- copie 2.png"],
    ["", "TS_CreaPack_Icon_-BCB- copie.png"],
    ["Blue Skull Shield", "TS_CreaPack_Icon_-BCB-.png"],
    ["Red Skull Shield", "TS_CreaPack_Icon_-BCR-.png"],
    ["Black Heart Shield", "TS_CreaPack_Icon_-BN-.png"],
    ["Lock Icon", "TS_CreaPack_Icon_-CAD-.png"],
    ["First Icon", "TS_CreaPack_Icon_-CC-.png"],
    ["", "TS_CreaPack_Icon_-CD-.png"],
    ["Red Skull Icon", "TS_CreaPack_Icon_-CR-.png"],
    ["Flashlight Icon", "TS_CreaPack_Icon_-F-.png"],
    ["Hit Icon", "TS_CreaPack_Icon_-FD1R-.png"],
    ["Blank Disk Icon", "TS_CreaPack_Icon_-FDV-.png"],
    ["All Players Icon", "TS_CreaPack_Icon_-GRP-.png"],
    ["Blue Ammo", "TS_CreaPack_Icon_-JB-.png"],
    ["Yellow Ammo", "TS_CreaPack_Icon_-JJ-.png"],
    ["Brown Ammo", "TS_CreaPack_Icon_-JM-.png"],
    ["Gray Ammo", "TS_CreaPack_Icon_-JN-.png"],
    ["Green Ammo", "TS_CreaPack_Icon_-JV-.png"],
    ["Red TS Logo", "TS_CreaPack_Icon_-LOGO- copie 2.png"],
    ["Gray TS Logo", "TS_CreaPack_Icon_-LOGO- copie 3.png"],
    ["Green TS Logo", "TS_CreaPack_Icon_-LOGO- copie.png"],
    ["Blue TS Logo", "TS_CreaPack_Icon_-LOGO-.png"],
    ["Agility Icon", "TS_CreaPack_Icon_-M- copie.png"],
    ["Glibness Icon", "TS_CreaPack_Icon_-M-.png"],
    ["Trash Icon", "TS_CreaPack_Icon_-P-.png"],
    ["Exclamation Icon", "TS_CreaPack_Icon_-PE-.png"],
    ["Blue Heart Icon", "TS_CreaPack_Icon_-PV-.png"],
    ["Hit Icon", "TS_CreaPack_Icon_-R-.png"],
    ["Stop Icon", "TS_CreaPack_Icon_-SI-.png"],
    ["Blue Time Icon", "TS_CreaPack_Icon_-UT-.png"],
    ["Black Time Icon", "TS_CreaPack_Icon_-UTN-.png"],
    ["Yellow Time Icon", "TS_CreaPack_Icon_-UTR- copie.png"],
    ["Red Time Icon", "TS_CreaPack_Icon_-UTR-.png"],
    ["Location A Outline", "TS_CreaPack_Lieu-01.png"],
    ["Location B Outline", "TS_CreaPack_Lieu-02.png"],
    ["Location C Outline", "TS_CreaPack_Lieu-03.png"],
    ["Location D Outline", "TS_CreaPack_Lieu-04.png"],
    ["Item Outline", "TS_CreaPack_Lieu-05.png"],
    ["Plan Outline", "TS_CreaPack_Lieu-06.png"],
    ["Mission Success", "TS_CreaPack_Lieu-07.png"],
    ["Mission Failed (TU)", "TS_CreaPack_Lieu-08.png"],
    ["Mission Failed", "TS_CreaPack_Lieu-09.png"],
]


def build_empty_deck(root):
    d = Deck()
    # Load images
    for v in image_list:
        path = os.path.join(root, v[1])
        f = File(v[0])
        f.load_file(path)
        d.files.append(f)
    # Init the default style
    # default card
    # default item card
    # default location card
    # icon reference
    # plan
    return d

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
