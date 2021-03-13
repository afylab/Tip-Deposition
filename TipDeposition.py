'''
Guides the user through the deposition process, running a recipe

Load the base with: "pyuic5 -x Base_Process_Window.ui -o Base_Process_Window.py"
'''
from PyQt5 import QtGui, QtWidgets

from Interfaces.Base_Process_Window import Ui_mainWindow as Process_Window_Base
from sequencer import Sequencer

from Recipes.Testing_Calibration import Sequencer_Unit_Test

import sys

class Process_Window(Process_Window_Base):
    '''
    The window used to execute a recipe. Adds functionality to the base class made in
    Qt Designer.
    '''

    def __init__(self, recipe):
        super(Process_Window, self).__init__()

        self.step_cnt = 0
        self.ins_text = ""

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


        self.sequencer.start()


    #

    def setupUi(self, mainWindow):
        super(Process_Window, self).setupUi(mainWindow)

        # Read only text
        self.insDisplay.setReadOnly(True)

        # Bind Buttons
        self.proceedButton.clicked.connect(self.proceedCallback)
        # self.proceedButton.setEnabled(True)
        self.abortButton.clicked.connect(self.abortCallback)

        self.stepLabel.setText(str(self.step_cnt))
    #

    def setup_step(self, step):
        '''
        Handels the inital setup of the recipe
        '''
        pass
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
    def proceedCallback(self):
        '''
        Callback function for the proceed button
        '''
        self.append_ins_text("Got Here "+str(self.step_cnt))
        self.step_cnt += 1
        self.stepLabel.setText(str(self.step_cnt))
        self.sequencer.canAdvanceSignal.emit()
    #

    def abortCallback(self):
        '''
        Callback function for the abort button
        '''
        self.append_ins_warning("Aborting Process...")
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
