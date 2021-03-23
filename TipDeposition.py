'''
Guides the user through the deposition process, running a recipe

Load the base with: "pyuic5 -x Base_Process_Window.ui -o Base_Process_Window.py"
'''
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidgetItem

from Interfaces.Base_Process_Window import Ui_mainWindow
from Interfaces.Base_Recipe_Dialog import Ui_RecipeDialog
from sequencer import Sequencer

import recipe
from Recipes.Testing_Calibration import Sequencer_Unit_Test

import sys
import os
from os.path import join
from queue import Queue
from inspect import getmembers, isclass
from importlib.util import spec_from_file_location #, module_from_spec

class RecipeDialog(Ui_RecipeDialog):
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
        self.loadButton.clicked.connect(parent.close)
        self.cancelButton.clicked.connect(parent.close)
    #

    def getRecipe(self):
        key = self.recipeListWidget.currentItem().text()
        return self.items[key]
    #

    def loadCallback(self):
        pass
    #
#

class Process_Window(Ui_mainWindow):
    '''
    The window used to execute a recipe. Adds functionality to the base class made in
    Qt Designer.
    '''

    def __init__(self):
        super(Process_Window, self).__init__()

        self.step_cnt = 0
        self.ins_text = ""
        self.stepQueue = Queue(1000)

        recipe = self.getRecipe()
        self.setupSequencer(recipe)
    #

    def getRecipe(self):
        '''
        Open a dialog box to load a recipe

        WHEN ADDED TO MENUBAR, make sure to confirm if you want to load a new one.
        '''
        recipeDialogBox = QtWidgets.QDialog()
        dialog = RecipeDialog()
        dialog.setupUi(recipeDialogBox)
        dialog.loadRecipes('Recipes')
        recipeDialogBox.exec()
        return dialog.getRecipe()
    #

    def setupSequencer(self, recipe):
        '''
        Setup the Sequencer thread
        '''
        # Setup the sequencer
        self.sequencer = Sequencer(recipe, None)

        # Connect Signals from Sequencer
        self.sequencer.instructSignal.connect(self.append_ins_text)
        self.sequencer.warnSignal.connect(self.append_ins_warning)
        self.sequencer.startupSignal.connect(self.setup_step)
        self.sequencer.autoStepSignal.connect(self.auto_step)
        self.sequencer.userStepSignal.connect(self.user_step)
        self.sequencer.finishedSignal.connect(self.finished)

        # Connect singals back to the sequencer
        self.sequencer.canAdvanceSignal.connect(self.sequencer.advance)
        self.sequencer.errorSignal.connect(self.sequencer.slient_error)

        self.sequencer.start()
    #

    def setupUi(self, mainWindow):
        super(Process_Window, self).setupUi(mainWindow)

        # Read only text
        self.insDisplay.setReadOnly(True)

        # Bind Buttons
        self.proceedButton.clicked.connect(self.startCallback)
        # self.proceedButton.setEnabled(True)
        self.abortButton.clicked.connect(self.abortCallback)

        self.stepLabel.setText(str(self.step_cnt))

        self.params = dict()

        self.set_status("standby")
    #

    def setup_step(self, step):
        '''
        Handels the inital setup of the recipe, getting the parameters
        '''
        self.add_user_inputs(step, self.coreParamsLayout, max=12, overflow=False)
    #


    def user_step(self, step):
        '''
        Display a step requiring user input. If step.get_params is false the user simply
        needs to click the proceed button after performing an action, otherwise
        the user is prompted for some input.

        Args:
            step : The Step object corresponding to the input
        '''
        self.step_cnt += 1
        self.stepLabel.setText(str(self.step_cnt))
        self.append_ins_text(step.instructions)
        self.proceedButton.setEnabled(True)
        if step.get_params:
            self.add_user_inputs(step, self.paramCol1Layout)
    #

    def auto_step(self, message=None):
        '''
        Display an automated step, i.e. one requiring no user input

        Args:
            message (string) : The message to display to the user, if None nothing is output.
        '''

        self.step_cnt += 1
        self.stepLabel.setText(str(self.step_cnt))
        if message is not None:
            self.append_ins_text(message)
    #

    '''
    Functions to Handel User Inputs
    '''

    def set_status(self, status):
        if status == "standby":
            self.statusLabel.setText("Standby")
            self.statusLabel.setStyleSheet("color:black")
        elif status == "active":
            self.statusLabel.setText("Active")
            self.statusLabel.setStyleSheet("color:green")
        elif status == "error":
            self.statusLabel.setText("Error")
            self.statusLabel.setStyleSheet("color:red")
        else:
            print("Warning Status not recognized in set_status, no change")
        self.status = status
    #

    def add_user_inputs(self, step, layout, max=8, overflow=True):
        '''
        Add widgets for user input

        Args:
            step : Step object, will load widgets specified in step.input_spec
            layout : The QFormLayout to add the widgets to
            max (int) : The Maximum number of rows
            overflow : If layout is full will attempt to put widgets here, if None will throw an exception
        '''
        for k in step.input_spec.keys():
            try:
                # If the box is full, move to next box if there is one
                if layout.rowCount() >= max:
                    if overflow:
                        for lay in [self.paramCol1Layout, self.paramCol2Layout, self.paramCol3Layout, "outofspace"]:
                            if lay == "outofspace":
                                raise Exception("Attempting to add parameter "+str(k)+" widgets to a full layout, maximum widgets reached")
                            if lay.rowCount() < max:
                                layout = lay
                                break
                    else:
                        raise Exception("Attempting to add parameter "+str(k)+" widgets to a full layout, cannot overflow")
                #

                # Make the widgets
                spec = step.input_spec[k]
                if spec[2] is not None: # Select between options
                    widget = QComboBox()
                    widget.addItems(spec[2])
                elif spec[1] is not None and spec[3]: # If it has limits, integer
                    widget = QSpinBox()
                    widget.setRange(int(spec[1][0]), int(spec[1][1]))
                    if spec[0] is not None:
                        widget.setValue(int(spec[0]))
                    else:
                        widget.setValue(0)
                elif spec[1] is not None and not spec[3]: # If it has limits, floating point value
                    widget = QDoubleSpinBox()
                    widget.setRange(spec[1][0], spec[1][1])
                    if spec[0] is not None:
                        widget.setValue(float(spec[0]))
                    else:
                        widget.setValue(0.0)
                else:
                    widget = QLineEdit()
                    if spec[0] is not None:
                        widget.setText(str(spec[0]))
                self.params[k] = widget
                layout.addRow(QLabel(k), self.params[k])
            except ValueError:
                self.sequencer.errorSignal.emit()
                self.append_ins_warning("Could not add parameter " + k + ". Probably improperly specified")
                self.append_ins_warning("Process may be unstable without parameter, abort recommended.")
            except:
                self.sequencer.errorSignal.emit()
                self.abortCallback()
                break
        #
        self.stepQueue.put(step)
    #

    def processQueuedStep(self):
        if not self.stepQueue.empty():
            step = self.stepQueue.get()
            for k in step.input_spec.keys():
                widget = self.params[k]
                if isinstance(widget, QComboBox): # if it is an option box
                    val = widget.currentText()
                elif isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox): # if it is a numerical entry
                    val = widget.value()
                else: # if it is a simple label
                    val = widget.text()
                step.input_param_values[k] = val
                widget.setEnabled(False)
        #
    #

    def finished(self):
        '''
        When the sequencer is finished it signals this slot.
        '''
        self.proceedButton.setEnabled(True)
        self.proceedButton.setText("Load")
        self.proceedButton.clicked.disconnect()
        self.proceedButton.clicked.connect(self.reload)
    #


    def reload(self):
        '''
        When a deposition ends allow the user to choose another recipe
        '''
        self.clear()
        recipe = self.getRecipe()
        self.setupSequencer(recipe)

        self.proceedButton.setEnabled(True)
        self.proceedButton.setText("Start")
        self.proceedButton.clicked.disconnect()
        self.proceedButton.clicked.connect(self.startCallback)
    #

    def clear(self):
        """
        Removes all entries from all FormLayouts and clear the instructions
        """
        for layout in [self.paramCol1Layout, self.paramCol2Layout, self.paramCol3Layout, self.coreParamsLayout]:
            while layout.rowCount() > 0:
                layout.removeRow(0)
        self.ins_text = ""
        self.insDisplay.setHtml(self.ins_text)
        self.step_cnt = 0
        self.stepLabel.setText(str(self.step_cnt))
    #

    '''
    TEXT PROCESSING
    '''

    def append_ins_text(self, txt):
        '''
        Add text to the instructions browser
        '''
        self.ins_text += txt+"<br>"
        self.insDisplay.setHtml(self.ins_text)
        self.insDisplay.moveCursor(QtGui.QTextCursor.End)
    #

    def append_ins_warning(self, txt):
        '''
        Add text to the instructions browser, highligted in red
        '''
        self.ins_text += "<font color=red>"+txt+"</font><br>"
        self.insDisplay.setHtml(self.ins_text)
        self.insDisplay.moveCursor(QtGui.QTextCursor.End)
    #

    '''
    CALLBACK FUNCTIONS
    '''
    def startCallback(self):
        self.processQueuedStep()
        self.proceedButton.setEnabled(False)
        self.proceedButton.setText("Proceed")
        self.proceedButton.clicked.disconnect()
        self.proceedButton.clicked.connect(self.proceedCallback)
        self.sequencer.canAdvanceSignal.emit()
    #

    def proceedCallback(self):
        '''
        Callback function for the proceed button
        '''
        self.proceedButton.setEnabled(False)
        self.step_cnt += 1
        self.stepLabel.setText(str(self.step_cnt))
        self.processQueuedStep()
        self.sequencer.canAdvanceSignal.emit()
    #


    def abortCallback(self):
        '''
        Callback function for the abort button
        '''
        self.proceedButton.setEnabled(False)
        self.append_ins_warning("Aborting Process...IMPLEMENT")
        #self.ins_text("Got Here "+str(self.step_cnt))
    #
#

# Start the Program
if __name__ == '__main__':
    # cxn = labrad.connect('localhost', password='pass')
    # rand = cxn.random_server

    app = QtWidgets.QApplication(sys.argv)
    mainWindow = QtWidgets.QMainWindow()
    ui = Process_Window()
    ui.setupUi(mainWindow)

    mainWindow.show()

    sys.exit(app.exec_())
