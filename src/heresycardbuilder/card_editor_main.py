#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#
from datetime import date
import io
import json
import threading
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets
from asset_gui import AssetGui
from card_objects import Card, Deck, Face, Renderable, build_empty_deck
from card_render import ImageRender, RectRender, Renderer, TextRender
from dulwich import porcelain
import requests
from utilities import is_directory
from view_widgets import CERenderableItem, CETreeWidgetItem

# TODO:
# create/delete/reorder cards
# text edit insert assets
# text edit insert macro
# verification functions
# export -> PDF, tabletop simulator, png files (+ padding, output directory)


class CardEditorMain(AssetGui):
    def __init__(self, version, parent=None) -> None:
        super(CardEditorMain, self).__init__(parent)
        self._version: str = version
        self._dirty: bool = False
        self._deck_filename: str = ""
        self._property_object = None
        self._render_object = None
        self._current_card = None
        self._current_renderable: Optional[Renderable] = None
        self._changing_selection: bool = False
        self._renderer: Optional[Renderer] = None
        self._zoom: float = 1.0
        self.do_new()
        self.lwGfxItems.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.lwGfxItems.customContextMenuRequested.connect(self.do_renderlist_context_menu)
        self.lwGfxItems.setDragDropMode(QtWidgets.QListWidget.InternalMove)
        self.lwGfxItems.model().rowsMoved.connect(self.do_renderlist_reorder)
        self.toolbar.addAction(self.actionLoad)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionZoomIn)
        self.toolbar.addAction(self.actionZoomOut)
        self.toolbar.addAction(self.actionZoomReset)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionFrontFace)
        self.menuView.aboutToShow.connect(self.update_view_menu)
        self.update_github_repo_list()

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
        self.deck_loaded(build_empty_deck(), "")

    def do_load(self):
        if self._deck and self._dirty:
            s = "There are unsaved changes, are you sure you want to load a new deck?"
            btn = QtWidgets.QMessageBox.question(self, "Load a new deck", s)
            if btn != QtWidgets.QMessageBox.Yes:
                return
        tmp = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load deck", "", "Card deck (*.deck);;All files (*)"
        )
        if len(tmp[0]) == 0:
            return
        filename = tmp[0]
        tmp = Deck()
        if not tmp.load(filename):
            QtWidgets.QMessageBox.critical(
                self, "Unable to load deck", "An error occurred while loading the deck"
            )
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
        tmp = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save deck as", "Untitled.deck", "Card deck (*.deck);;All files (*)"
        )
        if len(tmp[0]) == 0:
            return
        filename = tmp[0]
        if not self._deck.save(filename):
            QtWidgets.QMessageBox.critical(
                self, "Unable to save deck", "An error occurred while saving the deck"
            )
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
            QtWidgets.QMessageBox.critical(
                self, "Unable to save deck", "An error occurred while saving the deck"
            )
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
        CETreeWidgetItem(
            self._deck.default_location_card, parent=tmp, can_move=False, can_rename=False
        )
        for location in self._deck.locations:
            loc = CETreeWidgetItem(location, parent=tmp)
            for c in location.cards:
                CETreeWidgetItem(c, parent=loc)

    def set_current_renderable_target(
        self, renderable: Optional[Renderable], selection_only: bool = False
    ):
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
        # callback on QModel for drop operation
        self.rebuild_renderlist_from_list_widget()

    def rebuild_renderlist_from_list_widget(self):
        # rebuild the renderable list based on the new model order
        is_background_card = self.current_card().is_background()
        underlay = True
        item_list = list()
        for idx in range(self.lwGfxItems.count()):
            item = self.lwGfxItems.item(idx)
            if item.renderable:
                # if we are processing a background card, update the underlay flags
                if is_background_card:
                    item.renderable.underlay = underlay
                item_list.append(item.renderable)
            else:
                # this would be the dividing line item
                underlay = False
        face = self.current_card_face()
        face.renderables = item_list
        # update the rendering order
        face.recompute_renderable_order(background=is_background_card)
        self.update_card_render()

    def do_renderlist_context_menu(self, pos: QtCore.QPoint):
        # lwGfxItems
        menu = QtWidgets.QMenu(self)
        item = self.lwGfxItems.itemAt(pos)
        if item:
            if item.is_separator():
                return
            item.setSelected(True)
            remove = menu.addAction(f"Remove {item.text()}")
        else:
            remove = None
        add_rect = menu.addAction("New rectangle")
        add_image = menu.addAction("New image")
        add_text = menu.addAction("New text box")
        action = menu.exec(self.lwGfxItems.mapToGlobal(pos))
        if action is None:
            return
        face = self.current_card_face()
        renderable = None
        idx = len(face.renderables)
        if item:
            renderable = item.renderable
            idx = face.renderables.index(renderable)
        if action == remove:
            face.renderables.remove(renderable)
            renderable = None
        elif action == add_rect:
            renderable = RectRender()
            face.renderables.insert(idx, renderable)
        elif action == add_text:
            renderable = TextRender()
            face.renderables.insert(idx, renderable)
        elif action == add_image:
            renderable = ImageRender()
            face.renderables.insert(idx, renderable)
        is_background_card = self.current_card().is_background()
        face.recompute_renderable_order(background=is_background_card)
        self.update_card_render()
        # update the selection and the underlay flags
        underlay = True
        for idx in range(self.lwGfxItems.count()):
            item = self.lwGfxItems.item(idx)
            if item.renderable:
                # if we are processing a background card, update the underlay flags
                if is_background_card:
                    item.renderable.underlay = underlay
                if item.renderable == renderable:
                    self.lwGfxItems.setCurrentRow(idx)
            else:
                # this would be the dividing line item
                underlay = False

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
            if self.swGfxItemProps.widget(i).objectName() == "pg_" + name:
                self.swGfxItemProps.setCurrentIndex(i)
                break
        if name == "none":
            return
        # Update the page widgets
        rect = self._current_renderable.rectangle
        rot = self._current_renderable.rotation
        if isinstance(self._current_renderable, ImageRender):
            self.set_value(self.sbImageX, rect[0])
            self.set_value(self.sbImageY, rect[1])
            self.set_value(self.sbImageW, rect[2])
            self.set_value(self.sbImageH, rect[3])
            self.set_value(self.dsImageR, rot)
            image = self._current_renderable.image
            self.init_combo(self.cbImageImage, image, "images")

        elif isinstance(self._current_renderable, RectRender):
            self.set_value(self.sbRectX, rect[0])
            self.set_value(self.sbRectY, rect[1])
            self.set_value(self.sbRectW, rect[2])
            self.set_value(self.sbRectH, rect[3])
            self.set_value(self.dsRectR, rot)
            style = self._current_renderable.style
            self.init_combo(self.cbRectStyle, style, "styles")

        elif isinstance(self._current_renderable, TextRender):
            self.set_value(self.sbTextX, rect[0])
            self.set_value(self.sbTextY, rect[1])
            self.set_value(self.sbTextW, rect[2])
            self.set_value(self.sbTextH, rect[3])
            self.set_value(self.dsTextR, rot)
            text = self._current_renderable.text
            self.set_plaintext(self.leTextText, text)
            style = self._current_renderable.style
            self.init_combo(self.cbTextStyle, style, "styles")

    def do_rect_update(self):
        renderable = self._current_renderable
        if renderable is None:
            return
        rect, rot = self.get_rect_rot(
            self.sbRectX, self.sbRectY, self.sbRectW, self.sbRectH, self.dsRectR
        )
        style = self.get_cb_data(self.cbRectStyle)
        renderable.style = style
        renderable.rectangle = rect
        renderable.rotation = rot
        self._renderer.update_gfx_items(self._current_card, renderable)

    def do_image_update(self):
        renderable = self._current_renderable
        if renderable is None:
            return
        rect, rot = self.get_rect_rot(
            self.sbImageX, self.sbImageY, self.sbImageW, self.sbImageH, self.dsImageR
        )
        image = self.get_cb_data(self.cbImageImage)
        renderable.image = image
        renderable.rectangle = rect
        renderable.rotation = rot
        self._renderer.update_gfx_items(self._current_card, renderable)

    def do_text_update(self):
        renderable = self._current_renderable
        if renderable is None:
            return
        rect, rot = self.get_rect_rot(
            self.sbTextX, self.sbTextY, self.sbTextW, self.sbTextH, self.dsTextR
        )
        style = self.get_cb_data(self.cbTextStyle)
        renderable.style = style
        renderable.rectangle = rect
        renderable.rotation = rot
        renderable.text = self.leTextText.toPlainText()
        self._renderer.update_gfx_items(self._current_card, renderable)

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

    def current_card(self) -> Card:
        return self._current_card

    def current_card_face(self) -> Face:
        if self._current_card is None:
            return None
        face: Face = self._current_card.bot_face
        if self.actionFrontFace.isChecked():
            face = self._current_card.top_face
        return face

    def current_card_face_name(self) -> Optional[str]:
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
        self.update_zoom()
        self.lwGfxItems.clear()

        # is it a background card (should overlay checkbox be visible)
        is_background = False
        previous_underlay = True
        if self.current_card():
            is_background = self.current_card().is_background()
        for renderable in render_list:
            if is_background:
                if previous_underlay and not renderable.underlay:
                    separator = CERenderableItem(None)
                    self.lwGfxItems.addItem(separator)
                    previous_underlay = False
            item = CERenderableItem(renderable)
            self.lwGfxItems.addItem(item)
            self._renderer.update_gfx_items(self.current_card(), renderable)
        if is_background and previous_underlay:
            separator = CERenderableItem(None)
            self.lwGfxItems.addItem(separator)
        self.set_current_renderable_target(None)

    def update_zoom(self):
        if self._renderer is None:
            return
        self._renderer.view.resetTransform()
        self._renderer.view.scale(self._zoom, self._zoom)
        self._renderer.view.setProperty("CARD_SCALE", self._zoom)

    def current_card_changed(self, new: CETreeWidgetItem, _):
        if isinstance(new, CETreeWidgetItem):
            obj = new.obj
        else:
            obj = None
        self._current_card = obj
        self.update_card_render()

    def update_view_menu(self):
        tmp = "Front face"
        if self.actionFrontFace.isChecked():
            tmp = "Back face"
        self.actionFrontFace.setText(tmp)

    def update_github_repo_list(self):
        # Query for repos that have the "heresycarddeck" topic set
        url = "https://api.github.com/search/repositories?q=topic:heresycarddeck"
        r = requests.get(url)
        if r.status_code == 200:
            info = json.loads(r.text)
            for item in info.get("items", []):
                target = item.get("clone_url", "")
                if target:
                    action = QtGui.QAction(item.get("full_name", "Unknown name"), self)
                    action.setProperty("github", target)
                    action.triggered.connect(self.handle_github_download)
                    self.menuDownload.addAction(action)

    def handle_github_download(self, _) -> None:
        action = self.sender()
        url = action.property("github")
        destination = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select an empty directory to save into..."
        )
        if destination:
            if not is_directory(destination, empty=True):
                QtWidgets.QMessageBox.critical(
                    self,
                    "Not an empty directory",
                    "The selected path is not a directory or is not empty.",
                )
                return
            output = dict()
            thread = threading.Thread(target=self.download, args=(url, destination, output))
            dlg = QtWidgets.QProgressDialog(
                "Downloading content via git clone.", "", 0, 0, parent=self
            )
            dlg.setWindowTitle("Downloading")
            dlg.setModal(True)
            dlg.show()
            thread.start()
            while thread.is_alive():
                QtWidgets.QApplication.instance().processEvents()
            thread.join()
            dlg.close()
            error_txt = output.get("error", "")
            if error_txt:
                QtWidgets.QMessageBox.critical(
                    self, "Clone error", f"The selected repo could not be cloned ({error_txt})."
                )
            else:
                QtWidgets.QMessageBox.information(
                    self, "Success", "The selected repo has been successfully cloned."
                )

    def download(self, url: str, destination: str, result: dict) -> None:
        buffer = io.BytesIO()
        try:
            porcelain.clone(url, destination, errstream=buffer)
        except Exception as e:
            result["error"] = str(e)
        result["stderr"] = buffer.getvalue().decode("ascii")
