#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, time

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QDialog, QProgressDialog
from PyQt5.QtGui import QPixmap, QColor, QBrush, QImage
from PyQt5.QtCore import QRectF, QPointF, Qt, QUrl

try:
    from ui_js_plot_dialog import Ui_JSPlotDialog
except ImportError:
    from .ui_js_plot_dialog import Ui_JSPlotDialog

import cv2

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

# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    current_dir_path = sys._MEIPASS
    print(current_dir_path)
    if os.name == 'nt':
        import win32api

        win32api.SetDllDirectory(sys._MEIPASS)
elif __file__:
    current_dir_path = os.getcwd()

import urllib.request
if os.path.exists(os.path.join(current_dir_path, "index.html")):
    d3_url = "file:" + urllib.request.pathname2url(os.path.join(current_dir_path, "index.html"))
else:
    d3_url = "file:" + urllib.request.pathname2url(os.path.join(current_dir_path, 'lib', 'd3', "index.html"))

class ChordDiagramDialog(Ui_JSPlotDialog, QDialog):
    def __init__(self, parent=None):
        Ui_JSPlotDialog.__init__(self)
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.webView.loadFinished.connect(self.draw)
        self.webView.load(QUrl(d3_url))

        self.matrix = [
                [11975,  5871, 8916, 2868],
                [ 1951, 10048, 2060, 6171],
                [ 8010, 16145, 8090, 8045],
                [ 1013,   990,  940, 6907]
                ]

        self.colors = ["#000000", "#FFDD89", "#957244", "#F26223"]

    def setMatrix(self, mtx):
        self.matrix = mtx

    def setColors(self, clr):
        self.colors = [QColor(rgb).name() for rgb in clr]

    def show(self):
        self.webView.load(QUrl(d3_url))
        QDialog.show(self)

    def draw(self, flag):
        frame= self.webView.page().mainFrame()
        frame.evaluateJavaScript("draw_chord_diagram({mtx}, {clr})".format(mtx=self.matrix, clr=self.colors))

    def closeEvent(self,event):
        pass


class TimelineDiagramDialog(Ui_JSPlotDialog, QDialog):
    def __init__(self, parent=None):
        Ui_JSPlotDialog.__init__(self)
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.webView.loadFinished.connect(self.draw)
        self.webView.load(QUrl(d3_url))

        self.tasks = [
                {
                    "startDate": 10,
                    "endDate": 20,
                    "taskName": "E Job",
                    "status": "no0"
                    },
                {
                    "startDate": 30,
                    "endDate": 40,
                    "taskName": "A Job",
                    "status": "no1"
                    }
                ]

        self.taskNames = [ "D Job", "P Job", "E Job", "A Job", "N Job" ]
        self.statusNames = ["no0", "no1"]
        self.colors = ["#000000", "#FFDD89", "#957244", "#F26223"]

    def setTasks(self, tasks):
        self.tasks = tasks

        taskNames = {}
        statusNames = {}

        for task in self.tasks:
            taskName = task["taskName"]
            statusName = str(task["status"])

            taskNames[taskName] = 0
            statusName = "no" + statusName
            task["status"] = statusName
            statusNames[statusName] = 0

        self.taskNames = list(taskNames.keys())
        self.statusNames = list(statusNames.keys())

    def setColors(self, clr):
        self.colors = [clr[name].name() for name in self.statusNames]

    def show(self):
        self.webView.load(QUrl(d3_url))
        QDialog.show(self)

    def draw(self, flag):
        frame= self.webView.page().mainFrame()
        frame.evaluateJavaScript("draw_timeline_diagram({tasks}, {taskNames}, {statusNames}, {colors})".format(tasks=self.tasks, taskNames=self.taskNames, statusNames=self.statusNames, colors=self.colors))

    def closeEvent(self,event):
        pass

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Dialog = ChordDiagramDialog()
    Dialog.show()
    sys.exit(app.exec_())

