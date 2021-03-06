# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Base_Process_Window.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_mainWindow(object):
    def setupUi(self, mainWindow):
        mainWindow.setObjectName("mainWindow")
        mainWindow.resize(966, 678)
        self.centralWidget = QtWidgets.QWidget(mainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.instructionsFrame = QtWidgets.QFrame(self.centralWidget)
        self.instructionsFrame.setGeometry(QtCore.QRect(0, 0, 951, 351))
        self.instructionsFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.instructionsFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.instructionsFrame.setObjectName("instructionsFrame")
        self.stepStaticLabel = QtWidgets.QLabel(self.instructionsFrame)
        self.stepStaticLabel.setGeometry(QtCore.QRect(670, 0, 71, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.stepStaticLabel.setFont(font)
        self.stepStaticLabel.setObjectName("stepStaticLabel")
        self.stepLabel = QtWidgets.QLabel(self.instructionsFrame)
        self.stepLabel.setGeometry(QtCore.QRect(740, 0, 28, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.stepLabel.setFont(font)
        self.stepLabel.setObjectName("stepLabel")
        self.insDisplay = QtWidgets.QTextEdit(self.instructionsFrame)
        self.insDisplay.setGeometry(QtCore.QRect(3, 3, 661, 348))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.insDisplay.setFont(font)
        self.insDisplay.setAcceptDrops(False)
        self.insDisplay.setReadOnly(True)
        self.insDisplay.setObjectName("insDisplay")
        self.statusStaticLabel = QtWidgets.QLabel(self.instructionsFrame)
        self.statusStaticLabel.setGeometry(QtCore.QRect(775, 0, 61, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.statusStaticLabel.setFont(font)
        self.statusStaticLabel.setObjectName("statusStaticLabel")
        self.statusLabel = QtWidgets.QLabel(self.instructionsFrame)
        self.statusLabel.setEnabled(True)
        self.statusLabel.setGeometry(QtCore.QRect(840, 0, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.statusLabel.setFont(font)
        self.statusLabel.setObjectName("statusLabel")
        self.formLayoutWidget = QtWidgets.QWidget(self.instructionsFrame)
        self.formLayoutWidget.setGeometry(QtCore.QRect(670, 60, 271, 291))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.coreParamsLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.coreParamsLayout.setContentsMargins(0, 0, 0, 0)
        self.coreParamsLayout.setHorizontalSpacing(7)
        self.coreParamsLayout.setVerticalSpacing(5)
        self.coreParamsLayout.setObjectName("coreParamsLayout")
        self.timerStaticLabel = QtWidgets.QLabel(self.instructionsFrame)
        self.timerStaticLabel.setGeometry(QtCore.QRect(670, 30, 71, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.timerStaticLabel.setFont(font)
        self.timerStaticLabel.setObjectName("timerStaticLabel")
        self.timerLabel = QtWidgets.QLabel(self.instructionsFrame)
        self.timerLabel.setGeometry(QtCore.QRect(730, 30, 201, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.timerLabel.setFont(font)
        self.timerLabel.setObjectName("timerLabel")
        self.parametersFrame = QtWidgets.QFrame(self.centralWidget)
        self.parametersFrame.setGeometry(QtCore.QRect(-1, 399, 951, 231))
        self.parametersFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.parametersFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.parametersFrame.setObjectName("parametersFrame")
        self.formLayoutWidget_2 = QtWidgets.QWidget(self.parametersFrame)
        self.formLayoutWidget_2.setGeometry(QtCore.QRect(9, 9, 291, 221))
        self.formLayoutWidget_2.setObjectName("formLayoutWidget_2")
        self.paramCol1Layout = QtWidgets.QFormLayout(self.formLayoutWidget_2)
        self.paramCol1Layout.setContentsMargins(0, 0, 0, 0)
        self.paramCol1Layout.setHorizontalSpacing(7)
        self.paramCol1Layout.setVerticalSpacing(5)
        self.paramCol1Layout.setObjectName("paramCol1Layout")
        self.formLayoutWidget_3 = QtWidgets.QWidget(self.parametersFrame)
        self.formLayoutWidget_3.setGeometry(QtCore.QRect(330, 10, 291, 221))
        self.formLayoutWidget_3.setObjectName("formLayoutWidget_3")
        self.paramCol2Layout = QtWidgets.QFormLayout(self.formLayoutWidget_3)
        self.paramCol2Layout.setContentsMargins(0, 0, 0, 0)
        self.paramCol2Layout.setHorizontalSpacing(7)
        self.paramCol2Layout.setVerticalSpacing(5)
        self.paramCol2Layout.setObjectName("paramCol2Layout")
        self.formLayoutWidget_4 = QtWidgets.QWidget(self.parametersFrame)
        self.formLayoutWidget_4.setGeometry(QtCore.QRect(650, 10, 291, 221))
        self.formLayoutWidget_4.setObjectName("formLayoutWidget_4")
        self.paramCol3Layout = QtWidgets.QFormLayout(self.formLayoutWidget_4)
        self.paramCol3Layout.setContentsMargins(0, 0, 0, 0)
        self.paramCol3Layout.setHorizontalSpacing(7)
        self.paramCol3Layout.setVerticalSpacing(5)
        self.paramCol3Layout.setObjectName("paramCol3Layout")
        self.proceedButton = QtWidgets.QPushButton(self.centralWidget)
        self.proceedButton.setEnabled(True)
        self.proceedButton.setGeometry(QtCore.QRect(114, 355, 181, 41))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.proceedButton.setFont(font)
        self.proceedButton.setObjectName("proceedButton")
        self.abortButton = QtWidgets.QPushButton(self.centralWidget)
        self.abortButton.setGeometry(QtCore.QRect(650, 355, 181, 41))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.abortButton.setFont(font)
        self.abortButton.setObjectName("abortButton")
        self.pauseButton = QtWidgets.QPushButton(self.centralWidget)
        self.pauseButton.setEnabled(True)
        self.pauseButton.setGeometry(QtCore.QRect(382, 355, 181, 41))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.pauseButton.setFont(font)
        self.pauseButton.setObjectName("pauseButton")
        mainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtWidgets.QMenuBar(mainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 966, 21))
        self.menuBar.setObjectName("menuBar")
        self.fileMenu = QtWidgets.QMenu(self.menuBar)
        self.fileMenu.setObjectName("fileMenu")
        self.displayMenu = QtWidgets.QMenu(self.menuBar)
        self.displayMenu.setObjectName("displayMenu")
        mainWindow.setMenuBar(self.menuBar)
        self.statusBar = QtWidgets.QStatusBar(mainWindow)
        self.statusBar.setObjectName("statusBar")
        mainWindow.setStatusBar(self.statusBar)
        self.loadRecipeAction = QtWidgets.QAction(mainWindow)
        self.loadRecipeAction.setObjectName("loadRecipeAction")
        self.abortAction = QtWidgets.QAction(mainWindow)
        self.abortAction.setObjectName("abortAction")
        self.exitAction = QtWidgets.QAction(mainWindow)
        self.exitAction.setObjectName("exitAction")
        self.openTipAction = QtWidgets.QAction(mainWindow)
        self.openTipAction.setObjectName("openTipAction")
        self.calibrateAction = QtWidgets.QAction(mainWindow)
        self.calibrateAction.setObjectName("calibrateAction")
        self.fileMenu.addAction(self.loadRecipeAction)
        self.fileMenu.addAction(self.calibrateAction)
        self.fileMenu.addAction(self.abortAction)
        self.fileMenu.addAction(self.exitAction)
        self.displayMenu.addAction(self.openTipAction)
        self.menuBar.addAction(self.fileMenu.menuAction())
        self.menuBar.addAction(self.displayMenu.menuAction())

        self.retranslateUi(mainWindow)
        QtCore.QMetaObject.connectSlotsByName(mainWindow)

    def retranslateUi(self, mainWindow):
        _translate = QtCore.QCoreApplication.translate
        mainWindow.setWindowTitle(_translate("mainWindow", "MainWindow"))
        self.stepStaticLabel.setText(_translate("mainWindow", "Step #:"))
        self.stepLabel.setText(_translate("mainWindow", "##"))
        self.statusStaticLabel.setText(_translate("mainWindow", "Status:"))
        self.statusLabel.setText(_translate("mainWindow", "<Standby>"))
        self.timerStaticLabel.setText(_translate("mainWindow", "Timer:"))
        self.timerLabel.setText(_translate("mainWindow", "   "))
        self.proceedButton.setText(_translate("mainWindow", "Start"))
        self.abortButton.setText(_translate("mainWindow", "Abort"))
        self.pauseButton.setText(_translate("mainWindow", "Pause"))
        self.fileMenu.setTitle(_translate("mainWindow", "File"))
        self.displayMenu.setTitle(_translate("mainWindow", "Display"))
        self.loadRecipeAction.setText(_translate("mainWindow", "Load Recipe"))
        self.abortAction.setText(_translate("mainWindow", "Abort Process"))
        self.exitAction.setText(_translate("mainWindow", "Exit"))
        self.openTipAction.setText(_translate("mainWindow", "Open Previous"))
        self.calibrateAction.setText(_translate("mainWindow", "Calibrate"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = QtWidgets.QMainWindow()
    ui = Ui_mainWindow()
    ui.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec_())
