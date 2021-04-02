'''
Generic recipes for testing and calibration of equipment.
'''

from recipe import Recipe, Step

#from time import sleep

class Sequencer_Unit_Test(Recipe):

    def __init__(self, equip):
        super().__init__(equip, required_servers=['dummy'])

    def proceed(self):
        self.trackVariable('Time', 'dummy', 'get_time')

        # step1 = Step(False, "Testing the timing code. Waiting for 6 s.")
        # yield step1
        #
        # self.wait_for(0.1)

        # step2 = Step(True, "Ready to try Labrad server commands.")
        # yield step2
        #
        # self.command('stopwatch', 'start_timer', None)
        # self.trackVariable('Stopwatch', 'stopwatch', 'get_time')
        #
        # step3 = Step(False, "Testing the stopwatch code. Waiting for 6 s.")
        # yield step3
        # self.wait_until('Stopwatch', 6, conditional='greater than')
        #

        self.command('dummy', 'reset', None)
        self.trackVariable('DummyOutput', 'dummy', 'query')

        step4 = Step(True, "Testing out a dummy piece of hardware")
        # step4.add_input_param("coefficient", default=self.default("coefficient"), limits=(0,10))
        # step4.add_input_param("alpha", default=self.default("alpha"), limits=(0,1))
        yield step4
        # params = step4.get_all_params()
        # C = params['coefficient']
        # alpha = params['alpha']
        # self.command


        finalstep = Step(True, "All Done")
        yield finalstep

    #
#
