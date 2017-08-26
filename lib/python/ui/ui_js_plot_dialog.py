# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_js_plot_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_JSPlotDialog(object):
    def setupUi(self, JSPlotDialog):
        JSPlotDialog.setObjectName("JSPlotDialog")
        JSPlotDialog.resize(650, 650)
        JSPlotDialog.setMinimumSize(QtCore.QSize(650, 650))
        JSPlotDialog.setMaximumSize(QtCore.QSize(650, 650))
        self.horizontalLayout = QtWidgets.QHBoxLayout(JSPlotDialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.webView = QtWebEngineWidgets.QWebEngineView(JSPlotDialog)
        self.webView.setUrl(QtCore.QUrl("about:blank"))
        self.webView.setObjectName("webView")
        self.horizontalLayout.addWidget(self.webView)

        self.retranslateUi(JSPlotDialog)
        QtCore.QMetaObject.connectSlotsByName(JSPlotDialog)

    def retranslateUi(self, JSPlotDialog):
        _translate = QtCore.QCoreApplication.translate
        JSPlotDialog.setWindowTitle(_translate("JSPlotDialog", "Dialog"))

from PyQt5 import QtWebEngineWidgets
