#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys

# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    currentDirPath = sys._MEIPASS
    print(currentDirPath)
    if os.name == 'nt':
        import win32api

        win32api.SetDllDirectory(sys._MEIPASS)
elif __file__:
    currentDirPath = os.getcwd()

sampleDataPath = os.path.join(currentDirPath,"data")
userDir        = os.path.expanduser('~')

import re, hashlib, json

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QFileDialog, QMainWindow, QDialog, QItemEditorCreatorBase, QItemEditorFactory, QTableWidget, QTableWidgetItem, QStyledItemDelegate, QProgressDialog, QStyle
from PyQt5.QtGui import QPixmap, QColor, QBrush, QIcon
from PyQt5.QtCore import QRectF, QPointF, Qt, QVariant
# from shapely.geometry import Polygon, Point

import cv2
import pandas as pd
import numpy as np

import icon
from lib.python import misc
from lib.python.ui.main_window_base import Ui_MainWindowBase
from lib.python.ui.tracking_path_group import TrackingPathGroup
from lib.python.ui.editorfactory import *

import urllib.request
blocklyURL = "file:" + urllib.request.pathname2url(os.path.join(currentDirPath,"lib","editor","index.html"))

# Log file setting.
# import logging
# logging.basicConfig(filename='MainWindow.log', level=logging.DEBUG)

# Log output setting.
# If handler = StreamHandler(), log will output into StandardOutput.
from logging import getLogger, NullHandler, StreamHandler, DEBUG
logger = getLogger(__name__)
handler = NullHandler() if True else StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)


class Ui_MainWindow(QMainWindow, Ui_MainWindowBase):
    def __init__(self):
        super(Ui_MainWindow, self).__init__()
        self.setupUi(self)

        self.videoPlaybackInit()
        self.imgInit()
        self.menuInit()
        self.fgbg = None
        self.filePath = None
        self.df = None
        self.df_dist = None
        self.df_region = None
        self.trackingPathGroup = None
        self.currentFrameNo = None

        factory = QItemEditorFactory()
        factory.registerEditor(QVariant.Color, ColorListItemEditorCreator())

        self.createGUI()

    def createGUI(self):
        colorEditorFactory = QItemEditorFactory()
        colorEditorFactory.registerEditor(QVariant.Color, ColorListItemEditorCreator())
        colorEditorDelegate = QStyledItemDelegate(self)
        colorEditorDelegate.setItemEditorFactory(colorEditorFactory)

        figureEditorFactory = QItemEditorFactory()
        figureEditorFactory.registerEditor(QVariant.String, FigureListItemEditorCreator())
        figureEditorDelegate = QStyledItemDelegate(self)
        figureEditorDelegate.setItemEditorFactory(figureEditorFactory)

        self.regionTableWidget.cellChanged.connect(self.regionTableWidgetCellChanged)
        self.regionTableWidget.setColumnCount(3)
        self.regionTableWidget.setItemDelegateForColumn(1, colorEditorDelegate)
        self.regionTableWidget.setItemDelegateForColumn(2, figureEditorDelegate)

        self.regionTableWidget.setHorizontalHeaderLabels(["Name", "Color", "Type"])
        self.regionTableWidget.verticalHeader().setVisible(False)
        self.regionTableWidget.resize(150, 50)


        qApp = QtWidgets.qApp
        self.upRegionButton.setIcon(qApp.style().standardIcon(QStyle.SP_ArrowUp))
        self.downRegionButton.setIcon(qApp.style().standardIcon(QStyle.SP_ArrowDown))

        self.addRegionButton.clicked.connect(self.addRegionButtonClicked)
        self.removeRegionButton.clicked.connect(self.removeRegionButtonClicked)
        self.upRegionButton.clicked.connect(self.upRegionButtonClicked)
        self.downRegionButton.clicked.connect(self.downRegionButtonClicked)

    def addRegionButtonClicked(self):
        if not self.videoPlaybackWidget.isOpened():
            return

        name_num = self.regionTableWidget.rowCount()

        for i, name in enumerate(map(lambda x: x.data(Qt.DisplayRole), self.getCol(0))):
            try:
                val = int(name)
            except:
                continue

            name_num = max(name_num, val+1)

        self.addRow(str(name_num), QColor('red'), FigureType.Recutangular)

    def removeRegionButtonClicked(self):
        if not self.videoPlaybackWidget.isOpened():
            return

        if not len(self.regionTableWidget.selectedItems()) > 0:
            return

        selected_row = self.regionTableWidget.row(self.regionTableWidget.selectedItems()[0])

        name_item = self.regionTableWidget.item(selected_row, 0)
        name = name_item.data(Qt.UserRole)

        item = self.getGraphicsItemFromInputScene(name)
        if item is not None:
            self.inputScene.removeItem(item)

        self.regionTableWidget.removeRow(selected_row)

    def upRegionButtonClicked(self):
        if not self.videoPlaybackWidget.isOpened():
            return

        self.moveRow(True)

    def downRegionButtonClicked(self):
        if not self.videoPlaybackWidget.isOpened():
            return

        self.moveRow(False)

    def addRow(self, name, color, figType):
        i = self.regionTableWidget.rowCount()
        self.regionTableWidget.insertRow(i)

        nameItem = QTableWidgetItem(name)
        nameItem.setData(Qt.UserRole, name)
        nameItem.setFlags(Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        colorItem = QTableWidgetItem()
        colorItem.setData(Qt.BackgroundRole, color)
        colorItem.setData(Qt.DisplayRole, color)

        figItem = QTableWidgetItem()
        figItem.setData(Qt.DisplayRole, figType.name)

        self.regionTableWidget.setItem(i, 0, nameItem)
        self.regionTableWidget.setItem(i, 1, colorItem)
        self.regionTableWidget.setItem(i, 2, figItem)

        self.regionTableWidget.resizeColumnToContents(0)
        self.regionTableWidget.horizontalHeader().setStretchLastSection(True)

    def regionTableWidgetCellChanged(self, row, col):
        changed_item = self.regionTableWidget.item(row, col)

        if col==0:
            old_name = changed_item.data(Qt.UserRole)
            new_name = changed_item.data(Qt.DisplayRole)

            if old_name!=new_name:
                for i, name in enumerate(map(lambda x: x.data(Qt.DisplayRole), self.getCol(0))):
                    if i==row:
                        continue

                    if name==new_name:
                        changed_item.setData(Qt.DisplayRole, old_name)
                        return

                item = self.getGraphicsItemFromInputScene(old_name)
                if item is not None:
                    item.setObjectName(new_name)
                changed_item.setData(Qt.UserRole, new_name)

        if col==1:
            try:
                bg_color = changed_item.data(Qt.BackgroundRole)
                disp_color = changed_item.data(Qt.DisplayRole)

                if disp_color.name() != bg_color.name():
                    bg_color.setNamedColor(disp_color.name())
                    changed_item.setData(Qt.BackgroundRole, bg_color)

                    name_item = self.regionTableWidget.item(row, 0)
                    name = name_item.data(Qt.DisplayRole)
                    item = self.getGraphicsItemFromInputScene(name)
                    if item is not None:
                        item.setColor(disp_color)
            except:
                pass

        if col==2:
            old_type = changed_item.data(Qt.UserRole)
            new_type = FigureType[changed_item.data(Qt.DisplayRole)]

            if new_type is not old_type:
                name_item = self.regionTableWidget.item(row, 0)
                name = name_item.data(Qt.UserRole)

                item = self.getGraphicsItemFromInputScene(name)
                if item is not None:
                    self.inputScene.removeItem(item)

                new_fig = new_type.value()
                new_fig.setObjectName(name)
                if new_type is not FigureType.Point:
                    new_fig.setZValue(1000-10*row)
                else:
                    new_fig.autoAdjustRadius(self.cv_img.shape)
                new_fig.setColor(self.regionTableWidget.item(row, 1).data(Qt.BackgroundRole))
                self.inputScene.addItem(new_fig)

                changed_item.setData(Qt.UserRole, new_type)

                height, width, dim = self.cv_img.shape
                if new_type is not FigureType.Point:
                    array = [[0.1*width, 0.1*height], [0.9*width, 0.9*height]]
                else:
                    array = np.array([0.5*width, 0.5*height])
                new_fig.setPoints(array)

        self.updateInputGraphicsView()

    def moveRow(self, up):
        if not len(self.regionTableWidget.selectedItems()) > 0:
            return

        source_row = self.regionTableWidget.row(self.regionTableWidget.selectedItems()[0])
        if up:
            dest_row = source_row-1
        else:
            dest_row = source_row+1

        if not (dest_row >= 0 and dest_row < self.regionTableWidget.rowCount()):
            return

        source_type = self.regionTableWidget.item(source_row, 2).data(Qt.UserRole)
        dest_type = self.regionTableWidget.item(dest_row, 2).data(Qt.UserRole)

        if source_type is not FigureType.Point and dest_type is not FigureType.Point:
            source_name = self.regionTableWidget.item(source_row, 0).data(Qt.DisplayRole)
            source_fig_item = self.getGraphicsItemFromInputScene(source_name)
            source_z = source_fig_item.zValue()

            dest_name = self.regionTableWidget.item(dest_row, 0).data(Qt.DisplayRole)
            dest_fig_item = self.getGraphicsItemFromInputScene(dest_name)
            dest_z = dest_fig_item.zValue()

            source_fig_item.setZValue(dest_z)
            dest_fig_item.setZValue(source_z)

        # take whole rows
        sourceItems = self.takeRow(source_row)
        destItems = self.takeRow(dest_row)

        # set back in reverse order
        self.setRow(source_row, destItems)
        self.setRow(dest_row, sourceItems)

    def takeRow(self, row):
        rowItems = []
        for col in range(self.regionTableWidget.columnCount()):
            rowItems.append(self.regionTableWidget.takeItem(row, col))
        return rowItems

    def getCol(self, col):
        colItems = []
        for row in range(self.regionTableWidget.rowCount()):
            colItems.append(self.regionTableWidget.item(row, col))
        return colItems

    def setRow(self, row, rowItems):
        for col in range(self.regionTableWidget.columnCount()):
            self.regionTableWidget.setItem(row, col, rowItems[col])

    def getGraphicsItemFromInputScene(self, name):
        for item in self.inputScene.items():
            #QGraphicsObjectをSceneから取り出そうとすると，
            #親クラスであるQGraphicsItem(QPixmapGraphicsItem)にダウンキャスト
            #されて返ってくるためtryが必要．
            try:
                if name == item.objectName():
                    return item
            except:
                pass
        return None


    def dragEnterEvent(self,event):
        event.acceptProposedAction()

    def dropEvent(self,event):
        mime = event.mimeData()
        if mime.hasUrls():
            urls = mime.urls()
            if len(urls) > 0:
                self.processDropedFile(urls[0].toLocalFile())

        event.acceptProposedAction()

    def closeEvent(self,event):
        pass

    def processDropedFile(self,filePath):
        root,ext = os.path.splitext(filePath)
        if ext == ".csv":
            self.openCSVFile(filePath=filePath)
        elif self.openVideoFile(filePath=filePath):
            return

    def videoPlaybackInit(self):
        self.videoPlaybackWidget.hide()
        self.videoPlaybackWidget.frameChanged.connect(self.setFrame, type=Qt.QueuedConnection)

    def setFrame(self, frame, frameNo):
        if frame is not None:
            self.cv_img = frame
            self.currentFrameNo = frameNo
            self.updateInputGraphicsView()
            self.evaluate()

    def imgInit(self):
        self.cv_img = cv2.imread(os.path.join(sampleDataPath,"color_filter_test.png"))

        self.inputScene = QGraphicsScene()
        self.inputGraphicsView.setScene(self.inputScene)
        self.inputGraphicsView.resizeEvent = self.inputGraphicsViewResized

        qimg = misc.cvMatToQImage(self.cv_img)
        self.inputPixMap = QPixmap.fromImage(qimg)
        self.inputPixMapItem = QGraphicsPixmapItem(self.inputPixMap)
        self.inputScene.addItem(self.inputPixMapItem)

    def menuInit(self):
        self.actionOpenVideo.triggered.connect(self.openVideoFile)
        self.actionOpenCSVFile.triggered.connect(self.openCSVFile)
        self.actionCalculate.triggered.connect(self.process)

    def openVideoFile(self, activated=False, filePath = None):
        if filePath is None:
            filePath, _ = QFileDialog.getOpenFileName(None, 'Open Video File', userDir)

        if len(filePath) is not 0:
            self.filePath = filePath
            self.fgbg = None

            ret = self.videoPlaybackWidget.openVideo(filePath)
            if ret == False:
                return False

            self.videoPlaybackWidget.show()
            return True

    def openCSVFile(self, activated=False, filePath=None):
        if filePath is None:
            filePath, _ = QFileDialog.getOpenFileName(None, 'Open CSV File', userDir, 'CSV files (*.csv)')

        if len(filePath) is not 0:
            self.filePath = filePath
            self.df = pd.read_csv(filePath, index_col=0)

            if self.trackingPathGroup is not None:
                self.inputScene.removeItem(self.trackingPathGroup)

            self.trackingPathGroup = TrackingPathGroup()
            self.trackingPathGroup.setRect(self.inputScene.sceneRect())
            self.inputScene.addItem(self.trackingPathGroup)

            self.trackingPathGroup.setDataFrame(self.df)

            self.evaluate()


    def updateInputGraphicsView(self):
        self.inputScene.removeItem(self.inputPixMapItem)
        qimg = misc.cvMatToQImage(self.cv_img)
        self.inputPixMap = QPixmap.fromImage(qimg)

        rect = QtCore.QRectF(self.inputPixMap.rect())
        self.inputScene.setSceneRect(rect)

        self.inputPixMapItem = QGraphicsPixmapItem(self.inputPixMap)
        self.inputScene.addItem(self.inputPixMapItem)

        self.inputGraphicsView.viewport().update()
        self.inputGraphicsViewResized()

    def inputGraphicsViewResized(self, event=None):
        self.inputGraphicsView.fitInView(QtCore.QRectF(self.inputPixMap.rect()), QtCore.Qt.KeepAspectRatio)

    def process(self, activated=False):
        if self.df is None or len(self.getCol(0))==0:
            return

        names = list(map(lambda x: x.data(Qt.UserRole), self.getCol(0)))
        items = list(map(lambda x: self.getGraphicsItemFromInputScene(x), names))
        region_list = list(filter(lambda x:type(x[1]) is not FigureType.Point.value, zip(names, items)))
        point_list = list(filter(lambda x:type(x[1]) is FigureType.Point.value, zip(names, items)))

        col_n = int(len(self.df.columns)/2)
        columns = ["{0}_{1}".format(name, col) for col in range(col_n) for name, _ in point_list]

        df = self.df.copy()
        df.columns = list(range(2*col_n))

        self.df_region = pd.DataFrame(
                index=df.index,
                columns=range(col_n)
                )

        self.df_dist = pd.DataFrame(
                index=df.index,
                columns=columns
                )

        progress = QProgressDialog("Running...", "Abort", 0, len(df.index), self)
        progress.setWindowModality(Qt.WindowModal)

        for i, row in enumerate(df.index):
            progress.setValue(i)
            if progress.wasCanceled():
                break

            for col in range(col_n):
                pt = np.array(df.loc[row, 2*col:2*col+1])
                for name, item in point_list:
                    self.df_dist.loc[row, "{0}_{1}".format(name, col)] = item.distance(pt)
                for name, item in region_list:
                    if item.includes(pt):
                        self.df_region.loc[row, col] = name
                        break

        progress.setValue(len(df.index))
        self.saveCSVFile()

    def saveCSVFile(self, activated=False, filePath = None):
        if self.df is None or self.df_dist is None or self.df_region is None:
            return

        dirctory = os.path.dirname(self.filePath)
        base_name = os.path.splitext(os.path.basename(self.filePath))[0]

        for attr in ['distance', 'region']:
            path = os.path.join(dirctory, '{0}-{1}.csv'.format(base_name, attr))
            filePath, _ = QFileDialog.getSaveFileName(None, 'Save CSV File', path, "CSV files (*.csv)")

            if len(filePath) is not 0:
                logger.debug("Saving CSV file: {0}".format(filePath))
                if attr=='distance':
                    self.df_dist.to_csv(filePath)
                elif attr=='region':
                    self.df_region.to_csv(filePath)

    def evaluate(self):
        if self.df is None or not self.videoPlaybackWidget.isOpened():
            return

        if self.trackingPathGroup is not None:
            self.trackingPathGroup.setPoints(self.currentFrameNo)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = Ui_MainWindow()
    MainWindow.setWindowIcon(QIcon(':/icon/icon.ico'))
    MainWindow.setWindowTitle('UMATracker-Area51')
    MainWindow.show()
    sys.exit(app.exec_())

