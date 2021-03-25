'''
A module for defining tip deposition recipes generically
'''

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

    def __init__(self, servers, required_servers=None, version="1.0.0"):
        '''
        Class initilizer, inhert and extend with any needed features then call the superclass initilizer
        i.e. super().__init__(servers, required, version_number)
        where:
        - servers is a list of availible LabRAD servers and should be the first argument of your initilizer.
        - required is a list of the server names (keys to the servers dictionary) that your recipe needs.
          be sure to add all relevant equipment to this.
        - version is the version number of the recipe, if major changes are made to a recipe increment
          the version number and a new record of parameters will automatically be logged seperatly from
          any previous runs, elimiating potential compatability issues.
        '''
        self.name = type(self).__name__.replace("_"," ")
        self.version = version

        # Checks that all the equipment needed to carry out the recipe is in servers
        if required_servers is not None:
            missing = False
            for equip in required_servers:
                if not equip in servers:
                    print("Server " + str(equip) + "not found")
                    missing = True
            if missing:
                raise ValueError("Required LabRAD server not found")
        self.servers = servers

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
        Attempts to shutdown any relevant equipment and put the system on standby. Either part of
        normal shutdown or in the event of an unexpected error.
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
