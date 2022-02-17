#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#

from datetime import date
from PySide6 import QtCore
from PySide6 import QtWidgets

from ui_card_editor_main import Ui_card_editor_main
from card_objects import build_empty_deck, Deck, Location
from card_render import Renderer


class CEListItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, obj, parent=None, can_move=True, can_rename=True, can_select=True):
        super(CEListItem, self).__init__()
        self._obj = obj
        self.setText(0, obj.name)
        flags = QtCore.Qt.ItemIsEnabled
        if can_select:
            flags |= QtCore.Qt.ItemIsSelectable
        if can_rename:
            flags |= QtCore.Qt.ItemIsEditable
        if can_move:
            flags |= QtCore.Qt.ItemIsDropEnabled
            flags |= QtCore.Qt.ItemIsDragEnabled
        self.setFlags(flags)
        if parent:
            parent.addChild(self)

    def get_obj(self):
        return self._obj


class CardEditorMain(QtWidgets.QMainWindow, Ui_card_editor_main):
    def __init__(self, version, parent=None):
        super(CardEditorMain, self).__init__(parent)
        self.setupUi(self)
        self._version = version
        self._dirty = False
        self._deck = None
        self._deck_filename = None
        self._property_object = None
        self._render_object = None
        self._current_card = None
        self._current_asset = None
        self._gs_asset = QtWidgets.QGraphicsScene()
        self.gvAsset.setScene(self._gs_asset)
        self._renderer = None
        self._zoom = 1.0
        self.do_new()

    def do_zoom(self):
        action = self.sender()
        if action == self.actionZoomOut:
            self._zoom *= 0.80
        elif action == self.actionZoomIn:
            self._zoom *= 1.20
        elif action == self.actionZoomReset:
            self._zoom = 1.0
        self.update_zoom()

    def do_new(self):
        if self._deck and self._dirty:
            s = "There are unsaved changes, are you sure you want to start a new deck?"
            btn = QtWidgets.QMessageBox.question(self, "Start a new deck", s)
            if btn != QtWidgets.QMessageBox.Yes:
                return
        self._deck = build_empty_deck()
        self._renderer = Renderer(self._deck, parent=self.wCardView)
        self._deck_filename = None
        self._dirty = False
        self.lblInfo.setText("Deck: Untitled")
        self.deck_update()

    def do_saveas(self):
        tmp = QtWidgets.QFileDialog.getSaveFileName(self, "Save deck as", "Untitled.deck",
                                                    "Card deck (*.deck);;All files (*)")
        if len(tmp[0]) == 0:
            return
        filename = tmp[0]
        if not self._deck.save(filename):
            QtWidgets.QMessageBox.critical(self, "Unable to save deck",
                                           "An error occurred while saving the deck")
            return
        self._dirty = False
        self._deck_filename = filename
        self.lblInfo.setText("Deck: " + filename)

    def do_save(self):
        if self._deck is None:
            return
        if self._deck_filename is None:
            self.do_saveas()
            return
        if not self._deck.save(self._deck_filename):
            QtWidgets.QMessageBox.critical(self, "Unable to save deck",
                                           "An error occurred while saving the deck")
            return
        self._dirty = False

    def do_load(self):
        if self._deck and self._dirty:
            s = "There are unsaved changes, are you sure you want to load a new deck?"
            btn = QtWidgets.QMessageBox.question(self, "Load a new deck", s)
            if btn != QtWidgets.QMessageBox.Yes:
                return
        tmp = QtWidgets.QFileDialog.getOpenFileName(self, "Save deck as", "",
                                                    "Card deck (*.deck);;All files (*)")
        if len(tmp[0]) == 0:
            return
        filename = tmp[0]
        tmp = Deck()
        if not tmp.load(filename):
            QtWidgets.QMessageBox.critical(self, "Unable to load deck",
                                           "An error occurred while loading the deck")
            return
        self._deck = tmp
        self._renderer = Renderer(self._deck, parent=self.wCardView)
        self._deck_filename = filename
        self.lblInfo.setText("Deck: " + filename)
        self._dirty = False
        self.deck_update()

    def do_frontface(self, b):
        self.update_card_render()

    def set_dirty(self, d):
        self._dirty = d

    @QtCore.Slot()
    def do_about(self):
        s = "T.I.M.E Stories card editor\n"
        s += f"Copyright (C) 2017-{date.today().year} Randall Frank\n"
        s += "Version: " + self._version
        QtWidgets.QMessageBox.about(self, "Card Editor", s)

    def closeEvent(self, event):
        if self._dirty:
            # prompt user
            s = "There are unsaved changes, are you sure you want to quit?"
            btn = QtWidgets.QMessageBox.question(self, "Quit Card Editor", s)
            if btn != QtWidgets.QMessageBox.Yes:
                event.ignore()
                return
        event.accept()  # let the window close

    def deck_update(self):
        self._current_asset = None
        self._current_card = None
        self.update_assetlist()
        self.update_asset_props()
        self.update_asset_render()
        self.update_cardlist()
        self.update_card_props()
        self.update_card_render()

    def update_cardlist(self):
        tw = self.twCards
        tw.clear()
        if self._deck is None:
            return
        self._deck.renumber_entities()
        tmp = CEListItem(self._deck.default_card, can_move=False, can_rename=False)
        tw.addTopLevelItem(tmp)
        tmp = QtWidgets.QTreeWidgetItem(["Deck cards"])
        tmp.setFlags(QtCore.Qt.ItemIsEnabled)
        tw.addTopLevelItem(tmp)
        for i in self._deck.deckcards:
            CEListItem(i, parent=tmp, can_move=True, can_rename=True)
        tmp = QtWidgets.QTreeWidgetItem(["Base Cards"])
        tmp.setFlags(QtCore.Qt.ItemIsEnabled)
        tw.addTopLevelItem(tmp)
        for i in self._deck.base:
            CEListItem(i, parent=tmp, can_move=True, can_rename=True)
        tmp = QtWidgets.QTreeWidgetItem(["Item Cards"])
        tmp.setFlags(QtCore.Qt.ItemIsEnabled)
        tw.addTopLevelItem(tmp)
        CEListItem(self._deck.default_item_card, parent=tmp, can_move=False, can_rename=False)
        for i in self._deck.items:
            CEListItem(i, parent=tmp, can_move=True, can_rename=True)
        tmp = QtWidgets.QTreeWidgetItem(["Plan Cards"])
        tmp.setFlags(QtCore.Qt.ItemIsEnabled)
        tw.addTopLevelItem(tmp)
        for p in self._deck.plan:
            CEListItem(p, parent=tmp, can_move=True, can_rename=True)
        tmp = QtWidgets.QTreeWidgetItem(["Misc Cards"])
        tmp.setFlags(QtCore.Qt.ItemIsEnabled)
        tw.addTopLevelItem(tmp)
        for c in self._deck.misc:
            CEListItem(c, parent=tmp, can_move=True, can_rename=True)
        tmp = QtWidgets.QTreeWidgetItem(["Characters"])
        tmp.setFlags(QtCore.Qt.ItemIsEnabled)
        tw.addTopLevelItem(tmp)
        for c in self._deck.characters:
            CEListItem(c, parent=tmp, can_move=True, can_rename=True)
        tmp = CEListItem(self._deck.icon_reference, can_move=False, can_rename=False)
        tw.addTopLevelItem(tmp)
        tmp = QtWidgets.QTreeWidgetItem(["Locations"])
        tmp.setFlags(QtCore.Qt.ItemIsEnabled)
        tw.addTopLevelItem(tmp)
        CEListItem(self._deck.default_location_card, parent=tmp, can_move=False, can_rename=False)
        for l in self._deck.locations:
            loc = CEListItem(l, parent=tmp, can_move=True, can_rename=True)
            for c in l.cards:
                CEListItem(c, parent=loc, can_move=True, can_rename=True)

    def update_assetlist(self):
        tw = self.twAssets
        tw.clear()
        if self._deck is None:
            return
        tmp = QtWidgets.QTreeWidgetItem(["Files"])
        tmp.setFlags(QtCore.Qt.ItemIsEnabled)
        tw.addTopLevelItem(tmp)
        for f in self._deck.files:
            CEListItem(f, parent=tmp, can_move=True, can_rename=True)
        tmp = QtWidgets.QTreeWidgetItem(["Images"])
        tmp.setFlags(QtCore.Qt.ItemIsEnabled)
        tw.addTopLevelItem(tmp)
        for i in self._deck.images:
            CEListItem(i, parent=tmp, can_move=True, can_rename=True)
        tmp = QtWidgets.QTreeWidgetItem(["Styles"])
        tmp.setFlags(QtCore.Qt.ItemIsEnabled)
        tw.addTopLevelItem(tmp)
        for s in self._deck.styles:
            CEListItem(s, parent=tmp, can_move=True, can_rename=True)

    def update_asset_props(self):
        # Files, Images, Styles
        if self._current_asset is None:
            self.swAssetProps.setCurrentIndex(0)
            return
        tag = self._current_asset.get_xml_name()
        for i in range(self.swAssetProps.count()):
            if self.swAssetProps.widget(i).objectName() == 'pg' + tag:
                self.swAssetProps.setCurrentIndex(i)
                break
        if tag == 'file':
            self.lblFilename.setText(self._current_asset.name)
            self.lblSize.setText(self._current_asset.get_column_info(1))
        elif tag == 'image':
            pass
        elif tag == 'style':
            pass

    def update_asset_render(self):
        self._gs_asset.clear()
        if self._current_asset is None:
            return

    def current_asset_changed(self, new, dummy):
        if isinstance(new, CEListItem):
            obj = new.get_obj()
        else:
            obj = None
        self._current_asset = obj
        self.update_asset_props()
        self.update_asset_render()

    def update_card_props(self):
        if self._current_card is None:
            self.swCardProps.setCurrentIndex(0)
            return
        tag = self._current_card.get_xml_name()
        for i in range(self.swCardProps.count()):
            if self.swCardProps.widget(i).objectName() == 'pg' + tag:
                self.swCardProps.setCurrentIndex(i)
                break

    def update_card_render(self):
        if self._renderer is None:
            return
        face = "bot"
        if self.actionFrontFace.isChecked():
            face = "top"
        self._renderer.build_card_face_scene(self._current_card, face)
        self.update_zoom()

    def update_zoom(self):
        if self._renderer is None:
            return
        self._renderer.view.resetTransform()
        self._renderer.view.scale(self._zoom, self._zoom)

    def current_card_changed(self, new, dummy):
        if isinstance(new, CEListItem):
            obj = new.get_obj()
        else:
            obj = None
        self._current_card = obj
        self.update_card_props()
        self.update_card_render()
