#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#
import logging
import sys

from PySide6 import QtXml


class CardTranslator:
    def __init__(self) -> None:
        self._translations = {}
        self._xliffdoc: QtXml.QDomDocument = QtXml.QDomDocument()
        self._id: int = 0
        self._use_ph: bool = True

    @property
    def use_ph(self) -> bool:
        return self._use_ph

    @use_ph.setter
    def use_ph(self, wrap: bool) -> None:
        self._use_ph = wrap

    def next_id(self) -> str:
        """
        Generate a unique XLIFF id string.

        Returns
        -------
        str
        """
        self._id += 1
        return f"{self._id}"

    def load_translation(self, filename: str) -> None:
        """
        Load translations from the specified XLIFF file.

        Parameters
        ----------
        filename : the filename of the XLIFF translation file

        """
        try:
            fp = open(filename, "rb")
            xml = fp.read()
            fp.close()
        except Exception:
            logging.error(f"reading translation file: {filename}")
            sys.exit(1)
        doc = QtXml.QDomDocument()
        ok, msg, line, col = doc.setContent(xml)
        if not ok:
            logging.error(f"parsing translation file line {line}, column {col}: {msg}")
            sys.exit(1)
        # Parse the XLIFF file  <xliff><file><body>
        xliff = doc.firstChildElement("xliff")
        if xliff.isNull():
            logging.error(f"no xliff element found in translation file: {filename}")
            sys.exit(1)
        file_elem = xliff.firstChildElement("file")
        if file_elem.isNull():
            logging.error(f"no file element found in translation file: {filename}")
            sys.exit(1)
        source_lang = file_elem.attribute("source-language", "en")
        target_lang = file_elem.attribute("target-language", "unknown")
        logging.info(f"Loading translation file: {filename} {source_lang} -> {target_lang}")
        body = file_elem.firstChildElement("body")
        if body.isNull():
            logging.error(f"no body element found in translation file: {filename}")
            sys.exit(1)
        # <trans-unit> <source> & <target>
        self._translations = {}
        trans_unit = body.firstChildElement("trans-unit")
        while not trans_unit.isNull():
            source = trans_unit.firstChildElement("source")
            if not source.isNull():
                target = trans_unit.firstChildElement("target")
                if not target.isNull():
                    self._translations[source.text()] = target.text()
                else:
                    # return source translation
                    self._translations[source.text()] = source.text()
            trans_unit = trans_unit.nextSiblingElement("trans-unit")
        logging.info(f"Loaded {len(self._translations)} translations")

    def translate(self, text: str) -> str:
        """
        Translate the specified text if a translation is available.

        Parameters
        ----------
        text : str the string to translate

        Returns
        -------
        str : the translated string
        """
        if text in self._translations:
            return self._translations[text]
        return text

    def extract_xliff_source(self, source: str, target: str, lang: str = "") -> None:
        """
        Extract the source string from a .deck format XML file and
        write them into an XLIFF file.

        Parameters
        ----------
        source: str the source .deck file
        target: str the target XLIFF file
        lang: str the target language code (default "")
        """
        try:
            with open(source, "rb") as fp:
                deckxml = fp.read()
        except Exception:
            logging.error(f"reading source file: {source}")
            sys.exit(1)
        srcdoc = QtXml.QDomDocument()
        ok, msg, line, col = srcdoc.setContent(deckxml)
        if not ok:
            logging.error(f"parsing source file line {line}, column {col}: {msg}")
            sys.exit(1)

        # Create the XLIFF document
        self._xliffdoc = QtXml.QDomDocument()
        xliff = self._xliffdoc.createElement("xliff")
        self._xliffdoc.appendChild(xliff)
        xliff.setAttribute("version", "1.2")
        xmlns = "urn:oasis:names:tc:xliff:document:1.2"
        xliff.setAttribute("xmlns", xmlns)
        file_elem = self._xliffdoc.createElement("file")
        xliff.appendChild(file_elem)
        file_elem.setAttribute("source-language", "en")
        file_elem.setAttribute("target-language", lang)
        file_elem.setAttribute("datatype", "plaintext")
        body = self._xliffdoc.createElement("body")
        file_elem.appendChild(body)
        # Walk the srcdoc looking for text to translate
        deck = srcdoc.firstChildElement("deck")
        self.walk_deck_dom(deck, body)
        try:
            fp = open(target, "wb")
            fp.write(bytes(self._xliffdoc.toString(), "UTF-8"))
            fp.close()
        except Exception:
            logging.error(f"writing target file: {target}")
            sys.exit(1)
        logging.info(f"Generated {len(self._translations)} translations")
        logging.info(f"Wrote XLIFF file: {target}")
        self._translations = {}
        self._xliffdoc = QtXml.QDomDocument()

    def add_ph(self, text: str) -> str:
        """
        Wrap text in braces with <ph> tags.

        Parameters
        ----------
        text: str the text to modify

        Returns
        -------
        str: the modified text
        """
        if not self.use_ph:
            return text
        idx = text.find("{")
        while idx >= 0:
            end_idx = text.find("}", idx + 1)
            if end_idx > idx:
                block = text[idx : end_idx + 1]
                repl = f'<ph id="{self.next_id()}">{block}</ph>'
                text = text[:idx] + repl + text[end_idx + 1 :]
                idx = text.find("{", idx + len(repl))
            else:
                break
        return text

    def add_trans_unit(self, body: QtXml.QDomElement, source: str, target: str = "") -> None:
        """
        Add a source string (and optionally a target string) to a new XLIFF
        <trans-unit> element.  One can get access to the new element by looking
        the string up in _translations.

        Parameters
        ----------
        body : the parent <body> element
        source : the source string
        target : an optional target string
        """
        if not source:
            return
        if source in self._translations:
            return
        trans_unit = self._xliffdoc.createElement("trans-unit")
        trans_unit.setAttribute("id", self.next_id())
        body.appendChild(trans_unit)
        source_elem = self._xliffdoc.createElement("source")
        trans_unit.appendChild(source_elem)
        text_node = self._xliffdoc.createTextNode(self.add_ph(source))
        source_elem.appendChild(text_node)
        if target:
            target_elem = self._xliffdoc.createElement("target")
            trans_unit.appendChild(target_elem)
            text_node = self._xliffdoc.createTextNode(self.add_ph(target))
            target_elem.appendChild(text_node)
        self._translations[source] = trans_unit

    def walk_deck_dom(self, parent: QtXml.QDomElement, body: QtXml.QDomElement) -> None:
        """
        Walk the .deck DOM looking for text to translate.
        Parameters
        ----------
        parent : the parent element to walk
        body : the <body> element of the XLIFF file

        What needs translating?
        - <text> elements with <text> parent elements
        - <location> "name" attributes
        - <card> "name" attributes
            for immediate children of <base>,<items>,<characters>,<cards>,<plan> elements

        """
        if parent.isNull():
            return
        child = parent.firstChildElement()
        while not child.isNull():
            tag = child.tagName()
            if tag == "text":
                text = child.text()
                if text and parent.tagName() in ("text"):
                    self.add_trans_unit(body, text)
            elif tag == "location":
                text = child.attribute("name", "")
                if text:
                    self.add_trans_unit(body, text)
            elif tag == "card":
                text = child.attribute("name", "")
                if text and parent.tagName() in ("base", "items", "characters", "cards", "plan"):
                    self.add_trans_unit(body, text)
            # recurse
            self.walk_deck_dom(child, body)
            child = child.nextSiblingElement()
