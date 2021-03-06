# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Interfaces\Base_Display_Window.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_DisplayWindow(object):
    def setupUi(self, DisplayWindow):
        DisplayWindow.setObjectName("DisplayWindow")
        DisplayWindow.resize(1015, 806)
        self.plotFrame = QtWidgets.QFrame(DisplayWindow)
        self.plotFrame.setGeometry(QtCore.QRect(460, 5, 905, 800))
        self.plotFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.plotFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.plotFrame.setObjectName("plotFrame")
        self.parametersFrame = QtWidgets.QFrame(DisplayWindow)
        self.parametersFrame.setGeometry(QtCore.QRect(5, 5, 450, 600))
        self.parametersFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.parametersFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.parametersFrame.setObjectName("parametersFrame")
        self.saveButton = QtWidgets.QPushButton(DisplayWindow)
        self.saveButton.setGeometry(QtCore.QRect(155, 750, 150, 50))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.saveButton.setFont(font)
        self.saveButton.setObjectName("saveButton")
        self.notesBrowser = QtWidgets.QTextBrowser(DisplayWindow)
        self.notesBrowser.setGeometry(QtCore.QRect(5, 610, 450, 130))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.notesBrowser.setFont(font)
        self.notesBrowser.setObjectName("notesBrowser")

        self.retranslateUi(DisplayWindow)
        QtCore.QMetaObject.connectSlotsByName(DisplayWindow)

    def retranslateUi(self, DisplayWindow):
        _translate = QtCore.QCoreApplication.translate
        DisplayWindow.setWindowTitle(_translate("DisplayWindow", "Form"))
        self.saveButton.setText(_translate("DisplayWindow", "Save"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    DisplayWindow = QtWidgets.QWidget()
    ui = Ui_DisplayWindow()
    ui.setupUi(DisplayWindow)
    DisplayWindow.show()
    sys.exit(app.exec_())
