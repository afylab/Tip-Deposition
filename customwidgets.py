'''
A Modules for customized widgets that enable the actual displays
'''
import os
from os.path import join

from inspect import getmembers, isclass
from importlib.util import spec_from_file_location #, module_from_spec

from PyQt5 import QtCore
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QLabel, QMainWindow, QListWidgetItem, QDoubleSpinBox, QWidget
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem

import pyqtgraph as pg

from Interfaces.Base_Recipe_Dialog import Ui_RecipeDialog
from Interfaces.Base_Tip_Selection_Dialog import Ui_TipSelectionDialog
import recipe

class CustomViewBox(pg.ViewBox):
    '''
    Viewbox that allows for selecting range, taken from PyQtGraphs documented examples
    '''
    def __init__(self, *args, **kwds):
        kwds['enableMenu'] = False
        pg.ViewBox.__init__(self, *args, **kwds)
        self.setMouseMode(self.RectMode)
    #

    ## reimplement right-click to zoom out
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.autoRange()
    #

    ## reimplement mouseDragEvent to disable continuous axis zoom
    def mouseDragEvent(self, ev, axis=None):
        if axis is not None and ev.button() == QtCore.Qt.RightButton:
            ev.ignore()
        else:
            pg.ViewBox.mouseDragEvent(self, ev, axis=axis)
    #
#

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

class TipSelectionDialog(Ui_TipSelectionDialog):
    '''
    A Dialog box to select a tip to load data from
    '''
    def setupUi(self, parent):
        super().setupUi(parent)
        self.cancelled = True
        self.parent = parent
        self.loadButton.clicked.connect(self.loadCallback)
        self.cancelButton.clicked.connect(self.cancelCallback)

        self.parent.setWindowIcon(QIcon(join('Interfaces','images','squid_tip.png')))
        self.loadTips()
    #

    def loadTips(self, directory='database'):
        self.treeWidget.setHeaderLabels(["Select a Deposition"])
        for file in os.listdir(directory):
            if file.endswith(".csv"):
                name = file.replace('_params.csv','')
                name = name.replace('_v', ' v')
                name = name.replace('_', ' ')
                name = name.replace('-', '.')
                recipeItem = QTreeWidgetItem([name])

                with open(join(directory, file), 'r') as reader:
                    lines = reader.readlines()
                    for i in range(1,len(lines)):
                        ln = lines[i].split(',')
                        tip = QTreeWidgetItem([ln[1]])
                        recipeItem.addChild(tip)
                self.treeWidget.addTopLevelItem(recipeItem)
        #
    #

    def getTip(self):
        '''
        Return the recipe class, returns None if cancelled.
        '''
        if self.cancelled:
            return None, None
        else:
            current = self.treeWidget.currentItem()
            parent = current.parent()
            if parent is None: # If you just selected a recipe, don't load
                return None, None
            else:
                recipe = parent.text(0)
                recipe = recipe.replace(' v', '_v')
                recipe = recipe.replace(' ', '_')
                recipe = recipe.replace('.', '-')
                return recipe, current.text(0)
    #

    def loadCallback(self):
        self.cancelled = False
        self.parent.close()
    #

    def cancelCallback(self):
        self.cancelled = True
        self.parent.close()
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
    def __init__(self, parent, label, units="", width=300, height=35, labelwidth=150, valuewidth=100, unitswidth=50):
        super().__init__(parent)
        self.setMaximumSize(labelwidth+valuewidth+unitswidth, height)
        self.value = 0.0

        font = QFont()
        font.setPointSize(14)

        self.staticLabel = QLabel(self)
        self.staticLabel.setGeometry(QtCore.QRect(0, 5, labelwidth, height-10))
        self.staticLabel.setFont(font)
        #self.staticLabel.setStyleSheet("background-color: green")

        self.dynamicLabel = QLabel(self)
        self.dynamicLabel.setGeometry(QtCore.QRect(labelwidth, 5, valuewidth, height-10))
        self.dynamicLabel.setFont(font)
        self.setLabel(label)
        #self.dynamicLabel.setStyleSheet("background-color: blue")

        self.unitsLabel = QLabel(self)
        self.unitsLabel.setGeometry(QtCore.QRect(labelwidth+valuewidth, 5, unitswidth, height-10))
        self.unitsLabel.setFont(font)
        self.setUnits(units)
        #self.unitsLabel.setStyleSheet("background-color: yellow")
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
            val (float) : The value
        '''
        self.value = val
        self.dynamicLabel.setText(str(self.value))
    #

    def setUnits(self, unit):
        '''
        Set the units of the value

        Args:
            unit (str) : The unit
        '''
        self.units = unit
        self.unitsLabel.setText(str(self.units))
    #
#
