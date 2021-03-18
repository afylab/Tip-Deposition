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
        return super().setup(None)
    #

    def proceed(self):
        step1 = Step(False, "You must answer me these questions three, err the other side ye see")

        yield step1
        sleep(1)

        step2 = Step(True, "Ask me the questions bridgekeeper, Im not afraid")
        yield step2
        sleep(1)

        step3 = Step(True, "What is your name?")
        step3.add_input_param("YourName")
        yield step3
        sleep(1)

        step4 = Step(True, "What if your quest?")
        step4.add_input_param("YourQuest", default="To seek the Holy Grail")
        yield step4
        sleep(1)

        step5 = Step(True, "What if your favorite color?")
        step5.add_input_param("FavColor", options=["Blue", "Blue, No Yellow"])
        yield step5
        sleep(1)
    #
#
