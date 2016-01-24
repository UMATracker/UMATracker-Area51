from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsItemGroup, QGraphicsPixmapItem, QGraphicsEllipseItem, QFrame, QFileDialog, QPushButton, QGraphicsObject
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPolygonF, QColor
from PyQt5.QtCore import QPoint, QPointF, QRectF
import numpy as np

class MovablePolyLine(QGraphicsObject):
    def __init__(self, parent=None):
        super(MovablePolyLine, self).__init__(parent)
        self.setZValue(1000)
        self.polygon = QPolygonF()
        self.radius = 5.0
        self.itemList = []
        self.rect = QRectF()
        self.color = QColor(255,0,0)

        self.setOpacity(0.5)
        # self.setHandlesChildEvents(False)
        # self.setFlags(QGraphicsItem.ItemIsMovable)

        self.isDrawLine = True
        self.drawItemFlags = None

        self.points = None

        self.itemType = QGraphicsEllipseItem

    def setDrawLine(self, flag):
        self.isDrawLine = flag

    def setDrawItems(self, flags):
        self.drawItemFlags = flags
        for item, flag in zip(self.itemList, flags):
            if flag:
                item.show()
            else:
                item.hide()

    def setRadius(self, r):
        self.radius = r

        radii = 2*self.radius
        rectList = [QRectF(-self.radius, -self.radius, radii, radii) for p in self.points]
        for item, rect in zip(self.itemList, rectList):
            item.setRect(rect)

    def setColor(self, rgb):
        self.color = QColor(*rgb)
        for item in self.itemList:
            item.setBrush(self.color)

    def getRadius(self):
        return self.radius

    def setPoints(self, ps=None, flags=None):
        if ps is not None and self.points is not None:
            if len(ps)==len(self.points):
                self.points = ps
                for item, point in zip(self.itemList, self.points):
                    item.setPos(*point)
                    item.mouseMoveEvent = self.generateItemMouseMoveEvent(item, point)
                    item.mousePressEvent = self.generateItemMousePressEvent(item, point)
                self.update()
                return

        scene = self.scene()
        if scene is not None:
            for item in self.itemList:
                scene.removeItem(item)
                del item
        self.itemList.clear()

        if ps is not None:
            self.points = ps

        if flags is not None:
            self.drawItemFlags = flags

        if self.points is not None:
            radii = 2*self.radius
            rectList = [QRectF(-self.radius, -self.radius, radii, radii) for p in self.points]
            self.itemList = [self.itemType(self) for rect in rectList]

            for item, point, rect, flag in zip(self.itemList, self.points, rectList, self.drawItemFlags):
                item.setBrush(self.color)
                item.setRect(rect)
                item.setPos(*point)

                if not flag:
                    item.hide()

                item.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsScenePositionChanges)
                item.setAcceptHoverEvents(True)
                item.mouseMoveEvent = self.generateItemMouseMoveEvent(item, point)
                item.mousePressEvent = self.generateItemMousePressEvent(item, point)

    def setRect(self, rect):
        self.rect = rect

    def generateItemMouseMoveEvent(self, item, point):
        def itemMouseMoveEvent(event):
            self.itemType.mouseMoveEvent(item, event)
            centerPos = item.scenePos()

            point[0] = centerPos.x()
            point[1] = centerPos.y()
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
        if self.points is not None and self.isDrawLine:
            painter.save()

            painter.setPen(self.color)
            qPoints = [QPointF(*p.tolist()) for p in self.points]
            polygon = QPolygonF(qPoints)
            painter.drawPolyline(polygon)

            painter.restore()
