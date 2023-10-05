#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#

# this core is derived from a solution posted on stack overflow
# https://stackoverflow.com/questions/34429632/resize-a-qgraphicsitem-with-the-mouse
# It has been refactored to more easily be used for multiple item classes

from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsPixmapItem,
                               QGraphicsRectItem, QGraphicsSceneHoverEvent,
                               QGraphicsSceneMouseEvent, QGraphicsTextItem,
                               QStyleOptionGraphicsItem, QWidget)


class GraphicsHandlesBase:

    handleTopLeft: int = 1
    handleTopMiddle: int = 2
    handleTopRight: int = 3
    handleMiddleLeft: int = 4
    handleMiddleRight: int = 5
    handleBottomLeft: int = 6
    handleBottomMiddle: int = 7
    handleBottomRight: int = 8

    handleSize: float = +8.0

    handleCursors: dict = {
        handleTopLeft: Qt.SizeFDiagCursor,
        handleTopMiddle: Qt.SizeVerCursor,
        handleTopRight: Qt.SizeBDiagCursor,
        handleMiddleLeft: Qt.SizeHorCursor,
        handleMiddleRight: Qt.SizeHorCursor,
        handleBottomLeft: Qt.SizeBDiagCursor,
        handleBottomMiddle: Qt.SizeVerCursor,
        handleBottomRight: Qt.SizeFDiagCursor,
    }

    def __init__(self):
        self.handles: dict = {}
        self.handleSelected: Optional[int] = None
        self.mousePressPos: Optional[QPointF] = None
        self.mousePressRect: Optional[QRectF] = None

    def enableHandles(self, v: bool) -> None:
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, v)
        self.setFlag(QGraphicsItem.ItemIsSelectable, v)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, v)
        self.setFlag(QGraphicsItem.ItemIsFocusable, v)
        if v:
            self.updateHandlesPos()

    def handleAt(self, point: QPointF) -> Optional[int]:
        """
        Returns the resize handle below the given point.
        """
        for (
            k,
            v,
        ) in self.handles.items():
            if v.contains(point):
                return k
        return None

    def hoverMoveEvent(self, moveEvent: QGraphicsSceneHoverEvent) -> None:
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        """
        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            cursor = Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)
        super().hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent: QGraphicsSceneHoverEvent) -> None:
        """
        Executed when the mouse leaves the shape (NOT PRESSED).
        """
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent: QGraphicsSceneMouseEvent) -> None:
        """
        Executed when the mouse is pressed on the item.
        """
        self.handleSelected = self.handleAt(mouseEvent.pos())
        if self.handleSelected:
            self.mousePressPos = mouseEvent.pos()
            self.mousePressRect = self.boundingRect()
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent: QGraphicsSceneMouseEvent) -> None:
        """
        Executed when the mouse is being moved over the item while being pressed.
        """
        if self.handleSelected is not None:
            self.interactiveResize(mouseEvent.pos())
        else:
            super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent: QGraphicsSceneMouseEvent) -> None:
        """
        Executed when the mouse is released from the item.
        """
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.update()

    def updateHandlesPos(self) -> None:
        """
        Update current resize handles according to the shape size and position.
        """
        s = self.handleSize
        b = self.boundingRect()
        self.handles[self.handleTopLeft] = QRectF(b.left(), b.top(), s, s)
        self.handles[self.handleTopMiddle] = QRectF(b.center().x() - s / 2, b.top(), s, s)
        self.handles[self.handleTopRight] = QRectF(b.right() - s, b.top(), s, s)
        self.handles[self.handleMiddleLeft] = QRectF(b.left(), b.center().y() - s / 2, s, s)
        self.handles[self.handleMiddleRight] = QRectF(b.right() - s, b.center().y() - s / 2, s, s)
        self.handles[self.handleBottomLeft] = QRectF(b.left(), b.bottom() - s, s, s)
        self.handles[self.handleBottomMiddle] = QRectF(b.center().x() - s / 2, b.bottom() - s, s, s)
        self.handles[self.handleBottomRight] = QRectF(b.right() - s, b.bottom() - s, s, s)

    def interactiveResize(self, mousePos: QPointF) -> None:
        """
        Perform shape interactive resize.
        """
        size = self.handleSize
        boundingRect = self.boundingRect()
        rect = boundingRect  # self.rect()
        diff = QPointF(0, 0)

        self.prepareGeometryChange()

        if self.handleSelected == self.handleTopLeft:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setTop(toY)
            rect.setLeft(boundingRect.left() + size)
            rect.setTop(boundingRect.top() + size)
            self.setItemRect(rect)

        elif self.handleSelected == self.handleTopMiddle:

            fromY = self.mousePressRect.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setY(toY - fromY)
            boundingRect.setTop(toY)
            rect.setTop(boundingRect.top() + size)
            self.setItemRect(rect)

        elif self.handleSelected == self.handleTopRight:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setTop(toY)
            rect.setRight(boundingRect.right() - size)
            rect.setTop(boundingRect.top() + size)
            self.setItemRect(rect)

        elif self.handleSelected == self.handleMiddleLeft:

            fromX = self.mousePressRect.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setLeft(toX)
            rect.setLeft(boundingRect.left() + size)
            self.setItemRect(rect)

        elif self.handleSelected == self.handleMiddleRight:
            fromX = self.mousePressRect.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setRight(toX)
            rect.setRight(boundingRect.right() - size)
            self.setItemRect(rect)

        elif self.handleSelected == self.handleBottomLeft:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setBottom(toY)
            rect.setLeft(boundingRect.left() + size)
            rect.setBottom(boundingRect.bottom() - size)
            self.setItemRect(rect)

        elif self.handleSelected == self.handleBottomMiddle:

            fromY = self.mousePressRect.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setY(toY - fromY)
            boundingRect.setBottom(toY)
            rect.setBottom(boundingRect.bottom() - size)
            self.setItemRect(rect)

        elif self.handleSelected == self.handleBottomRight:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setBottom(toY)
            rect.setRight(boundingRect.right() - size)
            rect.setBottom(boundingRect.bottom() - size)
            self.setItemRect(rect)

        self.updateHandlesPos()

    def paintHandles(self, painter: QPainter) -> None:
        if not self.isSelected():
            return
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(0, 0, 255, 255)))
        painter.setPen(QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        for handle, rect in self.handles.items():
            if self.handleSelected is None or handle == self.handleSelected:
                painter.drawRect(rect)


class GraphicsRectItem(GraphicsHandlesBase, QGraphicsRectItem):
    def __init__(self, selectable, *args):
        QGraphicsRectItem.__init__(self, *args)
        GraphicsHandlesBase.__init__(self)
        self.enableHandles(selectable)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget) -> None:
        super().paint(painter, option, widget)
        self.paintHandles(painter)

    def setItemRect(self, rect: QRectF) -> None:
        self.setRect(rect)


class GraphicsPixmapItem(GraphicsHandlesBase, QGraphicsPixmapItem):
    def __init__(self, selectable, *args):
        QGraphicsPixmapItem.__init__(self, *args)
        GraphicsHandlesBase.__init__(self)
        self.enableHandles(selectable)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget) -> None:
        super().paint(painter, option, widget)
        self.paintHandles(painter)

    def setItemRect(self, rect: QRectF) -> None:
        pass


class GraphicsTextItem(GraphicsHandlesBase, QGraphicsTextItem):
    def __init__(self, selectable, *args):
        QGraphicsTextItem.__init__(self, *args)
        GraphicsHandlesBase.__init__(self)
        self.enableHandles(selectable)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget) -> None:
        super().paint(painter, option, widget)
        self.paintHandles(painter)

    def setItemRect(self, rect: QRectF) -> None:
        pass
