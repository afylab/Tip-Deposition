'''
Primary module for tip deposition, contains the sequencer at the heart of the program
which handles the backend of executing a recipe.

'''

import threading
#import labrad

from data_logging import recipe_logger

from PyQt5 import QtWidgets

from Interfaces.Process_Window import Process_Window

from Recipes.Testing_Calibration import Sequencer_Unit_Test

import sys

class Sequencer(threading.Thread):
    '''
    Backend of the tip deposition that translates a tip deposition recipe into a sequence
    of hardware commands, checking user input
    '''
    def __init__(self, recipe, servers, gui):
        '''
        Setup the recipe.

        Args:
            recipe : The recipe object to load
            servers : A dictionary ordered with 'equipment-name':labRAD-Server-Reference. The
                key will be used as a generic key to lookup the hardware from Sequencer.servers[key]
            gui : the process window that controlls the sequence moving foreward
        '''
        super(Sequencer, self).__init__()

        self.active = False # Parameter is active when a tip is being deposited

        self.recipe = recipe
        self.servers = servers
        self.gui = gui

        # Check that the recipe has all the equipment it needs
        if not self.recipe.equipment_check(self.servers):
            # Manage equipment
            pass

        # Initlize the process window
        # Probably needs to be outside the thread
        # self.gui = ProcessWindow


        # Setup the equipment
    #

    '''
    Main loop of the sequencer, handles the basic process of the running a recipe.
    Basic process is to run recipe.proceed generator and context switch from the recipe to
    the sequencer, with the recipe yielding feedback which the sequencer processes.

    The sequencer handels the queueing of steps and control flow, and also feedsback to the
    GUI to get user feedback and user steps.
    '''
    def run(self):
        # Setup, load old control parameters into the recipe and UI and allow the user to update
        self.recipe.setup()

        # Validate, make sure the parameters are all in range and no obvious problems are going to occur

        # Confirm Start on UI
        self.gui.append_ins_text("Recipe \"" + self.recipe.name + "\" v" + self.recipe.version + " Loaded")

        logger = recipe_logger(self.recipe)

        # Begin the main loop
        steps = self.recipe.proceed() # Generator for controlling steps
        try:
            for step in steps: # Proceed through steps, process feedback as it arises.

                # If user action is needed, ask for it and wait
                if step.user_input:
                    pass

                # Log information
                self.logger.log(step)

            #
        except Exception as ex:
            # Handle specific errors and attempt to recover
            pass

        # Safely shutdown the thread, put all equipment on standby
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

    recipe = Sequencer_Unit_Test()
    sequence = Sequencer(recipe, None, ui)

    sequence.start()
    mainWindow.show()
    #sequence.stop() # Add shutdown procedure for anything in process

    sys.exit(app.exec_())
