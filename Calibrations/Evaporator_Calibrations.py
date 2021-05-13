from recipe import CalibrationRecipe, Step
from numpy import abs

class Calibrate_Evaporator_Shutter(CalibrationRecipe):
    def __init__(self, *args):
        super().__init__(*args, required_servers=['evaporator_shutter_server'])
    #

    def proceed(self):
        self.command('evaporator_shutter_server', 'select_device')

        s = "Calibrating the zero position of the Evaporator shutter."
        s = s + " Enter the angle from the analog dial of the stepper motor."
        s = s + " 60&deg; is the normal closed position."
        step1 = Step(True, s)
        step1.add_input_param("Angle", default=60, limits=(0,360))
        yield step1
        val = int(step1.get_param("Angle"))

        yield Step(False, "Recalibrating")

        diff = 60 - val
        if diff > 0:
            self.command('evaporator_shutter_server', 'rot', args=[str(int(abs(diff))), "C"])
        else:
            self.command('evaporator_shutter_server', 'rot', args=[str(int(abs(diff))), "A"])

        self.wait_for(0.25)
        self.command('evaporator_shutter_server', 'manual_reset_close')

        finalstep = Step(False, "Evaporator server recalibrated and set to closed position.")
        yield finalstep
    #

class Evaporation_Test(CalibrationRecipe):
    """
    Tests the evaporation hardware.
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
        # step1.add_input_param("Contact Thickness (A)", default=self.default("Contact Thickness (A)"), limits=(10,500))
        # step1.add_input_param("Head Thickness (A)", default=self.default("Head Thickness (A)"), limits=(10,500))

        step1.add_input_param("P", default=self.default("P"), limits=(0,1))
        step1.add_input_param("I", default=self.default("I"), limits=(0,1))
        step1.add_input_param("D", default=self.default("D"), limits=(0,1))

        step1.add_input_param("Vmax", default=self.default("Vmax"), limits=(0,10))
        step1.add_input_param("Voffset", default=self.default("Voffset"), limits=(0,10))
        yield step1
        params = step1.get_all_params()

        """
        Pump out process
        """

        # ## First rough out the chamber with the scroll pump
        # self.valve('all', True) # Open all the valves
        # # self.leakvalve(True)
        # self.pump('scroll', True)
        # self.wait_until('Pressure', 1e-1, "less than")
        # #
        # # ## Close the Chamber valve
        # self.valve('chamber', False)
        # self.wait_for(0.1)
        # self.leakvalve(False)
        # self.pump('turbo', True)

        yield Step(False, "Pumping down to base pressure.")

        self.wait_until('Pressure', 5e-6, "less than")

        '''
        Evaporation test
        '''

        # Calibrate the voltage needed to reach set deposition rate
        yield Step(True, "Rotate Tip to 165&deg;.")

        yield Step(False, "Calibrating voltage to reach deposition rate.")

        # Voltage calibration step, to get the voltage that gives hte deposition
        # rate we want, as a starting point for later evaporations.
        self.command('power_supply_server', 'switch', 'on')
        self.shutter("evaporator", True)

        P = params['P']
        I = params['I']
        D = params['D']
        Voffset = params['Voffset']
        Vmax = params['Vmax']
        setpoint = int(params['Deposition Rate (A/s)'])

        self.PIDLoop('Deposition Rate', 'power_supply_server', 'volt_set', P, I, D, setpoint, Voffset, (0, Vmax))
        self.wait_until('Deposition Rate', setpoint-0.1, "greater than", timeout=5)
        yield Step(True, "Once deposition rate appears stable press proceed to pause evaporation.")
        self.pausePIDLoop('Deposition Rate')
        self.shutter("evaporator", False)

        # yield Step(True, "Ready for cooldown, follow cooldown instructions then press proceed.")

        # yield Step(False, "Wait until stable cryostat temperature is reached. Adjust the liquid helium flow to acheive desired stability.")

        # # Deposit the first contact
        # yield Step(False, "Waiting 10 min")
        #
        # # Open the helium at ~1e-3 Torr for 20 min to thermalize tip
        # # self.leakvalve(True, pressure=1e-3)
        # self.wait_for(10)

        #yield Step(True, "Rotate Tip to 90&deg;.")

        yield Step(False, "Beginning first contact deposition. Waiting 2 min for evaporator to heat up")

        # First Contact Depositon
        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness
        self.resumePIDLoop('Deposition Rate', 120)
        self.wait_for(2)
        self.shutter("evaporator", True)

        self.wait_until('Thickness', 200, conditional='greater than', timeout=5)

        self.pausePIDLoop('Deposition Rate')
        self.shutter("evaporator", False)
        yield Step(False, "First contact deposition finished")

        # Deposit the SQUID head
        yield Step(False, "Beginning thermalization, waiting 10 min")
        self.wait_for(10)

        #yield Step(True, "Rotate Tip to 345&deg;.")

        yield Step(False, "Beginning head deposition.")

        # SQUID Head Deposition
        self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness
        self.resumePIDLoop('Deposition Rate', 120)
        self.wait_for(2)
        self.shutter("evaporator", True)

        self.wait_until('Thickness', 150, conditional='greater than', timeout=5)

        self.pausePIDLoop('Deposition Rate')
        self.shutter("evaporator", False)
        yield Step(False, "Head deposition finished")

        # # Deposit the second contact
        # yield Step(False, "Beginning thermalization, waiting 10 min")
        # self.wait_for(10)
        #
        # yield Step(True, "Rotate Tip to 240&deg;.")
        #
        # yield Step(False, "Beginning second contact deposition.")
        #
        # # First Contact Depositon
        # self.command('ftm_server', 'zero_rates_thickness') # Zero the thickness
        # self.resumePIDLoop('Deposition Rate', 120)
        # self.wait_for(2)
        # self.shutter("evaporator", True)
        #
        # self.wait_until('Thickness', 'greater than', 200, timeout=5)
        #
        # self.pausePIDLoop('Deposition Rate')
        # self.shutter("evaporator", False)
        #
        # yield Step(False, "Second contact deposition finished")

        finalstep = Step(False, "All Done. Chamber still being pumped on.")
        yield finalstep

        '''
        Finishing process
        '''
        # yield Step(True, "Press proceed to close valves and prepare to vent.")
        # self.valve('all', False) # close all valves
        # self.wait_for(0.1)
        # self.pump('turbo', False) # Turn off the turbo pump
        # yield Step(True, "Turbo spinning down, gently open turbo vent bolt for proper spin-down. Press proceed after spin-down.")
        #
        # self.leakvalve(True)
        # self.wait_for(0.1)
        # # self.pump('scroll', False) # Turn off the scroll pump
        #
        # # Stop updating the plots of the tracked quantities
        # self.stopPlotting("Pressure")
        # self.stopTracking('all')
        #
        # finalstep = Step(False, "All Done. Leak valve open, ready to vent the chamber.")
        # yield finalstep

    def shutdown(self):
        try:
            self.command('power_supply_server', 'switch', 'off')
            self.shutter("evaporator", False)
        except:
            print("Warning could not shutdown the power supply.")
        super().shutdown()
    #
