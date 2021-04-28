'''
A simple thermal evaporation using only the thermal evaporator and the cryogenic insert.

'''

from recipe import Recipe, Step

class Cryo_Thermal_Evaporation(Recipe):
    def __init__(self, equip):
        # Add all the hardwave servers needed for evaporation

        # Starting iwth the servers you always need, including 'data_vault'
        servers = ['data_vault', 'stepper_server', 'rvc_server', 'valve_relay_server', 'ftm_server']

        # Then evaporation specific servers
        servers.append('power_supply_server')

        super().__init__(equip, required_servers=servers, version="1.0.0")
    #

    def proceed(self):
        '''
        Initilize Servers with any setup needed. Devices communicating over the
        labRAD serial server need to be selected.

        Following the initilization from the old Evaporator software, with any comments
        '''
        self.command('rvc_server', 'select_device')
        self.command('stepper_server', 'select_device')
        self.command('ftm_server', 'select_device')
        #
        # # Setup the power supply server
        self.command('power_supply_server', 'select_device')
        self.command('power_supply_server', 'adr', '6')
        self.command('power_supply_server', 'rmt_set', 'REM')
        #
        self.command('valve_relay_server', 'select_device')
        # #Iden command added so that arduino will respond to first command given from GUI.
        # #Lack of response is somehow connected to dsrdtr port connection, but not yet sure how...
        self.command('valve_relay_server', 'iden')

        '''
        Track the variables
        '''
        self.trackVariable('Pressure', 'rvc_server', 'get_pressure_mbar', units='mbar')
        self.trackVariable('Deposition Rate', 'ftm_server', 'get_sensor_rate')
        self.trackVariable('Thickness', 'ftm_server', 'get_sensor_thickness')
        self.trackVariable('Voltage', 'power_supply_server', 'volt_read', units='V')

        self.plotVariable("Pressure")
        self.plotVariable('Deposition Rate')

        '''
        !!!!!!!!!!!!!!
        For Debugging
        !!!!!!!!!!!!!!
        '''

        yield Step(True, "Press Proceed to continue")

        '''
        Get parameters from the user
        '''
        instruct = "Follow instructions for tip loading, confirm that:"
        instruct += "\n 1. The tip is loaded"
        instruct += "\n 2. The evaporation boat has been loaded with 6-7 pellets of superconductor."
        instruct += "\n 3. the evaporator is sealed and ready for pump out."
        instruct += "\n Confirm parameters below and press proceed to begin pumping out."
        step1 = Step(True, instruct)
        step1.add_input_param("Deposition Rate (A/s)", default=self.default("Deposition Rate (A/s)"), limits=(0,10))
        step1.add_input_param("Therm. Time 1", default=self.default("Therm. Time 1"), limits=(0,100))
        step1.add_input_param("Therm. Time 2", default=self.default("Therm. Time 2"), limits=(0,100))
        step1.add_input_param("He Pressure (mbar)", default=self.default("He Pressure (mbar)"), limits=(1e-9,1000))
        step1.add_input_param("Contact Thickness (A)", default=self.default("Contact Thickness (A)"), limits=(10,500))
        step1.add_input_param("Head Thickness (A)", default=self.default("Head Thickness (A)"), limits=(10,500))

        step1.add_input_param("P", default=self.default("P"), limits=(0,1))
        step1.add_input_param("I", default=self.default("I"), limits=(0,1))
        step1.add_input_param("D", default=self.default("D"), limits=(0,1))

        step1.add_input_param("Vmax", default=self.default("Vmax"), limits=(0,10))
        step1.add_input_param("Voffset", default=self.default("Voffset"), limits=(0,10))
        yield step1

        params = step1.get_all_params()
        #print(params['Deposition Rate (A/s)'])

        step2 = Step(True, "Record the Crystal Life")
        step2.add_input_param("Crystal Life", limits=(0,100))
        yield step2

        '''
        Pump out sequence
        '''

        # Access data from step1 and initilize servers with information
        yield Step(False, "Beginning pump out sequence, waiting until pressure falls below 1E-6 mbar.")

        ## First rough out the chamber with the scroll pump
        self.valve('all', True) # Open all the valves
        self.pump('scroll', True)
        self.wait_until('Pressure', 1e-1, "less than")

        ## Close the Chamber valve
        self.valve('chamber', False)
        self.pump('turbo', True)

        self.wait_until('Pressure', 1e-2, "less than")

        yield Step(True, "Close external Helium line valve 5.")
        self.wait_until('Pressure', 1e-6, "less than")

        yield Step(False, "Base pressure reached. Flowing Helium, wait 5 minutes for flow to stabalize.")
        self.leakvalve(True, pressure=5e-3)
        self.wait_for(5)

        '''
        Pump out complete, calibrate the evaporation voltage
        '''

        # Calibrate the voltage needed to reach set deposition rate
        yield Step(True, "Rotate Tip to 165&deg;.")

        yield Step(False, "Calibrating voltage to reach deposition rate.")

        # Voltage calibration  <--------
        setpoint = 0.0
        self.PIDLoop('DummyVar', 'testserver', 'set_output', params('P'), params('I'), params('D'), setpoint, 0.0, (0,100))

        yield Step(True, "Ready for cooldown, follow cooldown instructions then press proceed.")

        yield Step(False, "Wait until stable cryostat temperature is reached. Adjust the helium flow to acheive desired stability.")

        # Deposit the first contact
        yield Step(False, "Beginning thermalization, waiting 20 min")
        self.wait_for(20)

        yield Step(True, "Rotate Tip to 90&deg;.")

        yield Step(False, "Beginning first contact deposition.")

        # Contact Depositon Step <--------

        yield Step(False, "First contact deposition finished")

        # Deposit the SQUID head
        yield Step(False, "Beginning thermalization, waiting 10 min")
        self.wait_for(10)

        yield Step(True, "Rotate Tip to 345&deg;.")

        yield Step(False, "Beginning head deposition.")

        # Contact Depositon Step <--------

        yield Step(False, "Head deposition finished")

        # Deposit the second contact
        yield Step(False, "Beginning thermalization, waiting 10 min")
        self.wait_for(10)

        yield Step(True, "Rotate Tip to 240&deg;.")

        yield Step(False, "Beginning second contact deposition.")

        # Contact Depositon Step <--------

        yield Step(False, "Second contact deposition finished")

        # Warm up procedure
        yield Step(True, "Deposition Finished. Follow warm up procedure.")

        yield Step(True, "Press proceed to shut down vacuum system.")

        #
        self.valve('all', False) # close all valves
        self.pump('all', False) # Turn off all the pumps
        yield Step(True, "Turbo spinning down, gently open turbo vent bolt for proper spin-down.")

        # Stop updating the plots of the tracked varaibles
        self.wait_for(0.1)
        self.stopPlotting("Pressure")
        self.stopPlotting('Deposition Rate')

        finalstep = Step(False, "All Done.")
        yield finalstep

    #
#
