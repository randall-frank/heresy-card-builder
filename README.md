
[Heresy]: http://heresy.mrtrashcan.com

#Heresy Deck Generation Tools
Copyright &copy; 2017 Randall Frank

These tools were developed for use with the Heresy series of T.I.M.E Stories
scenarios.  For more details on the scenarios and how to obtain them, see
[Heresy].

* The source code of this package is being made available under an MIT 
open source license. See LICENSE for additional Copyright information.
* See the file deck_format.txt for a more detailed description of the deck 
XML schema and renderable entities details.

###What can they do?
The Heresy, Python-based toolset is capable of laying out and rendering cards
in various forms.  It is capable of generating individual PNG files for the 
top and bottom of each card in the deck as well as Letter and A4 format PDF 
files of the whole deck and the composite PNG file deck images used by Tabletop 
Simulator from the same XML source.  The tool has the ability to pad out a card 
with the bleeding region needed for printing services like makeplayingcards.com.

###How do they work?
The tools work on a 'deck' file, an XML formatted description of a T.I.M.E 
Stories deck.  A deck contains lists of cards (e.g. Items, plans, characters, 
etc).  Each card contains a set of text or image blocks that can be sized, 
rotated and placed on the card.  Individual items have the concept of 'depth' 
which controls the compositing order of the various card elements. Finally, 
every type of card has a "default" card that it can inherit from as base layer.  
This makes it very easy to do things like add the item number to all item cards 
by adding it to the default card with a depth that ensures it is visible over 
(or under) other content.

The text item plays a key role. It allows for the application of "styles" to 
sections of text that are common over all cards (e.g. all item references should 
be bold and green).  The text item includes a collection of macros that can 
substitute for actual card names, numbers, letters, etc.  These are computed 
when the card is rendered and help make sure that moving things around leaves 
most links intact.

The deck XML schema describes text styles and images as "assets" that can be 
referenced by name on the cards. One can even refer to subsections of a source 
image file as an image, making it very simple to crop out portions of a larger 
image (or a single image of a location into cards) and use them in additional 
places. We often import the Space Cowboys' SDK at the start of a new scenario 
for consistency with other decks.

###Quick Example
Suppose one has a file named "hersey.deck", Python 3.5 has been installed in
C:\Python35 and the source code to the deck tools where checked out to
D:\git\card_builder\.  One can build all of the output imagery types using 
the command line:

<pre>C:\Python35\python.exe D:\git\card_builder\build_deck.py --pdf --tabletop heresy.deck</pre>

Will create a directory "generated_cards" in the same directory as hersey.deck
containing all of the output products.  

The complete command line to the tool looks like:

<pre>
C:\Python35\python.exe D:\git\card_builder\build_deck.py -h
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
</pre>

The most useful options are --outdir, --card, --pdf, and --tabletop


###Notes
The card builder uses the Qt rendering engine to generate card images.
If you are using custom TrueType typefaces in your deck, they need to 
be installed such that the version of Qt used by your Python interpreter
can access the typeface.
