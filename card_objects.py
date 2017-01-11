#
# T.I.M.E Stories card editor
# Copyright (C) 2017 Randall Frank
# See LICENSE for details
#

from PyQt5 import QtXml

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

    @classmethod
    def from_element(cls, elem):
        return None

    def to_element(self, doc, elem):
        return True


class File(Base):
    def __init__(self, name):
        super(File, self).__init__(name, 'file')

    @classmethod
    def from_element(cls, elem):
        return None

    def to_element(self, doc, elem):
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
        self.base = list()  # of Cards
        self.plan = list()  # of Cards
        self.items = list()  # of Cards
        self.reference = Card("Icon Reference", xml_tag='iconreference')
        self.characters = list()  # of Cards
        self.locations = list()  # of Locations

    def save(self, filename):
        doc = QtXml.QDomDocument()
        root = doc.createElement('deck')
        doc.appendChild(root)
        # single objects
        # lists
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
            assets = deck.firstChildElement("assets")
            if not assets.isNull():
                if not self.parse_assets(assets):
                    return False
            cards = deck.firstChildElement("cards")
            if not cards.isNull():
                if not self.parse_cards(cards):
                    return False
        return True

    def parse_cards(self, root):
        # default cards (layering) and the reference card
        # single cards
        work = dict(defaultcard=[Card, 'default_card'],
                    defaultitemcard=[Card, 'default_item_card'],
                    defaultlocationcard=[Card, 'default_location_card'],
                    iconreference=[Card, 'reference'])
        for tag, v in work.items():
            tmp = root.firstChildElement(tag)
            if not tmp.isNull():
                tmp_obj = v[0].from_element(tmp)
                if tmp_obj is not None:
                    tmp_obj.set_xml_name(tag)
                    self.__setattr__(v[1], tmp_obj)

        # Plan, Items, Base, Characters, Locations - simple lists
        work = dict(plan=[Card, 'plan'],
                    items=[Card, 'items'],
                    base=[Card, 'base'],
                    characters=[Card, 'characters'],
                    locations=[Location, 'locations'])
        for tag, v in work.items():
            tmp_root = root.firstChildElement(tag)
            if not tmp_root.isNull():
                self.__setattr__(v[1], list())
                tmp = tmp_root.firstChildElement('card')
                while not tmp.isNull():
                    tmp_obj = v[0].from_element(tmp)
                    if tmp_obj is not None:
                        self.__getattribute__(v[1]).append(tmp_obj)
                    tmp = tmp.nextSiblingElement('card')

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
# 			<defaultitemcard>
# 				<top>
# 					<image name="top"></image>
# 					<textblock name="locationname"></textblock>
# 				</top>
# 				<bottom>
# 					<image name="bottom"></image>
# 				</bottom>
# 			</defaultitemcard>
# 			<defaultlocationcard>
# 				<top>
# 					<image name="top"></image>
# 					<textblock name="locationname"></textblock>
# 				</top>
# 				<bottom>
# 					<image name="bottom"></image>
# 				</bottom>
# 			</defaultlocationcard>
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
