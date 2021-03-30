'''
Window to display the current status of the equipment
'''

from Interfaces.Base_Status_Window import Ui_StatusWindow

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
        self.equip = equipment
        self.widget = widget
        self.gui = gui
        self.setupUi(self.widget)
    #

    def setupUi(self, widget):
        super(Status_Window, self).setupUi(widget)
        widget.setWindowTitle("Tip Status Window")
        widget.setGUIRef(self.gui) # IMPORTANT, to make window closing work due to convoluted nature of Qt Designer classes
        # Setup additional stuff here
    #
#
