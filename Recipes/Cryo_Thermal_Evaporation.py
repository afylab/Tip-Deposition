'''
A simple thermal evaporation using only the thermal evaporator and the cryogenic insert.
'''

from recipe import Recipe, Step

class Cryo_Thermal_Evaporation(Recipe):
    def __init__(self, *args):
        # Add all the hardwave servers needed for evaporation

        # Starting with the servers you always need, including 'data_vault'
        servers = ['data_vault', 'rvc_server', 'valve_relay_server', 'ftm_server', 'power_supply_server', 'evaporator_shutter_server']


        super().__init__(*args, required_servers=servers, version="1.0.0")
    #

    def proceed(self):
        '''
        Initilize Servers with any setup needed. Devices communicating over the
        labRAD serial server need to be selected.

        Following the initilization from the old Evaporator software, with any comments
        '''
        self.command('rvc_server', 'select_device')
        self.command('valve_relay_server', 'select_device')
        # #Iden command added so that arduino will respond to first command given from GUI.
        # #Lack of response is somehow connected to dsrdtr port connection, but not yet sure how...
        self.command('valve_relay_server', 'iden')


        self.command('evaporator_shutter_server', 'select_device')
        self.command('ftm_server', 'select_device')

        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness
        self.command('ftm_server', 'select_sensor', 1) # Ensure the user has the right crystal selected, in this case 1

        #
        # # Setup the power supply server
        self.command('power_supply_server', 'select_device')
        self.command('power_supply_server', 'adr', '6')
        self.command('power_supply_server', 'rmt_set', 'REM')
        #

        '''
        Track the variables
        '''
        self.trackVariable('Pressure', 'rvc_server', 'get_pressure_mbar', units='mbar')
        self.trackVariable('Deposition Rate', 'ftm_server', 'get_sensor_rate', units='(A/s)')
        self.trackVariable('Thickness', 'ftm_server', 'get_sensor_thickness', units='A')
        self.trackVariable('Voltage', 'power_supply_server', 'act_volt', units='V')
        self.trackVariable('Voltage Setpoint', 'power_supply_server', 'volt_read', units='V')
        self.trackVariable('Current', 'power_supply_server', 'act_cur', units='A')
        self.wait_for(0.01) # Here because it threw an error one time

        self.recordVariable("Pressure")
        self.recordVariable("Deposition Rate")

        '''
        Get parameters from the user
        '''
        instruct = "Follow instructions for tip loading, confirm that:"
        instruct += "\n 1. The tip is loaded"
        instruct += "\n 2. The evaporation boat has been loaded with 6-7 pellets of superconductor."
        instruct += "\n 3. The evaporator is sealed and being pumped on."
        instruct += "\n 4. The correct film has been selected on the FTM-2400."
        instruct += "\n Confirm parameters below and press proceed to begin."
        step1 = Step(True, instruct)
        step1.add_input_param("Deposition Rate (A/s)", default=self.default("Deposition Rate (A/s)"), limits=(0,10))
        step1.add_input_param("Therm. Time 1", default=self.default("Therm. Time 1"), limits=(0,100))
        step1.add_input_param("Therm. Time 2", default=self.default("Therm. Time 2"), limits=(0,100))
        step1.add_input_param("He Pressure (mbar)", default=self.default("He Pressure (mbar)"), limits=(1e-9,1000))
        step1.add_input_param("Contact Thickness (A)", default=self.default("Contact Thickness (A)"), limits=(1,5000))
        step1.add_input_param("Head Thickness (A)", default=self.default("Head Thickness (A)"), limits=(1,500))

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

        yield Step(True, "Turn on water cooling.")
        '''
        Pump out sequence
        '''
        self.leakvalve(False)
        yield Step(False, "Begin pump out sequence, waiting until pressure falls below 5E-6 mbar.")

        self.wait_until('Pressure', 7e-6, "less than")

        # Calibrate the voltage needed to reach set deposition rate
        yield Step(True, "Rotate Tip to 165&deg;.")

        yield Step(False, "Calibrating voltage to reach deposition rate.")

        # Voltage calibration step, to get the voltage that gives hte deposition
        # rate we want, as a starting point for later evaporations.
        self.leakvalve(False)
        self.command('power_supply_server', 'switch', 'on')
        self.shutter("evaporator", True)

        P = params['P']
        I = params['I']
        D = params['D']
        Voffset = params['Voffset']
        Vmax = params['Vmax']
        setpoint = float(params["Deposition Rate (A/s)"])

        self.PIDLoop('Deposition Rate', 'power_supply_server', 'volt_set', P, I, D, setpoint, Voffset, (0, Vmax))
        self.wait_stable('Deposition Rate', setpoint, 1, window=5)
        self.pausePIDLoop('Deposition Rate')
        self.shutter("evaporator", False)


        yield Step(True, "Ready for He line flushing. Check that all the valves are opened!")
        yield Step(False, "Flushing He line for 2 minutes.")
        self.leakvalve(True, pressure=params["He Pressure (mbar)"])
        self.wait_for(2)
        self.leakvalve(False)
        self.wait_for(0.5)

        yield Step(True, "Ready for cooldown, follow cooldown instructions then press proceed.")

        yield Step(True, "Wait until stable cryostat temperature is reached. Adjust the liquid helium flow to acheive desired stability.")

        yield Step(True, "Rotate Tip to 90&deg;.")
        # Deposit the first contact
        yield Step(False, "Beginning thermalization, waiting " + str(params["Therm. Time 1"]) + " minutes")

        # Open the helium at ~1e-3 Torr to thermalize tip
        self.leakvalve(True, pressure=params["He Pressure (mbar)"])
        self.wait_for(params["Therm. Time 1"])
        self.leakvalve(False)
        self.wait_for(0.5)
        yield Step(True, "Ready to begin first contact deposition. Will wait 1 min for evaporator to heat up")

        # First Contact Depositon
        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness
        self.resumePIDLoop('Deposition Rate', 60)
        self.wait_for(0.95)
        self.shutter("evaporator", True)

        self.wait_until('Thickness', params["Contact Thickness (A)"], conditional='greater than')

        self.pausePIDLoop('Deposition Rate')
        self.shutter("evaporator", False)
        yield Step(False, "First contact deposition finished")

        # Deposit the SQUID head
        yield Step(True, "Rotate Tip to 345&deg;.")

        yield Step(False, "Beginning second thermalization, waiting " + str(params["Therm. Time 2"]) + " minutes")

        self.leakvalve(True, pressure=params["He Pressure (mbar)"])
        self.wait_for(params["Therm. Time 2"])
        self.leakvalve(False)
        self.wait_for(0.5)
        yield Step(True, "Ready to begin head deposition.")

        # SQUID Head Deposition
        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness
        self.resumePIDLoop('Deposition Rate', 60)
        self.wait_for(0.95)
        self.shutter("evaporator", True)

        self.wait_until('Thickness', params["Head Thickness (A)"], conditional='greater than') 

        self.pausePIDLoop('Deposition Rate')
        self.shutter("evaporator", False)
        yield Step(False, "Head deposition finished")

        # Deposit the second contact
        yield Step(True, "Rotate Tip to 240&deg;.")

        yield Step(False, "Beginning third thermalization, waiting " + str(params["Therm. Time 2"]) + " minutes")

        self.leakvalve(True, pressure=params["He Pressure (mbar)"])
        self.wait_for(params["Therm. Time 2"])
        self.leakvalve(False)
        self.wait_for(0.5)
        yield Step(True, "Ready to begin second contact deposition.")

        # Second Contact Depositon
        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness
        self.resumePIDLoop('Deposition Rate', 60)
        self.wait_for(0.95)
        self.shutter("evaporator", True)

        self.wait_until('Thickness', params["Contact Thickness (A)"], conditional='greater than')

        self.pausePIDLoop('Deposition Rate')
        self.shutter("evaporator", False)

        yield Step(False, "Second contact deposition finished")

        yield Step(True, "Deposition Finished. Follow warm up procedure.")

        self.stopRecordingVariable("all")
        self.stopTracking('all')

        finalstep = Step(False, "All Done. Let the system warm up and retreive your SQUID!")
        yield finalstep
    #

    def shutdown(self):
        try:
            self.command('power_supply_server', 'switch', 'off')
            self.shutter("evaporator", False)
        except:
            print("Warning could not shutdown the power supply.")
        super().shutdown()
    #
#
