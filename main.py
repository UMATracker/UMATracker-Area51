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

import re, hashlib, json, itertools, operator

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QFileDialog, QMainWindow, QDialog, QItemEditorCreatorBase, QItemEditorFactory, QTableWidget, QTableWidgetItem, QStyledItemDelegate, QProgressDialog, QStyle
from PyQt5.QtGui import QPixmap, QColor, QBrush, QIcon, QPen
from PyQt5.QtCore import QRectF, QPointF, Qt, QVariant, pyqtSignal, pyqtSlot
# from shapely.geometry import Polygon, Point

import cv2
import pandas as pd
import numpy as np
import pyqtgraph as pg

import icon
from lib.python import misc
from lib.python.ui.main_window_base import Ui_MainWindowBase
from lib.python.ui.tracking_path_group import TrackingPathGroup
from lib.python.ui.editorfactory import *

from lib.python.ui.js_plot_dialog import *

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

import math

def nCr(n,r):
    f = math.factorial
    return f(n) / f(r) / f(n-r)

def get_interval(data):
    ranges = []
    for key, group in itertools.groupby(enumerate(data), lambda index: index[0] - index[1]):
        group = list(map(operator.itemgetter(1), group))
        if len(group) > 1:
            ranges.append((group[0], group[-1]))
        else:
            ranges.append((group[0], group[0]))
    return ranges


class Ui_MainWindow(QMainWindow, Ui_MainWindowBase):
    updateFrame = pyqtSignal()

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
        self.relation_matrix = None
        self.trackingPathGroup = None
        self.currentFrameNo = None

        self.graphics_items = {}
        self.plot_widgets = []

        factory = QItemEditorFactory()
        factory.registerEditor(QVariant.Color, ColorListItemEditorCreator())

        self.createGUI()

        self.updateFrame.connect(self.videoPlaybackWidget.videoPlayback)

        self.chord_diagram_dialog = ChordDiagramDialog(self)
        self.timeline_diagram_dialog = TimelineDiagramDialog(self)

        self.savedFlag = True

        # dialog = TimelineDiagramDialog(self)
        # dialog.show()

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

        self.radiusSpinBox.valueChanged.connect(self.radiusSpinBoxValueChanged)

    def radiusSpinBoxValueChanged(self, i):
        if self.trackingPathGroup is not None:
            self.trackingPathGroup.setRadius(i)
        self.updateInputGraphicsView()

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

        item = self.graphics_items.pop(name)
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

                self.graphicsItem[new_name] = self.graphics_items.pop(old_name)
                item = self.graphics_items[new_name]
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
                    item = self.graphics_items[name]
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

                self.graphics_items[name] = new_fig

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
            source_fig_item = self.graphicsItem[source_name]
            source_z = source_fig_item.zValue()

            dest_name = self.regionTableWidget.item(dest_row, 0).data(Qt.DisplayRole)
            dest_fig_item = self.graphics_items[dest_name]
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

    def closeEvent(self, event):
        if self.df is None or self.savedFlag:
            return

        quit_msg = "Data is not saved.\nAre you sure you want to exit the program?"
        reply = QtWidgets.QMessageBox.question(
                self,
                'Warning',
                quit_msg,
                QtWidgets.QMessageBox.Yes,
                QtWidgets.QMessageBox.No
                )

        if reply == QtWidgets.QMessageBox.Yes:
            self.closeDialog()
            event.accept()
        else:
            event.ignore()

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
        self.actionSaveCSVFile.triggered.connect(self.saveCSVFile)
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
            self.cv_img = self.videoPlaybackWidget.getCurrentFrame()

            self.initialize()

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

            self.initialize()

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

    def closeDialog(self):
        self.chord_diagram_dialog.hide()
        self.timeline_diagram_dialog.hide()
        for plot_widget in self.plot_widgets:
            plot_widget.window().close()
        self.plot_widgets.clear()

    def process(self, activated=False):
        # if self.df is None or len(self.getCol(0))==0:
        #     return

        if self.df is None:
            return

        self.closeDialog()

        names = list(map(lambda x: x.data(Qt.UserRole), self.getCol(0)))
        items = [self.graphics_items[name] for name in names]
        colors = {('no'+name):color.data(Qt.BackgroundRole) for name, color in zip(names, self.getCol(1))}
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

        interactions = [0 for i in range(int(nCr(col_n, 2)))]
        radius = 2*self.trackingPathGroup.getRadius()
        # radius = 100


        for i, row in enumerate(df.index):
            progress.setValue(i)
            if progress.wasCanceled():
                break

            pts = []
            for col in range(col_n):
                pt = np.array(df.loc[row, 2*col:2*col+1])
                pts.append(pt)
                for name, item in point_list:
                    self.df_dist.loc[row, "{0}_{1}".format(name, col)] = item.distance(pt)
                for name, item in region_list:
                    if item.includes(pt):
                        self.df_region.loc[row, col] = name
                        break
            for count, (p1, p2) in enumerate(itertools.combinations(pts, 2)):
                d = np.linalg.norm(p1-p2)
                if d <= radius:
                    interactions[count] += 1
        progress.setValue(len(df.index))

        matrix = np.zeros((col_n, col_n))
        for pos, (i, j) in enumerate(itertools.combinations(range(col_n), 2)):
            matrix[i, j] = interactions[pos]
            matrix[j, i] = interactions[pos]

        for name, item in point_list:
            plot_widget = pg.plot(title="Point: "+name)
            plot_widget.addLegend()
            plot_item = plot_widget.getPlotItem()
            bottom_axis = plot_item.getAxis("bottom")
            bottom_axis.setLabel("# of Frame")
            left_axis = plot_item.getAxis("left")
            left_axis.setLabel("Distance [pixel]")
            for col, color in zip(range(col_n), self.trackingPathGroup.getColors()):
                pen = QPen(QColor(*color))
                pen.setWidth(5)
                plot_widget.plot(self.df_dist.loc[:, "{0}_{1}".format(name, col)], pen=pen, name=str(col))

            self.plot_widgets.append(plot_widget)

        tasks = []
        for name, item in region_list:
            for col in range(col_n):
                df = self.df_region.loc[self.df_region.loc[:, col]==name, col]

                intervals = get_interval(df.index)
                for interval in intervals:
                    start, end = interval
                    data = {
                            "startDate": start,
                            "endDate": end,
                            "taskName": col,
                            "status": name
                    }
                    tasks.append(data)

        self.chord_diagram_dialog.setMatrix(matrix.tolist())
        self.chord_diagram_dialog.setColors(self.trackingPathGroup.getColors())
        self.timeline_diagram_dialog.setTasks(tasks)
        self.timeline_diagram_dialog.setColors(colors)

        self.chord_diagram_dialog.show()

        if len(region_list)!=0:
            self.timeline_diagram_dialog.show()


        self.relation_matrix = matrix

        self.savedFlag = False

        # self.saveCSVFile()

    def saveCSVFile(self, activated=False, filePath = None):
        if self.df is None or self.df_dist is None or self.df_region is None or self.relation_matrix is None:
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

        path = os.path.join(dirctory, '{0}-relation.csv'.format(base_name))
        filePath, _ = QFileDialog.getSaveFileName(None, 'Save CSV File', path, "CSV files (*.csv)")
        if len(filePath) is not 0:
            pd.DataFrame(self.relation_matrix).to_csv(filePath)

        self.savedFlag = True

    def initialize(self):
        if self.df is None or not self.videoPlaybackWidget.isOpened():
            return

        self.trackingPathGroup.setPoints(self.currentFrameNo)
        r = self.trackingPathGroup.autoAdjustRadius(self.cv_img.shape)
        self.radiusSpinBox.setValue(r)

    def evaluate(self, update=True):
        if self.df is None or not self.videoPlaybackWidget.isOpened():
            pass
        else:
            if self.trackingPathGroup is not None:
                self.trackingPathGroup.setPoints(self.currentFrameNo)

        if update:
            self.updateFrame.emit()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = Ui_MainWindow()
    MainWindow.setWindowIcon(QIcon(':/icon/icon.ico'))
    MainWindow.setWindowTitle('UMATracker-Area51')
    MainWindow.show()
    sys.exit(app.exec_())

