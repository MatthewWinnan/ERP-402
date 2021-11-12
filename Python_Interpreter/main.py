import matplotlib.pyplot as plt
import numpy as np
import serial
from scipy.stats import norm
import seaborn as sns
from IPython.display import clear_output
import bitstring
import networkx as nx


#Setting Print Options For The Terminal
np.set_printoptions(precision=4, linewidth=170, edgeitems=10, floatmode='fixed', sign=' ')
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams.update({'font.size': 13})
live = False
show_network_graph = False

#Setting COM options
#General COM parameters
BYTE_ORDER = 'big'  # or 'big'
SAMPLING_FREQ = 1  # Hz (every 1 sec)
SAMPLING_TIME = 10 # Time to sample in seconds
NUM_SAMPLES = int(SAMPLING_TIME/(1/SAMPLING_FREQ) ) # 1 minute
BAUD_RATE = 115200

#PORTS for specific devices
COM_PORT_TEST = 'COM19'
COM_PORT_NODE_CLIENT = 'COM12'
COM_PORT_NODE_1 = 'COM34'
COM_PORT_NODE_2 = 'COM35'
COM_PORT_NODE_3 = 'COM30'
COM_PORT_NODE_4 = 'COM3'
# COM_PORT_NODE_DESTINATION = 'COM33'
COM_PORT_NODE_DESTINATION = 'COM33'

#TEST PARAMETERS
# What test are we doing????
current_test = 0
# Define the test strings
test_array = ["Defining"]
#Measurements taken
measurement_array = ["_load_per_node","_pdr_per_node","_etx_per_node","_rssi_per_node","_snr_per_node",
                     "_throughput_per_dest","_ping_per_dest","_mdr_per_dest","_dest_route_visual","_origin_route_visual"]

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
DESTINATION_ROUTING_table_next = []
#STores the next hop for the chosen path
DESTINATION_ROUTING_table_path = []
#Stores the routing table next hop entries for each node for a given origin
ORIGIN_ROUTING_table_next = []
#STores the next hop for the chosen path
ORIGIN_ROUTING_table_path = []
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
Start_Byte = ['S','L','P','N','R','M','T','C','D','O']
Second_Byte = ['T','D','S','A','R','I','N','E','P']
Packet_Headers = ['MS','PI','MR','SN','RI','NS','PR','RA','ND','PS','LD','ST','TE','CP','DA','CN','OA']
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
DATATYPE_LIST = ['Load (packets/s)','Packet Delivery Ration','ETX value for link',
                 'RSSI for link (dB)','SNR for link (dB)','Throughput (packets/s)','Packet Delay (ms)',
                 'Message Delivery Ratio','Destination Route Visualize','Origin Route Visualize']
LINE_COLORS = ['b','g','r','c','m','y','k','w']
#Defining clock per second for microcontroller
CLOCKS_PER_SEC = 100

#Libraries used for graphing
#Defining what colors the nodes should be
# r = clients
# b = destination
# g = routing nodes
Node_Color = ["r","b","g"]
#Defining what color the edges should be
# k = merely neighbours
# y = valid path to destination/origin
# m = chosen path to destination
Edge_Color = ['k','y','m']
#Defining what sizes the nodes should be
# 2 = clients
# 3 = destination
# 1 = routing nodes
Node_Size = [600,900,1200]
#Defining what thickness the edges should be
# 1 = merely neighbours
# 2 = valid path to destination/origin
# 3 = chosen path to destination
Edge_Size = [1,2,3]
#Defining the shapes of the nodes
# "v" = clients
# "^" = destination
# "o" = routing nodes
Node_Shape = ['v','^','o']


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
            return True
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
    return False

def wait_for_load_value(ser):
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''
    shift = 0

    return wait_for_header('LD',ser)
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

    return wait_for_header('ND',ser)
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
    return wait_for_header('NS',ser)
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

    return wait_for_header('PS',ser)
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

    return wait_for_header('PR',ser)
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

    return wait_for_header('RA',ser)
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
    i = 0
    current_header = ''

    while (rxData != Stop_Byte):
        print("read_load_data current byte is " + str(rxData))
        #Adds the measurement to the variable
        load = load <<8 | (rxData)
        # load = rxData - 48
        # Reads next byte
        rxData = int.from_bytes(ser.read(1), "big")
        i+=1
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
    i = 0

    while (rxData != Stop_Byte) and (chr(rxData) != 'R'):
        print("read_in_measurement current byte is " + str(rxData))
        #Adds the measurement to the variable
        sent = sent<<8 | rxData
        # sent = rxData
        # Reads next byte
        rxData = int.from_bytes(ser.read(1), "big")
        i+=1
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
        #sent = rxData
        # Reads next byte
        rxData = int.from_bytes(ser.read(1), "big",signed=True)
        loop+=1
    #Convert from unsigned to signed
    sent = -bitstring.BitArray(uint = sent, length=loop*8).int
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
        #sent = rxData
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
        if (wait_for_neighbour_destination_add(ser)):
            #This means that an error occured return with an error
            return True
        #Remember last read byte is not looked at by while loop
        #Thus that is the start of the address
        neighbour_add = rxData
        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        #First fill up potential missed entries and leave to be filled up eventually
        while len(NEIGH_add) < Address_Index:
            holder = []
            NEIGH_add.append(holder)
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
        if(wait_for_neighbour_sent_amount_head(ser)):
            #This means that an error occured return with an error
            return True
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        packets_sent = read_in_measurement(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        while len(PACKETS_sent)<=Address_Index:
            holder=[]
            PACKETS_sent.append(holder)
        while len(PACKETS_sent[Address_Index])<=Address_Index_Neigh:
            holder=[]
            PACKETS_sent[Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        PACKETS_sent[Address_Index][Address_Index_Neigh].append(packets_sent)
        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            if(wait_for_next(ser)):
                # This means that an error occured return with an error
                return True
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.
    return False

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
        if(wait_for_neighbour_source_add(ser)):
            #This means that an error occured return with an error
            return True
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
        if(wait_for_neighbour_receive_amount_head(ser)):
            #This means that an error occured return with an error
            return True
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        packets_received = read_in_measurement(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        while len(PACKETS_received)<=Address_Index:
            holder=[]
            PACKETS_received.append(holder)
        while len(PACKETS_received[Address_Index])<=Address_Index_Neigh:
            holder=[]
            PACKETS_received[Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        PACKETS_received[Address_Index][Address_Index_Neigh].append(packets_received)
        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            if(wait_for_next(ser)):
                # This means that an error occured return with an error
                return True
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.
    return False

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
        if(wait_for_neighbour_source_add(ser)):
            #This means that an error occured return with an error
            return True
        #Remember last read byte is not looked at by while loop
        #Thus that is the start of the address
        neighbour_add = rxData
        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        while len(NEIGH_add) < Address_Index:
            holder = []
            NEIGH_add.append(holder)
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
        if(wait_for_header('RI',ser)):
            #This means that an error occured return with an error
            return True
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        RSSI_result = measure_RSSI(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        while len(RSSI_value)<=Address_Index:
            holder=[]
            RSSI_value.append(holder)
        while len(RSSI_value[Address_Index])<=Address_Index_Neigh:
            holder=[]
            RSSI_value[Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        RSSI_value[Address_Index][Address_Index_Neigh].append(RSSI_result)
        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            if(wait_for_next(ser)):
                # This means that an error occured return with an error
                return True
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.
    return False

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
        if(wait_for_neighbour_source_add(ser)):
            #This means that an error occured return with an error
            return True
        #Remember last read byte is not looked at by while loop
        #Thus that is the start of the address
        neighbour_add = rxData
        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        while len(NEIGH_add) < Address_Index:
            holder = []
            NEIGH_add.append(holder)
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
        if(wait_for_header('SN',ser)):
            #This means that an error occured return with an error
            return True
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        SNR_result = read_in_measurement(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        while len(SNR_value)<=Address_Index:
            holder=[]
            SNR_value.append(holder)
        while len(SNR_value[Address_Index])<=Address_Index_Neigh:
            holder=[]
            SNR_value[Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        SNR_value[Address_Index][Address_Index_Neigh].append(SNR_result)
        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            if(wait_for_next(ser)):
                # This means that an error occured return with an error
                return True
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.
    return False

def read_in_DESTINATION_ROUTING_TABLE(ser):
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
        if(wait_for_header('DA', ser)):
            #This means that an error occured return with an error
            return True
        # Remember last read byte is not looked at by while loop
        # Thus that is the start of the address
        destination_add = rxData
        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        while len(NODE_TO_DEST_add) <= Address_Index:
            holder = []
            NODE_TO_DEST_add.append(holder)
        if destination_add not in NODE_TO_DEST_add[Address_Index]:
            NODE_TO_DEST_add[Address_Index].append(destination_add)

        try:
            Address_Index_Dest = NODE_TO_DEST_add[Address_Index].index(destination_add)
        except:
            print(NODE_TO_DEST_add)
        # Now obtain the chosen path , first wait for header
        rxData = int.from_bytes(ser.read(1), "big")
        # Clear header trackers
        header = 0
        current_header = ''
        # Now wait for the SNR start header
        if(wait_for_header('CP', ser)):
            #This means that an error occured return with an error
            return True
        # Remember last read byte is not looked at by while loop
        # Thus that is the start of the chosen path
        chosen_path_add = rxData
        while len(DESTINATION_ROUTING_table_path) <= Address_Index:
            holder = []
            DESTINATION_ROUTING_table_path.append(holder)
        while len(DESTINATION_ROUTING_table_path[Address_Index]) <= Address_Index_Dest:
            holder = []
            DESTINATION_ROUTING_table_path[Address_Index].append(holder)
        if chosen_path_add != DESTINATION_ROUTING_table_path[Address_Index][Address_Index_Dest]:
            DESTINATION_ROUTING_table_path[Address_Index][Address_Index_Dest] = chosen_path_add

        # Now obtain the next hop values
        rxData = int.from_bytes(ser.read(1), "big")
        # Clear header trackers
        header = 0
        current_header = ''
        # Now wait for the table enrty start header
        if(wait_for_header('TE', ser)):
            #This means that an error occured return with an error
            return True
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        NEXT_HOP = read_in_measurement(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        while  len(DESTINATION_ROUTING_table_next)<=Address_Index:
            holder=[]
            DESTINATION_ROUTING_table_next.append(holder)
        while len(DESTINATION_ROUTING_table_next[Address_Index])<=Address_Index_Dest:
            holder=[]
            DESTINATION_ROUTING_table_next[Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        if NEXT_HOP not in DESTINATION_ROUTING_table_next[Address_Index][Address_Index_Dest]:
            DESTINATION_ROUTING_table_next[Address_Index][Address_Index_Dest].append(NEXT_HOP)
        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            if(wait_for_next(ser)):
                # This means that an error occured return with an error
                return True
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.
    return False


def read_in_ORIGIN_ROUTING_TABLE(ser):
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
            NODE_TO_CLIENT_add.append(holder)

        # Obtain the index of the node
        Address_Index = NODE_index.index(rxData)
        # Now wait for the queue to start obtaining the origin address
        rxData = int.from_bytes(ser.read(1), "big")
        if(wait_for_header('OA', ser)):
            #This means that an error occured return with an error
            return True
        # Remember last read byte is not looked at by while loop
        # Thus that is the start of the address
        origin_add = rxData
        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        while len(NODE_TO_CLIENT_add) <= Address_Index:
            holder = []
            NODE_TO_CLIENT_add.append(holder)
        if origin_add not in NODE_TO_CLIENT_add[Address_Index]:
            NODE_TO_CLIENT_add[Address_Index].append(origin_add)

        Address_Index_Origin = NODE_TO_CLIENT_add[Address_Index].index(origin_add)
        # Now obtain the chosen path , first wait for header
        rxData = int.from_bytes(ser.read(1), "big")
        # Clear header trackers
        header = 0
        current_header = ''
        # Now wait for the SNR start header
        if(wait_for_header('CP', ser)):
            #This means that an error occured return with an error
            return True
        # Remember last read byte is not looked at by while loop
        # Thus that is the start of the chosen path
        chosen_path_add = rxData
        while len(ORIGIN_ROUTING_table_path) <= Address_Index:
            holder = []
            ORIGIN_ROUTING_table_path.append(holder)
        while len(ORIGIN_ROUTING_table_path[Address_Index]) <= Address_Index_Origin:
            holder = []
            ORIGIN_ROUTING_table_path[Address_Index].append(holder)
        if chosen_path_add != ORIGIN_ROUTING_table_path[Address_Index][Address_Index_Origin]:
            ORIGIN_ROUTING_table_path[Address_Index][Address_Index_Origin] = chosen_path_add

        # Now obtain the next hop values
        rxData = int.from_bytes(ser.read(1), "big")
        # Clear header trackers
        header = 0
        current_header = ''
        # Now wait for the table enrty start header
        if(wait_for_header('TE', ser)):
            #This means that an error occured return with an error
            return True
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        NEXT_HOP = read_in_measurement(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        while  len(ORIGIN_ROUTING_table_next)<=Address_Index:
            holder=[]
            ORIGIN_ROUTING_table_next.append(holder)
        while len(ORIGIN_ROUTING_table_next[Address_Index])<=Address_Index_Origin:
            holder=[]
            ORIGIN_ROUTING_table_next[Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        if NEXT_HOP not in ORIGIN_ROUTING_table_next[Address_Index][Address_Index_Origin]:
            ORIGIN_ROUTING_table_next[Address_Index][Address_Index_Origin].append(NEXT_HOP)
        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            if(wait_for_next(ser)):
                # This means that an error occured return with an error
                return True
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.
    return False

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
        if(wait_for_header('CN',ser)):
            #This means that an error occured return with an error
            return True
        #Remember last read byte is not looked at by while loop
        #Thus that is the start of the client address
        Client_Address = rxData

        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        while len(DEST_TO_CLIENT_add) < Dest_Address_Index:
            holder = []
            DEST_TO_CLIENT_add.append(holder)
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
        if(wait_for_header('MR',ser)):
            #This means that an error occured return with an error
            return True
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        Amount_RX = read_in_AMOUNT_RX(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        while len(Dest_RX_Amount)<=Dest_Address_Index:
            holder=[]
            Dest_RX_Amount.append(holder)
        while len(Dest_RX_Amount[Dest_Address_Index])<=Address_Index_Client:
            holder=[]
            Dest_RX_Amount[Dest_Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        Dest_RX_Amount[Dest_Address_Index][Address_Index_Client].append(Amount_RX)

        #Now wait for the PING measurements start header
        if(wait_for_header('PI',ser)):
            #This means that an error occured return with an error
            return True
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        Amount_PING = read_in_measurement(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        while len(Dest_PING_Amount)<=Dest_Address_Index:
            holder=[]
            Dest_PING_Amount.append(holder)
        while len(Dest_PING_Amount[Dest_Address_Index])<=Address_Index_Client:
            holder=[]
            Dest_PING_Amount[Dest_Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        Dest_PING_Amount[Dest_Address_Index][Address_Index_Client].append(Amount_PING)


        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            if(wait_for_next(ser)):
                # This means that an error occured return with an error
                return True
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.
    return False

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
        if(wait_for_header('DA',ser)):
            #This means that an error occured return with an error
            return True
        #Remember last read byte is not looked at by while loop
        #Thus that is the start of the destination address
        Destination_Address = rxData

        # if neighbour_add not in NEIGH_add[Address_Index]:
        #     NEIGH_add[Address_Index].append(neighbour_add)
        while len(CLIENT_TO_DEST_add) < Client_Address_Index:
            holder = []
            CLIENT_TO_DEST_add.append(holder)

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
        if(wait_for_header('MS',ser)):
            #This means that an error occured return with an error
            return True
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        Amount_RX = read_in_measurement(ser)
        #Last byte is either 'R' or endl.
        #First save the new data
        while len(Client_TX_Amount)<=Client_Address_Index:
            holder=[]
            Client_TX_Amount.append(holder)
        while len(Client_TX_Amount[Client_Address_Index])<=Address_Index_Destination:
            holder=[]
            Client_TX_Amount[Client_Address_Index].append(holder)
        #This should make sure the indexes are always full?????
        Client_TX_Amount[Client_Address_Index][Address_Index_Destination].append(Amount_RX)


        #AFter this check if 'R' or endl
        if chr(rxData)=='R':
            #wait for the next measurements
            if(wait_for_next(ser)):
                # This means that an error occured return with an error
                return True
        else:
            wait_for_stop(ser)
        #Remember the last read byte at this point is either endl or the start of a new node measurement.
    return False

def Update_Destination_Graph():
    #Updates the visualization for the path towards a destination
    # Initialize Graph
    G = nx.DiGraph()
    # Initialize legend array
    legend = []
    for i in range(0, len(NODE_index)):
        if (NODE_index[i] in CLIENT_add):
            # Adding Client nodes
            G.add_node(NODE_index[i], color=Node_Color[0], size=Node_Size[1], shape=Node_Shape[0])
            legend.append("Client Node " + str(NODE_index[i]))
        elif (NODE_index[i] in DEST_add):
            # Adding Dest nodes
            G.add_node(NODE_index[i], color=Node_Color[1], size=Node_Size[2], shape=Node_Shape[1])
            legend.append("Destination Node " + str(NODE_index[i]))
        else:
            # Adding routing nodes
            G.add_node(NODE_index[i], color=Node_Color[2], size=Node_Size[0], shape=Node_Shape[2])
            legend.append("Routing Node " + str(NODE_index[i]))
        try:
            for j in range(0, len(NEIGH_add[i])):
                # Adding edges
                b_flag = False  # This flag says was the edge a path to the destination
                for k in range(0, len(DEST_add)):
                    # We need to check if this edge is a path to the destination
                    if (NEIGH_add[i][j] in DESTINATION_ROUTING_table_next[i][k]):
                        # It is a path
                        b_flag = True
                        print(NEIGH_add)
                        print(NEIGH_add[i][j])
                        print(DESTINATION_ROUTING_table_path)
                        print(DESTINATION_ROUTING_table_path[i][k])
                        if (NEIGH_add[i][j] == DESTINATION_ROUTING_table_path[i][k]):
                            # Now check if it is the chosen path if it is treat according
                            G.add_edge(NODE_index[i], NEIGH_add[i][j], color=Edge_Color[2], width=Edge_Size[2])
                        else:
                            # Only an available path thus treat according
                            G.add_edge(NODE_index[i], NEIGH_add[i][j], color=Edge_Color[1], width=Edge_Size[1])
                if (not b_flag):
                    # The edge is not a path as such treat according
                    G.add_edge(NODE_index[i], NEIGH_add[i][j], color=Edge_Color[0], width=Edge_Size[0])
        except:
            print("MASSIVE GRAPHING ISSUES")
    return G

def Update_Origin_Graph():
    #Updates the visualization for the path towards a client
    # Initialize Graph
    G = nx.DiGraph()
    # Initialize legend array
    legend = []
    for i in range(0, len(NODE_index)):
        if (NODE_index[i] in CLIENT_add):
            # Adding Client nodes
            G.add_node(NODE_index[i], color=Node_Color[0], size=Node_Size[1], shape=Node_Shape[0])
            legend.append("Client Node " + str(NODE_index[i]))
        elif (NODE_index[i] in DEST_add):
            # Adding Dest nodes
            G.add_node(NODE_index[i], color=Node_Color[1], size=Node_Size[2], shape=Node_Shape[1])
            legend.append("Destination Node " + str(NODE_index[i]))
        else:
            # Adding routing nodes
            G.add_node(NODE_index[i], color=Node_Color[2], size=Node_Size[0], shape=Node_Shape[2])
            legend.append("Routing Node " + str(NODE_index[i]))
        for j in range(0, len(NEIGH_add[i])):
            # Adding edges
            b_flag = False  # This flag says was the edge a path to the destination
            for k in range(0, len(CLIENT_add)):
                # We need to check if this edge is a path to the destination
                if (NEIGH_add[i][j] in ORIGIN_ROUTING_table_next[i][k]):
                    # It is a path
                    b_flag = True
                    if (NEIGH_add[i][j] == ORIGIN_ROUTING_table_path[i][k]):
                        # Now check if it is the chosen path if it is treat according
                        G.add_edge(NODE_index[i], NEIGH_add[i][j], color=Edge_Color[2], width=Edge_Size[2])
                    else:
                        # Only an available path thus treat according
                        G.add_edge(NODE_index[i], NEIGH_add[i][j], color=Edge_Color[1], width=Edge_Size[1])
            if (not b_flag):
                # The edge is not a path as such treat according
                G.add_edge(NODE_index[i], NEIGH_add[i][j], color=Edge_Color[0], width=Edge_Size[0])
    return G

def Display_Destination_Graph (G):
    plt.close()
    # Now graph it
    pos = nx.spring_layout(G)
    labels_edge = nx.get_edge_attributes(G, 'color')
    colors_edge = nx.get_edge_attributes(G, 'color').values()
    width_edge = nx.get_edge_attributes(G, 'width').values()
    colors_node = nx.get_node_attributes(G, 'color').values()
    size_nodes = list(nx.get_node_attributes(G, 'size').values())
    shapes_nodes = list(nx.get_node_attributes(G, 'shape').values())
    nx.draw_networkx(G, pos, with_labels=True, font_weight='bold', node_color=colors_node, node_size=size_nodes,
                     node_shape='D', edge_color=colors_edge, width=list(width_edge))
    # nx.draw_networkx_edge_labels(G, pos, edge_labels=labels_edge)
    plt.savefig(test_array[current_test] +measurement_array[8]+ "_result_network.pdf")
    plt.show()  # display

def Display_Origin_Graph (G):
    plt.close()
    # Now graph it
    pos = nx.spring_layout(G)
    labels_edge = nx.get_edge_attributes(G, 'color')
    colors_edge = nx.get_edge_attributes(G, 'color').values()
    width_edge = nx.get_edge_attributes(G, 'width').values()
    colors_node = nx.get_node_attributes(G, 'color').values()
    size_nodes = list(nx.get_node_attributes(G, 'size').values())
    shapes_nodes = list(nx.get_node_attributes(G, 'shape').values())
    nx.draw_networkx(G, pos, with_labels=True, font_weight='bold', node_color=colors_node, node_size=size_nodes,
                     node_shape='D', edge_color=colors_edge, width=list(width_edge))
    # nx.draw_networkx_edge_labels(G, pos, edge_labels=labels_edge)
    plt.savefig(test_array[current_test] +measurement_array[9]+ "_result_network.pdf")
    plt.show()  # display


#Function that creates backups of the current measurements
def Create_Backup():
    print("########### Initializing Backups #############")
    # Store the addresses here
    # Address index corresponds to index of the measured node
    BACKUP_NODE_index = np.copy(NODE_index)
    # Store neighbour addresses here
    BACKUP_NEIGH_add = np.copy(NEIGH_add)
    # Store destination address here
    BACKUP_DEST_add = np.copy(DEST_add)
    # STores client addresses here
    BACKUP_CLIENT_add = np.copy(CLIENT_add)
    # Stores destination to client adds here
    BACKUP_DEST_TO_CLIENT_add = np.copy(DEST_TO_CLIENT_add)
    # Stores cliebnt to dest adds here
    BACKUP_CLIENT_TO_DEST_add = np.copy(CLIENT_TO_DEST_add)
    # Stores node to destination adds
    BACKUP_NODE_TO_DEST_add = np.copy(NODE_TO_DEST_add)
    # Stores node to client adds
    BACKUP_NODE_TO_CLIENT_add = np.copy(NODE_TO_CLIENT_add)
    # Data to be stored defined here
    # Store the loads here
    BACKUP_LOAD_array = np.copy(LOAD_array)
    # Store amount of packets sent here
    BACKUP_PACKETS_sent = np.copy(PACKETS_sent)
    # Store amount of packets received here
    BACKUP_PACKETS_received = np.copy(PACKETS_received)
    # Store the average RSSI of received link rememeber it is signed
    BACKUP_RSSI_value = np.copy(RSSI_value)
    # Store the average SNR of received link rememeber this is again unsigned???? makes sure
    BACKUP_SNR_value = np.copy(SNR_value)
    # Stores the routing table next hop entries for each node for a given destination
    BACKUP_DESTINATION_ROUTING_table_next = np.copy(DESTINATION_ROUTING_table_next)
    # STores the next hop for the chosen path
    BACKUP_DESTINATION_ROUTING_table_path = np.copy(DESTINATION_ROUTING_table_path)
    # Stores the routing table next hop entries for each node for a given origin
    BACKUP_ORIGIN_ROUTING_table_next = np.copy(ORIGIN_ROUTING_table_next)
    # STores the next hop for the chosen path
    BACKUP_ORIGIN_ROUTING_table_path = np.copy(ORIGIN_ROUTING_table_path)
    # Stores the amount of messages packets received per epoch
    BACKUP_Dest_RX_Amount = np.copy(Dest_RX_Amount)
    # Stores the average PING for received messages
    BACKUP_Dest_PING_Amount = np.copy(Dest_PING_Amount)
    # Stores the amount of messages sent by client to destination per epoch
    BACKUP_Client_TX_Amount = np.copy(Client_TX_Amount)
    # STores the PDR for each link between node x and neighbour y
    BACKUP_NODE_PDR_value = np.copy(NODE_PDR_value)
    # Stores the ETX for each link between node x and neighbour y
    BACKUP_NODE_ETX_value = np.copy(NODE_ETX_value)
    return list(BACKUP_NODE_index),list(BACKUP_NEIGH_add),list(BACKUP_DEST_add),list(BACKUP_CLIENT_add),list(BACKUP_DEST_TO_CLIENT_add),list(BACKUP_CLIENT_TO_DEST_add)\
        ,list(BACKUP_NODE_TO_DEST_add),list(BACKUP_NODE_TO_CLIENT_add),list(BACKUP_LOAD_array),list(BACKUP_PACKETS_sent),list(BACKUP_PACKETS_received),list(BACKUP_RSSI_value)\
        ,list(BACKUP_SNR_value),list(BACKUP_DESTINATION_ROUTING_table_next),list(BACKUP_DESTINATION_ROUTING_table_path),\
           list(BACKUP_ORIGIN_ROUTING_table_next),list(BACKUP_ORIGIN_ROUTING_table_path),list(BACKUP_Dest_RX_Amount),\
           list(BACKUP_Dest_PING_Amount),list(BACKUP_Client_TX_Amount),list(BACKUP_NODE_PDR_value),list(BACKUP_NODE_ETX_value)

def revert_to_backup(BACKUP_NODE_index,BACKUP_NEIGH_add,BACKUP_DEST_add,BACKUP_CLIENT_add,BACKUP_DEST_TO_CLIENT_add,BACKUP_CLIENT_TO_DEST_add\
        ,BACKUP_NODE_TO_DEST_add,BACKUP_NODE_TO_CLIENT_add,BACKUP_LOAD_array,BACKUP_PACKETS_sent,BACKUP_PACKETS_received,BACKUP_RSSI_value\
        ,BACKUP_SNR_value,BACKUP_DESTINATION_ROUTING_table_next,BACKUP_DESTINATION_ROUTING_table_path,\
           BACKUP_ORIGIN_ROUTING_table_next,BACKUP_ORIGIN_ROUTING_table_path,BACKUP_Dest_RX_Amount,\
           BACKUP_Dest_PING_Amount,BACKUP_Client_TX_Amount,BACKUP_NODE_PDR_value,BACKUP_NODE_ETX_value):
    global NODE_index
    global NEIGH_add
    global DEST_add
    global CLIENT_add
    global DEST_TO_CLIENT_add
    global CLIENT_TO_DEST_add
    global NODE_TO_DEST_add
    global NODE_TO_CLIENT_add
    global LOAD_array
    global PACKETS_sent
    global PACKETS_received
    global RSSI_value
    global SNR_value
    global DESTINATION_ROUTING_table_next
    global DESTINATION_ROUTING_table_path
    global ORIGIN_ROUTING_table_next
    global ORIGIN_ROUTING_table_path
    global Dest_RX_Amount
    global Dest_PING_Amount
    global Client_TX_Amount
    global NODE_PDR_value
    global NODE_ETX_value
    print("########### Performing Backups Resetting #############")
    # Take backups as inputs and revert stores variables to old values
    # Address index corresponds to index of the measured node

    NODE_index =np.copy(BACKUP_NODE_index).tolist()
    # Store neighbour addresses here
    NEIGH_add = np.copy(BACKUP_NEIGH_add).tolist()
    # Store destination address here
    DEST_add =np.copy(BACKUP_DEST_add).tolist()
    # STores client addresses here
    CLIENT_add = np.copy(BACKUP_CLIENT_add).tolist()
    # Stores destination to client adds here
    DEST_TO_CLIENT_add = np.copy(BACKUP_DEST_TO_CLIENT_add).tolist()
    # Stores cliebnt to dest adds here
    CLIENT_TO_DEST_add =np.copy(BACKUP_CLIENT_TO_DEST_add).tolist()
    # Stores node to destination adds
    NODE_TO_DEST_add = np.copy(BACKUP_NODE_TO_DEST_add).tolist()
    # Stores node to client adds
    NODE_TO_CLIENT_add = np.copy(BACKUP_NODE_TO_CLIENT_add).tolist()
    # Data to be stored defined here
    # Store the loads here
    LOAD_array =np.copy(BACKUP_LOAD_array).tolist()
    # Store amount of packets sent here
    PACKETS_sent = np.copy(BACKUP_PACKETS_sent).tolist()
    # Store amount of packets received here
    PACKETS_received = np.copy(BACKUP_PACKETS_received).tolist()
    # Store the average RSSI of received link rememeber it is signed
    RSSI_value =np.copy(BACKUP_RSSI_value).tolist()
    # Store the average SNR of received link rememeber this is again unsigned???? makes sure
    SNR_value = np.copy(BACKUP_SNR_value).tolist()
    # Stores the routing table next hop entries for each node for a given destination
    DESTINATION_ROUTING_table_next = np.copy(BACKUP_DESTINATION_ROUTING_table_next).tolist()
    # STores the next hop for the chosen path
    DESTINATION_ROUTING_table_path = np.copy(BACKUP_DESTINATION_ROUTING_table_path).tolist()
    # Stores the routing table next hop entries for each node for a given origin
    ORIGIN_ROUTING_table_next =np.copy(BACKUP_ORIGIN_ROUTING_table_next).tolist()
    # STores the next hop for the chosen path
    ORIGIN_ROUTING_table_path = np.copy(BACKUP_ORIGIN_ROUTING_table_path).tolist()
    # Stores the amount of messages packets received per epoch
    Dest_RX_Amount =np.copy(BACKUP_Dest_RX_Amount).tolist()
    # Stores the average PING for received messages
    Dest_PING_Amount = np.copy(BACKUP_Dest_PING_Amount).tolist()
    # Stores the amount of messages sent by client to destination per epoch
    Client_TX_Amount = np.copy(BACKUP_Client_TX_Amount).tolist()
    # STores the PDR for each link between node x and neighbour y
    NODE_PDR_value = np.copy(BACKUP_NODE_PDR_value).tolist()
    # Stores the ETX for each link between node x and neighbour y
    NODE_ETX_value = np.copy(BACKUP_NODE_ETX_value).tolist()

#Reads in standard routing node data
def rx_Read_Node(ser,loops):
    global rxData
    global current_header
    global header
    # Make backup of global variables incase a message is missed
    BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add, BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
        , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent, BACKUP_PACKETS_received, BACKUP_RSSI_value \
        , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next, BACKUP_DESTINATION_ROUTING_table_path, \
    BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
    BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value = Create_Backup()
    # Clear header trackers
    header = 0
    current_header = ''
    # Start measurements
    rxData = int.from_bytes(ser.read(1), "big")
    # First Obtains the start of the measurements
    wait_for_start(ser)
    # Clear header trackers
    header = 0
    current_header = ''
    # The start has been obtained measurements will now commence
    # Remember for loop already read the next byte after the header
    # First measurement is address
    if rxData not in NODE_index:
        NODE_index.append(rxData)
    # Obtain the index of the address
    Address_Index = NODE_index.index(rxData)
    # Read in First header value to denote start of load
    rxData = int.from_bytes(ser.read(1), "big")
    if (wait_for_load_value(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
        # Remember while loop read in last rx data
    # Now wait for end line and read in the load data
    load = read_load_data(ser)
    if len(LOAD_array) == Address_Index:
        holder = [load]
        LOAD_array.append(holder)
    else:
        LOAD_array[Address_Index].append(load)
    # This case the last read in byte was '\n' so we end here for now
    print("######## PRINTING LOAD MEASUREMENTS #############")
    print("-----Current Index Of Nodes---------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current Load Of Nodes-----------")
    print(LOAD_array)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the sent data
    # Read in Packet Sent Data (this is the current address)
    if (read_in_packet_sent_data(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True

    print("######## PRINTING PACKET SENT MEASUREMENTS #############")
    # End of the packet sent data
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Sent Packets-----------")
    print(PACKETS_sent)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the received data
    if (read_in_packet_received_data(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
        # End of the packet received data
    print("######## PRINTING PACKET RECEIVED MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Received Packets-----------")
    print(PACKETS_received)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the RSSI values
    if (read_in_RSSI(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING RSSI MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of RSSI values-----------")
    print(RSSI_value)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the SNR values
    if (read_in_SNR(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING SNR MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of SNR values-----------")
    print(SNR_value)
    print("-------------------------------------")
    print("###########################################################")
    # Read the routing table entries
    if (read_in_DESTINATION_ROUTING_TABLE(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING DESTINATION ROUTING TABLE MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List known destinations for known nodes-----------")
    print(NODE_TO_DEST_add)
    print("-------------------------------------")
    print("-----Chosen next hop path for each node to destination-----------")
    print(DESTINATION_ROUTING_table_path)
    print("-------------------------------------")
    print("-----All known next hop path for each node to destination-----------")
    print(DESTINATION_ROUTING_table_next)
    print("-------------------------------------")
    print("###########################################################")
    # Read the routing table entries
    if (read_in_ORIGIN_ROUTING_TABLE(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING ORIGIN ROUTING TABLE MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List known origin for known nodes-----------")
    print(NODE_TO_CLIENT_add)
    print("-------------------------------------")
    print("-----Chosen next hop path for each node to origin-----------")
    print(ORIGIN_ROUTING_table_path)
    print("-------------------------------------")
    print("-----All known next hop path for each node to origin-----------")
    print(ORIGIN_ROUTING_table_next)
    print("-------------------------------------")
    print("###########################################################")


    #Now we check if everything has been filled in correctly for the arrays
    for i in range(0,len(PACKETS_sent)):
        for j in range(0,len(PACKETS_sent[i])):
            #Used to recover new sudden nodes that join
            if (( len(PACKETS_sent[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = PACKETS_sent[i][j][0]
                PACKETS_sent[i][j][0] = 0
                while len(PACKETS_sent[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    PACKETS_sent[i][j].append(0)
                PACKETS_sent[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(PACKETS_sent[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_sent[i][j].append(0)
    for i in range(0,len(PACKETS_received)):
        for j in range(0,len(PACKETS_received[i])):
            #Used to recover new sudden nodes that join
            if (( len(PACKETS_received[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = PACKETS_received[i][j][0]
                PACKETS_received[i][j][0] = 0
                while len(PACKETS_received[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    PACKETS_received[i][j].append(0)
                PACKETS_received[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(PACKETS_received[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_received[i][j].append(0)
    for i in range(0,len(RSSI_value)):
        for j in range(0,len(RSSI_value[i])):
            #Used to recover new sudden nodes that join
            if (( len(RSSI_value[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = RSSI_value[i][j][0]
                RSSI_value[i][j][0] = 0
                while len(RSSI_value[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    RSSI_value[i][j].append(0)
                RSSI_value[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(RSSI_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                RSSI_value[i][j].append(0)
    for i in range(0,len(SNR_value)):
        for j in range(0,len(SNR_value[i])):
            #Used to recover new sudden nodes that join
            if (( len(SNR_value[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = SNR_value[i][j][0]
                SNR_value[i][j][0] = 0
                while len(SNR_value[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    SNR_value[i][j].append(0)
                SNR_value[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(SNR_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                SNR_value[i][j].append(0)
    return False

#Reads in standard destination node data
def rx_Read_Dest(ser,loops):
    global rxData
    global current_header
    global header
    # Make backup of global variables incase a message is missed
    BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add, BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
        , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent, BACKUP_PACKETS_received, BACKUP_RSSI_value \
        , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next, BACKUP_DESTINATION_ROUTING_table_path, \
    BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
    BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value = Create_Backup()
    # Clear header trackers
    header = 0
    current_header = ''
    # Start measurements
    rxData = int.from_bytes(ser.read(1), "big")
    # First Obtains the start of the measurements
    wait_for_start(ser)
    # Clear header trackers
    header = 0
    current_header = ''
    # The start has been obtained measurements will now commence
    # Remember for loop already read the next byte after the header
    # First measurement is address
    if rxData not in NODE_index:
        NODE_index.append(rxData)
    # Obtain the index of the address
    Address_Index = NODE_index.index(rxData)
    # Read in First header value to denote start of load
    rxData = int.from_bytes(ser.read(1), "big")
    if (wait_for_load_value(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
        # Remember while loop read in last rx data
    # Now wait for end line and read in the load data
    load = read_load_data(ser)
    if len(LOAD_array) == Address_Index:
        holder = [load]
        LOAD_array.append(holder)
    else:
        LOAD_array[Address_Index].append(load)
    # This case the last read in byte was '\n' so we end here for now
    print("######## PRINTING LOAD MEASUREMENTS #############")
    print("-----Current Index Of Nodes---------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current Load Of Nodes-----------")
    print(LOAD_array)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the sent data
    # Read in Packet Sent Data (this is the current address)
    if (read_in_packet_sent_data(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True

    print("######## PRINTING PACKET SENT MEASUREMENTS #############")
    # End of the packet sent data
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Sent Packets-----------")
    print(PACKETS_sent)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the received data
    if (read_in_packet_received_data(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
        # End of the packet received data
    print("######## PRINTING PACKET RECEIVED MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Received Packets-----------")
    print(PACKETS_received)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the RSSI values
    if (read_in_RSSI(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING RSSI MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of RSSI values-----------")
    print(RSSI_value)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the SNR values
    if (read_in_SNR(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING SNR MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of SNR values-----------")
    print(SNR_value)
    print("-------------------------------------")
    print("###########################################################")
    # Read the routing table entries
    if (read_in_DESTINATION_ROUTING_TABLE(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING DESTINATION ROUTING TABLE MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List known destinations for known nodes-----------")
    print(NODE_TO_DEST_add)
    print("-------------------------------------")
    print("-----Chosen next hop path for each node to destination-----------")
    print(DESTINATION_ROUTING_table_path)
    print("-------------------------------------")
    print("-----All known next hop path for each node to destination-----------")
    print(DESTINATION_ROUTING_table_next)
    print("-------------------------------------")
    print("###########################################################")
    # Read the routing table entries
    if (read_in_ORIGIN_ROUTING_TABLE(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING ORIGIN ROUTING TABLE MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List known origin for known nodes-----------")
    print(NODE_TO_CLIENT_add)
    print("-------------------------------------")
    print("-----Chosen next hop path for each node to origin-----------")
    print(ORIGIN_ROUTING_table_path)
    print("-------------------------------------")
    print("-----All known next hop path for each node to origin-----------")
    print(ORIGIN_ROUTING_table_next)
    print("-------------------------------------")
    print("###########################################################")

    #Read in the message received data
    if(read_in_AMOUNT_RECEIVED_DEST(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
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
            #Used to recover new sudden nodes that join
            if (( len(PACKETS_sent[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = PACKETS_sent[i][j][0]
                PACKETS_sent[i][j][0] = 0
                while len(PACKETS_sent[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    PACKETS_sent[i][j].append(0)
                PACKETS_sent[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(PACKETS_sent[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_sent[i][j].append(0)
    for i in range(0,len(PACKETS_received)):
        for j in range(0,len(PACKETS_received[i])):
            #Used to recover new sudden nodes that join
            if (( len(PACKETS_received[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = PACKETS_received[i][j][0]
                PACKETS_received[i][j][0] = 0
                while len(PACKETS_received[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    PACKETS_received[i][j].append(0)
                PACKETS_received[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(PACKETS_received[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_received[i][j].append(0)
    for i in range(0,len(RSSI_value)):
        for j in range(0,len(RSSI_value[i])):
            #Used to recover new sudden nodes that join
            if (( len(RSSI_value[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = RSSI_value[i][j][0]
                RSSI_value[i][j][0] = 0
                while len(RSSI_value[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    RSSI_value[i][j].append(0)
                RSSI_value[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(RSSI_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                RSSI_value[i][j].append(0)
    for i in range(0,len(SNR_value)):
        for j in range(0,len(SNR_value[i])):
            #Used to recover new sudden nodes that join
            if (( len(SNR_value[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = SNR_value[i][j][0]
                SNR_value[i][j][0] = 0
                while len(SNR_value[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    SNR_value[i][j].append(0)
                SNR_value[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(SNR_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                SNR_value[i][j].append(0)
    for i in range(0,len(Dest_PING_Amount)):
        for j in range(0,len(Dest_PING_Amount[i])):
            #Used to recover new sudden nodes that join
            if (( len(Dest_PING_Amount[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = Dest_PING_Amount[i][j][0]
                Dest_PING_Amount[i][j][0] = 0
                while len(Dest_PING_Amount[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    Dest_PING_Amount[i][j].append(0)
                Dest_PING_Amount[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(Dest_PING_Amount[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                Dest_PING_Amount[i][j].append(0)
    for i in range(0,len(Dest_RX_Amount)):
        for j in range(0,len(Dest_RX_Amount[i])):
            #Used to recover new sudden nodes that join
            if (( len(Dest_RX_Amount[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = Dest_RX_Amount[i][j][0]
                Dest_PING_Amount[i][j][0] = 0
                while len(Dest_RX_Amount[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    Dest_RX_Amount[i][j].append(0)
                Dest_RX_Amount[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(Dest_RX_Amount[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                Dest_RX_Amount[i][j].append(0)
    return False

#Reads in standard client node data
def rx_Read_Client(ser,loops):
    global rxData
    global current_header
    global header
    # Make backup of global variables incase a message is missed
    BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add, BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
        , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent, BACKUP_PACKETS_received, BACKUP_RSSI_value \
        , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next, BACKUP_DESTINATION_ROUTING_table_path, \
    BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
    BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value = Create_Backup()
    # Clear header trackers
    header = 0
    current_header = ''
    # Start measurements
    rxData = int.from_bytes(ser.read(1), "big")
    # First Obtains the start of the measurements
    wait_for_start(ser)
    # Clear header trackers
    header = 0
    current_header = ''
    # The start has been obtained measurements will now commence
    # Remember for loop already read the next byte after the header
    # First measurement is address
    if rxData not in NODE_index:
        NODE_index.append(rxData)
    # Obtain the index of the address
    Address_Index = NODE_index.index(rxData)
    # Read in First header value to denote start of load
    rxData = int.from_bytes(ser.read(1), "big")
    if (wait_for_load_value(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
        # Remember while loop read in last rx data
    # Now wait for end line and read in the load data
    load = read_load_data(ser)
    if len(LOAD_array) == Address_Index:
        holder = [load]
        LOAD_array.append(holder)
    else:
        LOAD_array[Address_Index].append(load)
    # This case the last read in byte was '\n' so we end here for now
    print("######## PRINTING LOAD MEASUREMENTS #############")
    print("-----Current Index Of Nodes---------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current Load Of Nodes-----------")
    print(LOAD_array)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the sent data
    # Read in Packet Sent Data (this is the current address)
    if (read_in_packet_sent_data(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True

    print("######## PRINTING PACKET SENT MEASUREMENTS #############")
    # End of the packet sent data
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Sent Packets-----------")
    print(PACKETS_sent)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the received data
    if (read_in_packet_received_data(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
        # End of the packet received data
    print("######## PRINTING PACKET RECEIVED MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Received Packets-----------")
    print(PACKETS_received)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the RSSI values
    if (read_in_RSSI(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING RSSI MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of RSSI values-----------")
    print(RSSI_value)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the SNR values
    if (read_in_SNR(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING SNR MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of SNR values-----------")
    print(SNR_value)
    print("-------------------------------------")
    print("###########################################################")
    # Read the routing table entries
    if (read_in_DESTINATION_ROUTING_TABLE(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING DESTINATION ROUTING TABLE MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List known destinations for known nodes-----------")
    print(NODE_TO_DEST_add)
    print("-------------------------------------")
    print("-----Chosen next hop path for each node to destination-----------")
    print(DESTINATION_ROUTING_table_path)
    print("-------------------------------------")
    print("-----All known next hop path for each node to destination-----------")
    print(DESTINATION_ROUTING_table_next)
    print("-------------------------------------")
    print("###########################################################")
    # Read the routing table entries
    if (read_in_ORIGIN_ROUTING_TABLE(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING ORIGIN ROUTING TABLE MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List known origin for known nodes-----------")
    print(NODE_TO_CLIENT_add)
    print("-------------------------------------")
    print("-----Chosen next hop path for each node to origin-----------")
    print(ORIGIN_ROUTING_table_path)
    print("-------------------------------------")
    print("-----All known next hop path for each node to origin-----------")
    print(ORIGIN_ROUTING_table_next)
    print("-------------------------------------")
    print("###########################################################")

    # Read in the message sdent data
    if(read_in_AMOUNT_SENT_CLIENT(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
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
            #Used to recover new sudden nodes that join
            if (( len(PACKETS_sent[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = PACKETS_sent[i][j][0]
                PACKETS_sent[i][j][0] = 0
                while len(PACKETS_sent[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    PACKETS_sent[i][j].append(0)
                PACKETS_sent[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(PACKETS_sent[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_sent[i][j].append(0)
    for i in range(0,len(PACKETS_received)):
        for j in range(0,len(PACKETS_received[i])):
            #Used to recover new sudden nodes that join
            if (( len(PACKETS_received[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = PACKETS_received[i][j][0]
                PACKETS_received[i][j][0] = 0
                while len(PACKETS_received[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    PACKETS_received[i][j].append(0)
                PACKETS_received[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(PACKETS_received[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_received[i][j].append(0)
    for i in range(0,len(RSSI_value)):
        for j in range(0,len(RSSI_value[i])):
            #Used to recover new sudden nodes that join
            if (( len(RSSI_value[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = RSSI_value[i][j][0]
                RSSI_value[i][j][0] = 0
                while len(RSSI_value[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    RSSI_value[i][j].append(0)
                RSSI_value[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(RSSI_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                RSSI_value[i][j].append(0)
    for i in range(0,len(SNR_value)):
        for j in range(0,len(SNR_value[i])):
            #Used to recover new sudden nodes that join
            if (( len(SNR_value[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = SNR_value[i][j][0]
                SNR_value[i][j][0] = 0
                while len(SNR_value[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    SNR_value[i][j].append(0)
                SNR_value[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(SNR_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                SNR_value[i][j].append(0)
    for i in range(0,len(Client_TX_Amount)):
        for j in range(0,len(Client_TX_Amount[i])):
            #Used to recover new sudden nodes that join
            if (( len(Client_TX_Amount[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = Client_TX_Amount[i][j][0]
                Client_TX_Amount[i][j][0] = 0
                while len(Client_TX_Amount[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    Client_TX_Amount[i][j].append(0)
                Client_TX_Amount[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(Client_TX_Amount[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                Client_TX_Amount[i][j].append(0)
    return False

#Reads in standard client node data
def rx_Read_TESTING(ser,loops):
    global rxData
    global current_header
    global header
    # Make backup of global variables incase a message is missed
    BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add, BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
        , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent, BACKUP_PACKETS_received, BACKUP_RSSI_value \
        , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next, BACKUP_DESTINATION_ROUTING_table_path, \
    BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
    BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value = Create_Backup()
    # Clear header trackers
    header = 0
    current_header = ''
    # Start measurements
    rxData = int.from_bytes(ser.read(1), "big")
    # First Obtains the start of the measurements
    wait_for_start(ser)
    # Clear header trackers
    header = 0
    current_header = ''
    # The start has been obtained measurements will now commence
    # Remember for loop already read the next byte after the header
    # First measurement is address
    if rxData not in NODE_index:
        NODE_index.append(rxData)
    # Obtain the index of the address
    Address_Index = NODE_index.index(rxData)
    # Read in First header value to denote start of load
    rxData = int.from_bytes(ser.read(1), "big")
    if (wait_for_load_value(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
        # Remember while loop read in last rx data
    # Now wait for end line and read in the load data
    load = read_load_data(ser)
    if len(LOAD_array) == Address_Index:
        holder = [load]
        LOAD_array.append(holder)
    else:
        LOAD_array[Address_Index].append(load)
    # This case the last read in byte was '\n' so we end here for now
    print("######## PRINTING LOAD MEASUREMENTS #############")
    print("-----Current Index Of Nodes---------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current Load Of Nodes-----------")
    print(LOAD_array)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the sent data
    # Read in Packet Sent Data (this is the current address)
    if (read_in_packet_sent_data(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True

    print("######## PRINTING PACKET SENT MEASUREMENTS #############")
    # End of the packet sent data
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Sent Packets-----------")
    print(PACKETS_sent)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the received data
    if (read_in_packet_received_data(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
        # End of the packet received data
    print("######## PRINTING PACKET RECEIVED MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of Received Packets-----------")
    print(PACKETS_received)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the RSSI values
    if (read_in_RSSI(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING RSSI MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of RSSI values-----------")
    print(RSSI_value)
    print("-------------------------------------")
    print("###########################################################")
    # Now starts reading in the SNR values
    if (read_in_SNR(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING SNR MEASUREMENTS #############")
    print("-----Current List Of Neighbours-----------")
    print(NEIGH_add)
    print("-------------------------------------")
    print("-----Current List Of SNR values-----------")
    print(SNR_value)
    print("-------------------------------------")
    print("###########################################################")
    # Read the routing table entries
    if (read_in_DESTINATION_ROUTING_TABLE(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING DESTINATION ROUTING TABLE MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List known destinations for known nodes-----------")
    print(NODE_TO_DEST_add)
    print("-------------------------------------")
    print("-----Chosen next hop path for each node to destination-----------")
    print(DESTINATION_ROUTING_table_path)
    print("-------------------------------------")
    print("-----All known next hop path for each node to destination-----------")
    print(DESTINATION_ROUTING_table_next)
    print("-------------------------------------")
    print("###########################################################")
    # Read the routing table entries
    if (read_in_ORIGIN_ROUTING_TABLE(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
    print("######## PRINTING ORIGIN ROUTING TABLE MEASUREMENTS #############")
    print("-----Current list of known nodes-----------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current List known origin for known nodes-----------")
    print(NODE_TO_CLIENT_add)
    print("-------------------------------------")
    print("-----Chosen next hop path for each node to origin-----------")
    print(ORIGIN_ROUTING_table_path)
    print("-------------------------------------")
    print("-----All known next hop path for each node to origin-----------")
    print(ORIGIN_ROUTING_table_next)
    print("-------------------------------------")
    print("###########################################################")

    # Read in the message sdent data
    if(read_in_AMOUNT_SENT_CLIENT(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
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
    if(read_in_AMOUNT_RECEIVED_DEST(ser)):
        # This means error occured so decrease i and revert variables. Lastly exit this function
        revert_to_backup(BACKUP_NODE_index, BACKUP_NEIGH_add, BACKUP_DEST_add, BACKUP_CLIENT_add,
                         BACKUP_DEST_TO_CLIENT_add, BACKUP_CLIENT_TO_DEST_add \
                         , BACKUP_NODE_TO_DEST_add, BACKUP_NODE_TO_CLIENT_add, BACKUP_LOAD_array, BACKUP_PACKETS_sent,
                         BACKUP_PACKETS_received, BACKUP_RSSI_value \
                         , BACKUP_SNR_value, BACKUP_DESTINATION_ROUTING_table_next,
                         BACKUP_DESTINATION_ROUTING_table_path, \
                         BACKUP_ORIGIN_ROUTING_table_next, BACKUP_ORIGIN_ROUTING_table_path, BACKUP_Dest_RX_Amount, \
                         BACKUP_Dest_PING_Amount, BACKUP_Client_TX_Amount, BACKUP_NODE_PDR_value, BACKUP_NODE_ETX_value)
        return True
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
            #Used to recover new sudden nodes that join
            if (( len(PACKETS_sent[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = PACKETS_sent[i][j][0]
                PACKETS_sent[i][j][0] = 0
                while len(PACKETS_sent[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    PACKETS_sent[i][j].append(0)
                PACKETS_sent[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(PACKETS_sent[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_sent[i][j].append(0)
    for i in range(0,len(PACKETS_received)):
        for j in range(0,len(PACKETS_received[i])):
            #Used to recover new sudden nodes that join
            if (( len(PACKETS_received[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = PACKETS_received[i][j][0]
                PACKETS_received[i][j][0] = 0
                while len(PACKETS_received[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    PACKETS_received[i][j].append(0)
                PACKETS_received[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(PACKETS_received[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_received[i][j].append(0)
    for i in range(0,len(RSSI_value)):
        for j in range(0,len(RSSI_value[i])):
            #Used to recover new sudden nodes that join
            if (( len(RSSI_value[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = RSSI_value[i][j][0]
                RSSI_value[i][j][0] = 0
                while len(RSSI_value[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    RSSI_value[i][j].append(0)
                RSSI_value[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(RSSI_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                RSSI_value[i][j].append(0)
    for i in range(0,len(SNR_value)):
        for j in range(0,len(SNR_value[i])):
            #Used to recover new sudden nodes that join
            if (( len(SNR_value[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = SNR_value[i][j][0]
                SNR_value[i][j][0] = 0
                while len(SNR_value[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    SNR_value[i][j].append(0)
                SNR_value[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(SNR_value[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                SNR_value[i][j].append(0)
    for i in range(0,len(Dest_PING_Amount)):
        for j in range(0,len(Dest_PING_Amount[i])):
            #Used to recover new sudden nodes that join
            if (( len(Dest_PING_Amount[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = Dest_PING_Amount[i][j][0]
                Dest_PING_Amount[i][j][0] = 0
                while len(Dest_PING_Amount[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    Dest_PING_Amount[i][j].append(0)
                Dest_PING_Amount[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(Dest_PING_Amount[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                Dest_PING_Amount[i][j].append(0)
    for i in range(0,len(Dest_RX_Amount)):
        for j in range(0,len(Dest_RX_Amount[i])):
            #Used to recover new sudden nodes that join
            if (( len(Dest_RX_Amount[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = Dest_RX_Amount[i][j][0]
                Dest_PING_Amount[i][j][0] = 0
                while len(Dest_RX_Amount[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    Dest_RX_Amount[i][j].append(0)
                Dest_RX_Amount[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(Dest_RX_Amount[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                Dest_RX_Amount[i][j].append(0)
    for i in range(0,len(Client_TX_Amount)):
        for j in range(0,len(Client_TX_Amount[i])):
            #Used to recover new sudden nodes that join
            if (( len(Client_TX_Amount[i][j])==1) and (loops>1)):
                #This means this measurement randomly joined in the middle of messuring
                #Create a dummy fill as usual and add dummy at the end
                dummy = Client_TX_Amount[i][j][0]
                Client_TX_Amount[i][j][0] = 0
                while len(Client_TX_Amount[i][j]) < loops:
                    # Nothing was received at this time step as such put 0 so all arrays are equal length
                    Client_TX_Amount[i][j].append(0)
                Client_TX_Amount[i][j].append(dummy)
            #USed to recover nodes vanashing then rejoining
            while len(Client_TX_Amount[i][j])<loops+1:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                Client_TX_Amount[i][j].append(0)
                
    return False

if __name__ == "__main__":
    if live:
        print("##### TODO LIVE PLOTS #########")
        #For live plots during demo?????
        # plt.figure(figsize=(6.5, 7.2))
        # plt.ylabel("Testing\n" + DATATYPE_LIST[0] + "\n")
        # plt.tick_params(labelcolor='w', top=False, bottom=False, left=False, right=False)
        #
        # plt.xlabel("Time (s)")
        # # fig.tight_layout()
        # plt.xlim([0, (NUM_SAMPLES - 1) // SAMPLING_FREQ])
        # plt.grid(True)
        # try:
        #     # Setup the serial
        #     ser = serial.Serial(COM_PORT_TEST, BAUD_RATE, timeout=None, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS)
        #     print("Connected to " + COM_PORT_TEST + ".")
        # except:
        #     print("Could not connect to the device "+COM_PORT_TEST+".")
        #     exit()
        #
        # lines = []
        # for i in range(NUM_SAMPLES):
        #     rx_Read_Node(ser)
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
            # plt.pause(0.33)
    elif not live:
        header = 0
        #Merely samples the serial at these intervals
        try:
            # Setup the serial
            ser_R1 = serial.Serial(COM_PORT_NODE_1, BAUD_RATE, timeout=None, parity=serial.PARITY_NONE,
                                   bytesize=serial.EIGHTBITS)
            print("Connected to " + COM_PORT_NODE_1 + ".")
        except:
            print("Could not connect to the device " + COM_PORT_NODE_1 + ".")
            exit()
        try:
            # Setup the serial
            ser_Client = serial.Serial(COM_PORT_NODE_CLIENT, BAUD_RATE, timeout=None, parity=serial.PARITY_NONE,
                                       bytesize=serial.EIGHTBITS)
            print("Connected to " + COM_PORT_NODE_CLIENT + ".")
        except:
            print("Could not connect to the device " + COM_PORT_NODE_CLIENT + ".")
            exit()
        try:
            # Setup the serial
            ser_Dst = serial.Serial(COM_PORT_NODE_DESTINATION, BAUD_RATE, timeout=None, parity=serial.PARITY_NONE,
                                    bytesize=serial.EIGHTBITS)
            print("Connected to " + COM_PORT_NODE_DESTINATION + ".")
        except:
            print("Could not connect to the device " + COM_PORT_NODE_DESTINATION + ".")
            exit()

        for i in range(NUM_SAMPLES):
            flag_got = False #Says if got error
            #Every time the serial need to be opened then closed again
            # Now obtain the data
            if (rx_Read_Client(ser_Client, i) and (not flag_got)):
                flag_got = True
            # Now obtain the data
            if (rx_Read_Dest(ser_Dst, i) and (not flag_got)):
                flag_got = True
            #Now obtain the data
            if (rx_Read_Node(ser_R1,i) and (not flag_got)):
                flag_got = True

            if(flag_got):
                print("Increase NUM_SAMPLES")
                NUM_SAMPLES+=1

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
            while (len(LOAD_array[i])<len(X_axis)):
                LOAD_array[i].append(0)
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
                    if (neigh_add in NODE_index):
                        node_index = NODE_index.index(neigh_add)
                    # Obtain index of the current node in the neighbour's neighbour index
                    if (NODE_index[i] in NEIGH_add[node_index]):
                        my_index = NEIGH_add[node_index].index(NODE_index[i])
                        #As such the corresponding data received was sent by node_index to my_index
                        try:
                            if (PACKETS_sent[node_index][my_index][k]!=0):
                                PDR_data.append(PACKETS_received[i][j][k]/PACKETS_sent[node_index][my_index][k])
                            else:
                                PDR_data.append(0)
                        except:
                            PDR_data.append(0)
                    else:
                        PDR_data.append(0)
                    #CETX_data.append(1/(PACKETS_received[i][j][k]*PACKETS_sent[node_index][my_index][k]))
                while (len(PDR_data)>len(X_axis)):
                    PDR_data.pop(-1)
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
                    try:
                        node_index = NODE_index.index(neigh_add)
                        # Obtain index of the current node in the neighbour's neighbour index
                        my_index = NEIGH_add[node_index].index(NODE_index[i])
                        #As such the corresponding data received was sent by node_index to my_index
                        #PDR_data.append(PACKETS_received[i][j][k]/PACKETS_sent[node_index][my_index][k])
                        if (PACKETS_sent[node_index][my_index][k] and PACKETS_received[i][j][k]):
                            CETX_data.append(1/(PACKETS_received[i][j][k]*PACKETS_sent[node_index][my_index][k]))
                        else:
                            CETX_data.append(0)
                    except:
                        CETX_data.append(0)
                while (len(CETX_data)> len(X_axis)):
                    CETX_data.pop(-1)
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
                try:
                    neigh_add = NEIGH_add[i][j]
                    #Define the RSSI holder
                    RSSI_holder = []
                    legend.append("Neighbour " + str(neigh_add))
                    for k in range(0,len(RSSI_value[i][j])):
                        RSSI_holder.append(RSSI_value[i][j][k])
                    while(len(RSSI_holder)>len(X_axis)):
                        RSSI_holder.pop(-1)
                    plt.plot(X_axis, RSSI_holder, LINE_COLORS[j])
                except:
                    print("#### ERROR IN RSSI #######")
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
                try:
                    neigh_add = NEIGH_add[i][j]
                    #Define the RSSI holder
                    SNR_holder = []
                    legend.append("Neighbour " + str(neigh_add))
                    for k in range(0,len(SNR_value[i][j])):
                        SNR_holder.append(SNR_value[i][j][k])
                    while(len(SNR_holder)>len(X_axis)):
                        SNR_holder.pop(-1)
                    plt.plot(X_axis, SNR_holder, LINE_COLORS[j])
                except:
                    print("########### ERROR AT SNR #########")
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
                while(len(RX_holder)<len(X_axis)):
                    RX_holder.append(0)
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
                    PING_holder.append(Dest_PING_Amount[i][j][k])
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

        print("########### Plotting " + DATATYPE_LIST[8] + " ###########")
        DST_Network = nx.DiGraph()
        G = Update_Destination_Graph()
        DST_Network.update(G)
        Display_Destination_Graph(DST_Network)

        print("########### Plotting " + DATATYPE_LIST[9] + " ###########")
        ORIGIN_Network = nx.DiGraph()
        G = Update_Origin_Graph()
        ORIGIN_Network.update(G)
        Display_Origin_Graph(ORIGIN_Network)


    if show_network_graph:
        #Test data to create suggested graph
        NODE_index = [100, 110, 120, 130]
        DEST_add = [130]
        CLIENT_add = [100]
        NEIGH_add = [[110, 120], [100, 120, 130], [100, 110, 130], [110, 120]]
        DESTINATION_ROUTING_table_next = [[[120]], [[130]], [[130]], [[130]]]
        DESTINATION_ROUTING_table_path = [[120], [130], [130], [130]]
        DST_Network = nx.DiGraph()
        G = Update_Destination_Graph()
        DST_Network.update(G)
        Display_Destination_Graph(DST_Network)




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