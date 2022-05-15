#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#

from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6 import QtGui

from card_objects import Base, Renderable
from card_objects import Deck, Style, Image, File

from typing import Optional


class CETreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, obj: Base, parent: Optional[QtWidgets.QTreeWidgetItem] = None,
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

    @property
    def obj(self) -> Base:
        return self._obj


class CERenderableItem(QtWidgets.QListWidgetItem):
    def __init__(self, renderable: Optional[Renderable]):
        super().__init__()
        self.renderable = renderable

        # this could be the overlay/underlay separator
        if self.renderable is None:
            flags = QtCore.Qt.ItemIsDropEnabled
            self.setFlags(flags)
            self.setText('\u23af'*4 + '\u00bb overlay \u00bb' + '\u23af'*4)
        else:
            self.setText(renderable.name)


    def is_separator(self) -> bool:
        return self.renderable is None


class CardTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.customContextMenuRequested.connect(self.custom_menu)
        self.itemChanged.connect(self.item_changed)
        self._deck: Optional[Deck] = None

    @property
    def deck(self):
        return self._deck

    @deck.setter
    def deck(self, deck):
        self._deck = deck

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        super().dragMoveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        super().dropEvent(event)

    def item_changed(self, item: QtWidgets.QTreeWidgetItem, _) -> None:
        if not isinstance(item, CETreeWidgetItem):
            return
        obj = item.obj
        obj.name = item.text(0)

    def custom_menu(self, point: QtCore.QPoint) -> None:
        item = self.itemAt(point)
        if not isinstance(item, CETreeWidgetItem):
            return
        obj = item.obj
        print("Card menu:", obj)


class AssetTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.customContextMenuRequested.connect(self.custom_menu)
        self._deck = None

    @property
    def deck(self):
        return self._deck

    @deck.setter
    def deck(self, deck):
        self._deck = deck

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        target = self.itemAt(event.pos())
        source = self.currentItem()
        # Can drop on another asset item of the same type (move before)
        event.ignore()
        if target == source:
            return
        # have to share the same parent
        if target.parent() == source.parent():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        target = self.itemAt(event.pos())
        source = self.currentItem()
        parent = source.parent()
        # we handle the event ourselves
        event.ignore()
        # remove source from the parent
        idx = parent.indexOfChild(source)
        source = parent.takeChild(idx)
        # place before the target item
        idx = parent.indexOfChild(target)
        parent.insertChild(idx, source)
        # rebuild the appropriate asset list
        assets = self.deck.files
        if isinstance(source.obj, Image):
            assets = self.deck.images
        elif isinstance(source.obj, Style):
            assets = self.deck.styles
        assets.clear()
        for i in range(parent.childCount()):
            child = parent.child(i)
            assets.append(child.obj)

    def custom_menu(self, point: QtCore.QPoint) -> None:
        item = self.itemAt(point)
        menu = QtWidgets.QMenu(self)
        root_type = None
        delete_item = None
        asset = None
        if isinstance(item, CETreeWidgetItem):
            asset = item.obj
            delete_item = item
            if isinstance(asset, File):
                root_type = "File"
            elif isinstance(asset, Image):
                root_type = "Image"
            elif isinstance(asset, Style):
                root_type = "Style"
                if not (item.flags() & QtCore.Qt.ItemIsEditable):
                    delete_item = None
        else:
            root_type = item.data(0, QtCore.Qt.UserRole)
        add_action = None
        delete_action = None
        if root_type == "File":
            add_action = menu.addAction("New file asset...")
        elif root_type == "Image":
            add_action = menu.addAction("New image asset...")
        elif root_type == "Style":
            add_action = menu.addAction("New style asset...")
        if delete_item:
            delete_action = menu.addAction(f"Delete {root_type} '{delete_item.text(0)}'")
        if menu.children():
            action = menu.exec(self.mapToGlobal(point))
            if action is None:
                return
            if action == add_action:
                if root_type == "File":
                    new_obj = File(f"New {root_type}")
                    self.deck.files.append(new_obj)
                elif root_type == "Image":
                    new_obj = Image(f"New {root_type}")
                    self.deck.images.append(new_obj)
                else:
                    new_obj = Style(f"New {root_type}")
                    self.deck.styles.append(new_obj)
                new_item = CETreeWidgetItem(new_obj)
                if asset is None:
                    # insert at start of items
                    item.insertChild(0, new_item)
                else:
                    # insert before 'item'
                    parent = item.parent()
                    idx = parent.indexOfChild(item)
                    parent.insertChild(idx, new_item)
                # print("Add new ", root_type, " to ", item)
            elif action == delete_action:
                # remove the item from the parent
                parent = delete_item.parent()
                idx = parent.indexOfChild(delete_item)
                _ = parent.takeChild(idx)
                # delete the item from the appropriate list
                try:
                    self.deck.files.remove(delete_item.obj)
                except ValueError:
                    pass
                try:
                    self.deck.images.remove(delete_item.obj)
                except ValueError:
                    pass
                try:
                    self.deck.styles.remove(delete_item.obj)
                except ValueError:
                    pass
                # print("Delete ", delete_item.text(0))
