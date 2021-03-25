# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Interfaces\Base_Recipe_Dialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_RecipeDialog(object):
    def setupUi(self, RecipeDialog):
        RecipeDialog.setObjectName("RecipeDialog")
        RecipeDialog.resize(270, 429)
        self.recipeListWidget = QtWidgets.QListWidget(RecipeDialog)
        self.recipeListWidget.setGeometry(QtCore.QRect(10, 5, 250, 301))
        self.recipeListWidget.setObjectName("recipeListWidget")
        self.loadLastCheckBox = QtWidgets.QCheckBox(RecipeDialog)
        self.loadLastCheckBox.setGeometry(QtCore.QRect(30, 310, 210, 32))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.loadLastCheckBox.setFont(font)
        self.loadLastCheckBox.setChecked(True)
        self.loadLastCheckBox.setObjectName("loadLastCheckBox")
        self.loadButton = QtWidgets.QPushButton(RecipeDialog)
        self.loadButton.setGeometry(QtCore.QRect(30, 395, 101, 23))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.loadButton.setFont(font)
        self.loadButton.setObjectName("loadButton")
        self.cancelButton = QtWidgets.QPushButton(RecipeDialog)
        self.cancelButton.setGeometry(QtCore.QRect(140, 395, 101, 23))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.cancelButton.setFont(font)
        self.cancelButton.setObjectName("cancelButton")
        self.loadSpecificCheckBox = QtWidgets.QCheckBox(RecipeDialog)
        self.loadSpecificCheckBox.setGeometry(QtCore.QRect(30, 335, 210, 32))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.loadSpecificCheckBox.setFont(font)
        self.loadSpecificCheckBox.setChecked(False)
        self.loadSpecificCheckBox.setObjectName("loadSpecificCheckBox")
        self.loadSpecificLineEdit = QtWidgets.QLineEdit(RecipeDialog)
        self.loadSpecificLineEdit.setGeometry(QtCore.QRect(70, 365, 113, 20))
        self.loadSpecificLineEdit.setObjectName("loadSpecificLineEdit")

        self.retranslateUi(RecipeDialog)
        QtCore.QMetaObject.connectSlotsByName(RecipeDialog)

    def retranslateUi(self, RecipeDialog):
        _translate = QtCore.QCoreApplication.translate
        RecipeDialog.setWindowTitle(_translate("RecipeDialog", "Dialog"))
        self.loadLastCheckBox.setText(_translate("RecipeDialog", "Parameters from last run"))
        self.loadButton.setText(_translate("RecipeDialog", "Load"))
        self.cancelButton.setText(_translate("RecipeDialog", "Cancel"))
        self.loadSpecificCheckBox.setText(_translate("RecipeDialog", "Parameters from SQUID:"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    RecipeDialog = QtWidgets.QDialog()
    ui = Ui_RecipeDialog()
    ui.setupUi(RecipeDialog)
    RecipeDialog.show()
    sys.exit(app.exec_())
