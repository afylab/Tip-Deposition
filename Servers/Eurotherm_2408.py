from labrad.server import setting, LabradServer
# from labrad.devices import DeviceServer, DeviceWrapper
# from twisted.internet.defer import inlineCallbacks
from labrad.types import Value
import minimalmodbus
import serial
# import time

TIMEOUT = Value(2, 's')
BAUD = 9600
BYTESIZE = 8
STOPBITS = 1
PARITY = serial.PARITY_NONE


class EurothermServer(LabradServer):
    name = "Eurotherm Server"

    def __init__(self):
        super().__init__()
        self._registers = {
            "setpoint1": 24,
            "setpoint2": 25,
            "setpoint3": 164,
            "setpoint4": 165,
            "setpoint5": 166,
            "setpoint6": 167,
            "setpoint7": 168,
            "setpoint8": 169,
            "setpoint9": 170,
            "setpoint10": 171,
            "setpoint11": 172,
            "setpoint12": 173,
            "setpoint13": 174,
            "setpoint14": 175,
            "setpoint15": 176,
            "setpoint16": 177,
            "selectedSetpoint": 15,
            "Local_or_remote_setpoint_select": 276,
            "Remote_setpoint": 485,
            "Remote_setpoint_trim": 486,
            "Ratio_setpoint": 61,
            "Local_setpoint_trim": 27,
            "Setpoint_1_low_limit": 112,
            "Setpoint_1_high_limit": 111,
            "Setpoint_2_low_limit": 114,
            "Setpoint_2_high_limit": 113,
            "Local_setpoint_trim_low_limit": 67,
            "Local_setpoint_trim_high_limit": 66,
            "Setpoint_rate_limit": 35,
            "Holdback_type_for_sp_rate_limit": 70,
            "Holdback_value_for_srtpoint_rate_limit": 65,
            "Dwell_Segment": 62,
            "Goto": 517,
            "Programmer_State_Write": 57,
            "Programmer_state_Read": 23,
            "Gain_scheduler_setpoint": 153,
            "Current_PID_set": 72,
            "Proportional_band_PID1": 6,
            "Integral_time_PID1": 8,
            "Derivative_time_PID1": 9,
            "Manual_reset_PID1": 28,
            "Cutback_high_PID1": 18,
            "Cutback_low_PID1": 17,
            "Relative_cool_gain_PID1": 19,
            "Proportional_band_PID2": 48,
            "Integral_time_PID2": 49,
            "Derivative_time_PID2": 51,
            "Manual_reset_PID2": 50,
            "Cutback_high_PID2": 118,
            "Cutback_low_PID2": 117,
            "Relative_cool_gain_PID2": 52,
            "Feedforward_proportional_band": 97,
            "Feedforward_trim": 98,
            "Feedforward_trim_limit": 99,

            "Valve travel_time": 21,
            "Valve_inertia_time": 123,
            "Valve_backlash_time": 124,
            "Minimum_pulse_time": 54,
            "Bounded_sensor_break_strategy": 128,
            "VP_Bounded_sensor_break": 62,

            "Current_program_running__active_prog_no": 22,
            "Program_status": 23,
            "Programmer_setpoint": 163,
            "Program_cycles_remaining": 59,
            "Current_segment_number": 56,
            "Current_segment_type": 29,
            "Segment_time_remaining_in_secs": 36,
            "Segment_time_remaining_in_mins": 63,
            "Target_setpoint__current_segment": 160,
            "Ramp_rate": 161,
            "Program_time_remaining": 58,
            "Fast_run": 57,
            "Logic_1_output__current_program": 464,
            "Logic_2_output__current_program": 465,
            "Logic_3_output__current_program": 466,
            "Logic_4_output__current_program": 467,
            "Logic_5_output__current_program": 468,
            "Logic_6_output__current_program": 469,
            "Logic_7_output__current_program": 470,
            "Logic_8_output__current_program": 471,
            "A__Segment_synchronisation": 488,
            "Flash_active_segment_in_lower_display": 284,
            "Advance_Segment_Flag": 149,
            "Skip_Segment_Flag": 154,
            "Program_Logic_Status": 162,
            "BBB_Alarm_1setpoint_value": 13,
            "BBB_Alarm_2setpoint_value": 14,
            "BBB_Alarm_3setpoint_value": 81,
            "BBB_Alarm_4setpoint_value": 82,
            "Alarm_1_hysteresis": 47,
            "Alarm_2_hysteresis": 68,
            "Alarm_3_hysteresis": 69,
            "Alarm_4_hysteresis": 71,
            "Loop_break_time": 83,
            "Enable_diagnostic_messages": 282,
            "Acknowledge_All_Alarms": 274,
            "Autotune_enable": 270,
            "Adaptive_tune_enable": 271,
            "Adaptive_tune_trigger_level": 100,
            "Automatic_droop_compensation__manual_reset": 272,
            "Process_Variable": 1,
            # below is likely the goal temp.. unless that is port 5 "Working_set_point"
            "Target_setpoint": 2,
            "pc_Output_power": 3,
            "Working_set_point": 5,
            "Auto_man_select": 273,
            "Pot_Position": 317,
            "Valve_Posn__computed_by_VP_algorithm": 53,
            "VP_Manual_Output__alterable_in_Man_only": 60,
            "Heater_current__With_PDSIO_mode_2": 80,
            "Customer_defined_identification_number": 629,
            "Setpoint_Span": 552,
            "Error__PV_SP": 39,
            "Remote_Input_Value": 26,
            "Input_1_filter_time_constant": 101,
            "Input_2_filter_time_constant": 103,
            "Select_input_1_or_input_2": 288,
            "Derived_input_function_factor_1": 292,
            "_Derived_input_function_factor_2": 293,
            "Switchover_transition_region_high": 286,
            "Switchover_transition_region_low": 287,
            "Potentiometer_Calibration_Enable": 310,
            "Potentiometer_Input_Calibration_Node": 311,
            "Potentiometer_Calibration_Go": 312,
            "Emmisivity": 38,
            "Emmisivity_input_2": 104,
            "User_calibration_enable": 110,
            "Selected_calibration_point": 102,
            "User_calibration_adjust_input_1": 146,
            "User_calibration_adjust_input_2": 148,
            "Input_1_calibration_offset": 141,
            "Input_2_calibration_offset": 142,
            "Input_1_measured_value": 202,
            "Input_2_measured_value": 208,
            "Input_1_cold_junction_temp__reading": 215,
            "Input_2_cold_junction_temp__reading": 216,
            "Input_1_linearised_value": 289,
            "Input_2_linearised_value": 290,
            "Currently_selected_setpoint": 291,
            "Low_power_limit": 31,
            "High_power_limit": 30,
            "Remote_low_power_limit": 33,
            "Remote_high_power_limit": 32,
            "Output_rate_limit": 37,
            "Forced_output_level": 84,
            "Heat_cycle_time": 10,
            "Heat_hysteresis__on_off_output": 86,
            "Heat_output_minimum_on_time": 45,
            "Cool_cycle_time": 20,
            "Cool_hysteresis__on_off_output": 88,
            "Cool_output_minimum_on_time": 89,
            "Heat_cool_deadband__on_off_op": 16,
            "Power_in_end_segment": 64,
            "Sensor_break_output_power": 34,
            "On_Off_Sensor_Break_Output": 40,

            "Configuration_of_lower_readout_display": 106,
            "PV_minimum": 134,
            "PV_maximum": 133,
            "PV_mean_value": 135,
            "Time_PV_above_threshold_level": 139,
            "PV_threshold_for_timer_log": 138,
            "Logging_reset": 140,
            "Maximum_Control_Task_Time__Processor_utilisation_factor": 201,
            "Working_output": 4,
            "PDSIO_SSR_status": 79,
            "Feedforward_component_of_output": 209,
            "Proportional_component_of_output": 214,
            "Integral_component_of_output": 55,
            "Derivative_component_of_output": 116,
            "VP_motor_calibration_state": 210,

            "DC_Output_1A_Telemetry": 12694,
            "DC_Output_2A_Telemetry": 12758,
            "DC_Output_3A_Telemetry": 12822,
            "BCD_Input_Value": 96,
            "Instrument_Mode": 199,
            "Instrument_Version_Number": 107,
            "Instrument_Ident": 122,
            "Slave_Instrument_Target_Setpoint": 92,
            "Slave_Instrument_Ramp_Rate": 93,
            "Slave_Instrument_Sync": 94,
            "Remote_SRL_Hold": 95,
            "CNOMO_Manufacturers_ID": 121,
            "Remote_Parameter": 151,
            "Error_Logged_Flag": 73,
            "Ramp_Rate_Disable": 78,
            "Maximum_Input_Value": 548,
            "Minimum_Input_Value": 549,
            "Holdback_Disable": 278,
            "All_User_Interface_Keys_Disable": 279,

            "Control_type": 512,
            "Control_Action": 7,
            "Type_of_cooling": 524,
            "Integral_and_Derivative_time_units": 529,
            "Derivative_action": 550,
            "Front_panel_Auto_Manual_button": 530,
            "Front_panel_Run_Hold_button": 564,
            "Power_feedback_enable": 565,
            "Feed_forward_type": 532,
            "Manual_Auto_transfer_PD_control": 555,
            "_5D6_Sensor_break_output": 553,
            "Forced_manual_output": 556,
            "BCD_input_function": 522,
            "Gain_schedule_enable": 567,
            "Custom_linearisation_input_1": 601,
            "Display_value_corresponding_to_input_1": 621,
            "Custom_linearisation_input_2": 602,
            "Display_value_corresponding_to_input_2": 622,
            "Custom_linearisation_input_3": 603,
            "Display_value_corresponding_to_input_3": 623,
            "Custom_linearisation_input_4": 604,
            "Display_value_corresponding_to_input_4": 624,
            "Custom_linearisation_input_5": 605,
            "Display_value_corresponding_to_input_5": 625,
            "Custom_linearisation_input_6": 606,
            "Display_value_corresponding_to_input_6": 626,
            "Custom_linearisation_input_7": 607,
            "Display_value_corresponding_to_input_7": 627,
            "Custom_linearisation_input_8": 608,
            "Display_value_corresponding_to_input_8": 628,
            "Instrument_units": 516,
            "Decimal_places_in_displayed_value": 525,
            "Setpoint_Min___Low_range_limit": 11,
            "Setpoint_Max___High_range_limit": 12,

            "Input_type": 12290,
            "Cold_junction_compensation": 12291,
            "Sensor_break_impedance": 12301,
            "Input_value_low": 12307,
            "Input_value_high": 12306,
            "Displayed_reading_low": 12303,
            "Displayed_reading_high": 12302,
            "Number_of_setpoints": 521,
            "Remote_tracking": 526,
            "Manual_tracking": 527,
            "Programmer_tracking": 528,
            "Setpoint_rate_limit_units": 531,
            "Remote_setpoint_configuration": 535,

            "Alarm_1_type": 536,
            "Alarm_1_Latching": 540,
            "Alarm_1_Blocking": 544,

            "Alarm_2_type": 537,
            "Alarm_2_Latching": 541,
            "Alarm_2_Blocking": 545,
            "Alarm_3_type": 538,
            "Alarm_3_Latching": 542,
            "Alarm_3_Blocking": 546,
            "Alarm_4_type": 539,
            "Alarm_4_Latching": 543,
            "Alarm_4_Blocking": 547,

            "Programmer_type": 517,
            "Holdback": 559,
            "Power_fail_recovery": 518,
            "Servo": 520,
            "Programmable_event_outputs": 558,
            "Synchronisation_of_programs": 557,
            "Maximum_Number_Of_Segments": 211,

            "DI1_Logic": 12352,
            "DI1_Input_functions": 12355,

            "DI2_Identity:": 12416,
            "DI2_Input_functions": 12419,
            "DI2_Low_scalar": 12431,
            "DI2_High_scalar": 12430,

            "AA_Module_identity": 12480,
            "AA_Module_function": 12483,
            "AA_Sense_of_output": 12489,
            "AA_Summary_of_AA_configuration": 12486,
            "AA_Program_summary_OP_AA_configuration": 12503,
            "AA_Comms_Resolution": 12550,
            "AA_Module_Identity": 12608,
            "AA_Retransmitted_Low_Scalar": 12623,
            "AA_Retransmitted_High_Scalar": 12622,

            "_1A_Module_identity": 12672,
            "_1A_Module_function": 12675,
            "_1A_PID_or_Retran_value_giving_min__o_p": 12687,
            "_1A_PID_or_Retran_value_giving_max__o_p": 12686,
            "_1A_Units": 12684,
            "_1A_Minimum_electrical_output": 12689,
            "_1A_Maximum_electrical_output": 12688,
            "_1A_Sense_of_output": 12681,
            "_1A_Summary_output_1A_configuration": 12678,
            "_1A_DC_output_1A_telemetry_parameter": 12694,
            "_1A_Program_summary_output_1A_config": 12695,

            "_1B_Module_1B_identity": 12673,
            "_1B_Module_1B_function": 12676,
            "_1B_Sense_of_output__nor_inv_as1A": 12682,
            "_1B_Summary_of_1B_configuration": 12679,
            "_1B_Summary_program_O_P_1B_config": 12696,

            "_1C_Module_1C_identity": 12674,
            "_1C_Module_1C_function": 12677,
            "_1C_Module_1C_value_giving_min_output": 12699,
            "_1C_Module_1C_value_giving_max_output": 12698,
            "_1C_Module_1C_Minimum_electrical_output": 12701,
            "_1C_Module_1C_Maximum_electrical": 12700,
            "_1C_Sense_of_output__nor_inv_as_1A": 12683,
            "_1C_Summary_of_1C_configuration": 12680,
            "_1C_Summary_program_O_P_1C_config": 12697,

            "_2A_Module_identity": 12736,
            "_2A_Module_function": 12739,
            "_2A_PID_or_Retran_low_value": 12751,
            "_2A_Potentiometer_input_low_scalar": 12763,
            "_2A_PID_or_Retran_high_value": 12750,
            "_2A_Potentiometer_input_high_scalar": 12762,
            "_2A_Units": 12748,
            "_2A_Minimum_electrical_output": 12753,
            "_2A_Maximum_electrical_output": 12752,
            "_2A_Sense_of_output": 12745,
            "_2A_Summary_output_2A_configuration": 12742,
            "_2A_Program_summary_output_2A_conf": 12759,

            "_2B_Module_2B_identity": 12737,
            "_2B_Module_2B_function": 12740,
            "_2B_Sense_of_output__nor_inv_as_2A": 12746,
            "_2B_Summary_of_2B_configuration": 12743,
            "_2B_Summary_program_O_P_2B_config": 12760,

            "_2C_Module_2C_identity": 12738,
            "_2C_Module_2C_function": 12741,
            "_2C_Sense_of_output__nor_inv_as_2A": 12747,
            "_2C_Summary_of_2C_configuration": 12744,
            "_2C_Summary_program_O_P_2C_config": 12761,

            "_3A_Module_identity": 12800,
            "_3A_Module_function": 12803,
            "_3A_input_type__input_2": 12830,
            "_3A_Cold_junction_compensation__ip_2": 12831,
            "_3A_Sensor_break_impedance__input_2": 12813,
            "_3A_Input_value_low": 12819,
            "_3A_Input_value_high": 12818,
            "_3A_Input_module_3A_low_value": 12829,
            "_3A_Input_module_3A_high_value": 12828,
            "_3A_Module_3A_low_value": 12815,
            "_3A_Potentiometer_input_3A_low_scalar": 12827,
            "_3A_Module_3A_high_value": 12814,
            "_3A_Potentiometer_input_3A_high_scalar": 12826,
            "_3A_Units_3A": 12812,
            "_3A_Minimum_electrical_output": 12817,
            "_3A_Maximum_electrical_output": 12816,
            "_3A_Sense_of_output": 12809,
            "_3A_Summary_output_3A_configuration": 12806,
            "_3A_Program_summary_output_3A_config": 12823,

            "_3B_Module_3B_identity": 12801,
            "_3B_Module_3B_function": 12804,
            "_3B_Sense_of_output__nor_inv_as_3A": 12810,
            "_3B_Summary_of_3B_configuration": 12807,
            "_3B_Summary_program_O_P_3B_config": 12824,

            "_3C_Module_3C_identity": 12802,
            "_3C_Module_3C_function": 12805,
            "_3C_Sense_of_output__nor_inv_as_3A": 12811,
            "_3C_Summary_of_3C_configuration": 12808,
            "_3C_Summary_program_O_P_3C_config": 12825,

            "_4A_Module_identity": 12864,
            "_4A_Module_function": 12867,
            "_4A_Input_module_4A_low_value": 12879,
            "_4A_Input_module_4A_high_value": 12878,
            "_4A_Minimum_electrical_output": 12881,
            "_4A_Maximum_electrical_output": 12880,
            "_4A_Sense_of_output__nor_inv_as_3A": 12873,
            "_4A_Summary_output_4A_configuration": 12870,
            "_4A_Program_summary_output_4A_config": 12887,
            "Access_Mode_Password": 514,
            "Configuration_Level_Password": 515,
        }
        self.serialPort = 'COM9'
        self.slaveAddress = 1
        self.baudrate = BAUD
        self.instrument = minimalmodbus.Instrument(self.serialPort, self.slaveAddress)
        self.instrument.serial.baudrate = self.baudrate

    @setting(10, returns='?')
    def get_temperature(self, c):
        try:
            res = yield self.instrument.read_register(self._registers['Process_Variable'], 0)
            return res
        except minimalmodbus.InvalidResponseError:
            print("Response Error in get_temperature")
            return "INVALID"

    @setting(11, returns='?')
    def get_setpoint(self, c):
        #register32bits = int(str((2 * self._registers['Target_setpoint'] + 8000)), 16)
        try:
            res = yield self.instrument.read_register(self._registers['Target_setpoint'], 0)
            return res
        except minimalmodbus.InvalidResponseError:
            print("Response Error in get_setpoint")
            return "INVALID"

    @setting(12, value='?', returns='?')
    def set_setpoint(self, c, value):
        '''
        Change the setpoint to the value at the current ramp rate. Ramp rate can be
        set with the set_ramprate function. In manual mode will just change it.

        Works in integer values.
        '''
        if type(value) != int:
            value = int(value)
        #register32bits = int(str((2 * self._registers['Target_setpoint'] + 8000)), 16)
        res = yield self.instrument.write_register(self._registers['Target_setpoint'], value)
        return res

    @setting(13, returns='?')
    def get_P(self, c):
        res = yield self.instrument.read_register(self._registers['Proportional_band_PID1'], 0)
        return res

    @setting(14, value='?', returns='?')
    def set_P(self, c, value):
        res = yield self.instrument.write_register(self._registers['Proportional_band_PID1'], value)
        return res

    @setting(15, returns='?')
    def get_I(self, c):
        res = yield self.instrument.read_register(self._registers['Integral_time_PID1'], 0)
        return res

    @setting(16, value='?', returns='?')
    def set_I(self, c, value):
        res = yield self.instrument.write_register(self._registers['Integral_time_PID1'], value)
        return res

    @setting(17, returns='?')
    def get_D(self, c):
        res = yield self.instrument.read_register(self._registers['Derivative_time_PID1'], 0)
        return res

    @setting(18, value='?', returns='?')
    def set_D(self, c, value):
        res = yield self.instrument.write_register(self._registers['Derivative_time_PID1'], value)
        return res

    @setting(19, returns='?')
    def toggle_autotune(self, c):
        mode = yield self.instrument.read_register(self._registers['Autotune_enable'], 0)
        if mode == 0:
            res = yield self.instrument.write_register(self._registers['Autotune_enable'], 1)
        else:
            res = yield self.instrument.write_register(self._registers['Autotune_enable'], 0)
        mode = yield self.instrument.read_register(self._registers['Autotune_enable'], 0)
        return mode

    @setting(20, returns='?')
    def get_autotune(self, c):
        res = yield self.instrument.read_register(self._registers['Autotune_enable'], 0)
        return res

    @setting(21, returns='?')
    def get_power(self, c):
        try:
            register32bits = int(str((2 * self._registers['pc_Output_power'] + 8000)), 16)
            res = yield self.instrument.read_float(register32bits)
        except minimalmodbus.InvalidResponseError:
            print("Invalid Response to get_power")
            res = "INVALID"
        return res

    @setting(22, value='?', returns='?')
    def set_power(self, c, value):
        '''
        Set the output power, needs to be in manual mode.
        '''
        register32bits = int(str((2 * self._registers['pc_Output_power'] + 8000)), 16)
        res = yield self.instrument.write_float(register32bits, value)
        return res

    @setting(23, returns='?')
    def get_auto_manual(self, c):
        '''
        Return automatic or manual mode
        '''
        res = yield self.instrument.read_register(self._registers['Auto_man_select'], 0)
        return res

    @setting(24, returns='?')
    def toggle_auto_manual(self, c):
        '''
        Toggles automatic or manual mode
        '''
        mode = yield self.instrument.read_register(self._registers['Auto_man_select'], 0)
        if mode == 1:
            res = yield self.instrument.write_register(self._registers['Auto_man_select'], 0)
        else:
            res = yield self.instrument.write_register(self._registers['Auto_man_select'], 1)
        mode = yield self.instrument.read_register(self._registers['Auto_man_select'], 0)
        return mode

    @setting(25, returns='?')
    def set_auto_mode(self, c):
        '''
        Turns the controller into automatic mode, which is used for normal operation.
        '''
        yield self.instrument.write_register(self._registers['Auto_man_select'], 0)
        mode = yield self.instrument.read_register(self._registers['Auto_man_select'], 0)
        return mode

    @setting(26, returns='?')
    def set_manual_mode(self, c):
        '''
        Turns the controller into manual mode, generall used when shutting down
        '''
        res = yield self.instrument.write_register(self._registers['Auto_man_select'], 1)
        mode = yield self.instrument.read_register(self._registers['Auto_man_select'], 0)
        return mode

    @setting(27, returns='?')
    def ramp_to_room(self, c):
        '''
        Ramps the setpoint down to slightly below room temeprature, ramping
        down the output. Safer for the crucible than just turning the output off.
        '''
        ramprate = yield self.get_ramprate(c) # Get the ramprate in C/Min
        if ramprate > 60:
            yield self.set_ramprate(c, 60)
        yield self.set_setpoint(c, 20)
        #

    @setting(28, returns='?', T='?')
    def ramp_to_idle_temp(self,c,T=None):
        '''
        Change the temperature to an idle temeprature. If a temperature is not given
        will set the temperature to 650C
        '''
        ramprate = yield self.get_ramprate(c) # Get the ramprate in C/Min
        if ramprate > 60:
            yield self.set_ramprate(c, 60)
        if T is None or not isinstance(T, (int,float)):
            T = 650
        yield self.set_setpoint(c, T)


    @setting(32, returns='?')
    def zero_output(self, c):
        '''
        FOR SAFETY, RAMP DOWN FROM HIGH TEMPERATURES. Use at the end of a rampdown
        or in emergency senario.

        Turns the controller into manual mode and set the output power 0.
        '''
        res = yield self.instrument.write_register(self._registers['Auto_man_select'], 1)
        mode = yield self.instrument.read_register(self._registers['Auto_man_select'], 0)
        register32bits = int(str((2 * self._registers['pc_Output_power'] + 8000)), 16)
        res = yield self.instrument.write_float(register32bits, 0.0) # Set the power to zero
        return res

    @setting(34, returns='?')
    def get_ramprate(self, c):
        '''
        Gets the setpoint ramprate in units of C/Min.
        '''
        try:
            res = yield self.instrument.read_register(self._registers['Setpoint_rate_limit'])
            return res
        except minimalmodbus.InvalidResponseError:
            print("Response Error in get_temperature")
            return "INVALID"

    @setting(35, value='?', returns='?')
    def set_ramprate(self, c, value):
        '''
        Changes the temeprature setpoint ramprate.
        '''
        res = yield self.instrument.write_register(self._registers['Setpoint_rate_limit'], value)
        return res

    @setting(36, returns='?')
    def get_ramprate_units(self, c):
        '''
        Get the setpoint ramp rate units, 0 = C/second, 1 = C/Min, 2 = C/Hour
        We generally use 1 (C/Min)
        '''

        res = yield self.instrument.read_register(self._registers['Instrument_Mode'])
        print("Instrument Mode", res)

        res = yield self.instrument.read_register(self._registers['Setpoint_rate_limit_units'])
        print("Rate Limit Units", res)
        return res

    @setting(37, returns='?')
    def get_output_rate_limit(self, c):
        '''
        Get the output rate limit (% per second)
        '''
        res = yield self.instrument.read_register(self._registers['Output_rate_limit'], number_of_decimals=1)
        return res

    @setting(38, value='i', returns='?')
    def set_output_rate_limit(self, c, value):
        '''
        set the output rate limit, (integer % per second)
        '''
        res = yield self.instrument.write_register(self._registers['Output_rate_limit'], value, number_of_decimals=1)
        return res

    @setting(39, returns='?')
    def get_output_max(self, c):
        '''
        Get the output maximum (%)
        '''
        try:
            res = yield self.instrument.read_register(self._registers['High_power_limit'], number_of_decimals=1)
            return res
        except minimalmodbus.InvalidResponseError:
            print("Response Error in get_temperature")
            return "INVALID"
        return res

    @setting(40, value='i', returns='?')
    def set_output_max(self, c, value):
        '''
        set the output maximum, (integer %)
        '''
        res = yield self.instrument.write_register(self._registers['High_power_limit'], value, number_of_decimals=1)
        return res


    '''
    Configuration Functions

    USE WITH CAUTION! Not only will changing the configuration mode stop
    any active process and put the controller in safe mode but setting the mode wrong
    could damage the calibration.

    BE CAREFUL AND READ THE MANUAL WELL
    '''
    @setting(236, returns='?')
    def set_ramprate_units(self, c):
        '''
        CAREFUL! USE WITH CAUTION! Not only will this stop any active process and put
        the controller in safe mode but setting the mode wrong could damage the calibration.
        BE CAREFUL AND READ THE MANUAL WELL

        Set the setpoint ramp rate units, 0 = C/second, 1 = C/Min, 2 = C/Hour
        '''

        # To prevent errors this function just returns, comment the below block to
        # use it and remember to comment it when you are done.
        print("TO PREVENT ERRORS set_ramprate_units IS DIABLED. UNCOMMENT BLOCK TO USE")
        return "DISABLED"

        res = yield self.instrument.write_register(self._registers['Instrument_Mode'], 2)
        print("Instrument Mode set to configuration")

        res = yield self.instrument.write_register(self._registers['Setpoint_rate_limit_units'], 1)
        print("Rate Limit Units Set To", res)

        res = yield self.instrument.write_register(self._registers['Instrument_Mode'], 0)
        print("Instrument Mode Set to normal")

        return res


__server__ = EurothermServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
