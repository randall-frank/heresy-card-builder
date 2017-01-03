#
# T.I.M.E Stories card editor
# Copyright (C) 2017 Randall Frank
# See LICENSE for details
#

from PyQt5 import QtXml

# these are the core objects that represent a deck of cards to the editor


class Base(object):
    def __init__(self, name):
        self.name = name


class Face(Base):
    def __init__(self):
        super(Face, self).__init__("face")


class Card(Base):
    def __init__(self, name):
        super(Card, self).__init__(name)
        self.top_face = Face()
        self.bot_face = Face()


class Location(Base):
    def __init__(self, name):
        super(Location, self).__init__(name)


class Style(Base):
    def __init__(self, name):
        super(Style, self).__init__(name)

    @classmethod
    def from_element(cls, elem):
        return None


class Image(Base):
    def __init__(self, name):
        super(Image, self).__init__(name)

    @classmethod
    def from_element(cls, elem):
        return None


class File(Base):
    def __init__(self, name):
        super(File, self).__init__(name)

    @classmethod
    def from_element(cls, elem):
        return None


class Deck(Base):
    def __init__(self, name=""):
        super(Deck, self).__init__(name)
        self.files = []
        self.images = []
        self.styles = []
        self.default_card = Card("default")
        self.base = []
        self.plan = []
        self.items = []
        self.reference = Card("Icon Reference")
        self.characters = []
        self.locations = []

    def load(self, filename):
        try:
            fp = open(filename, "rb")
            xml = fp.read()
            fp.close()
        except:
            return False
        doc = QtXml.QDomComment()
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
        # Locations
        # Plan
        # Items
        # Base
        # Icon Reference
        # Characters
        return True

    def parse_assets(self, root):
        work = dict(file=[File, self.files],
                    image=[Image, self.images],
                    style=[Style, self.styles])
        for tag, v in work.iteritems():
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
# 		<base>
# 			<card></card>
# 			<card></card>
# 			<card></card>
# 			<card></card>
# 			<card></card>
# 		</base>
# 		<reference>
# 			<card></card>
# 		</reference>
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
# 			<defaultcard>
# 				<top>
# 					<image name="top"></image>
# 					<textblock name="locationname"></textblock>
# 				</top>
# 				<bottom>
# 					<image name="bottom"></image>
# 				</bottom>
# 			</defaultcard>
# 			<card></card>
# 			<card></card>
# 		</items>
# 		<locations>
# 			<defaultcard>
# 				<top>
# 					<image name="top"></image>
# 					<textblock name="locationname"></textblock>
# 				</top>
# 				<bottom>
# 					<image name="bottom"></image>
# 				</bottom>
# 			</defaultcard>
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
