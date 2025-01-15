#
# T.I.M.E Stories card generator
# Copyright (C) Randall Frank
# See LICENSE for details
#

import argparse
import glob
import io
import logging
import os.path
import shutil
import sys

from PySide6 import QtCore, QtWidgets
from dulwich import porcelain

import heresycardbuilder

__version__ = heresycardbuilder.__version__
sys.path.append(os.path.dirname(heresycardbuilder.__file__))
from build_pdf import generate_pdf  # noqa: E402
from build_tts import generate_tts  # noqa: E402
import card_objects  # noqa: E402
from card_render import Renderer  # noqa: E402
from utilities import is_directory, qt_message_handler  # noqa: E402


def run() -> None:
    parser = argparse.ArgumentParser(description="Generate T.I.M.E Stories cards from art assets.")
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )
    parser.add_argument(
        "cardfile",
        nargs=1,
        help="Filename of a source .deck file or github repo containing a .deck file.",
    )
    parser.add_argument(
        "--outdir",
        default=None,
        nargs="?",
        help="Directory where the 'generated_cards' directory will be created. \
        By default, it is the directory containing the cardfile.",
    )
    parser.add_argument(
        "--pad_width", default=0, nargs="?", help="Extra border padding for printing."
    )
    parser.add_argument(
        "--default_deck",
        default=None,
        metavar="dirname",
        nargs="*",
        help="Create new deck from images in directories",
    )
    parser.add_argument(
        "--card", default=None, metavar="card_number", nargs="?", help="Render a single card"
    )
    parser.add_argument(
        "--mpc",
        action="store_true",
        default=False,
        help="Set up for printing with makeplayingcards.com (same as --pad_width 36)",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        default=False,
        help="Generate pdf files from the generated cards",
    )
    parser.add_argument(
        "--tabletop",
        action="store_true",
        default=False,
        help="Generate Tabletop Simulator deck images from generated cards",
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
    app = QtWidgets.QApplication(sys.argv)  # noqa F841

    cardfile = args.cardfile[0]
    if args.default_deck is not None:
        logging.info(f"Building deck {cardfile}...")
        deck = card_objects.build_empty_deck(media_dirs=args.default_deck)
        deck.save(args.cardfile[0])
        sys.exit(0)

    # if cardfile is a git URL, clone repo into a tempdir and use .deck file in tempdir root.
    if cardfile.startswith("http") and cardfile.endswith(".git"):
        if args.outdir is None:
            logging.error("--outdir must be specified for git source decks")
            sys.exit(1)
        destination = args.outdir
        if not is_directory(destination):
            logging.error("--outdir must be an empty directory")
            sys.exit(1)
        # do the download...
        logging.info(f"Cloning the git repo: {cardfile} to {destination}")
        buffer = io.BytesIO()
        try:
            porcelain.clone(cardfile, destination, errstream=buffer)
        except Exception as e:
            logging.error(f"Unable to clone source git repo: {str(e)}")
            sys.exit(1)
        for line in buffer.getvalue().decode("ascii").split("\n"):
            logging.debug(line)
        # Look for the .deck file
        deckfiles = glob.glob(os.path.join(destination, "*.deck"))
        if len(deckfiles) < 1:
            logging.error(f"Unable to find .deck file in cloned git repo: {destination}")
            sys.exit(1)
        cardfile = deckfiles[0]

    logging.info(f"Reading {cardfile}...")
    filename = os.path.abspath(cardfile)
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


if __name__ == "__main__":
    run()
