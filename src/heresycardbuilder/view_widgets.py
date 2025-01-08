#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#
import copy
from typing import List, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from card_objects import (Base, Card, Deck, File, Image, Location, Renderable, Style)


class CETreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(
        self,
        obj: Base,
        parent: Optional[QtWidgets.QTreeWidgetItem] = None,
        can_move: bool = True,
        can_rename: bool = True,
        can_select: bool = True,
    ):
        super().__init__()
        self._obj = obj
        self.setText(0, obj.name)
        flags = QtCore.Qt.ItemIsEnabled
        if can_select:
            flags |= QtCore.Qt.ItemIsSelectable
        if can_rename:
            flags |= QtCore.Qt.ItemIsEditable
        if can_move:
            # flags |= QtCore.Qt.ItemIsDropEnabled
            flags |= QtCore.Qt.ItemIsDragEnabled
        self.setFlags(flags)
        if parent:
            parent.addChild(self)

    @property
    def obj(self) -> Base:
        return self._obj


class CERootTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, name: str, obj: List, attr_name: str, parent: Optional[QtWidgets.QTreeWidgetItem] = None):
        super().__init__()
        self._obj = obj
        self._attr_name = attr_name
        self.setText(0, name)
        self.setFlags(QtCore.Qt.ItemIsEnabled)
        font = self.font(0)
        font.setBold(True)
        self.setFont(0, font)
        if parent:
            parent.addChild(self)

    @property
    def attr_name(self) -> Base:
        return self._attr_name

    @property
    def obj(self) -> Base:
        return self._obj

    @obj.setter
    def obj(self, obj):
        self._obj = obj


class CERenderableItem(QtWidgets.QListWidgetItem):
    def __init__(self, renderable: Optional[Renderable]):
        super().__init__()
        self.renderable = renderable

        # this could be the overlay/underlay separator
        if self.renderable is None:
            self.setText("\u23af" * 4 + "\u00bb overlay \u00bb" + "\u23af" * 4)
            flags = QtCore.Qt.NoItemFlags
            self.setFlags(flags)
        else:
            self.setText(renderable.name)
            flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsSelectable
            self.setFlags(flags)

    def is_separator(self) -> bool:
        return self.renderable is None


class CardTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.customContextMenuRequested.connect(self.custom_menu)
        self.itemChanged.connect(self.item_changed)
        self._deck: Optional[Deck] = None
        self._copy_buffer: dict = {}

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
        # cannot drop on "background" item
        if target.obj and target.obj.background:
            return
        # have to share the same parent
        if target.parent() == source.parent():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        super().dropEvent(event)
        # pass the parent to rebuild_child_list()
        self.rebuild_child_list(self.currentItem().parent())

    def rebuild_child_list(self, parent: CETreeWidgetItem) -> None:
        # The children of "parent" have changed in some way (delete, add, reorder)
        # Rebuild the underlying object lists from the tree structure.
        if isinstance(parent.obj, Location):
            # if a Location's children are changing, we update parent.obj.cards
            new_loc_list = []
            for idx in range(parent.childCount()):
                item = parent.child(idx)
                new_loc_list.append(item.obj)
            parent.obj.cards = new_loc_list
        else:
            # otherwise, we update the parent.obj list (non-Base subclass)
            new_item_list = []
            for idx in range(parent.childCount()):
                item = parent.child(idx)
                new_item_list.append(item.obj)
            # the new list goes in two places
            # the parent obj list
            parent.obj = new_item_list
            # and the deck slot
            setattr(self._deck, parent.attr_name, new_item_list)

    def item_changed(self, item: QtWidgets.QTreeWidgetItem, _) -> None:
        if not isinstance(item, CETreeWidgetItem):
            return
        obj = item.obj
        obj.name = item.text(0)

    def custom_menu(self, point: QtCore.QPoint) -> None:
        item = self.itemAt(point)
        # the object being clicked on
        obj = None
        objlist = None
        if isinstance(item, CETreeWidgetItem):
            obj = item.obj
        elif isinstance(item, CERootTreeWidgetItem):
            objlist = item.obj

        # if objlist is None, get it from the parent of the obj
        if objlist is None:
            parent = item.parent()
            if parent and hasattr(parent, "obj"):
                objlist = parent.obj

        # RMB menu
        menu = QtWidgets.QMenu(self)

        # delete action for non-background Card objects and Location objects
        del_action = menu.addAction("")
        if obj:
            del_action.setText(f"Delete {obj.name}")
            allow = isinstance(obj, Card) and (not obj.is_background()) and \
                    (not obj.xml_tag == "iconreference")
            allow |= isinstance(obj, Location)
        else:
            allow = False
        del_action.setVisible(allow)

        copy_action = menu.addAction("Copy")
        copy_action.setVisible(False)
        paste_action = menu.addAction("Paste")
        paste_action.setVisible(False)

        # Add card for: (1) Location and (2) Card if they are not top level or is the default location card
        if obj:
            allow = isinstance(obj, Location)
            allow |= isinstance(obj, Card) and (item.parent() is not None)
            if obj == self._deck.default_location_card:
                allow = False
        else:
            if objlist != self._deck.locations:
                allow = True
        add_card_action = menu.addAction("Add new card")
        add_card_action.setVisible(allow)
        if allow:
            if obj:
                copy_action.setVisible(not obj.is_background())
                copy_action.setProperty("clipboard", "card")
                copy_action.setText(f"Copy card '{obj.name}'")
            cbuf = self._copy_buffer.get("card", None)
            if cbuf:
                paste_action.setVisible(True)
                paste_action.setProperty("clipboard", "card")
                paste_action.setText(f"Paste card '{cbuf.name}'")
        # Add location if a location or the Location card base
        allow = isinstance(obj, Location)
        allow |= obj == self._deck.default_location_card
        allow |= objlist == self._deck.locations
        add_location_action = menu.addAction("Add new location")
        add_location_action.setVisible(allow)
        if allow:
            copy_action.setVisible((obj is not None) and (not obj.is_background()))
            copy_action.setProperty("clipboard", "location")
            copy_action.setText(f"Copy location '{obj.name}'")
            cbuf = self._copy_buffer.get("location", None)
            if cbuf:
                paste_action.setVisible(True)
                paste_action.setProperty("clipboard", "location")
                paste_action.setText(f"Paste location '{cbuf.name}'")
        # do the menu
        action = menu.exec(self.mapToGlobal(point))
        if action is None:
            return
        if action == del_action:
            # TODO delete card/location
            msg = f"Delete card '{obj.name}'?"
            if isinstance(obj, Location):
                msg = f"Delete location '{obj.name}'?"
            ret = QtWidgets.QMessageBox.question(self, "Confirm", msg)
            if ret != QtWidgets.QMessageBox.Yes:
                return
            print(f"RJF delete item:'{obj}'  parent:'{objlist}")
        elif action == add_card_action:
            # TODO add card
            print(f"RJF add card:'{obj}'  parent:'{objlist}")
        elif action == add_location_action:
            # TODO add location
            print(f"RJF add location:'{obj}'  parent:'{objlist}")
        elif action == copy_action:
            tag = action.property("clipboard")
            self._copy_buffer[tag] = deep_copy_item(obj)
        elif action == paste_action:
            # TODO paste
            tag = action.property("clipboard")
            print(f"RJF paste {tag} item:'{obj}'  parent:'{objlist}")


def deep_copy_item(item: Base):
    if isinstance(item, Card):
        top_render = item.top_face.renderables
        bot_render = item.bot_face.renderables
        item.top_face.renderables = []
        item.bot_face.renderables = []
        location = item.location
        background = item.background_card
        item.location = None
        item.background_card = None
        dup = copy.deepcopy(item)
        item.location = location
        item.background_card = background
        item.top_face.renderables = top_render
        item.bot_face.renderables = bot_render
        return dup
    return None


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
                msg = f"Delete '{delete_item.obj.name}'?"
                ret = QtWidgets.QMessageBox.question(self, "Confirm", msg)
                if ret != QtWidgets.QMessageBox.Yes:
                    return
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
