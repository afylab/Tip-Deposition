'''
A module to define equipment handling. The main goal being to manage signals to and from
the LabRAD servers in an intelligent and thread safe manner without blocking the sequencer
thread.
'''
import labrad
from PyQt5.QtCore import QThread, pyqtSignal

from datetime import datetime
from time import sleep, perf_counter
from os.path import join
import numpy as np

class PIDFeedbackController():
    def __init__(self, info, variable, outputFunction, P, I, D, setpoint, offset, minMaxOutput, ramptime, MaxIntegral=None):
        '''
        Controller to run a PID loop on the data.

        Args:
            info : A reference to EquipmentHandler.info, dictionary of tracked variables
            trackedVar : Name of the variable to track, must be in info.
            outputFunction : The function to call to change the output based on the loop.
                Must accept one floating point varaible.
            P (float) : The proportional term, must be positive
            I (float) : The integral term, must be positive
            D (float) : The derivative term, must be positive
            setpoint (float) : The setpoint for calculating error signal.
            minMaxOutput (tuple) : A tuple of (minimum_output, maximum_output)
            ramptime (float) : If nonzero will linearly ramp the output to the offset value over a given number of seconds before starting the loop.
            minMaxIntegral (float) : The maximum absolute value of the integral, if None will be set
                such that I*maximum_integral = maximum_output, i.e.
                values such that the integral term can drive to the maximum output by itself.
        '''
        self.varDict = info
        self.variable = variable
        self.function = outputFunction
        self.P = float(P)
        self.I = float(I)
        self.D = float(D)
        self.setpoint = float(setpoint)
        self.offset = offset
        self.t0 = datetime.now()
        self.prev_time = 0
        self.integral = 0
        self.prev_error = 0
        self.input = input
        self.min = minMaxOutput[0]
        self.max = minMaxOutput[1]

        if MaxIntegral is None:
            if self.I != 0.0:
                self.maxIntegral = np.abs(self.max/self.I)
                self.minIntegral = -1.0*self.maxIntegral
            else:
                self.minIntegral = 0
                self.maxIntegral = 0
        else:
            self.maxIntegral = np.abs(MaxIntegral)
            self.minIntegral = -1.0*self.maxIntegral
        #
        self.paused = False
        self.ramping = False
        self.ramp_to = 0.0
        self.output = 0.0
        if ramptime == 0.0:
            self.waiting = False
            self.wait_time = 0
            self.wait_start = datetime.now()
        else:
            self.wait_time = float(ramptime)
            self.wait_start = datetime.now()
            self.waiting = True
            self.rampto(float(ramptime), self.offset)
    #

    def pause(self, ramptime=0.0):
        '''
        Pauses the feedback loop, retaining all relevant parameters. Zeros the output
        while paused.

        Args:
            ramptime (float or None) : If not zero will ramp down the output to
                zero over the given number of seconds.
        '''
        if not self.paused:
            self.paused = True
            self.integral = 0.0
            self.offset = self.output
            if ramptime == 0.0:
                self.function(0.0)
            else:
                self.rampdown(ramptime)
        #
    #

    def rampdown(self, time):
        '''
        Linearly ramps down the output over some time interval. Pauses the loop.
        '''
        if not self.paused:
            self.paused = True
        self.ramp_time = time
        self.ramp_to = 0.0
        self.ramp_start = datetime.now()
        self.ramping = True
    #

    def rampto(self, time, value):
        '''
        Linearly ramps the output some value over some time interval.
        '''
        self.ramp_time = time
        self.ramp_to = value
        self.ramp_start = datetime.now()
        self.ramping = True
    #

    def resume_after(self, wait, ramptime=None):
        '''
        Resumes the output of the loop after waiting a certain period. The output
        is restored to the previous setting immediatly, then the loop waits a
        certain amount of time for the system to stabalize.

        Args:
            wait (float) : The number of second to wait after resetting the output
            ramptime (float or None) : If not None will ramp up the output over the
            given amount of time, this will be counted as part of the wait time.
        '''
        if self.paused:
            self.wait_time = float(wait)
            self.wait_start = datetime.now()
            #print("Resuming at ", str(self.offset), " After " + str(self.wait_time))
            if ramptime is None or ramptime == 0:
                self.function(self.offset)
            else:
                self.rampto(ramptime, self.offset)
            self.waiting = True
            self.paused = False # Do this last in case update is called while self.function is executing, it's happened before!
        #
    #

    def resume(self, ramptime=None):
        '''
        Immediately resumes both the output and the loop to the prior settings.

        Args:
            ramptime (float or None) : If not None will ramp up the output over the
            given amount of time before resuming.
        '''
        if self.paused:
            if ramptime is None or ramptime == 0:
                self.function(self.offset)
            else:
                self.rampto(ramptime, self.offset)
            self.prev_time = (datetime.now()-self.t0).total_seconds()
            self.paused = False
            self.waiting = False
        #
    #

    def update(self):
        '''
        Update the output based on current values.
        '''
        if self.ramping:
            t = (datetime.now()-self.ramp_start).total_seconds()
            if self.ramp_to == 0.0:
                out = self.output - self.output*t/(self.ramp_time)
            else:
                out = self.ramp_to*t/(self.ramp_time)

            if self.ramp_to == 0.0 and out <= 0.0:
                self.function(0.0)
                self.ramping = False
            elif self.ramp_to > 0.0 and out > self.ramp_to:
                self.function(self.ramp_to)
                self.ramping = False
                self.prev_time = (datetime.now()-self.t0).total_seconds() # reset the timing. In case it as called without waiting the loop as well.
            else:
                self.function(out)
                return # In case it as called without waiting the loop as well.

        if self.paused:
            return
        elif self.waiting:
            if (datetime.now()-self.wait_start).total_seconds() >= self.wait_time:
                self.prev_time = (datetime.now()-self.t0).total_seconds() # reset the timing
                self.waiting = False
            else:
                return
        #

        time = (datetime.now()-self.t0).total_seconds()
        error = self.setpoint - float(self.varDict[self.variable])

        # Proportional term
        P_value = self.P*error

        # Integral term
        self.integral = self.integral + error*(time - self.prev_time)
        if self.integral > self.maxIntegral:
            self.integral = self.maxIntegral
        elif self.integral < self.minIntegral:
            self.integral = self.minIntegral
        #
        I_value = self.I*self.integral

        # Derivative term
        if time - self.prev_time > 1e-3: # Protect from the derivative term diverging
            D_value = self.D*(error - self.prev_error)/(time - self.prev_time)
        else:
            D_value = 0

        output = P_value + I_value + D_value + self.offset
        if output > self.max:
            output = self.max
        elif output < self.min:
            output = self.min
        self.output = output

        if not self.paused: # Here for safety, incase pasued is called in this function
            self.function(self.output) # Set the output
        self.prev_time = time
        self.prev_error = error
    #

    def changeSetpoint(self, setpoint):
        '''
        Change the setpoint of the loop.

        Args:
            setpoint (float) : The setpoint for calculating error signal.
        '''
        self.setpoint = float(setpoint)
    #

    def changePID(self, P, I, D):
        '''
        Change the PID terms. Note, does not change the minimum or maximum integral.

        Args:
            P (float) : The proportional term
            I (float) : The integral term
            D (float) : The derivative term
        '''
        self.P = float(P)
        self.I = float(I)
        self.D = float(D)
    #

    def __del__(self):
        '''
        Sets the output to zero when closing
        '''
        try:
            self.function(0.0)
        except:
            print("Error closing feedback loop, hardware maybe unstable.")
#

class EquipmentHandler(QThread):
    '''
    Handels communication with the labRAD servers that run the equipment in an intelligent
    and thread safe manner without blocking the sequencer of GUI threads. Operates largly
    independant of whatever is happening with the recipe
    '''
    # Signals for GUI
    errorSignal = pyqtSignal() # Indicates an equipment error that is fatal to the process
    serverNotFoundSignal = pyqtSignal(str) # Indicates an equipment error that is fatal to the process
    guiTrackedVarSignal = pyqtSignal(bool, str, str) # Add/Remove a tracked variable entry on status window
    updateTrackedVarSignal = pyqtSignal(str)
    timerSignal = pyqtSignal(str)

    # Primary Signals
    commandSignal = pyqtSignal(str, str, list)
    trackSignal = pyqtSignal(str, str, str, str)
    stopTrackingSignal = pyqtSignal(str)
    initRecordSignal = pyqtSignal(str, str, str)
    recordSignal = pyqtSignal(str)
    stopRecordSignal = pyqtSignal(str)
    verifySignal = pyqtSignal(list)
    feedbackPIDSignal = pyqtSignal(str, str, list)
    pauseFeedbackPIDSignal = pyqtSignal(str, float)
    resumeFeedbackPIDSignal = pyqtSignal(str, float, float)
    changePIDSetpointSignal = pyqtSignal(str, float)
    rampdownPIDSignal = pyqtSignal(str, float)
    stopFeedbackPIDSignal = pyqtSignal(str)
    stopAllFeedbackSignal = pyqtSignal()

    def __init__(self, servers=None, debug=False):
        '''
        Initialize the equipment handler

        Args:
            servers : A list of servers to specifically load, if None it will load every
                labRAD server that it can find.
            debug (bool) : If True will print out serial error and timing information to the terminal
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
                if svrname not in ['Manager', 'Registry', 'Auth']: #and not 'Serial Server' in svrname:
                    name = svrname.replace(' ', '_').lower()
                    if hasattr(self.cxn, name):
                        self.servers[name] = getattr(self.cxn, name)
        #

        # Initilize various dictionaries
        self.trackedVarsAccess = dict() # Dictionary of the tracked varaibles, same keys as self.info
        self.feedbackLoops = dict()
        self.recordedVars = dict()
        self.info = dict() # Dictionary of the values of the tracked variables

        # Connect all the signals and slots
        # signals to GUI are connected in the relevant GUI code
        self.commandSignal.connect(self.commandSlot)
        self.trackSignal.connect(self.trackSlot)
        self.stopTrackingSignal.connect(self.stopTrackingSlot)
        self.initRecordSignal.connect(self.initRecording)
        self.recordSignal.connect(self.recordVariableSlot)
        self.stopRecordSignal.connect(self.stopRecordSlot)
        self.verifySignal.connect(self.verifySlot)
        self.feedbackPIDSignal.connect(self.feedbackPIDSlot)
        self.pauseFeedbackPIDSignal.connect(self.pauseFeedbackPIDSlot)
        self.resumeFeedbackPIDSignal.connect(self.resumeFeedbackPIDSlot)
        self.stopFeedbackPIDSignal.connect(self.stopFeedbackPIDSlot)
        self.changePIDSetpointSignal.connect(self.changePIDSetpointSlot)
        self.rampdownPIDSignal.connect(self.rampdownPIDSlot)
        self.stopAllFeedbackSignal.connect(self.stopAllFeedback)

        # To ensure that data is recored and updated at regular intervals have a target
        # update drequency that will attempt to match by sleeping the main loop for an
        # interval after all serial communications are made. If serial communictions are
        # too slow then it will not wait.
        self.targetUpdateFrequency = 4 # Hz
        self.targetUpdatePeriod = 1.0/self.targetUpdateFrequency

        self.debugmode = debug
    #

    def run(self):
        '''
        The main loop of the equipment thread. Updates tracked variables and feedback loops
        and logs data as appropriate. Handels errors if any come up.
        '''
        self.active = True
        try:
            while self.active:
                t0 = perf_counter()
                for k in list(self.trackedVarsAccess.keys()): # Update the tracked varaibles
                    try:
                        val = self.trackedVarsAccess[k]()
                        if val == "Timeout":
                            if self.debugmode:
                                print("Warning " + str(k) + " timed out, value not updated")
                        elif val == "ChecksumError": # Common error from power supply server
                            if self.debugmode:
                                print("Warning " + str(k) + " had a serial error, value not updated")
                        elif val == "INVALID": # Common error from Eurotherm
                            if self.debugmode:
                                print("Warning " + str(k) + " had a serial error, value not updated")
                        else:
                            self.info[k] = float(val)
                            self.updateTrackedVarSignal.emit(k)
                    except KeyError: # Sometimes untracking variables will cause a key error
                        pass
                tnow = datetime.now()

                # Update any feedback loops
                for k in list(self.feedbackLoops.keys()):
                    self.feedbackLoops[k].update()

                # Record any data that needs to be recorded.
                for k in list(self.recordedVars.keys()):
                    if self.recordedVars[k][0]:
                        self.recordedVars[k][1].add((tnow-self.recordedVars[k][2]).total_seconds(), self.info[k])

                #
                t1 = perf_counter()
                dt = t1 - t0
                delay = self.targetUpdatePeriod - dt
                if self.debugmode:
                    print(t1-t0, delay, dt+delay) # For Debugging timing issues
                if delay > 0:
                    sleep(delay)
        except:
            self.errorSignal.emit()
            self.active = False
            from traceback import format_exc
            print(format_exc())
        self.stopAllFeedback()
    #

    def trackSlot(self, name, server, accessor, units):
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
            units (str) : The units of the tracked varaible (for display purposes only).
        '''
        try:
            if server in self.servers:
                if name in self.trackedVarsAccess: # If it already exists, ignore this signal
                    return
                if hasattr(self.servers[server], accessor):
                    self.trackedVarsAccess[name] = getattr(self.servers[server], accessor)

                    try: # Try to get a starting value
                        val = self.trackedVarsAccess[name]()
                        self.info[name] = float(val)
                    except:
                        print("Warning: Couldn't get starting value of " + str(name) + ", starting from zero.")
                        self.info[name] = 0.0

                    self.guiTrackedVarSignal.emit(True, name, units)
                else:
                    raise ValueError("Server " + str(server) + " does not have " + str(accessor))
            else:
                raise ValueError("Server " + str(server) + " not found")
        except:
            self.errorSignal.emit()
    #

    def stopTrackingSlot(self, name):
        '''
        Stop tacking a variable

        Args:
            name (str) : The name of the variable, which will function as the key to access it.
                Setting name to 'all' will result in all tracked varaibles being stopped.
        '''
        if name.lower() == 'all':
            for k in list(self.trackedVarsAccess.keys()):
                if k != "Pressure": # We always want to be tracking pressure
                    self.trackedVarsAccess.pop(k)
        else:
            if name in self.trackedVarsAccess:
                self.trackedVarsAccess.pop(name)
        #
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

    def initRecording(self, database, version, squidname):
        '''
        Initilize the recording of data through the datavault server. If was recording previously will
        stop recording to previous files and setup to make new files. The location of the saves will
        be based on the type of recipe and version.

        File structure is as follows, files will be saved to database/version/data and the file
        names will be given as "00000 - squidname - varname.hdf5" where 00000 is the automatic datavault
        file number.

        Args:
            database (str) - Path like string to the root squid database.
            version (str) - The formatted name and version of the recipe, which is a subfolder in database
            squidname (str) - The unique name of the SQUID.
        '''
        self.savedir = join(database, version)
        self.recordedVars = dict()
        self.squidname = squidname.replace('.','-').replace(' ','_')
    #

    def recordVariableSlot(self, variable):
        '''
        Record a tracked variable to datavault. If the variable is already being recorded nthing
        happens.

        Args:
            variable (str) : The name of the tracked varirable, i.e. self.info[name]
        '''
        try:
            if variable not in self.recordedVars:
                if variable not in self.info:
                    raise ValueError("Cannot record, variable " + str(variable) + " not tracked.")
                dv = labrad.connect('localhost', password='pass').data_vault
                for dir in self.savedir.split('\\'):
                    dv.cd(dir, True)
                varname = variable.replace('.','-').replace(' ','_')
                dv.new(self.squidname+" - "+varname, 'x', 'y')
                self.recordedVars[variable] = [True, dv, datetime.now()]
        except:
            self.errorSignal.emit()
    #

    def stopRecordSlot(self, variable):
        '''
        Stop recording a tracked variable. If the variable is not currently being recorded
        this is ignored.

        Args:
            variable (str) : The name of the tracked varirable, i.e. self.info[name] or if varaible
                is "ALL" will stop recording all current tracked varaibles
        '''
        if variable in self.recordedVars:
            self.recordedVars[variable][0] = False
        if variable.lower() == "all":
            for k in self.recordedVars:
                self.recordedVars[k][0] = False
    #

    def feedbackPIDSlot(self, server, variable, feedbackParams):
        '''
        Starts a PID feedback loop on a piece of equipment.

        Args:
            server (str) : The name of the server
            variable (str) : The name of the variable to track for feedback. Will automatically
                be added to tracked varaibles if it is not already tracked.
            feedbackParams (list) : A list of parameters for the feedback loop to be passed.
                First is the name of the command to set the output, (accessible by getattr).
                Must accept one floating point argument. The subsequent parameters are
                numerical positional arguments to the constructor the PIDFeedbackController
                object, i.e. [outputFunc, P, I, D, setpoint, offset, minMaxOutput, ramptime]
        '''
        try:
            if server in self.servers:
                if variable not in self.info:
                    raise ValueError("Cannot feedback, variable " + str(variable) + " not tracked.")
                outputFunc, P, I, D, setpoint, offset, minMaxOutput, ramptime = feedbackParams
                if hasattr(self.servers[server], outputFunc):
                    command = getattr(self.servers[server], outputFunc)
                    self.feedbackLoops[variable] = PIDFeedbackController(self.info, variable, command, P, I, D, setpoint, offset, minMaxOutput, ramptime)
                else:
                    raise ValueError("Server " + str(server) + " does not have function" + str(outputFunc))
            else:
                raise ValueError("Server " + str(server) + " not found")
        except:
            self.errorSignal.emit()
    #

    def pauseFeedbackPIDSlot(self, variable, ramptime):
        '''
        Pause a PID feedback loop on a given variable, setting the output equal
        to zero but retaining the previous output

        Args:
            variable : The tracked variable, needs to be an established loop
            ramptime: If non-zero will ramp down the output to zero over a given
                number of seconds.
        '''
        if variable in self.feedbackLoops:
            self.feedbackLoops[variable].pause(ramptime)
    #

    def resumeFeedbackPIDSlot(self, variable, wait, ramptime):
        '''
        Resume a PID feedback loop on a given variable, setting the output equal
        to zero the previous output then waiting a certain amount of time before
        retuming the loop
        '''
        if variable in self.feedbackLoops:
            if wait > 0:
                # print("Waiting for ", wait)
                if ramptime > 0:
                    self.feedbackLoops[variable].resume_after(wait, ramptime)
                else:
                    self.feedbackLoops[variable].resume_after(wait)
            else:
                self.feedbackLoops[variable].resume()
    #

    def stopFeedbackPIDSlot(self, variable):
        '''
        Stop a PID feedback loop on a given variable, setting the output equal to zero.
        '''
        if variable in self.feedbackLoops:
            del self.feedbackLoops[variable]
    #

    def changePIDSetpointSlot(self, variable, setpoint):
        '''
        Change the setpoint on a given PID loop.
        '''
        if variable in self.feedbackLoops:
            self.feedbackLoops[variable].changeSetpoint(setpoint)
    #

    def rampdownPIDSlot(self, variable, time):
        '''
        Ramps down the output of a PID loop linearly over some time interval
        '''
        if variable in self.feedbackLoops:
            self.feedbackLoops[variable].rampdown(time)
    #

    def stopAllFeedback(self):
        '''
        Immediatly stop all feedback loops
        '''
        for variable in list(self.feedbackLoops):
            del self.feedbackLoops[variable]
    #

    def verifySlot(self, servers):
        '''
        Verify that certain servers exist within the equipment handler. Will generate an
        errorSignal if the given servers don't exist or were not added to the equipment
        handler.

        Args:
            servers (list) : A list of servers to check.
        '''
        err = ''
        for server in servers:
            if server == 'serial_server': # Need the serial server for the other servers to work, but it's name varies
                print("Warning, does not check for the serial server due to hostname ambiguity")
            elif server not in self.servers:
                    if err != '':
                        err += ','
                    err += " " + str(server)
        if err != '':
            err = "Server " + err
            err += " not found."
            self.serverNotFoundSignal.emit(err)
    #

    def toggleDebugMode(self):
        self.debugmode = not self.debugmode
    #

    def __del__(self):
        '''
        Handel the program closing
        '''
        self.stopAllFeedback()
    #
#
