#
# T.I.M.E Stories card generator
# Copyright (C) 2017 Randall Frank
# See LICENSE for details
#

import argparse
import card_objects
import os
import os.path
import shutil
import sys
from PyQt5 import QtWidgets
from PyQt5 import QtGui

__version__ = "0.1.0.0"


class Renderer(object):
    def __init__(self, the_deck, outdir):
        self.deck = the_deck
        self.outdir = outdir
        self.scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView()
        self.view.setScene(self.scene)
        self.card_size = (945, 1535)
        self.view.setSceneRect(0, 0, self.card_size[0], self.card_size[1])
        self.scene.setSceneRect(self.view.sceneRect())
        self.image = QtGui.QImage(self.scene.sceneRect().size().toSize(), QtGui.QImage.Format_RGBA8888)
        self.painter = QtGui.QPainter(self.image)
        self.number = 1

    def render(self, face):
        self.image.fill(0)
        self.scene.render(self.painter)
        self.image.save(os.path.join(self.outdir, "card_{}_{:03}.png".format(face, self.number)))

    def make_gfx_item(self, r):
        # the big TODO
        return None

    def render_face(self, face, background, top_bottom):
        self.scene.clear()
        # generate the QGraphicsItems from the face and the background
        for renderable in face.renderables:
            gfx_item = self.make_gfx_item(renderable)
            if gfx_item is not None:
                gfx_item.setZValue(renderable.order)
                self.scene.addItem(gfx_item)
        for renderable in background.renderables:
            gfx_item = self.make_gfx_item(renderable)
            if gfx_item is not None:
                gfx_item.setZValue(renderable.order)
                self.scene.addItem(gfx_item)
        # render them to a file
        self.render(top_bottom)

    def render_card(self, the_card, the_background):
        self.render_face(the_card.top_face, the_background.top_face, "top")
        self.render_face(the_card.bot_face, the_background.bot_face, "bot")
        self.number += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate T.I.M.E Stories cards from art assets.')
    parser.add_argument('cardfile', nargs=1, help='The name of a saved project.')
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('--outdir', default=None, nargs='?', help='The name of a saved project.')
    args = parser.parse_args()

    # bootstrap Qt
    app = QtWidgets.QApplication(sys.argv)

    print("Reading {}\n".format(args.cardfile))
    filename = os.path.abspath(args.cardfile)
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
        os.mkdir(outdir)
    except:
        pass

    # set up the renderer
    render = Renderer(deck, outdir)

    # Walk all of the cards, rendering them to images
    # misc? - the catacomb attackers
    # base
    for card in deck.base:
        render.render_card(card, deck.default_card)
    # reference card
    render.render_card(deck.icon_reference, deck.default_card)
    # plan
    for card in deck.plan:
        render.render_card(card, deck.default_card)
    # items
    for card in deck.items:
        render.render_card(card, deck.default_item_card)
    # characters
    for card in deck.characters:
        render.render_card(card, deck.default_card)
    # locations
    for location in deck.locations:
        for card in location.cards:
            render.render_card(card, deck.default_location_card)

    sys.exit(0)
