# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Interfaces\Base_Status_Window.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_StatusWindow(object):
    def setupUi(self, StatusWindow):
        StatusWindow.setObjectName("StatusWindow")
        StatusWindow.resize(1173, 757)
        self.vacuumFrame = QtWidgets.QFrame(StatusWindow)
        self.vacuumFrame.setGeometry(QtCore.QRect(5, 5, 450, 250))
        self.vacuumFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.vacuumFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.vacuumFrame.setObjectName("vacuumFrame")
        self.pressureStaticLabel = QtWidgets.QLabel(self.vacuumFrame)
        self.pressureStaticLabel.setGeometry(QtCore.QRect(0, 0, 150, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.pressureStaticLabel.setFont(font)
        self.pressureStaticLabel.setObjectName("pressureStaticLabel")
        self.pressureStaticLabel_2 = QtWidgets.QLabel(self.vacuumFrame)
        self.pressureStaticLabel_2.setGeometry(QtCore.QRect(150, 0, 91, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.pressureStaticLabel_2.setFont(font)
        self.pressureStaticLabel_2.setObjectName("pressureStaticLabel_2")
        self.plotFrame = QtWidgets.QFrame(StatusWindow)
        self.plotFrame.setGeometry(QtCore.QRect(5, 255, 450, 450))
        self.plotFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.plotFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.plotFrame.setObjectName("plotFrame")
        self.plot1 = PlotWidget(self.plotFrame)
        self.plot1.setGeometry(QtCore.QRect(0, 0, 450, 450))
        self.plot1.setObjectName("plot1")
        self.variablesFrame = QtWidgets.QFrame(StatusWindow)
        self.variablesFrame.setGeometry(QtCore.QRect(460, 5, 300, 700))
        self.variablesFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.variablesFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.variablesFrame.setObjectName("variablesFrame")
        self.serversFrame = QtWidgets.QFrame(StatusWindow)
        self.serversFrame.setGeometry(QtCore.QRect(765, 5, 400, 700))
        self.serversFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.serversFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.serversFrame.setObjectName("serversFrame")

        self.retranslateUi(StatusWindow)
        QtCore.QMetaObject.connectSlotsByName(StatusWindow)

    def retranslateUi(self, StatusWindow):
        _translate = QtCore.QCoreApplication.translate
        StatusWindow.setWindowTitle(_translate("StatusWindow", "Form"))
        self.pressureStaticLabel.setText(_translate("StatusWindow", "Pressure (mbar):"))
        self.pressureStaticLabel_2.setText(_translate("StatusWindow", "####"))
from pyqtgraph import PlotWidget


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    StatusWindow = QtWidgets.QWidget()
    ui = Ui_StatusWindow()
    ui.setupUi(StatusWindow)
    StatusWindow.show()
    sys.exit(app.exec_())
