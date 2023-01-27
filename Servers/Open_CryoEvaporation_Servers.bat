start labrad
timeout 5
start python Servers/serial_server.py
timeout 3
start python Servers/gpib_server.py
timeout 3
start python Servers/gpib_device_manager.py
timeout 3
start python Servers/data_vault.py
timeout 2
start python Servers/RVC_300.py
timeout 2
start python Servers/FTM_2400.py
timeout 2
start python Servers/Valve_Relay_Server.py
timeout 2
start python Servers/TDK_GEN10-240.py
timeout 2
start python Servers/Evaporator_Shutter_Control.py
timeout 2
start python Servers/SIM921.py
timeout 2
start python Servers/Lakeshore336.py
timeout 2
start python Servers/sr860_evap.py