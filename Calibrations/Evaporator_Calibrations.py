from recipe import CalibrationRecipe, Step
from numpy import abs

class Calibrate_Evaporator_Shutter(CalibrationRecipe):
    def __init__(self, equip):
        super().__init__(equip, required_servers=['evaporator_shutter_server'])
    #

    def proceed(self):
        self.command('evaporator_shutter_server', 'select_device')

        s = "Calibrating the zero position of the Evaporator shutter."
        s = s + " Enter the angle from the analog dial of the stepper motor."
        s = s + " 57&deg; is the normal closed position."
        step1 = Step(True, s)
        step1.add_input_param("Angle", default=57, limits=(0,360))
        yield step1
        val = int(step1.get_param("Angle"))

        yield Step(False, "Recalibrating")

        diff = 57 - val
        if diff > 0:
            self.command('evaporator_shutter_server', 'rot', args=[str(int(abs(diff))), "C"])
        else:
            self.command('evaporator_shutter_server', 'rot', args=[str(int(abs(diff))), "A"])

        self.wait_for(0.25)
        self.command('evaporator_shutter_server', 'manual_reset_close')

        finalstep = Step(False, "Evaporator server recalibrated and set to closed position.")
        yield finalstep
    #
