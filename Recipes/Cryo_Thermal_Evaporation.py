'''
A simple thermal evaporation using only the thermal evaporator and the cryogenic insert.

'''

from recipe import Recipe, Step

class Cryo_Thermal_Evaporation(Recipe):
    def __init__(self, equip):
        # Add all the hardwave servers needed for evaporation, including 'data_vault'
        # Starting iwth the servers you always need, including Data Vault
        # servers = ['data_vault', 'serial_server', 'stepper_server', 'rvc_server', 'valve_relay_server', 'ftm_server', 'turbo450']
        # Then evaporation specific servers
        # servers.append(['power_supply_server'])
        servers = ['data_vault', 'rvc_server']# FOR DEBUGGING
        super().__init__(equip, required_servers=servers, version="1.0.0")
    #

    def proceed(self):
        '''
        Initilize Servers with any setup needed.

        Following the initilization from the old Evaporator software, with any comments
        '''
        self.command('rvc_server', 'select_device')
        # self.command('stepper_server', 'select_device')
        # self.command('ftm_server', 'select_device')
        # self.command('turbo450', 'select_device')
        #
        # # Setup the power supply server
        # self.command('power_supply_server', 'select_device')
        # self.command('power_supply_server', 'adr', '6')
        # self.command('power_supply_server', 'rmt_set', 'REM')
        #
        # self.command('valve_relay_server', 'select_device')
        # #Iden command added so that arduino will respond to first command given from GUI.
        # #Lack of response is somehow connected to dsrdtr port connection, but not yet sure how...
        # self.command('valve_relay_server', 'iden')

        '''
        Track the variables
        '''
        self.trackVariable('Pressure', 'rvc_server', 'get_nom_prs')
        # self.trackVariable('Deposition Rate', 'ftm_server', 'get_sensor_rate')
        # self.trackVariable('Thickness', 'ftm_server', 'get_sensor_thickness')
        # self.trackVariable('Voltage (V)', 'power_supply_server', 'volt_read')
        # self.trackVariable('Temperature (C)', 'turbo450', 'temperature')
        # self.trackVariable('Frequency (Hz)', 'turbo450', 'csfrequency')
        # self.trackVariable('Current (0.1 A)', 'turbo450', 'mcurrent')

        # self.plotVariable("Pressure")
        # self.plotVariable('Temperature (C)')

        '''
        !!!!!!!!!!!!!!
        For Debugging
        !!!!!!!!!!!!!!
        '''

        yield Step(True, "Press Proceed to continue")

        # '''
        # Get parameters from the user
        # '''
        # instruct = "Follow instructions for tip loading, confirm that:"
        # instruct += "\n 1. The tip is loaded"
        # instruct += "\n 2. The evaporation boat has been loaded with 6-7 pellets of superconductor."
        # instruct += "\n 3. the evaporator is sealed and ready for pump out."
        # instruct += "\n Confirm parameters below and press proceed to begin pumping out."
        # step1 = Step(True, instruct)
        # step1.add_input_param("Deposition Rate (A/s)", default=self.default("Deposition Rate (A/s)"), limits=(0,10))
        # step1.add_input_param("Therm. Time 1", default=self.default("Therm. Time 1"), limits=(0,100))
        # step1.add_input_param("Therm. Time 2", default=self.default("Therm. Time 2"), limits=(0,100))
        # step1.add_input_param("He Pressure (mbar)", default=self.default("He Pressure (mbar)"), limits=(1e-9,1000))
        # step1.add_input_param("Contact Thickness (A)", default=self.default("Contact Thickness (A)"), limits=(10,500))
        # step1.add_input_param("Head Thickness (A)", default=self.default("Head Thickness (A)"), limits=(10,500))
        #
        # step1.add_input_param("P", default=self.default("P"), limits=(0,1))
        # step1.add_input_param("I", default=self.default("I"), limits=(0,1))
        # step1.add_input_param("D", default=self.default("D"), limits=(0,1))
        #
        # step1.add_input_param("Vmax", default=self.default("Vmax"), limits=(0,10))
        # step1.add_input_param("Voffset", default=self.default("Voffset"), limits=(0,10))
        # yield step1
        #
        # params = step1.get_all_params()
        # #print(params['Deposition Rate (A/s)'])
        #
        # step2 = Step(True, "Record the Crystal Life")
        # step2.add_input_param("Crystal Life", limits=(0,100))
        # yield step2
        #
        # # Access data from step1 and initilize servers with information
        #
        # yield Step(False, "Beginning pump out sequence, waiting until pressure falls below 1E-6 mbar.")
        #
        # '''
        # DEV NOTE: Check the valve server, it has return values that will need to be adjusted
        # to our scheme for monitoring valve status.
        # '''
        #
        # # Open all the valves
        # self.command('valve_relay_server', 'gate_open')
        # self.command('valve_relay_server', 'chamber_valve_open')
        # self.command('valve_relay_server', 'turbo_valve_open')
        #
        # # First rough out the chamber with the scroll pump
        # self.command('valve_relay_server', 'scroll_on')
        # self.wait_until('Pressure', 1e-1, "less than")
        #
        # # Close the Chamber valve
        # self.command('valve_relay_server', 'chamber_valve_close')
        # self.command('valve_relay_server', 'turbo_on')
        #
        #
        # yield Step(True, "Ready for cooldown, follow cooldown instructions then press proceed.")
        #
        # yield Step(False, "Waiting until stable temperature is reached.")
        #
        # # Wait until base temperature is reached.
        # self.wait_until('Temperature (C)', 7, "less than")
        #
        # yield Step(True, "Adjust the helium flow to acheive desired stability.")
        #
        # # Calibrate the voltage needed to reach set deposition rate
        # yield Step(True, "Rotate Tip to 165&deg;.")
        #
        # yield Step(False, "Calibrating voltage to reach deposition rate.")
        #
        # # Voltage calibration code <--------
        #
        # # Deposit the first contact
        # yield Step(False, "Beginning thermalization, waiting 20 min")
        # self.wait_for(20)
        #
        # yield Step(True, "Rotate Tip to 90&deg;.")
        #
        # yield Step(False, "Beginning first contact deposition.")
        #
        # # Contact Depositon Step <--------
        #
        # yield Step(False, "First contact deposition finished")
        #
        # # Deposit the SQUID head
        # yield Step(False, "Beginning thermalization, waiting 10 min")
        # self.wait_for(10)
        #
        # yield Step(True, "Rotate Tip to 345&deg;.")
        #
        # yield Step(False, "Beginning head deposition.")
        #
        # # Contact Depositon Step <--------
        #
        # yield Step(False, "Head deposition finished")
        #
        # # Deposit the second contact
        # yield Step(False, "Beginning thermalization, waiting 10 min")
        # self.wait_for(10)
        #
        # yield Step(True, "Rotate Tip to 240&deg;.")
        #
        # yield Step(False, "Beginning second contact deposition.")
        #
        # # Contact Depositon Step <--------
        #
        # yield Step(False, "Second contact deposition finished")
        #
        # # Warm up procedure
        # yield Step(True, "Deposition Finished. Follow warm up procedure.")

        # Stop updating the plots of the tracked varaibles
        # self.stopPlotting("Pressure")
        # self.stopPlotting('Temperature (C)')

        finalstep = Step(False, "All Done.")
        yield finalstep

    #
#
