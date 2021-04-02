'''
A module for defining tip deposition recipes generically
'''

from exceptions import ProcessInterruptionError, ProcessTimeoutError
from time import sleep

from datetime import datetime, timedelta

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
    - setup() defines the initial parameters of the recipe.
    - proceed() which is a generator that yields each step, defined by a Step object to the sequencer
      and receives input back from the user interface when appropriate. This is the main process by
      which recipes are executed.
    - shutdown() attempts to shutdown the process, either at the end or early if there is a problem
      use it to make sure the equipment returns to a normal state.
    Each function has comments and shows an example, familiarize yourself with the prototypes and
    how to use the Step objects before attempting to make a Recipe.
    '''

    def __init__(self, equip, required_servers=None, version="1.0.0"):
        '''
        Class initilizer, inhert and extend with any needed features then call the superclass initilizer
        i.e. super().__init__(equip, required, version_number)
        where:
        - equip is the equipment handler object and should be the first argument of your initilizer.
        - required is a list of the server names (keys to the servers dictionary) that your recipe needs.
          be sure to add all relevant equipment to this.
        - version is the version number of the recipe, if major changes are made to a recipe increment
          the version number and a new record of parameters will automatically be logged seperatly from
          any previous runs, elimiating potential compatability issues.
        '''
        self.name = type(self).__name__.replace("_"," ")
        self.version = version
        self.abort = False # Calling Sequencer.abortSlot will set this to false and stop current process
        self.pause = False

        # Checks that all the equipment needed to carry out the recipe is in servers
        '''
        Connect to the equipment handler and validate all the servers
        '''
        self.equip = equip
        if required_servers is not None:
            self.equip.verifySignal.emit(required_servers)
        #

    #

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
    def setup(self, defaults):
        if defaults is None:
            self.defaultParams = {}
        else:
            self.defaultParams = defaults
        setupstep = Step(instructions="Enter Tip and Deposition parameters")

        # Add Parameters, by default parameters are strings
        setupstep.add_input_param("SQUID Num.")

        # Add a default value, which may be loaded from previous
        setupstep.add_input_param("Person Evaporating")

        # Can also have users select from a list of options using
        setupstep.add_input_param("Superconductor", default=self.default("Superconductor") )#, options=["Lead", "Indium"])

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

        For reference Recipe.parameters is a dictionary containg the parameters defined at startup
        as {name:value}.
        '''
        # # Define numerical input using limits on the values for safety, even if it is a wide range
        # # if there are limits the GUI will automatically treat it as a number instead of a string.
        # setupstep.add_input_param("Diameter", default=100.0, limits=(10.0,1000.0))

        # # Numerical inputs can be integers, using the isInt option
        # setupstep.add_input_param("Num. Depositions", default=3, limits=(1,10), isInt=True)

        # Can also have users select from a list of options using
        # setupstep.add_input_param("Superconductor", default=self.default("Superconductor") )#, options=["Lead", "Indium"])
        yield "Your Steps go here"
    #

    def shutdown(self):
        '''
        Attempts to shutdown any relevant equipment and put the system on standby. Either
        part of normal shutdown or in the event of an unexpected error. Overload to protect
        critical equipment.
        '''
        pass
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

    def wait_for(self, minutes):
        ''' Sleep the recipe for a specified number of minutes. Still check for aborts. '''
        stoptime = datetime.now() + timedelta(minutes=minutes)
        while stoptime > datetime.now():
            sleep(0.05)
            if self.abort:
                raise ProcessInterruptionError
            elif self.pause: # If paused, wait
                while self.pause:
                    sleep(0.01)
    #

    def wait_until(self, variable, state, conditional="less than", timeout=100):
        '''
        Sleep the recipe until a variable meets a ceratin condition or until it
        times out.

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

        while not comparitor(self.equip.info[variable]):
            sleep(0.05)
            if self.abort:
                raise ProcessInterruptionError
            elif self.pause: # If paused, wait
                while self.pause:
                    sleep(0.01)
            if datetime.now() > stoptime:
                raise ProcessTimeoutError
    #

    def command(self, server, command, args=None, wait=True):
        '''
        Send a command to a LabRAD server through the equipment handler.

        Args:
            server (str) : The name of the LabRAD server to get the value from
            command (str): The name function (in the namespace of that server, i.e.
                getattr(server, accessor) gives the function)
            args (list) : A list containing the arguments of the command and the
                keyword arguments, which will be used to call the server using
                server.command(*args). If None, no arguments will be sent
            wait (bool) : If True will wait 0.1 seconds after sending the signal to allow
                the equipment handler and servers to catch up.
        '''
        if args is None:
            self.equip.commandSignal.emit(server, command, [])
        else:
            self.equip.commandSignal.emit(server, command, args)
        if wait:
            sleep(0.1) # give the program a little time to catch up
    #

    def trackVariable(self, name, server, accessor, wait=True):
        '''
        Send a signal to the equipment handler to track a varaible.

        Args:
            name (str) : The name of the variable, which will function as the key to access it.
            server (str) : The name of the LabRAD server to get the value from
            accessor (str): The accessor function (in the namespace of that server, i.e.
                getattr(server, accessor) gives the function) to get the value must return
                one floating point number.
            wait (bool) : If True will wait a 0.1 seconds after sending the signal
                to allow the equipment handler and servers to catch up.
        '''
        self.equip.trackSignal.emit(name, server, accessor)
        if wait:
            sleep(0.1) # give the program a little time to catch up
    #


    def _process_startup(self, startupstep):
        """
        Loads the startup parameters into Recipe.parameters
        """
        self.parameters = dict()
        for k in startupstep.input_param_values.keys():
            self.parameters[k] = startupstep.input_param_values[k]
    #
#

if __name__ == '__main__':
    pass
