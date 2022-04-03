#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#

from datetime import date
from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtGui

from card_objects import build_empty_deck, Deck, Renderable, Face
from card_render import Renderer, ImageRender, TextRender, RectRender
from asset_gui import AssetGui
from view_widgets import CETreeWidgetItem, CERenderableItem

from typing import Optional

# TODO:
# create/delete/reorder cards
# text edit insert assets
# text edit insert macro
# verification functions
# export -> PDF, tabletop simulator, png files (+ padding, output directory)


class CardEditorMain(AssetGui):
    def __init__(self, version, parent=None):
        super(CardEditorMain, self).__init__(parent)
        self._version: str = version
        self._dirty: bool = False
        self._deck_filename: str = ''
        self._property_object = None
        self._render_object = None
        self._current_card = None
        self._current_renderable: bool = None
        self._changing_selection: bool = False
        self._renderer: Renderer = None
        self._zoom: float = 1.0
        self.do_new()
        self.lwGfxItems.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.lwGfxItems.customContextMenuRequested.connect(self.do_renderlist_context_menu)
        self.lwGfxItems.setDragDropMode(QtWidgets.QListWidget.InternalMove)
        self.lwGfxItems.model().rowsMoved.connect(self.do_renderlist_reorder)

    def set_card_dirty(self):
        self.update_card_render()

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
        self.deck_loaded(build_empty_deck(), '')

    def do_load(self):
        if self._deck and self._dirty:
            s = "There are unsaved changes, are you sure you want to load a new deck?"
            btn = QtWidgets.QMessageBox.question(self, "Load a new deck", s)
            if btn != QtWidgets.QMessageBox.Yes:
                return
        tmp = QtWidgets.QFileDialog.getOpenFileName(self, "Load deck", "",
                                                    "Card deck (*.deck);;All files (*)")
        if len(tmp[0]) == 0:
            return
        filename = tmp[0]
        tmp = Deck()
        if not tmp.load(filename):
            QtWidgets.QMessageBox.critical(self, "Unable to load deck",
                                           "An error occurred while loading the deck")
            return
        self.deck_loaded(tmp, filename)

    def deck_loaded(self, deck: Deck, filename: str):
        self._deck = deck
        self.twAssets.deck = self._deck
        self.twCards.deck = self._deck
        self._renderer = Renderer(self._deck, parent=self.wCardView)
        self._renderer.scene.selectionChanged.connect(self.do_gfx_item_selection_changed)
        self._deck_filename = filename
        self._dirty = False
        self.lblInfo.setText("Deck: " + filename)
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
        if not self._deck_filename:
            self.do_saveas()
            return
        if not self._deck.save(self._deck_filename):
            QtWidgets.QMessageBox.critical(self, "Unable to save deck",
                                           "An error occurred while saving the deck")
            return
        self._dirty = False

    def do_frontface(self, _):
        self.update_card_render()

    def set_dirty(self, d: bool):
        self._dirty = d

    @QtCore.Slot()
    def do_about(self):
        s = "T.I.M.E Stories card editor\n"
        s += f"Copyright (C) 2017-{date.today().year} Randall Frank\n"
        s += "Version: " + self._version
        QtWidgets.QMessageBox.about(self, "Card Editor", s)

    def closeEvent(self, event: QtGui.QCloseEvent):
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
        self.swAssetProps.setCurrentIndex(0)
        self.update_assetlist()
        self.update_asset_props()
        self.update_cardlist()
        self.update_card_render()

    @staticmethod
    def card_root_item(item: QtWidgets.QTreeWidgetItem):
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)

    def update_cardlist(self):
        tw = self.twCards
        tw.clear()
        if self._deck is None:
            return
        self._deck.renumber_entities()
        tmp = CETreeWidgetItem(self._deck.default_card, can_move=False, can_rename=False)
        tw.addTopLevelItem(tmp)
        tmp = QtWidgets.QTreeWidgetItem(["Deck cards"])
        self.card_root_item(tmp)
        tw.addTopLevelItem(tmp)
        for i in self._deck.deckcards:
            CETreeWidgetItem(i, parent=tmp)
        tmp = QtWidgets.QTreeWidgetItem(["Base Cards"])
        self.card_root_item(tmp)
        tw.addTopLevelItem(tmp)
        for i in self._deck.base:
            CETreeWidgetItem(i, parent=tmp)
        tmp = QtWidgets.QTreeWidgetItem(["Item Cards"])
        self.card_root_item(tmp)
        tw.addTopLevelItem(tmp)
        CETreeWidgetItem(self._deck.default_item_card, parent=tmp, can_move=False, can_rename=False)
        for i in self._deck.items:
            CETreeWidgetItem(i, parent=tmp)
        tmp = QtWidgets.QTreeWidgetItem(["Plan Cards"])
        self.card_root_item(tmp)
        tw.addTopLevelItem(tmp)
        for p in self._deck.plan:
            CETreeWidgetItem(p, parent=tmp)
        tmp = QtWidgets.QTreeWidgetItem(["Misc Cards"])
        self.card_root_item(tmp)
        tw.addTopLevelItem(tmp)
        for c in self._deck.misc:
            CETreeWidgetItem(c, parent=tmp)
        tmp = QtWidgets.QTreeWidgetItem(["Characters"])
        self.card_root_item(tmp)
        tw.addTopLevelItem(tmp)
        for c in self._deck.characters:
            CETreeWidgetItem(c, parent=tmp)
        tmp = CETreeWidgetItem(self._deck.icon_reference, can_move=False, can_rename=False)
        tw.addTopLevelItem(tmp)
        tmp = QtWidgets.QTreeWidgetItem(["Locations"])
        self.card_root_item(tmp)
        tw.addTopLevelItem(tmp)
        CETreeWidgetItem(self._deck.default_location_card, parent=tmp, can_move=False, can_rename=False)
        for location in self._deck.locations:
            loc = CETreeWidgetItem(location, parent=tmp)
            for c in location.cards:
                CETreeWidgetItem(c, parent=loc)

    def set_current_renderable_target(self, renderable: Optional[Renderable], selection_only: bool = False):
        self._current_renderable = renderable
        if self._current_renderable:
            self._changing_selection = True
            self._renderer.scene.clearSelection()
            renderable.gfx_list[0].setSelected(True)
            self._changing_selection = False
        if selection_only:
            return
        self.update_current_renderable_props()

    def current_card_renderable_changed(self, row: int):
        # there has been a change in the renderable selection via list widget
        if self._changing_selection:
            return
        item = self.lwGfxItems.item(row)
        if item is None:
            self.set_current_renderable_target(None)
            return
        renderable = item.renderable
        self.set_current_renderable_target(renderable)

    def do_renderlist_reorder(self, parent, start, end, dest, row):
        item = self.lwGfxItems.item(row)
        renderable = item.renderable
        face = self.current_card_face()
        item_list = list()
        for idx in range(self.lwGfxItems.count()):
            item = self.lwGfxItems.item(idx)
            item_list.append(item.renderable)
        face.renderables = item_list
        self.update_card_render()
        for idx in range(self.lwGfxItems.count()):
            item = self.lwGfxItems.item(idx)
            if item.renderable == renderable:
                self.lwGfxItems.setCurrentRow(idx)

    def do_renderlist_context_menu(self, pos: QtCore.QPoint):
        # lwGfxItems
        item = self.lwGfxItems.itemAt(pos)
        if item is None:
            return
        item.setSelected(True)
        menu = QtWidgets.QMenu(self)
        top = menu.addAction("Move to top")
        up = menu.addAction("Move up")
        down = menu.addAction("Move down")
        bot = menu.addAction("Move to bottom")
        action = menu.exec(self.lwGfxItems.mapToGlobal(pos))
        if action is None:
            return
        renderable = item.renderable
        face = self.current_card_face()
        idx = face.renderables.index(renderable)
        face.renderables.remove(renderable)
        if action == top:
            face.renderables.append(renderable)
        elif action == up:
            face.renderables.insert(idx + 1, renderable)
        elif action == bot:
            face.renderables.insert(0, renderable)
        elif action == down:
            face.renderables.insert(max(idx - 1, 0), renderable)
        self.update_card_render()
        for idx in range(self.lwGfxItems.count()):
            item = self.lwGfxItems.item(idx)
            if item.renderable == renderable:
                self.lwGfxItems.setCurrentRow(idx)

    def do_gfx_item_selection_changed(self):
        # there has been a change in renderable selection in the gfx area
        if self._changing_selection:
            return
        new_current_item = None
        items = self._renderer.scene.selectedItems()
        if len(items):
            renderable = items[0].data(0)
            for i in range(self.lwGfxItems.count()):
                gui_item = self.lwGfxItems.item(i)
                if gui_item.renderable == renderable:
                    new_current_item = gui_item
        self._changing_selection = True
        self.lwGfxItems.setCurrentItem(new_current_item)
        if new_current_item is None:
            self.set_current_renderable_target(None)
        else:
            self.set_current_renderable_target(new_current_item.renderable)
        self._changing_selection = False

    def current_asset_changed(self, new: CETreeWidgetItem, _):
        if isinstance(new, CETreeWidgetItem):
            obj = new.obj
        else:
            obj = None
        self._current_asset = obj
        self.update_asset_props()

    def update_current_renderable_props(self):
        name = "none"
        if self._current_renderable:
            name = self._current_renderable.get_xml_name()
        for i in range(self.swGfxItemProps.count()):
            if self.swGfxItemProps.widget(i).objectName() == 'pg_' + name:
                self.swGfxItemProps.setCurrentIndex(i)
                break
        if name == "none":
            return
        # Update the page widgets
        rect = self._current_renderable.rectangle
        rot = self._current_renderable.rotation
        if isinstance(self._current_renderable, ImageRender):
            self.set_text(self.leImageX, str(rect[0]))
            self.set_text(self.leImageY, str(rect[1]))
            self.set_text(self.leImageW, str(rect[2]))
            self.set_text(self.leImageH, str(rect[3]))
            self.set_value(self.dsImageR, rot)
            image = self._current_renderable.image
            self.init_combo(self.cbImageImage, image, 'images')

        elif isinstance(self._current_renderable, RectRender):
            self.set_text(self.leRectX, str(rect[0]))
            self.set_text(self.leRectY, str(rect[1]))
            self.set_text(self.leRectW, str(rect[2]))
            self.set_text(self.leRectH, str(rect[3]))
            self.set_value(self.dsRectR, rot)
            style = self._current_renderable.style
            self.init_combo(self.cbRectStyle, style, 'styles')

        elif isinstance(self._current_renderable, TextRender):
            self.set_text(self.leTextX, str(rect[0]))
            self.set_text(self.leTextY, str(rect[1]))
            self.set_text(self.leTextW, str(rect[2]))
            self.set_text(self.leTextH, str(rect[3]))
            self.set_value(self.dsTextR, rot)
            text = self._current_renderable.text
            self.set_plaintext(self.leTextText, text)
            style = self._current_renderable.style
            self.init_combo(self.cbTextStyle, style, 'styles')

    def do_rect_update(self):
        renderable = self._current_renderable
        if renderable is None:
            return
        rect, rot = self.get_rect_rot(self.leRectX, self.leRectY, self.leRectW, self.leRectH, self.dsRectR)
        style = self.get_cb_data(self.cbRectStyle)
        renderable.style = style
        renderable.rectangle = rect
        renderable.rotation = rot
        self._renderer.update_gfx_items(renderable)

    def do_image_update(self):
        renderable = self._current_renderable
        if renderable is None:
            return
        rect, rot = self.get_rect_rot(self.leImageX, self.leImageY, self.leImageW, self.leImageH, self.dsImageR)
        image = self.get_cb_data(self.cbImageImage)
        renderable.image = image
        renderable.rectangle = rect
        renderable.rotation = rot
        self._renderer.update_gfx_items(renderable)

    def do_text_update(self):
        renderable = self._current_renderable
        if renderable is None:
            return
        rect, rot = self.get_rect_rot(self.leTextX, self.leTextY, self.leTextW, self.leTextH, self.dsTextR)
        style = self.get_cb_data(self.cbTextStyle)
        renderable.style = style
        renderable.rectangle = rect
        renderable.rotation = rot
        renderable.text = self.leTextText.toPlainText()
        self._renderer.update_gfx_items(renderable)

    def do_rect_update_int(self, _):
        self.do_rect_update()

    def do_image_update_int(self, _):
        self.do_image_update()

    def do_text_update_int(self, _):
        self.do_text_update()

    def do_rect_update_double(self, _):
        self.do_rect_update()

    def do_image_update_double(self, _):
        self.do_image_update()

    def do_text_update_double(self, _):
        self.do_text_update()

    def current_card_face(self) -> Face:
        if self._current_card is None:
            return None
        face: Face = self._current_card.bot_face
        if self.actionFrontFace.isChecked():
            face = self._current_card.top_face
        return face

    def current_card_face_name(self) -> str:
        if self._current_card is None:
            return None
        face = "bot"
        if self.actionFrontFace.isChecked():
            face = "top"
        return face

    def update_card_render(self):
        if self._renderer is None:
            return
        face = self.current_card_face_name()
        if face is None:
            return
        render_list = self._renderer.build_card_face_scene(self._current_card, face)
        self.lwGfxItems.clear()
        for renderable in render_list:
            item = CERenderableItem(renderable)
            self.lwGfxItems.addItem(item)
        self.update_zoom()
        self.set_current_renderable_target(None)

    def update_zoom(self):
        if self._renderer is None:
            return
        self._renderer.view.resetTransform()
        self._renderer.view.scale(self._zoom, self._zoom)

    def current_card_changed(self, new: CETreeWidgetItem, _):
        if isinstance(new, CETreeWidgetItem):
            obj = new.obj
        else:
            obj = None
        self._current_card = obj
        self.update_card_render()
