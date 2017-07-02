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

__version__ = "0.1.0.0"

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
    tmp = card_objects.Deck()
    if not tmp.load(filename):
        print("Unable to read the file: {}\n".format(filename))
        sys.exit(1)
    # remove and set up the output directory
    outdir = os.path.join(outdir, "generated_cards")
    try:
        shutil.rmtree(outdir)
        os.mkdir(outdir)
    except:
        pass
    sys.exit(0)
