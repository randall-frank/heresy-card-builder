T.I.M.E Stories Deck XML File Format
====================================

The deck format is a fairly simple xml schema that describes a deck of
cards.  Each card has a top and a bottom face.  Each face can have a
collection of image, text or rectangle renderable items that make up
the card visuals.

Overview
--------

One can generate the cards for a specific deck with the command line::

    build_deck example.deck

The generated content is placed in a subdirectory named ``generated_cards``
in the same directory as the `.deck` file. The Python needs to be 3.10
and include the PySide6 module.

Assets
------

In addition to cards, the deck includes 'assets'.  Assets are
used by renderable items to declare visual styles and imagery sources.
A 'file' asset refers to a .png or .jpg file on disk.  An 'image' asset
refers to a specific region of a 'file' asset.  Thus, a single 'file'
asset can be decomposed into many 'image' assets.  An image renderable
item scales, rotates and places an 'image' asset on a card face.  The other
asset entity is a 'style'.  Text and rectangle renderable items refer to
'style' assets to define their color and other rendering properties.

.. note::

    Note: cards are 825x1425 pixels for a standard Tarot card size
    card (70mmx120mm) @ 300 DPI.

    The build_deck tool will generate cards at the resolution specified by the **<decksize>**
    element and will then rescale the cards to 825x1425.  Heresy uses a 945x1535 decksize as
    this is the size used by the Space Cowboys SDK imagery.  In retrospect, it should have
    been laid out at 825x1425 resolution.

Deck Structure
--------------

Deck structure outline (note that in several places element values are specified
using Python list syntax)::

    <deck>
        <decksize>[825, 1425]</decksize>
        <assets>
            <file filename="somefilename.png" name="sample_file_name"/>  # refer to a png/jpg relative to the .deck location
            <image name="image_asset_name">  # define an image asset
                <file>sample_file_name.png</file>  # name of a file asset
                <rectangle>[x0,y0,dx,dy]</rectangle>  # rectangles are always in pixels are x,y,dx,dy
                <usage>any</usage>  # currently unused
            </image>
            <style name="style_name">
                <typeface>Arial</typeface>  # the name of a font typeface (can use :bold, :italic suffixes)
                <typesize>size</typesize>   # the size of the font in points (1/72 of an inch)
                <fillcolor>[255,255,255,255]</fillcolor>  # R,G,B,A [0-255]
                <borderthickness>1</borderthickness>  # thickness of border in pixels (0=no border)
                <bordercolor>[0,0,0,255]</bordercolor>
                <textcolor>[0,0,0,255]</textcolor>
                <linestyle>solid</linestyle>  # solid, dot, dash, dashdot
                <justification>full</justification>   # full, left, right, center
                <boundary_offset>n</boundary_offset>  # number of pixels to outset background rect outside of text rect
            </style>
        </assets>
        <cards>
            <defaultcard>  # This is the default card definition.  These items are included with most cards
                <top>
                    <image name="top"></image>
                    <text name="locationname"></text>
                    ...
                </top>
                <bottom>
                    ...
                </bottom>
            </defaultcard>
            <defaultitemcard>  # This is a card whose items are included in all "item" cards
                <top>
                    ...
                </top>
                <bottom>
                    ...
                </bottom>
            </defaultitemcard>
            <defaultlocationcard> # This is a card whose items are included in all "location" cards
                <top>
                    ...
                </top>
                <bottom>
                    ...
                </bottom>
            </defaultlocationcard>
            <deckcards>   # This defines a collection of cards that are not numbered and do not inherit from any default cards
                {card}
                ...
                {card}
            </deckcards>
            <base>  # The base cards.  Inherit from defaultcard
                {card}
                ...
                {card}
            </base>
            <iconreference>  # the icon reference cards.  Inherit from defaultcard
                <top>
                    ...
                </top>
                <bottom>
                    ...
                </bottom>
            </iconreference>
            <characters>   # the character cards.  Inherit from defaultcard
                {card}
                ...
                {card}
            </characters>
            <plan>  # the plan cards.  Inherit from defaultcard
                {card}
                ...
                {card}
            </plan>
            <items>  # the item cards.  Inherit from defaultitemcard
                {card}
                ...
                {card}
            </items>
            <misc>  # misc cards.  Inherit from defaultcard
                {card}
                ...
                {card}
            </misc>
            <locations>  # the location cards.  Inherit from defaultlocationcard
                <location>
                    {card}
                    ...
                    {card}
                </location>
                <location>
                    {card}
                    ...
                    {card}
                </location>
            </locations>
        </cards>
    </deck>

Card Structure
--------------

The **{card}** structure, containing a top and bottom face.  Each face includes a
list of renderable items::

    <card name="card_name">
        <top>
            # in this block, any number of <text> <rect> and <image> items can be specified
            # they will be rendered in the order specified by the <order> numbers
            <text name="text_renderable_name">
                <text>The actual text to render</text>  # see notes below
                <rotation>angle</rotation>
                <style>style_asset_name</style>  # set the default style
                <rectangle>[x,y,dx,dy]</rectangle>  # in pixels
                <order>number</order>
                <rotation>degrees</rotation>
            </text>
            <rect name="rect_renderable_name">
                <rotation>angle</rotation>
                <style>style_asset_name</style>
                <rectangle>[x,y,dx,dy]</rectangle>
                <order>number</order>
                <rotation>degrees</rotation>
            </rect>
            <image name="image_renderable_name">
                <image>image_asset_name</image>
                <rectangle>[x,y,dx,dy]</rectangle>
                <order>number</order>
                <rotation>degrees</rotation>
            </image>
        </top>
        <bottom>
            ...
        </bottom>
    </card>


Renderable Notes
----------------

Some notes on renderables:

    #. All rotations are around the upper left corner of the target renderable item.
    #. Image dx and dy can be -1, if so, they default to the width and height of the source image asset
       One of the two values (dx,dy) can also be set to -2.  In that case, the other value (which can be -1) is used
       to select the isotropic scaling factor for the image and the -2  value will be set to preserve the ratio selected
       by the other value.
    #. Image assets will be scaled to fill the image renderable rectangle.
    #. If the height of a text renderable is -1, the height will be selected to hold the formatted text.
    #. Order values specify the compositing order of elements. lower numbered elements are rendered first.

Text Macros
~~~~~~~~~~~

Text renderable text notes.  The text string can contain macros.  A macro take the form {value} and (if valid)
will be replaced by dynamically generated text.  If invalid, it will be replaced by {err} in the output.
Valid macros include::

    {n} = replace with an end of line character

    {XY:}
    {XY:name}

    X can be:
    c=card, i=item, l=location

    Y can be:
    N=card number in the deck (the global card numbering)
    n=card number of the specific type (e.g. {in:foo} is the item number of the item card named "foo" or
       {ln:} is the location number of the current location)
    s=card name (e.g. {cs:} is the name of the current card)
    a=the letter form of 'n', where 1="A".  Basically, just like 'n' except 1="A", 2="B" ...
    If "name" is empty it will be the current card, item or location (based on "X") otherwise, the macro
    will look for a card, item or location with the specified name and use that entity when resolving "Y".
    {s:} = set text formatting back to the style specified in the text renderable
    {s:style_name} = set text formatting to the style with the name "style_name"
    {I:image_name:dx:dy} = insert the image by name and resize to dx,dy}

Unicode characters can be inserted as per XML specification: ``&#x2022;``
