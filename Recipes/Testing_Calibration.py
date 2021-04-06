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
        self.trackVariable('DummyVar', 'dummy', 'query')
        self.trackVariable('DummyOutput', 'dummy', 'get_output')
        self.plotVariable("DummyVar")

        step4 = Step(True, "Confirm Parameters")
        step4.add_input_param("coefficient", default=self.default("coefficient"), limits=(0,10))
        step4.add_input_param("alpha", default=self.default("alpha"), limits=(0,1))
        yield step4
        params = step4.get_all_params()
        self.command('dummy', 'set_coefficient', params['coefficient'])
        self.command('dummy', 'set_alpha', params['alpha'])

        step5 = Step(True, "Setup Feedback")
        step5.add_input_param("setpoint", default=self.default("setpoint"), limits=(0,100))
        step5.add_input_param("P", default=self.default("P"), limits=(0,100))
        step5.add_input_param("I", default=self.default("I"), limits=(0,100))
        step5.add_input_param("D", default=self.default("D"), limits=(0,100))
        yield step5
        setpoint = step5.get_param('setpoint')


        self.PIDLoop('DummyVar', 'dummy', 'set_output', step5.get_param('P'), step5.get_param('I'), step5.get_param('D'), setpoint, 0.0, (0,100))

        yield Step(False, "Testing feedback, wait 1 min")
        self.wait_for(1)

        yield Step(False, "Stopping Feedback")
        self.stopPIDLoop('DummyVar')

        # self.command('dummy', 'set_output', setpoint)
        # yield Step(False, "Waiting until output reaches " + str(setpoint))
        # self.wait_until('DummyVar', setpoint, conditional='greater than')


        finalstep = Step(True, "All Done. Press proceed to end.")
        yield finalstep

    #

    def shutdown(self):
        self.command('dummy', 'reset', None)
        super().shutdown()
    #
#
