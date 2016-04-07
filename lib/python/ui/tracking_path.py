from .graphics_text_item_with_background import GraphicsTextItemWithBackground

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsTextItem, QGraphicsItemGroup, QGraphicsPixmapItem, QGraphicsEllipseItem, QGraphicsRectItem, QFrame, QFileDialog, QPushButton, QGraphicsObject
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPolygonF, QColor
from PyQt5.QtCore import QPoint, QPointF, QRectF, Qt, pyqtSignal, QObject

import numpy as np


class TrackingPath(QGraphicsObject):
    itemSelected = pyqtSignal(object)

    def __init__(self, parent=None):
        super(TrackingPath, self).__init__(parent)
        self.setZValue(10)
        self.polygon = QPolygonF()
        self.radius = 5.0
        self.itemList = []
        self.rect = QRectF()
        self.color = QColor(255,0,0)

        self.setOpacity(0.5)
        # self.setHandlesChildEvents(False)
        # self.setFlags(QGraphicsItem.ItemIsMovable)

        self.drawLineFlag = True
        self.drawItemFlag = True
        self.selected = False

        self.itemPos = None

        self.points = None

        self.itemType = QGraphicsEllipseItem
        self.item = self.itemType(self)
        self.isItemMovable = False

        self.textItem = GraphicsTextItemWithBackground(self)
        self.textItem.setBackgroundColor(Qt.white)
        self.textItem.hide()

    def setText(self, text):
        self.textItem.setPlainText(text)
        self.textItem.show()

    def setTextVisible(self, flag):
        if flag:
            self.textItem.show()
        else:
            self.textItem.hide()

    def setLineWidth(self, w):
        self.lineWidth = w
        self.update()

    def getLineWidth(self):
        return self.lineWidth

    def setDrawLine(self, flag):
        self.drawLineFlag = flag

    def setDrawItem(self, flag):
        if flag:
            self.item.show()
        else:
            self.item.hide()

    def setRadius(self, r):
        self.radius = r

        radii = 2*self.radius
        rect = QRectF(-self.radius, -self.radius, radii, radii)

        self.item.setRect(rect)

    def setColor(self, rgb):
        self.color = QColor(*rgb)
        self.item.setBrush(self.color)

    def getRadius(self):
        return self.radius

    def setPoints(self, ps, itemPos):
        self.points = ps
        self.itemPos = itemPos

        self.updateLine()

    def updateLine(self):
        if self.points is not None:
            diameter = 2*self.radius
            rect = QRectF(-self.radius, -self.radius, diameter, diameter)

            if self.itemPos is not None:
                point = self.points[self.itemPos]

                if not isinstance(self.item, self.itemType):
                    scene = self.scene()
                    if scene is not None:
                        scene.removeItem(self.item)

                    self.item = self.itemType(self)
                    self.item.setBrush(self.color)
                    self.item.setRect(rect)
                    self.item.mouseMoveEvent = self.generateItemMouseMoveEvent(self.item, point)
                    self.item.mousePressEvent = self.generateItemMousePressEvent(self.item, point)
                    self.setItemIsMovable(self.isItemMovable)

                else:
                    self.item.show()

                self.item.setPos(*point)
                self.textItem.setPos(*point)

            else:
                self.item.hide()

            self.update()

    def setItemIsMovable(self, flag):
        self.isItemMovable = flag
        if self.isItemMovable:
            self.item.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsScenePositionChanges)
            # self.item.setAcceptHoverEvents(False)
            # self.item.mouseMoveEvent = self.generateItemMouseMoveEvent(self.item, point)
            # self.item.mousePressEvent = self.generateItemMousePressEvent(self.item, point)
        else:
            self.item.setFlags(0)
            # self.item.mouseMoveEvent = self.itemType().mouseMoveEvent
            # self.item.mousePressEvent = self.itemType().mousePressEvent

    def setRect(self, rect):
        self.rect = rect

    def generateItemMouseMoveEvent(self, item, point):
        def itemMouseMoveEvent(event):
            self.itemType.mouseMoveEvent(item, event)
            centerPos = item.scenePos()

            point[0] = centerPos.x()
            point[1] = centerPos.y()

            self.textItem.setPos(centerPos)
            self.update()
        return itemMouseMoveEvent

    def generateItemMousePressEvent(self, item, point):
        def itemMousePressEvent(event):
            self.itemType.mousePressEvent(item, event)
            if event.button() == Qt.RightButton:
                if self.itemType is QGraphicsRectItem:
                    self.itemType = QGraphicsEllipseItem
                elif self.itemType is QGraphicsEllipseItem:
                    self.itemType = QGraphicsRectItem
                self.selected = not self.selected
                self.updateLine()
                self.itemSelected.emit(self)
        return itemMousePressEvent

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        if self.points is not None and self.drawLineFlag:
            painter.save()

            painter.setPen(self.color)
            qPoints = [QPointF(*p.tolist()) for p in self.points]
            polygon = QPolygonF(qPoints)
            painter.drawPolyline(polygon)

            painter.restore()

