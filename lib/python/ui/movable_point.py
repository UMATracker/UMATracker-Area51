from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsItemGroup, QGraphicsPixmapItem, QGraphicsEllipseItem, QFrame, QFileDialog, QPushButton, QGraphicsObject, QGraphicsRectItem
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPolygonF, QColor, QPen
from PyQt5.QtCore import QPoint, QPointF, QRectF, Qt
import numpy as np
import pandas as pd

from .graphics_text_item_with_background import GraphicsTextItemWithBackground


class MovablePoint(QGraphicsObject):
    def __init__(self, parent=None):
        super(MovablePoint, self).__init__(parent)
        self.setZValue(100000)
        self.radius = 5.0
        self.rect = QRectF()
        self.color = QColor(255,0,0)

        self.itemType = QGraphicsRectItem

        self.points = np.array([0.,0.])
        self.item = self.itemType(self)

        self.textItem = GraphicsTextItemWithBackground(self)
        self.textItem.setBackgroundColor(Qt.white)
        self.textItem.setZValue(9)

    def autoAdjustRadius(self, shape):
        # TODO: かなり適当
        m = np.max(shape)
        r = max(float(5.0*m/600), 5.0)
        self.setRadius(r)
        return int(self.getRadius())

    def setRadius(self, r):
        self.radius = r

        if self.points is None:
            return

        radii = 2*self.radius
        rect = QRectF(-self.radius, -self.radius, radii, radii)
        self.item.setRect(rect)

    def setColor(self, color):
        self.color = color
        self.item.setBrush(self.color)

    def getRadius(self):
        return self.radius

    def getPoints(self):
        return self.points

    def setPoints(self, ps):
        self.points[:] = ps

        radii = 2*self.radius
        rect = QRectF(-self.radius, -self.radius, radii, radii)

        self.item.setRect(rect)
        self.item.setPos(*self.points)
        self.item.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsScenePositionChanges)
        self.item.setAcceptHoverEvents(True)
        self.item.mouseMoveEvent = self.generateItemMouseMoveEvent(self.item, self.points)
        self.item.mousePressEvent = self.generateItemMousePressEvent(self.item, self.points)

        self.textItem.setPlainText('({0:.1f}, {1:.1f})'.format(*self.points))
        self.textItem.setPos(*self.points)

        self.update()

    def setRect(self, rect):
        self.rect = rect

    def showCoordinate(self):
        self.textItem.show()

    def hideCoordinate(self):
        self.textItem.hide()

    def generateItemMouseMoveEvent(self, item, point):
        def itemMouseMoveEvent(event):
            self.itemType.mouseMoveEvent(item, event)
            centerPos = item.scenePos()

            point[0] = centerPos.x()
            point[1] = centerPos.y()
            self.textItem.setPlainText('({0:.1f}, {1:.1f})'.format(*point))
            self.textItem.setPos(*point)
            self.update()
        return itemMouseMoveEvent

    def generateItemMousePressEvent(self, item, point):
        def itemMousePressEvent(event):
            self.itemType.mousePressEvent(item, event)
            pass
        return itemMousePressEvent

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        pass

    def distance(self,pt):
        v = self.points - np.array(pt)
        return np.sqrt(np.dot(v,v))
