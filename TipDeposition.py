'''
Guides the user through the deposition process, running a recipe

Load the base with: "pyuic5 -x Base_Process_Window.ui -o Base_Process_Window.py"
'''
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QLineEdit, QComboBox, QSpinBox, QMessageBox, qApp
from PyQt5.QtWidgets import QMainWindow

from Interfaces.Base_Process_Window import Ui_mainWindow
from Status_Window import Status_Window
from Display_Window import Display_Window
from ManualControlWidget import EvaporatorWidget
from equipmenthandler import EquipmentHandler

from sequencer import Sequencer
from recipe import CalibrationRecipe

from customwidgets import BaseMainWindow, BaseStatusWidget, CustomSpinBox
from customwidgets import RecipeDialog, TipSelectionDialog

import sys
from traceback import format_exc
from queue import Queue
from os.path import join
from time import sleep # Be careful with this in a GUI

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
        self.paused = False
        self.setupUi(parent)

        self.equip = EquipmentHandler()
        self.equip.errorSignal.connect(self.equipErrorSlot)
        self.equip.serverNotFoundSignal.connect(self.serverErrorSlot)
        self.equip.timerSignal.connect(self.timerSlot)
        self.equip.start()

        # Setup the Status Window
        self.statusWindowWidget = BaseStatusWidget()
        self.statusWindow = Status_Window(self.statusWindowWidget, self, self.equip)

        # # Vacuum System Manual Controller
        self.ManualController = EvaporatorWidget(self)

        self.proceedButton.setEnabled(True)
        self.proceedButton.setText("Load")
        self.pauseButton.setEnabled(False)
        self.proceedButton.clicked.connect(self.loadRecipe)
        self.set_status('standby')

        self.default_display() # Load the pressure variable by default

        self.statusWindowWidget.show()
    #

    def default_display(self):
        '''
        By default display the pressure
        '''
        self.equip.commandSignal.emit('rvc_server', 'select_device', [])
        self.equip.trackSignal.emit('Pressure', 'rvc_server', 'get_pressure_mbar', 'mbar')
        sleep(0.25)
        self.equip.plotVariableSignal.emit('Pressure', True, True)

    def setupUi(self, mainWindow):
        super(Process_Window, self).setupUi(mainWindow)
        self.mainWindow = mainWindow
        self.mainWindow.setSubRef(self) # IMPORTANT, to make window closing work due to convoluted nature of Qt Designer classes
        self.mainWindow.setWindowTitle("Tip Process Window")
        # Read only text
        self.insDisplay.setReadOnly(True)

        # Bind Menu Items
        self.loadRecipeAction.triggered.connect(self.loadRecipe)
        self.calibrateAction.triggered.connect(self.loadCalibration)
        self.abortAction.triggered.connect(self.abortCallback)
        self.exitAction.triggered.connect(mainWindow.close)
        self.openTipAction.triggered.connect(self.openTipCallback)

        # Bind Buttons
        self.abortButton.clicked.connect(self.abortCallback)
        self.pauseButton.clicked.connect(self.pauseCallback)

        self.stepLabel.setText(str(self.step_cnt))
        self.timerLabel.setText("")

        self.params = dict()
        self.otherDisplays = []

        self.set_status("standby")

        self.mainWindow.setWindowIcon(QtGui.QIcon(join('Interfaces','images','squid_tip.png')))
    #

    def loadRecipe(self, calibration=False):
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
        if calibration:
            dialog.loadRecipes('Calibrations')
        else:
            dialog.loadRecipes('Recipes')
        # dialog.viewButton.clicked.connect(self.openTipCallback)
        recipeDialogBox.exec()
        recipe = dialog.getRecipe()

        if recipe is None:
            return

        loadsquid = dialog.getLoadState()

        try:
            self.clear()
            self.statusWindow.reset()
        except:
            pass

        # Clear any previous variables of plots
        self.statusWindow.reset()

        # Setup the sequencer
        self.sequencer = Sequencer(recipe, self.equip, loadsquid=loadsquid)

        # Connect Signals from Sequencer
        self.sequencer.instructSignal.connect(self.append_ins_text)
        self.sequencer.warnSignal.connect(self.append_ins_warning)
        self.sequencer.startupSignal.connect(self.setup_step)
        self.sequencer.autoStepSignal.connect(self.auto_step)
        self.sequencer.userStepSignal.connect(self.user_step)
        self.sequencer.finishedSignal.connect(self.finished)
        self.sequencer.activeSignal.connect(self.active_process)
        self.sequencer.updateHardware.connect(self.ManualController.refresh)

        # Connect signals back to the sequencer
        self.sequencer.canAdvanceSignal.connect(self.sequencer.advanceSlot)
        self.sequencer.errorSignal.connect(self.sequencer.slient_error)
        self.sequencer.abortSignal.connect(self.sequencer.abortSlot)
        self.sequencer.pauseSignal.connect(self.sequencer.pauseSlot)

        # Prepare the Start Button
        self.pauseButton.setEnabled(False)
        self.proceedButton.setEnabled(True)
        self.proceedButton.setText("Start")
        try:
            self.proceedButton.clicked.disconnect()
        except:
            pass
        self.proceedButton.clicked.connect(self.startCallback)

        self.sequencer.start()
    #

    def loadCalibration(self):
        self.loadRecipe(calibration=True)
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
    Status Functions
    '''
    def set_status(self, status):
        if status == "standby":
            self.statusLabel.setText("Standby")
            self.statusLabel.setStyleSheet("color:black")
        elif status == "active":
            self.statusLabel.setText("Active")
            self.statusLabel.setStyleSheet("color:green")
        elif status == "pause":
            self.statusLabel.setText("Paused")
            self.statusLabel.setStyleSheet("color:blue")
        elif status == "error":
            self.statusLabel.setText("Error")
            self.statusLabel.setStyleSheet("color:red")
        else:
            print("Warning Status not recognized in set_status, no change")
        self.status = status
    #

    def active_process(self):
        '''
        Wrapper to set status to active, called by activeSignal when the sequencer starts
        '''
        self.set_status('active')
    #

    def finished(self):
        '''
        When the sequencer is finished it signals this slot.
        '''
        self.proceedButton.setEnabled(True)
        self.proceedButton.setText("Load")
        self.pauseButton.setEnabled(False)
        try:
            self.proceedButton.clicked.disconnect()
        except:
            pass
        self.proceedButton.clicked.connect(self.loadRecipe)
        self.set_status('standby')
        self.openTipDisplay(False)
    #

    def timerSlot(self, s):
        self.timerLabel.setText(s)
    #

    '''
    Functions to Handel User Inputs
    '''

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
                    if spec[0] is not None and spec[0] != '':
                        widget.setValue(int(spec[0]))
                    else:
                        widget.setValue(0)
                elif spec[1] is not None and not spec[3]: # If it has limits, floating point value
                    widget = CustomSpinBox()
                    widget.setDecimals(7) # Make sure there is enough percision to accomodate a small value
                    widget.setRange(spec[1][0], spec[1][1])
                    if spec[0] is not None and spec[0] != '':
                        widget.setValue(float(spec[0]))
                    else:
                        widget.setValue(0.0)
                else:
                    widget = QLineEdit()
                    if spec[0] is not None and spec[0] != '':
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
                try:
                    if isinstance(widget, QComboBox): # if it is an option box
                        val = widget.currentText()
                    elif isinstance(widget, QSpinBox) or isinstance(widget, CustomSpinBox): # if it is a numerical entry
                        val = widget.value()
                    else: # if it is a simple label
                        val = widget.text()
                    step.input_param_values[k] = val
                    widget.setEnabled(False)
                except RuntimeError: # To prevent issues when reloading after an abort
                    pass
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
            True if Ok button was pressed False if cancel button
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
    Text Processing
    '''

    def append_ins_text(self, txt):
        '''
        Add text to the instructions browser
        '''
        self.ins_text += txt.replace('\n', '<br>')+"<br>"
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
    Callback Functions
    '''
    def startCallback(self):
        self.processQueuedStep()
        self.proceedButton.setEnabled(False)
        self.proceedButton.setText("Proceed")
        self.pauseButton.setEnabled(True)
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

    def pauseCallback(self):
        '''
        DEV Note: Need to call the equipment handler somewhere to make sure the equipment is in a good state?
        '''
        print("Maybe we need to pause the equipment handler too?")
        if self.paused: # un-pause
            self.set_status("active")
            self.pauseButton.setText("Pause")
            if self.proceed_was_enabled:
                self.proceedButton.setEnabled(True)
            self.sequencer.pauseSignal.emit(False)
            self.paused = False
        else:
            self.set_status("pause")
            self.pauseButton.setText("Unpause")
            if self.proceedButton.isEnabled():
                self.proceed_was_enabled = True
            else:
                self.proceed_was_enabled = False
            self.proceedButton.setEnabled(False)
            self.sequencer.pauseSignal.emit(True)
            self.paused = True
    #

    def abort(self, warn=False):
        '''
        Abort the current process
        '''
        if warn:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setText("Are you sure you want to abort the current process?")
            msgBox.setWindowTitle("Abort Process Warning")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ret = msgBox.exec()
        else:
            ret = QMessageBox.Ok
        if ret == QMessageBox.Ok:
            self.proceedButton.setEnabled(False)
            self.append_ins_warning("Aborting Process")
            if hasattr(self, 'sequencer'):
                self.sequencer.abortSignal.emit()
            self.set_status('error')
            self.pauseButton.setEnabled(False)
            while not self.stepQueue.empty(): # clear out any Queued steps
                self.stepQueue.get()
    #

    def abortCallback(self):
        '''
        Callback function for the abort button, with a warning to the user.
        '''
        self.abort(warn=True)
    #

    def close(self):
        '''
        I need to define this to make the Status window able to close it?
        '''
        self.mainWindow.close()
    #

    def closeEvent(self, event):
        if not hasattr(self, 'sequencer'): # In the event the window is closed before sequencer is initialized
            event.accept()
            qApp.quit()
            return
        if self.status == 'active' or self.sequencer.active:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setText("Process active! It is highly recommended you attempt to abort the process first. Are you sure you want to quit?")
            msgBox.setWindowTitle("Active Process Warning")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ret = msgBox.exec()
            if ret == QMessageBox.Ok:
                if hasattr(self.sequencer, 'logger'): # make sure the file saves correctly
                    del self.sequencer.logger
                if hasattr(self, 'equip'): # Clean up the equipment monitor explicitly to makes sure it closes out correctly.
                    del self.equip
                qApp.quit()
            else:
                event.ignore()
        else:
            event.accept()
            qApp.quit()
    #

    def equipErrorSlot(self):
        self.append_ins_warning("Equipment Error, see errorlog for details.")
        if hasattr(self, 'sequencer'):
            self.sequencer.abortSignal.emit()
            self.sequencer.record_error()
        else:
            print(format_exc())
        self.set_status('error')
    #

    def serverErrorSlot(self, txt):
        self.append_ins_warning("LabRAD Server Error: " + txt)
        self.append_ins_warning("Fix the servers and restart the program.")
        self.set_status('error')
        self.proceedButton.setEnabled(False)
    #

    def openTipCallback(self):
        '''
        Open and display the data for a previous tip, for reference
        '''
        self.openTipDisplay(True)
    #

    def openTipDisplay(self, fromfile):
        '''
        Opens the data for a Tip Deposition, either opened at the end of a deposition or
        loading a previous one from file
        '''
        if fromfile:
            tipDialogBox = QtWidgets.QDialog()
            dialog = TipSelectionDialog()
            dialog.setupUi(tipDialogBox)
            tipDialogBox.exec()
            version, squidname = dialog.getTip()
            if version is None:
                return
            autosave = False
        else:
            if hasattr(self, 'sequencer'):
                if issubclass(type(self.sequencer.recipe), CalibrationRecipe):
                    return
                version = self.sequencer.get_recipe_name()
                squidname = self.sequencer.get_squid_name()
            else:
                print("Error no loaded recipe")
                return
                # version = ""
                # squidname = ""
            autosave = True
        try:
            base = QMainWindow()
            display = Display_Window(base, version, squidname, autosave=autosave)
            self.otherDisplays.append(display)
        except:
            pass
            #self.sequencer.errorSignal.emit()
    #
#

# Start the Program
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = BaseMainWindow()
    ui = Process_Window(mainWindow)

    mainWindow.show()
    sys.exit(app.exec_())
