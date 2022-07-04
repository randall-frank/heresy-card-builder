

[Heresy]: http://heresy.mrtrashcan.com

# Heresy Deck Generation Tools
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![CC-0 license](https://img.shields.io/badge/License-CC--0-blue.svg)](https://creativecommons.org/licenses/by-nd/4.0)

Copyright (C) 2017-2022 Randall Frank

These tools were developed for use with the Heresy series of T.I.M.E Stories
scenarios.  For more details on the scenarios and how to obtain them, see
[Heresy].

* The source code of this package is being made available under an MIT 
open source license. See LICENSE for additional Copyright information.
* See the file deck_format.txt for a more detailed description of the deck 
XML schema and renderable entities details.

### What can they do?
The Heresy, Python-based toolset is capable of laying out and rendering 
cards in various forms. It is capable of generating individual PNG files 
for the top and bottom of each card in the deck as well as Letter and A4 
format PDF files of the whole deck and the composite PNG file 'deck' images 
used by Tabletop Simulator from the same XML source. The tool has the 
ability to generate cards padded out with the bleeding region needed for 
printing services like makeplayingcards.com.

### How do they work?
The tools work on a 'deck' file, an XML formatted description of a T.I.M.E 
Stories deck.  A deck contains lists of cards (e.g. Items, plans, characters, 
etc). Each card contains a set of text or image blocks that can be sized, 
rotated and placed on the card. Individual items have the concept of 'depth' 
which controls the compositing order of the various card elements. Finally, 
every type of card has a "default" card that it can inherit from as base 
layer. This makes it very easy to do things like add the item number to 
all item cards by adding it to the default card with a depth that ensures 
it is visible over (or under) other content.

The deck XML schema describes text styles and images as "assets" that can 
be referenced by name on the cards. One can even refer to subsections of a 
source image file as an image, making it very simple to crop out portions 
of a larger image (or a single image of a location into cards) and use 
them in additional places. We often import the Space Cowboys' SDK at the 
start of a new scenario for consistency with other decks.

At the heart of the deck is the representation of a card face. Every card 
has a top and a bottom face with a different collection of renderable items. 
The final rendered card is a composite of the current card items and any 
items from the default card for the current card type. The items from the 
card and the default card are merged and sorted by depth (layers) that 
determine the order of the item compositing. There are rectangle, image 
and text items. The text item plays a key role as much of the story is told 
through these items. The text item allows for the application of "styles" 
to sections of text that are common over all cards (e.g. all item references 
should be bold and green). Text can include macros that substitute for 
actual card names, numbers, letters, etc. These are computed when the card 
is rendered and help make sure that moving things around leaves most links 
intact. Image objects can even be embedded (inline) into the text of a text 
item. In short enough functionality to cover the needs of the Heresy story.

### Quick Example
Suppose one has a file named "hersey.deck", Python 3.8 has been installed in
C:\Python38 and the source code to the deck tools where checked out to
D:\git\card_builder\.  One can build the output imagery types using 
the command line:

```C:\Python38\python.exe D:\git\card_builder\build_deck.py --pdf --tabletop heresy.deck```

It will create a directory "generated_cards" in the same directory as hersey.deck and 
place all of the generated output products into the target directory.

The complete command line to the tool looks like:

```
C:\Python38\python.exe D:\git\card_builder\build_deck.py -h
usage: build_deck.py [-h] [--version] [--outdir [OUTDIR]]
                     [--pad_width [PAD_WIDTH]]
                     [--default_deck [dirname [dirname ...]]]
                     [--card [card_number]] [--mpc] [--pdf] [--tabletop]
                     cardfile

Generate T.I.M.E Stories cards from art assets.

positional arguments:
  cardfile              The name of a saved project.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --outdir [OUTDIR]     The name of a saved project.
  --pad_width [PAD_WIDTH]
                        Extra border padding for printing.
  --default_deck [dirname [dirname ...]]
                        Create new deck from images in directories
  --card [card_number]  Render a single card
  --mpc                 Set up for printing with makeplayingcards.com (same as
                        --pad_width 36)
  --pdf                 Generate pdf files from the generated cards
  --tabletop            Generate Tabletop Simulator deck images from generated
                        cards
```

The most useful options are --outdir, --card, --pdf, and --tabletop

### Notes
The card builder uses the Qt rendering engine to generate card images.
If you are using custom TrueType typefaces in your deck, they need to 
be installed such that the version of Qt used by your Python interpreter
can access the typeface.

The project is now dependent on Python 3.8 and PySide6.  The project was developed in 
PyCharm and includes external tools in the IDE configuration to rebuild the .qrc
and .ui resources into .py files.  Those two files need to be updated before the
GUI project can be run.
