'''
A Modules for customized widgets
'''
import os
from os.path import join

from inspect import getmembers, isclass
from importlib.util import spec_from_file_location #, module_from_spec

from PyQt5 import QtCore
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QLabel, QMainWindow, QListWidgetItem, QDoubleSpinBox, QWidget
#from PyQt5.QtWidgets import QFrame, QSizePolicy, QGridLayout

from Interfaces.Base_Recipe_Dialog import Ui_RecipeDialog
import recipe

class BaseMainWindow(QMainWindow):
    '''
    Need this stupid wrapper because Qt Designer does not inhert from QMainWindow so the references
    get convoluted. Call thisInstance.setSubRef(self) from the class inheriting from QtDesigner and
    then this base can pass events to that instance, such as the closeEvent.
    '''
    def setSubRef(self, ref):
        '''
        Call this when setting up the subclass (inherited from the Qt Designer code) in order to
        reference it from the main Window itself.
        '''
        self.UIsubclass = ref
    #

    def closeEvent(self, event):
        if hasattr(self, 'UIsubclass'):
            self.UIsubclass.closeEvent(event)
        else:
            event.accept()
    #
#

class BaseStatusWidget(QWidget):
    '''
    Need this stupid wrapper because Qt Designer does not inhert from QWidget so the references
    get convoluted. Call thisInstance.setGUIRef(self) from the class inheriting from QtDesigner and
    then this base can pass events to the mainWindow
    '''

    def setGUIRef(self, ref):
        '''
        Call this when setting up the subclass (inherited from the Qt Designer code) in order to
        reference it from the main Window itself.
        '''
        self.GUIref = ref
    #

    def closeEvent(self, event):
        if hasattr(self, 'GUIref'):
            self.GUIref.close()
            event.ignore()
        else:
            event.accept()
    #
#

class RecipeDialog(Ui_RecipeDialog):
    '''
    A Dialog box to select the Recipe to load.
    '''
    def loadRecipes(self, directory):
        recipe_members = dict(getmembers(recipe, isclass))
        self.items = dict()
        for filename in os.listdir(directory):
            if filename.endswith('.py') and filename != "__init__.py":
                spec = spec_from_file_location(filename,join(directory, filename))
                module = spec.loader.load_module()
                for name, obj in getmembers(module, isclass):
                    if name not in recipe_members:
                        key = name.replace('_', ' ')
                        self.items[key] = obj
                        self.recipeListWidget.addItem(QListWidgetItem(key))
    #

    def setupUi(self, parent):
        super().setupUi(parent)
        self.cancelled = True
        self.parent = parent
        self.loadButton.clicked.connect(self.loadCallback)
        self.cancelButton.clicked.connect(self.cancelCallback)

        self.loadLastCheckBox.toggled.connect(self.loadLastCallback)
        self.loadSpecificCheckBox.toggled.connect(self.loadSpecificCallback)
        self.load_last = True

        self.parent.setWindowIcon(QIcon(join('Interfaces','images','squid_tip.png')))
    #

    def getRecipe(self):
        '''
        Return the recipe class, returns None if cancelled.
        '''
        if self.cancelled:
            return None
        key = self.recipeListWidget.currentItem().text()
        return self.items[key]
    #

    def getLoadState(self):
        '''
        Get the options for loading the previous parameters.

        Returns None is the parameters of the last run are to be used. Returns the SQUID name
        for loading a specific SQUID.
        '''
        if self.load_last:
            return None
        else:
            return str(self.loadSpecificLineEdit.text())
    #

    def loadCallback(self):
        self.cancelled = False
        self.parent.close()
    #

    def cancelCallback(self):
        self.cancelled = True
        self.parent.close()
    #

    def loadLastCallback(self):
        if self.loadLastCheckBox.isChecked():
            self.loadSpecificCheckBox.setChecked(False)
            self.load_last = True
    #

    def loadSpecificCallback(self):
        if self.loadSpecificCheckBox.isChecked():
            self.loadLastCheckBox.setChecked(False)
            self.load_last = False
    #
#

class CustomSpinBox(QDoubleSpinBox):
    def textFromValue(self, value):
        return str(value)
    #
#

class VarEntry(QWidget):
    '''
    A simple widget to display a value with a label
    '''
    def __init__(self, parent, label, width=300, height=35):
        super().__init__(parent)
        self.setMaximumSize(width, height)
        self.value = 0.0
        self.staticLabel = QLabel(self)
        self.staticLabel.setGeometry(QtCore.QRect(0, 5, width/2, height-10))
        font = QFont()
        font.setPointSize(14)
        self.staticLabel.setFont(font)
        self.dynamicLabel = QLabel(self)
        self.dynamicLabel.setGeometry(QtCore.QRect(150, 5, width/2, height-10))
        self.dynamicLabel.setFont(font)
        self.setLabel(label)
        self.show()
    #

    def setLabel(self, lbl):
        '''
        Set the text of the label.

        Args:
            lbl (str) : The Label
        '''
        self.label = lbl
        self.staticLabel.setText(str(lbl))

    def setValue(self, val):
        '''
        Set the numeric value of the label.

        Args:
            val : The value
        '''
        self.value = val
        self.dynamicLabel.setText(str(self.value))
    #
#
