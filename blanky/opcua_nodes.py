"""OPC UA nodes documented for the Blanky <-> PLC Send&Receive link."""

# Command nodes belong to the PLC's "OPC UA Enviar" namespace (currently ns=4).
COMMAND_TO_NODE = {
    "START": "ns=4;i=2",
    "STOP": "ns=4;i=3",
    "MODE_FAST": "ns=4;i=4",
    "MODE_IDEAL": "ns=4;i=5",
    "MODE_MANUAL": "ns=4;i=6",
    "MODE_UNSPEC": "ns=4;i=7",
    "MOTOR_1_ON": "ns=4;i=8",
    "MOTOR_2_ON": "ns=4;i=9",
    "MOTOR_3_ON": "ns=4;i=10",
    "CYL_A_EXTEND": "ns=4;i=11",
    "CYL_B_EXTEND": "ns=4;i=12",
    "CYL_C_EXTEND": "ns=4;i=13",
    "CYL_D_EXTEND": "ns=4;i=14",
    "GREEN_ON": "ns=4;i=15",
    "RED_ON": "ns=4;i=16",
    "ROBOT_TO_METAL": "ns=4;i=17",
    "ROBOT_TO_NONMETAL": "ns=4;i=18",
    "MOTOR_1_OFF": "ns=4;i=29",
    "MOTOR_2_OFF": "ns=4;i=40",
    "MOTOR_3_OFF": "ns=4;i=51",
    "CYL_A_RETRACT": "ns=4;i=62",
    "CYL_B_RETRACT": "ns=4;i=73",
    "GREEN_OFF": "ns=4;i=84",
    "RED_OFF": "ns=4;i=95",
}

# The current PLC map has no separate retract command for C/D.
COMMAND_LEVEL_FALLBACK = {
    "CYL_C_RETRACT": ("ns=4;i=13", False),
    "CYL_D_RETRACT": ("ns=4;i=14", False),
}

RECEIVE_NAMESPACE_URI = "http://OPC UA Receber"

# These are PLC Send&Receive signals, not necessarily physical position sensors.
RECEIVE_NODE_IDENTIFIERS = {
    "system_on": 2,
    "system_stopped": 3,
    "mode_fast": 4,
    "mode_ideal": 5,
    "mode_manual": 6,
    "mode_change": 7,
    "motor_1_on": 8,
    "motor_1_off": 9,
    "motor_2_on": 10,
    "motor_2_off": 11,
    "motor_3_on": 12,
    "motor_3_off": 13,
    "cyl_a_advanced": 14,
    "cyl_a_retracted": 15,
    "cyl_b_advanced": 16,
    "cyl_b_retracted": 17,
    "cyl_c_advance_signal": 18,
    "cyl_d_advance_signal": 19,
    "green_on": 20,
    "green_off": 21,
    "red_on": 22,
    "red_off": 23,
    "robot_metal": 24,
    "robot_nonmetal": 25,
    "system_error": 26,
}

COMMAND_TO_RECEIVE_SIGNAL = {
    "START": "system_on",
    "STOP": "system_stopped",
    "MODE_FAST": "mode_fast",
    "MODE_IDEAL": "mode_ideal",
    "MODE_MANUAL": "mode_manual",
    "MODE_UNSPEC": "mode_change",
    "MOTOR_1_ON": "motor_1_on",
    "MOTOR_1_OFF": "motor_1_off",
    "MOTOR_2_ON": "motor_2_on",
    "MOTOR_2_OFF": "motor_2_off",
    "MOTOR_3_ON": "motor_3_on",
    "MOTOR_3_OFF": "motor_3_off",
    "CYL_A_EXTEND": "cyl_a_advanced",
    "CYL_A_RETRACT": "cyl_a_retracted",
    "CYL_B_EXTEND": "cyl_b_advanced",
    "CYL_B_RETRACT": "cyl_b_retracted",
    "CYL_C_EXTEND": "cyl_c_advance_signal",
    "CYL_D_EXTEND": "cyl_d_advance_signal",
    "GREEN_ON": "green_on",
    "GREEN_OFF": "green_off",
    "RED_ON": "red_on",
    "RED_OFF": "red_off",
    "ROBOT_TO_METAL": "robot_metal",
    "ROBOT_TO_NONMETAL": "robot_nonmetal",
}

# PLC Maquete input addresses from the TIA screenshot. Their OPC UA node IDs
# have not yet been supplied, so they must not be guessed from these addresses.
PHYSICAL_SENSOR_INPUTS = {
    "cyl_c_retracted": "%I2.0",
    "cyl_c_advanced": "%I2.1",
    "cyl_d_retracted": "%I2.2",
    "cyl_d_advanced": "%I2.3",
}
