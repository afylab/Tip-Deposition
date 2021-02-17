'''
Primary module for tip deposition, contains the sequencer at the heart of the program
which handles the backend of executing a recipe.

'''

class Sequencer():
    '''
    Backend of the tip deposition that translates a tip deposition recipe into a sequence
    of hardware commands, checking user input
    '''
    def __init__(self, recipe, servers):
        '''
        Setup the recipe.

        Args:
            recipe : The recipe object to load
            servers : A dictionary ordered with 'equipment-name':labRAD-Server-Reference. The
                key will be used as a generic key to lookup the hardware from Sequencer.servers[key]
        '''
        self.active = False # Parameter is active when a tip is being deposited

        self.recipe = recipe
        self.servers = servers

        # Check that the recipe has all the equipment it needs
        if not self.recipe.equipment_check(self.servers):
            # Manage equipment
            pass

        # Initlize the process window
        # self.gui = ProcessWindow

        # Give the

        # Setup the equipment
    #
#

if __name__ == '__main__':
    pass
