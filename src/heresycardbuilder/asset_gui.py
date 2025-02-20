#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#
from typing import List, Optional, Tuple, Union

from PySide6 import QtCore, QtGui, QtWidgets
from card_objects import Deck, File, Image, Style
from ui_card_editor_main import Ui_card_editor_main
from view_widgets import CETreeWidgetItem


class AssetGui(QtWidgets.QMainWindow, Ui_card_editor_main):
    def __init__(self, parent) -> None:
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self._deck: Optional[Deck] = None
        self._current_asset: Union[File, Image, Style, None] = None

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

        self.twAssets.itemChanged.connect(self.asset_name_changed)

    def set_card_dirty(self):
        pass

    def init_combo(self, w: QtWidgets.QComboBox, value: str, assets: str):
        tmp = w.blockSignals(True)
        w.clear()
        if assets == "images":
            if self._deck:
                for image in self._deck.images:
                    icon = QtGui.QIcon(image.get_pixmap(self._deck))
                    w.addItem(icon, image.name, image.name)
        elif assets == "files":
            if self._deck:
                for fileobj in self._deck.files:
                    w.addItem(fileobj.name, fileobj.name)
        elif assets == "styles":
            if self._deck:
                for style in self._deck.styles:
                    w.addItem(style.name, style.name)
                    idx = w.count() - 1
                    font = QtGui.QFont(style.typeface)
                    w.setItemData(idx, font, QtCore.Qt.FontRole)
                    back = QtGui.QBrush(QtGui.QColor(*style.fillcolor))
                    w.setItemData(idx, back, QtCore.Qt.BackgroundRole)
                    front = QtGui.QBrush(QtGui.QColor(*style.textcolor))
                    w.setItemData(idx, front, QtCore.Qt.ForegroundRole)
                    align = self.get_alignment(style.justification)
                    w.setItemData(idx, align, QtCore.Qt.TextAlignmentRole)
        w.setCurrentIndex(w.findData(value))
        w.blockSignals(tmp)

    @staticmethod
    def get_cb_data(s: QtWidgets.QComboBox) -> str:
        idx = s.currentIndex()
        return s.itemData(idx)

    @staticmethod
    def set_value(w: Union[QtWidgets.QDoubleSpinBox, QtWidgets.QSpinBox], v: int):
        tmp = w.blockSignals(True)
        w.setValue(v)
        w.blockSignals(tmp)

    @staticmethod
    def set_plaintext(w: QtWidgets.QPlainTextEdit, s: str):
        tmp = w.blockSignals(True)
        w.setPlainText(s)
        w.blockSignals(tmp)

    @staticmethod
    def set_text(w: QtWidgets.QLineEdit, s: str):
        tmp = w.blockSignals(True)
        w.setText(s)
        w.blockSignals(tmp)

    @staticmethod
    def get_int(s: str, default: int = 0) -> int:
        try:
            i = int(s)
        except ValueError:
            i = default
        return i

    @staticmethod
    def get_rect_rot(
        x: Union[QtWidgets.QSpinBox, QtWidgets.QLineEdit],
        y: Union[QtWidgets.QSpinBox, QtWidgets.QLineEdit],
        w: Union[QtWidgets.QSpinBox, QtWidgets.QLineEdit],
        h: Union[QtWidgets.QSpinBox, QtWidgets.QLineEdit],
        r: Optional[QtWidgets.QDoubleSpinBox],
    ) -> Tuple[List[int], int]:
        if isinstance(x, QtWidgets.QLineEdit):
            rect = [
                AssetGui.get_int(x.text()),
                AssetGui.get_int(y.text()),
                AssetGui.get_int(w.text()),
                AssetGui.get_int(h.text()),
            ]
        else:
            rect = [x.value(), y.value(), w.value(), h.value()]
        rot = 0
        if r:
            rot = int(r.value())
        return rect, rot

    @staticmethod
    def resize_image(image: QtGui.QImage, width: int) -> QtGui.QImage:
        if (image.width() < width) and (image.height() < width):
            return image.scaled(image.width(), image.height())
        return image.scaled(width, width, QtCore.Qt.KeepAspectRatio)

    @staticmethod
    def build_color_swatch(rgb: List[int]) -> QtGui.QIcon:
        img = QtGui.QImage(20, 20, QtGui.QImage.Format_RGB888)
        color = QtGui.QColor(rgb[0], rgb[1], rgb[2])
        img.fill(color)
        return QtGui.QIcon(QtGui.QPixmap.fromImage(img))

    @staticmethod
    def get_alignment(align: str) -> QtCore.Qt.AlignmentFlag:
        if align == "center":
            return QtCore.Qt.AlignCenter
        elif align == "left":
            return QtCore.Qt.AlignLeft
        elif align == "right":
            return QtCore.Qt.AlignRight
        return QtCore.Qt.AlignJustify

    @staticmethod
    def split_typeface(name: str) -> Tuple[str, bool, bool]:
        tmp = name.split(":")
        face = tmp[0]
        bold = False
        italic = False
        if len(tmp) > 1:
            italic = "italic" in tmp[1]
            bold = "bold" in tmp[1]
        return face, bold, italic

    @staticmethod
    def build_typeface(family: str, bold=False, italic=False) -> str:
        s = family
        if bold:
            s += ":bold"
            if ":" not in s:
                s += ":"
        if italic:
            if ":" not in s:
                s += ":"
            s += "italic"
        return s

    def typeface_to_font(self, typeface: str) -> QtGui.QFont:
        family, bold, italic = self.split_typeface(typeface)
        font = QtGui.QFont(family)
        font.setBold(bold)
        font.setItalic(italic)
        return font

    @staticmethod
    def root_item(item: QtWidgets.QTreeWidgetItem, column: int, user: str):
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        item.setData(column, QtCore.Qt.UserRole, user)
        font = item.font(column)
        font.setBold(True)
        item.setFont(column, font)

    def update_assetlist(self):
        tw = self.twAssets
        tw.clear()
        if self._deck is None:
            return
        tmp = QtWidgets.QTreeWidgetItem(["Files"])
        self.root_item(tmp, 0, "File")
        tw.addTopLevelItem(tmp)
        for f in self._deck.files:
            CETreeWidgetItem(f, parent=tmp, can_rename=not f.filename.startswith(":"))
        tmp = QtWidgets.QTreeWidgetItem(["Images"])
        self.root_item(tmp, 0, "Image")
        tw.addTopLevelItem(tmp)
        for i in self._deck.images:
            CETreeWidgetItem(i, parent=tmp)
        tmp = QtWidgets.QTreeWidgetItem(["Styles"])
        self.root_item(tmp, 0, "Style")
        tw.addTopLevelItem(tmp)
        for s in self._deck.styles:
            CETreeWidgetItem(s, parent=tmp, can_rename=not (s.name == "default"))

    def update_asset_props(self):
        # Files, Images, Styles
        if self._current_asset is None:
            self.swAssetProps.setCurrentIndex(0)
            return
        tag = self._current_asset.get_xml_name()
        for i in range(self.swAssetProps.count()):
            if self.swAssetProps.widget(i).objectName() == "pg" + tag:
                self.swAssetProps.setCurrentIndex(i)
                break
        if tag == "file":
            self.lblFileName.setText("File: " + self._current_asset.name)
            self.lblFileFilename.setText("Pathname: " + self._current_asset.filename)
            self.lblFileSize.setText(self._current_asset.get_column_info(1))
            img = self.resize_image(self._current_asset.get_image(), 200)
            self.lblFileImage.setPixmap(QtGui.QPixmap.fromImage(img))
            self.pbSelectFile.setEnabled(not self._current_asset.filename.startswith(":"))
        elif tag == "image":
            self.lblImgAssetName.setText("Image: " + self._current_asset.name)
            # self.lblImgAssetFile.setText("Source file: " + self._current_asset.file)
            self.lblImgAssetFile.setText("Source file:")
            self.leImgAssetX.setText(str(self._current_asset.rectangle[0]))
            self.leImgAssetY.setText(str(self._current_asset.rectangle[1]))
            self.leImgAssetW.setText(str(self._current_asset.rectangle[2]))
            self.leImgAssetH.setText(str(self._current_asset.rectangle[3]))
            self.init_combo(self.cbImgAssetFile, self._current_asset.file, "files")
            self.update_image_images()
        elif tag == "style":
            self.lblStyleName.setText("Style: " + self._current_asset.name)
            self.lblStyleTypeface.setText(self._current_asset.typeface)
            font = self.typeface_to_font(self._current_asset.typeface)
            self.lblStyleTypeface.setFont(font)
            self.lblStyleSize.setText(f" Point size: {self._current_asset.typesize}")

            tmp = self._current_asset.linestyle
            self.cbStyleLinestyle.setCurrentIndex(self.cbStyleLinestyle.findData(tmp))
            tmp = self._current_asset.justification
            self.cbStyleJustification.setCurrentIndex(self.cbStyleJustification.findData(tmp))

            icon = self.build_color_swatch(self._current_asset.fillcolor)
            self.pbStyleFillcolor.setIcon(icon)
            icon = self.build_color_swatch(self._current_asset.bordercolor)
            self.pbStyleBordercolor.setIcon(icon)
            icon = self.build_color_swatch(self._current_asset.textcolor)
            self.pbStyleTextcolor.setIcon(icon)

            self.sbStyleBorderthickness.setValue(self._current_asset.borderthickness)
            self.sbStyleBoundaryoffset.setValue(self._current_asset.boundary_offset)

    def update_image_images(self):
        img = self._current_asset.get_image(self._deck)
        img = self.resize_image(img, 200)
        self.lbImgAssetImage.setPixmap(QtGui.QPixmap.fromImage(img))
        img = self._current_asset.get_file_image(self._deck, mask=True)
        img = self.resize_image(img, 200)
        self.lbImgAssetFile.setPixmap(QtGui.QPixmap.fromImage(img))

    def asset_name_changed(self, item: QtWidgets.QTreeWidgetItem, _) -> None:
        if not isinstance(item, CETreeWidgetItem):
            return
        obj = item.obj
        obj.name = item.text(0)
        self.update_asset_props()

    def do_as_file_select(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select image file",
            self._current_asset.get_full_pathname(self._deck),
            "Images (*.png *.jpg)",
        )
        if filename[0]:
            try:
                self._current_asset.load_file(self._deck, filename[0])
                self.update_asset_props()
            except Exception:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Unable to load image",
                    f"An error occurred while reading the file: '{filename[0]}'.",
                )

    def do_as_image_update(self):
        if self._current_asset is None:
            return
        rect, _ = self.get_rect_rot(
            self.leImgAssetX, self.leImgAssetY, self.leImgAssetW, self.leImgAssetH, None
        )
        self._current_asset.rectangle = rect
        filename = self.get_cb_data(self.cbImgAssetFile)
        self._current_asset.file = filename
        self.update_image_images()
        self.set_card_dirty()

    def do_as_image_update_int(self, _):
        self.do_as_image_update()

    def do_as_style_update(self):
        if self._current_asset is None:
            return
        self._current_asset.borderthickness = self.sbStyleBorderthickness.value()
        self._current_asset.boundary_offset = self.sbStyleBoundaryoffset.value()
        self._current_asset.linestyle = self.get_cb_data(self.cbStyleLinestyle)
        self._current_asset.justification = self.get_cb_data(self.cbStyleJustification)
        self.set_card_dirty()

    def do_as_style_update_int(self, _):
        self.do_as_style_update()

    def do_as_style_font(self):
        font = self.typeface_to_font(self._current_asset.typeface)
        font.setPointSize(self._current_asset.typesize)
        ok, new_font = QtWidgets.QFontDialog.getFont(font, self)
        if not ok:
            return
        family = new_font.family()
        bold = new_font.bold()
        italic = new_font.italic()
        self._current_asset.typeface = self.build_typeface(family, bold=bold, italic=italic)
        self._current_asset.typesize = new_font.pointSize()
        self.update_asset_props()
        self.set_card_dirty()

    def do_as_style_bordercolor(self):
        color = QtWidgets.QColorDialog.getColor(
            QtGui.QColor(*self._current_asset.bordercolor),
            self,
            "Select style border color",
            QtWidgets.QColorDialog.ShowAlphaChannel,
        )
        if not color.isValid():
            return
        self._current_asset.bordercolor = [color.red(), color.green(), color.blue(), color.alpha()]
        self.update_asset_props()
        self.set_card_dirty()

    def do_as_style_textcolor(self):
        color = QtWidgets.QColorDialog.getColor(
            QtGui.QColor(*self._current_asset.textcolor),
            self,
            "Select style text color",
            QtWidgets.QColorDialog.ShowAlphaChannel,
        )
        if not color.isValid():
            return
        self._current_asset.textcolor = [color.red(), color.green(), color.blue(), color.alpha()]
        self.update_asset_props()
        self.set_card_dirty()

    def do_as_style_fillcolor(self):
        color = QtWidgets.QColorDialog.getColor(
            QtGui.QColor(*self._current_asset.fillcolor),
            self,
            "Select style fill color",
            QtWidgets.QColorDialog.ShowAlphaChannel,
        )
        if not color.isValid():
            return
        self._current_asset.fillcolor = [color.red(), color.green(), color.blue(), color.alpha()]
        self.update_asset_props()
        self.set_card_dirty()
