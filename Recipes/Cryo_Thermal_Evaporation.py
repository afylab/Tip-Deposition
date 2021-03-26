'''
A simple thermal evaporation using only the thermal evaporator and the cryogenic insert.

'''

from recipe import Recipe, Step

class Cryo_Thermal_Evaporation(Recipe):
    def proceed(self):
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
        step1.add_input_param("Vmin", default=self.default("Vmin"), limits=(0,10))
        yield step1

        #params = step1.get_all_params()
        #print(params['Deposition Rate (A/s)'])

        step2 = Step(True, "Record the Crystal Life")
        step2.add_input_param("Crystal Life", limits=(0,100))
        yield step2

        # Acess data from step1 and prepare

        yield Step(False, "Beginning pump out sequence, waiting until pressure falls below 1E-6 mbar.")

        # Perform pump down sequence

        yield Step(True, "Ready for cooldown, follow cooldown instructions the press proceed.")

        yield Step(False, "Waiting until stable temperature is reached.")

        # Wait until base temperature is reached.

        # Calibrate the voltage needed to reach set deposition rate
        yield Step(True, "Rotate Tip to 165&deg;.")

        yield Step(False, "Calibrating voltage to reach deposition rate.")

        # Deposit the first contact
        yield Step(False, "Beginning thermalization, waiting 20 min")

        yield Step(True, "Rotate Tip to 90&deg;.")

        yield Step(False, "Beginning first contact deposition.")

        yield Step(False, "First contact deposition finished")

        # Deposit the SQUID head
        yield Step(False, "Beginning thermalization, waiting 10 min")

        yield Step(True, "Rotate Tip to 345&deg;.")

        yield Step(False, "Beginning head deposition.")

        yield Step(False, "Head deposition finished")

        # Deposit the second contact
        yield Step(False, "Beginning thermalization, waiting 10 min")

        yield Step(True, "Rotate Tip to 240&deg;.")

        yield Step(False, "Beginning second contact deposition.")

        yield Step(False, "First contact deposition finished")

        # Warm up procedure
        yield Step(True, "Deposition Finished. Follow warm up procedure.")

    #
#
