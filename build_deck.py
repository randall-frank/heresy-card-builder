#
# T.I.M.E Stories card generator
# Copyright (C) Randall Frank
# See LICENSE for details
#

import argparse
import logging
import os.path
import shutil
import sys

from PySide6 import QtCore, QtWidgets

import card_objects
from _version import VERSION
from build_pdf import generate_pdf
from build_tts import generate_tts
from card_render import Renderer
from utilities import qt_message_handler

# Bug: text word wrapping not correct yet


__version__ = VERSION


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate T.I.M.E Stories cards from art assets.")
    parser.add_argument("cardfile", nargs=1, help="The name of a saved project.")
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    parser.add_argument("--outdir", default=None, nargs="?", help="The name of a saved project.")
    parser.add_argument("--pad_width", default=0, nargs="?", help="Extra border padding for printing.")
    parser.add_argument(
        "--default_deck", default=None, metavar="dirname", nargs="*", help="Create new deck from images in directories"
    )
    parser.add_argument("--card", default=None, metavar="card_number", nargs="?", help="Render a single card")
    parser.add_argument(
        "--mpc",
        action="store_true",
        default=False,
        help="Set up for printing with makeplayingcards.com (same as --pad_width 36)",
    )
    parser.add_argument("--pdf", action="store_true", default=False, help="Generate pdf files from the generated cards")
    parser.add_argument(
        "--tabletop", action="store_true", default=False, help="Generate Tabletop Simulator deck images from generated cards"
    )
    parser.add_argument("--verbose", action="store_true", default=False, help="Enable verbose mode")
    parser.add_argument("--logfile", default=None, help="Save console output to the specified file")
    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    logging.basicConfig(filename=args.logfile, level=log_level, format="%(levelname)s: %(message)s")

    # bootstrap Qt
    QtCore.qInstallMessageHandler(qt_message_handler)
    app = QtWidgets.QApplication(sys.argv)

    if args.default_deck is not None:
        logging.info("Building deck {}...".format(args.cardfile[0]))
        deck = card_objects.build_empty_deck(media_dirs=args.default_deck)
        deck.save(args.cardfile[0])
        sys.exit(0)

    logging.info("Reading {}...".format(args.cardfile[0]))
    filename = os.path.abspath(args.cardfile[0])
    directory = os.path.dirname(filename)
    os.chdir(directory)
    outdir = directory
    if args.outdir is not None:
        outdir = args.outdir
    deck = card_objects.Deck()
    if not deck.load(filename):
        logging.info("Unable to read the file: {}\n".format(filename))
        sys.exit(1)
    outdir = os.path.join(outdir, "generated_cards")
    if args.card is None:
        # remove and set up the output directory
        try:
            shutil.rmtree(outdir)
        except Exception:
            pass
        try:
            os.mkdir(outdir)
        except Exception as e:
            logging.error("Unable to create output directory {} : {}".format(outdir, str(e)))
            sys.exit(1)

    the_card = None
    if args.card is not None:
        the_card = int(args.card)
        logging.info("Rendering card: {}".format(the_card))

    # set up the renderer
    render = Renderer(deck, outdir)
    if args.mpc:
        render.pad_size = 36
    render.pad_size = int(args.pad_width)
    render.render_deck(the_card)

    # generate pdf file(s)
    if args.pdf:
        logging.info("Generating PDF files")
        generate_pdf(render)

    # generate Tabletop Simulator images
    if args.tabletop:
        logging.info("Generating Tabletop Simulator files")
        generate_tts(render)

    sys.exit(0)
