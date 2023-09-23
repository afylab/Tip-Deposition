from recipe import CalibrationRecipe, Step

class Effusion_Deposition_Test(CalibrationRecipe):
    """
    Tests the effusion cell hardware temeprature control. Use to find ramp up/down parameters
    idle temperture and evaporation temperature.
    """
    def __init__(self, *args):
        # Add all the hardwave servers needed for evaporation

        # Starting iwth the servers you always need, including 'data_vault'
        servers = ['data_vault', 'rvc_server', 'valve_relay_server']

        # Then evaporation specific servers
        servers.append('power_supply_server')
        servers.append('evaporator_shutter_server')
        servers.append('eurotherm_server')

        super().__init__(*args, required_servers=servers, version="1.0.1")
        #

    def proceed(self):
        message = "Set the parameters for the FTM-2400 before attempting to run the recipe."
        message += "\n 1. Modifying parameters on the fly may cause labrad issues."
        Step(True, message)

        self.command('rvc_server', 'select_device')

        self.command('valve_relay_server', 'select_device')
        # #Iden command added so that arduino will respond to first command given from GUI.
        # #Lack of response is somehow connected to dsrdtr port connection, but not yet sure how...
        self.command('valve_relay_server', 'iden')

        self.command('evaporator_shutter_server', 'select_device')

        self.command('ftm_server', 'select_device')
        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness

        # Ensure the user has the right crystal selected, in this case 2
        self.command('ftm_server', 'select_sensor', 2)

        # Eurotherm 2400 server does not need to select_device as it is not using the serial server
        # But you need to set it to automatic mode
        self.command('eurotherm_server', 'set_auto_mode')

        Step(True, "Setup the values for the FTM Controller")

        # Initilize Variables
        self.trackVariable('Pressure', 'rvc_server', 'get_pressure_mbar', units='mbar')
        self.trackVariable('Deposition Rate', 'ftm_server', 'get_sensor_rate', units='(A/s)')
        self.trackVariable('Thickness', 'ftm_server', 'get_sensor_thickness', units='A')

        self.trackVariable('Power', 'eurotherm_server', 'get_power', units='%')
        self.trackVariable('Temperature', 'eurotherm_server', 'get_temperature', units='C')
        #self.trackVariable('Setpoint', 'eurotherm_server', 'get_setpoint', units='C')
        self.wait_for(0.01) # Here because it threw an error one time

        # Crystal parameters
        step2 = Step(True, "Turn on the cooling water and record the flow rate")
        step2.add_input_param("Cooling Water Flow")
        yield step2

        step2 = Step(True, "Record the Crystal Life")
        step2.add_input_param("Crystal Num", limits=(0,100))
        step2.add_input_param("Crystal Life", limits=(0,100))
        yield step2

        '''
        Get parameters from the user
        '''
        instruct = "Follow instructions for tip loading, confirm that:"
        instruct += "\n 1. The Si chip is loaded if desired."
        instruct += "\n 3. The system is pumped out and/or cooled to the desired temperature."
        instruct += "\n Confirm parameters below."
        step1 = Step(True, instruct)

        step1.add_input_param("Idle Temperature", default=self.default("Idle Temperature"), limits=(0,1400))
        step1.add_input_param("Dep. Temperature", default=self.default("Dep. Temperature"), limits=(0,1400))
        step1.add_input_param("Therm. Time", default=self.default("Therm. Time"), limits=(0,100))
        step1.add_input_param("He Pressure (mbar)", default=self.default("He Pressure (mbar)"), limits=(1e-9,10))
        step1.add_input_param("Calibration Thickness (A)", default=self.default("Calibration Thickness (A)"), limits=(0,5000))

        yield step1

        params = step1.get_all_params()

        '''
        Ramp up the temperature setpoint in steps to allow the effusion cell to rise slowly.
        '''

        yield Step(True, "Press proceed to warm up the effusion cell to the idling temperature.")
        self.command('eurotherm_server', 'ramp_to_idle_temp', int(params["Idle Temperature"]))
        self.shutter("effusion", False) # Close the effusion shutter
        self.wait_stable('Temperature', int(params["Idle Temperature"]), 10, window=30)

        '''
        Thermalization step to make sure the chip is thermalized when doing cryogenic deposition
        '''
        Step(True, "Cooldown the Tip, if not done already. Press proceed thermalize the tip.")
        # Open the helium at ~1e-3 Torr for 10 min to make sure tip is cold
        self.leakvalve(True, pressure=params["He Pressure (mbar)"])
        self.wait_for(params["Therm. Time"])
        self.leakvalve(False)
        self.wait_for(0.5)
        yield Step(True, "Ready to begin deposition.")


        yield Step(True, "Press proceed to heat up the effusion cell to the Deposition temperature.")
        self.command('eurotherm_server', 'set_setpoint', int(params["Dep. Temperature"]))

        yield Step(False, "Waiting for stable temperature")
        self.wait_stable('Temperature', int(params["Dep. Temperature"]), 5, window=60)

        # Deposit the SQUID head
        yield Step(True, "Rotate Tip to 90&deg; if using chip adapter.")

        yield Step(True, "Press proceed to deposit.")
        self.shutter("effusion", True)

        self.wait_until('Thickness', params["Calibration Thickness (A)"], conditional='greater than')

        self.shutter("effusion", False)

        yield Step(True, "Deposition complete. Press proceed to ramp down the effusion cell temperture")
        self.command('eurotherm_server', 'ramp_to_room')

        step1 = Step(True, "Press proceed to end.")
        yield step1

        self.stopTracking('all')

        finalstep = Step(False, "All Done. Time to let the system warm up.")
        yield finalstep

class Effusion_Manual_Calibration(CalibrationRecipe):
    """
    A single deposition, controlling temperature manually
    """
    def __init__(self, *args):
        # Add all the hardwave servers needed for evaporation

        # Starting iwth the servers you always need, including 'data_vault'
        servers = ['data_vault', 'rvc_server', 'valve_relay_server', 'ftm_server']

        # Then evaporation specific servers
        servers.append('power_supply_server')
        servers.append('evaporator_shutter_server')

        super().__init__(*args, required_servers=servers, version="1.0.0")
        #

    def proceed(self):
        self.command('rvc_server', 'select_device')

        self.command('valve_relay_server', 'select_device')
        # #Iden command added so that arduino will respond to first command given from GUI.
        # #Lack of response is somehow connected to dsrdtr port connection, but not yet sure how...
        self.command('valve_relay_server', 'iden')

        self.command('evaporator_shutter_server', 'select_device')

        self.command('ftm_server', 'select_device')
        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness

        # Ensure the user has the right crystal selected, in this case 2
        self.command('ftm_server', 'select_sensor', 2)

        # Eurotherm 2400 server does not need to select_device as it is not using the serial server

        # Initilize Variables
        self.trackVariable('Pressure', 'rvc_server', 'get_pressure_mbar', units='mbar')
        self.trackVariable('Deposition Rate', 'ftm_server', 'get_sensor_rate', units='(A/s)')
        self.trackVariable('Thickness', 'ftm_server', 'get_sensor_thickness', units='A')

        self.trackVariable('Power', 'eurotherm_server', 'get_power', units='%')
        self.trackVariable('Temperature', 'eurotherm_server', 'get_temperature', units='C')
        #self.trackVariable('Setpoint', 'eurotherm_server', 'get_setpoint', units='C')
        self.wait_for(0.01) # Here because it threw an error one time

        step2 = Step(True, "Turn on the cooling water and record the flow rate")
        step2.add_input_param("Cooling Water Flow")
        yield step2

        '''
        Get parameters from the user
        '''
        step1 = Step(True, "Enter desired calibration thickness")

        step1.add_input_param("Calibration Thickness (A)", default=self.default("Calibration Thickness (A)"), limits=(0,5000))
        yield step1
        params = step1.get_all_params()

        # Deposit the SQUID head
        yield Step(True, "Rotate Tip to 165&deg;.")

        yield Step(True, "Press proceed to open shutter.")
        self.shutter("effusion", True)

        yield Step(True, "Manually calibrate deposition rate. Then press proceed to close shutter.")
        self.shutter("effusion", False)

        # Deposit the SQUID head
        yield Step(True, "Rotate Tip to deposition angle.")
        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness

        yield Step(True, "Press proceed to deposit.")
        self.shutter("effusion", True)
        self.wait_until('Thickness', params["Calibration Thickness (A)"], conditional='greater than')
        self.shutter("effusion", False)

        step3 = Step(True, "Press proceed to end.")
        yield step3

        self.stopTracking('all')

        finalstep = Step(False, "All Done. Time to let the system cool down.")
        yield finalstep

class Effusion_Test(CalibrationRecipe):
    """
    Tests the effusion cell hardware temeprature control by just displaying while
    you change the hardware directly.

    Use to find ramp up/down parameters, idle temperture and evaporation temperatures as needed.
    """
    def __init__(self, *args):
        # Add all the hardwave servers needed for evaporation

        # Starting iwth the servers you always need, including 'data_vault'
        servers = ['data_vault', 'rvc_server', 'valve_relay_server', 'ftm_server']

        # Then evaporation specific servers
        servers.append('power_supply_server')
        servers.append('evaporator_shutter_server')

        super().__init__(*args, required_servers=servers, version="1.0.0")
        #

    def proceed(self):
        self.command('rvc_server', 'select_device')

        self.command('valve_relay_server', 'select_device')
        # #Iden command added so that arduino will respond to first command given from GUI.
        # #Lack of response is somehow connected to dsrdtr port connection, but not yet sure how...
        self.command('valve_relay_server', 'iden')

        self.command('evaporator_shutter_server', 'select_device')

        self.command('ftm_server', 'select_device')
        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness

        # Ensure the user has the right crystal selected, in this case 2
        self.command('ftm_server', 'select_sensor', 2)

        # Eurotherm 2400 server does not need to select_device as it is not using the serial server

        # Initilize Variables
        self.trackVariable('Pressure', 'rvc_server', 'get_pressure_mbar', units='mbar')
        self.trackVariable('Deposition Rate', 'ftm_server', 'get_sensor_rate', units='(A/s)')
        self.trackVariable('Thickness', 'ftm_server', 'get_sensor_thickness', units='A')

        self.trackVariable('Power', 'eurotherm_server', 'get_power', units='%')
        self.trackVariable('Temperature', 'eurotherm_server', 'get_temperature', units='C')
        self.trackVariable('Setpoint', 'eurotherm_server', 'get_setpoint', units='C')
        self.wait_for(0.01) # Here because it threw an error one time

        step2 = Step(True, "Turn on the cooling water and record the flow rate")
        step2.add_input_param("Cooling Water Flow")
        yield step2

        # step2 = Step(True, "Record the Crystal Life")
        # step2.add_input_param("Crystal Num", limits=(0,100))
        # step2.add_input_param("Crystal Life", limits=(0,100))
        # yield step2

        step3 = Step(True, "Press proceed to end.")
        yield step3

        self.stopTracking('all')

        finalstep = Step(False, "All Done. Time to let the system cool down.")
        yield finalstep
