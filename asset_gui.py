#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#
from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtGui


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


class AssetGui:
    def __init__(self):
        self._current_asset = None

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

    @staticmethod
    def set_value(w: QtWidgets.QDoubleSpinBox, v: int):
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
    def resize_image(image, width):
        if (image.width() < width) and (image.height() < width):
            return image.scaled(image.width(), image.height())
        return image.scaled(width, width, QtCore.Qt.KeepAspectRatio)

    @staticmethod
    def build_color_swatch(rgb):
        img = QtGui.QImage(20, 20, QtGui.QImage.Format_RGB888)
        color = QtGui.QColor(rgb[0], rgb[1], rgb[2])
        img.fill(color)
        return QtGui.QIcon(QtGui.QPixmap.fromImage(img))

    @staticmethod
    def get_alignment(align):
        if align == "center":
            return QtCore.Qt.AlignCenter
        elif align == "left":
            return QtCore.Qt.AlignLeft
        elif align == "right":
            return QtCore.Qt.AlignRight
        return QtCore.Qt.AlignJustify

    @staticmethod
    def split_typeface(name):
        tmp = name.split(":")
        face = tmp[0]
        bold = False
        italic = False
        if len(tmp) > 1:
            italic = "italic" in tmp[1]
            bold = "bold" in tmp[1]
        return face, bold, italic

    @staticmethod
    def build_typeface(family, bold=False, italic=False):
        s = family
        if bold:
            s += ":bold"
            if ':' not in s:
                s += ":"
        if italic:
            if ':' not in s:
                s += ":"
            s += "italic"
        return s

    def typeface_to_font(self, typeface):
        family, bold, italic = self.split_typeface(typeface)
        font = QtGui.QFont(family)
        font.setBold(bold)
        font.setItalic(italic)
        return font

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
            self.lblFileName.setText("File: " + self._current_asset.name)
            self.lblFileFilename.setText("Pathname: " + self._current_asset.filename)
            self.lblFileSize.setText(self._current_asset.get_column_info(1))
            img = self.resize_image(self._current_asset.get_image(), 200)
            self.lblFileImage.setPixmap(QtGui.QPixmap.fromImage(img))
        elif tag == 'image':
            self.lblImgAssetName.setText("Image: " + self._current_asset.name)
            self.lblImgAssetFile.setText("Source file: "  + self._current_asset.file)
            self.leImgAssetX.setText(str(self._current_asset.rectangle[0]))
            self.leImgAssetY.setText(str(self._current_asset.rectangle[1]))
            self.leImgAssetW.setText(str(self._current_asset.rectangle[2]))
            self.leImgAssetH.setText(str(self._current_asset.rectangle[3]))
            img = self._current_asset.get_image(self._deck)
            img = self.resize_image(img, 200)
            self.lbImgAssetImage.setPixmap(QtGui.QPixmap.fromImage(img))
            img = self._current_asset.get_file_image(self._deck, mask=True)
            img = self.resize_image(img, 200)
            self.lbImgAssetFile.setPixmap(QtGui.QPixmap.fromImage(img))
        elif tag == 'style':
            self.lblStyleName.setText("Style: " + self._current_asset.name)
            self.lblStyleTypeface.setText("Typeface: " + self._current_asset.typeface)
            font = self.typeface_to_font(self._current_asset.typeface)
            self.lblStyleTypeface.setFont(font)
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

            self.sbStyleSize.setValue(self._current_asset.typesize)
            self.sbStyleBorderthickness.setValue(self._current_asset.borderthickness)
            self.sbStyleBoundaryoffset.setValue(self._current_asset.boundary_offset)

    def do_as_image_update(self):
        pass

    def do_as_style_update(self):
        pass

    def do_as_style_update_int(self, _):
        self.do_as_style_update()

    def do_as_style_font(self):
        font = self.typeface_to_font(self._current_asset.typeface)
        ok, new_font = QtWidgets.QFontDialog.getFont(font, self)
        if not ok:
            return
        family = new_font.family()
        bold = new_font.bold()
        italic = new_font.italic()
        self._current_asset.typeface = self.build_typeface(family, bold=bold, italic=italic)
        self.update_asset_props()

    def do_as_style_bordercolor(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(*self._current_asset.bordercolor),
                                                self, "Select style border color",
                                                QtWidgets.QColorDialog.ShowAlphaChannel)
        if not color.isValid():
            return
        self._current_asset.bordercolor = [color.red(), color.green(), color.blue(), color.alpha()]
        self.update_asset_props()

    def do_as_style_textcolor(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(*self._current_asset.textcolor),
                                                self, "Select style text color",
                                                QtWidgets.QColorDialog.ShowAlphaChannel)
        if not color.isValid():
            return
        self._current_asset.textcolor = [color.red(), color.green(), color.blue(), color.alpha()]
        self.update_asset_props()

    def do_as_style_fillcolor(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(*self._current_asset.fillcolor),
                                                self, "Select style fill color",
                                                QtWidgets.QColorDialog.ShowAlphaChannel)
        if not color.isValid():
            return
        self._current_asset.fillcolor = [color.red(), color.green(), color.blue(), color.alpha()]
        self.update_asset_props()
