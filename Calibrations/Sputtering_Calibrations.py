from recipe import CalibrationRecipe, Step

class Sputtering_Test(CalibrationRecipe):
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
        servers.append('dcxs_power')
        servers.append('alicat_mcv')

        super().__init__(*args, required_servers=servers, version="1.0.0")
        #

    def proceed(self):
        self.command('rvc_server', 'select_device')

        self.command('valve_relay_server', 'select_device')
        # #Iden command added so that arduino will respond to first command given from GUI.
        # #Lack of response is somehow connected to dsrdtr port connection, but not yet sure how...
        self.command('valve_relay_server', 'iden')

        self.command('ftm_server', 'select_device')
        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness

        # Ensure the user has the right crystal selected, in this case 2
        self.command('ftm_server', 'select_sensor', 2)

        self.command('dcxs_power', 'select_device')
        self.command('alicat_mcv', 'select_device')

        Step(True, "Setup the values for the FTM Controller")

        # Initilize Variables
        self.trackVariable('Pressure', 'rvc_server', 'get_pressure_mbar', units='mbar')
        self.trackVariable('Deposition Rate', 'ftm_server', 'get_sensor_rate', units='(A/s)')
        self.trackVariable('Thickness', 'ftm_server', 'get_sensor_thickness', units='A')
        self.trackVariable('Setpoint power', 'dcxs_power', 'get_setpoint', units='W')
        self.trackVariable('Power', 'dcxs_power', 'get_power', units='W')
        # self.trackVariable('Voltage', 'dcxs_power', 'get_voltage', units='V')
        # self.trackVariable('Current', 'dcxs_power', 'get_current', units='mA')

        self.trackVariable('Flow rate', 'alicat_mcv', 'get_mass_flow', units='SCCM')
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
