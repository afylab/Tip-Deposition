'''
Primary module for tip deposition, contains the sequencer at the heart of the program
which handles the backend of executing a recipe.

'''
from traceback import format_exc
from time import sleep
from os.path import exists

from recipe_logging import recipe_logger
from recipe import Step
from exceptions import ProcessInterruptionError, LogFileFormatError

from PyQt5.QtCore import QThread, pyqtSignal

# Use QThread instead of native python threading to avoid issues and take advantage of Qt Signals.Slots features
class Sequencer(QThread):
    '''
    Backend of the tip deposition that translates a tip deposition recipe into a sequence
    of hardware commands, checking user input
    '''
    # Need to define Signals and Slots as class variables due to QT BS
    instructSignal = pyqtSignal(str)
    warnSignal = pyqtSignal(str)
    autoStepSignal = pyqtSignal(str)
    userStepSignal = pyqtSignal(Step)
    startupSignal = pyqtSignal(Step)
    canAdvanceSignal = pyqtSignal()
    activeSignal = pyqtSignal()
    errorSignal = pyqtSignal()
    finishedSignal = pyqtSignal()
    abortSignal = pyqtSignal()
    pauseSignal = pyqtSignal(bool)
    updateHardware = pyqtSignal()

    def __init__(self, recipe, equip, loadsquid=None):
        '''
        Setup the recipe.

        Args:
            recipe : The recipe object to load
            servers : A dictionary ordered with 'equipment-name':labRAD-Server-Reference. The
                key will be used as a generic key to lookup the hardware from Sequencer.servers[key]
            gui : the process window that controlls the sequence moving foreward
        '''
        self.active = False # Parameter is active the process is running, will not load a new process
        self.abort = False # Calling self.abortSlot will set false and stop current process
        self.pause = False
        self.equip = equip
        self.loadsquid = loadsquid

        super().__init__()
        self.recipe = recipe(equip, self.updateHardware)
    #

    '''
    Main loop of the sequencer, handles the basic process of the running a recipe.
    Basic process is to run recipe.proceed generator and context switch from the recipe to
    the sequencer, with the recipe yielding feedback which the sequencer processes.

    The sequencer handels the queueing of steps and control flow, and also feedsback to the
    GUI to get user feedback and user steps.
    '''
    def run(self):
        # Confirm Start on UI
        self.instructSignal.emit("Recipe \"" + self.recipe.name + "\" v" + self.recipe.version + " Loaded")

        self.logger = recipe_logger(self.recipe)

        try:
            loaded = self.logger.load(self.loadsquid)
        except LogFileFormatError:
            self.warnSignal.emit("Tried to load improperly formatted log file, process canceled.")
            self.record_error()
            self.active = False
            return

        try: # Setup the process
            startupstep = self.recipe.setup(loaded)
            self.startupSignal.emit(startupstep)
            self.wait_for_gui() # Wait for the user to enter the starting parameters and press start
            startupstep.processed = True # Flag the step as processed
            self.logger.startlog(startupstep) # Start logging, will not start writing to the file untill this is called
            self.squidname = self.logger.squidname
            self.recipe._process_startup(startupstep) # laod the startup paramters into the recipe
        except ProcessInterruptionError:
            self.warnSignal.emit("Process Aborted before it began. Reload process to continue.")
            return
        except:
            self.warnSignal.emit("Error starting up, process canceled.")
            self.record_error()
            self.active = False
            return
        #

        self.active = True
        self.activeSignal.emit()
        try: # Begin the main loop
            steps = self.recipe.proceed() # Generator for controlling steps
            for step in steps: # Proceed through steps, process feedback as it arises.
                if self.pause: # If paused, wait
                    while self.pause:
                        sleep(0.01)
                if not self.active:
                    raise ProcessInterruptionError
                if step.user_input: # If user action is needed, ask for it and wait
                    self.userStepSignal.emit(step)
                    self.wait_for_gui()
                else:
                    self.autoStepSignal.emit(step.instructions)
                #
                step.processed = True # Flag the step as processed
                self.logger.log(step) # Log information
            self.instructSignal.emit("Process ended sucessfully.")
        except ProcessInterruptionError:
            self.warnSignal.emit("Attempting to return equipment to standby.")
        except:
            self.warnSignal.emit("Unexpected Error, process canceled. Attempting to shutdown equipment safely.")
            self.record_error()

        try: # Safely shutdown the thread, put all equipment on standby
            self.recipe.shutdown()
        except:
            self.warnSignal.emit("Error encountered while attempting to shutdown equipment safely. Equipment may be unstable, full shutdown of servers recommended.")
        self.finishedSignal.emit()
        del self.logger
        self.active = False
    #

    def wait_for_gui(self):
        self.advance = False
        self.equip.timerSignal.emit("Waiting for input")
        while not self.advance:
            sleep(0.01)
            if self.abort:
                raise ProcessInterruptionError
    #

    def abortSlot(self):
        '''
        Slot for signal (send from GUI thread using abortSignal) that the sequencer can stop waiiting for user input
        '''
        self.active = False
        self.abort = True
        self.recipe.abort = True
    #

    def pauseSlot(self, val):
        '''
        Slot for the signal to Pause/Unpause the process.

        Args:
            val (bool) : The operation to perform, if True pause the process, if False unpause.
        '''
        if val:
            self.pause = True
            self.recipe.pause = True
        else:
            self.pause = False
            self.recipe.pause = False
    #

    def advanceSlot(self):
        '''
        Slot for signal (send from GUI thread using canAdvanceSignal) to abort the current process.
        '''
        self.advance = True
    #

    def slient_error(self):
        '''
        Slot for recording a silent error to the errorlog, called by the GUI using silentErrorSignal
        '''
        self.record_error(display=False)
    #

    def record_error(self, override=None, flname='errorlog.txt', display=True):
        if override is None:
            err = format_exc()
        else:
            err = override
        print(err) # Print it to the terminal if there is one running
        if exists(flname):
            file_mode = 'a' # append if already exists
        else:
            file_mode = 'w' # create a new file if not
        with open(flname, file_mode) as errorlog:
            errorlog.write('\n'+err+'\n')
            errorlog.flush()
        if display:
            self.warnSignal.emit("See " + flname + " for full details")
    #

    def get_recipe_name(self):
        try:
            return self.recipe.get_name()
        except:
            print("Error: no Recipe name")
            return ""
    #

    def get_squid_name(self):
        try:
            return self.squidname
        except:
            print("Error: no SQUID name")
            return ""
    #
#
