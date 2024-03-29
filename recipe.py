'''
A module for defining tip deposition recipes generically
'''

from exceptions import ProcessInterruptionError, ProcessTimeoutError
from time import sleep
from datetime import datetime, timedelta
from os.path import join
import numpy as np

def timeformat(delta):
    '''
    Put the time in a nice fuman readable format.

    Args:
        delta (timedelta) : The timedetlta object
    '''
    hours, remainder = divmod(delta.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours != 0.0:
        return '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
    else:
        return '{:02}:{:02}'.format(int(minutes), int(seconds))

class Step():
    '''
    Feedback from the recipe to the user interface. Is set up in the recipie,
    yielded to the gui via a context switch to the sequencer and

    Args:
        user_input (bool) : If user input is required.
        instructions (string) : Instructions to the user, or simply an aacknowledgment of an automated step.
    '''
    def __init__(self, user_input=False, instructions=None):
        self.user_input = user_input
        self.params_needed = False
        self.instructions = instructions
        self.input_spec = dict()
        self.input_param_values = dict()
        self.processed = False # If a step has been processed by the sequencer
    #

    def add_input_param(self, name, default=None, limits=None, options=None, isInt=False):
        '''
        TO BE CALLED BEFORE THE STEP IS YIELDED TO THE SEQUENCER,
        calling this out of order will result in an exception.

        Add a parameter that the user will be asked for. Parameters will always
        be displayed on the GUI alphabetically sorted by their name, and their
        name is used to access them.

        Note: Python 3.7+ is needed to maintain insertion order of parameters in dictionaries.

        Args:
            prompt (string) : The user-facing label for the parameter.
            default (string or value) : The default value to display. If None the
                field will be empty.
            limits (tuple) : If the value is a float, defined as (minimum, maximum)
            options : A list of strings, for discrete options the user can choose between. If None
                a arbitrary value is allowed (within limits).
            isInt (bool) : If True numerical input (i.e. where limits are specified) is treated as an integer

        '''
        if self.processed:
            raise ValueError("Attempted to add a parameter to a Step that has already been processed.")
        else:
            if not self.user_input:
                self.user_input = True
            self.params_needed = True
            self.input_spec[name] = [default, limits, options, isInt]
            self.input_param_values[name] = None
    #

    def get_param(self, name):
        '''
        TO BE CALLED AFTER THE STEP IS YIELDED TO THE SEQUENCER,
        calling this out of order will result in an exception.

        Accesses a parameter once user input has been given to it.
        '''
        if not self.processed:
            raise ValueError("Attempted to read the outcome of a Step that hasn't been processed.")
        else:
            return self.input_param_values[name]
    #

    def get_all_params(self):
        '''
        TO BE CALLED AFTER THE STEP IS YIELDED TO THE SEQUENCER,
        calling this out of order will result in an exception.

        Returns the parameters dictionary, protects from early access.
        '''
        if not self.processed:
            raise ValueError("Attempted to read the outcome of a Step that hasn't been processed.")
        else:
            return self.input_param_values
    #
#

class Recipe():
    '''
    Generic class for a specific recipe for tip deposition, defines a particular ordering
    of steps as well as any special behavior that is needed to carry out the recipe.

    WORKFLOW: To make a new receipe make a new class and inherit and extend the following functions,
    which are called by the sequencer.
    - __init__() add anything else needed them call the superclass initializer to check that the recipe
      has all the equipment it needs to the
    - proceed() which is a generator that yields each step, defined by a Step object to the sequencer
      and receives input back from the user interface when appropriate. This is the main process by
      which recipes are executed.
    - shutdown() attempts to shutdown the process, either at the end or early if there is a problem
      use it to make sure the equipment returns to a normal state.
    Each function has comments and a full worked example is given in, the Recipe_test class of the
    Testing_Calibration module. Familiarize yourself with the prototypes and how to use the Step
    objects before attempting to make a Recipe.
    '''

    def __init__(self, equip, updateSig, required_servers=None, version="1.0.0", savedir=None):
        '''
        Class initilizer, inhert and extend with any needed features then call the superclass initilizer
        i.e. super().__init__(equip, required, version_number)
        where:
        - equip is the equipment handler object and should be the first argument of your initilizer.
        - updateSig is the signal to update the manual hardware control everytime the recipe makes
            a change to the hardware
        - required is a list of the server names (keys to the servers dictionary) that your recipe needs.
            be sure to add all relevant equipment to this.
        - version is the version number of the recipe, if major changes are made to a recipe increment
            the version number and a new record of parameters will automatically be logged seperatly from
            any previous runs, elimiating potential compatability issues.
         -savedir is the root Vault file where deposition data is saved.
        '''
        self.name = type(self).__name__.replace("_"," ")
        self.version = version
        self.abort = False # Calling Sequencer.abortSlot will set this to false and stop current process
        self.pause = False
        self.wait_delay = 0.25 # Amount of time to wait after sending a command to hardware, to give the hardware time to catch up
        self.updateSig = updateSig

        if savedir is None:
            if issubclass(type(self), CalibrationRecipe):
                self.savedir = join('Tip Deposition Database','Calibrations')
            else:
                self.savedir = 'Tip Deposition Database'
        else:
            self.savedir = savedir

        # Connect to the equipment handler and validate all the servers
        self.equip = equip
        if required_servers is not None:
            self.equip.verifySignal.emit(required_servers)
        #
    #

    def get_name(self):
        '''
        Returns the unique name of this recipie and version in a file-saveable format.
        '''
        return type(self).__name__ + '_v' + self.version.replace('.','-')
    #

    def setup(self, defaults):
        '''
        Setup the recipe by loading defaults or information from previous depositions and getting user
        input. This function returns a Step object which is used to get the initial parameters in the
        user interface. Add parameter to it using Step.add_input_param then at startup the sequencer
        will automatically pass this step to the user interface and subsequently load the values into
        Recipe.parameters, a dictionary containg the parameters as {name:value}.  Use limits on
        numerical values to make sure no equipment breaking values are entered.

        To preserve insertion order and load in defaults when overloading, always call the superclass
        constructor before adding any parameters, i.e. the first line should be super().__init__(step, defaults)

        Args:
            defaults (dict) : a dictionary containg the previous parameters as {name:value}, to use as
                defaults. This dictionary is loaded and default values can be accessed using
                Recipe.default("Param Name") which will return the default or None if there is no such
                default parameter.
        '''
        if defaults is None:
            self.defaultParams = {}
        else:
            self.defaultParams = defaults
        setupstep = Step(instructions="Enter Tip and Deposition parameters")

        # Basic paramters that should be included for all recipies
        setupstep.add_input_param("SQUID Num.")
        setupstep.add_input_param("Person Evaporating")
        setupstep.add_input_param("Superconductor", default=self.default("Superconductor") )
        setupstep.add_input_param("SEM Diameter")
        setupstep.add_input_param("Tip to SHOVET Distance")
        setupstep.add_input_param("Tip to Leads Distance")
        setupstep.add_input_param("TF Aligned")
        return setupstep
    #

    def proceed(self):
        '''
        Run the recipe, overload to create a particular recipe.

        Overload to extend for a particular recipe, follow the prototype shown in this function.

        Basic Workflow:
        - define a new step object with a message to the user
        - add input parameters if appropriate
        - yield the step back to the sequencer
        - access the parameters in the step (if needed)
        - perform some action using the labRAD servers

        For reference parameters from previous runs are loaded at startup and accessible using the
        deafult function.
        '''
        yield Step(False, "Add steps to your recipe.")
    #

    def shutdown(self):
        '''
        Attempts to shutdown any relevant equipment and put the system on standby. Either
        part of normal shutdown or in the event of an unexpected error. Overload to protect
        critical equipment, but call super().shutdown().
        '''
        self.stopAllFeedback()
        self.equip.stopRecordSignal.emit("ALL")
        self.equip.stopTrackingSignal.emit("ALL")
    #

    def default(self, name):
        '''
        Attempts to return the default value of the parameter corresponding to name, will return
        None if no parameter exists. Do not attempt to call the default parameter dictionary directly
        as there may be missing parameters that will result in a KeyError.
        '''
        if name in self.defaultParams:
            return self.defaultParams[name]
        else:
            return None
    #

    def wait_for(self, minutes, shutdown=False):
        '''
        Sleep the recipe for a specified number of minutes. Still check for abort signals.

        Args:
            minutes (float) : Number of minutes to wait for, can be a fraction of a minute.
            shutdown (bool) : Set to true if this is occuring at shutdown, otherwise it will
                not wait due to the abort signal
        '''
        stoptime = datetime.now() + timedelta(minutes=minutes)
        while stoptime > datetime.now():
            self.equip.timerSignal.emit(timeformat(stoptime - datetime.now()))
            sleep(0.05)
            if self.abort and not shutdown:
                raise ProcessInterruptionError
            elif self.pause: # If paused, wait
                while self.pause:
                    sleep(0.01)
        self.equip.timerSignal.emit("")
    #

    def wait_until(self, variable, state, conditional="less than", timeout=100):
        '''
        Sleep the recipe until a variable meets a ceratin condition or until it
        times out. Still checks for abort signals.

        Args:
            variable (str) : The name of the tracked variable to follow, i.e. the key in
                self.equip.info[varaible]
            state : The desired state of that variable.
            conditional : The conditional to compare varaible and state. "less than" for
                variable < state, "greater than" for variable > state, "equal" for variable = state.
                Alternatively conditional can be a function that accepts a floating point value
                and returns a boolean when a certain condition is met.
            timeout : The number of minutes to wait, after which the condition will raise a
                ProcessTimeoutError exception.
        '''
        if variable not in self.equip.info:
            raise ValueError("Varaible " + str(variable) + " not a tracked variable.")

        stoptime = datetime.now() + timedelta(minutes=timeout)
        if conditional == "less than":
            comparitor = lambda x : x < state
        elif conditional == "greater than":
            comparitor = lambda x : x > state
        elif conditional == "equal":
            comparitor = lambda x : x == state
        elif callable(conditional): # the conditional is a function
            comparitor = conditional
        else:
            raise ValueError("Conditional not recognized.")
        self.equip.timerSignal.emit("Waiting for condition")
        while not comparitor(self.equip.info[variable]):
            sleep(0.05)
            if self.abort:
                raise ProcessInterruptionError
            elif self.pause: # If paused, wait
                while self.pause:
                    sleep(0.01)
            if datetime.now() > stoptime:
                raise ProcessTimeoutError
        self.equip.timerSignal.emit("")
    #

    def wait_stable(self, variable, state, interval, window=30, timeout=60):
        '''
        Sleep the recipe until a variable is stable to within a specified time
        window.

        Args:
            variable (str) : The name of the tracked variable to follow, i.e. the key in
                self.equip.info[varaible]
            state (float): The desired state of that variable, must be numeric
            interval (float, tuple) : The interval that the setpoint needs to be within for the whole window of time.
                If it is a float, stable means state-interval/2 < variable < state + interval/2
                If it's a tuple, stable means interval[0] < variable < interval[1]
            window (float) : the window of time to examine, in seconds.
            timeout : The number of minutes to wait, after which the condition will raise a
                ProcessTimeoutError exception.
        '''
        if variable not in self.equip.info:
            raise ValueError("Varaible " + str(variable) + " not a tracked variable.")

        t0 = datetime.now()
        stoptime = t0 + timedelta(minutes=timeout)

        if isinstance(interval, tuple) or isinstance(interval, list):
            min = interval[0]
            max = interval[1]
        else:
            min = state - interval/2
            max = state + interval/2

        points = np.zeros(int(window/0.05)) # The buffer to put the points into
        N = len(points)
        ix = 0
        filled = False
        def comparitor(value):
            if not filled:
                return False
            return np.max(points) < max and np.min(points) > min
        #

        self.equip.timerSignal.emit("Waiting until stable")
        while not comparitor(self.equip.info[variable]):
            points[ix] = self.equip.info[variable]
            ix += 1
            if ix >= N:
                ix = 0
                filled = True

            sleep(0.05)
            if self.abort:
                raise ProcessInterruptionError
            elif self.pause: # If paused, wait
                while self.pause:
                    sleep(0.01)
            if datetime.now() > stoptime:
                raise ProcessTimeoutError
        self.equip.timerSignal.emit("")

    def command(self, server, command, args=None, wait=True):
        '''
        Send a command to a LabRAD server through the equipment handler.

        Args:
            server (str) : The name of the LabRAD server to get the value from
            command (str): The name function (in the namespace of that server, i.e.
                getattr(server, accessor) gives the function)
            args : The arguments of the command and the keyword arguments, which will be
                used to call the server using server.command(*args). Must be a sting, float,
                list or None. If None, no arguments will be sent
            wait (bool) : If True will wait 0.1 seconds after sending the signal to allow
                the equipment handler and servers to catch up.
        '''
        if args is None:
            self.equip.commandSignal.emit(server, command, [])
        elif isinstance(args, float) or isinstance(args, str) or isinstance(args, int):
            self.equip.commandSignal.emit(server, command, [args])
        else:
            self.equip.commandSignal.emit(server, command, args)
        if wait:
            sleep(self.wait_delay) # give the program a little time to catch up
    #

    def valve(self, valve, open, wait=True, server='valve_relay_server'):
        '''
        Handels opening and closing of simple vacuum valves, leak valve is handeled
        with the leakvalve function. Also sends signal to update the status widget.

        Args:
            Valves (str) : Which valve to open/close. OPeitons "gate", "chamber", "turbo" and "all"
            open (bool) : Will open valve if True, close if False.
            wait (bool) : If True will wait 0.1 seconds after sending the signal to allow
                the equipment handler and servers to catch up.
            server (str) : The name of the valve relay server
        '''
        if valve == "gate":
            if open:
                self.equip.commandSignal.emit(server, 'gate_open', [])
            else:
                self.equip.commandSignal.emit(server, 'gate_close', [])
        elif valve == "chamber":
            if open:
                self.equip.commandSignal.emit(server, 'chamber_valve_open', [])
            else:
                self.equip.commandSignal.emit(server, 'chamber_valve_close', [])
        elif valve == "turbo":
            if open:
                self.equip.commandSignal.emit(server, 'turbo_valve_open', [])
                print("opened the turbo")
            else:
                self.equip.commandSignal.emit(server, 'turbo_valve_close', [])
                print("closed the turbo")
        elif valve == 'all':
            if open:
                self.equip.commandSignal.emit(server, 'gate_open', [])
                self.equip.commandSignal.emit(server, 'chamber_valve_open', [])
                self.equip.commandSignal.emit(server, 'turbo_valve_open', [])
            else:
                self.equip.commandSignal.emit(server, 'gate_close', [])
                self.equip.commandSignal.emit(server, 'chamber_valve_close', [])
                self.equip.commandSignal.emit(server, 'turbo_valve_close', [])
        else:
            print("WARNNG invalid valve command, no change", valve)
        if wait:
            sleep(self.wait_delay) # give the program a little time to catch up
        self.updateSig.emit()
    #

    def pump(self, pump, on, wait=True, server='valve_relay_server'):
        '''
        Handels opening and closing of simple vacuum valves, leak valve is handeled
        with the leakvalve function. Also sends signal to update the status widget.

        Args:
            Valves (str) : Which valve to open/close. Options "gate", "chamber", "turbo" and "all"
            open (bool) : Will open valve if True, close if False.
            wait (bool) : If True will wait 0.1 seconds after sending the signal to allow
                the equipment handler and servers to catch up.
            server (str) : The name of the valve relay server
        '''
        if pump == "scroll":
            if on:
                self.equip.commandSignal.emit(server, 'scroll_on', [])
            else:
                self.equip.commandSignal.emit(server, 'scroll_off', [])
        elif pump == "turbo":
            if open:
                self.equip.commandSignal.emit(server, 'turbo_on', [])
            else:
                self.equip.commandSignal.emit(server, 'turbo_off', [])
        elif pump == 'all':
            if open:
                self.equip.commandSignal.emit(server, 'scroll_on', [])
                self.equip.commandSignal.emit(server, 'turbo_on', [])
            else:
                self.equip.commandSignal.emit(server, 'turbo_off', [])
                if wait:
                    sleep(self.wait_delay) # give the program a little time to catch up
                self.equip.commandSignal.emit(server, 'scroll_off', [])
        else:
            print("WARNNG invalid pump command, no change", pump)
        if wait:
            sleep(self.wait_delay) # give the program a little time to catch up
        self.updateSig.emit()
    #

    def leakvalve(self, open, flow=None, pressure=None, wait=True, server='rvc_server'):
        '''
        Handels opening and closing of simple vacuum valves, leak valve is handeled
        with the leakvalve function. Also sends signal to update the status widget.

        Args:
            Valves (str) : Which valve to open/close. Options: "gate", "chamber", "turbo" and "all"
            open (bool) : Will close if False, if open will look for a flow or pressure,
                if neither are defined will open to 100% flow.
            flow (float) : The percentage of flow in flow mode, needs open to be True
            pressure (float) : The target pressure, in mbar, for pressure mode, needs open to be True
            wait (bool) : If True will wait 0.1 seconds after sending the signal to allow
                the equipment handler and servers to catch up.
            server (str) : The name of the valve relay server
        '''
        if not open: # Close the valve in both flow and pressure modes
            self.equip.commandSignal.emit(server, 'close_valve', [])
        elif open and flow is None and pressure is None: # open the valve to 100% flow
            self.equip.commandSignal.emit(server, 'set_mode_flo', [])
            self.equip.commandSignal.emit(server, 'set_nom_flo', ['100.0'])
        elif open and flow is not None: # open to an arbitrary flow
            if not isinstance(flow, float) or float > 100.0 or float < 0.0:
                print("WARNNG invalid leakvalve command, malformatted flow parameter, no change")
                return
            else:
                self.equip.commandSignal.emit(server, 'set_mode_flo', [])
                self.equip.commandSignal.emit(server, 'set_nom_flo', ["{:05.1F}".format(flow)])
        elif open and pressure is not None: # open to an arbitrary pressure
            if not isinstance(pressure, float):
                print("WARNNG invalid leakvalve command, malformatted pressure parameter, no change")
                return
            else:
                self.equip.commandSignal.emit(server, 'set_mode_prs', [])
                self.equip.commandSignal.emit(server, 'set_nom_prs', [pressure])
        else:
            print("WARNNG invalid leakvalve command, no change")
        if wait:
            sleep(self.wait_delay) # give the program a little time to catch up
        self.updateSig.emit()
    #

    def shutter(self, shutter, open, wait=True):
        '''
        Handels opening and closing of the deposition source shutters.

        Args:
            shutter (str) : Which shutter to open/close. Options "evaporator", "effusion", and "all"
            open (bool) : Will open valve if True, close if False.
            wait (bool) : If True will wait 0.1 seconds after sending the signal to allow
                the equipment handler and servers to catch up.
            server (str) : The name of the valve relay server
        '''
        if shutter == "evaporator":
            if open:
                self.equip.commandSignal.emit('evaporator_shutter_server', 'open_shutter', [])
            else:
                self.equip.commandSignal.emit('evaporator_shutter_server', 'close_shutter', [])
        elif shutter == "effusion":
            if open:
                self.equip.commandSignal.emit('evaporator_shutter_server', 'open_effusion_shutter', [])
            else:
                self.equip.commandSignal.emit('evaporator_shutter_server', 'close_effusion_shutter', [])
        elif shutter == 'all':
            if open:
                self.equip.commandSignal.emit('evaporator_shutter_server', 'open_shutter', [])
                self.equip.commandSignal.emit('evaporator_shutter_server', 'open_effusion_shutter', [])
            else:
                self.equip.commandSignal.emit('evaporator_shutter_server', 'close_shutter', [])
                self.equip.commandSignal.emit('evaporator_shutter_server', 'close_effusion_shutter', [])
        else:
            print("WARNNG invalid shutter command, no change", shutter)
        if wait:
            sleep(self.wait_delay) # give the program a little time to catch up
        self.updateSig.emit()
    #

    def trackVariable(self, name, server, accessor, units='', wait=True):
        '''
        Send a signal to the equipment handler to track a varaible.

        Args:
            name (str) : The name of the variable, which will function as the key to access it.
            server (str) : The name of the LabRAD server to get the value from
            accessor (str): The accessor function (in the namespace of that server, i.e.
                getattr(server, accessor) gives the function) to get the value must return
                one floating point number.
            units (str) : If not '' a label will appear after the tracked varaible with the given unit
            wait (bool) : If True will wait short while after sending the signal
                to allow the equipment handler and servers to catch up.
        '''
        self.equip.trackSignal.emit(name, server, accessor, units)
        if wait:
            sleep(self.wait_delay) # give the program a little time to catch up
    #

    def stopTracking(self, variable):
        '''
        Stop plotting a tracked varaible.

        Args:
            variable (str) : The tracked variable to stop.
        '''
        self.equip.stopTrackingSignal.emit(variable)
    #

    def recordVariable(self, variable):
        '''
        Begin recording a tracked varaible to data vault

        Args:
            variable (str) : The tracked variable to record, must be a tracked variable in self.equip.info
        '''
        self.equip.recordSignal.emit(variable)
    #

    def stopRecordingVariable(self, variable):
        '''
        Stop recording a tracked varaible to data vault

        Args:
            variable (str) : The tracked variable to stop record, must be a tracked variable in
                self.equip.info or "ALL" in which case it will stop recording everything.
        '''
        self.equip.stopRecordSignal.emit(variable)
    #

    def PIDLoop(self, trackedVar, server, outputFunc, P, I, D, setpoint, offset, minMaxOutput, ramptime=0.0, heatup_time=0.0, wait=True):
        '''
        Begin plotting a tracked varaible.

        Args:
            trackedVar (str) : The tracked variable to feedback on, must be a tracked variable in self.equip.info
            server (str) : The server that the output function outputs to.
            P (float) : The P-coefficient, following standard conventions.
            I (float) : The I-coefficient, following standard conventions.
            D (float) : The D-coefficient, following standard conventions.
            setpoint (float) : The initial setpoint of the loop
            offset (float) : The offset for the output.
            minMaxOutput (tuple) : A tuple containing the minimum and maximum outputs values.
            ramptime (float) : If nonzero will ramp up the output over the
                given amount of seconds before starting the loop.
            heatup_time (float) : If nonzero will heat up the boat at offset voltage over a given number of seconds before starting the loop.
            wait (bool) : If True will wait 0.1 seconds after sending the
                signal to allow the equipment handler and servers to catch up.
        '''
        args = [outputFunc, float(P), float(I), float(D), float(setpoint), float(offset), (float(minMaxOutput[0]), float(minMaxOutput[1])), float(ramptime), float(heatup_time)]
        self.equip.feedbackPIDSignal.emit(server, trackedVar, args)
        if wait:
            sleep(self.wait_delay) # give the program a little time to catch up
        self.updateSig.emit()
    #

    def changePIDSetpoint(self, trackedVar, setpoint, wait=True):
        '''
        Changes the PID setpoint for an existing PID loop. The PID loop on trackedVar
        must have been stated before (this can be called on a paused or stopped loop.)

        Args:
            trackedVar (str) : The tracked variable to feedback on, must be a tracked variable in self.equip.info
            setpoint (float) : The initial setpoint of the loop
            wait (bool) : If True will wait 0.1 seconds after sending the
                signal to allow the equipment handler and servers to catch up.
        '''
        self.equip.changePIDSetpointSignal.emit(trackedVar, setpoint)
        if wait:
            sleep(self.wait_delay) # give the program a little time to catch up
        self.updateSig.emit()
    #

    def rampdownPID(self, trackedVar, time, wait=True):
        '''
        Takes the output of the PID loop and ramps it down to zero. The ramp is linear
        taking some time given in the function.

        Args:
            trackedVar (str) : The tracked variable to feedback on, must be a tracked variable in self.equip.info
            time (float) : The time over which to ramp down in seconds
            wait (bool) : If True will wait 0.1 seconds after sending the
                signal to allow the equipment handler and servers to catch up.
        '''
        self.equip.rampdownPIDSignal.emit(trackedVar, float(time))
        if wait:
            sleep(self.wait_delay) # give the program a little time to catch up
        self.updateSig.emit()
    #

    def stopPIDLoop(self, trackedVar, wait=True):
        '''
        Stops feedback on the given tracked variable.

        Args:
            wait (bool) : If True will wait 0.1 seconds after sending the
                signal to allow the equipment handler and servers to catch up.
        '''
        self.equip.stopFeedbackPIDSignal.emit(trackedVar)
        if wait:
            sleep(self.wait_delay) # give the program a little time to catch up
        self.updateSig.emit()
    #

    def stopAllFeedback(self, wait=True):
        '''
        Signals the equipment handler to stop all feedback loops.

        Args:
            wait (bool) : If True will wait 0.1 seconds after sending the
                signal to allow the equipment handler and servers to catch up.
        '''
        self.equip.stopAllFeedbackSignal.emit()
        if wait:
            sleep(self.wait_delay) # give the program a little time to catch up
        self.updateSig.emit()
    #

    def rampdownAllFeedback(self, time=100, wait=True):
        '''
        Signals the equipment handler to rampdown all feedback loops.

        Args:
            time (float) : The time over which to ramp down in seconds
            wait (bool) : If True will wait 0.1 seconds after sending the
                signal to allow the equipment handler and servers to catch up.
        '''
        self.equip.rampdownAllFeedbackSignal.emit(float(time))
        if wait:
            sleep(self.wait_delay) # give the program a little time to catch up
        self.updateSig.emit()
    #

    def pausePIDLoop(self, trackedVar, ramptime=0.0, wait=True):
        '''
        Stops feedback on the given tracked variable.

        Args:
            ramptime (float): If non-zero will ramp down the output to zero over a given
                number of seconds.
            wait (bool) : If True will wait 0.1 seconds after sending the
                signal to allow the equipment handler and servers to catch up.
        '''
        self.equip.pauseFeedbackPIDSignal.emit(trackedVar, ramptime)
        if wait:
            sleep(self.wait_delay) # give the program a little time to catch up
        self.updateSig.emit()
    #

    def resumePIDLoop(self, trackedVar, wait, ramptime=0.0, updateWait=True):
        '''
        Resumes a paused PID loop. Sets the output to the previous value immediatly
        the resumes the loop after a certain amount of time.

        Args:
            wait (flaot) : The number of seconds to wait before resuming the loop,
                to allow the systme to stabilize.
            ramptime (float) : If nonzero will ramp up the output over the
                given amount of seconds, this time will be counted as part of the wait time.
            updateWait (bool) : If True will wait 0.1 seconds after sending the
                signal to allow the equipment handler and servers to catch up.
        '''
        self.equip.resumeFeedbackPIDSignal.emit(trackedVar, wait, ramptime)
        if updateWait:
            sleep(self.wait_delay) # give the program a little time to catch up
        self.updateSig.emit()
    #

    def _process_startup(self, startupstep):
        """
        Loads the startup parameters into Recipe.parameters and initilizes recording in the equipment
        handeler.
        """
        self.parameters = dict()
        for k in startupstep.input_param_values.keys():
            self.parameters[k] = startupstep.input_param_values[k]

        try:
            self.equip.initRecordSignal.emit(self.savedir, self.get_name(), self.parameters['SQUID Num.'])
        except:
            err = "Cannot initilize files for recording variables. "
            err += "Likely the starting parameters were not setup correctly."
            raise ValueError(err)
    #
#

class CalibrationRecipe(Recipe):
    def setup(self, defaults):
        '''
        Setup the recipe by loading defaults or information from previous depositions and getting user
        input. This function returns a Step object which is used to get the initial parameters in the
        user interface. Add parameter to it using Step.add_input_param then at startup the sequencer
        will automatically pass this step to the user interface and subsequently load the values into
        Recipe.parameters, a dictionary containg the parameters as {name:value}.  Use limits on
        numerical values to make sure no equipment breaking values are entered.

        To preserve insertion order and load in defaults when overloading, always call the superclass
        constructor before adding any parameters, i.e. the first line should be super().__init__(step, defaults)

        Args:
            defaults (dict) : a dictionary containg the previous parameters as {name:value}, to use as
                defaults. This dictionary is loaded and default values can be accessed using
                Recipe.default("Param Name") which will return the default or None if there is no such
                default parameter.
        '''
        if defaults is None:
            self.defaultParams = {}
        else:
            self.defaultParams = defaults
        setupstep = Step(instructions="Press Start to proceed.")

        # Basic paramters that should be included for all recipies
        setupstep.add_input_param("Person Calibrating")
        return setupstep
    #

    def _process_startup(self, startupstep):
        """
        Loads the startup parameters into Recipe.parameters, doesn't start recording.
        """
        self.parameters = dict()
        for k in startupstep.input_param_values.keys():
            self.parameters[k] = startupstep.input_param_values[k]

        # Maybe put some calibration data somewhere in the future?

        # try:
        #     self.equip.initRecordSignal.emit(self.savedir, self.get_name(), self.parameters['SQUID Num.'])
        # except:
        #     err = "Cannot initilize files for recording variables. "
        #     err += "Likely the starting parameters were not setup correctly."
        #     raise ValueError(err)

    def recordVariable(self, variable):
        '''
        Here for compatability
        '''
        print("Warning cannot record variabels in standard format in a calibration run")
        print("Variable", variable, "not recorded.")
    #

class SET_Recipe(Recipe):
    def setup(self, defaults):
        '''
        Setup the recipe by loading defaults or information from previous depositions and getting user
        input. This function returns a Step object which is used to get the initial parameters in the
        user interface. Add parameter to it using Step.add_input_param then at startup the sequencer
        will automatically pass this step to the user interface and subsequently load the values into
        Recipe.parameters, a dictionary containg the parameters as {name:value}.  Use limits on
        numerical values to make sure no equipment breaking values are entered.

        To preserve insertion order and load in defaults when overloading, always call the superclass
        constructor before adding any parameters, i.e. the first line should be super().__init__(step, defaults)

        Args:
            defaults (dict) : a dictionary containg the previous parameters as {name:value}, to use as
                defaults. This dictionary is loaded and default values can be accessed using
                Recipe.default("Param Name") which will return the default or None if there is no such
                default parameter.
        '''
        if defaults is None:
            self.defaultParams = {}
        else:
            self.defaultParams = defaults
        setupstep = Step(instructions="Enter Tip and Deposition parameters")

        # Basic paramters that should be included for all recipies
        setupstep.add_input_param("SET Num.")
        setupstep.add_input_param("Person Evaporating")
        setupstep.add_input_param("Metal", default=self.default("Metal") )
        setupstep.add_input_param("SEM Diameter")
        setupstep.add_input_param("Tip to Leads Distance")
        setupstep.add_input_param("TF Aligned")
        return setupstep
    #

    def _process_startup(self, startupstep):
        """
        Loads the startup parameters into Recipe.parameters and initilizes recording in the equipment
        handeler.
        """
        self.parameters = dict()
        for k in startupstep.input_param_values.keys():
            self.parameters[k] = startupstep.input_param_values[k]

        try:
            self.equip.initRecordSignal.emit(self.savedir, self.get_name(), self.parameters["SET Num."])
        except:
            err = "Cannot initilize files for recording variables. "
            err += "Likely the starting parameters were not setup correctly."
            raise ValueError(err)
    #
#
