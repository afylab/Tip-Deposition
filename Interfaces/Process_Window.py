'''
Guides the user through the deposition process, running a recipe

Load the base with: "pyuic5 -x Base_Process_Window.ui -o Base_Process_Window.py"
'''
from PyQt5 import QtGui
from Interfaces.Base_Process_Window import Ui_mainWindow as Process_Window_Base

class Process_Window(Process_Window_Base):
    '''
    The window used to execute a recipe. Adds functionality to the base class made in
    Qt Designer.
    '''
    def __init__(self):
        super(Process_Window, self).__init__()

        self.step_cnt = 0
        self.ins_text = ""
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

    '''
    Add text to the instructions browser
    '''
    def append_ins_text(self, txt):
        self.ins_text += txt+"<br>"
        self.insDisplay.setHtml(self.ins_text)
        self.insDisplay.moveCursor(QtGui.QTextCursor.End)
    #

    '''
    Add text to the instructions browser, highligted in red
    '''
    def append_ins_warning(self, txt):
        self.ins_text += "<font color=red>"+txt+"</font><br>"
        self.insDisplay.setHtml(self.ins_text)
        self.insDisplay.moveCursor(QtGui.QTextCursor.End)
    #

    '''
    Callback function for the proceed button
    '''
    def proceedCallback(self):
        self.append_ins_text("Got Here "+str(self.step_cnt))
        self.step_cnt += 1
        self.stepLabel.setText(str(self.step_cnt))
    #

    '''
    Callback function for the abort button
    '''
    def abortCallback(self):
        self.append_ins_warning("Warning "+str(self.step_cnt))
        self.step_cnt += 1
        #self.ins_text("Got Here "+str(self.step_cnt))
    #
#
