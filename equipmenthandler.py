'''
A module to define equipment handling. The main goal being to manage signals to and from
the LabRAD servers in an intelligent and thread safe manner without blocking the sequencer
thread.
'''
import labrad
from PyQt5.QtCore import QThread, pyqtSignal
# from exceptions import LabRADError

from time import sleep

class EquipmentHandler(QThread):
    '''
    Handels communication with the labRAD servers that run the equipment in an intelligent
    and thread safe manner without blocking the sequencer of GUI threads. Operates largly
    independant of whatever is happening with the recipe
    '''
    # Signals for GUI
    errorSignal = pyqtSignal() # Indicates an equipment error that is fatal to the process
    guiTrackedVarSignal = pyqtSignal(str, bool) # Add/Remove a tracked variable entry on status window
    updateTrackedVarSignal = pyqtSignal(str)

    # Primary Signals
    commandSignal = pyqtSignal(str, str, list)
    trackSignal = pyqtSignal(str, str, str)
    recordSignal = pyqtSignal(str)
    stopRecordSignal = pyqtSignal(str)
    verifySignal = pyqtSignal(list)
    feedbackPIDSignal = pyqtSignal(str, str, list, list)

    def __init__(self, servers=None):
        '''
        Initialize the equipment handler

        Args:
            servers : A list of servers to specifically load, if None it will load every
                labRAD server that it can find.
        '''
        super().__init__()

        self.active = False

        self.cxn = labrad.connect('localhost', password='pass')

        self.servers = dict()
        if servers is not None: # Load specific servers
            for name in servers:
                if hasattr(self.cxn, name):
                    self.servers[name] = getattr(self.cxn, name)
                else:
                    print("Warning server " + name + " not found.")
                #
        else: # Load all the servers you can find
            for num, svrname in self.cxn['manager'].servers():
                if svrname not in ['Manager', 'Registry', 'Auth']:
                    name = svrname.replace(' ', '_').lower()
                    self.servers[name] = getattr(self.cxn, name)
        #

        self.trackedVarsAccess = dict() # Dictionary of the tracked varaibles, same keys as self.info
        self.info = dict() # Dictionary of the values of the tracked variables

        # Connect all the signals and slots
        # signals to GUI are connected in the relevant GUI code
        self.commandSignal.connect(self.commandSlot)
        self.trackSignal.connect(self.trackSlot)
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
        try:
            while self.active:
                sleep(0.05) # FOR TESTING, REMOVE OR MODIFY
                for k in list(self.trackedVarsAccess.keys()): # Update the tracked varaibles
                    self.info[k] = self.trackedVarsAccess[k]()
                    self.updateTrackedVarSignal.emit(k)

                # Update any feedback loops

                # Record any data that needs to be recorded.

                # Special GUI tasks, such as the status of the valves or GUI interfaces
        except:
            self.errorSignal.emit()
            self.active = False
            from traceback import format_exc
            print(format_exc())
    #

    def trackSlot(self, name, server, accessor):
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
            accessor (str): The accessor function (in the namespace of that server, i.e.
                getattr(server, accessor) gives the function) to get the value must return
                one floating point number.
        '''
        try:
            if server in self.servers:
                if name in self.trackedVarsAccess: # If it already exists, ignore this.
                    return
                if hasattr(self.servers[server], accessor):
                    self.trackedVarsAccess[name] = getattr(self.servers[server], accessor)
                    self.guiTrackedVarSignal.emit(name, True)
                else:
                    raise ValueError("Server " + str(server) + " does not have " + str(accessor))
            else:
                raise ValueError("Server " + str(server) + " not found")
        except:
            self.errorSignal.emit()
    #

    def commandSlot(self, server, command, args):
        '''
        Sends a simple command to a labRAD server. No return values

        Args:
            server (str) : The name of the server.
            command (str) : The name of the command, accessible by getattr
            args_kwargs (list) : A list containing the arguments of the command and the
                keyword arguments, which will be used to call the server using
                server.command(*args). This must be a list, otherwise will emit an errorSignal.
                The list may be empty
        '''
        try:
            if server in self.servers:
                if not isinstance(args, list):
                    raise ValueError("Server Command Arguments not properly formatted.")
                if hasattr(self.servers[server], command):
                    com = getattr(self.servers[server], command)
                    com(*args)
                else:
                    raise ValueError("Server " + str(server) + " does not have function" + str(command))
            else:
                raise ValueError("Server " + str(server) + " not found")
        except:
            self.errorSignal.emit()
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
        Verify that certain servers exist within the equipment handler. Will generate an
        errorSignal if the given servers don't exist or were not added to the equipment
        handler.

        Args:
            servers (list) : A list of servers to check.
        '''
        try:
            for server in servers:
                if server not in self.servers:
                    err = "Server not found. Either it does not exist or it was not added "
                    err += "to the equipment handler."
                    raise ValueError(err)
        except:
            self.errorSignal.emit()
    #
#
