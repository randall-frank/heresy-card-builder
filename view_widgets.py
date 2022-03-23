#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#

from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6 import QtGui
from card_objects import Base

from typing import Optional


class CETreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, obj: Base, parent: Optional[QtWidgets.QWidget] = None,
                 can_move: bool = True, can_rename: bool = True, can_select: bool = True):
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

    def get_obj(self) -> Base:
        return self._obj


class CardTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.customContextMenuRequested.connect(self.custom_menu)
        self.itemChanged.connect(self.item_changed)

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        super().dragMoveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        super().dropEvent(event)

    def item_changed(self, item: QtWidgets.QTreeWidgetItem, _) -> None:
        if not isinstance(item, CETreeWidgetItem):
            return
        obj = item.get_obj()
        obj.text = item.text(0)
        print("Card edit:", obj)

    def custom_menu(self, point: QtCore.QPoint) -> None:
        item = self.itemAt(point)
        if not isinstance(item, CETreeWidgetItem):
            return
        obj = item.get_obj()
        print("Card menu:", obj)


class AssetTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.customContextMenuRequested.connect(self.custom_menu)
        self.itemChanged.connect(self.item_changed)

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        super().dragMoveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        super().dropEvent(event)

    def item_changed(self, item: QtWidgets.QTreeWidgetItem, _) -> None:
        if not isinstance(item, CETreeWidgetItem):
            return
        obj = item.get_obj()
        obj.text = item.text(0)
        print("Asset edit:", obj)

    def custom_menu(self, point: QtCore.QPoint) -> None:
        item = self.itemAt(point)
        if not isinstance(item, CETreeWidgetItem):
            return
        obj = item.get_obj()
        print("Asset menu:", obj)
