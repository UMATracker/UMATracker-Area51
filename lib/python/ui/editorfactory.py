#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2013 Riverbank Computing Limited
## Copyright (C) 2010 Hans-Peter Jansen <hpj@urpla.net>.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################


from PyQt5.QtCore import pyqtProperty, Qt, QVariant, QAbstractListModel, QModelIndex
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QApplication, QComboBox, QGridLayout,
        QItemEditorCreatorBase, QItemEditorFactory, QTableWidget,
        QTableWidgetItem, QWidget)

from enum import Enum
from lib.python.ui.resizable_object import ResizableRect, ResizableEllipse
from lib.python.ui.movable_polygon import MovablePolygon, MovableLine
from lib.python.ui.movable_point import MovablePoint

class ColorListEditor(QComboBox):
    def __init__(self, widget=None):
        super(ColorListEditor, self).__init__(widget)

        self.populateList()

    def getColor(self):
        color = self.itemData(self.currentIndex(), Qt.DecorationRole)
        return color

    def setColor(self, color):
        self.setCurrentIndex(self.findData(color, Qt.DecorationRole))

    color = pyqtProperty(QColor, getColor, setColor, user=True)

    def populateList(self):
        for i, colorName in enumerate(QColor.colorNames()):
            color = QColor(colorName)
            self.insertItem(i, colorName)
            self.setItemData(i, color, Qt.DecorationRole)

    # def currentIndexChanged(self, index):
    #     color = self.itemData(i).toPyObject()[0]

class ColorListItemEditorCreator(QItemEditorCreatorBase):
    def createWidget(self, parent):
        return ColorListEditor(parent)

# TODO: Polygon support
class FigureType(Enum):
    Rectangular = ResizableRect
    Ellipse = ResizableEllipse
    Polygon = MovablePolygon
    Point = MovablePoint
    Line = MovableLine

class FigureListEditor(QComboBox):
    def __init__(self, widget=None):
        super(FigureListEditor, self).__init__(widget)

        region_items = []
        dist_items = []
        for i, fig in enumerate(FigureType):
            if callable(getattr(fig.value, 'distance', None)):
                dist_items.append(fig)
            elif callable(getattr(fig.value, 'includes', None)):
                region_items.append(fig)

        self.items = region_items
        self.items.append(None)
        self.items += dist_items

        self.populateList()

    def getString(self):
        string = self.itemData(self.currentIndex(), Qt.DisplayRole)
        return string

    def setString(self, string):
        self.setCurrentIndex(self.findData(string, Qt.DisplayRole))

    string = pyqtProperty(str, getString, setString, user=True)

    def populateList(self):
        for i, fig in enumerate(self.items):
            if fig is None:
                self.insertSeparator(i)
            else:
                self.insertItem(i, fig.name)

class FigureListItemEditorCreator(QItemEditorCreatorBase):
    def createWidget(self, parent):
        return FigureListEditor(parent)

class Window(QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        factory = QItemEditorFactory()
        factory.registerEditor(QVariant.Color, ColorListItemEditorCreator())
        QItemEditorFactory.setDefaultFactory(factory)

        self.createGUI()

    def createGUI(self):
        tableData = [
            ("Alice", QColor('aliceblue')),
            ("Neptun", QColor('aquamarine')),
            ("Ferdinand", QColor('springgreen'))
        ]

        table = QTableWidget(3, 2)
        table.setHorizontalHeaderLabels(["Name", "Hair Color"])
        table.verticalHeader().setVisible(False)
        table.resize(150, 50)

        for i, (name, color) in enumerate(tableData):
            nameItem = QTableWidgetItem(name)
            colorItem = QTableWidgetItem()
            colorItem.setData(Qt.DisplayRole, color)
            table.setItem(i, 0, nameItem)
            table.setItem(i, 1, colorItem)

        table.resizeColumnToContents(0)
        table.horizontalHeader().setStretchLastSection(True)

        layout = QGridLayout()
        layout.addWidget(table, 0, 0)
        self.setLayout(layout)

        self.setWindowTitle("Color Editor Factory")


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    window = Window()
    window.show()

    sys.exit(app.exec_())
