'''
Guides the user through the deposition process, running a recipe

Load the base with: "pyuic5 -x Base_Process_Window.ui -o Base_Process_Window.py"
'''
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox

from Interfaces.Base_Process_Window import Ui_mainWindow as Process_Window_Base
from sequencer import Sequencer

from Recipes.Testing_Calibration import Sequencer_Unit_Test

import sys
from queue import Queue

class Process_Window(Process_Window_Base):
    '''
    The window used to execute a recipe. Adds functionality to the base class made in
    Qt Designer.
    '''

    def __init__(self, recipe):
        super(Process_Window, self).__init__()

        self.step_cnt = 0
        self.ins_text = ""
        self.stepQueue = Queue(1000)

        # More advanced loading of recipe

        # Setup the sequencer
        self.sequencer = Sequencer(recipe, None)

        # Connect Signals from Sequencer
        self.sequencer.instructSignal.connect(self.append_ins_text)
        self.sequencer.warnSignal.connect(self.append_ins_warning)
        self.sequencer.startupSignal.connect(self.setup_step)
        self.sequencer.autoStepSignal.connect(self.auto_step)
        self.sequencer.userStepSignal.connect(self.user_step)

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
        self.add_user_inputs(step, self.coreParamsLayout)
    #


    def user_step(self, step):
        '''
        Display a step requiring user input. If inputspec is None the user simply
        needs to click the proceed button after performing an action, otherwise
        the user is prompted for some input.

        Args:
            step : The Step object corresponding to the input
        '''
        self.step_cnt += 1
        self.stepLabel.setText(str(self.step_cnt))
        self.append_ins_text(step.instructions)

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

    def add_user_inputs(self, step, layout):
        for k in step.input_spec.keys():
            try:
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
        self.proceedButton.setText("Proceed")
        self.proceedButton.clicked.disconnect()
        self.proceedButton.clicked.connect(self.proceedCallback)
        self.sequencer.canAdvanceSignal.emit()
    #

    def proceedCallback(self):
        '''
        Callback function for the proceed button
        '''
        self.append_ins_text("Got Here "+str(self.step_cnt))
        self.step_cnt += 1
        self.stepLabel.setText(str(self.step_cnt))

        self.processQueuedStep()
        self.sequencer.canAdvanceSignal.emit()
    #

    def abortCallback(self):
        '''
        Callback function for the abort button
        '''
        self.append_ins_warning("Aborting Process...IMPLEMENT")
        #self.ins_text("Got Here "+str(self.step_cnt))
    #
#

# Start the Program
if __name__ == '__main__':
    # cxn = labrad.connect('localhost', password='pass')
    # rand = cxn.random_server

    recipe = Sequencer_Unit_Test

    app = QtWidgets.QApplication(sys.argv)
    mainWindow = QtWidgets.QMainWindow()
    ui = Process_Window(recipe)
    ui.setupUi(mainWindow)

    mainWindow.show()

    sys.exit(app.exec_())
