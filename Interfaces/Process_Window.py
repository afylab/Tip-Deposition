'''
Guides the user through the deposition process, running a recipe
'''

from Interfaces.Base_Process_Window import Ui_mainWindow as Process_Window_Base

class Process_Window(Process_Window_Base):
    '''
    The window used to execute a recipe. Adds functionality to the base class made in
    Qt Designer.
    '''
    def __init__(self):
        super(Process_Window, self).__init__()
    #
#
