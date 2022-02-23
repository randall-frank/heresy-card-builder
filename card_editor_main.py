#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#

from datetime import date
from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtGui

from ui_card_editor_main import Ui_card_editor_main
from card_objects import build_empty_deck, Deck, Location, Renderable
from card_render import Renderer, ImageRender, TextRender, RectRender


class CERenderableItem(QtWidgets.QListWidgetItem):
    def __init__(self, renderable: Renderable):
        super().__init__()
        self.renderable = renderable
        self.setText(renderable.name)


class CEListItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, obj, parent=None, can_move=True, can_rename=True, can_select=True):
        super().__init__()
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
        self._deck_filename = ''
        self._property_object = None
        self._render_object = None
        self._current_card = None
        self._current_asset = None
        self._current_renderable = None
        self._changing_selection = False
        self._renderer = None
        self._zoom = 1.0

        self.cbStyleLinestyle.clear()
        self.cbStyleLinestyle.addItem("Solid", "solid")
        self.cbStyleLinestyle.addItem("Dash", "dash")
        self.cbStyleLinestyle.addItem("Dot", "dot")
        self.cbStyleLinestyle.addItem("Dash Dot", "dashdot")
        self.cbStyleLinestyle.addItem("Halo outline", "halo")

        self.cbStyleJustification.clear()
        self.cbStyleJustification.addItem("Full", "full")
        self.cbStyleJustification.addItem("Left", "left")
        self.cbStyleJustification.addItem("Right", "right")
        self.cbStyleJustification.addItem("Center", "center")

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

    def do_frontface(self, b: bool):
        self.update_card_render()

    def set_dirty(self, d):
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
            self.lblFileName.setText(self._current_asset.name)
            self.lblFileFilename.setText(self._current_asset.filename)
            self.lblFileSize.setText(self._current_asset.get_column_info(1))
            img = self.resize_image(self._current_asset.image, 200)
            self.lblFileImage.setPixmap(QtGui.QPixmap.fromImage(img))
        elif tag == 'image':
            self.lblImgAssetName.setText(self._current_asset.name)
            self.lblImgAssetFile.setText(self._current_asset.file)
            self.leImgAssetX.setText(str(self._current_asset.rectangle[0]))
            self.leImgAssetY.setText(str(self._current_asset.rectangle[1]))
            self.leImgAssetW.setText(str(self._current_asset.rectangle[2]))
            self.leImgAssetH.setText(str(self._current_asset.rectangle[3]))
            img = self._current_asset.get_image(self._deck)
            img = self.resize_image(img, 200)
            self.lbImgAssetImage.setPixmap(QtGui.QPixmap.fromImage(img))
        elif tag == 'style':
            self.lblStyleName.setText(self._current_asset.name)
            self.lblStyleTypeface.setText(self._current_asset.typeface)

            tmp = self._current_asset.linestyle
            self.cbStyleLinestyle.setCurrentIndex(self.cbStyleLinestyle.findData(tmp))
            tmp = self._current_asset.justification
            self.cbStyleJustification.setCurrentIndex(self.cbStyleJustification.findData(tmp))

            img = self.build_color_swatch(self._current_asset.fillcolor)
            self.lblStyleFillcolor.setPixmap(QtGui.QPixmap.fromImage(img))
            img = self.build_color_swatch(self._current_asset.bordercolor)
            self.lblStyleBordercolor.setPixmap(QtGui.QPixmap.fromImage(img))
            img = self.build_color_swatch(self._current_asset.textcolor)
            self.lblStyleTextcolor.setPixmap(QtGui.QPixmap.fromImage(img))

            self.sbStyleSize.setValue(self._current_asset.typesize)
            self.sbStyleBorderthickness.setValue(self._current_asset.borderthickness)
            self.sbStyleBoundaryoffset.setValue(self._current_asset.boundary_offset)

    @staticmethod
    def resize_image(image, width):
        if (image.width() < width) and (image.height() < width):
            return image.scaled(image.width(), image.height())
        return image.scaled(width, width, QtCore.Qt.KeepAspectRatio)

    @staticmethod
    def build_color_swatch(rgb):
        img = QtGui.QImage(20, 20, QtGui.QImage.Format_RGB888)
        color = QtGui.QColor(rgb[0], rgb[1], rgb[2])
        img.fill(color)
        return img

    def set_current_renderable_target(self, renderable: Renderable):
        self._current_renderable = renderable
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
        self._changing_selection = True
        self._renderer.scene.clearSelection()
        renderable.gfx_list[0].setSelected(True)
        self._changing_selection = False
        self.set_current_renderable_target(renderable)

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

    def current_asset_changed(self, new: CEListItem, dummy):
        if isinstance(new, CEListItem):
            obj = new.get_obj()
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
            self.leImageX.setText(str(rect[0]))
            self.leImageY.setText(str(rect[1]))
            self.leImageW.setText(str(rect[2]))
            self.leImageH.setText(str(rect[3]))
            self.leImageR.setText(str(rot))
            image = self._current_renderable.image
            self.cbImageImage.clear()
            for asset in self._deck.images:
                self.cbImageImage.addItem(asset.name, asset.name)
            self.cbImageImage.setCurrentIndex(self.cbImageImage.findData(image))
        elif isinstance(self._current_renderable, RectRender):
            self.leRectX.setText(str(rect[0]))
            self.leRectY.setText(str(rect[1]))
            self.leRectW.setText(str(rect[2]))
            self.leRectH.setText(str(rect[3]))
            self.leRectR.setText(str(rot))
            style = self._current_renderable.style
            self.cbRectStyle.clear()
            for asset in self._deck.styles:
                self.cbRectStyle.addItem(asset.name, asset.name)
            self.cbRectStyle.setCurrentIndex(self.cbRectStyle.findData(style))
        elif isinstance(self._current_renderable, TextRender):
            self.leTextX.setText(str(rect[0]))
            self.leTextY.setText(str(rect[1]))
            self.leTextW.setText(str(rect[2]))
            self.leTextH.setText(str(rect[3]))
            self.leTextR.setText(str(rot))
            text = self._current_renderable.text
            self.leTextText.setPlainText(text)
            style = self._current_renderable.style
            self.cbTextStyle.clear()
            for asset in self._deck.styles:
                self.cbTextStyle.addItem(asset.name, asset.name)
            self.cbTextStyle.setCurrentIndex(self.cbTextStyle.findData(style))

    def update_card_render(self):
        if self._renderer is None:
            return
        face = "bot"
        if self.actionFrontFace.isChecked():
            face = "top"
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

    def current_card_changed(self, new: CEListItem, dummy):
        if isinstance(new, CEListItem):
            obj = new.get_obj()
        else:
            obj = None
        self._current_card = obj
        self.update_card_render()
