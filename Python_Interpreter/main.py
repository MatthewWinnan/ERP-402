import matplotlib.pyplot as plt
import numpy as np
import serial
from scipy.stats import norm
import seaborn as sns
from IPython.display import clear_output
import bitstring

#Setting Print Options For The Terminal
np.set_printoptions(precision=4, linewidth=170, edgeitems=10, floatmode='fixed', sign=' ')
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams.update({'font.size': 13})
live = False

#Setting COM options
#General COM parameters
BYTE_ORDER = 'big'  # or 'big'
SAMPLING_FREQ = 0.2  # Hz (every 5 sec)
SAMPLING_TIME = 20 # Time to sample in seconds
NUM_SAMPLES = int(SAMPLING_TIME/(1/SAMPLING_FREQ) ) # 1 minute
BAUD_RATE = 9600

#PORTS for specific devices
COM_PORT_TEST = 'COM19'
COM_PORT_NODE_CLIENT = 'COM12'
COM_PORT_NODE_1 = 'COM34'
COM_PORT_NODE_2 = 'COM35'
COM_PORT_NODE_3 = 'COM30'
COM_PORT_NODE_4 = 'COM3'
COM_PORT_NODE_DESTINATION = 'COM33'

#TEST PARAMETERS
# What test are we doing????
current_test = 0
# Define the test strings
test_array = ["Case_1"]
#Measurements taken
measurement_array = ["_load_per_node","_pdr_per_node","_etx_per_node","_rssi_per_node","_snr_per_node","_throughput_per_dest","_ping_per_dest","_mdr_per_dest"]

#Store the addresses here
#Address index corresponds to index of the measured node
NODE_index = []

#Store neighbour addresses here
NEIGH_add = []

#Store destination address here
DEST_add = []

#STores client addresses here
CLIENT_add = []

#Stores destination to client adds here
DEST_TO_CLIENT_add = []

#Stores cliebnt to dest adds here
CLIENT_TO_DEST_add = []

#Stores node to destination adds
NODE_TO_DEST_add = []

#Stores node to client adds
NODE_TO_CLIENT_add = []

#Data to be stored defined here
#Store the loads here
LOAD_array = []
#Store amount of packets sent here
PACKETS_sent = []
#Store amount of packets received here
PACKETS_received = []
#Store the average RSSI of received link rememeber it is signed
RSSI_value = []
#Store the average SNR of received link rememeber this is again unsigned???? makes sure
SNR_value = []
#Stores the routing table next hop entries for each node for a given destination
ROUTING_table_next = []
#STores the next hop for the chosen path
ROUTING_table_path = []
#Stores the amount of messages packets received per epoch
Dest_RX_Amount = []
#Stores the average PING for received messages
Dest_PING_Amount = []
#Stores the amount of messages sent by client to destination per epoch
Client_TX_Amount = []
#STores the PDR for each link between node x and neighbour y
NODE_PDR_value = []
#Stores the ETX for each link between node x and neighbour y
NODE_ETX_value = []

X_axis = np.linspace(0, (NUM_SAMPLES - 1) / SAMPLING_FREQ, NUM_SAMPLES)

# Libraries to decode byte stream
Start_Byte = ['S','L','P','N','R','M','T','C','D']
Second_Byte = ['T','D','S','A','R','I','N','E','P']
Packet_Headers = ['MS','PI','MR','SN','RI','NS','PR','RA','ND','PS','LD','ST','TE','CP','DA','CN']
Stop_Byte = 13 #Line feed denotes the end of line
Next_Line = 10 #Endl indicates next measurement
#Denotes the n'th byte of the header we are looking for
header = 0
#Denotes global variable for rx data byte
rxData = 0
#Denotes the global variab;e to store current header
current_header = ''
#Keeps count of the amount of loops currently performed
loops = 0
#Libraries for graphing
DATATYPE_LIST = ['Load (packets/s)','Packet Delivery Ration','ETX value for link','RSSI for link (dB)','SNR for link (dB)','Throughput (packets/s)','Packet Delay (ms)','Message Delivery Ratio']
LINE_COLORS = ['b','g','r','c','m','y','k','w']
#Defining clock per second for microcontroller
CLOCKS_PER_SEC = 100

def wait_for_start(ser):
    global rxData
    global current_header
    global header

    current_header = ''
    while current_header != 'ST':
        print("wait_for_start current byte is "+ chr(rxData) + " and current header is "+current_header)
        #Resets if header not yet found
        if (header == 2):
            current_header=''
            header = 0
        #Adds first byte
        if (chr(rxData) in Start_Byte) and (header == 0) :
            current_header+=chr(rxData)
            header = 1
        #If first byte found adds second byte
        elif (chr(rxData) in Second_Byte) and (header == 1):
            current_header+=chr(rxData)
            header = 2
        #Reads next byte
        rxData = int.from_bytes(ser.read(1), "big")

def wait_for_header(wait_byte,ser):
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''
    shift = 0


    while current_header != wait_byte:
        print("Waiting for header " + wait_byte+ " current byte is " + chr(rxData) + " and current header is " + current_header)
        # Resets if header not yet found
        if (header == 2):
            current_header = ''
            header = 0
            #An error occured
            print(wait_byte+" not found wtf")
            exit()
        # Adds first byte
        if (chr(rxData) in Start_Byte) and (header == 0):
            current_header += chr(rxData)
            header = 1
        # If first byte found adds second byte
        elif (chr(rxData) in Second_Byte) and (header == 1):
            current_header += chr(rxData)
            header = 2
        # Reads next byte
        rxData = int.from_bytes(ser.read(1), "big")

def wait_for_load_value(ser):
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''
    shift = 0

    wait_for_header('LD',ser)
    # while current_header != 'LD':
    #     print("wait_for_load_value current byte is " + chr(rxData) + " and current header is " + current_header)
    #     # Resets if header not yet found
    #     if (header == 2):
    #         current_header = ''
    #         header = 0
    #         #An error occured
    #         print("LD not found wtf")
    #         exit()
    #     # Adds first byte
    #     if (chr(rxData) in Start_Byte) and (header == 0):
    #         current_header += chr(rxData)
    #         header = 1
    #     # If first byte found adds second byte
    #     elif (chr(rxData) in Second_Byte) and (header == 1):
    #         current_header += chr(rxData)
    #         header = 2
    #     # Reads next byte
    #     rxData = int.from_bytes(ser_Test.read(1), "big")

def wait_for_neighbour_destination_add(ser):
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''
    shift = 0

    wait_for_header('ND',ser)
    # while current_header != 'ND':
    #     print("wait_for_neighbour_destination_add current byte is " + chr(rxData) + " and current header is " + current_header)
    #     # Resets if header not yet found
    #     if (header == 2):
    #         current_header = ''
    #         header = 0
    #         #An error occured
    #         print("ND not found wtf")
    #         exit()
    #     # Adds first byte
    #     if (chr(rxData) in Start_Byte) and (header == 0):
    #         current_header += chr(rxData)
    #         header = 1
    #     # If first byte found adds second byte
    #     elif (chr(rxData) in Second_Byte) and (header == 1):
    #         current_header += chr(rxData)
    #         header = 2
    #     # Reads next byte
    #     rxData = int.from_bytes(ser_Test.read(1), "big")

def wait_for_neighbour_source_add(ser):
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''
    shift = 0
    wait_for_header('NS',ser)
    # while current_header != 'NS':
    #     print("wait_for_neighbour_source_add current byte is " + chr(rxData) + " and current header is " + current_header)
    #     # Resets if header not yet found
    #     if (header == 2):
    #         current_header = ''
    #         header = 0
    #         #An error occured
    #         print("NS not found wtf")
    #         exit()
    #     # Adds first byte
    #     if (chr(rxData) in Start_Byte) and (header == 0):
    #         current_header += chr(rxData)
    #         header = 1
    #     # If first byte found adds second byte
    #     elif (chr(rxData) in Second_Byte) and (header == 1):
    #         current_header += chr(rxData)
    #         header = 2
    #     # Reads next byte
    #     rxData = int.from_bytes(ser_Test.read(1), "big")

def wait_for_neighbour_sent_amount_head(ser):
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''
    shift = 0

    wait_for_header('PS',ser)
    # while current_header != 'PS':
    #     print("wait_for_neighbour_sent_amount_head current byte is " + chr(rxData) + " and current header is " + current_header)
    #     # Resets if header not yet found
    #     if (header == 2):
    #         current_header = ''
    #         header = 0
    #         #An error occured
    #         print("PS not found wtf")
    #         exit()
    #     # Adds first byte
    #     if (chr(rxData) in Start_Byte) and (header == 0):
    #         current_header += chr(rxData)
    #         header = 1
    #     # If first byte found adds second byte
    #     elif (chr(rxData) in Second_Byte) and (header == 1):
    #         current_header += chr(rxData)
    #         header = 2
    #     # Reads next byte
    #     rxData = int.from_bytes(ser_Test.read(1), "big")

def wait_for_neighbour_receive_amount_head(ser):
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''
    shift = 0

    wait_for_header('PR',ser)
    # while current_header != 'PR':
    #     print("wait_for_neighbour_receive_amount_head current byte is " + chr(rxData) + " and current header is " + current_header)
    #     # Resets if header not yet found
    #     if (header == 2):
    #         current_header = ''
    #         header = 0
    #         #An error occured
    #         print("PR not found wtf")
    #         exit()
    #     # Adds first byte
    #     if (chr(rxData) in Start_Byte) and (header == 0):
    #         current_header += chr(rxData)
    #         header = 1
    #     # If first byte found adds second byte
    #     elif (chr(rxData) in Second_Byte) and (header == 1):
    #         current_header += chr(rxData)
    #         header = 2
    #     # Reads next byte
    #     rxData = int.from_bytes(ser_Test.read(1), "big")

def wait_for_next(ser):
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''
    shift = 0

    wait_for_header('RA',ser)
    # while current_header != 'RA':
    #     print("wait_for_next current byte is " + chr(rxData) + " and current header is " + current_header)
    #     # Resets if header not yet found
    #     if (header == 2):
    #         current_header = ''
    #         header = 0
    #         #An error occured
    #         print("RA not found wtf")
    #         exit()
    #     # Adds first byte
    #     if (chr(rxData) in Start_Byte) and (header == 0):
    #         current_header += chr(rxData)
    #         header = 1
    #     # If first byte found adds second byte
    #     elif (chr(rxData) in Second_Byte) and (header == 1):
    #         current_header += chr(rxData)
    #         header = 2
    #     # Reads next byte
    #     rxData = int.from_bytes(ser_Test.read(1), "big")

def wait_for_stop(ser):
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''

    while (rxData!=Next_Line):
        # Reads next byte
        rxData = int.from_bytes(ser.read(1), "big")


def read_load_data(ser):
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''

    while (rxData != Stop_Byte):
        print("read_load_data current byte is " + str(rxData))
        #Adds the measurement to the variable
        load = load<<8 | rxData
        # Reads next byte
        rxData = int.from_bytes(ser.read(1), "big")
    while (rxData!=Next_Line):
        # Reads next byte
        rxData = int.from_bytes(ser.read(1), "big")
    return load

def read_in_measurement(ser):
    global rxData
    global current_header
    global header

    sent = 0
    current_header = ''

    while (rxData != Stop_Byte) and (chr(rxData) != 'R'):
        print("read_in_measurement current byte is " + str(rxData))
        #Adds the measurement to the variable
        sent = sent<<8 | rxData
        # Reads next byte
        rxData = int.from_bytes(ser.read(1), "big")
    return sent



def measure_RSSI(ser):
    global rxData
    global current_header
    global header
    #We make a unique one since this needs to be signed
    sent = 0
    current_header = ''
    loop = 0

    while (rxData != Stop_Byte) and (chr(rxData) != 'R'):
        print("read_in_RSSI current byte is " + str(rxData))
        #Adds the measurement to the variable
        sent = sent<<8 | rxData
        # Reads next byte
        rxData = int.from_bytes(ser.read(1), "big")
        loop+=1
    #Convert from unsigned to signed
    sent = bitstring.BitArray(uint = sent, length=loop*8).int
    return sent

def read_in_AMOUNT_RX(ser):
    global rxData
    global current_header
    global header
    #We make a unique one since this needs to be signed
    sent = 0
    current_header = ''
    loop = 0

    while (rxData != Stop_Byte) and (chr(rxData) != 'P'):
        print("read_in_AMOUNT_RX current byte is " + str(rxData))
        #Adds the measurement to the variable
        sent = sent<<8 | rxData
        # Reads next byte
        rxData = int.from_bytes(ser.read(1), "big")
        loop+=1
    return sent

def read_in_packet_sent_data(ser):
    global rxData
    global current_header
    global header

    #We do this until an end line is obtained
    rxData = int.from_bytes(ser.read(1), "big")
    while (rxData!= Stop_Byte) and (rxData!=Next_Line ):
        # First reset trackers
        header = 0
        current_header = ''
        # First measurement is address
        if rxData not in NODE_index:
            NODE_index.append(rxData)
        #Create the first entry into neighbour list if none exhists
        if len(NEIGH_add)==0:
            holder=[]
            NEIGH_add.append(holder)
        #Obtain the index of the node
        Address_Index = NODE_index.index(rxData)
        #Now wait for the queue to start obtaining the niehgbour address
        rxData = int.from_bytes(ser.read(1), "big")
        wait_for_neighbour_destination_add(ser)
        #Remember last read byte is not looked at by while loop
        #Thus that is the start of the address
        neighbour_add = rxData
        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        if len(NEIGH_add) == Address_Index:
            holder = [neighbour_add]
            NEIGH_add.append(holder)
        else:
            if neighbour_add not in NEIGH_add[Address_Index]:
                NEIGH_add[Address_Index].append(neighbour_add)

        Address_Index_Neigh = NEIGH_add[Address_Index].index(neighbour_add)
        #Now obtain the packet sent list , first wait for header
        rxData = int.from_bytes(ser.read(1), "big")
        # Clear header trackers
        header = 0
        current_header = ''
        wait_for_neighbour_sent_amount_head(ser)
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        packets_sent = read_in_measurement(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        if len(PACKETS_sent)==Address_Index:
            holder=[]
            PACKETS_sent.append(holder)
        if len(PACKETS_sent[Address_Index])==Address_Index_Neigh:
            holder=[]
            PACKETS_sent[Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        PACKETS_sent[Address_Index][Address_Index_Neigh].append(packets_sent)
        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            wait_for_next(ser)
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.

def read_in_packet_received_data(ser):
    global rxData
    global current_header
    global header

    #We do this until an end line is obtained
    rxData = int.from_bytes(ser.read(1), "big")
    while (rxData!= Stop_Byte) and (rxData!=Next_Line ):
        # First reset trackers
        header = 0
        current_header = ''
        # First measurement is address
        if rxData not in NODE_index:
            NODE_index.append(rxData)
        #Create the first entry into neighbour list if none exhists
        if len(NEIGH_add)==0:
            holder=[]
            NEIGH_add.append(holder)
        #Obtain the index of the node
        Address_Index = NODE_index.index(rxData)
        #Now wait for the queue to start obtaining the niehgbour address
        rxData = int.from_bytes(ser.read(1), "big")
        wait_for_neighbour_source_add(ser)
        #Remember last read byte is not looked at by while loop
        #Thus that is the start of the address
        neighbour_add = rxData
        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        if len(NEIGH_add) == Address_Index:
            holder = [neighbour_add]
            NEIGH_add.append(holder)
        else:
            if neighbour_add not in NEIGH_add[Address_Index]:
                NEIGH_add[Address_Index].append(neighbour_add)

        Address_Index_Neigh = NEIGH_add[Address_Index].index(neighbour_add)
        #Now obtain the packet sent list , first wait for header
        rxData = int.from_bytes(ser.read(1), "big")
        # Clear header trackers
        header = 0
        current_header = ''
        wait_for_neighbour_receive_amount_head(ser)
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        packets_received = read_in_measurement(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        if len(PACKETS_received)==Address_Index:
            holder=[]
            PACKETS_received.append(holder)
        if len(PACKETS_received[Address_Index])==Address_Index_Neigh:
            holder=[]
            PACKETS_received[Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        PACKETS_received[Address_Index][Address_Index_Neigh].append(packets_received)
        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            wait_for_next(ser)
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.

def read_in_RSSI(ser):
    global rxData
    global current_header
    global header

    #We do this until an end line is obtained
    rxData = int.from_bytes(ser.read(1), "big")
    while (rxData!= Stop_Byte) and (rxData!=Next_Line ):
        # First reset trackers
        header = 0
        current_header = ''
        # First measurement is address
        if rxData not in NODE_index:
            NODE_index.append(rxData)
        #Create the first entry into neighbour list if none exhists
        if len(NEIGH_add)==0:
            holder=[]
            NEIGH_add.append(holder)
        #Obtain the index of the node
        Address_Index = NODE_index.index(rxData)
        #Now wait for the queue to start obtaining the niehgbour address
        rxData = int.from_bytes(ser.read(1), "big")
        wait_for_neighbour_source_add(ser)
        #Remember last read byte is not looked at by while loop
        #Thus that is the start of the address
        neighbour_add = rxData
        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        if len(NEIGH_add) == Address_Index:
            holder = [neighbour_add]
            NEIGH_add.append(holder)
        else:
            if neighbour_add not in NEIGH_add[Address_Index]:
                NEIGH_add[Address_Index].append(neighbour_add)

        Address_Index_Neigh = NEIGH_add[Address_Index].index(neighbour_add)
        #Now obtain the packet sent list , first wait for header
        rxData = int.from_bytes(ser.read(1), "big")
        # Clear header trackers
        header = 0
        current_header = ''
        #Now wait for the RSSI start header
        wait_for_header('RI',ser)
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        RSSI_result = measure_RSSI(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        if len(RSSI_value)==Address_Index:
            holder=[]
            RSSI_value.append(holder)
        if len(RSSI_value[Address_Index])==Address_Index_Neigh:
            holder=[]
            RSSI_value[Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        RSSI_value[Address_Index][Address_Index_Neigh].append(RSSI_result)
        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            wait_for_next(ser)
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.

def read_in_SNR(ser):
    global rxData
    global current_header
    global header

    #We do this until an end line is obtained
    rxData = int.from_bytes(ser.read(1), "big")
    while (rxData!= Stop_Byte) and (rxData!=Next_Line ):
        # First reset trackers
        header = 0
        current_header = ''
        # First measurement is address
        if rxData not in NODE_index:
            NODE_index.append(rxData)
        #Create the first entry into neighbour list if none exhists
        if len(NEIGH_add)==0:
            holder=[]
            NEIGH_add.append(holder)
        #Obtain the index of the node
        Address_Index = NODE_index.index(rxData)
        #Now wait for the queue to start obtaining the niehgbour address
        rxData = int.from_bytes(ser.read(1), "big")
        wait_for_neighbour_source_add(ser)
        #Remember last read byte is not looked at by while loop
        #Thus that is the start of the address
        neighbour_add = rxData
        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        if len(NEIGH_add) == Address_Index:
            holder = [neighbour_add]
            NEIGH_add.append(holder)
        else:
            if neighbour_add not in NEIGH_add[Address_Index]:
                NEIGH_add[Address_Index].append(neighbour_add)

        Address_Index_Neigh = NEIGH_add[Address_Index].index(neighbour_add)
        #Now obtain the packet sent list , first wait for header
        rxData = int.from_bytes(ser.read(1), "big")
        # Clear header trackers
        header = 0
        current_header = ''
        #Now wait for the SNR start header
        wait_for_header('SN',ser)
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        SNR_result = read_in_measurement(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        if len(SNR_value)==Address_Index:
            holder=[]
            SNR_value.append(holder)
        if len(SNR_value[Address_Index])==Address_Index_Neigh:
            holder=[]
            SNR_value[Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        SNR_value[Address_Index][Address_Index_Neigh].append(SNR_result)
        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            wait_for_next(ser)
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.

def read_in_ROUTING_TABLE(ser):
    global rxData
    global current_header
    global header

    #We do this until an end line is obtained
    rxData = int.from_bytes(ser.read(1), "big")
    #We can do this outside as this measurement only repeats the TE entries
    while (rxData!= Stop_Byte) and (rxData!=Next_Line ):
        # First reset trackers
        header = 0
        current_header = ''
        # First measurement is address
        if rxData not in NODE_index:
            NODE_index.append(rxData)
        # Create the first entry into dest list if none exhists
        if len(NODE_TO_DEST_add) == 0:
            holder = []
            NODE_TO_DEST_add.append(holder)

        # Obtain the index of the node
        Address_Index = NODE_index.index(rxData)
        # Now wait for the queue to start obtaining the destination address
        rxData = int.from_bytes(ser.read(1), "big")
        wait_for_header('DA', ser)
        # Remember last read byte is not looked at by while loop
        # Thus that is the start of the address
        destination_add = rxData
        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        if len(NODE_TO_DEST_add) == Address_Index:
            holder = [destination_add]
            NODE_TO_DEST_add.append(holder)
        else:
            if destination_add not in NODE_TO_DEST_add[Address_Index]:
                NODE_TO_DEST_add[Address_Index].append(destination_add)

        Address_Index_Dest = NODE_TO_DEST_add[Address_Index].index(destination_add)
        # Now obtain the chosen path , first wait for header
        rxData = int.from_bytes(ser.read(1), "big")
        # Clear header trackers
        header = 0
        current_header = ''
        # Now wait for the SNR start header
        wait_for_header('CP', ser)
        # Remember last read byte is not looked at by while loop
        # Thus that is the start of the chosen path
        chosen_path_add = rxData
        if len(ROUTING_table_path) == Address_Index:
            holder = []
            ROUTING_table_path.append(holder)
        if len(ROUTING_table_path[Address_Index]) == Address_Index_Dest:
            holder = []
            ROUTING_table_path[Address_Index].append(holder)
        if chosen_path_add != ROUTING_table_path[Address_Index][Address_Index_Dest]:
            ROUTING_table_path[Address_Index][Address_Index_Dest] = chosen_path_add

        # Now obtain the next hop values
        rxData = int.from_bytes(ser.read(1), "big")
        # Clear header trackers
        header = 0
        current_header = ''
        # Now wait for the table enrty start header
        wait_for_header('TE', ser)
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        NEXT_HOP = read_in_measurement(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        if len(ROUTING_table_next)==Address_Index:
            holder=[]
            ROUTING_table_next.append(holder)
        if len(ROUTING_table_next[Address_Index])==Address_Index_Dest:
            holder=[]
            ROUTING_table_next[Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        if NEXT_HOP not in ROUTING_table_next[Address_Index][Address_Index_Dest]:
            ROUTING_table_next[Address_Index][Address_Index_Dest].append(NEXT_HOP)
        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            wait_for_next(ser)
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.


def read_in_AMOUNT_RECEIVED_DEST(ser):
    global rxData
    global current_header
    global header

    #We do this until an end line is obtained
    rxData = int.from_bytes(ser.read(1), "big")
    while (rxData!= Stop_Byte) and (rxData!=Next_Line ):
        # First reset trackers
        header = 0
        current_header = ''
        # First measurement is destination address
        if rxData not in NODE_index:
            NODE_index.append(rxData)
        if rxData not in DEST_add:
            DEST_add.append(rxData)
        #Create the first entry into client list if none exhists
        if len(DEST_TO_CLIENT_add)==0:
            holder=[]
            DEST_TO_CLIENT_add.append(holder)
        #Obtain the index of the node
        Dest_Address_Index = DEST_add.index(rxData)
        #Now wait for the queue to start obtaining the client address
        rxData = int.from_bytes(ser.read(1), "big")
        wait_for_header('CN',ser)
        #Remember last read byte is not looked at by while loop
        #Thus that is the start of the client address
        Client_Address = rxData

        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        if len(DEST_TO_CLIENT_add) == Dest_Address_Index:
            holder = [Client_Address]
            DEST_TO_CLIENT_add.append(holder)
        else:
            if Client_Address not in DEST_TO_CLIENT_add[Dest_Address_Index]:
                DEST_TO_CLIENT_add[Dest_Address_Index].append(Client_Address)

        Address_Index_Client = DEST_TO_CLIENT_add[Dest_Address_Index].index(Client_Address)

        #Now obtain the measurement of amount of packets received , first wait for header
        rxData = int.from_bytes(ser.read(1), "big")
        # Clear header trackers
        header = 0
        current_header = ''
        #Now wait for the RX measurements start header
        wait_for_header('MR',ser)
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        Amount_RX = read_in_AMOUNT_RX(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        if len(Dest_RX_Amount)==Dest_Address_Index:
            holder=[]
            Dest_RX_Amount.append(holder)
        if len(Dest_RX_Amount[Dest_Address_Index])==Address_Index_Client:
            holder=[]
            Dest_RX_Amount[Dest_Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        Dest_RX_Amount[Dest_Address_Index][Address_Index_Client].append(Amount_RX)

        #Now wait for the PING measurements start header
        wait_for_header('PI',ser)
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        Amount_PING = read_in_measurement(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        if len(Dest_PING_Amount)==Dest_Address_Index:
            holder=[]
            Dest_PING_Amount.append(holder)
        if len(Dest_PING_Amount[Dest_Address_Index])==Address_Index_Client:
            holder=[]
            Dest_PING_Amount[Dest_Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        Dest_PING_Amount[Dest_Address_Index][Address_Index_Client].append(Amount_PING)


        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            wait_for_next(ser)
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.

def read_in_AMOUNT_SENT_CLIENT(ser):
    global rxData
    global current_header
    global header

    #We do this until an end line is obtained
    rxData = int.from_bytes(ser.read(1), "big")
    while (rxData!= Stop_Byte) and (rxData!=Next_Line ):
        # First reset trackers
        header = 0
        current_header = ''
        # First measurement is destination address
        if rxData not in NODE_index:
            NODE_index.append(rxData)
        if rxData not in CLIENT_add:
            CLIENT_add.append(rxData)
        #Create the first entry into client list if none exhists
        if len(CLIENT_TO_DEST_add)==0:
            holder=[]
            CLIENT_TO_DEST_add.append(holder)
        #Obtain the index of the node
        Client_Address_Index = CLIENT_add.index(rxData)
        #Now wait for the queue to start obtaining the client address
        rxData = int.from_bytes(ser.read(1), "big")
        wait_for_header('DA',ser)
        #Remember last read byte is not looked at by while loop
        #Thus that is the start of the destination address
        Destination_Address = rxData

        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        if len(CLIENT_TO_DEST_add) == Client_Address_Index:
            holder = [Destination_Address]
            CLIENT_TO_DEST_add.append(holder)
        else:
            if Destination_Address not in CLIENT_TO_DEST_add[Client_Address_Index]:
                CLIENT_TO_DEST_add[Client_Address_Index].append(Destination_Address)

        Address_Index_Destination = CLIENT_TO_DEST_add[Client_Address_Index].index(Destination_Address)

        #Now obtain the measurement of amount of packets received , first wait for header
        rxData = int.from_bytes(ser.read(1), "big")
        # Clear header trackers
        header = 0
        current_header = ''
        #Now wait for the TX measurements start header
        wait_for_header('MS',ser)
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        Amount_RX = read_in_measurement(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        if len(Client_TX_Amount)==Client_Address_Index:
            holder=[]
            Client_TX_Amount.append(holder)
        if len(Client_TX_Amount[Client_Address_Index])==Address_Index_Destination:
            holder=[]
            Client_TX_Amount[Client_Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        Client_TX_Amount[Client_Address_Index][Address_Index_Destination].append(Amount_RX)


        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            wait_for_next(ser)
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.


#Reads in standard routing node data
def rx_Read_Node(ser,loops):
    global rxData
    global current_header
    global header
    #Clear header trackers
    header = 0
    current_header = ''
    #Start measurements
    rxData =  int.from_bytes(ser.read(1), "big")
    #First Obtains the start of the measurements
    wait_for_start(ser)
    #Clear header trackers
    header = 0
    current_header = ''
    #The start has been obtained measurements will now commence
    #Remember for loop already read the next byte after the header
    #First measurement is address
    if rxData not in NODE_index:
        NODE_index.append(rxData)
    #Obtain the index of the address
    Address_Index = NODE_index.index(rxData)
    #Read in First header value to denote start of load
    rxData = int.from_bytes(ser.read(1), "big")
    wait_for_load_value(ser)
    #Remember while loop read in last rx data
    #Now wait for end line and read in the load data
    load = read_load_data(ser)
    if len(LOAD_array)==Address_Index:
        holder = [load]
        LOAD_array.append(holder)
    else:
        LOAD_array[Address_Index].append(load)
    #This case the last read in byte was '\n' so we end here for now
    print("######## PRINTING LOAD MEASUREMENTS #############")
    print("-----Current Index Of Nodes---------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current Load Of Nodes-----------")
    print(LOAD_array)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the sent data
    #Read in Packet Sent Data (this is the current address)
    read_in_packet_sent_data(ser)
    print("######## PRINTING PACKET SENT MEASUREMENTS #############")
    #End of the packet sent data
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Sent Packets-----------")
    print(PACKETS_sent)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the received data
    read_in_packet_received_data(ser)
    #End of the packet received data
    print("######## PRINTING PACKET RECEIVED MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Received Packets-----------")
    print(PACKETS_received)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the RSSI values
    read_in_RSSI(ser)
    print("######## PRINTING RSSI MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of RSSI values-----------")
    print(RSSI_value)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the SNR values
    read_in_SNR(ser)
    print("######## PRINTING SNR MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of SNR values-----------")
    print(SNR_value)
    print("-------------------------------------")
    print("###########################################################")
    #Read the routing table entries
    read_in_ROUTING_TABLE(ser)
    print("######## PRINTING ROUTING TABLE MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List known destinations for known nodes-----------")
    print(NODE_TO_DEST_add)
    print("-------------------------------------")
    print("-----Chosen next hop path for each node to destination-----------")
    print(ROUTING_table_path)
    print("-------------------------------------")
    print("-----All known next hop path for each node to destination-----------")
    print(ROUTING_table_next)
    print("-------------------------------------")
    print("###########################################################")


    #Now we check if everything has been filled in correctly for the arrays
    for i in range(0,len(PACKETS_sent)):
        for j in range(0,len(PACKETS_sent[i])):
            while len(PACKETS_sent[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_sent[i][j].append(0)
    for i in range(0,len(PACKETS_received)):
        for j in range(0,len(PACKETS_received[i])):
            while len(PACKETS_received[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_received[i][j].append(0)
    for i in range(0,len(RSSI_value)):
        for j in range(0,len(RSSI_value[i])):
            while len(RSSI_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                RSSI_value[i][j].append(0)
    for i in range(0,len(SNR_value)):
        for j in range(0,len(SNR_value[i])):
            while len(SNR_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                SNR_value[i][j].append(0)

#Reads in standard destination node data
def rx_Read_Dest(ser,loops):
    global rxData
    global current_header
    global header
    #Clear header trackers
    header = 0
    current_header = ''
    #Start measurements
    rxData =  int.from_bytes(ser.read(1), "big")
    #First Obtains the start of the measurements
    wait_for_start(ser)
    #Clear header trackers
    header = 0
    current_header = ''
    #The start has been obtained measurements will now commence
    #Remember for loop already read the next byte after the header
    #First measurement is address
    if rxData not in NODE_index:
        NODE_index.append(rxData)
    #Obtain the index of the address
    Address_Index = NODE_index.index(rxData)
    #Read in First header value to denote start of load
    rxData = int.from_bytes(ser.read(1), "big")
    wait_for_load_value(ser)
    #Remember while loop read in last rx data
    #Now wait for end line and read in the load data
    load = read_load_data(ser)
    if len(LOAD_array)==Address_Index:
        holder = [load]
        LOAD_array.append(holder)
    else:
        LOAD_array[Address_Index].append(load)
    #This case the last read in byte was '\n' so we end here for now
    print("######## PRINTING LOAD MEASUREMENTS #############")
    print("-----Current Index Of Nodes---------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current Load Of Nodes-----------")
    print(LOAD_array)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the sent data
    #Read in Packet Sent Data (this is the current address)
    read_in_packet_sent_data(ser)
    print("######## PRINTING PACKET SENT MEASUREMENTS #############")
    #End of the packet sent data
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Sent Packets-----------")
    print(PACKETS_sent)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the received data
    read_in_packet_received_data(ser)
    #End of the packet received data
    print("######## PRINTING PACKET RECEIVED MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Received Packets-----------")
    print(PACKETS_received)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the RSSI values
    read_in_RSSI(ser)
    print("######## PRINTING RSSI MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of RSSI values-----------")
    print(RSSI_value)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the SNR values
    read_in_SNR(ser)
    print("######## PRINTING SNR MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of SNR values-----------")
    print(SNR_value)
    print("-------------------------------------")
    print("###########################################################")
    #Read the routing table entries
    read_in_ROUTING_TABLE(ser)
    print("######## PRINTING ROUTING TABLE MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List known destinations for known nodes-----------")
    print(NODE_TO_DEST_add)
    print("-------------------------------------")
    print("-----Chosen next hop path for each node to destination-----------")
    print(ROUTING_table_path)
    print("-------------------------------------")
    print("-----All known next hop path for each node to destination-----------")
    print(ROUTING_table_next)
    print("-------------------------------------")
    print("###########################################################")
    #Read in the message received data
    read_in_AMOUNT_RECEIVED_DEST(ser)
    print("######## PRINTING DESTINATION RECIVED RX AND PING MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List Destinations-----------")
    print(DEST_add)
    print("-------------------------------------")
    print("-----Current List known clients for destinations-----------")
    print(DEST_TO_CLIENT_add)
    print("-------------------------------------")
    print("-----PING for clients-----------")
    print(Dest_PING_Amount)
    print("-------------------------------------")
    print("-----Throughput clients-----------")
    print(Dest_RX_Amount)
    print("-------------------------------------")
    print("###########################################################")

    #Now we check if everything has been filled in correctly for the arrays
    for i in range(0,len(PACKETS_sent)):
        for j in range(0,len(PACKETS_sent[i])):
            while len(PACKETS_sent[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_sent[i][j].append(0)
    for i in range(0,len(PACKETS_received)):
        for j in range(0,len(PACKETS_received[i])):
            while len(PACKETS_received[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_received[i][j].append(0)
    for i in range(0,len(RSSI_value)):
        for j in range(0,len(RSSI_value[i])):
            while len(RSSI_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                RSSI_value[i][j].append(0)
    for i in range(0,len(SNR_value)):
        for j in range(0,len(SNR_value[i])):
            while len(SNR_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                SNR_value[i][j].append(0)
    for i in range(0,len(Dest_PING_Amount)):
        for j in range(0,len(Dest_PING_Amount[i])):
            while len(Dest_PING_Amount[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                Dest_PING_Amount[i][j].append(0)
    for i in range(0,len(Dest_RX_Amount)):
        for j in range(0,len(Dest_RX_Amount[i])):
            while len(Dest_RX_Amount[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                Dest_RX_Amount[i][j].append(0)

#Reads in standard client node data
def rx_Read_Client(ser,loops):
    global rxData
    global current_header
    global header
    #Clear header trackers
    header = 0
    current_header = ''
    #Start measurements
    rxData =  int.from_bytes(ser.read(1), "big")
    #First Obtains the start of the measurements
    wait_for_start(ser)
    #Clear header trackers
    header = 0
    current_header = ''
    #The start has been obtained measurements will now commence
    #Remember for loop already read the next byte after the header
    #First measurement is address
    if rxData not in NODE_index:
        NODE_index.append(rxData)
    #Obtain the index of the address
    Address_Index = NODE_index.index(rxData)
    #Read in First header value to denote start of load
    rxData = int.from_bytes(ser.read(1), "big")
    wait_for_load_value(ser)
    #Remember while loop read in last rx data
    #Now wait for end line and read in the load data
    load = read_load_data(ser)
    if len(LOAD_array)==Address_Index:
        holder = [load]
        LOAD_array.append(holder)
    else:
        LOAD_array[Address_Index].append(load)
    #This case the last read in byte was '\n' so we end here for now
    print("######## PRINTING LOAD MEASUREMENTS #############")
    print("-----Current Index Of Nodes---------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current Load Of Nodes-----------")
    print(LOAD_array)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the sent data
    #Read in Packet Sent Data (this is the current address)
    read_in_packet_sent_data(ser)
    print("######## PRINTING PACKET SENT MEASUREMENTS #############")
    #End of the packet sent data
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Sent Packets-----------")
    print(PACKETS_sent)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the received data
    read_in_packet_received_data(ser)
    #End of the packet received data
    print("######## PRINTING PACKET RECEIVED MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Received Packets-----------")
    print(PACKETS_received)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the RSSI values
    read_in_RSSI(ser)
    print("######## PRINTING RSSI MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of RSSI values-----------")
    print(RSSI_value)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the SNR values
    read_in_SNR(ser)
    print("######## PRINTING SNR MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of SNR values-----------")
    print(SNR_value)
    print("-------------------------------------")
    print("###########################################################")
    #Read the routing table entries
    read_in_ROUTING_TABLE(ser)
    print("######## PRINTING ROUTING TABLE MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List known destinations for known nodes-----------")
    print(DEST_add)
    print("-------------------------------------")
    print("-----Chosen next hop path for each node to destination-----------")
    print(ROUTING_table_path)
    print("-------------------------------------")
    print("-----All known next hop path for each node to destination-----------")
    print(ROUTING_table_next)
    print("-------------------------------------")
    print("###########################################################")
    # Read in the message sdent data
    read_in_AMOUNT_SENT_CLIENT(ser)
    print("######## PRINTING DESTINATION RECIVED RX AND PING MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List Clients-----------")
    print(CLIENT_add)
    print("-------------------------------------")
    print("-----Current List known destinations for clients-----------")
    print(CLIENT_TO_DEST_add)
    print("-------------------------------------")
    print("-----Message rate for clients-----------")
    print(Client_TX_Amount)
    print("-------------------------------------")
    print("###########################################################")

    #Now we check if everything has been filled in correctly for the arrays
    for i in range(0,len(PACKETS_sent)):
        for j in range(0,len(PACKETS_sent[i])):
            while len(PACKETS_sent[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_sent[i][j].append(0)
    for i in range(0,len(PACKETS_received)):
        for j in range(0,len(PACKETS_received[i])):
            while len(PACKETS_received[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_received[i][j].append(0)
    for i in range(0,len(RSSI_value)):
        for j in range(0,len(RSSI_value[i])):
            while len(RSSI_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                RSSI_value[i][j].append(0)
    for i in range(0,len(SNR_value)):
        for j in range(0,len(SNR_value[i])):
            while len(SNR_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                SNR_value[i][j].append(0)
    for i in range(0,len(Client_TX_Amount)):
        for j in range(0,len(Client_TX_Amount[i])):
            while len(Client_TX_Amount[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                Client_TX_Amount[i][j].append(0)

#Reads in standard client node data
def rx_Read_TESTING(ser,loops):
    global rxData
    global current_header
    global header
    #Clear header trackers
    header = 0
    current_header = ''
    #Start measurements
    rxData =  int.from_bytes(ser.read(1), "big")
    #First Obtains the start of the measurements
    wait_for_start(ser)
    #Clear header trackers
    header = 0
    current_header = ''
    #The start has been obtained measurements will now commence
    #Remember for loop already read the next byte after the header
    #First measurement is address
    if rxData not in NODE_index:
        NODE_index.append(rxData)
    #Obtain the index of the address
    Address_Index = NODE_index.index(rxData)
    #Read in First header value to denote start of load
    rxData = int.from_bytes(ser.read(1), "big")
    wait_for_load_value(ser)
    #Remember while loop read in last rx data
    #Now wait for end line and read in the load data
    load = read_load_data(ser)
    if len(LOAD_array)==Address_Index:
        holder = [load]
        LOAD_array.append(holder)
    else:
        LOAD_array[Address_Index].append(load)
    #This case the last read in byte was '\n' so we end here for now
    print("######## PRINTING LOAD MEASUREMENTS #############")
    print("-----Current Index Of Nodes---------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current Load Of Nodes-----------")
    print(LOAD_array)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the sent data
    #Read in Packet Sent Data (this is the current address)
    read_in_packet_sent_data(ser)
    print("######## PRINTING PACKET SENT MEASUREMENTS #############")
    #End of the packet sent data
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Sent Packets-----------")
    print(PACKETS_sent)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the received data
    read_in_packet_received_data(ser)
    #End of the packet received data
    print("######## PRINTING PACKET RECEIVED MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Received Packets-----------")
    print(PACKETS_received)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the RSSI values
    read_in_RSSI(ser)
    print("######## PRINTING RSSI MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of RSSI values-----------")
    print(RSSI_value)
    print("-------------------------------------")
    print("###########################################################")
    #Now starts reading in the SNR values
    read_in_SNR(ser)
    print("######## PRINTING SNR MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of SNR values-----------")
    print(SNR_value)
    print("-------------------------------------")
    print("###########################################################")
    #Read the routing table entries
    read_in_ROUTING_TABLE(ser)
    print("######## PRINTING ROUTING TABLE MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List known destinations for known nodes-----------")
    print(DEST_add)
    print("-------------------------------------")
    print("-----Chosen next hop path for each node to destination-----------")
    print(ROUTING_table_path)
    print("-------------------------------------")
    print("-----All known next hop path for each node to destination-----------")
    print(ROUTING_table_next)
    print("-------------------------------------")
    print("###########################################################")
    # Read in the message sdent data
    read_in_AMOUNT_SENT_CLIENT(ser)
    print("######## PRINTING DESTINATION RECIVED RX AND PING MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List Clients-----------")
    print(CLIENT_add)
    print("-------------------------------------")
    print("-----Current List known destinations for clients-----------")
    print(CLIENT_TO_DEST_add)
    print("-------------------------------------")
    print("-----Message rate for clients-----------")
    print(Client_TX_Amount)
    print("-------------------------------------")
    print("###########################################################")
    #Read in the message received data
    read_in_AMOUNT_RECEIVED_DEST(ser)
    print("######## PRINTING DESTINATION RECIVED RX AND PING MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List Destinations-----------")
    print(DEST_add)
    print("-------------------------------------")
    print("-----Current List known clients for destinations-----------")
    print(DEST_TO_CLIENT_add)
    print("-------------------------------------")
    print("-----PING for clients-----------")
    print(Dest_PING_Amount)
    print("-------------------------------------")
    print("-----Throughput clients-----------")
    print(Dest_RX_Amount)
    print("-------------------------------------")
    print("###########################################################")

    #Now we check if everything has been filled in correctly for the arrays
    for i in range(0,len(PACKETS_sent)):
        for j in range(0,len(PACKETS_sent[i])):
            while len(PACKETS_sent[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_sent[i][j].append(0)
    for i in range(0,len(PACKETS_received)):
        for j in range(0,len(PACKETS_received[i])):
            while len(PACKETS_received[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_received[i][j].append(0)
    for i in range(0,len(RSSI_value)):
        for j in range(0,len(RSSI_value[i])):
            while len(RSSI_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                RSSI_value[i][j].append(0)
    for i in range(0,len(SNR_value)):
        for j in range(0,len(SNR_value[i])):
            while len(SNR_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                SNR_value[i][j].append(0)
    for i in range(0,len(Client_TX_Amount)):
        for j in range(0,len(Client_TX_Amount[i])):
            while len(Client_TX_Amount[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                Client_TX_Amount[i][j].append(0)
    for i in range(0,len(Dest_PING_Amount)):
        for j in range(0,len(Dest_PING_Amount[i])):
            while len(Dest_PING_Amount[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                Dest_PING_Amount[i][j].append(0)
    for i in range(0,len(Dest_RX_Amount)):
        for j in range(0,len(Dest_RX_Amount[i])):
            while len(Dest_RX_Amount[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                Dest_RX_Amount[i][j].append(0)

if __name__ == "__main__":
    if live:
        #For live plots during demo?????
        plt.figure(figsize=(6.5, 7.2))
        plt.ylabel("Testing\n" + DATATYPE_LIST[0] + "\n")
        plt.tick_params(labelcolor='w', top=False, bottom=False, left=False, right=False)

        plt.xlabel("Time (s)")
        # fig.tight_layout()
        plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
        plt.grid(True)
        try:
            # Setup the serial
            ser = serial.Serial(COM_PORT_TEST, BAUD_RATE, timeout=None, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS)
            print("Connected to " + COM_PORT_TEST + ".")
        except:
            print("Could not connect to the device "+COM_PORT_TEST+".")
            exit()

        lines = []
        for i in range(NUM_SAMPLES):
            rx_Read_Node(ser)
            # remove old lines
            # for line in lines:
            #     if len(line) > 0:
            #         line.pop(0).remove()
            # for j in range(3):
            #     # Select colour
            #     if j == 0:
            #         label = 'X'
            #         color = 'g'
            #     elif j == 1:
            #         color = 'b'
            #         label = 'Y'
            #     else:
            #         color = 'r'
            #         label = 'Z'
            #     lines.append(plt.plot(X_axis[:i], RNG_array[:i, j], color, label=label, alpha=0.8))
            #     if j == 2:
            #         plt.legend(loc='upper right')
            # plt.grid(True)
            plt.pause(0.33)
    else:
        try:
            # Setup the serial
            ser_Test = serial.Serial(COM_PORT_TEST, BAUD_RATE, timeout=None, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS)
            print("Connected to " + COM_PORT_TEST + ".")
        except:
            print("Could not connect to the device "+COM_PORT_TEST+".")
            exit()
        header = 0
        #Merely samples the serial at these intervals
        for i in range(NUM_SAMPLES):
            rx_Read_TESTING(ser_Test,i)
            plt.pause(1/SAMPLING_FREQ)
        print("########### Starting Plotting Data ###########")
        #Print the load data
        print("########### Plotting "+DATATYPE_LIST[0]+" ###########")
        plt.ylabel(DATATYPE_LIST[0])
        plt.xlabel("Time (s)")
        # fig.tight_layout()
        plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
        plt.grid(True)
        #Obtaining the legend array
        legend = []
        for i in range (0,len(NODE_index)):
            legend.append("Node "+str(NODE_index[i]))
        for i in range(0,len(LOAD_array)):
            plt.plot(X_axis,LOAD_array[i],LINE_COLORS[i])
        plt.legend(legend)
        plt.savefig(test_array[current_test]+measurement_array[0]+".pdf")
        plt.show()
        plt.close()
        #Print the load data
        print("########### Plotting " + DATATYPE_LIST[1] + " ###########")
        #Now plotting the PDR data
        for i in range(0,len(PACKETS_received)):
            plt.ylabel(DATATYPE_LIST[1])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            holder = []
            for j in range(0,len(PACKETS_received[i])):
                # Define the array
                PDR_data = []
                # define the cetx array too
                CETX_data = []
                neigh_add = NEIGH_add[i][j]
                legend.append("Neighbour " + str(neigh_add))
                for k in range(0,len(PACKETS_received[i][j])):
                    #Obtain index of the current neighbour the measurements were received from
                    node_index = NODE_index.index(neigh_add)
                    # Obtain index of the current node in the neighbour's neighbour index
                    my_index = NEIGH_add[node_index].index(NODE_index[i])
                    #As such the corresponding data received was sent by node_index to my_index
                    if (PACKETS_sent[node_index][my_index][k]!=0):
                        PDR_data.append(PACKETS_received[i][j][k]/PACKETS_sent[node_index][my_index][k])
                    else:
                        PDR_data.append(0)
                    #CETX_data.append(1/(PACKETS_received[i][j][k]*PACKETS_sent[node_index][my_index][k]))
                plt.plot(X_axis, PDR_data, LINE_COLORS[j])
                holder.append(PDR_data)
            NODE_PDR_value.append(holder)
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[1] + "_for_node_"+str(NODE_index[i])+".pdf")
            plt.show()
            plt.close()
        print("########### Plotting " + DATATYPE_LIST[2] + " ###########")
        #Now plotting the ETX data
        for i in range(0,len(PACKETS_received)):
            plt.ylabel(DATATYPE_LIST[2])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            holder = []
            for j in range(0,len(PACKETS_received[i])):
                # Define the array
                PDR_data = []
                # define the cetx array too
                CETX_data = []
                neigh_add = NEIGH_add[i][j]
                legend.append("Neighbour " + str(neigh_add))
                for k in range(0,len(PACKETS_received[i][j])):
                    #Obtain index of the current neighbour the measurements were received from
                    node_index = NODE_index.index(neigh_add)
                    # Obtain index of the current node in the neighbour's neighbour index
                    my_index = NEIGH_add[node_index].index(NODE_index[i])
                    #As such the corresponding data received was sent by node_index to my_index
                    #PDR_data.append(PACKETS_received[i][j][k]/PACKETS_sent[node_index][my_index][k])
                    if (PACKETS_sent[node_index][my_index][k] and PACKETS_received[i][j][k]):
                        CETX_data.append(1/(PACKETS_received[i][j][k]*PACKETS_sent[node_index][my_index][k]))
                    else:
                        CETX_data.append(0)
                plt.plot(X_axis, CETX_data, LINE_COLORS[j])
                holder.append(CETX_data)
            NODE_ETX_value.append(holder)
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[2] + "_for_node_"+str(NODE_index[i])+".pdf")
            plt.show()
            plt.close()

        print("########### Plotting " + DATATYPE_LIST[3] + " ###########")
        #Now plotting the RSSI data
        for i in range(0,len(RSSI_value)):
            plt.ylabel(DATATYPE_LIST[3])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            for j in range(0,len(RSSI_value[i])):
                neigh_add = NEIGH_add[i][j]
                #Define the RSSI holder
                RSSI_holder = []
                legend.append("Neighbour " + str(neigh_add))
                for k in range(0,len(RSSI_value[i][j])):
                    RSSI_holder.append(RSSI_value[i][j][k])
                plt.plot(X_axis, RSSI_holder, LINE_COLORS[j])
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[3] + "_for_node_"+str(NODE_index[i])+".pdf")
            plt.show()
            plt.close()

        print("########### Plotting " + DATATYPE_LIST[4] + " ###########")
        #Now plotting the SNR data
        for i in range(0,len(SNR_value)):
            plt.ylabel(DATATYPE_LIST[4])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            for j in range(0,len(SNR_value[i])):
                neigh_add = NEIGH_add[i][j]
                #Define the RSSI holder
                SNR_holder = []
                legend.append("Neighbour " + str(neigh_add))
                for k in range(0,len(SNR_value[i][j])):
                    SNR_holder.append(SNR_value[i][j][k])
                plt.plot(X_axis, SNR_holder, LINE_COLORS[j])
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[4] + "_for_node_"+str(NODE_index[i])+".pdf")
            plt.show()
            plt.close()

        print("########### Plotting " + DATATYPE_LIST[5] + " ###########")
        #Now plotting the Throughput data
        for i in range(0,len(Dest_RX_Amount)):
            plt.ylabel(DATATYPE_LIST[5])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            for j in range(0,len(Dest_RX_Amount[i])):
                client_add = DEST_TO_CLIENT_add[i][j]
                #Define the RX holder
                RX_holder = []
                legend.append("Client " + str(client_add))
                for k in range(0,len(Dest_RX_Amount[i][j])):
                    RX_holder.append(Dest_RX_Amount[i][j][k])
                plt.plot(X_axis, RX_holder, LINE_COLORS[j])
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[5] + "_for_destination_"+str(DEST_add[i])+".pdf")
            plt.show()
            plt.close()

        print("########### Plotting " + DATATYPE_LIST[6] + " ###########")
        #Now plotting the PING data
        for i in range(0,len(Dest_PING_Amount)):
            plt.ylabel(DATATYPE_LIST[6])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            for j in range(0,len(Dest_PING_Amount[i])):
                client_add = DEST_TO_CLIENT_add[i][j]
                #Define the ping holder
                PING_holder = []
                legend.append("Client " + str(client_add))
                for k in range(0,len(Dest_PING_Amount[i][j])):
                    PING_holder.append(Dest_PING_Amount[i][j][k]/CLOCKS_PER_SEC*1000)
                plt.plot(X_axis, PING_holder, LINE_COLORS[j])
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[6] + "_for_destination_"+str(DEST_add[i])+".pdf")
            plt.show()
            plt.close()

        print("########### Plotting " + DATATYPE_LIST[7] + " ###########")
        #Now plotting the MDR data
        for i in range(0,len(Client_TX_Amount)):
            plt.ylabel(DATATYPE_LIST[7])
            plt.xlabel("Time (s)")
            # fig.tight_layout()
            plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
            plt.grid(True)
            # Construct legend for this node's data
            legend = []
            for j in range(0,len(Client_TX_Amount[i])):
                dest_add = CLIENT_TO_DEST_add[i][j]
                #Define the mdr holder
                MDR_holder = []
                legend.append("Client " + str(client_add))
                for k in range(0,len(Client_TX_Amount[i][j])):
                    #Obtain index of the current client the measurements were received from
                    dest_index = DEST_add.index(dest_add)
                    # Obtain index of the current destination in the client's destination index
                    my_index = DEST_TO_CLIENT_add[dest_index].index(CLIENT_add[i])
                    #As such the corresponding data received was received by dest_index from my_index
                    if (Client_TX_Amount[i][j][k]!=0):
                        MDR_holder.append(Dest_RX_Amount[dest_index][my_index][k]/Client_TX_Amount[i][j][k])
                    else:
                        MDR_holder.append(0)
                plt.plot(X_axis, MDR_holder, LINE_COLORS[j])
            plt.legend(legend)
            plt.savefig(test_array[current_test] + measurement_array[7] + "_for_client_"+str(CLIENT_add[i])+".pdf")
            plt.show()
            plt.close()



    # print(RNG_array)
    # plt.close()
    # data_normal = []
    # for i in range(0,len(RNG_array)):
    #     for j in range(0,len(RNG_array[i])):
    #         data_normal.append(RNG_array[i][j])
    # data_normal = np.array(data_normal)
    # ax = sns.distplot(data_normal,
    #                   bins=256,
    #                   kde=True,
    #                   color='black',
    #                   hist_kws={"linewidth": 15, 'alpha': 1, 'color':'skyblue'})
    # ax.set(xlabel='Normal Distribution', ylabel='Frequency')
    # plt.savefig("PDF_data.pdf")
    # plt.show()