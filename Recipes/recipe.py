'''
A module for defining tip deposition recipes generically
'''

class Recipe():
    '''
    Generic class for a specific recipe for tip deposition, defines a particular ordering
    of steps as well as any special behavior that is needed to carry out the recipe.

    Main function to inherit and override is proceed() which is a generator that contains
    each step before a yield keyword.
    '''
    def __init__(self):
        '''
        '''
        pass
    #

    '''
    Checks that all the equipment needed to carry out the recipie
    '''
    def equipment_check(self, servers):
        pass
        # Identify all the keys in the instruction set and check that they are in servers
    #
#

if __name__ == '__main__':
    pass
