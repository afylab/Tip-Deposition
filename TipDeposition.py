'''
Guides the user through the deposition process, running a recipe

Load the base with: "pyuic5 -x Base_Process_Window.ui -o Base_Process_Window.py"
'''
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidgetItem, QMessageBox

from Interfaces.Base_Process_Window import Ui_mainWindow
from Interfaces.Base_Recipe_Dialog import Ui_RecipeDialog
from sequencer import Sequencer

import recipe

import sys
import os
from os.path import join
from queue import Queue
from inspect import getmembers, isclass
from importlib.util import spec_from_file_location #, module_from_spec

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
        self.cancelled = False
        self.parent = parent
        self.loadButton.clicked.connect(self.parent.close)
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

class Process_Window(Ui_mainWindow):
    '''
    The window used to execute a recipe. Adds functionality to the base class made in
    Qt Designer.
    '''

    def __init__(self, parent):
        super(Process_Window, self).__init__()

        self.step_cnt = 0
        self.ins_text = ""
        self.stepQueue = Queue(1000)

        self.setupUi(parent)
        self.loadRecipe()
    #

    def setupUi(self, mainWindow):
        super(Process_Window, self).setupUi(mainWindow)

        # Read only text
        self.insDisplay.setReadOnly(True)

        # Bind Menu Items
        self.loadRecipeAction.triggered.connect(self.loadRecipe)
        self.abortAction.triggered.connect(self.abortCallback)
        self.exitAction.triggered.connect(mainWindow.close)

        # Bind Buttons
        self.abortButton.clicked.connect(self.abortCallback)

        self.stepLabel.setText(str(self.step_cnt))

        self.params = dict()

        self.set_status("standby")
    #

    def loadRecipe(self):
        '''
        Open a dialog box to load a recipe and then setup the Sequencer thread
        '''
        try: # Make sure there isn't a process running
            if self.sequencer.active:
                self.append_ins_warning("Cannot load a new recipe while there is an active process. Abort process to load a new one.")
                return
        except:
            pass

        recipeDialogBox = QtWidgets.QDialog()
        dialog = RecipeDialog()
        dialog.setupUi(recipeDialogBox)
        dialog.loadRecipes('Recipes')
        recipeDialogBox.exec()
        recipe = dialog.getRecipe()

        if recipe is None:
            return

        loadsquid = dialog.getLoadState()

        try:
            self.clear()
        except:
            pass

        # Setup the sequencer
        self.sequencer = Sequencer(recipe, None, loadsquid=loadsquid)

        # Connect Signals from Sequencer
        self.sequencer.instructSignal.connect(self.append_ins_text)
        self.sequencer.warnSignal.connect(self.append_ins_warning)
        self.sequencer.startupSignal.connect(self.setup_step)
        self.sequencer.autoStepSignal.connect(self.auto_step)
        self.sequencer.userStepSignal.connect(self.user_step)
        self.sequencer.finishedSignal.connect(self.finished)

        # Connect signals back to the sequencer
        self.sequencer.canAdvanceSignal.connect(self.sequencer.advanceSlot)
        self.sequencer.errorSignal.connect(self.sequencer.slient_error)
        self.sequencer.abortSignal.connect(self.sequencer.abortSlot)

        # Prepare the Start Button
        self.proceedButton.setEnabled(True)
        self.proceedButton.setText("Start")
        try:
            self.proceedButton.clicked.disconnect()
        except:
            pass
        self.proceedButton.clicked.connect(self.startCallback)

        self.sequencer.start()
    #

    def setup_step(self, step):
        '''
        Handels the inital setup of the recipe, getting the parameters
        '''
        self.add_user_inputs(step, self.coreParamsLayout, max=12, overflow=False)
    #


    def user_step(self, step):
        '''
        Display a step requiring user input. If step.params_needed is false the user simply
        needs to click the proceed button after performing an action, otherwise
        the user is prompted for some input.

        Args:
            step : The Step object corresponding to the input
        '''
        self.step_cnt += 1
        self.stepLabel.setText(str(self.step_cnt))
        self.append_ins_text(step.instructions)
        self.proceedButton.setEnabled(True)
        if step.params_needed:
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
        self.proceedButton.clicked.connect(self.loadRecipe)
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

    def warn(self, warning):
        '''
        Opens a dialog to print a warning to the user

        Args:
            warning (str) : The warning to display

        Returns:
            True if Ok button was press,ed False if cancel button
        '''
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setText(str(warning))
        msgBox.setWindowTitle("Warning")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        ret = msgBox.exec()
        if ret == QMessageBox.Ok:
            return True
        else:
            return False
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
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setText("Are you sure you want to abort the current process?")
        msgBox.setWindowTitle("Abort Process Warning")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        ret = msgBox.exec()
        if ret == QMessageBox.Ok:
            self.proceedButton.setEnabled(False)
            self.append_ins_warning("Aborting Process")
            self.sequencer.abortSignal.emit()
    #
#

# Start the Program
if __name__ == '__main__':
    # cxn = labrad.connect('localhost', password='pass')
    # rand = cxn.random_server

    app = QtWidgets.QApplication(sys.argv)
    mainWindow = QtWidgets.QMainWindow()
    ui = Process_Window(mainWindow)

    mainWindow.show()
    sys.exit(app.exec_())
