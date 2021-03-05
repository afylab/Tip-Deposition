'''
A module for defining tip deposition recipes generically
'''

class Step():
    '''
    Feedback from the recipe to the sequencer

    Args:
        user_input (bool) : If user input is required.
    '''
    def __init__(self, user_input=False, instructions=None):
        self.user_input = user_input()
        self.instructions = instructions
    #
#

class Recipe():
    '''
    Generic class for a specific recipe for tip deposition, defines a particular ordering
    of steps as well as any special behavior that is needed to carry out the recipe.

    Main function to inherit and override is proceed() which is a generator that contains
    each step before a yield keyword.

    Recipe parameters are entered on the interface. The interface will automatically load
    the parameters defined in Recipe.recipe_params, a dictionary containg the parameters as
    {name:value}. Define this variable with default values in recipe.__init__ function and
    the previous values may be automatically loaded at startup.

    '''
    def __init__(self):
        '''
        '''
        self.name = type(self).__name__.replace("_"," ")
        self.version = "1.0.0"
    #

    '''
    Checks that all the equipment needed to carry out the recipie
    '''
    def equipment_check(self, servers):
        pass
        # Identify all the keys in the instruction set and check that they are in servers
    #

    '''
    Setup the recipe by loading defaults or information from previous depositions and getting user input

    Overload to enxtend for a particular recipe
    '''
    def setup(self, defaults, previous):
        pass
    #

    '''
    Run the recipe, overload to create a particular recipe
    '''
    def proceed():
        pass
    #
#

if __name__ == '__main__':
    pass
