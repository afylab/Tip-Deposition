'''
A Modules for customized widgets
'''
import os
from os.path import join

from inspect import getmembers, isclass
from importlib.util import spec_from_file_location #, module_from_spec

from PyQt5.QtWidgets import QMainWindow, QListWidgetItem, QDoubleSpinBox

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
