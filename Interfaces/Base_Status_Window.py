# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Base_Status_Window.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_StatusWindow(object):
    def setupUi(self, StatusWindow):
        StatusWindow.setObjectName("StatusWindow")
        StatusWindow.resize(1615, 810)
        self.plotFrame = QtWidgets.QFrame(StatusWindow)
        self.plotFrame.setGeometry(QtCore.QRect(510, 405, 1100, 400))
        self.plotFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.plotFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.plotFrame.setObjectName("plotFrame")
        self.variablesFrame = QtWidgets.QFrame(StatusWindow)
        self.variablesFrame.setGeometry(QtCore.QRect(510, 5, 550, 400))
        self.variablesFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.variablesFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.variablesFrame.setObjectName("variablesFrame")
        self.ManualWidgetFrame = QtWidgets.QFrame(StatusWindow)
        self.ManualWidgetFrame.setGeometry(QtCore.QRect(5, 30, 500, 750))
        self.ManualWidgetFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.ManualWidgetFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.ManualWidgetFrame.setObjectName("ManualWidgetFrame")
        self.defaultPlotFrame = QtWidgets.QFrame(StatusWindow)
        self.defaultPlotFrame.setGeometry(QtCore.QRect(1060, 5, 550, 400))
        self.defaultPlotFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.defaultPlotFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.defaultPlotFrame.setObjectName("defaultPlotFrame")
        self.timerLabel = QtWidgets.QLabel(StatusWindow)
        self.timerLabel.setGeometry(QtCore.QRect(60, 0, 201, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.timerLabel.setFont(font)
        self.timerLabel.setText("")
        self.timerLabel.setObjectName("timerLabel")
        self.timerStaticLabel = QtWidgets.QLabel(StatusWindow)
        self.timerStaticLabel.setGeometry(QtCore.QRect(0, 0, 71, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.timerStaticLabel.setFont(font)
        self.timerStaticLabel.setObjectName("timerStaticLabel")

        self.retranslateUi(StatusWindow)
        QtCore.QMetaObject.connectSlotsByName(StatusWindow)

    def retranslateUi(self, StatusWindow):
        _translate = QtCore.QCoreApplication.translate
        StatusWindow.setWindowTitle(_translate("StatusWindow", "Form"))
        self.timerStaticLabel.setText(_translate("StatusWindow", "Timer:"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    StatusWindow = QtWidgets.QWidget()
    ui = Ui_StatusWindow()
    ui.setupUi(StatusWindow)
    StatusWindow.show()
    sys.exit(app.exec_())
