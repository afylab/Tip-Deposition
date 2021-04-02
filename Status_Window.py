'''
Window to display the current status of the equipment
'''

from Interfaces.Base_Status_Window import Ui_StatusWindow
from customwidgets import VarEntry

#from PyQt5.QtCore import Qt

class Status_Window(Ui_StatusWindow):
    '''
    The window to display information about the system.

    Args:
        widget : the QWidget that is the base for this window
        gui : The main GUI this window adds onto, usually the process main window.
        equipment : The Equipment handler object
    '''
    def __init__(self, widget, gui, equipment):
        super(Status_Window, self).__init__()

        # Connect the equipment handler
        self.equip = equipment
        self.equip.guiTrackedVarSignal.connect(self.trackedVariableSlot)
        self.equip.updateTrackedVarSignal.connect(self.updateTrackedVarSlot)

        self.widget = widget
        self.gui = gui
        self.setupUi(self.widget)

        self.trackedVarsWidgets = dict()
        self.trackedrow = 0

        self.floatpercision = 3
    #

    def setupUi(self, widget):
        super(Status_Window, self).setupUi(widget)
        widget.setWindowTitle("Tip Status Window")
        widget.setGUIRef(self.gui) # IMPORTANT, to make window closing work due to convoluted nature of Qt Designer classes
        # Setup additional stuff here
    #

    def trackedVariableSlot(self, name, create):
        '''
        Add or remove a tracked variable to the GUI.

        Args:
            name (str) : The name of the tracked varaible, will display.
            create (bool) : If True will add it, if False will remove.
        '''
        if create:
            widget = VarEntry(self.variablesFrame, name)
            widget.move(0, 35*self.trackedrow)
            self.trackedVarsWidgets[name] = widget
            self.trackedrow += 1
        else:
            print("NEED TO IMPLEMENT REMOVAL")
    #

    def updateTrackedVarSlot(self, name):
        '''
        Update the value of a tracked variable. If a variable does not exist, command is
        ignored. Value of varaible is taken from the EquipmentHandler.info[name]

        Args:
            name (str) : The name of the tracked varaible to update.
        '''
        if name in self.trackedVarsWidgets:
            val = self.equip.info[name]
        if isinstance(val, float):
            s = str(round(val, self.floatpercision))
        else:
            s = str(val)
        self.trackedVarsWidgets[name].setValue(s)
    #
#
