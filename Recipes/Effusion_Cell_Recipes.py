'''
Recipes using the effusion cell
'''

from recipe import Recipe, Step

class Cryogenic_Effusion_Evap(Recipe):
    def __init__(self, *args):
        # Add all the hardwave servers needed for evaporation
        # Starting with the servers you always need, including 'data_vault'
        servers = ['data_vault', 'rvc_server', 'valve_relay_server', 'ftm_server', 'evaporator_shutter_server']

        # Then process specific servers
        servers.append('eurotherm_server')

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
        self.command('ftm_server', 'select_sensor', 2) # Ensure the user has the right crystal selected, in this case 2

        self.command('eurotherm_server', 'set_auto_mode') # Change it into automatic mode, so you can change the setpoint.
        self.command('eurotherm_server', 'set_ramprate', 60) # 60 C/Min, don't go far above.

        '''
        Track the variables
        '''
        self.trackVariable('Pressure', 'rvc_server', 'get_pressure_mbar', units='mbar')
        self.trackVariable('Deposition Rate', 'ftm_server', 'get_sensor_rate', units='(A/s)')
        self.trackVariable('Thickness', 'ftm_server', 'get_sensor_thickness', units='A')
        self.trackVariable('Temperature', 'eurotherm_server', 'get_temperature', units='C')
        self.wait_for(0.01) # Here because it threw an error one time

        self.recordVariable("Pressure")
        self.recordVariable("Temperature")
        self.recordVariable("Deposition Rate")

        '''
        Get parameters from the user
        '''
        instruct = "Follow instructions for tip loading, confirm that:"
        instruct += "\n 1. The tip is loaded"
        instruct += "\n 2. the evaporator is sealed and being pumped on."
        instruct += "\n 3. The correct film has been selected on the FTM-2400."
        instruct += "\n Confirm parameters below and press proceed to begin."
        step1 = Step(True, instruct)
        step1.add_input_param("Deposition Temp. (C)", default=self.default("Deposition Temp. (C)"), limits=(0,1400))
        step1.add_input_param("Idle Temp. (C)", default=self.default("Idle Temp. (C)"), limits=(0,700))
        step1.add_input_param("Therm. Time 1", default=self.default("Therm. Time 1"), limits=(0,100))
        step1.add_input_param("Therm. Time 2", default=self.default("Therm. Time 2"), limits=(0,100))
        step1.add_input_param("He Pressure (mbar)", default=self.default("He Pressure (mbar)"), limits=(1e-9,1000))
        step1.add_input_param("Contact Thickness (A)", default=self.default("Contact Thickness (A)"), limits=(1,5000))
        step1.add_input_param("Head Thickness (A)", default=self.default("Head Thickness (A)"), limits=(1,500))
        yield step1

        params = step1.get_all_params()
        setpoint = float(params["Deposition Temp. (C)"])
        idle_temp = float(params["Idle Temp. (C)"])

        # Not setting this as a parameter for now.
        #print(params['Deposition Rate (A/s)'])

        step2 = Step(True, "Record the Crystal Life")
        step2.add_input_param("Crystal Life", limits=(0,100))
        yield step2

        '''
        Startup by ramping the temperature up to the idle temperture (is pressure is below 1e-3 mbar)
        '''
        self.wait_until('Pressure', 1e-3, "less than") # For safe effusion cell operation
        yield Step(False, "Ramping Temperature up to idle temperature.")
        self.command('eurotherm_server', 'ramp_to_idle_temp', idle_temp)
        self.wait_until('Temperature', idle_temp, "greater than")

        yield Step(False, "Waiting until pressure falls below 5E-6 mbar.")
        self.wait_until('Pressure', 5e-6, "less than")

        self.wait_for(0.5)
        yield Step(False, "Flushing He line for 2 minutes.")
        self.leakvalve(True, pressure=params["He Pressure (mbar)"])
        self.wait_for(2)
        self.leakvalve(False)
        self.wait_for(0.5)

        yield Step(True, "Ready for cooldown, follow cooldown instructions then press proceed.")

        yield Step(True, "Wait until stable cryostat temperature is reached. Adjust the cryogen flow to achieve desired stability.")

        # Deposit the first contact
        yield Step(True, "Rotate Tip to 90&deg;.")

        # Open the helium at ~1e-3 Torr to thermalize tip
        yield Step(False, "Beginning thermalization, waiting " + str(params["Therm. Time 1"]) + " minutes")
        self.leakvalve(True, pressure=params["He Pressure (mbar)"])
        self.wait_for(params["Therm. Time 1"])
        self.leakvalve(False)
        self.wait_for(0.5)

        # The PID loop will overshoot significantly if you go diretly to the setpoint from idle temeprature and it will take
        # longer to stabalize. To avoid this go to 15C below the setpoint the go the final distance.
        yield Step(True, "Ready to begin first contact deposition. Press proceed to heat up the effusion cell to the deposition temperature.")
        self.command('eurotherm_server', 'set_setpoint', setpoint-15)
        self.wait_until('Temperature', setpoint-15, "greater than")
        self.wait_for(1)
        self.command('eurotherm_server', 'set_setpoint', setpoint)
        self.wait_stable('Temperature', setpoint, 1, window=30)

        # First Contact Depositon
        yield Step(False, "Depositing first contact.")
        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness
        self.shutter("effusion", True)
        self.wait_until('Thickness', params["Contact Thickness (A)"], conditional='greater than')
        self.shutter("effusion", False)

        yield Step(False, "First contact deposition finished, returning to idle temp.")
        self.command('eurotherm_server', 'ramp_to_idle_temp', idle_temp)
        self.wait_until('Temperature', idle_temp+5, "less than")

        # Deposit the SQUID head
        yield Step(True, "Rotate Tip to 345&deg;.")

        yield Step(False, "Beginning second thermalization, waiting " + str(params["Therm. Time 2"]) + " minutes")
        self.leakvalve(True, pressure=params["He Pressure (mbar)"])
        self.wait_for(params["Therm. Time 2"])
        self.leakvalve(False)
        self.wait_for(0.5)

        yield Step(True, "Ready to begin head deposition. Press proceed to heat up the effusion cell to the deposition temperature.")
        self.command('eurotherm_server', 'set_setpoint', setpoint-15)
        self.wait_until('Temperature', setpoint-15, "greater than")
        self.wait_for(1)
        self.command('eurotherm_server', 'set_setpoint', setpoint)
        self.wait_stable('Temperature', setpoint, 1, window=30)

        # SQUID Head Deposition
        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness
        self.shutter("evaporator", True)
        self.wait_until('Thickness', params["Head Thickness (A)"], conditional='greater than')
        self.shutter("evaporator", False)

        yield Step(False, "Head deposition finished, returning to idle temp.")
        self.command('eurotherm_server', 'ramp_to_idle_temp', idle_temp)
        self.wait_until('Temperature', idle_temp+5, "less than")

        # Deposit the second contact
        yield Step(True, "Rotate Tip to 240&deg;.")

        yield Step(False, "Beginning third thermalization, waiting " + str(params["Therm. Time 2"]) + " minutes")
        self.leakvalve(True, pressure=params["He Pressure (mbar)"])
        self.wait_for(params["Therm. Time 2"])
        self.leakvalve(False)
        self.wait_for(0.5)

        yield Step(True, "Ready to begin second contact deposition. Press proceed to heat up the effusion cell to the deposition temperature")
        self.command('eurotherm_server', 'set_setpoint', setpoint-15)
        self.wait_until('Temperature', setpoint-15, "greater than")
        self.wait_for(1)
        self.command('eurotherm_server', 'set_setpoint', setpoint)
        self.wait_stable('Temperature', setpoint, 1, window=30)

        # Second Contact Depositon
        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness
        self.shutter("evaporator", True)
        self.wait_until('Thickness', params["Contact Thickness (A)"], conditional='greater than')
        self.shutter("evaporator", False)

        yield Step(False, "Second contact deposition finished")

        yield Step(False, "Deposition Finished. Ramping the effusion cell down to room temperature. Remove cryogen and start warming up the SQUID.")

        self.command('eurotherm_server', 'ramp_to_room')
        self.wait_until('Temperature', 100, "less than")

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
