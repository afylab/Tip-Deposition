'''
Generic recipes for testing and calibration of equipment.
'''

from recipe import Recipe, Step

from time import sleep

class Sequencer_Unit_Test(Recipe):
    def __init__(self):
        super().__init__([], [])
    #

    def setup(self):
        setupstep = Step(instructions="Enter Tip and Deposition parameters")

        # ADD YOUR PARAMETERS HERE, FOR EXAMPLE
        setupstep.add_input_param("Example1", default=1.0, limits=(0,5))
        #They can be strings instead of number, for example
        setupstep.add_input_param("TuningFork", default="green")
        #Can also have users select from a list of options using
        setupstep.add_input_param("OptionExample", default="option1", options=["option1", "option2", "option3"])

        return setupstep
    #

    def proceed(self):
        step1 = Step(False, "You must answer me these questions three, err the other side ye see")
        yield step1
        print("processing step 1")
        sleep(1)
        print("Done")

        step2 = Step(True, "Ask me the questions bridgekeeper, Im not afraid")
        yield step2
        print("processing step 2")
        sleep(1)
        print("Done")
    #
#
