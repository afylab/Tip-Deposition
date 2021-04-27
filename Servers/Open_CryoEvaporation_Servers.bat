echo off
start labrad
timeout 3
start python Servers/serial_server.py
timeout 1
start python Servers/data_vault.py
timeout 1
start python Servers/RVC_300.py
timeout 1
start python Servers/FTM_2400.py
timeout 1
start python Servers/Valve_Relay_Server.py
timeout 1
start python Servers/TDK_GEN10-240.py
timeout 1
start python Servers/Stepper_Server.py
