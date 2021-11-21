The folders contain the following:
#######################################################################
Bin - Binaries for each of the nodes for AODV and the proposes protocol
#######################################################################
HC_06_Config - Basic Arduino sketc to cofnigure the HC-06 with AT commands
The basic ARDUINO IDE can be used to compile the program 
#######################################################################
Python_Interpreter - The main serial interpreter. Contains virtual environment to by used with pycharm
The following libraries are needed:
import matplotlib.pyplot as plt
import numpy as np
import serial
import bitstring
import networkx as nx
from timeit import default_timer as timer
#######################################################################
Python_Interpreter_Tester - Basic program to test the interpreter's functionality
and to confirm if the HC-06 module works, firmware works and the interpreter works:
The following is needed:
The CRYPTO library
MbedOS firmware
Environment that uses the ARM6 or GCC compiler;
Alternatively basic programs can compile on IDE's
Use MBED Studio to compile what is needed
#######################################################################
Python_Simulation - The main simulation platform, the virtual environment for pychamr is included,
else use any suitable environment 
The following libraries are needed:
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
#######################################################################
Routing_Protocol - Contains all the software related to developing the protocol
Includes the tested AODV,
Untested AOMDV and AOMDV-LR
The final protocol called LR-EE-AOMDV-LB
The following is needed:
The CRYPTO library
MbedOS firmware
libmdot library for LoRa functionaility
Environment that uses the ARM6 or GCC compiler;
