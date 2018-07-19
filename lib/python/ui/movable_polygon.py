from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsItemGroup, QGraphicsPixmapItem, QGraphicsEllipseItem, QFrame, QFileDialog, QPushButton, QGraphicsObject
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPolygonF, QColor
from PyQt5.QtCore import QPoint, QPointF, QRectF, Qt, pyqtSignal

import numpy as np
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon, Point

import copy

from .graphics_text_item_with_background import GraphicsTextItemWithBackground


class MovablePolygonVertex(QGraphicsObject):
    geometryChange = pyqtSignal(object)

    def __init__(self, parent=None):
        super(MovablePolygonVertex, self).__init__(parent)
        self.setZValue(1000)

        self.isMousePressed = False

        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self.buttonList = []
        self.points = []
        self.textItemList = []
        self.setFocus(Qt.ActiveWindowFocusReason)

        self._boundingRect = QRectF()
        self._rect = QRectF()

    def setColor(self, color):
        self.color = QColor(color)
        self.color.setAlpha(32)

    def getPoints(self):
        return [[p.x(), p.y()] for p in self.points]

    def setPoints(self, ps):
        self.points.clear()
        self.textItemList.clear()
        for point in ps:
            self.points.append(QPointF(*point))

            textItem = GraphicsTextItemWithBackground(self)
            textItem.setBackgroundColor(Qt.white)
            textItem.setZValue(9)

            textItem.setPlainText('({0:.1f}, {1:.1f})'.format(*point))
            textItem.setPos(*point)

            self.textItemList.append(textItem)

        self.updateResizeHandles()

    def setRect(self):
        polygon = QPolygonF(self.points)
        rect = polygon.boundingRect()
        self._rect = rect
        self._boundingRect = rect

    def showCoordinate(self):
        for item in self.textItemList:
            item.show()

    def hideCoordinate(self):
        for item in self.textItemList:
            item.hide()

    def prepareGeometryChange(self):
        self.geometryChange.emit([[p.x(), p.y()] for p in self.points])
        super(MovablePolygonVertex, self).prepareGeometryChange()

    def hoverMoveEvent(self, event):
        hoverMovePos = event.scenePos()
        mouseHoverArea = None
        for item in self.buttonList:
            if item.contains(hoverMovePos):
                mouseHoverArea = item
                break
        if mouseHoverArea:
            self.setCursor(QtCore.Qt.PointingHandCursor)
            return
        self.setCursor(QtCore.Qt.SizeAllCursor)
        super(MovablePolygonVertex, self).hoverMoveEvent(event)

    def hoverEnterEvent(self, event):
        self.setCursor(QtCore.Qt.SizeAllCursor)
        super(MovablePolygonVertex, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setCursor(QtCore.Qt.ArrowCursor)
        super(MovablePolygonVertex, self).hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        self.isMousePressed = True
        self.mousePressedPos = event.scenePos()
        self.pressedRectPos = None
        self.originalPoints = copy.deepcopy(self.points)
        for i, item in enumerate(self.buttonList):
            if item.contains(self.mousePressedPos):
                self.pressedRectPos = i
                break
        super(MovablePolygonVertex, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.isMousePressed = False
        self.updateResizeHandles()
        self.prepareGeometryChange()
        super(MovablePolygonVertex, self).mouseReleaseEvent(event)

    def paint(self, painter, option, widget):
        self.updateResizeHandles()
        self.draw(painter, option, widget, self._rect)
        for item in self.buttonList:
            painter.drawRect(item)

    def draw(self, painter, option, widget, rect):
        return

    def boundingRect(self):
        return self._boundingRect

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def mouseMoveEvent(self, event):
        mouseMovePos = event.scenePos()
        if self.isMousePressed:
            # TODO: 重複あり，要修正．
            if self.pressedRectPos is None:
                for point, original_point, textItem in zip(self.points, self.originalPoints, self.textItemList):
                    newPos = original_point + (mouseMovePos - self.mousePressedPos)
                    point.setX(newPos.x())
                    point.setY(newPos.y())

                    textItem.setPlainText('({0:.1f}, {1:.1f})'.format(point.x(), point.y()))
                    textItem.setPos(point)
            else:
                newPos = self.originalPoints[self.pressedRectPos] + (mouseMovePos - self.mousePressedPos)
                point = self.points[self.pressedRectPos]
                point.setX(newPos.x())
                point.setY(newPos.y())

                textItem = self.textItemList[self.pressedRectPos]
                textItem.setPlainText('({0:.1f}, {1:.1f})'.format(point.x(), point.y()))
                textItem.setPos(point)

        self.updateResizeHandles()
        self.prepareGeometryChange()

    def updateResizeHandles(self):
        self.resizeHandleSize = 4.0

        self.setRect()
        self._rect = self._rect.normalized()

        # FIXME:結構アドホック，複数のビューでシーンを表示してるときには問題が出る．
        views = self.scene().views()
        self.offset = self.resizeHandleSize * (views[0].mapToScene(1, 0).x() - views[0].mapToScene(0, 1).x())
        self._boundingRect = self._rect.adjusted(
                -self.offset*2,
                -self.offset*2,
                self.offset*2,
                self.offset*2
            )

        self.buttonList.clear()
        for point, textItem in zip(self.points, self.textItemList):
            rect = QRectF(
                    point.x()-self.offset,
                    point.y()-self.offset,
                    2*self.offset,
                    2*self.offset
                )
            self.buttonList.append(rect)

            # textItem.setPlainText('({0:.1f}, {1:.1f})'.format(point.x(), point.y()))
            # textItem.setPos(point)

class MovablePolygon(MovablePolygonVertex):
    def __init__(self, parent=None):
        super(MovablePolygon, self).__init__(parent)

    def includes(self, pt):
        poly = Polygon(((point.x(), point.y()) for point in self.points))
        return poly.contains(Point(pt))

    def draw(self, painter, option, widget, rect):
        if len(self.points) != 0:
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 0, QtCore.Qt.DashLine))
            # hull = ConvexHull([[p.x(), p.y()] for p in self.points])
            # polygon = QPolygonF([self.points[i] for i in hull.vertices])
            polygon = QPolygonF(self.points)

            painter.setBrush(QtGui.QBrush(self.color))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawConvexPolygon(polygon)
            painter.setPen(QtGui.QPen(QtCore.Qt.black, 0, QtCore.Qt.DashLine))
            painter.drawConvexPolygon(polygon)

            painter.setPen(QtGui.QPen(QtCore.Qt.black, 0, QtCore.Qt.SolidLine))
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 255, 255)))

class MovableLine(MovablePolygonVertex):
    def __init__(self, parent=None):
        super(MovableLine, self).__init__(parent)

        self.tmp_points = None

    def setColor(self, color):
        self.color = QColor(color)

    def calcLineParams(self):
        ps = np.array(
                [
                    [self.points[0].x(), self.points[0].y()],
                    [self.points[1].x(), self.points[1].y()]
                    ]
                )
        if np.all(self.tmp_points == ps):
            pass
        else:
            self.tmp_points = ps

            p0 = ps[0, :]
            p1 = ps[1, :]

            self.a = p1[1] - p0[1]
            self.b = p0[0] - p1[0]
            self.c = - (self.b*p0[1] + self.a*p0[0])
            self.denominator = np.sqrt(self.a*self.a + self.b*self.b)

    def distance(self, pt):
        self.calcLineParams()
        numerator = np.fabs(self.a*pt[0] + self.b*pt[1] + self.c)

        return numerator/self.denominator

    def setPoints(self, ps):
        super(MovableLine, self).setPoints(ps)
        self.calcLineParams()

    def mouseReleaseEvent(self, event):
        super(MovableLine, self).mouseReleaseEvent(event)
        self.calcLineParams()

    def draw(self, painter, option, widget, rect):
        if len(self.points) != 0:
            polygon = QPolygonF(self.points)

            painter.setPen(QtGui.QPen(self.color, 2, QtCore.Qt.DashDotLine))
            painter.drawConvexPolygon(polygon)

            painter.setPen(QtGui.QPen(QtCore.Qt.black, 0, QtCore.Qt.SolidLine))
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 255, 255)))

