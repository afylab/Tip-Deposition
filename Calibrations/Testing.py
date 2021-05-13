'''
Generic recipes for testing and calibration of equipment.
'''

from recipe import CalibrationRecipe, Recipe, Step

class Recipe_Test(Recipe):
    '''
    A simple recipe to test the core functions of the Recipe. Generally when making a new type of
    nanoSQUID tip the workflow is as follows:
    - Make LabRAD servers for any new hardware
    - Make a new Recipe class, inheriting from Recipe, to handle the deposition procedure
    - Iterate on the process and parameters in order to find the optimum steps

    Comments are the code are very explicit to give a worked example of how to develop a new Recipe
    class for new users. All core recipe functions are detailed below.
    '''

    def __init__(self, *args):
        '''
        The initilizer setups the recipe, normally the only thing needed is to call the superclass
        initilizer with the list of required servers and a version number. The program will check
        that the required servers are present.

        The version number should be incremented whenever there is a significant change, in order to
        keep track of new iterations of the recipe. In particular, if the number of recorded parameters
        is changed without changing the version number there may be issues loading and saving parameters
        to file.
        '''
        super().__init__(*args, required_servers=['data_vault','testserver'], version="1.0.1")

    def proceed(self):
        '''
        Proceed is the main function of the Recipe object, it is a generator that is called at each
        step in the recipe and contains functions communicating with all the equipment and defining
        what variables to track, record and display.
        '''

        ''' --- Startup operations --- '''

        # Pass commands to a server using the command functions
        # command(server, function_name, function_arguments)
        # function_arguments can be a string, float, list or None
        self.command('testserver', 'reset', None)

        # Track the variables that you want to track on the interface
        # trackVariable(name, server, accessor_function)
        # The accessor function takes no arguments and returns the given value
        self.trackVariable('DummyVar', 'testserver', 'query')
        self.trackVariable('DummyOutput', 'testserver', 'get_output')

        # Variables can be plotted on the interface using the plotVariable function, but they need
        # to be tracked first
        self.plotVariable("DummyVar")
        self.plotVariable("DummyOutput")

        # You can record a variable to the Data Vault using the recordVariable function
        self.recordVariable("DummyVar")
        self.recordVariable("DummyOutput")

        ''' --- Main Operation --- '''

        # Give instructions to the user and get feedback using the Step object. The first two arguments
        # are Step(user_input, instructions) where user_input is a boolean which if True will cause
        # the program to wait for user input (which can be as simple as pressing the proceed button)
        # The instructions are displayed to the user in the process window.
        step1 = Step(False, "Testing the timing code. Waiting for 6 s.")
        # After the step is defined send it out for processing using the yield keyword. If a Step is
        # not yielded it is not processed.
        yield step1

        # Wait for a specific amount of time using the wait_for function
        # wait_for(minutes) where the interval is measured in minutes
        self.wait_for(0.1)

        # Get parameters from the user using the Step.add_input_param function, each parameter
        # should have a unique name, and may have a default value (the parameters loaded from a
        # previous run are accessible using the default function) or numerical limits that the
        # value must fall between.
        step2 = Step(True, "Confirm Parameters")
        step2.add_input_param("coefficient", default=self.default("coefficient"), limits=(0,10))
        step2.add_input_param("alpha", default=self.default("alpha"), limits=(0,1))
        yield step2
        params = step2.get_all_params() # retreive all of the parameters into a dictionary

        # Setup the server with the parameters
        self.command('testserver', 'set_coefficient', params['coefficient'])
        self.command('testserver', 'set_alpha', params['alpha'])

        # The program can hold a parameter in feedback using a PID loop, to do this, get the PID parameters
        # then call the PIDLoop function with the following arguments:
        # PIDLoop(trackedVar, server, outputFunc, P, I, D, setpoint, offset, minMaxOutput)
        # For more information see the function documentation
        step3 = Step(True, "Setup Feedback")
        step3.add_input_param("setpoint", default=self.default("setpoint"), limits=(0,100))
        step3.add_input_param("P", default=self.default("P"), limits=(0,100))
        step3.add_input_param("I", default=self.default("I"), limits=(0,100))
        step3.add_input_param("D", default=self.default("D"), limits=(0,100))
        yield step3
        setpoint = step3.get_param('setpoint')
        self.PIDLoop('DummyVar', 'testserver', 'set_output', step3.get_param('P'), step3.get_param('I'), step3.get_param('D'), setpoint, 0.0, (0,100))

        yield Step(False, "Testing feedback, wait 30s")
        self.wait_for(0.5)

        yield Step(False, "Pausing feedback, wait 30s")
        self.pausePIDLoop("DummyVar")
        self.wait_for(0.5)

        yield Step(False, "Resuming feedback after 20 seconds")
        self.resumePIDLoop("DummyVar", 20.0)
        self.wait_for(2.0/6)

        yield Step(False, "Output Resumed, wait 20s")
        self.wait_for(2.0/6)

        yield Step(False, "Stopping Feedback")
        self.stopPIDLoop('DummyVar') # Stop the feedback on the varaible "DummyVar"

        # We can also haev the program wait untill a specific condition is met, in the below example
        # setting the feedback zeros the output and we want to wait until "DummyVar" falls below
        # 1.0, then we can stop recording. To do this use the wait_until function where the program
        # will wait for a certain condition to be met, many different conditions can be specified
        # see the wait_until function docstring for more information.
        yield Step(False, "Waiting until DummyVar is below 1")
        self.wait_until('DummyVar', 1.0, conditional='less than')

        self.stopRecordingVariable("DummyVar") # Stop recording the values of the varaible "DummyVar"

        # Stop updating the plots of the tracked varaibles
        self.stopPlotting("DummyVar")
        self.stopPlotting("DummyOutput")

        finalstep = Step(False, "All Done.")
        yield finalstep
    #

    def shutdown(self):
        '''
        The shutdown function is here to ensure that equipment is reset to a safe state after the
        process is done, even if the recipe is aborted or ends unexpectedly due to an error.
        '''
        self.command('testserver', 'reset', None)
        super().shutdown() # call the superclass shutdown sequence which will stop all feedback and recording
    #
#

class Timing_Test(CalibrationRecipe): # A simple class for debugging timing issues in the serial ports
    def __init__(self, equip, updateSig):
        equip.toggleDebugMode()
        super().__init__(equip, updateSig, required_servers=['data_vault','valve_relay_server','rvc_server', 'ftm_server', 'power_supply_server'], version="1.0.1")
    #

    def proceed(self):
        """
        Below add all the servers and plots you would in a normal evaporation, but don't atually do
        anything with the equipment. Timing information will be printed out to the terminal by the equipment handler
        """
        self.command('rvc_server', 'select_device')
        self.command('valve_relay_server', 'select_device')
        # #Iden command added so that arduino will respond to first command given from GUI.
        # #Lack of response is somehow connected to dsrdtr port connection, but not yet sure how...
        self.command('valve_relay_server', 'iden')


        self.command('evaporator_shutter_server', 'select_device')
        self.command('ftm_server', 'select_device')
        #
        # # Setup the power supply server
        self.command('power_supply_server', 'select_device')
        self.command('power_supply_server', 'adr', '6')
        self.command('power_supply_server', 'rmt_set', 'REM')

        self.trackVariable('Pressure', 'rvc_server', 'get_pressure_mbar', units='mbar')
        self.trackVariable('Deposition Rate', 'ftm_server', 'get_sensor_rate', units='(A/s)')
        self.trackVariable('Thickness', 'ftm_server', 'get_sensor_thickness', units='A')
        self.trackVariable('Voltage', 'power_supply_server', 'volt_read', units='V')
        self.wait_for(0.01) # Here because it threw an error one time
        self.plotVariable("Pressure", logy=True)
        self.plotVariable('Deposition Rate')
        #
        yield Step(True, "Testing update timing")

        # Stop updating the plots of the tracked varaibles
        self.stopPlotting("Pressure")
        self.stopPlotting('Deposition Rate')

        finalstep = Step(False, "All Done.")
        yield finalstep
    #

class Vacuum_Test(CalibrationRecipe):
    """
    Tests the pump out sequence of the vacuum system.
    """
    def __init__(self, *args):
        super().__init__(*args, required_servers=['data_vault','valve_relay_server','rvc_server'])
    #

    def proceed(self):
        self.command('rvc_server', 'select_device')
        self.command('valve_relay_server', 'select_device')
        # #Iden command added so that arduino will respond to first command given from GUI.
        # #Lack of response is somehow connected to dsrdtr port connection, but not yet sure how...
        self.command('valve_relay_server', 'iden')

        self.trackVariable('Pressure', 'rvc_server', 'get_pressure_mbar', units='mbar')
        self.wait_for(0.01)
        self.plotVariable("Pressure", logy=True)

        """
        Pump out process
        """
        yield Step(True, "Ready for pump out.")

        ## First rough out the chamber with the scroll pump
        self.valve('all', True) # Open all the valves

        yield Step(True, "Valves opened, ready for rough-out")

        self.leakvalve(True)
        self.pump('scroll', True)
        self.wait_until('Pressure', 6e-2, "less than")

        ## Close the Chamber valve
        self.valve('chamber', False)
        self.pump('turbo', True)

        self.wait_until('Pressure', 1e-2, "less than")

        yield Step(True, "Close external Helium line valve 5.")
        yield Step(False, "Pumping down to base pressure.")
        self.leakvalve(False)
        self.wait_until('Pressure', 5e-6, "less than")

        # yield Step(False, "Base pressure reached. Flowing Helium, wait 5 minutes for flow to stabalize.")
        # self.leakvalve(True, pressure=5e-3)
        # self.wait_for(5)

        '''
        Pump out complete, uncomment to include spin-down
        '''
        # yield Step(True, "Press proceed to close valves.")
        # self.valve('all', False) # close all valves
        # self.wait_for(0.1)
        # self.pump('all', False) # Turn off all the pumps
        # yield Step(True, "Turbo spinning down, gently open turbo vent bolt for proper spin-down.")
        #
        # self.leakvalve(True)
        # self.wait_for(0.1)

        # Stop updating the plots of the tracked quantities
        self.stopPlotting("Pressure")
        self.stopTracking('all')

        finalstep = Step(False, "All Done. Leak valve open, vent the chamber and retreive your SQUID!")
        yield finalstep
    #
