
T.I.M.E Stories Deck Generation Tools
=====================================
|pypi| |python| |MIT| |pre-commit| |black| |isort| |flake8|

.. |pypi| image:: https://img.shields.io/pypi/v/heresycardbuilder.svg?logo=python&logoColor=white
   :target: https://pypi.org/project/heresycardbuilder

.. |python| image:: https://img.shields.io/badge/python-3.10-blue.svg?logo=python
   :target: https://www.python.org/downloads/release/python-3100/

.. |MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT

.. |black| image:: https://img.shields.io/badge/code_style-black-000000.svg
   :target: https://github.com/psf/black

.. |isort| image:: https://img.shields.io/badge/imports-isort-%231674b1.svg
   :target: https://pycqa.github.io/isort/

.. |flake8| image:: https://img.shields.io/badge/flake8-checked-blueviolet
    :target: https://flake8.pycqa.org/

.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit


Overview
--------

These tools were developed for use with the Heresy series of
`T.I.M.E Stories <https://www.spacecowboys.fr/time-stories-english>`_
scenarios.  For more details on the scenarios and how to obtain them, see
`Heresy <http://heresy.mrtrashcan.com>`_.

The source code of this package is being made available under an MIT
open source license. See `LICENSE <https://github.com/randall-frank/heresy-card-builder/blob/master/LICENSE>`_
for additional Copyright information. See the file
`deck_format.rst <https://github.com/randall-frank/heresy-card-builder/blob/master/deck_format.rst>`_ for
a more detailed description of the deck XML schema and renderable entities details.

The content for the Heresy T.I.M.E Stories card deck is available on github
`heresy-assets <https://github.com/randall-frank/heresy-assets>`_.  These tools were
used to generate that deck.


What can they do?
~~~~~~~~~~~~~~~~~

The Heresy, Python-based toolset is capable of laying out and rendering
cards in various forms. It is capable of generating individual PNG files
for the top and bottom of each card in the deck as well as Letter and A4
format PDF files of the whole deck and the composite PNG file `deck` images
used by Tabletop Simulator from the same XML source. The tool has the
ability to generate cards padded out with the bleeding region needed for
printing services like makeplayingcards.com.

How do they work?
~~~~~~~~~~~~~~~~~

The tools work on a 'deck' file, an XML formatted description of a T.I.M.E
Stories deck.  A deck contains lists of cards (e.g. Items, plans, characters,
etc). Each card contains a set of text or image blocks that can be sized,
rotated and placed on the card. Individual items have the concept of 'depth'
which controls the compositing order of the various card elements. Finally,
every type of card has a "default" card that it can inherit from as base
layer. This makes it very easy to do things like add the item number to
all item cards by adding it to the default card with a depth that ensures
it is visible over (or under) other content.

The Deck XML file
`````````````````

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
through these items. The text item allows for the application of *styles*
to sections of text that are common over all cards (e.g. all item references
should be bold and green). Text can include macros that substitute for
actual card names, numbers, letters, etc. These are computed when the card
is rendered and help make sure that moving things around leaves most links
intact. Image objects can even be embedded (inline) into the text of a text
item. In short enough functionality to cover the needs of the Heresy story.

Quick Usage Example
~~~~~~~~~~~~~~~~~~~

Suppose one has a file named `hersey.deck` and Python has been installed in
`C:\Python310`.  The tools can be installed by building them from source
or installing the module via pip::

    C:\Python310\python.exe -m pip install heresycardbuilder


One can build output imagery types using the command line::

    C:\Python310\Scripts\build_deck --pdf --tabletop heresy.deck


It will create a directory ``generated_cards`` in the same directory as ``hersey.deck`` and
place all of the generated output products (card images, PDF and Tabletop Simulator) into
the target directory.

The complete command line interface to the tool looks like::

    usage: build_deck [-h] [-V] [--outdir [OUTDIR]] [--pad_width [PAD_WIDTH]] [--default_deck [dirname ...]] [--card [card_number]] [--mpc] [--pdf] [--tabletop] [--verbose] [--logfile LOGFILE] cardfile

    Generate T.I.M.E Stories cards from art assets.

    positional arguments:
      cardfile              Filename of a source .deck file or github repo containing a .deck file.

    options:
      -h, --help            show this help message and exit
      -V, --version         show program's version number and exit
      --outdir [OUTDIR]     Directory where the 'generated_cards' directory will be created. By default, it is the directory containing the cardfile.
      --pad_width [PAD_WIDTH]
                            Extra border padding for printing.
      --default_deck [dirname ...]
                            Create new deck from images in directories
      --card [card_number]  Render a single card
      --mpc                 Set up for printing with makeplayingcards.com (same as --pad_width 36)
      --pdf                 Generate pdf files from the generated cards
      --tabletop            Generate Tabletop Simulator deck images from generated cards
      --verbose             Enable verbose mode
      --logfile LOGFILE     Save console output to the specified file


The most useful options are ``--outdir``, ``--card``, ``--pdf`` and ``--tabletop``.

The card deck can actually be a git repo specification.  In that case, in the root
of the git repo there should be one and only one ``.deck`` file.  The git repo will be cloned
into the directory specified by ``--outdir`` and then the card images will be generated.  One
can render the original Heresy deck using a command line like this::

    build_deck https://github.com/randall-frank/heresy-assets.git --outdir D:/myoutputdir --pdf


Note that the host system should have the 'Carlito' font (included in the Heresy repo) installed
to get the best results.

Notes
~~~~~

The card builder uses the Qt rendering engine to generate card images.
If you are using custom TrueType typefaces in your deck, they need to
be installed such that the version of Qt used by your Python interpreter
can access the typeface.

The project is dependent on Python 3.10 and PySide6.  It was developed in
PyCharm.

Developers
----------

Building the package is pretty straightforward.  The use of a
`virtual environment <https://docs.python.org/3/library/venv.html>`_
is strongly recommended::

   git clone https://github.com/randall-frank/heresy-card-builder.git
   cd heresy-card-builder
   pip install virtualenv
   python -m virtualenv venv
   .\venv\Scripts\activate.ps1   # for Windows PowerShell, different for other shells
   pip install .[dev]


Build
~~~~~

To build and install `heresycardbuilder` tools, run these commands::

   python -m build
   python -m pip uninstall heresycardbuilder -y
   python -m pip install .\dist\heresycardbuilder-0.9.0-py3-none-any.whl
   build_deck --help


Pre-commit
~~~~~~~~~~

``pre-commit`` is used in this project to enforce code styling and other
features.  Code must pass the pre-commit check before it can be committed
to the repo.

To install pre-commit into your git hooks, run this command::

   pre-commit install

``pre-commit`` then runs on every commit. Each time you clone a project,
installing ``pre-commit`` should always be the first action that you take.

If you want to manually run all pre-commit hooks on a repository, run this
command::

   pre-commit run --all-files

flake8, isort, codespell and black will all be applied.

To run individual hooks, use this command, where ``<hook_id>`` is obtained from
from the ``.pre-commit-config.yaml`` file::

   pre-commit run <hook_id>

The first time pre-commit runs on a file, it automatically downloads, installs,
and runs the hook.

Testing
~~~~~~~

Basic unit tests are implemented using pytest.  To run the tests::

    pytest

TODO
~~~~

* New cards/copy/paste
* Issues with deleted assets?
* Reordering computation with no or higher-level parent (no 'obj' on the parent)

----

Copyright (C) 2017-2025 Randall Frank