'''
A module to define equipment handling. The main goal being to manage signals to and from
the LabRAD servers in an intelligent and thread safe manner without blocking the sequencer
thread.
'''
import labrad
from PyQt5.QtCore import QThread, pyqtSignal
# from exceptions import LabRADError

class EquipmentHandler(QThread):
    '''
    Handels communication with the labRAD servers that run the equipment in an intelligent
    and thread safe manner without blocking the sequencer of GUI threads. Operates largly
    independant of whatever is happening with the recipe
    '''
    # Signals for GUI
    errorSignal = pyqtSignal() # Indicates an equipment error that is fatal to the process

    # Primary Signals
    commandSignal = pyqtSignal(str, str, list)
    trackSignal = pyqtSignal(str, str, str)
    recordSignal = pyqtSignal(str)
    stopRecordSignal = pyqtSignal(str)
    verifySignal = pyqtSignal(list)
    feedbackPIDSignal = pyqtSignal(str, str, list, list)

    def __init__(self, servers):
        '''
        Initialize the equipment handler
        '''
        super().__init__()

        self.active = False

        self.cxn = labrad.connect('localhost', password='pass')

        self.servers = dict()
        for name in servers:
            if hasattr(self.cxn, name):
                self.servers[name] = getattr(self.cxn, name)
            else:
                print("Warning server " + name + " not found.")
            #
        #

        self.trackedVars = dict() # Dictionary of the tracked varaibles, same keys as self.info
        self.info = dict() # Dictionary of the values of the tracked variables

        # Connect all the signals and slots
        # errorSignal is connected to main interface
        self.commandSignal.connect(self.commandSlot)
        self.recordSignal.connect(self.recordVariableSlot)
        self.stopRecordSignal.connect(self.stopRecordSlot)
        self.verifySignal.connect(self.verifySlot)
        self.feedbackPIDSignal.connect(self.feedbackPIDSlot)
    #

    def run(self):
        '''
        The main loop of the equipment thread. Updates tracked variables and feedback loops
        and logs data as appropriate. Handels errors if any come up.
        '''
        self.active = True

        while self.active:
            for k in self.trackedVars.keys(): # Update the tracked varaibles
                self.info[k] = float(self.trackedVars[k])
                # Send updates to GUI? Or can it read on it's own?

            # Update any feedback loops
            # Record any data that needs to be recorded.
            # Send other signals to GUI? Status of the valves?
    #

    def commandSlot(self, server, command, args_kwargs):
        '''
        Sends a simple command to a labRAD server. No return values

        Args:
            server (str) : The name of the server.
            command (str) : The name of the command, accessible by getattr
            args_kwargs (list) : A list containing the arguments of the command and the
                keyword arguments, which will be used to call the server using
                server.command(*args, **kwargs). This must be a list with [args, kwargs],
                if either is None that one will not be passed, if it is not a two item list
                with emit an errorSignal.
        '''
        pass
    #

    def trackSlot(self, name, server, variable):
        '''
        Creates a tracked variable, after creation the tracked variable is continuously
        updated and the value is accessable at self.info[name]. After creating a tracked
        variable it is wise to wait a short amount of time for the handler to catch up
        before attempting to access it. Tracked variables will be displayed on the interface.

        If a variable already exists this command is ignored. If a varaible does not exist
        on a server it generates an errorSignal.

        Args:
            name (str) : The name of the variable, which will function as the key to access it.
            server (str) : The name of the LabRAD server to get the value from
            variable (str): The varaiable (in the namespace of that server) to access to get
            the value, i.e. server.variable accessible with getattr.
        '''
        pass
    #

    def recordVariableSlot(self, name):
        '''
        Record a tracked variable to datavault

        Args:
            name (str) : The name of the tracked varirable, i.e. self.info[name]

        Raises:
            UntrackedVaraibleError : When the varaible is not being tracked.
        DEV NOTE: Should we raise or should emit an errorSignal?
        '''
        pass
    #

    def stopRecordSlot(self, name):
        '''
        Stop recording a tracked variable. If the variable is not currently being recorded
        this is ignored.

        Args:
            name (str) : The name of the tracked varirable, i.e. self.info[name]

        Raises:
            UntrackedVaraibleError : When the varaible is not being tracked.
        DEV NOTE: Should we raise or should emit an errorSignal?
        '''
        pass
    #

    def feedbackPIDSlot(self, server, variable, outputParams, feedbackParams):
        '''
        Starts a PID feedback loop on a piece of equipment.

        Args:
            server (str) : The name of the server
            variable (str) : The name of the variable to track for feedback. Will automatically
                be added to tracked varaibles if it is not already tracked.
            outputParams (list) : A list of parameters for the output DEV NOTE: SPECIFY
            feedbackParams (list) : A list of parameters for the feedback loop DEV NOTE: SPECIFY
        '''
        pass
    #

    def verifySlot(self, servers):
        '''
        Verify that certain servers exist. Will generate an errorSignal if the given servers
        are not present.

        Args:
            servers (list) : A list of servers to check.
        '''
        pass
    #
#
