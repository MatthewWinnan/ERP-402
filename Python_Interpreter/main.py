import matplotlib.pyplot as plt
import numpy as np
import serial
from scipy.stats import norm
import seaborn as sns
from IPython.display import clear_output




#Setting Print Options For The Terminal
np.set_printoptions(precision=4, linewidth=170, edgeitems=10, floatmode='fixed', sign=' ')
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams.update({'font.size': 13})
live = False

#Setting COM options
#General COM parameters
BYTE_ORDER = 'big'  # or 'big'
SAMPLING_FREQ = 0.25  # Hz
NUM_SAMPLES = 120  # 1 minute
BAUD_RATE = 9600

#PORTS for specific devices
COM_PORT_TEST = 'COM19'
COM_PORT_NODE_CLIENT = 'COM12'
COM_PORT_NODE_1 = 'COM34'
COM_PORT_NODE_2 = 'COM35'
COM_PORT_NODE_3 = 'COM30'
COM_PORT_NODE_4 = 'COM3'
COM_PORT_NODE_DESTINATION = 'COM33'

#Store the address here
#Address index corresponds to load measurement index in LOAD_array
NODE_index = []

#Store the loads here
LOAD_array = []

#Store neighbour addresses here
PACKETS_sent_add = []
#Store amount of packets sent here
PACKETS_sent = []

X_axis = np.linspace(0, (NUM_SAMPLES - 1) / SAMPLING_FREQ, NUM_SAMPLES)

# Library to decode byte stream
Start_Byte = ['S','L','P','N','R','M']
Second_Byte = ['T','D','S','A','R','I','N']
Packet_Headers = ['MS','PI','MR','SN','RI','NS','PR','RA','ND','PS','LD','ST']
Stop_Byte = 13 #Line feed denotes the end of line
Next_Line = 10 #Endl indicates next measurement
#Library for ease of plotting
DATATYPE_LIST = ['Load (packets/s)']
#Denotes the n'th byte of the header we are looking for
header = 0
#Denotes global variable for rx data byte
rxData = 0
#Denotes the global variab;e to store current header
current_header = ''
#Keeps count of the amount of loops currently performed
loops = 0

def wait_for_start():
    global ser_Test
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
        rxData = int.from_bytes(ser_Test.read(1), "big")

def wait_for_load_value():
    global ser_Test
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''
    shift = 0


    while current_header != 'LD':
        print("wait_for_load_value current byte is " + chr(rxData) + " and current header is " + current_header)
        # Resets if header not yet found
        if (header == 2):
            current_header = ''
            header = 0
            #An error occured
            print("LD not found wtf")
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
        rxData = int.from_bytes(ser_Test.read(1), "big")

def wait_for_neighbour_receive_add():
    global ser_Test
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''
    shift = 0


    while current_header != 'ND':
        print("wait_for_neighbour_receive_add current byte is " + chr(rxData) + " and current header is " + current_header)
        # Resets if header not yet found
        if (header == 2):
            current_header = ''
            header = 0
            #An error occured
            print("ND not found wtf")
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
        rxData = int.from_bytes(ser_Test.read(1), "big")

def wait_for_neighbour_sent_amount_head():
    global ser_Test
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''
    shift = 0


    while current_header != 'PS':
        print("wait_for_neighbour_sent_amount_head current byte is " + chr(rxData) + " and current header is " + current_header)
        # Resets if header not yet found
        if (header == 2):
            current_header = ''
            header = 0
            #An error occured
            print("PS not found wtf")
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
        rxData = int.from_bytes(ser_Test.read(1), "big")

def wait_for_next():
    global ser_Test
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''
    shift = 0


    while current_header != 'RA':
        print("wait_for_next current byte is " + chr(rxData) + " and current header is " + current_header)
        # Resets if header not yet found
        if (header == 2):
            current_header = ''
            header = 0
            #An error occured
            print("RA not found wtf")
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
        rxData = int.from_bytes(ser_Test.read(1), "big")

def wait_for_stop():
    global ser_Test
    global rxData
    global current_header
    global header

    load = 0
    current_header = ''

    while (rxData!=Next_Line):
        # Reads next byte
        rxData = int.from_bytes(ser_Test.read(1), "big")


def read_load_data():
    global ser_Test
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
        rxData = int.from_bytes(ser_Test.read(1), "big")
    while (rxData!=Next_Line):
        # Reads next byte
        rxData = int.from_bytes(ser_Test.read(1), "big")
    return load

def read_packet_sent_data():
    global ser_Test
    global rxData
    global current_header
    global header

    sent = 0
    current_header = ''

    while (rxData != Stop_Byte) and (chr(rxData) != 'R'):
        print("read_packet_sent_data current byte is " + str(rxData))
        #Adds the measurement to the variable
        sent = sent<<8 | rxData
        # Reads next byte
        rxData = int.from_bytes(ser_Test.read(1), "big")

    return sent

def read_in_packet_sent_data():
    global ser_Test
    global rxData
    global current_header
    global header

    #We do this until an end line is obtained
    rxData = int.from_bytes(ser_Test.read(1), "big")
    while (rxData!= Stop_Byte) and (rxData!=Next_Line ):
        # First reset trackers
        header = 0
        current_header = ''
        # First measurement is address
        if rxData not in NODE_index:
            NODE_index.append(rxData)
        #Create the first entry into neighbour list if none exhists
        if len(PACKETS_sent_add)==0:
            holder=[]
            PACKETS_sent_add.append(holder)
        #Obtain the index of the node
        Address_Index = NODE_index.index(rxData)
        #Now wait for the queue to start obtaining the niehgbour address
        rxData = int.from_bytes(ser_Test.read(1), "big")
        wait_for_neighbour_receive_add()
        #Remember last read byte is not looked at by while loop
        #Thus that is the start of the address
        neighbour_add = rxData
        # if neighbour_add not in PACKETS_sent_add[Address_Index]:
        #     PACKETS_sent_add[Address_Index].append(neighbour_add)
        if len(PACKETS_sent_add) == Address_Index:
            holder = [neighbour_add]
            PACKETS_sent_add.append(holder)
        else:
            if neighbour_add not in PACKETS_sent_add[Address_Index]:
                PACKETS_sent_add[Address_Index].append(neighbour_add)

        Address_Index_Neigh = PACKETS_sent_add[Address_Index].index(neighbour_add)
        #Now obtain the packet sent list , first wait for header
        rxData = int.from_bytes(ser_Test.read(1), "big")
        # Clear header trackers
        header = 0
        current_header = ''
        wait_for_neighbour_sent_amount_head()
        #Rememeber last read byte is left over. What follows is the measurements
        # Clear header trackers
        header = 0
        current_header = ''
        packets_sent = read_packet_sent_data()
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
            wait_for_next()
        else:
            wait_for_stop()
        #Remember the last read byte at this point is either endl or the start of a new node measurement.

def rx_Read_Test():
    global ser_Test
    global rxData
    global current_header
    global header
    global loops
    #Clear header trackers
    header = 0
    current_header = ''
    #Start measurements
    rxData =  int.from_bytes(ser_Test.read(1), "big")
    #First Obtains the start of the measurements
    wait_for_start()
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
    rxData = int.from_bytes(ser_Test.read(1), "big")
    wait_for_load_value()
    #Remember while loop read in last rx data
    #Now wait for end line and read in the load data
    load = read_load_data()
    if len(LOAD_array)==Address_Index:
        holder = [load]
        LOAD_array.append(holder)
    else:
        LOAD_array[Address_Index].append(load)
    #This case the last read in byte was '\n' so we end here for now
    print("-----Current Index Of Nodes---------")
    print(NODE_index)
    print("-------------------------------------")
    print("-----Current Load Of Nodes-----------")
    print(LOAD_array)
    print("-------------------------------------")
    #Now starts reading in the sent data
    #Read in Packet Sent Data (this is the current address)
    read_in_packet_sent_data()

    #End of the packet sent data
    print("-----Current List Of Neighbours-----------")
    print(PACKETS_sent_add)
    print("-------------------------------------")
    print("-----Current List Of Sent Packets-----------")
    print(PACKETS_sent)
    print("-------------------------------------")
    #Increase loops
    loops+=1
    #Now we check if everything has been filled in correctly for the arrays
    for i in range(0,len(PACKETS_sent)):
        for j in range(0,len(PACKETS_sent[i])):
            if len(PACKETS_sent[i][j])<loops:
                #Nothing was received at this time step as such put 0 so all arrays are equal length
                PACKETS_sent[i][j].append(0)







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
            rx_Read_Test()
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
        loops = 0
        #Merely samples the serial at these intervals
        for i in range(NUM_SAMPLES):
            rx_Read_Test()
            plt.pause(1/SAMPLING_FREQ)

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